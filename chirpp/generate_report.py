#! python

import argparse as arg
from datetime import datetime

import pandas as pd

from torch.cuda import is_available
from transformers import logging as hf_logging
from dotenv import dotenv_values
from sqlalchemy import create_engine

hf_logging.set_verbosity_error()

from chirpp.preprocess.preprocess import Preprocess, SectionRemover
from chirpp.preprocess.config import preprocess_config

from chirpp.inference.inference import Inference, LlamaCppServer, SemanticChunking

#TODO deal with postprocess
#TODO deal with database
from chirpp.database.database import DataBase
from chirpp.postprocess.postprocess import PostProcess

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
gpu=is_available()

if gpu:
    device = "cuda:0"
    from chirpp.inference.config_transformers import inference_config
else:
    device = "cpu"
    from chirpp.inference.config_llama import inference_config

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
merged_notes, processed_notes = preprocess.preprocess_pipeline()

# remove empty notes, there must be at least one triage note
inference_notes = processed_notes.copy()
inference_notes = inference_notes[~pd.isnull(inference_notes["processed_notes"])].copy()

#TODO this will need to be refactored to use gpu if available
llama_server=LlamaCppServer(binary_path=inference_config["server"]["binary_path"],
                            model_dict=inference_config["server"]["models"],)

chunker= SemanticChunking(chunking_model=inference_config["chunking"]["model"],
                          embedding_model=inference_config["embedding"]["model"],
                          chunk_size=inference_config["chunking"]["chunk_size"],
                          min_sentences=inference_config["chunking"]["min_sentences"],
                          threshold=inference_config["chunking"]["threshold"],)

inference=Inference(device=device, server=llama_server, chunker=chunker)

print("[" + datetime.now().strftime("%Y/%m/%d %H:%M:%S") + "] " + "Classifying")

#TODO this is not done, there was a bunch of mistakes in the previous commit.
probs=inference.run_pipeline(inference_config["pipelines"]["classification"], inference_notes["processed_notes"].tolist())

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

#TODO need to add model cleanup to all the llamacpp inference things, this will depend on how reliable the the models are when
# they are being used for inference via the openai api.
summaries=inference.server_inference("summarization", notes=inference_notes["processed_notes"])
summary_embeddings=inference.embed_notes(summaries, chunk=False)

inference_notes["PHAC Narrative"] = summaries
inference_notes["phac_embeddings"] = summary_embeddings

print("[" + datetime.now().strftime("%Y/%m/%d %H:%M:%S") + "] " + "Classifying intent")

pipeline=inference.load_pipeline(inference_config["pipelines"]["intent"]["model"],
                                 inference_config["pipelines"]["intent"]["num_labels"],)

intent=inference.run_pipeline(inference_notes["processed_notes"][inference_notes["is_chirpp"]].tolist(),
                    inference_config["pipelines"]["intent"]["labels"],
                    inference_config["pipelines"]["intent"]["cutoff"],)

inference_notes["intent"] = None
inference_notes["intent"][inference_notes["is_chirpp"]] = intent

print("[" + datetime.now().strftime("%Y/%m/%d %H:%M:%S") + "] " + "Classifying substance use")

substance=inference.server_inference("substance",
                                      notes=inference_notes["processed_notes"][inference_notes["is_chirpp"]].tolist())

inference_notes["substance"] = None
inference_notes["substance"][inference_notes["is_chirpp"]] = substance

print("[" + datetime.now().strftime("%Y/%m/%d %H:%M:%S") + "] " + "Classifying inside/outside")

io=inference.server_inference("io",
                              notes=inference_notes["processed_notes"]["is_chirpp"])
inference_notes["io"] = None
inference_notes["io"][inference_notes["is_chirpp"]] = io

print("[" + datetime.now().strftime("%Y/%m/%d %H:%M:%S") + "] " + "Classifying am/pm")

am_pm=inference.server_inference("am_pm",
                              notes=inference_notes["processed_notes"]["is_chirpp"])

inference_notes["am_pm"] = None
inference_notes["am_pm"][inference_notes["is_chirpp"]] = substance

print("[" + datetime.now().strftime("%Y/%m/%d %H:%M:%S") + "] " + "Classifying Location")

location=inference.server_inference("location",
                              notes=inference_notes["processed_notes"]["is_chirpp"])

inference_notes["location"]=None
inference_notes["location"][inference_notes["is_chirpp"]] = location

print("[" + datetime.now().strftime("%Y/%m/%d %H:%M:%S") + "] " + "Classifying Area")

area=inference.server_inference("area",
                              notes=inference_notes["processed_notes"]["is_chirpp"])

inference_notes["area"]=None
inference_notes["area"][inference_notes["is_chirpp"]] = area


### POSTPROCESS
#TODO this is waiting on selecting a good model for autofill

print("[" + datetime.now().strftime("%Y/%m/%d %H:%M:%S") + "] " + "Generating Report")

postprocess = PostProcess(merged_notes, inference_notes, params["post_process"])
postprocess = postprocess.autofill()


#why not
print("[" + datetime.now().strftime("%Y/%m/%d %H:%M:%S") + "] " + "Creating Excel Report")
postprocess.create_report(args.outname)
### POSTPROCESS

print("[" + datetime.now().strftime("%Y/%m/%d %H:%M:%S") + "] " + "Moving things to the database")

database.process_dump(preprocess.raw_notes)
database.process_report(postprocess.sheet2)

print("[" + datetime.now().strftime("%Y/%m/%d %H:%M:%S") + "] " + "Generating Embeddings for RAG")
database.import_processed_notes(processed_notes, inference.chunker)
database.import_chunked_notes(merged_notes, inference.chunker)

print("[" + datetime.now().strftime("%Y/%m/%d %H:%M:%S") + "] " + "Done!")
