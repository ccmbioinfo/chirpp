import os

from medspacy.section_detection import SectionRule

from .utils import *


class SectionRemover:
    """
    SectionRemover class for removing unnecessary sections for data pre-processing, these sections will then be used in
    model training for classification and summarization
    """

    def __init__(self, lang_model, remove_sections, keep_sections, rules_json, additional_rules=None, gpu=False):
        """
        class init, this sets up all the necessary sections
        :param lang_model: str name of the language model to use
        :param remove_sections: names of the sections to use these are "section_categories" an iterable preferably a list of tuple
        :param keep_sections: same as above for sections that we want to keep
        :param rules_json: collection of section rules in json format, this will override the default values.
        :param additional_rules: additional rules that are not in the rules.json thsee are not strings but they are SectioRule objects
        :param gpu: whether to use gpu or not, if no gpu is available will revert to cpu
        """
        if gpu:
            spacy.prefer_gpu()
        else:
            spacy.require_cpu()

        self.lang = lang_model
        nlp = spacy.load(self.lang)
        nlp.add_pipe("medspacy_sectionizer")
        sectionizer = nlp.get_pipe("medspacy_sectionizer")

        if rules_json is not None:
            sections = SectionRule.from_json(rules_json)
            sectionizer.add(sections)

        if additional_rules is not None:
            sectionizer.add(additional_rules)

        self.sectionizer = sectionizer
        self.nlp = nlp
        self.keep_sections = keep_sections
        self.rem_sections = remove_sections

    def remove_sections(self, text, keep_unlabelled):
        """
        remove/keep sections that are specified in the init method and return the new notes
        :param text: note_text, this is not series or list, it's just str
        :param keep_unlabelled: whether to keep a section if spacy cannot determine its category
        :return: cleaned up note_text as str
        """
        doc = self.nlp(text)
        kept_sections = []
        unclear_sections = []
        for section, body in zip(doc._.section_categories, doc._.section_bodies):
            if section in self.keep_sections:
                kept_sections.append(body)
            elif section in self.rem_sections:
                continue
            else:
                if keep_unlabelled:
                    unclear_sections.append(body)
                else:
                    continue
        clean_note = kept_sections + unclear_sections
        clean_note = " ".join([str(note) for note in clean_note])
        return clean_note


# also need to add some addition section headers for removal to remove doc names and abbreviations
# this is legacy for files
class Preprocess:
    """
    This is the class for preprocessing, it will get relevant note types, remove unwanted sections, fix abbreviations and will
    create 2 files one for summarization another for classification, the order of the notes will be the same in both files
    """

    def __init__(self, note_file, term_to_replace):
        """
        init method to get all the info needed to start preprocessing
        :param note_file: path to the excel file that is coming from EPIC
        :param term_to_replace: a dict of abbreviations to replace with their values
        """
        if os.path.exists(note_file):
            self.note_file = note_file
        else:
            raise FileNotFoundError("{} does not exist".format(note_file))

        self.terms_to_replace = term_to_replace
        self.raw_notes = None

    def read_raw_notes(self):
        """
        read unprocessed Crystal notes and filter out note types specified above
        :param path: path for the file
        :param additional_columns: what additional columns to read from the crystal file
        :param filters: a dict describing what kind of values to keep, for example {"Note Type":"ED Provider Notes"} will
        take only ED provider notes from the Note type column
        :return: self with raw section filled in
        """
        if self.note_file.endswith("xlsx"):
            notes = read_crystal_excel_file(path=self.note_file)
        elif self.note_file.endswith("txt"):
            notes=process_epic_dump(self.note_file)
        self.raw_notes = notes
        return self

    def get_relevant_notes(self, filters, additional_columns):
        df = self.raw_notes
        df = df[
            [
                "CSN",
                "MRN",
                "Arrival Date",
                "Arrival Time",
                "LINE",
                "Note Text",
                "Note Type",
            ] + additional_columns
            ]
        df["Arrival Date"] = pd.to_datetime(df["Arrival Date"])
        for key in list(filters.keys()):
            df = df[df[key].isin(filters[key])].copy()

        self.for_preprocess = df
        return self

    def merge_notes(self, section_remover=None, include_cols=None, group_cols=["CSN"],
                    orientation="front", keep_unlabelled=True, anonymize=True, language_model="en_core_web_trf",
                    line_col="Note Line"):
        """
        merge repeated notes of same visit into a single note text to be used by llms
        :param section_remover: an instance of SectionRemover
        :param include_cols: which additional columns to include in the note text like Chief complaint, diagnosis etc., an iterable
        :param group_cols: which columns to group by default is ["MRN", "Arrival Date"] this way each pandas.groupby will
        be specific to one visit of one patient, an iterable or str
        :param orientation: which way to add the extra columns, at the beginning of the note or at the end?, str
        :return: self with merged raw filled in
        """
        notes_grouped = self.for_preprocess.groupby(group_cols)

        merged_raw = []
        if include_cols is not None:  # to make sure that they are stored at the end, they do not change with the row
            # there will always be a single value
            group_cols = group_cols + include_cols

        for _, group in notes_grouped:
            df = group[group_cols].drop_duplicates()
            # I want to get the first files note at the top because I think that is more likely to contain the description
            # of what happened to the patient

            note_text = " ".join(
                [str(x) for x in
                 group.sort_values(by=["Note Type", line_col], ignore_index=True)["Note Text"].tolist()])

            note_text = remove_extra_spaces(note_text)

            if self.terms_to_replace is not None:
                note_text = replace_terms(note_text, self.terms_to_replace)

            if section_remover is not None:
                note_text = section_remover.remove_sections(note_text, keep_unlabelled)
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

            if anonymize:
                name = df["Patient Name"].drop_duplicates().to_list()

                note_text = deidentify(note_text, language_model, name)

            df["Note Text"] = note_text
            merged_raw.append(df)
        merged_raw = pd.concat(merged_raw)
        # TODO need to make this less hacky
        merged_raw = merged_raw[~merged_raw[["MRN", "Arrival Date"]].duplicated()]

        self.merged_raw = merged_raw
        return self





