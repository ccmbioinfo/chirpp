
import spacy_transformers
import pandas as pd
from chirpp.postprocess.utils import *
from chirpp.database.utils import calculate_age

#TODO this needs to be refactored to utils so I can use it on database prepare report
class PostProcess:
    def __init__(self, raw_notes, inference_notes, params):
        """
        create a report template to be autofilled this contains all the cases and all the columns that needs to be
        filled, this template will then be split into 2 sheets to be saved as an excel file
        :param raw_notes: raw notes, this includes everynote, this is basically the excel file
        :param inference_notes: this is the output of the intference section it includes a lot of stuff that will be used
        for autofill
        :param params: params from config.yaml
        """
        self.params = params

        raw_notes["Arrival Date"] = pd.to_datetime(raw_notes["Arrival Date"])
        raw_notes["Date of Birth"] = pd.to_datetime(raw_notes["Date of Birth"])
        inference_notes["Arrival Date"] = pd.to_datetime(inference_notes["Arrival Date"])
        inference_notes = inference_notes.rename(columns={"Note Text": "pre_processed"})
        inference_notes = inference_notes[['CSN',  'probs', 'is_chirpp', 'PHAC Narrative',
                                           'pre_processed', 'io', 'intent', 'sub',
                                           'location', 'area', 'ampm', 'has_sd']]
        merged = raw_notes.merge(inference_notes, how="inner", on=["CSN"])
        merged["Arrival Time"] = pd.to_datetime(merged["Arrival Time"].astype(str))
        merged = merged.groupby(["MRN", "Arrival Date", "Arrival Time"])

        report_df = pd.DataFrame(columns=self.params["report_header"])

        template = []
        for _, data in merged:
            group_df = report_df.copy()
            group_df["POSTAL"] = data["Postal Code"].apply(process_postal).drop_duplicates()
            group_df["SEX"] = data["Sex"].apply(process_sex).drop_duplicates()
            group_df["MRN"] = data["MRN"].drop_duplicates()
            group_df["CSN"] = data["CSN"].drop_duplicates()
            group_df["ScrMRN"] = data["MRN"].apply(scramble_mrn).drop_duplicates()
            group_df["DOB"] = pd.to_datetime(data["Date of Birth"]).apply(
                lambda x: x.strftime('%Y-%m-%d')).drop_duplicates()
            group_df["AGE"] = calculate_age(data["Arrival Date"].drop_duplicates().tolist()[0],
                                            data["Date of Birth"].drop_duplicates().tolist()[0])
            group_df["ER Date"] = pd.to_datetime(data["Arrival Date"]).dt.strftime('%Y-%m-%d').drop_duplicates()
            group_df["ER Time"] = data["Arrival Time"].apply(lambda x: x.strftime('%H:%M')).drop_duplicates()
            group_df["CTAS"] = data["CTAS"].apply(process_ctas).drop_duplicates()
            group_df["Chief Complaint"] = data["Chief Complaint"].drop_duplicates()
            group_df["W4P"] = 0  # this is hardcoded because it almost never happens
            group_df["Notes"] = get_report_note(data)
            group_df["LOS"] = data["LOS"].drop_duplicates()
            group_df["Diagnosis"] = data["Diagnosis"].drop_duplicates()
            group_df["probs"] = data["probs"].drop_duplicates()
            group_df["Problem List"] = data["Problem List"].drop_duplicates()
            group_df["is_chirpp"] = data["is_chirpp"].drop_duplicates()
            group_df["PHAC Narrative"] = data["PHAC Narrative"].drop_duplicates()
            group_df["I/O"] = data["io"].drop_duplicates()
            group_df["IN"] = data["intent"]
            group_df["sub"] = data["sub"]
            group_df["AREA"]=data["area"]
            group_df["LOCATION"]=data["location"]
            group_df["AM/PM"]=data["ampm"]
            group_df["has_sd"]=data["has_sd"]

            for_narrative = data[data["Note Type"].isin(self.params["note_types"])]
            for_narrative["Note Type"] = pd.Categorical(for_narrative["Note Type"],
                                                        categories=self.params["note_types"])
            for_narrative = for_narrative.sort_values(by="Note Type")
            narrative = []
            for note_type, note_text in zip(for_narrative["Note Type"].tolist(), for_narrative["Note Text"].tolist()):
                if not pd.isna(note_text):
                    narrative.append(str(note_type) + "\n\n" + str(note_text))
            narrative = "\n\n".join(narrative)
            group_df["SK Narrative"] = narrative
            group_df["Disposition"] = data['Disposition'].drop_duplicates().astype(str)
            group_df["pre_processed"] = data["pre_processed"].drop_duplicates().astype(str)
            group_df.fillna('')
            template.append(group_df)
        template = pd.concat(template)

        self.template = template

        self.sheet1 = self.template[~self.template["is_chirpp"]]
        self.sheet2 = self.template[self.template["is_chirpp"]]

    # TODO sd1-5, place, Inj date, Inj time, sports code
    def autofill(self):
        """
        autofills couple of columns using the functions from utils,
        the current columns are NO1, BP1, disposotion and substance id
        :return: returns self with the sheet2 filled in
        """
        complaints = self.sheet2["Chief Complaint"].to_list()
        notes = self.sheet2["pre_processed"].to_list()
        diags = self.sheet2["Diagnosis"].to_list()
        merged_notes = self.sheet2["Notes"].to_list()
        dispositions = self.sheet2["Disposition"].to_list()
        has_substance = self.sheet2["sub"].to_list()
        has_device=self.sheet2["has_sd"].to_list()

        autofill_cols = {
            "subID": [],
            "NO1": [],
            "BP1": [],
            "DISP": [],
            "sd1": [],
            "sd2": [],
            "sd3": [],
            "sd4": [],
            "sd5": [],
        }
        safety_cols = ["sd1", "sd2", "sd3", "sd4", "sd5"]

        for complaint, note, merged, diag, disp, has_sub, has_sd in zip(complaints, notes, merged_notes, diags,
                                                                dispositions, has_substance, has_device):
            diag = str(diag).lower()
            if complaint == "Medical Device Problem":
                no1 = 99
                bp1 = 999
            else:
                no1, bp1 = injuries(diag)
            report_disposition = get_disposition(merged, disp, no1, bp1, complaint)
            subid = get_substances(note, has_sub)
            devices=get_devices(note, has_sd)
            i=0
            while i <= 4:
                if i <= len(devices)-1:
                    autofill_cols[safety_cols[i]].append(devices[i])
                else:
                    autofill_cols[safety_cols[i]].append(None)
                i+=1

            autofill_cols["NO1"].append(no1)
            autofill_cols["BP1"].append(bp1)
            autofill_cols["subID"].append(subid)
            autofill_cols["DISP"].append(report_disposition)

        for key in autofill_cols.keys():
            self.sheet2[key] = autofill_cols[key]

        return self

    def create_report(self, path, overwrite=False):
        """
        write report to excel
        :param path: path of the file
        :param overwrite: whether to replace the file or noe
        :return: None, unless there is an error raised by pandas
        """
        if os.path.exists(path) and not overwrite:
            raise FileExistsError("{} already exisits".format(path))

        self.sheet1 = self.sheet1.drop(columns=["pre_processed", "Disposition", "is_chirpp", "probs", "has_sd"])
        self.sheet2 = self.sheet2.drop(columns=["pre_processed", "Disposition", "is_chirpp", "probs", "has_sd"])

        self.sheet2=touchups(self.sheet2)

        with pd.ExcelWriter(path) as out:
            self.sheet1.to_excel(out, sheet_name="Sheet 1", index=False)
            self.sheet2.to_excel(out, sheet_name="Sheet 2", index=False)
