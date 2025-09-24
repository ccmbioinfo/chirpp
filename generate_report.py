#! python
import argparse as arg
from datetime import datetime

import yaml

from torch.cuda import is_available
from transformers import logging as hf_logging
from dotenv import dotenv_values
from sqlalchemy import create_engine

hf_logging.set_verbosity_error()

from chirpp.preprocess.preprocess import Preprocess, SectionRemover
from chirpp.inference.inference import *

from chirpp.database.database import DataBase
from chirpp.postprocess.postprocess import PostProcess

# we will not be generating anymore excel outputs so there is no to_excel option
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

print("[" + datetime.now().strftime("%Y/%m/%d %H:%M:%S") + "] " + "Preprocessing notes for inference")

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

print("[" + datetime.now().strftime("%Y/%m/%d %H:%M:%S") + "] " + "Running inference pipeline, this may take a while")

inference_config=config["inference"]
inference=Inference(inference_config, device=device)

# this is the inference pipeline just going throught the columns one by one
cutoff=get_probs(database, merged_notes["Arrival Date"].min(), #get the previous montth
                 inference_config["pos_complaints"], time_delta=inference_config["time_delta"])

print("[" + datetime.now().strftime("%Y/%m/%d %H:%M:%S") + "] " + "Running chirpp classifcation")

processed_notes["probs"]=inference.classify(processed_notes["processed_notes"])

print("[" + datetime.now().strftime("%Y/%m/%d %H:%M:%S") + "] " + "Summarizing notes")
processed_notes["summary"]=inference.summarize(processed_notes["processed_notes"])

print("[" + datetime.now().strftime("%Y/%m/%d %H:%M:%S") + "] " + "Calculating embeddings for semantic search")
processed_notes["embeddings"]=inference.embed(processed_notes["processed_notes"])


# fill in columns because only chirpp cases will be inferred
processed_notes["intent"]=None
processed_notes["subs"]=None
processed_notes["sub_ids"]=None
processed_notes["io"]=None
processed_notes["location"]=None
processed_notes["area"]=None
processed_notes["date"]=None
processed_notes["hr"]=None
processed_notes["min"]=None
processed_notes["ampm"]=None
processed_notes["sports"]=None
processed_notes["sd1"]=None
processed_notes["sd2"]=None
processed_notes["sd3"]=None
processed_notes["sd4"]=None
processed_notes["sd5"]=None

# determine which notes are chirpp
processed_notes["is_chirpp"]=processed_notes["probs"]>=cutoff
notes_to_process=processed_notes["processed_notes"][processed_notes["is_chirpp"]]

print("[" + datetime.now().strftime("%Y/%m/%d %H:%M:%S") + "] " + "Classiftying intent")
intents=inference.intent(notes_to_process)

print("[" + datetime.now().strftime("%Y/%m/%d %H:%M:%S") + "] " + "Extracting substance use information")
subs, sub_ids=inference.substance(notes_to_process)

print("[" + datetime.now().strftime("%Y/%m/%d %H:%M:%S") + "] " + "Extracting safety devices information and sports involvement")
sd1, sd2, sd3, sd4, sd5 = inference.safety(notes_to_process)
sports=inference.sports(notes_to_process)

print("[" + datetime.now().strftime("%Y/%m/%d %H:%M:%S") + "] " + "Extracting location information")
area=inference.area(notes_to_process)
location=inference.location(notes_to_process)
io=inference.io(notes_to_process)

print("[" + datetime.now().strftime("%Y/%m/%d %H:%M:%S") + "] " + "Extracting date and time information")
hr, min = inference.time(notes_to_process)
date=inference.date(notes_to_process)
ampm=inference.ampm(notes_to_process)

#weirdly the time is more reliable than the ampm so we will use it and replace values
for i in range(len(ampm)):
    if hr[i] is not None and hr[i]<12:
        ampm[i]=1
    elif hr[i] is not None and 12 <= hr[i] <= 23:
        ampm[i]=2

# fill it in
processed_notes["intent"][processed_notes["is_chirpp"]]=intents
processed_notes["subs"][processed_notes["is_chirpp"]]=subs
processed_notes["sub_ids"][processed_notes["is_chirpp"]]=sub_ids
processed_notes["io"][processed_notes["is_chirpp"]]=io
processed_notes["hr"][processed_notes["is_chirpp"]]=hr
processed_notes["min"][processed_notes["is_chirpp"]]=min
processed_notes["date"][processed_notes["is_chirpp"]]=date
processed_notes["ampm"][processed_notes["is_chirpp"]]=ampm
processed_notes["area"][processed_notes["is_chirpp"]]=area
processed_notes["location"][processed_notes["is_chirpp"]]=location
processed_notes["sports"][processed_notes["is_chirpp"]]=sports
processed_notes["sd1"][processed_notes["is_chirpp"]]=sd1
processed_notes["sd2"][processed_notes["is_chirpp"]]=sd2
processed_notes["sd3"][processed_notes["is_chirpp"]]=sd3
processed_notes["sd4"][processed_notes["is_chirpp"]]=sd4
processed_notes["sd5"][processed_notes["is_chirpp"]]=sd5

# the order of the notes in the merged notes should be the same as when they are dumped in the db
for note in merged_notes["Note Text"]:
    chunks=inference.chunk(note)
    chunk_embeddings=inference.embed(chunks)

#### POSTPROCESSING #####
# TODO

#### ADD TO DATABASE #####

print("[" + datetime.now().strftime("%Y/%m/%d %H:%M:%S") + "] " + "Done!")
