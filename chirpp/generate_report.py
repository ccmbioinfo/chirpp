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

from chirpp.preprocess.preprocess import Preprocess, SectionRemover
from chirpp.preprocess.config import preprocess_config

from chirpp.inference.inference import Inference, LlamaCppServer, SemanticChunking
from chirpp.inference.config import inference_config
from chirpp.inference.prompts import *

#TODO deal with postprocess
#TODO deal with database
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

print("[" + datetime.now().strftime("%Y/%m/%d %H:%M:%S") + "] " + "Gathering requirements")


# there is an environment file that contains the database connection information, this is not to be pushed to the repo
env_values=dotenv_values(args.env_file)  

# check for gpu availability
if is_available():
    device = "cuda:0"
else:
    device = "cpu"

# preprocessing, remove unwanted sections and keep raw notes in memory
if "additional_rules" in list(preprocess_config.keys()):
    additional_rules = preprocess_config["additional_rules"]
else:
    additional_rules = None

# database connection this is essential for rag, non-db connections will not be supported
engine = create_engine('postgresql+psycopg2://{}:{}@{}:{}/{}'. \
                           format(env_values["DB_USER"],
                                  env_values["DB_PWD"],
                                  env_values["DB_HOST"],
                                  env_values["DB_PORT"],
                                  env_values["DB_NAME"]))

database=DataBase(engine)

print("[" + datetime.now().strftime("%Y/%m/%d %H:%M:%S") + "] " + "Preprocessing")

section_remover_for_inference = SectionRemover(lang_model="en_core_web_trf",
                                               remove_sections=preprocess_config["remove_sections"],
                                               keep_sections=preprocess_config["inference_sections"],
                                               rules_json=preprocess_config["section_rules"],
                                               additional_rules=additional_rules,
                                               gpu=device)

preprocess=Preprocess(args.notes, preprocess_config, section_remover_for_inference)
merged_notes= preprocess.preprocess_pipeline()

# remove empty notes, there must be at least one triage note
inference_notes = merged_notes.copy()
inference_notes = inference_notes[~pd.isnull(inference_notes[params["inference"]["note_col"]])].copy()

llama_server=LlamaCppServer(binary_path=["server"]["binary_path"],
                            host=inference_config["server"]["host"],
                            port=inference_config["server"]["port"],
                            model_dict=inference_config["server"]["models"],)

chunker= SemanticChunking(chunking_model=inference_config["chunking"]["model"],
                          embedding_model=inference_config["embedding"]["model"],
                          chunk_size=inference_config["chunking"]["chunk_size"],
                          min_sentences=inference_config["chunking"]["min_sentences"],
                          threshold=inference_config["chunking"]["threshold"],)

inference=Inference(device=device, server=llama_server, chunker=chunker)

print("[" + datetime.now().strftime("%Y/%m/%d %H:%M:%S") + "] " + "Classifying")
pipeline=inference.load_pipeline(inference_config["pipelines"]["classification"]["model"],
                                       inference_config["pipelines"]["classification"]["num_labels"],)

probs=inference.run(pipeline, inference_notes["Note Text"].tolist(),
                    inference_config["pipelines"]["classification"]["labels"],
                    inference_config["pipelines"]["classification"]["cutoff"],)

inference_notes["probs"] = probs
inference_notes = inference_notes.sort_values(by=["probs"], ascending=False)

inference_notes["Arrival Date"] = pd.to_datetime(inference_notes["Arrival Date"], errors="coerce")

# this is to go back in time and get notes so that we have enough cases and the probabilities are more stable
filter_date=inference_notes["Arrival Date"].drop_duplicates().min()+pd.DateOffset(days=inference_config["time_delta"]).tolist()[0]

#prob cutoff uses the last 30 days, single day is not reliable to use, there is too much variability
prob_cutoff = inference.get_probs(database, start_date=filter_date, complaint_filter=inference_config["pos_complaints"])

if inference_config["use_chirpp"]:
    inference_notes["probs"][inference_notes[inference_config["chirpp_col"]] == "CHIRPP ICON"] = 1

# re-order because we just changed the probabilities
inference_notes["is_chirpp"] = inference_notes["probs"] >= prob_cutoff

# get summaries for all notes

print("[" + datetime.now().strftime("%Y/%m/%d %H:%M:%S") + "] " + "Summarizing")

# model stuff is in the llama server model_dict, so we can just pass the model name
# one limitation is here that we can only use one model at a time, we start and stop the server with each model.
# this adds couple of minutes to the inference time.

summaries=inference.server_inference("summarization", sys_prompt=system_prompt,
                                      task_prompt=summary_prompt,
                                      notes=inference_notes["Note Text"],
                                      context=inference_config["server"]["context_length"],
                                      max_tokens=inference_config["server"]["summarization"]["max_tokens"],
                                      threads= inference_config["server"]["threads"],
                                      temperature=inference_config["server"]["summarization"]["temperature"],
                                      summary=True)

inference_notes["PHAC Narrative"] = summaries

print("[" + datetime.now().strftime("%Y/%m/%d %H:%M:%S") + "] " + "Classifying intent")

pipeline=inference.load_pipeline(inference_config["pipelines"]["intent"]["model"],
                                 inference_config["pipelines"]["intent"]["num_labels"],)

intent=inference.run(pipeline, inference_notes["Note Text"].tolist(),
                    inference_config["pipelines"]["intent"]["labels"],
                    inference_config["pipelines"]["intent"]["cutoff"],)

inference_notes["intent"] = None
inference_notes["intent"][inference_notes["is_chirpp"]] = intent

print("[" + datetime.now().strftime("%Y/%m/%d %H:%M:%S") + "] " + "Classifying substance use")

#TODO stopeed here need to fix the rest.
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
