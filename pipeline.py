import argparse as arg

import pandas as pd
import yaml

from inference.inference import Inference
from preprocess.preprocess import SectionRemover, Preprocess
from postprocess.postprocess import PostProcess

# from postprocess.report_processing import create_report

parser = arg.ArgumentParser(description='Preprocess notes file for inference')
parser.add_argument('-n', '--notes', type=str, help='Path to raw patient notes')
parser.add_argument('-o', '--outname', type=str, help='Path to outputs')
parser.add_argument('-c', '--config', type=str, help='config file in yaml format', default="config.yaml",
                    action="store")

args = parser.parse_args()

with open(args.config) as f:
    params = yaml.safe_load(f)

# preprocessing, remove unwanted sections and keep raw notes in memory
if "additional_rules" in list(params["pre_process"].keys()):
    additional_rules = params["pre_process"]["additional_rules"]
else:
    additional_rules = None

section_remover_for_inference = SectionRemover(lang_model=params["pre_process"]["lang_model"],
                                               remove_sections=params["pre_process"]["remove_sections"],
                                               keep_sections=params["pre_process"]["inference_sections"],
                                               rules_json=params["pre_process"]["section_rules"],
                                               additional_rules=additional_rules,
                                               gpu=params["pre_process"]["device"])

# remove sections and generate inference notes these will be used for inference
preprocessed_notes = Preprocess(args.notes, params["pre_process"]["terms_to_fix"])

preprocessed_notes = preprocessed_notes.read_raw_notes()

preprocessed_notes = preprocessed_notes.get_relevant_notes(filters=params["pre_process"]["note_types"],
                                                           additional_columns=params["pre_process"]["include__cols"])
## Inference
preprocessed_notes = preprocessed_notes.merge_notes(section_remover_for_inference,
                                                 params["pre_process"]["include_cols"],
                                                 params["pre_process"]["group_cols"],
                                                 params["pre_process"]["orientation"],
                                                 keep_unlabelled=True)
#TODO there probably is a better way than to create a copy
inference_notes=preprocessed_notes.merged_raw.copy()

inference_notes = inference_notes[~pd.isnull(inference_notes[params["inference"]["note_col"]])].copy()

# set up inference instance
infer_notes = Inference(classification_model=params["inference"]["classification_model"],
                        summarization_model=params["inference"]["summarization_model"],
                        zshot_model=params["inference"]["zshot_model"],
                        num_labels=params["inference"]["num_labels"],
                        device=params["pre_process"]["device"])  # device should probably be a global param

# get model probabilities
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
inference_notes = inference_notes.sort_values(by=["probs"], ascending=False)
inference_notes["to_summarize"] = inference_notes["probs"] >= params["inference"]["cutoff"]

# get summaries of positive cases
summaries = infer_notes.summarize(inference_notes[inference_notes["to_summarize"]],
                                  params["inference"]["note_col"],
                                  params["inference"]["truncation"],
                                  params["inference"]["max_length"])

distances = infer_notes.calculate_cosine_distances(params["inference"]["distance_model"],
                                                   inference_notes[params["inference"]["note_col"]][
                                                   inference_notes["to_summarize"]],
                                                   summaries)
is_injury = infer_notes.is_injury(inference_notes["Diagnosis"][inference_notes["to_summarize"]].astype(str),
                                  params["inference"]["inj_list"])

is_sports = infer_notes.zshot(
    inference_notes[params["inference"]["note_col"]][inference_notes["to_summarize"]].to_list(),
    candidate_labels=params["inference"]["sports_labels"])

is_inside = infer_notes.zshot(
    inference_notes[params["inference"]["note_col"]][inference_notes["to_summarize"]].to_list(),
    candidate_labels=params["inference"]["io_labels"])

# to be used in autofill
inference_notes["PHAC Narrative"] = None
inference_notes["cosine_similarity"]=None
inference_notes["is_injury"]=None
inference_notes["is_inside"]=None
inference_notes["inside_prob"]=None
inference_notes["is_sports"]=None
inference_notes["sports_prob"]=None

inference_notes["PHAC Narrative"][inference_notes["to_summarize"]] = summaries
inference_notes["cosine_similarity"][inference_notes["to_summarize"]] = distances
inference_notes["is_injury"][inference_notes["to_summarize"]] = is_injury

#TODO the check needs to refer to the config yaml and that needs to be a dict
inference_notes["is_inside"][inference_notes["to_summarize"]] = [[False if item=="indoors" else True for item in is_inside[0]]]
inference_notes["inside_prob"][inference_notes["to_summarize"]] = [item for item in is_inside[1]]
inference_notes["is_sports"][inference_notes["to_summarize"]] = [False if item=="not involving sports" else True for item in is_sports[0]]
inference_notes["sports_prob"][inference_notes["to_summarize"]] = [item for item in is_sports[1]]

# post processing to generate the final output

postprocess=PostProcess(preprocessed_notes.raw_notes, inference_notes, params["postprocess"])
postprocess=postprocess.autofill()
postprocess.create_report(args.outname)