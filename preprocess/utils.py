import re

import pandas as pd
import spacy
import Levenshtein as ls
from math import ceil

spacy.prefer_gpu()

class MultipleNamesError(Exception):
    pass

def split(ls, max_size, combine=True, join_w=" "):
    """
    if the note lenght is too long split it down in the middle, this is for deidentification only it will not effect the
    document itself see deidenitfy below
    :param ls: note text as a list
    :param max_size: maximum size allowed
    :param combine: combine the individual tokens back together with
    :param join_w: the separator for the combination
    :return: another list but the note text is split into n pieces depending on the max_size
    """
    n = ceil(len(ls) / max_size)
    size = ceil(len(ls) / n)
    split_list = [ls[i * size:i * size + size] for i in range(n)]
    if combine:
        combined = []
        for ls in split_list:
            combined.append(join_w.join(ls))
        return combined
    else:
        return split_list

def deidentify(note_text, language_model, name):
    """

    :param df:
    :param language_model:
    :param name_col:
    :param text_col:
    :return:
    """
    nlp=spacy.load(language_model)

    if len(name) > 1:
        raise MultipleNamesError("There are multiple patients by that CSN")
    else:
        name = name[0].lower()
        name = name.replace(",", " ").split(" ")

        note_text = str(note_text)
        note_text = note_text.lower()
        note_text = re.sub(" +", " ", note_text)
        split_note = note_text.split(" ")
        note_len = len(split_note)
        docs = []
        if note_len > 512:  # if the note is really long unlikely but possible > 512 words
            split_notes = split(split_note, 512, combine=True, join_w=" ")
            for note in split_notes:
                docs.append(nlp(note))
        else:
            docs.append(nlp(note_text))
        people = []
        for doc in docs:
            people = people + [ent for ent in doc.ents if ent.label_ == "PERSON"]

        for word in name:
            for person in people:
                person = str(person)
                person_split = person.split(" ")
                for person_word in person_split:
                    dist = ls.distance(word, str(person_word))
                    if len(word) < 4:  # no typos
                        if dist == 0:
                            note_text = note_text.replace(person, "[redacted]")
                    elif len(word) < 6:
                        if dist <= 1:
                            note_text = note_text.replace(person, "[redacted]")
                    else:
                        if dist <= 2:
                            note_text = note_text.replace(person, "[redacted]")
        # removing these because they do not contain any important information contain patient info
        note_text = re.sub("mrn(:| )*[0-9]+", "[redacted]", note_text)
        note_text = re.sub(" dob(:| )*[0-9]+/[0-9]+/[0-9]+", "[redacted]", note_text)

        # note_df=note_df.drop(columns=["Patient Name", "CSN"])
        return note_text


def read_crystal_excel_file(path):
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
        df = pd.read_excel(path, header=0, skiprows=1)
        if "MRN" not in df:
            raise ValueError("MRN column not found")

    return df


def remove_extra_spaces(text):
    """
    remove extra spaces and from the text other kinds of whitespace are handles elsewhere
    :param text: note text, string
    :return: modified note text, string
    """
    words = text.split()
    new_text = ' '.join(words)
    return new_text

def replace_terms(text, to_fix):
    """
    replace abbreviations with longer form if present
    :param text: note text ideally after the extra white spaces have been removed
    :param to_fix: dictionary of abbreviations and their long form
    :return:
    """
    for key in to_fix.keys():
        to_find = "{}{}{}".format("(?<![a-zA-Z0-9])", key, "(?![a-zA-Z0-9])")
        to_find = re.compile(to_find)
        modified_text = re.sub(to_find, to_fix[key], text)
        return modified_text
