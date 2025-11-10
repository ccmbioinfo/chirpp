import os

from chirpp.preprocess.utils import *

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
        
        from medspacy.section_detection import SectionRule
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

    def __init__(self, note_file, params, section_remover, keep_unlabelled=True, anonymize=False):
        """
        init method to get all the info needed to start preprocessing
        :param note_file: path to the excel file that is coming from EPIC
        :param term_to_replace: a dict of abbreviations to replace with their values
        """
        if os.path.exists(note_file):
            self.note_file = note_file
        else:
            raise FileNotFoundError("{} does not exist".format(note_file))

        self.params = params
        self.section_remover = section_remover
        self.keep_unlabelled = keep_unlabelled
        self.anonymize = anonymize

    def _read_raw_notes(self):
        """
        read unprocessed Crystal notes and or epic notes there is no filtering here, that will be done later
        :param path: path for the file
        :param additional_columns: what additional columns to read from the crystal file
        :param filters: a dict describing what kind of values to keep, for example {"Note Type":"ED Provider Notes"} will
        take only ED provider notes from the Note type column
        :return: dataframe with raw notes. This will be used for further processing, this contains all the original columns, there is
        not change to the dataframe
        """
        if self.note_file.endswith("xlsx"):
            notes = read_crystal_excel_file(path=self.note_file)
        elif self.note_file.endswith("txt"):
            notes = process_epic_dump(self.note_file)
        return notes

    def _merge_notes(self, notes, group_cols=["CSN"], line_col="Note Line", note_types=["ED Provider Notes", "ED Triage Notes"]):
        """
        Merge notes, in the EPIC database sometimes if a note is too long they are split into multiple lines, this will
        combine those lines into one note and return the dataframe where no other columns are changes. I am also removing
        the visits where there are no notes, even is LAMA there should be a triage note, if not how do we even know that they
        were a patient.
        :param notes: Notes dataframe from _read_raw_notes
        :param group_cols: Group the columns by csn, the CSN is unique for each patient visit so a patient can have multiple visits
        :param line_col: The column that shows the integer note line this is 1 based.
        :return: return the dataframe with merged notes. In addition to merging the notes I am replacing some abbreviations in the text
        the dict showing these are in the utils file
        """
        notes=notes[notes["Note Type"].isin(note_types)]
        notes_grouped = notes.groupby(group_cols)

        merged_raw = []
        for _, group in notes_grouped:
            df = group[group_cols].drop_duplicates()
            # I want to get the first files note at the top because I think that is more likely to contain the description
            # of what happened to the patient

            note_text = " ".join([str(x) for x in group.sort_values(by=["Note Type", line_col], ignore_index=True)[
                "Note Text"].tolist()])

            note_text = remove_extra_spaces(note_text)
            if self.params['terms_to_replace'] is not None:
                note_text = replace_terms(note_text, self.params['terms_to_replace'])

            df["Note Text"] = note_text
            merged_raw.append(df)
        merged_raw = pd.concat(merged_raw)
        merged_raw = merged_raw[~merged_raw[group_cols].duplicated()]
        return merged_raw

    def _remove_sections(self, merged_notes, raw_notes, section_remover, keep_unlabelled=True, anonymize=False, ):
        """
        take all the relevant notes but remove all the sections that we do not care about, these are things like vaccinations, vitals etc
        I am using medspacy for this. This reduces the number of tokens that need to be processed so that a CPU bound llamacpp server actually
        finishes the job.
        :param relevant_notes: output of _get_relevant_notes
        :param raw_notes: This is only needed if we need to anonymize the notes, because if I don't know the name of the patient I cannot remove it.
        :param section_remover: SectionRemover object, see above
        :param keep_unlabelled: If we are not sure about what a section may be then we decide to keep it or not.
        I'm defaulting to True, there are usually not that many of them but some pop here an there.
        :param anonymize: Whether to anonymize the notes or not, this will remove the patient name from the notes.
        :return:
        """
        processed_notes = []
        for csn, note in zip(merged_notes["CSN"], merged_notes["Note Text"]):
            note_text = section_remover.remove_sections(note, keep_unlabelled)
            processed_notes.append({"CSN": csn, "processed_notes": note_text})

        processed_notes = pd.DataFrame(processed_notes)
        if anonymize:
            names_removed = []
            processed_notes.merge(raw_notes[["CSN", "Patient Name"]], how="left", on="CSN")
            for name, notes in zip(processed_notes["Patient Name"].tolist(), processed_notes["processed_notes"].tolist()):
                notes = deidentify(notes, section_remover.nlp, name)
                names_removed.append(notes)
            processed_notes["processed_notes"] = names_removed

        return processed_notes

    def preprocess_pipeline(self):
        """
        run the whole pipeline of preprocessing, this will read the notes, merge them, get relevant notes, remove sections and
        return the processed notes
        :return: dataframe with processed notes and raw notes
        """
        raw_notes = self._read_raw_notes()
        merged_notes = self._merge_notes(raw_notes, self.params["group_cols"], 
                                         self.params["line_col"], note_types=self.params["note_types"])
        processed_notes = self._remove_sections(merged_notes, raw_notes, self.section_remover, self.keep_unlabelled,
                                               self.anonymize)

        return raw_notes, processed_notes