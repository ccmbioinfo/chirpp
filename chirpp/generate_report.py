#! python
import argparse as arg
import os
from datetime import datetime

import pandas as pd
import yaml
from torch.cuda import is_available
from transformers import logging as hf_logging

hf_logging.set_verbosity_error()

from chirpp.inference.inference import Inference
from chirpp.postprocess.postprocess import PostProcess
from chirpp.preprocess.preprocess import SectionRemover, Preprocess
from chirpp.preprocess.utils import deidentify

#TODO this will need to migrate to the db
parser = arg.ArgumentParser(description='Preprocess notes file for inference')
parser.add_argument('-n', '--notes', type=str, help='Path to raw patient notes')
parser.add_argument('-o', '--outname', type=str, help='Path to outputs')
parser.add_argument('-c', '--config', type=str, help='config file in yaml format', default="config.yaml",
                    action="store")

args = parser.parse_args()

with open(args.config) as f:
    params = yaml.safe_load(f)

if is_available():
    device = "cuda:0"
else:
    device = "cpu"

# preprocessing, remove unwanted sections and keep raw notes in memory
if "additional_rules" in list(params["pre_process"].keys()):
    additional_rules = params["pre_process"]["additional_rules"]
else:
    additional_rules = None

print("[" + datetime.now().strftime("%Y/%m/%d %H:%M:%S") + "] " + "Generating Section remover")

section_remover_for_inference = SectionRemover(lang_model="en_core_web_trf",
                                               remove_sections=params["pre_process"]["remove_sections"],
                                               keep_sections=params["pre_process"]["inference_sections"],
                                               rules_json=params["pre_process"]["section_rules"],
                                               additional_rules=additional_rules,
                                               gpu=device)

# remove sections and generate inference notes these will be used for inference

print("[" + datetime.now().strftime("%Y/%m/%d %H:%M:%S") + "] " + "Preprocessing")

preprocessed_notes = Preprocess(args.notes, params["pre_process"]["terms_to_fix"])

preprocessed_notes = preprocessed_notes.read_raw_notes()

additional_columns = params["pre_process"]["include_cols"] + [params["pre_process"]["line_col"]]

preprocessed_notes = preprocessed_notes.get_relevant_notes(filters=params["pre_process"]["note_types"],
                                                           additional_columns=additional_columns)
include_cols = params["pre_process"]["include_cols"]
include_cols.append(params["pre_process"]["line_col"])
preprocessed_notes = preprocessed_notes.merge_notes(section_remover=section_remover_for_inference,
                                                    include_cols=include_cols,
                                                    group_cols=params["pre_process"]["group_cols"],
                                                    orientation=params["pre_process"]["orientation"],
                                                    keep_unlabelled=params["pre_process"]["keep_unlabelled"],
                                                    anonymize=params["pre_process"]["anonymize"],
                                                    language_model="en_core_web_trf",
                                                    line_col=params["pre_process"]["line_col"])

# TODO there probably is a better way than to create a copy
inference_notes = preprocessed_notes.merged_raw.copy()

inference_notes = inference_notes[~pd.isnull(inference_notes[params["inference"]["note_col"]])].copy()

print("[" + datetime.now().strftime("%Y/%m/%d %H:%M:%S") + "] " + "Collecting inference models")
# set up inference instance
infer_notes = Inference(classification_model=os.path.abspath(params["inference"]["classification_model"]),
                        summarization_model=os.path.abspath(params["inference"]["summarization_model"]),
                        classification_labels=params["inference"]["classification_labels"],
                        intent_model=os.path.abspath(params["inference"]["intent_model"]),
                        intent_labels=params["inference"]["intent_labels"],
                        substance_model=os.path.abspath(params["inference"]["substance_model"]),
                        substance_labels=params["inference"]["substance_labels"],
                        io_model=os.path.abspath(params["inference"]["io_model"]),
                        io_labels=params["inference"]["io_labels"],
                        device=device)

# get model probabilities
print("[" + datetime.now().strftime("%Y/%m/%d %H:%M:%S") + "] " + "Classifying")

probs = infer_notes.classify(inference_notes,
                             params["inference"]["note_col"],
                             params["inference"]["include_labels"])

inference_notes["probs"] = probs
inference_notes = inference_notes.sort_values(by=["probs"], ascending=False)

complaint_filter = inference_notes["Chief Complaint"].isin(params["inference"]["pos_complaints"])

# summary inference takes a long time, and I do not want to summarize all the notes. Here I will be looking at the
# distribution of definitely positive cases (assuming they are similarly distributed with other chirpp+ cases) and
# the % of them from the top, I will get a probability cutoff and then summarize everything that's above that prob

# get all the rows that contain a "definitiely chirpp" complaint
pos_based_on_complaint = inference_notes[complaint_filter]
num_rows = pos_based_on_complaint.shape[0]  # get the number of cases

# these are descending sorted so get the top cutoff (round the number just in case)
row_cutoff = round(num_rows * params["inference"]["cutoff"]) - 1

# get the model prob of that row, anything above that we will summarize
prob_cutoff = pos_based_on_complaint["probs"].tolist()[row_cutoff]
inference_notes["probs"][complaint_filter] = 1

if params["inference"]["use_chirpp"]:
    inference_notes["probs"][inference_notes[params["inference"]["chirpp_col"]] == "CHIRPP ICON"] = 1

# re-order because we just changed the probabilities
inference_notes["to_summarize"] = inference_notes["probs"] >= prob_cutoff

# get summaries of positive cases
print("[" + datetime.now().strftime("%Y/%m/%d %H:%M:%S") + "] " + "Summarizing")

summaries = infer_notes.summarize(inference_notes[inference_notes["to_summarize"]],
                                  params["inference"]["note_col"],
                                  params["inference"]["truncation"],
                                  params["inference"]["max_length"])

if params['inference']['anonymize_summaries'] and not params["pre_process"]['anonymize']:
    new_summaries=[]
    for sumr, name in zip(summaries, inference_notes["Patient Name"].to_list()):
        deidentified=deidentify(sumr, params["pre_process"]["lang_model"], [name])
        new_summaries.append(deidentified)
    summaries=new_summaries

print("[" + datetime.now().strftime("%Y/%m/%d %H:%M:%S") + "] " + "Calculating cosine similarities")

distances = infer_notes.calculate_cosine_distances(params["inference"]["distance_model"],
                                                   inference_notes[params["inference"]["note_col"]][
                                                       inference_notes["to_summarize"]],
                                                   summaries)

inference_notes["PHAC Narrative"]="None"
inference_notes["cosine_similarity"]=None

inference_notes["PHAC Narrative"][inference_notes["to_summarize"]] = summaries
inference_notes["cosine_similarity"][inference_notes["to_summarize"]] = distances

print("[" + datetime.now().strftime("%Y/%m/%d %H:%M:%S") + "] " + "Classifying intent")

intent = infer_notes.get_intent(notes=inference_notes[inference_notes["to_summarize"]],
                                notes_col=params["inference"]["note_col"],
                                label_dict=params["inference"]["intent_label_dict"],
                                cutoff=params["inference"]["intent_cutoff"])

inference_notes["intent"] = None
inference_notes["intent"][inference_notes["to_summarize"]] = intent

print("[" + datetime.now().strftime("%Y/%m/%d %H:%M:%S") + "] " + "Classifying substance use")

substance = infer_notes.get_substance(notes=inference_notes[inference_notes["to_summarize"]],
                                      notes_col=params["inference"]["note_col"],
                                      cutoff=params["inference"]["subs_cutoff"])
inference_notes["sub"] = None
inference_notes["sub"][inference_notes["to_summarize"]] = substance

print("[" + datetime.now().strftime("%Y/%m/%d %H:%M:%S") + "] " + "Classifying inside/outside")

io = infer_notes.get_io(notes=inference_notes[(inference_notes["to_summarize"]) & (inference_notes["intent"] == 10)],
                        notes_col=params["inference"]["note_col"],
                        cutoff=params["inference"]["io_cutoff"])

inference_notes["io"] = None
inference_notes["io"][(inference_notes["to_summarize"]) & (inference_notes["intent"] == 10)] = io


# post processing to generate the final output
print("[" + datetime.now().strftime("%Y/%m/%d %H:%M:%S") + "] " + "Generating Report")

params["post_process"]["pos_complaints"] = params["inference"]["pos_complaints"]
postprocess = PostProcess(preprocessed_notes.raw_notes, inference_notes, params["post_process"])
postprocess = postprocess.autofill()
postprocess.create_report(args.outname)

print("[" + datetime.now().strftime("%Y/%m/%d %H:%M:%S") + "] " + "Done!")
