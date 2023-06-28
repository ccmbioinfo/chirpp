import re
import spacy
from negspacy.negation import Negex
from negspacy.termsets import termset
import medspacy
from medspacy.section_detection import Sectionizer
import spacy_transformers
import scispacy
from medspacy.context import ConTextRule
from medspacy.section_detection import SectionRule
from datetime import datetime
from grammarly import textFix

# Step 1, import pandas and the data
import pandas as pd

df = pd.read_excel("jan_2023-Copy1.xlsx", sheet_name=1)

skNarCol = df["SK Narrative"]
testNar = skNarCol[0]


class Summary():
    def __init__(self):
        """
        Initialize a Summary object.

        This class provides functionality for summarizing medical narratives.
        It initializes the necessary components and variables.
        """
        self.mednlp = None
        self.negnlp = None
        self.sent_rem_list = []
        self.section_rem_list = ["past_medical_history","family_history","patient_instructions","education","patient_education","observation_and_plan","history_of_present_illness","medications","allergies","allergy","imaging","transfer in / advice note","consult","hospital_course", "labs_and_studies","comments", "social_history" ,"physical_exam","other", "useless"]
        self.keep_sections = ["ED Provider Notes", "ED Triage Notes","Consult","Consult Note","Consults","Consult Notes"]
        self.keep_sent = ["bsa","tbsa", "km/hr", "km/h", "m/s", "body surface"]
        self.ts = termset("en_clinical")
        self.load_nlp()

    def checker(self, text):
        """
        Check if a given text should be skipped for processing.

        Args:
        - text (str): The input text to check.

        Returns:
        - bool: True if the text should be skipped, False otherwise.
        """
        if(len(text) == 0): return True
        if(text == " "): return True
        for string in self.sent_rem_list:
            if(string.lower() in text.lower()): return True
        return False

    def split_sentences(self, text):
        """
        Split a given text into sentences.

        Args:
        - text (str): The input text to split.

        Returns:
        - list: A list of sentences extracted from the input text.
        """
        nlp = spacy.load("en_core_sci_scibert")
        doc = nlp(text)
    
        sentences = []
        sentence = ''
        
        for token in doc:
            if token.text == '.' or token.text.isspace():
                if sentence.strip():
                    sentences.append(sentence.strip())
                sentence = ''
            else:
                sentence += token.text_with_ws
        
        if sentence.strip():
            sentences.append(sentence.strip())
        
        return sentences

    def lemmatize(self, note):
        """
        Lemmatize the words in a given narrative.

        Args:
        - note (str): The input narrative to lemmatize.

        Returns:
        - str: The lemmatized version of the input narrative.
        """
        doc = self.negnlp(note)
        lemNote = [wd.lemma_ for wd in doc]
        return " ".join(lemNote)

    def load_negnlp(self):
        """
        Load the negation model for handling negation in narratives.
        """
        nlp = medspacy.load()
        context = nlp.get_pipe("medspacy_context")
        
        context_rules = [
            ConTextRule(literal="Suspected COVID", category="USELESS",
                direction="BACKWARD",
                max_scope=7),
            ConTextRule(literal="Negative", category="NEGATED_EXISTENCE",
                direction="BIDIRECTIONAL",
                max_scope=7),
        ]
        
        context.add(context_rules)

        self.negnlp = nlp
    
    def negation_handling(self, text):
        """
        Handle negation in a given text.

        Args:
        - text (str): The input text to handle negation in.

        Returns:
        - str: The text with negation handled.
        """
        output = []
        sents = self.split_sentences(text)
        
        for sent in sents:
            doc = self.negnlp(sent)
            modifiers = doc._.context_graph.modifiers
            spans_to_remove = []
            curr_sent = []
        
            for modifier in modifiers:
                if modifier.category == "NEGATED_EXISTENCE":
                    mod_span = modifier.modifier_span
                    target_span = modifier.scope_span
                    spans_to_remove.extend(range(mod_span[0]-1,mod_span[-1]))
                    spans_to_remove.extend(range(target_span[0]-1,target_span[-1]))

            for i in range(len(doc)):
                if (i in spans_to_remove): continue
                curr_sent.append(str(doc[i]))
            output.append(curr_sent)
        
        op = [" ".join(i)for i in output]
        op1 = list(filter(lambda x: x != "", op))
        return ". ".join(op1)
    
    def manual_section_remover(self, narrative):
        """
        Remove sections that are useless for parsing through.

        Args:
        - narrative (str): The input narrative to remove useless sections from.

        Returns:
        - str: The narrative with useless sections removed.
        """
        obj = narrative.split("\n")
        obj = [i for i in obj if i]
        good_sections = []

        for i in range(len(obj)):
            if(obj[i] in self.keep_sections and i != len(obj)):
                good_sections.append(obj[i + 1])
        return ". ".join(good_sections)

    def load_mednlp(self):
        """
        Load the medspacy model for processing medical text.
        """
        mednlp = medspacy.load()
        sectionizer = mednlp.add_pipe("medspacy_sectionizer")
        self.mednlp = mednlp
    
    def sub_section_remover(self, note):
        """
        Remove subsections from a given note.

        Args:
        - note (str): The input note to remove subsections from.

        Returns:
        - str: The note with subsections removed.
        """
        doc = self.mednlp(note)
        counter = -1
        for section in doc._.sections:
            counter+=1
            if(section.category not in self.section_rem_list):
                print("---"*10)
                print(section.category, doc._.section_spans[counter])
                print("---"*10)
                continue
            note = note.replace(str(doc._.section_spans[counter]),"")
        return note
    
    def load_nlp(self):
        """
        Load the necessary models and components for text processing.
        """
        self.load_mednlp()
        self.load_negnlp()
        
    def summarize(self, note):
        """
        Summarize a given medical note.

        Args:
        - note (str): The input medical note to summarize.

        Returns:
        - str: The summarized version of the input note.
        """
        start_time = datetime.now()
        res1 = self.manual_section_remover(note)
        print("res1:" ,res1 + "\n")
        try:
            res2 = self.sub_section_remover(res1)
            print("res2:" ,res2 + "\n")
            res3 = self.negation_handling(res2)
            if(len(res3) == 0 or len(res2) == 0):
                if(len(res2) == 0):
                    return res1
                return res2
            end_time = datetime.now()
            time_difference = end_time - start_time
            print("Time to compute: ", time_difference)
            return res3
        except:
            return res1
            
summarizer = Summary()

def make_nars(note):
    """
    Generate a summarized version of a given medical note.

    Args:
    - note (str): The input medical note.

    Returns:
    - str: The summarized version of the input note.
    """
    testNar = note
    res = summarizer.summarize(testNar)
    return res

        

