import os
import argparse as arg

import pandas as pd

from utils import *
import params

from utils import Postprocess

parser = arg.ArgumentParser(description="Generate chirpp report")
parser.add_argument('-n', '--notes', type=str, help='Path to raw patient notes')
parser.add_argument('-i', '--inferred', type=str, help='Path to inferred notes')
# parser.add_argument('-a', '--autofill', type=str, help='Path to processed notes for autofill')
# parser.add_argument('-c', '--census_file', type=str, help='Path to census file')
parser.add_argument('-o', '--outname', type=str, help='Path to outputs')
args = parser.parse_args()

all_notes = pd.read_excel(args.notes, header=0)

inference_notes = pd.read_csv(args.inferred, header=0, sep="\t")
inference_notes = inference_notes[["CSN", "MRN", "Arrival Date", "probs", "summary", "cosine_similarity"]]

all_notes["Arrival Date"] = pd.to_datetime(all_notes["Arrival Date"])
all_notes["Arrival Time"] = pd.to_datetime(all_notes["Arrival Time"])
inference_notes["Arrival Date"] = pd.to_datetime(inference_notes["Arrival Date"])

all_notes["Note Text"] = all_notes["Note Text"].astype(str)
all_notes["Disposition"] = all_notes["Disposition"].astype(str)



report_df = create_report(all_notes, inference_notes,
                          params.REPORT_HEADER, params.note_types)
report_df.sort_values(by="probs", inplace=True, ascending=False)

sheet1 = report_df[pd.isna(report_df["cosine_similarity"])]
sheet2 = report_df[~pd.isna(report_df["cosine_similarity"])]

with pd.ExcelWriter(args.outname) as out:
    sheet1.to_excel(out, sheet_name="Sheet 1", index=False)
    sheet2.to_excel(out, sheet_name="Sheet 2", index=False)

    alvaroalon2/biobert_chemical_ner