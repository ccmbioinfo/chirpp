import pandas as pd
from math import floor

from chirpp.postprocess.utils import process_postal, scramble_mrn, process_ctas, process_sex

col_dict = {
    "CSN": "csn", "INJ DATE": "injury_date", "Hr": "injury_hour", "Min": "injury_min", "AM/PM": "am_pm",
    "I/O": "i_o", "LOCATION": "location", "AREA": "area", "PLACE": "place", "SK Narrative": "sk_narrative",
    "PHAC Narrative": "phac_narrative", "W4P": "w4p", "NO1": "no1", "NO2": "no2", "NO3": "no3", "BP1": "bp1",
    "BP2": "bp2", "BP3": "bp3", "IN": "intent", "DISP": "disp", "subID": "sub_id", "SPORTS CODE": "sports_code",
    "veh p": "veh_p", "Notes": "notes"
}


def invert_dict(dict):
    new_dict = {}
    for k, v in dict.items():
        new_dict[v] = k
    return new_dict

# because epic gives you the current age not what the age was when the patient presented
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
    patients = notes[["MRN", "Date of Birth"]].drop_duplicates()
    patients["Date of Birth"] = pd.to_datetime(patients["Date of Birth"])

    patients = patients[["MRN", "Date of Birth"]]
    patients = patients.rename(columns={"MRN": "mrn", "Date of Birth": "dob"})

    visits = notes[["CSN", "Sex", "MRN", "Arrival Date", "Date of Birth", "Arrival Time", "Postal Code",
                    "Chief Complaint", "Diagnosis", "Disposition", "CTAS", "Address", "City",
                    "Province"]].drop_duplicates()
    visits["Arrival Date"] = pd.to_datetime(visits["Arrival Date"])
    visits["Date of Birth"] = pd.to_datetime(visits["Date of Birth"])
    ages = []
    for arrival, dob in zip(visits["Arrival Date"].tolist(), visits["Date of Birth"].tolist()):
        ages.append(calculate_age(arrival, dob))
    visits["age"] = ages

    visits["processed"] = False
    visits = visits.rename(columns={"CSN": "csn", "Sex": "sex", "MRN": "mrn",
                                    "Arrival Date": "arrival_date",
                                    "Arrival Time": "arrival_time",
                                    "Postal Code": "postal_code",
                                    "Chief Complaint": "chief_complaint",
                                    "Diagnosis": "diagnosis",
                                    "Disposition": "disposition",
                                    "Referral Order": "referral_order",
                                    "CTAS": "ctas", "Address": "address", "City": "city", "Province": "province"})
    # this is arrived in error
    visits = visits.drop(columns="Date of Birth")

    referrals = notes[["CSN", "Referral Order"]].dropna().drop_duplicates()
    referrals = referrals.rename(columns={"CSN": "csn", "Referral Order": "referrals"})

    problems = notes[["CSN", "Problem List"]].drop_duplicates().dropna()
    problems['Problem List'] = [str(x).split(',') for x in problems['Problem List'].dropna()]
    problems = problems.explode("Problem List")
    problems = problems[problems["Problem List"] != " "]
    problems["Problem List"] = problems["Problem List"].str.replace("^ ", "", regex=True)
    problems = problems.rename(columns={"CSN": "csn", "Problem List": "problem"})
    if "Note ID" in notes.columns:
        notes_df = notes[
            ["CSN", "Note Type", "Author Type", "Author Service", "Note Text", "LINE", "Note ID"]].drop_duplicates()
        notes_grouped = notes_df.groupby(["Note ID"])

        notes_merged = []
        for _, group in notes_grouped:
            df = group[["CSN", "Note Type", "Author Type", "Author Service", ]].drop_duplicates()
            note_text = " ".join(
                [str(x) for x in
                 group.sort_values(by=["LINE"], ignore_index=True)["Note Text"].tolist()])
            df["Note Text"] = note_text
            notes_merged.append(df)
        notes_df = pd.concat(notes_merged)
        notes_df = notes_df.rename(columns={"CSN": "csn", "Note Type": "note_type",
                                            "Author Type": "author_type",
                                            "Author Service": "author_service",
                                            "Note Text": "note_text", })
    else:
        notes_df = notes[
            ["CSN", "Note Type", "Author Type", "Author Service", "Note Text"]].drop_duplicates()

    return patients, visits, referrals, problems, notes_df



def prepare_report(visits, cases, patients, problems):
    """
    this prepares the report from the database, not to be confused with the postprocess methods, when you want to generate
    a report from the db for a given date range (see above) you will use this method
    :param visits:
    :param cases:
    :param patients:
    :param problems:
    :return:
    """
    header = ["MRN", "CSN", "ScrMRN", "DOB", "SEX", "POSTAL", "ER Time", "ER Date", "INJ DATE", "Hr", "Min",
              "AM/PM", "I/O", "LOCATION", "AREA", "PLACE", "Diagnosis", "SK Narrative", "PHAC Narrative",
              "W4P", "NO1", "BP1", "NO2", "BP2", "NO3", "BP3", 'veh', 'veh p', "Notes", 'LOS', "DISP",
              "IN", "sub", "subID", 'sd1', "sd2", "sd3", "sd4", "sd5", "SPORTS CODE",
              "E1", "E2", "E3", "E4", "CTAS", "Chief Complaint", "Problem List"]

    merged = visits.merge(patients, how="inner", on="mrn")
    merged = merged.merge(cases, how="left", on="csn")
    merged = merged.merge(problems, how="left", on="csn")

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
    report_df["SEX"] = merged["sex"].apply(process_sex)
    report_df["MRN"] = merged["mrn"]
    report_df["CSN"] = merged["csn"]
    report_df["ScrMRN"] = merged["mrn"].apply(scramble_mrn)
    report_df["DOB"] = merged["dob"]
    report_df["ER Date"] = merged["arrival_date"]
    report_df["ER Time"] = merged["arrival_time"]
    report_df["CTAS"] = merged["ctas"].apply(process_ctas)
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
