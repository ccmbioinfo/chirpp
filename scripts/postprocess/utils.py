import numpy as np
import pandas as pd


class MissingDataError(Exception):
    pass

def process_sex(sex):
    """
    chang M/F to male, female
    :param sex:
    :return:
    """
    if sex.lower() == "male":
        sex = "M"
    elif sex.lower() == "female":
        sex = "F"
    else:
        sex = sex
    return sex


def get_sk_narrative(notes, note_types):
    """
    concat relevant notes for the SK Narrative column
    :param notes: all notes from a specific visit determined by "Arrival Date" and MRN
    :param note_types: list of note types to select from the dataframe
    :return: a concatanated string for all the notes with their respective header
    """
    narrative = []
    for note_type in note_types:
        if note_type in notes:
            narrative.append(
                note_type + "\n\n" + " ".join(notes[note_type]))
    return "\n\n".join(narrative)


def scramble_mrn(mrn):
    """
    takes the mrn value of the note and runs a simple scramble
    :param mrn: mrn
    :return: scrambled mrn
    """
    mrn = str(mrn).strip()
    last_digit = (int(mrn[-1]) + int(mrn[-2])) % 10
    return mrn[:-2] + mrn[-1] + mrn[-2] + str(last_digit)


def process_postal(postal):
    """
    remove the last 3 digits of postal code to increase privacy
    :param postal: postal code
    :return: truncated postal code
    """
    if type(postal) == str and len(postal) == 7 and postal[3] == " ":
        postal = str(postal).split(" ")[0]
    return postal


def get_report_note(df):
    """
    fill in the Notes column with some relevant information, this is a legacy function, not sure what the notes column
    entail in this case will need to clarify
    :param df: all notes for a specific visit determined by "Arrival Date" and "MRN"
    :return: string with relevant information
    """
    disposition = df["Disposition"].drop_duplicates().tolist()[0].lower()
    merged_text = " ".join(df["Note Text"])
    if disposition in [
        'admit',
        'deceased',
        'lama',
        'lwbr',
        'lwbs',
        'send to or',
        'transfer to another facility'
    ]:
        return disposition
    elif "Consults" in merged_text or 'Consult Follow Up' in merged_text:
        return "Consult"
    elif "ED Provider Notes" in df["Note Type"].tolist():
        provider_note = " ".join(df["Note Text"][df["Note Type"] == "ED Provider Notes"])
        idx = provider_note.lower().find("assessment and plan")
        if idx == -1:
            return ""
        return provider_note[idx:]
    else:
        return ""


def create_report(all_notes, inference_notes, report_header, note_types):
    """
    create a report DataFrame to be filled in, this will only contain the classification probabilities the rest will
    be done elsewhere
    :param all_notes: all notes from EPIC
    :param inference_notes: output of inference for classification
    :param report_header: report header list of strings that will be used colum headers
    :param note_types: note types to be included in SK Narrative
    :return: a DataFrame to filled in more later
    """
    report_df = pd.DataFrame(columns=report_header)
    notes_grouped = all_notes.merge(inference_notes, how="inner", on="CSN").groupby(
        ["CSN", "MRN", "Arrival Date", "Arrival Time"])
    inferred = []
    for _, data in notes_grouped:
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
        group_df["Notes"] = get_report_note(data)
        group_df["LOS"] = data["ED Completed Length of Stay (Hours)"].drop_duplicates()
        group_df["Diagnosis"] = data["Diagnosis"].drop_duplicates()
        group_df["probs"] = data["probs"].drop_duplicates()
        group_df["summary"] = data["summary"].drop_duplicates()
        narrative = []
        for note_type, note_text in zip(data["Note Type"].tolist(), data["Note Text"].tolist()):
            if note_type in note_types:
                if not pd.isna(note_text):
                    narrative.append(note_type + "\n\n" + note_text)
        narrative = "\n\n".join(narrative)
        group_df["SK Narrative"] = narrative
        group_df.fillna('')
        inferred.append(group_df)
    inferred = pd.concat(inferred)
    return inferred


