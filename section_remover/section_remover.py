import spacy

from medspacy.section_detection import SectionRule


class SectionRemover:
    """
    SectionRemover class for removing unecessary sections for data pre-processing, these sections will then be used in
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
