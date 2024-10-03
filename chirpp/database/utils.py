import pandas as pd
from math import floor


def scramble_mrn(mrn):
    """
    takes the mrn value of the note and runs a simple scramble
    :param mrn: mrn
    :return: scrambled mrn
    """
    mrn = str(mrn).strip()
    last_digit = (int(mrn[-1]) + int(mrn[-2])) % 10
    return mrn[:-2] + mrn[-1] + mrn[-2] + str(last_digit)

def calculate_age(arrival, dob):
    td=arrival-dob
    td=td.days
    td=int(td)
    age=floor(td/365)
    return age


# right now I'm not changing the column names, I'm relying on the existing reports and they will remain constant and
# the column names will not be changed for no good reason
def get_sections(notes, col_dict):

    notes = notes[~pd.isna(notes["Note Text"])]
    patients = notes[["MRN", "Date of Birth", "Arrival Date"]].drop_duplicates()
    patients["Date of Birth"] = pd.to_datetime(patients["Date of Birth"])
    patients["Arrival Date"] = pd.to_datetime(patients["Arrival Date"])
    patients["age"] = patients.apply(lambda x: calculate_age(patients["Arrival Date"], patients["Date of Birth"]),
                                     axis=1)

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

    referrals = notes[["CSN", "Referral Order"]].dropna().drop_duplicates()
    referrals = referrals.rename(columns={"CSN": "csn", "Referral Order": "referrals"})

    problems = notes[["CSN", "Problem List"]].drop_duplicates().dropna()
    problems['Problem List'] = [str(x).split(',') for x in problems['Problem List'].dropna()]
    problems = problems.explode("Problem List")
    problems = problems[problems["Problem List"] != " "]
    problems["Problem List"] = problems["Problem List"].str.replace("^ ", "", regex=True)
    problems = problems.rename(columns={"CSN": "csn", "Problem List": "problem"})

    notes_df = notes[["CSN", "Note Type", "Author Type", "Author's Service", "Note Text"]].drop_duplicates()
    notes_df=notes_df.rename(columns={"CSN": "csn", "Note Type": "note_type",
                    "Author Type": "author_type",
                    "Author's Service": "author_service",
                    "Note Text": "note_text", })

    return patients, visits, referrals, problems, notes_df
