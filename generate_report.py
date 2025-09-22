#! python
import argparse as arg
from datetime import datetime

import pandas as pd
import yaml

from torch.cuda import is_available
from transformers import logging as hf_logging
from dotenv import dotenv_values
from sqlalchemy import create_engine

hf_logging.set_verbosity_error()

from chirpp.preprocess.preprocess import Preprocess, SectionRemover

from chirpp.inference.inference import Inference

from chirpp.database.database import DataBase
from chirpp.postprocess.postprocess import PostProcess

# we will not be generating any more excel outputs so there is no to_excel option
# the code will stay in the post process for legacy support
parser = arg.ArgumentParser(description='Preprocess notes file for inference')
parser.add_argument('-n', '--notes', type=str, help='Path to raw patient notes')
parser.add_argument('-c', '--config', type=str, help='config file in yaml format', default="config.yaml",
                    action="store")
parser.add_argument('--env_file', help='env_file that contains the information about db connection', action="store")
args = parser.parse_args()


with open(args.config) as f:
    config = yaml.safe_load(f)

if is_available():
    device = "cuda:0"
else:
    device = "cpu"



##### DATABASE CONNECTION #####
env_values=dotenv_values(args.env_file)

engine = create_engine('postgresql+psycopg2://{}:{}@{}:{}/{}'. \
                           format(env_values["DB_USER"],
                                  env_values["DB_PWD"],
                                  env_values["DB_HOST"],
                                  env_values["DB_PORT"],
                                  env_values["DB_NAME"]))

database=DataBase(engine)


##### PREPROCESSING #####
preprocess_config=config["pre_process"]

if "additional_rules" in list(preprocess_config.keys()):
    additional_rules = preprocess_config["additional_rules"]
else:
    additional_rules = None

section_remover_for_inference = SectionRemover(lang_model="en_core_web_trf",
                                               remove_sections=preprocess_config["remove_sections"],
                                               keep_sections=preprocess_config["inference_sections"],
                                               rules_json=preprocess_config["section_rules"],
                                               additional_rules=additional_rules,
                                               gpu=device)

preprocess=Preprocess(args.notes, preprocess_config, section_remover_for_inference)
merged_notes, processed_notes = preprocess.preprocess_pipeline()


#### INFERENCE #####

inference_config=config["inference"]

print("[" + datetime.now().strftime("%Y/%m/%d %H:%M:%S") + "] " + "Collecting inference models")
# TODO re-write the inference class to accomodate ggufs and other types of models but load them one
# by one to save ram/vram

# get model probabilities
print("[" + datetime.now().strftime("%Y/%m/%d %H:%M:%S") + "] " + "Classifying")

inference_notes = processed_notes.copy()
inference_notes = inference_notes[~pd.isnull(inference_notes["processed_notes"])].copy()

probs=inference.run_pipeline(inference_config)

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
