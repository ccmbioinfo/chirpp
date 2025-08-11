from datetime import datetime

import pandas as pd

from sqlalchemy import MetaData, select
from sqlalchemy.orm import Session

from chirpp.database import utils

#TODO need a space to fix column names

class DataBase:
    """
    this is the base database class to add/update notes, I'm not sure if we will ever remove them, we might remove
    from the notes section
    """

    def __init__(self, engine):
        self.engine = engine
        self.meta = MetaData(bind=self.engine)
        self.meta.reflect(bind=self.engine)
        self.session = Session(self.engine)
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
        patients, visits, referrals, problems, notes = utils.get_sections(epic_notes)
        # filter for unique constraint
        patients = patients[~patients["mrn"].isin(self.mrns)]
        visits = visits[~visits["csn"].isin(self.csns)]
        referrals = referrals[~referrals["csn"].isin(self.csns)]
        problems = problems[~problems["csn"].isin(self.csns)]
        notes = notes[~notes["csn"].isin(self.csns)]

        patients.to_sql("patients", self.engine, if_exists="append", index=False)

        visits["csn"]=visits["csn"].astype(int)
        visits.to_sql("visits", self.engine, if_exists="append", index=False)

        referrals.to_sql("referrals", self.engine, if_exists="append", index=False)

        problems.to_sql("problems", self.engine, if_exists="append", index=False)
        notes.to_sql("notes", self.engine, if_exists="append", index=False)
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
        
        cases=cases.rename(columns=col_dict)
        cases = cases[~cases["csn"].isin(csns)]

        cases = cases[["csn", "injury_date", "injury_hour", "injury_min", "am_pm", "i_o", "location", "area",
                       "place","phac_narrative","w4p", "no1", "no2", 'no3', 'bp1', 'bp2', 'bp3', 'notes', 'sub',
                       'sub_id', 'sports_code', 'disp','intent','veh', 'veh_p', 'sd1', 'sd2', 'sd3', 'sd4', 'sd5',
                      'sk_narrative']]

        cases.to_sql("chirpp_report", self.engine, if_exists="append", index=False)

    #This will be hardcoded because there needs to be a match between the embedding dict and the
    # database table columns, using a json for a flexible solution defeats the purpose of pgvector
    def import_processed_notes(self, csns, processed_notes, embedding_dict):
        """
        This will take the processed notes and the embedings dictionary {model_name:embedding_vector} and add them
        to the database
        :param processed_notes: output or section remover on the triage and provider notes
        :param embedding_dict: output of huggingface embeddings
        :return: nothing update the database or raise errors
        """
        notes_table=self.meta.tables["processed_notes"]
        num_notes=len(processed_notes)
        keys=list(embedding_dict.keys())

        old_csns = select(self.tables["processed_notes"].c.csn)
        old_csns = [item[0] for item in self.session.execute(old_csns).fetchall()]
        
        
        for key in keys:
            if embedding_dict[key].shape[0] != num_notes:
                raise ValueError("embedding shape does not match number of notes")
            else:
                for i in range(num_notes):
                    if csns[i] not in old_csns:
                        statement = notes_table.insert().values(csn=csns[i],
                                                            note_text=processed_notes[i],
                                                            jina_match_embed=embedding_dict["text-matching"][i, :],
                                                            jina_pass_embed=embedding_dict["retrieval.passage"][i, :],
                                                            jina_sep_embed=embedding_dict["separation"][i, :],
                                                            jina_class_embed=embedding_dict["classification"][i, :],
                                                            jina_query_embed=embedding_dict["retrieval.query"][i, :], )
                        self.session.execute(statement)
                        self.session.commit()
                    else:
                        continue

    # use this to pass a set of raw reports, this will be a bunch of joins
    # I need to select Triage and ED Provider notes from the database and pass it ot generate report
    def get_raw(self, start, end):
        visits_table = self.tables["visits"]
        problems_table = self.tables["problems"]
        referrals_table = self.tables["referrals"]
        notes_table = self.tables["notes"]
        patients_table = self.tables["patients"]

        visits=self.session.execute(select(visits_table).where((visits_table.c.arrival_date >= start) &
                                       (visits_table.c.arrival_date <= end))).fetchall()
        visits=pd.DataFrame(visits)
        mrns=visits["mrn"].to_list()
        csns=visits["csn"].to_list()

        patients=pd.DataFrame(self.session.execute(select(patients_table).\
                                                   where(patients_table.c.mrn.in_(mrns))).\
            fetchall())

        referrals=pd.DataFrame(self.session.execute(select(referrals_table).\
                               where(referrals_table.c.csn.in_(csns))).fetchall()).\
            drop(columns="id")

        notes = pd.DataFrame(self.session.execute(select(notes_table). \
                                 where(notes_table.c.csn.in_(csns))).fetchall()).\
            drop(columns="id")

        problems = pd.DataFrame(self.session.execute(select(problems_table). \
                                 where(problems_table.c.csn.in_(csns))).fetchall())

        problems_grouped = problems.groupby("csn")
        merged_probs=[]
        for _, group in problems_grouped:
            merged_probs.append(",".join(group["problem"].to_list()))

        problems = problems.drop(columns=["problem", "id"]).drop_duplicates()
        problems["problem_list"]=merged_probs

        visits=visits.merge(patients, how="left", on="mrn")
        visits=visits.merge(referrals, how="left", on="csn")
        visits=visits.merge(notes, how="left", on="csn")
        visits=visits.merge(problems, how="left", on="csn")
        visits=visits[["csn", "mrn", "sex", "dob", "age", "postal_code", "arrival_date",
                       "arrival_time", "los", "chief_complaint", "problem_list", "diagnosis",
                       "ctas", "referrals", "note_type", "author_type", "author_service",
                       "note_text", 'address', 'city', 'province', 'disposition', 'ctas', ]]
        visits=visits.rename(columns={
            "csn":"CSN", "mrn":'MRN', 'sex':'Sex', 'dob':'Date of Birth', 'age':'Age (Years)',
            'arrival_date':'Arrival Date', 'arrival_time':'Arrival Time', 'address':'Address',
            'city':'City', 'province':'Province', 'postal_code':'Postal Code',
            'chief_complaint':'Chief Complaint', 'problem_list':'Problem List', 'los':'LOS',
            'disposition':'Disposition', 'referrals':'Referral Order', 'diagnosis':"Diagnosis",
            'ctas':'CTAS', 'note_type':'Note Type', 'author_type':'Author Type',
            'author_service':'Author Service', 'note_text':'Note Text',
        })
        if "LINE" not in visits.columns:
            visits["LINE"]=1

        if "CHIRPP Icon" not in visits.columns:
            visits["CHIRPP Icon"]=None

        if "Patient Name" not in visits.columns:
            visits["Patient Name"]=None

        return visits

    #TODO get appropriate columns, process postal and scramble mrn add sheet1 and sheet2
    def get_report(self, start, end):
        """
        generate a report from the database
        :param start: a datetime.datetime
        :param end: a datetime.datetime
        :return: a pandas dataframe
        """
        case_table=self.tables["chirpp_report"]
        visit_table=self.tables["visits"]
        problems_table=self.tables["problems"]
        patients_table=self.tables["patients"]

        visits=self.session.execute(select(visit_table).where((visit_table.c.arrival_date >= start) &
                                                         (visit_table.c.arrival_date <= end))).fetchall()
        visits =pd.DataFrame(visits)
        
        cases=self.session.execute(select(case_table).where(case_table.c.csn.in_(visits["csn"].to_list()))).\
        fetchall()
        cases=pd.DataFrame(cases)
        cases["chirpp"]=True

        patients=self.session.execute(select(patients_table).\
                         where(patients_table.c.mrn.in_(visits["mrn"].to_list()))).fetchall()
        patients=pd.DataFrame(patients)

        problems=self.session.execute(select(problems_table).\
                         where(problems_table.c.csn.in_(visits["csn"].to_list()))).fetchall()
        problems=pd.DataFrame(problems)

        problems_merged=[]
        problems_grouped=problems.groupby("csn")
        for _, group in problems_grouped:
            problems_merged.append(",".join(group["problem"].to_list()))
        
        new_problems_df=pd.DataFrame({"csn":problems["csn"].drop_duplicates(), "problem_list":problems_merged})
        
        sheet1, sheet2=utils.prepare_report(visits, cases, patients, new_problems_df)
        return sheet1, sheet2

    #TODO this is not implemented yet, we need to figure out how to update the raw data
    def update_raw(self, txt_file):
        pass

    def update_report(self, excel_file, col_dict):
        """
        here the assumption is that the sheet 2 is always the cases, and it is always the second sheet.
        :param excel_file:
        :return:
        """
        data=pd.read_excel(excel_file, sheet_name=1)[list(col_dict.keys)].rename(columns=col_dict)
        visits_table = self.tables["visits"]
        csns=data["csn"].to_list()
        case_values=data.drop(columns="csn").to_dict(orient="records")
        for case, values in zip(csns, case_values):
            statement = visits_table.update().where(visits_table.c.csn == case).values(values)
            self.session.execute(statement)
            self.session.commit()

    #TODO
    def previous_visits(self, mrn):
        """
        get previous visits for a patient
        :param mrn: a patient MRN
        :return: a list of csns for previous visits an the text of the most similar visit based on phac narrative and cosine similarity
        """
        visits_table = self.tables["visits"]
        patients_table = self.tables["patients"]

        visits = self.session.execute(select(visits_table.c.mrn, visits_table.c.phac_narrativie).\
                                      where(visits_table.c.mrn == mrn)).fetchall()


        return visits


