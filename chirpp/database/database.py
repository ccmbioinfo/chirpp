from datetime import datetime

import pandas as pd

from sqlalchemy import MetaData, select, Table, Column, Integer, String, ForeignKey
from sqlalchemy.orm import sessionmaker

from chirpp.database import utils


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
        self.session = sessionmaker(self.engine)
        self.tables = self.meta.tables
        self.get_mrns()
        self.get_csns()

    def get_mrns(self):
        mrns = select(self.tables["patients"].c.mrn)
        self.mrns = [item[0] for item in self.session.execute(mrns).fetchall()]

    def get_csns(self):
        csns = select(self.tables["visits"].c.csn)
        self.csns = [item[0] for item in self.session.execute(csns).fetchall()]


    def process_dump(self, epic_notes):
        """
        take a PreProcess instance and from within the preprocess instance take preprocessed notes and get note sections
        then import the stuff to the database
        :param preprocess: PreProcess instance
        :return: None, things will be imported to the database
        """
        #TODO this need to process the epic dump and put it in the database it's the first thing we need to do
        self.get_mrns()
        self.get_csns()

    def process_report(self, cases, col_dict=utils.col_dict):
        """
        take a postprocess instance and add to the database, we are only adding the sheet 2
        :param postprocess: chirpp.postprocess.postprocess.Postprocess instance
        :return: None, things will be imported to the database
        """
        csns = select(self.tables["chirpp_report"].c.csn)
        csns = [item[0] for item in self.session.execute(csns).fetchall()]

        cases = cases.rename(columns=col_dict)
        cases = cases[~cases["csn"].isin(csns)]

        cases = cases[["csn", "injury_date", "injury_hour", "injury_min", "am_pm", "i_o", "location", "area",
                       "place", "phac_narrative", "w4p", "no1", "no2", 'no3', 'bp1', 'bp2', 'bp3', 'notes', 'sub',
                       'sub_id', 'sports_code', 'disp', 'intent', 'veh', 'veh_p', 'sd1', 'sd2', 'sd3', 'sd4', 'sd5',
                       'sk_narrative']]

        cases.to_sql("chirpp_report", self.engine, if_exists="append", index=False)

    # This will be hardcoded because there needs to be a match between the embedding dict and the
    # database table columns, using a json for a flexible solution defeats the purpose of pgvector
    def import_processed_notes(self, inference_notes, chunker):
        """
        This imports the processed notes embeddings to the database, we are already creating this in the generate_report.py
        this is a dataframe that does not need to take any further processing
        :param inference_notes: inference notes databframe,
        :return:
        """
        # this will put the notes after they have been processed by sectionremover
        pass

    def import_chunked_notes(self, merged_notes, chunker):
        # I need to implement a new embedding model not the model2vec, that one is good for chunking but not embeddings
        pass

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

    # TODO get appropriate columns, process postal and scramble mrn add sheet1 and sheet2
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

        sheet1, sheet2 = utils.prepare_report(visits, cases, patients, new_problems_df)
        return sheet1, sheet2

    # TODO this is not implemented yet, we need to figure out how to update the raw data, or if needed at all
    # I do not think we will ever use this
    def update_raw(self, txt_file):
        pass

    def update_report(self, excel_file, col_dict):
        """
        here the assumption is that the sheet 2 is always the cases, and it is always the second sheet.
        :param excel_file:
        :return:
        """
        data = pd.read_excel(excel_file, sheet_name=1)[list(col_dict.keys)].rename(columns=col_dict)
        visits_table = self.tables["visits"]
        csns = data["csn"].to_list()
        case_values = data.drop(columns="csn").to_dict(orient="records")
        for case, values in zip(csns, case_values):
            statement = visits_table.update().where(visits_table.c.csn == case).values(values)
            self.session.execute(statement)
            self.session.commit()

    def previous_visits(self, merged_notes):
        """
        get previous visits for a patient
        :param mrn: a list of mrns to get previous visits for
        :return: return a list of csns and phac narratives for the patient, currently looking
        """
        visits_table = self.tables["visits"]

        previous_visits = self.session.execute(
            select(visits_table.c.mrn, visits_table.c.csn, visits_table.c.phac_narrativie). \
            where(visits_table.c.mrn.in_(merged_notes["MRN"].tolist()))) \
            .fetchall()

        visit_texts = []
        for mrn in merged_notes["mrn"]:
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

        return visit_texts
