import pandas as pd
from tqdm import tqdm

from .utils import read_chirpp_excel_file, read_crystal_excel_file


class PreprocessForClassfication:
    """
    This is the class for preprocessing for binary classification, I'm writing this in a way that methods can be
    chained ala pandas or numpy. This I think makes it easier to use, this might change in the future,
    the util will definitely change with migration to EPIC workbooks
    """

    def __init__(self, mapping_file, note_types, pos_complaints, **kwargs):
        """
        init method
        :param mapping_file: a txt file that has 2 columns, processed (these are manually labelled) and raw (crystal notes)
        there does not need to be 1:1 mapping, if some months do not have processed files that's ok (see below). This is the path
        to the txt file.
        :param note_types: which note types to use such as "ED Provider Notes" etc, an iterable
        :param pos_complaints: values that are definitely chirpp postive cases in the "Cheif Complaint" column, an iterable
        :param kwargs: passed to pd.read_csv for different parameters
        """
        self.preprocessed = None
        self.processed = None
        self.raw = None
        self.merged_raw = None
        self.files = pd.read_csv(mapping_file, **kwargs)
        self.note_types = note_types
        self.pos_complaints = pos_complaints

    def read_processed_notes(self, processed_col="processed_files"):
        """
        read processed manually labelled files
        :param processed_col: name of the column in self.files
        :return: self with processed filled in
        """
        notes = []
        for file in tqdm(self.files[processed_col].tolist()):
            dat = read_chirpp_excel_file(file)
            notes.append(dat)
        notes = pd.concat(notes).reset_index(drop=True).drop_duplicates()
        notes["label"] = 1  # this is only for classification of whether chirpp or not
        self.processed = notes
        return self

    def read_raw_notes(self, use_unlabelled, raw_col="raw_files", processed_col="processed_files",
                       additional_columns=[]):
        """
        read unprocessed Crystal notes and filter out note types specified above
        :param use_unlabelled: Whether to use the file if it does not have a corresponding manually labelled file
        :param raw_col: the name of the column that contains the raw file paths
        :param processed_col: same as above
        :param additional_columns: what additional columns to read from the crystal file
        :return: self with raw section filled in
        """
        notes = []
        for processed, raw in tqdm(zip(self.files[processed_col].tolist(), self.files[raw_col].tolist())):
            if pd.isna(processed):
                if use_unlabelled:
                    dat = read_crystal_excel_file(raw, additional_columns)
                    notes.append(dat)
                else:
                    continue
        notes = pd.concat(notes).reset_index(drop=True).drop_duplicates()
        notes = notes[notes["Note Type"].isin(self.note_types)]
        self.raw = notes
        return self

    def merge_notes(self, section_remover=None, include_cols=None, group_cols=None, orientation="front"):
        """
        merge repeated notes of same visit into a single note text to be used by llms
        :param section_remover: an instance of SectionRemover
        :param include_cols: which additional columns to include in the note text like Chief complaint, diagnosis etc., an iterable
        :param group_cols: which columns to group by default is ["MRN", "Arrival Date"] this way each pandas.groupby will
        be specific to one visit of one patient, an iterable or str
        :param orientation: which way to add the extra columns, at the beginning of the note or at the end?, str
        :return: self with merged raw filled in
        """
        if group_cols is None:
            group_cols = ["MRN", "Arrival Date"]
        notes_grouped = self.raw.groupby(group_cols)
        merged_raw = []
        if include_cols is not None:  # to make sure that they are stored at the end, they do not change with the row
            # there will always be a single value
            group_cols = group_cols + include_cols
        for _, group in notes_grouped:
            df = group[group_cols].drop_duplicates()
            # I want to get the first files note at the top because I think that is more likely to contain the description
            # of what happened to the patient
            note_text = " ".join(
                [str(x) for x in group.sort_values(by=["File Time"], ignore_index=True)["Note Text"].tolist()])
            if section_remover is not None:
                note_text = section_remover.remove_sections(note_text)
            # add them one by one so there is more flexibility but at the cost of speed, these columns are things like
            # diagnoses, chief complaints etc. They are included as long as they are strings
            if include_cols is not None:
                for col in include_cols:
                    to_include = group[col].drop_duplicates().tolist()
                    if type(to_include) != str:
                        continue
                    else:
                        if orientation == "front":
                            note_text = " ".join([to_include, note_text])
                        elif orientation == "back":
                            note_text = " ".join([note_text, to_include])
                        else:
                            raise ValueError("orientation can be either front or back")
            df["Note Text"] = note_text
            merged_raw.append(df)
        merged_raw = pd.concat(merged_raw)
        self.merged_raw = merged_raw
        return self

    def add_labels(self, use_chirpp_column, positive_complaints, merge_columns):
        """
        add labels for classification
        :param use_chirpp_column: whether to use the "CHIRPP Icon column bool
        :param positive_complaints: list of Chief Complaints that are definitely chirpp +
        :param merge_columns: a dict of column names mapping columns of Crystal notes to processed excel files
        :return: self with processed filled in
        """
        dat = self.merged_raw
        dat["label"] = None
        if positive_complaints is not None:
            dat["label"][dat["Chief Complaint"].isin(positive_complaints)] = 1
        if use_chirpp_column:
            dat["label"][~pd.isna(dat["CHIRPP Icon"])] = 1
        merged = dat.merge(self.processed[list(merge_columns.values)], how="left",
                           left_on=list(merge_columns.keys), right_on=list(merge_columns.values))
        merged["label"][pd.isna(merged["label"])] = 0
        self.preprocessed = merged
        return self

    def write_labeled_notes(self, file_path, **kwargs):
        """
        save processed notes to dist
        :param file_path: file path
        :param kwargs: additional arguments to pandas.to_csv
        :return: None, save file to disk
        """
        self.processed.to_csv(file_path, **kwargs)


class PreprocessForSummary:
    pass
