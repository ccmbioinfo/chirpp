from datetime import datetime

import pandas as pd
from jsonschema.exceptions import SchemaError
from sqlalchemy import MetaData, select
from sqlalchemy.orm import Session

from chirpp.database import utils
from chirpp.database.query_builder import QueryBuilder


class Event:
    """
    This is the event code class, it will have context awere search and full text search
    """

    def __init__(self, name, keywords, rules=None, contex_aware=True, description=None,):
        """
        create a contex aware event class, this will be filling up the
        :param keywords:
        :param rules:
        """
        self.name = name
        self.description = description
        self.keywords = keywords
        self.contex_aware = contex_aware
        if self.contex_aware:
            if self.verify_schema(rules) and rules is not None:
                self.rules = rules
            elif rules is None:
                raise ValueError("rules cannot be None for context aware labels")
            else:
                raise SchemaError("rules do not match the proper medspacy schema")

    def to_db(self):
        pass

    def from_db(self):
        pass

    def search(self, start, end):
        pass

    def update_notes(self):
        pass

    def toggle(self):
        """
        if in the database toggle active/inactive
        :return: the result of the toggle, error if not in the database
        """
        pass

    def verify_schema(self, schema):
        """
        verify the json schema of the context rules
        :return:
        """
        pass


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
        mrns = select(self.tables["patients"].c.mrn)
        self.mrns = [item[0] for item in self.session.execute(mrns).fetchall()]
        csns = select(self.tables["visits"].c.csn)
        self.csns = [item[0] for item in self.session.execute(csns).fetchall()]
        #TODO move this to params
        self.col_dict={"INJ DATE": "injury_date", "Hr": "injury_hour", "Min": "injury_min", "AM/PM": "am_pm",
                              "I/O": "i_o", "LOCATION": "location", "AREA": "area", "PLACE": "place",
                              "PHAC Narrative": "phac_narrative",
                              "W4P": "w4p", "NO1": "no1", "NO2": "no2", "NO3": "no3", "BP1": "bp1", "BP2": "bp2",
                              "BP3": "bp3",
                              "Notes": "notes", "subID": "sub_id", "SPORTS CODE": "sports_code", "DISP": "disp",
                              "IN": "intent",
                              'veh p': 'veh_p'}

    def process_dump(self, preprocess):
        """
        take a PreProcess instance and from within the preprocess instance take preprocessed notes and get note sections
        then import the stuff to the database
        :param preprocess: PreProcess instance
        :return: None, things will be imported to the database
        """
        patients, visits, referrals, problems, notes = utils.get_sections(preprocess.merged_notes)
        # filter for unique constraint
        patients = patients[~patients["mrn"].isin(self.mrns)]
        visits = visits[~visits["csn"].isin(self.csns)]
        referrals = referrals[~referrals["csn"].isin(self.csns)]
        problems = problems[~problems["csn"].isin(self.csns)]
        notes = notes[~notes["csn"].isin(self.csns)]

        # TODO switch to sqlalchemy
        patients.to_sql("patients", self.engine, if_exists="append", index=False)
        referrals.to_sql("referrals", self.engine, if_exists="append", index=False)
        visits.to_sql("visits", self.engine, if_exists="append", index=False)
        problems.to_sql("problems", self.engine, if_exists="append", index=False)
        notes.to_sql("notes", self.engine, if_exists="append", index=False)

    def process_report(self, postprocess):
        """
        take a postprocess instance and add to the database, we are only adding the sheet 2
        :param postprocess: chirpp.postprocess.postprocess.Postprocess instance
        :return: None, things will be imported to the database
        """
        cases = postprocess.sheet2
        cases=cases.rename(columns=self.col_dict)

        cases = cases[["csn", "injury_date", "injury_hour", "injury_min", "am_pm", "i_o", "location", "area",
                       "place","phac_narrative","w4p", "no1", "no2", 'no3', 'bp1', 'bp2', 'bp3', 'notes', 'sub',
                       'sub_id', 'sports_code', 'disp','intent','veh', 'veh_p', 'sd1', 'sd2', 'sd3', 'sd4', 'sd5']]

        #TODO switch to sqlalchemy
        cases.to_sql("chirpp_report", self.engine, if_exists="append", index=False)

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

        visits=visits.merge(patients, how="inner", on="mrn")
        visits=visits.merge(referrals, how="inner", on="csn")
        visits=visits.merge(notes, how="inner", on="csn")
        visits=visits.merge(problems, how="inner", on="csn")
        visits=visits[["csn", "mrn", "sex", "dob", "age", "postal_code", "arrival_date",
                       "arrival_time", "los", "chief_complaint", "problem_list", "diagnosis",
                       "ctas", "referrals", "note_type", "author_type", "author_service",
                       "note_text"]]
        return visits

    def get_report(self, start, end):
        """
        generate a report from the database
        :param start: a datetime.datetime
        :param end: a datetime.datetime
        :return: a pandas dataframe
        """
        case_table=self.tables["chirpp_report"]
        visit_table=self.tables["visits"]

        cases=select(case_table).where(case_table.c.injury_date >= start and case_table.c.injury_date <= end)
        cases=pd.DataFrame(cases)
        visits=select(visit_table.c.mrn, visit_table.c.csn).where(visit_table.c.csn.in_())
        visits=pd.DataFrame(visits)

        cases=cases.merge(visits, how="inner", on="csn")
        return cases

    def update_raw(self, txt_file):
        pass

    def update_report(self, excel_file):
        """
        here the assumption is that the sheet 2 is always the cases, and it is always the second sheet.
        :param excel_file:
        :return:
        """
        data=pd.read_excel(excel_file, sheet_name=1)[list(self.col_dict.keys)].rename(columns=self.col_dict)
        visits_table = self.tables["visits"]
        csns=data["csn"].to_list()
        case_values=data.drop(columns="csn").to_dict(orient="records")
        for case, values in zip(csns, case_values):
            statement = visits_table.update().where(visits_table.c.csn == case).values(values)
            self.session.execute(statement)
            self.session.commit()

    def query(self, query):
        pass
