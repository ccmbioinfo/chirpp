import os

import pandas as pd
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import Session
from chirpp.database import tables
from dotenv import load_dotenv
from math import floor

load_dotenv()
user=os.environ["DB_USER"]
pwd=os.environ["DB_PWD"]
port=os.environ["DB_PORT"]
db=os.environ["DB_NAME"]

db = create_engine('postgresql+psycopg2://{}:{}}@localhost:{}/{}'.format(user, pwd, port, db))

project_meta = MetaData(bind=db)
session = Session(db)
tables.Base.metadata.create_all(db)

# this is hardcoded for first time setup
processed_cases="../past_data/complete_data.csv"
raw_dir = "../past_data/raw"

processed_cases=pd.read_csv(processed_cases, header=0, sep="\t")
processed_cases= processed_cases.drop(columns=["ScrMRN", "MRN"])
processed_cases["ER Date"]=pd.to_datetime(processed_cases["ER Date"])
processed_cases=processed_cases.drop_duplicates()
years=processed_cases["ER Date"].dt.year.drop_duplcates().to_list()
months=processed_cases["ER Date"].dt.year.drop_duplicates().to_list()


files = os.listdir(raw_dir)
files = [file for file in files if file.endswith("xlsx")]
num_sheets = [7, 12, 12, 12, 12, 11]

old_mrns = []
old_csns = []

def calculate_age(arrival, dob):
    td=arrival-dob
    td=td.days
    td=int(td)
    age=floor(td/365)
    return age

for file, sheets in zip(files, num_sheets):
    for i in range(sheets):
        path = raw_dir + file
        dat = pd.read_excel(path, sheet_name=i)
        dat = dat[~pd.isna(dat["Note Text"])]
        patients = dat[["MRN", "Date of Birth", "Arrival Date"]].drop_duplicates()
        patients = patients[~patients["MRN"].isin(old_mrns)]  # remove repeat visitors
        patients["Date of Birth"] = pd.to_datetime(patients["Date of Birth"])
        patients["Arrival Date"] = pd.to_datetime(patients["Arrival Date"])
        patients["age"]=patients.apply(lambda x: calculate_age(patients["Arrival Date"], patients["Date of Birth"]), axis=1)

        visits = dat[["CSN", "Sex", "MRN", "Arrival Date", "Arrival Time", "Postal Code",
                      "Chief Complaint", "Diagnosis", "Disposition", "CTAS"]].drop_duplicates()
        visits["processed"] = False
        visits = visits[~visits["CSN"].isin(old_csns)]

        referrals = dat[["CSN", "Referral Order"]].dropna().drop_duplicates()
        problems = dat[["CSN", "Problem List"]].drop_duplicates().dropna()
        problems['Problem List'] = [str(x).split(',') for x in problems['Problem List'].dropna()]
        problems = problems.explode("Problem List")
        problems = problems[problems["Problem List"] != " "]
        problems["Problem List"] = problems["Problem List"].str.replace("^ ", "", regex=True)
        notes = dat[["CSN", "Note Type", "Author Type", "Author's Service", "Note Text", "LINE"]].drop_duplicates()
        notes_grouped = notes.groupby(["Note ID"])
        notes_merged = []
        for _, group in notes_grouped:
            df = group[["CSN", "Note Type", "Author Type", "Author's Service", ]].drop_duplicates()
            note_text = " ".join(
                [str(x) for x in
                 group.sort_values(by=["LINE"], ignore_index=True)["Note Text"].tolist()])
            df["Note Text"] = note_text
            notes_merged.append(df)
        notes_merged = pd.concat(notes_merged)

        patients = patients.rename(columns={"MRN": "mrn", "Date of Birth": "dob",
                                            "Age (Years)": "age"})

        referrals = referrals.rename(columns={"CSN": "csn", "Referral Order": "referrals"})

        visits = visits.rename(columns={"CSN": "csn", "Sex": "sex", "MRN": "mrn",
                                        "Arrival Date": "arrival_date",
                                        "Arrival Time": "arrival_time",
                                        "Postal Code": "postal_code",
                                        "Chief Complaint": "chief_complaint",
                                        "Diagnosis": "diagnosis",
                                        "Disposition": "disposition",
                                        "Referral Order": "referral_order",
                                        "CTAS": "ctas"})

        problems = problems.rename(columns={"CSN": "csn", "Problem List": "problem"})

        notes_merged = notes_merged.rename(columns={"CSN": "csn", "Note Type": "note_type",
                                                    "Author Type": "author_type",
                                                    "Author's Service": "author_service",
                                                    "Note Text": "note_text", })

        patients.to_sql("patients", db, if_exists="append", index=False)
        referrals.to_sql("referrals", db, if_exists="append", index=False)
        visits.to_sql("visits", db, if_exists="append", index=False)
        visit_year=visits["arrival_date"].dt.year.drop_duplicates()
        visit_month = visits["arrival_date"].dt.month.drop_duplicates()
        if visit_year in years and visit_month in months:
            visits["processed"]=True
        else:
            visits["processed"]=False

        problems.to_sql("problems", db, if_exists="append", index=False)
        notes_merged["note_text"] = notes["note_text"].astype(str)
        notes_merged.to_sql("notes", db, if_exists="append", index=False)

        # add new visitors
        old_mrns = old_mrns + patients["mrn"].tolist()
        old_mrns = list(set(old_mrns))

        old_csns = old_csns + visits["csn"].tolist()
        old_csns = list(set(old_csns))