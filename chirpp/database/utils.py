from warnings import warn

import pandas as pd
import numpy as np


class ReportValidationError(Exception):
    pass

class TooManySheetsError(Exception):
    pass

class NoCSNError(Exception):
    pass

def check_excel(excel_file):
    xl = pd.ExcelFile(excel_file)
    sheet_count=len(xl.sheet_names)

    if len(sheet_count) > 2:
        raise TooManySheetsError("The excel files provided has 2 sheets, you have more than that, you will need to remove "
                            "extra sheets, if there are 2 sheets sheet 2 will be used for updating reports")
    elif len(sheet_count) <= 2:
        data=pd.read_excel(xl,sheet_name=sheet_count)

    header = ["CSN", "MRN", "ScrMRN", "DOB", "SEX", "POSTAL", "ER Time", "ER Date", "ER Day", "INJ DATE", "Hr", "Min",
                  "AM/PM", "I/O", "LOCATION", "AREA", "PLACE", "Diagnosis", "SK Narrative", "PHAC Narrative",
                  "W4P", "NO1", "BP1", "NO2", "BP2", "NO3", "BP3", 'veh', 'veh p', "Notes", 'LOS', "DISP",
                  "IN", "sub", "subID", 'sd1', "sd2", "sd3", "sd4", "sd5", "SPORTS CODE",
                  "E1", "E2", "E3", "E4", "CTAS", "Chief Complaint", "Problem List"]

    if "CNS" not in data.columns:
        raise NoCSNError("There is no CSN column in the excel file, this is crucial for database updates")

    missing_cols=[]
    for col in header:
        if col not in data.columns:
            missing_cols.append(col)

    if len(missing_cols) > 0:
        warn("The following columns are missing in the excel file: {}".format(",".join(missing_cols)))

    return data

def knee_threshold(scores):
    """
    Assumes scores are sorted descending.
    Finds the knee point using max deviation from straight line.
    """
    s = np.asarray(scores, dtype=float)
    n = len(s)
    x = np.linspace(0, 1, n)
    s_norm = (s - s.min()) / (s.max() - s.min() + 1e-12)
    line = s_norm[0] + (s_norm[-1] - s_norm[0]) * x
    idx = int(np.argmax(s_norm - line))
    return idx

def cumulative_mass_threshold(scores, mass=0.95):
    """
    Assumes scores are sorted descending.
    Returns threshold where cumulative sum reaches 'mass' fraction of total.
    """
    s = np.asarray(scores, dtype=float)
    fracs = np.cumsum(s) / sum(s)
    idx=sum(fracs<=mass)
    return idx-1
