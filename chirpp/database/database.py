from datetime import datetime

import pandas as pd

from sqlalchemy import MetaData, select, insert
from sqlalchemy.orm import sessionmaker

from chirpp.postprocess.utils import process_postal


# a lot of the methods rely on other functions returning errors, in this instance I think it makes sense because most of
# these are just sql queries, so we can just return the error message and let the user handle it.
class DataBase:
    """
    this is the base database class to add/update notes, I'm not sure if we will ever remove them, we might remove
    from the notes section
    """

    def __init__(self, engine):
        self.engine = engine
        self.meta = MetaData(bind=self.engine)
        self.meta.reflect(bind=self.engine)
        session = sessionmaker(self.engine)
        self.session=session()
        self.tables = self.meta.tables
        self.get_mrns()
        self.get_csns()

    def get_mrns(self):
        mrns = select(self.tables["patients"].c.mrn)
        self.mrns = [item[0] for item in self.session.execute(mrns).fetchall()]

    def get_csns(self):
        csns = select(self.tables["visits"].c.csn)
        self.csns = [item[0] for item in self.session.execute(csns).fetchall()]

    #TODO need version updates
    def to_db(self, patients, visits, referrals, problems, notes_df, chunked_notes, summaries, processed_notes, cases):
        """
        add data to the database
        :param patients: a pandas dataframe of patients
        :param visits: a pandas dataframe of visits
        :param referrals: a pandas dataframe of referrals
        :param problems: a pandas dataframe of problems
        :param notes_df: a pandas dataframe of notes
        :param chunked_notes: a pandas dataframe of chunked notes
        :param summaries: a pandas dataframe of summaries
        :param processed_notes: a pandas dataframe of processed notes
        :param cases: a pandas dataframe of cases
        :return: None or an error message
        """
        patients_table = self.tables["patients"]
        visits_table = self.tables["visits"]
        referrals_table = self.tables["referrals"]
        problems_table = self.tables["problems"]
        notes_table = self.tables["notes"]
        chunked_notes_table = self.tables["chunked_notes"]
        summaries_table = self.tables["summaries"]
        processed_notes_table = self.tables["processed_notes"]
        cases_table = self.tables["chirpp_report"]


        with self.engine.begin() as conn:
            # patients
            new_patients = patients[~patients["mrn"].isin(self.mrns)]
            if not new_patients.empty:
                conn.execute(insert(patients_table), new_patients.to_dict(orient="records"))
                self.get_mrns()

            # visits
            new_visits = visits[~visits["csn"].isin(self.csns)]
            if not new_visits.empty:
                conn.execute(insert(visits_table), new_visits.to_dict(orient="records"))
                self.get_csns()

            # referrals
            if not referrals.empty:
                conn.execute(insert(referrals_table), referrals.to_dict(orient="records"))

            # problems
            if not problems.empty:
                conn.execute(insert(problems_table), problems.to_dict(orient="records"))

            # notes
            if not notes_df.empty:
                conn.execute(insert(notes_table), notes_df.to_dict(orient="records"))

            # chunked notes
            if not chunked_notes.empty:
                conn.execute(insert(chunked_notes_table), chunked_notes.to_dict(orient="records"))

            # summaries
            if not summaries.empty:
                conn.execute(insert(summaries_table), summaries.to_dict(orient="records"))

            # processed notes
            if not processed_notes.empty:
                conn.execute(insert(processed_notes_table), processed_notes.to_dict(orient="records"))

            # cases
            if not cases.empty:
                conn.execute(insert(cases_table), cases.to_dict(orient="records"))

        conn.close()
        return None

    # use this to pass a set of raw reports, this will be a bunch of joins
    # I need to select Triage and ED Provider notes from the database and pass it ot generate report
    def get_raw(self, start, end):
        visits_table = self.tables["visits"]
        problems_table = self.tables["problems"]
        referrals_table = self.tables["referrals"]
        notes_table = self.tables["notes"]
        patients_table = self.tables["patients"]

        visits = self.session.execute(select(visits_table).where((visits_table.c.arrival_date >= start) &
                                                                 (visits_table.c.arrival_date <= end))).fetchall()
        visits = pd.DataFrame(visits)
        mrns = visits["mrn"].to_list()
        csns = visits["csn"].to_list()

        patients = pd.DataFrame(self.session.execute(select(patients_table). \
                                                     where(patients_table.c.mrn.in_(mrns))). \
                                fetchall())

        referrals = pd.DataFrame(self.session.execute(select(referrals_table). \
                                                      where(referrals_table.c.csn.in_(csns))).fetchall()). \
            drop(columns="id")

        notes = pd.DataFrame(self.session.execute(select(notes_table). \
                                                  where(notes_table.c.csn.in_(csns))).fetchall()). \
            drop(columns="id")

        problems = pd.DataFrame(self.session.execute(select(problems_table). \
                                                     where(problems_table.c.csn.in_(csns))).fetchall())

        problems_grouped = problems.groupby("csn")
        merged_probs = []
        for _, group in problems_grouped:
            merged_probs.append(",".join(group["problem"].to_list()))

        problems = problems.drop(columns=["problem", "id"]).drop_duplicates()
        problems["problem_list"] = merged_probs

        visits = visits.merge(patients, how="left", on="mrn")
        visits = visits.merge(referrals, how="left", on="csn")
        visits = visits.merge(notes, how="left", on="csn")
        visits = visits.merge(problems, how="left", on="csn")
        visits = visits[["csn", "mrn", "sex", "dob", "age", "postal_code", "arrival_date",
                         "arrival_time", "los", "chief_complaint", "problem_list", "diagnosis",
                         "ctas", "referrals", "note_type", "author_type", "author_service",
                         "note_text", 'address', 'city', 'province', 'disposition', 'ctas', ]]

        visits = visits.rename(columns={
            "csn": "CSN", "mrn": 'MRN', 'sex': 'Sex', 'dob': 'Date of Birth', 'age': 'Age (Years)',
            'arrival_date': 'Arrival Date', 'arrival_time': 'Arrival Time', 'address': 'Address',
            'city': 'City', 'province': 'Province', 'postal_code': 'Postal Code',
            'chief_complaint': 'Chief Complaint', 'problem_list': 'Problem List', 'los': 'LOS',
            'disposition': 'Disposition', 'referrals': 'Referral Order', 'diagnosis': "Diagnosis",
            'ctas': 'CTAS', 'note_type': 'Note Type', 'author_type': 'Author Type',
            'author_service': 'Author Service', 'note_text': 'Note Text',
        })

        # this is there to keep up apparences, because these columns are sometimes used in the generate_report.py
        # they are not crucial to the report generation but are there for additional features and selection methods
        if "LINE" not in visits.columns:
            visits["LINE"] = 1

        if "CHIRPP Icon" not in visits.columns:
            visits["CHIRPP Icon"] = None

        if "Patient Name" not in visits.columns:
            visits["Patient Name"] = None

        return visits

    def get_report(self, start, end):
        """
        generate a report from the database
        :param start: a datetime.datetime
        :param end: a datetime.datetime
        :return: a pandas dataframe
        """
        case_table = self.tables["chirpp_report"]
        visit_table = self.tables["visits"]
        problems_table = self.tables["problems"]
        patients_table = self.tables["patients"]

        visits = self.session.execute(select(visit_table).where((visit_table.c.arrival_date >= start) &
                                                                (visit_table.c.arrival_date <= end))).fetchall()
        visits = pd.DataFrame(visits)

        cases = self.session.execute(select(case_table).where(case_table.c.csn.in_(visits["csn"].to_list()))). \
            fetchall()
        cases = pd.DataFrame(cases)
        cases["chirpp"] = True

        patients = self.session.execute(select(patients_table). \
                                        where(patients_table.c.mrn.in_(visits["mrn"].to_list()))).fetchall()
        patients = pd.DataFrame(patients)

        problems = self.session.execute(select(problems_table). \
                                        where(problems_table.c.csn.in_(visits["csn"].to_list()))).fetchall()
        problems = pd.DataFrame(problems)

        problems_merged = []
        problems_grouped = problems.groupby("csn")
        for _, group in problems_grouped:
            problems_merged.append(",".join(group["problem"].to_list()))

        new_problems_df = pd.DataFrame({"csn": problems["csn"].drop_duplicates(), "problem_list": problems_merged})

        sheet1, sheet2 = self._prepare_report(visits, cases, patients, new_problems_df)
        return sheet1, sheet2

    # TODO this is not implemented yet, we need to figure out how to update the raw data, or if needed at all
    # I do not think we will ever use this
    def update_raw(self, txt_file):
        pass

    # TODO this is not implemented yet, I need to figure out versioning
    def update_report(self, excel_file, col_dict):
        """
        here the assumption is that the sheet 2 is always the cases, and it is always the second sheet.
        :param excel_file:
        :return:
        """
        pass

    #TODO I need to have a date selection I cannot get visits from the future
    def previous_visits(self, mrns, end_date=None):
        """
        get previous visits for a patient
        :param mrn: a list of mrns to get previous visits for
        :return: return a list of csns and phac narratives for the patient, currently looking
        """
        visits_table = self.tables["visits"]

        previous_visits = self.session.execute(
            select(visits_table.c.mrn, visits_table.c.csn, visits_table.c.phac_narrativie). \
            where((visits_table.c.mrn.in_(mrns)) & (visits_table.c.arrival_date < end_date if end_date else True)
                  )). \
            fetchall()

        previous_visits = pd.DataFrame(previous_visits).groupby(["mrn"])
        visit_texts = []
        for mrn in mrns:
            patient_visits = previous_visits[previous_visits["mrn"] == mrn]
            if patient_visits.shape[0] == 0:
                visit_texts.append(None)
            elif patient_visits.shape[0] == 1:
                visit_texts.append("\n".join([patient_visits["csn"].iloc[0],
                                              patient_visits["phac_narrative"].iloc[0]]))
            else:
                combined_texts = []
                for csn, text in zip(patient_visits["csn"].tolist(), patient_visits["phac_narrative"].tolist()):
                    visit_text = "\n".join([csn, text])
                    combined_texts.append(visit_text)
                visit_texts.append("\n\n".join(combined_texts))

        previous_visits_df=pd.DataFrame({"mrn": mrns, "previous visits": visit_texts})
        return previous_visits_df

    def _get_report(self, patients, visits, cases, problems):


        header = ["CSN", "MRN", "ScrMRN", "DOB", "SEX", "POSTAL", "ER Time", "ER Date", "ER Day", "INJ DATE", "Hr", "Min",
                  "AM/PM", "I/O", "LOCATION", "AREA", "PLACE", "Diagnosis", "SK Narrative", "PHAC Narrative",
                  "W4P", "NO1", "BP1", "NO2", "BP2", "NO3", "BP3", 'veh', 'veh p', "Notes", 'LOS', "DISP",
                  "IN", "sub", "subID", 'sd1', "sd2", "sd3", "sd4", "sd5", "SPORTS CODE",
                  "E1", "E2", "E3", "E4", "CTAS", "Chief Complaint", "Problem List", "previous visits"]

        merged = visits.merge(patients, how="inner", on="mrn")
        merged = merged.merge(cases, how="left", on="csn")
        merged = merged.merge(problems, how="left", on="csn")
        previous_visits= self.get_previous_visits(merged["mrn"].drop_duplicates().to_list(), merged["arrival_date"].min())
        merged = merged.merge(previous_visits, how="left", on="mrn")

        cols_to_keep = []
        for col in merged.columns:
            if "vector" in col or col == "id":
                continue
            else:
                cols_to_keep.append(col)

        merged = merged[cols_to_keep]
        # adding all columns here so I don't forget them as they are getting more and more autofilled
        # not for the E columns as they are not needed for chirpp but are internal
        # this can probably be a loop and a dict but still hard coded so will leave it for now

        report_df = pd.DataFrame(columns=header)
        report_df["POSTAL"] = merged["postal_code"].apply(process_postal)
        report_df["SEX"] = merged["sex"]
        report_df["MRN"] = merged["mrn"]
        report_df["CSN"] = merged["csn"]
        report_df["ScrMRN"] = merged["scr_mrn"]
        report_df["DOB"] = merged["dob"]
        report_df["ER Date"] = merged["arrival_date"]
        report_df["ER Time"] = merged["arrival_time"]
        report_df["ER Day"] = merged["day_of_week"]
        report_df["CTAS"] = merged["ctas"]
        report_df["Chief Complaint"] = merged["chief_complaint"]
        report_df["W4P"] = merged["w4p"]
        report_df["Notes"] = merged["notes"]
        report_df["LOS"] = merged["los"]
        report_df["Diagnosis"] = merged["diagnosis"]
        report_df["Problem List"] = merged["problem_list"]
        report_df["PHAC Narrative"] = merged["phac_narrative"]
        report_df["SK Narrative"] = merged["sk_narrative"]
        report_df["I/O"] = merged["i_o"]
        report_df["IN"] = merged["intent"]
        report_df["sub"] = merged["sub"]
        report_df["subID"] = merged["sub_id"]
        report_df["chirpp"] = merged["chirpp"]
        report_df["NO1"] = merged["no1"]
        report_df["NO2"] = merged["no2"]
        report_df["NO3"] = merged["no3"]
        report_df["BP1"] = merged["bp1"]
        report_df["BP2"] = merged["bp2"]
        report_df["BP3"] = merged["bp3"]
        report_df["sd1"] = merged["sd1"]
        report_df["sd2"] = merged["sd2"]
        report_df["sd3"] = merged["sd3"]
        report_df["sd4"] = merged["sd4"]
        report_df["sd5"] = merged["sd5"]
        report_df["SPORTS CODE"] = merged["sports_code"]
        report_df["INJ DATE"] = merged["injury_date"]
        report_df["Hr"] = merged["injury_hour"]
        report_df["Min"] = merged["injury_min"]
        report_df["AM/PM"] = merged["am_pm"]
        report_df["DISP"] = merged["disp"]
        report_df["LOCATION"] = merged["location"]
        report_df["AREA"] = merged["area"]
        report_df["PLACE"] = merged["place"]
        report_df["veh"] = merged["veh"]
        report_df["veh p"] = merged["veh_p"]

        sheet2 = report_df[report_df["chirpp"] == True]
        sheet1 = report_df[pd.isna(report_df["chirpp"])]

        return sheet1, sheet2