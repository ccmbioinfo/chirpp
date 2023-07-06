import pandas as pd
import os
import re

def read_crystal_excel_file(path, filters, additional_columns=[]):
    """
    read crystal excel file
    :param path: path of the excel file
    :param additional_columns: what other columns to use other than CSN, MRN, Arrival date/time
    note text and note type
    :return: a pd.DataFrame of all the records of a specific visit
    """
    colnames = pd.read_excel(path, header=0, nrows=1)
    if "MRN" in colnames:
        df = pd.read_excel(path, header=0)
    else:
        df = pd.read_excel(path, header=1)
        if "MRN" not in df:
            raise ValueError("MRN column not found")
    df = df[
        [
            "CSN",
            "MRN",
            "Arrival Date",
            "Arrival Time",
            "Note Text",
            "Note Type",
        ] + additional_columns
    ]
    df["Arrival Date"] = pd.to_datetime(df["Arrival Date"])
    for key in list(filters.keys()):
        df=df[df[key].isin(filters[key])].copy()
    return df

def decode_scr_mrn(scr_mrn):
    scr_mrn = str(scr_mrn)
    mrn = scr_mrn[:-3] + scr_mrn[-2] + scr_mrn[-3]
    return int(mrn)

def read_chirpp_excel_file(path):
    """
    same as read_crystal_excel_file
    :param path: path of the excel file
    :return: pd.DataFrame of selected columns
    """
    with pd.ExcelFile(path) as xls:
        if "Data Entry" in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name="Data Entry")
        else:
            df = pd.read_excel(xls)
    if "PHAC Narrative" not in df and "Narrative" in df:
        df["PHAC Narrative"] = df["Narrative"]
    df = df[
        [
            "ScrMRN",
            "ER Date",
            "PHAC Narrative",
            "IN",
            "NO1",
            "BP1",
            "NO2",
            "BP2",
            "NO3",
            "BP3",
            "sub",
            "subID",
        ]
    ]

    df["MRN"] = df["ScrMRN"].apply(decode_scr_mrn)
    df = df.drop("ScrMRN", axis=1)
    df = df.drop(df[df["MRN"].isnull()].index)
    df["ER Date"] = df["ER Date"].astype(str)
    df["ER Date"] = pd.to_datetime(df['ER Date'])
    df["MRN"] = df["MRN"].astype(int)
    return df

