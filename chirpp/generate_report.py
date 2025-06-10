#! python

import argparse as arg
import os
from datetime import datetime

import pandas as pd
import yaml
from torch.cuda import is_available
from transformers import logging as hf_logging
from dotenv import dotenv_values
from sqlalchemy import create_engine

hf_logging.set_verbosity_error()

from chirpp.inference.inference import Inference
from chirpp.postprocess.postprocess import PostProcess
from chirpp.preprocess.preprocess import SectionRemover, Preprocess
from chirpp.preprocess.utils import deidentify
from chirpp.database.database import DataBase

parser = arg.ArgumentParser(description='Preprocess notes file for inference')
parser.add_argument('-n', '--notes', type=str, help='Path to raw patient notes')
parser.add_argument('-o', '--outname', type=str, help='Path to outputs')
parser.add_argument('-c', '--config', type=str, help='config file in yaml format', default="config.yaml",
                    action="store")
parser.add_argument('-d', '--to_database', help='Import notes to database', action="store_true")
parser.add_argument('-e', '--to_excel', help='create an excel report', action="store_true")
parser.add_argument('--env_file', help='env_file that contains the information about db connection', action="store")
args = parser.parse_args()

# load config file this contains the parameters for inference and pre/post-processing
with open(args.config) as f:
    params = yaml.safe_load(f)

# there is an environment file that contains the database connection information, this is not to be pushed to the repo
env_values=dotenv_values(args.env_file)  

# check for gpu availability
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
# database connection
engine = create_engine('postgresql+psycopg2://{}:{}@{}:{}/{}'. \
                           format(env_values["DB_USER"],
                                  env_values["DB_PWD"],
                                  env_values["DB_HOST"],
                                  env_values["DB_PORT"],
                                  env_values["DB_NAME"]))

database=DataBase(engine)

# remove sections and generate inference notes these will be used for inference

print("[" + datetime.now().strftime("%Y/%m/%d %H:%M:%S") + "] " + "Preprocessing")

preprocess = Preprocess(args.notes, params["pre_process"]["terms_to_fix"])
preprocessed_notes = preprocess.read_raw_notes()
additional_columns = params["pre_process"]["include_cols"] + [params["pre_process"]["line_col"]]
preprocess = preprocessed_notes.get_relevant_notes(filters=params["pre_process"]["note_types"],
                                                           additional_columns=additional_columns)
include_cols = params["pre_process"]["include_cols"]
include_cols.append(params["pre_process"]["line_col"])
preprocess = preprocess.merge_notes(section_remover=section_remover_for_inference,
                                                    include_cols=include_cols,
                                                    group_cols=params["pre_process"]["group_cols"],
                                                    orientation=params["pre_process"]["orientation"],
                                                    keep_unlabelled=params["pre_process"]["keep_unlabelled"],
                                                    anonymize=params["pre_process"]["anonymize"],
                                                    language_model="en_core_web_trf",
                                                    line_col=params["pre_process"]["line_col"])

# remove empty notes, there must be at least one triage note
inference_notes = preprocess.merged_raw.copy()
inference_notes = inference_notes[~pd.isnull(inference_notes[params["inference"]["note_col"]])].copy()


#TODO refactor to use openai package to llamma cpp connection
inference = Inference(classification_model=os.path.abspath(params["inference"]["classification_model"]),
                        summarization_model=os.path.abspath(params["inference"]["summarization_model"]),
                        classification_labels=params["inference"]["classification_labels"],
                        intent_model=os.path.abspath(params["inference"]["intent_model"]),
                        intent_labels=params["inference"]["intent_labels"],
                        substance_model=os.path.abspath(params["inference"]["substance_model"]),
                        substance_labels=params["inference"]["substance_labels"],
                        io_model=os.path.abspath(params["inference"]["io_model"]),
                        io_labels=params["inference"]["io_labels"],
                        location_model=os.path.abspath(params["inference"]["location_model"]),
                        location_labels=params["inference"]["location_labels"],
                        area_model=os.path.abspath(params["inference"]["area_model"]),
                        area_labels=params["inference"]["area_labels"],
                        ampm_model=os.path.abspath(params["inference"]["am_pm_model"]),
                        ampm_labels=params["inference"]["am_pm_labels"],
                        embedding_model=params["inference"]["embedding_model"],
                        device=device)

# get model probabilities
print("[" + datetime.now().strftime("%Y/%m/%d %H:%M:%S") + "] " + "Classifying")

probs = inference.classify(inference_notes,
                             params["inference"]["note_col"],
                             params["inference"]["include_labels"])

inference_notes["probs"] = probs
inference_notes = inference_notes.sort_values(by=["probs"], ascending=False)
preprocessed_notes["Arrival Date"] = pd.to_datetime(preprocessed_notes["Arrival Date"], errors="coerce")
filter_date=preprocessed_notes["Arrival Date"].drop_duplicates().min()+pd.DateOffset(days=params["inference"]["time_delta"]).tolist()[0]

#prob cutoff uses the last 30 days, single day is not reliable to use, there is too much variability
prob_cutoff = inference.get_probs(database, start_date=filter_date, complaint_filter=params["inference"]["pos_complaints"])

if params["inference"]["use_chirpp"]:
    inference_notes["probs"][inference_notes[params["inference"]["chirpp_col"]] == "CHIRPP ICON"] = 1

# re-order because we just changed the probabilities
inference_notes["is_chirpp"] = inference_notes["probs"] >= prob_cutoff

# get summaries of positive cases
print("[" + datetime.now().strftime("%Y/%m/%d %H:%M:%S") + "] " + "Summarizing")

#this needs to change to use lllamacpp
summaries = inference.summarize(inference_notes,
                                  params["inference"]["note_col"],
                                  params["inference"]["truncation"],
                                  params["inference"]["max_length"])

if params['inference']['anonymize_summaries'] and not params["pre_process"]['anonymize']:
    new_summaries=[]
    for sumr, name in zip(summaries, inference_notes["Patient Name"].to_list()):
        deidentified=deidentify(sumr, params["pre_process"]["lang_model"], [name])
        new_summaries.append(deidentified)
    summaries=new_summaries

inference_notes["PHAC Narrative"] = summaries

print("[" + datetime.now().strftime("%Y/%m/%d %H:%M:%S") + "] " + "Classifying intent")

intent = inference.get_intent(notes=inference_notes[inference_notes["is_chirpp"]],
                                notes_col=params["inference"]["note_col"],
                                label_dict=params["inference"]["intent_label_dict"],
                                cutoff=params["inference"]["intent_cutoff"],
                                )
inference_notes["intent"] = None
inference_notes["intent"][inference_notes["is_chirpp"]] = intent

print("[" + datetime.now().strftime("%Y/%m/%d %H:%M:%S") + "] " + "Classifying substance use")

substance = inference.get_substance(notes=inference_notes[inference_notes["is_chirpp"]],
                                      notes_col=params["inference"]["note_col"],
                                      cutoff=params["inference"]["subs_cutoff"])
inference_notes["sub"] = None
inference_notes["sub"][inference_notes["is_chirpp"]] = substance

print("[" + datetime.now().strftime("%Y/%m/%d %H:%M:%S") + "] " + "Classifying inside/outside")

io=inference.get_io(notes=inference_notes[inference_notes["is_chirpp"]],
                          notes_col=params["inference"]["note_col"],
                          cutoff=params["inference"]["io_cutoff"])

inference_notes["io"]=None
inference_notes["io"][(inference_notes["is_chirpp"])] = io

print("[" + datetime.now().strftime("%Y/%m/%d %H:%M:%S") + "] " + "Classifying am/pm")

ampm=inference.get_ampm(notes=inference_notes[inference_notes["is_chirpp"]],
                          notes_col=params["inference"]["note_col"],
                          cutoff=params["inference"]["am_pm_cutoff"])

inference_notes["ampm"]=None
inference_notes["ampm"][(inference_notes["is_chirpp"])] = ampm

print("[" + datetime.now().strftime("%Y/%m/%d %H:%M:%S") + "] " + "Classifying Location")

location=inference.get_location(notes=inference_notes[inference_notes["is_chirpp"]],
                                      notes_col=params["inference"]["note_col"],
                                      cutoff=params["inference"]["location_cutoff"],
                                     label_dict=params["inference"]["location_label_dict"])

inference_notes["location"]=None
inference_notes["location"][inference_notes["is_chirpp"]] = location

print("[" + datetime.now().strftime("%Y/%m/%d %H:%M:%S") + "] " + "Classifying Area")

area=inference.get_area(notes=inference_notes[inference_notes["is_chirpp"]],
                              notes_col=params["inference"]["note_col"],
                              cutoff=params["inference"]["area_cutoff"],
                              label_dict=params["inference"]["area_label_dict"])
inference_notes["area"]=None
inference_notes["area"][inference_notes["is_chirpp"]] = area

# no neeed to calculate embeddings if we are not going to use them.

print("[" + datetime.now().strftime("%Y/%m/%d %H:%M:%S") + "] " + "Generating Embeddings")
embeddings=inference.get_embeddings(notes=inference_notes,
                                    notes_col=params["inference"]["note_col"])


# post processing to generate the final output
print("[" + datetime.now().strftime("%Y/%m/%d %H:%M:%S") + "] " + "Generating Report")

params["post_process"]["pos_complaints"] = params["inference"]["pos_complaints"]
params["post_process"]["terms_to_fix"] = params["pre_process"]["terms_to_fix"]
postprocess = PostProcess(preprocessed_notes.raw_notes, inference_notes, params["post_process"])
postprocess = postprocess.autofill()


#why not
print("[" + datetime.now().strftime("%Y/%m/%d %H:%M:%S") + "] " + "Creating Excel Report")
postprocess.create_report(args.outname)


#TODO this need to be refactored to always use the database

print("[" + datetime.now().strftime("%Y/%m/%d %H:%M:%S") + "] " + "Moving things to the database")

database.process_dump(preprocess.raw_notes)
database.process_report(postprocess.sheet2)
database.import_processed_notes(inference_notes["CSN"].tolist(),
                                inference_notes[params["inference"]["note_col"]].tolist(),
                                embeddings)

print("[" + datetime.now().strftime("%Y/%m/%d %H:%M:%S") + "] " + "Done!")
