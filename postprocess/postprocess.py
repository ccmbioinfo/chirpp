import os

import numpy as np
import pandas as pd

from .utils import *


class PostProcess:
    def __init__(self, raw_notes, inference_notes, params):
        """
        create a report template to be autofilled this contains all the cases and all the columns that needs to be
        filled, this template will then be split into 2 sheets to be saved as an excel file
        :param raw_notes: raw notes, this include everynote, this is basically the excel file
        :param inference_notes: this is the output of the intference section it includes a lot of stuff that will be used
        for autofill
        :param params:
        """
        self.params = params

        raw_notes["Arrival Date"] = pd.to_datetime(raw_notes["Arrival Date"])
        inference_notes["Arrival Date"] = pd.to_datetime(inference_notes["Arrival Date"])
        #inference_notes = inference_notes.rename(columns={"Note Text": "pre_processed"})
        inference_notes = inference_notes[['MRN', 'Arrival Date', 'probs', 'to_summarize', 'PHAC Narrative',
                                           'cosine_similarity', 'is_injury', 'is_inside', 'is_sports', 'inside_prob',
                                           'sports_prob', 'pre_processed']]
        merged = raw_notes.merge(inference_notes, how="inner", on=["MRN", "Arrival Date"])
        merged["Arrival Time"]=pd.to_datetime(merged["Arrival Time"])
        merged = merged.groupby(["CSN", "MRN", "Arrival Date", "Arrival Time"])

        report_df = pd.DataFrame(columns=self.params["report_header"])

        template = []
        for _, data in merged:
            group_df = report_df.copy()
            group_df["POSTAL"] = data["Postal Code"].apply(process_postal).drop_duplicates()
            group_df["SEX"] = data["Sex"].apply(process_sex).drop_duplicates()
            group_df["MRN"] = data["MRN"].drop_duplicates()
            group_df["ScrMRN"] = data["MRN"].apply(scramble_mrn).drop_duplicates()
            group_df["DOB"] = pd.to_datetime(data["Date of Birth"]).apply(
                lambda x: x.strftime('%Y-%m-%d')).drop_duplicates()
            group_df["ER Date"] = pd.to_datetime(data["Arrival Date"]).dt.strftime('%Y-%m-%d').drop_duplicates()
            group_df["ER Time"] = data["Arrival Time"].apply(lambda x: x.strftime('%H:%M')).drop_duplicates()
            group_df["CTAS"] = data["CTAS"].apply(lambda x: int(x) if not np.isnan(x) else "").drop_duplicates()
            group_df["Chief Complaint"] = data["Chief Complaint"].drop_duplicates()
            group_df["W4P"] = 0  # this is hardcoded because it almost never happens
            group_df["Notes"] = get_report_note(data)
            #group_df["LOS"] = data["Length of Stay (Hours)"].drop_duplicates()
            group_df["Diagnosis"] = data["Diagnosis"].drop_duplicates()
            group_df["probs"] = data["probs"].drop_duplicates()
            group_df["Problem List"]=data["Problem List"].drop_duplicates()
            group_df["cosine_similarity"]=data["cosine_similarity"].drop_duplicates()
            group_df["PHAC Narrative"] = data["PHAC Narrative"].drop_duplicates()
            inside=data["is_inside"].drop_duplicates().to_list()[0]
            if inside:
                io=1
            else:
                io=2
            group_df["I/O"] =io
            narrative = []
            texts=[str(text) for text in data["Note Text"].to_list()]
            for note_type, note_text in zip(data["Note Type"].tolist(), texts):
                if note_type in self.params["note_types"]:
                    if not pd.isna(note_text):
                        narrative.append(note_type + "\n\n" + note_text)
            narrative = "\n\n".join(narrative)
            group_df["SK Narrative"] = narrative
            group_df["Disposition"]=data['Disposition'].drop_duplicates().astype(str)
            group_df["pre_processed"]=data["pre_processed"].drop_duplicates().astype(str)
            group_df.fillna('')
            template.append(group_df)
        template = pd.concat(template)

        self.template = template
        self.sheet1 = self.template[pd.isna(self.template["cosine_similarity"])]
        self.sheet2 = self.template[~pd.isna(self.template["cosine_similarity"])]

    # TODO add devices, sports_code, vehicles
    def autofill(self):
        complaints = self.sheet2["Chief Complaint"].to_list()
        notes = self.sheet2["pre_processed"].to_list()
        problems = self.sheet2["Problem List"].to_list()
        diags = self.sheet2["Diagnosis"]
        merged_notes = self.sheet2["Notes"].to_list()
        dispositions = self.sheet2["Disposition"].to_list()

        autofill_cols = {
            "sub": [],
            "subID": [],
            "NO1": [],
            "BP1": [],
            "DISP": [],
            "IN": [],
        }

        for complaint, note, problem, diag, disp in zip(complaints, notes, problems, diags, dispositions):
            substance, has_substance = get_substances(note, complaint, problem, diag,
                                                      self.params["cc_filter"],
                                                      self.params["diag_pl_filter"])

            diag = str(diag).lower()
            no, bp = injuries(diag)

            report_disposition = get_disposition(merged_notes, disp)

            autofill_cols["sub"].append(has_substance)
            autofill_cols["subID"].append(substance)
            autofill_cols["NO1"] = no
            autofill_cols["BP1"] = bp
            autofill_cols["DISP"] = report_disposition

        autofill_cols["IN"] = get_intent(self.sheet2, self.params["intent_filters"], self.params["intent_order"])

        for key in autofill_cols.keys():
            self.sheet2[key] = autofill_cols[key]

        return self

    def create_report(self, path, overwrite=False):
        """
        write the report to file
        :param path: path for the file
        :param overwrite: whether to write the file if it exisist
        :return: nothing
        """
        if os.path.exists(path) and not overwrite:
            raise FileExistsError("{} already exisits".format(path))

        self.sheet2=self.sheet2.drop(columns=["pre_processed", "Disposition"])

        with pd.ExcelWriter(path) as out:
            self.sheet1.to_excel(out, sheet_name="Sheet 1", index=False)
            self.sheet2.to_excel(out, sheet_name="Sheet 2", index=False)
