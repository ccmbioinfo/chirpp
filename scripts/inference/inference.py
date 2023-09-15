import argparse as arg

import pandas as pd

from utils import Inference
import params


parser = arg.ArgumentParser(description='Run inference on processed notes')
parser.add_argument('-n', '--notes', type=str, help='Path to processed patient notes')
parser.add_argument('-o', '--outname', type=str, help='Path to outputs')
parser.add_argument('-d', '--device', type=str, help='which device to use defaults to cuda:0', default="cuda:0")
parser.add_argument('-c', '--classification_dir', type=str, help='path for the directory for the trained classification model')
parser.add_argument('-s', '--summarization_dir', type=str, help='path for the trained summarization model')
parser.add_argument('--distance_model_name', type=str, help='sentence transformers model to use to calculate cosine distance')
parser.add_argument('--distance_model_dir', type=str, help='sentence transformers model cache directory')
parser.add_argument('--cutoff', type=float, help='crude cutoff calculation to filter notes for summarization defaults '
                                                 'to 0.9 represents relative capture rate',
                    default=0.9)
parser.add_argument('--use_chirpp', help='whether to use the chirpp column as a positive case',
                    default=False, action="store_true")

args = parser.parse_args()

pre_processed_notes=pd.read_csv(args.notes, **params.read_args)
pre_processed_notes=pre_processed_notes[~pd.isnull(pre_processed_notes[params.note_col])]

# get model probabilities
infer_notes=Inference(args.classification_dir, args.summarization_dir, params.num_labels, args.device)
probs=infer_notes.classify(pre_processed_notes, params.note_col, params.include_labels)
pre_processed_notes["probs"]=probs
pre_processed_notes=pre_processed_notes.sort_values(by=["probs"], ascending=False)

# summary inference takes a long time, and I do not want to summarize all the notes. Here I will be looking at the
# distribution of definitely positive cases (assuming they are similarly distributed with other chirpp+ cases) and
# the % of them from the top, I will get a probability cutoff and then summarize everything that's above that prob

# get all the rows that contain a "definitiely chirpp" complaint
pre_processed_notes["pos_complaint"]=pre_processed_notes["Chief Complaint"].isin(params.pos_complaints)
pos_based_on_complaint=pre_processed_notes[pre_processed_notes["pos_complaint"]]
num_rows=pos_based_on_complaint.shape[0] # get the number of cases

# these are descending sorted so get the top cutoff (round the number just in case)
row_cutoff=round(num_rows*args.cutoff)-1

# get the model prob of that row, anything above that we will summarize
prob_cutoff=pos_based_on_complaint["probs"].tolist()[row_cutoff]
pre_processed_notes["probs"][pre_processed_notes["pos_complaint"]]=1

if args.use_chirpp:
    pre_processed_notes["probs"][pre_processed_notes[params.chirpp_col]=="CHIRPP ICON"] = 1

# re-order because we just changed the probabilities
pre_processed_notes=pre_processed_notes.sort_values(by=["probs"], ascending=False)
pre_processed_notes["to_summarize"]=pre_processed_notes["probs"]>prob_cutoff

summaries=infer_notes.summarize(pre_processed_notes[pre_processed_notes["to_summarize"]], params.note_col,
                                params.truncation, params.max_length)

distances=infer_notes.calculate_cosine_distances(args.distance_model, args.distance_model_dir,
                                                 pre_processed_notes[params.note_col][pre_processed_notes["to_summarize"]],
                                                 summaries)

pre_processed_notes["summary"]=None
pre_processed_notes["summary"][pre_processed_notes["to_summarize"]]=summaries
pre_processed_notes["cosine_similarity"][pre_processed_notes["to_summarize"]]=distances

#TODO generate the excel spreadsheet here




