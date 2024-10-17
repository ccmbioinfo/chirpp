import pandas as pd
from math import floor

from chirpp.postprocess import utils as ps_utils



def calculate_age(arrival, dob):
    td = arrival - dob
    td = td.days
    td = int(td)
    age = floor(td / 365)
    return age




# right now I'm not changing the column names, I'm relying on the existing reports and they will remain constant and
# the column names will not be changed for no good reason
def get_sections(notes):
    notes = notes[~pd.isna(notes["Note Text"])]
    patients = notes[["MRN", "Date of Birth", "Arrival Date"]].drop_duplicates()
    patients["Date of Birth"] = pd.to_datetime(patients["Date of Birth"])
    patients["Arrival Date"] = pd.to_datetime(patients["Arrival Date"])
    ages=[]
    for arrival, dob in zip(patients["Arrival Date"].tolist(), patients["Date of Birth"].tolist()):
        ages.append(calculate_age(arrival, dob))
    patients["age"] = ages
    patients=patients[["MRN", "Date of Birth", "age"]]
    patients=patients.rename(columns={"MRN":"mrn", "Date of Birth":"dob"})

    visits = notes[["CSN", "Sex", "MRN", "Arrival Date", "Arrival Time", "Postal Code",
                    "Chief Complaint", "Diagnosis", "Disposition", "CTAS"]].drop_duplicates()
    visits["processed"] = False
    visits = visits.rename(columns={"CSN": "csn", "Sex": "sex", "MRN": "mrn",
                                    "Arrival Date": "arrival_date",
                                    "Arrival Time": "arrival_time",
                                    "Postal Code": "postal_code",
                                    "Chief Complaint": "chief_complaint",
                                    "Diagnosis": "diagnosis",
                                    "Disposition": "disposition",
                                    "Referral Order": "referral_order",
                                    "CTAS": "ctas"})
    # this is arrived in error
    visits["ctas"][pd.isna(visits["ctas"])] = 0
    visits["ctas"][visits["ctas"] == ""] = 0

    referrals = notes[["CSN", "Referral Order"]].dropna().drop_duplicates()
    referrals = referrals.rename(columns={"CSN": "csn", "Referral Order": "referrals"})

    problems = notes[["CSN", "Problem List"]].drop_duplicates().dropna()
    problems['Problem List'] = [str(x).split(',') for x in problems['Problem List'].dropna()]
    problems = problems.explode("Problem List")
    problems = problems[problems["Problem List"] != " "]
    problems["Problem List"] = problems["Problem List"].str.replace("^ ", "", regex=True)
    problems = problems.rename(columns={"CSN": "csn", "Problem List": "problem"})

    notes_df = notes[["CSN", "Note Type", "Author Type", "Author's Service", "Note Text", "Note ID"]].drop_duplicates()
    notes_grouped = notes_df.groupby(["Note ID"])
    notes_merged = []
    for _, group in notes_grouped:
        df = group[["CSN", "Note Type", "Author Type", "Author's Service", ]].drop_duplicates()
        note_text = " ".join(
            [str(x) for x in
             group.sort_values(by=["LINE"], ignore_index=True)["Note Text"].tolist()])
        df["Note Text"] = note_text
        notes_merged.append(df)
    notes_df = pd.concat(notes_merged)
    notes_df = notes_df.rename(columns={"CSN": "csn", "Note Type": "note_type",
                                        "Author Type": "author_type",
                                        "Author's Service": "author_service",
                                        "Note Text": "note_text", })

    return patients, visits, referrals, problems, notes_df


# TODO  merge this and see what columns we have
# rename the columns and then copy paste postprocess init
def prepare_report(visits, cases, patients, notes):
    cases = cases.merge(visits, how="left", on="csn")
    cases = cases.merge(patients, how="left", on="mrn")
    notes = notes[notes["csn"].isin(cases["csn"])]
    cases = cases.merge(notes, on="csn", how="left")

    cases_grouped = cases.groupby(["csn"])
    for _, data in cases_grouped:
        pass

    cases = cases[["mrn", "csn", "dob", "sex", "postal_code", "arrival_time", "arrival_date",
                   "injury_date", "injury_min", "injury_hour", "am_pm", "i_o", "location",
                   "area", "place", "diagnosis"]]
    pass
