import torch
from sentence_transformers import SentenceTransformer, util
from transformers import pipeline, AutoModelForSequenceClassification, AutoTokenizer, AutoModelForSeq2SeqLM


class NoModelError(Exception):
    pass


class Inference:
    """
    This will perform the inference for classification and summarization
    """

    def __init__(self, classification_model, summarization_model, classification_labels,
                 intent_model, intent_labels, substance_model, substance_labels, io_model, io_labels,
                 device=None):
        """
        init method, specify pipeline parameters for classification and summarization
        :param classification_model: model directory for the trained classification model
        :param summarization_model: model directory for summarization model
        :param num_labels: number of labels to infer this has to match the training data
        :param device: whether to use gpu or cpu, if None will default to whatever gpu torch finds or cpu
        """
        if device is None:
            device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

        if classification_model is not None:
            model = AutoModelForSequenceClassification.from_pretrained(classification_model, num_labels=classification_labels)
            tokenizer = AutoTokenizer.from_pretrained(classification_model, padding="max_length")
            self.clf = pipeline("text-classification", model=model, tokenizer=tokenizer, device=device)
        else:
            raise NoModelError("no classification model provided")

        if summarization_model is not None:
            model = AutoModelForSeq2SeqLM.from_pretrained(summarization_model)
            tokenizer = AutoTokenizer.from_pretrained(summarization_model, padding="max_length", truncation=True)
            self.summarizer = pipeline("summarization", model=model, tokenizer=tokenizer, device=device)
        else:
            raise NoModelError("no summarization model provided")

        if intent_model is not None:
            model = AutoModelForSequenceClassification.from_pretrained(intent_model,
                                                                       num_labels=intent_labels)
            tokenizer = AutoTokenizer.from_pretrained(intent_model, padding="max_length")
            self.intent_clf = pipeline("text-classification", model=model, tokenizer=tokenizer, device=device)
        else:
            raise NoModelError("There is no intent model")

        if substance_model is not None:
            model = AutoModelForSequenceClassification.from_pretrained(substance_model,
                                                                       num_labels=substance_labels,
                                                                       ignore_mismatched_sizes=True)
            tokenizer = AutoTokenizer.from_pretrained(substance_model, padding="max_length")
            self.substance_clf = pipeline("text-classification", model=model, tokenizer=tokenizer, device=device)
        else:
            raise NoModelError("There is no substance model")

        if io_model is not None:
            model = AutoModelForSequenceClassification.from_pretrained(io_model,
                                                                       num_labels=io_labels)
            tokenizer = AutoTokenizer.from_pretrained(io_model, padding="max_length")
            self.io_clf = pipeline("text-classification", model=model, tokenizer=tokenizer, device=device)
        else:
            raise NoModelError("There is no inside outside model")

    def classify(self, notes, note_col="Note Text", include_labels=False):
        """
        :param notes: pre processed notes as a pd dataframe
        :param note_col: the column that contains the preprocessed notes
        :param include_labels: whether to inlcude the prediction labels, if false only the probability of being a chirpp
        is returned
        :return: model probabilities of being a chirpp case
        """

        if self.clf is None:
            raise NoModelError("No model has been specified for classification")

        to_infer = notes[~notes[note_col].isnull()][note_col].copy().to_list()
        labels = self.clf(to_infer, padding=True, truncation=True)

        edited_labels = []
        for lab in labels:
            edited = lab["label"]
            edited = edited.replace("LABEL_", "")
            edited = int(edited)
            edited_labels.append(edited)

        scores = []
        for lab in labels:
            scores.append(lab["score"])

        report_probs = []
        for label, score in zip(edited_labels, scores):
            if label == 0:
                report_probs.append(1 - score)
            else:
                report_probs.append(score)

        if include_labels:
            return edited_labels, report_probs
        else:
            return report_probs

    def summarize(self, notes, note_col="Note Text", truncation=True, max_length=128):
        """
        run summarization using the specified moden in __init
        :param notes: notes, dataframe
        :param note_col: a column within the dataframe to summarize ideally this is the pre-processed notes
        :param truncation: whether to trunctate the texts if its longer than the model max
        :param max_length: model max length
        :return: summaries in a list
        """
        if self.summarizer is None:
            raise NoModelError("No model has been specified for summarization")

        to_infer = [str(note) for note in notes[note_col].to_list()]
        summaries = self.summarizer(to_infer, truncation=truncation, max_length=max_length)
        summary_texts = []
        for summary in summaries:
            summary_texts.append(summary["summary_text"])

        return summary_texts

    def calculate_cosine_distances(self, model, notes, summaries):
        """
        calculate the cosine distance between the generated summary and the cleaned note text, this uses the cleaned text not just the hpi section
        :param model: name of the model
        :param notes: list of "sections_removed" notes
        :param summaries: list of summaries
        :return: list of cosine distances in the same order as the notes and the summaries
        """
        model = SentenceTransformer(model)

        distances = []
        for summary, note in zip(notes, summaries):
            em1 = model.encode(summary)
            em2 = model.encode(note)
            dist = util.cos_sim(em1, em2)
            distances.append(float(dist[0]))

        return distances

    def get_intent(self, notes, notes_col, label_dict, cutoff=0.8):
        """
        run intent classification with the specified model in __init__
        :param notes: dataframe with the notes
        :param notes_col: column where the notes are ideally these are pre-processed
        :param label_dict: label dict to look up chirpp codes to translate from torch labels
        :param cutoff: the model confidence cutoff, anything below that will be left blank
        :return: labels for intent in a list
        """
        to_infer=notes[notes_col].to_list()
        labels = self.intent_clf(to_infer, padding=True, truncation=True)

        edited_labels = []
        for lab in labels:
            edited = lab["label"]
            edited = edited.replace("LABEL_", "")
            actual= label_dict[edited]
            edited_labels.append(int(actual))

        scores = []
        for lab in labels:
            scores.append(lab["score"])

        results=[]
        for lab, scr in zip(edited_labels, scores):
            if scr >= cutoff:
                results.append(lab)
            else:
                results.append(None)

        return results


    def get_substance(self, notes, notes_col, cutoff=0.9):
        """
        determine whether substances are mentioned
        :param notes: same as abvoe
        :param notes_col: same as above
        :param cutoff: same as above
        :return: a list of labels
        """
        to_infer = notes[notes_col].to_list()
        labels = self.substance_clf(to_infer, padding=True, truncation=True)

        edited_labels = []
        for lab in labels:
            edited = lab["label"]
            edited = edited.replace("LABEL_", "")
            edited = int(edited) + 1
            edited_labels.append(edited)

        scores = []
        for lab in labels:
            scores.append(lab["score"])

        results = []
        for lab, scr in zip(edited_labels, scores):
            if scr >= cutoff:
                results.append(lab)
            else:
                results.append(None)

        return results

    def get_io(self, notes, notes_col, cutoff=0.9):
        """
        determine whether the incident happened inside or outside
        :param notes: same as above
        :param notes_col: same as above
        :param cutoff: same as above
        :return: labels in a list
        """
        to_infer = notes[notes_col].to_list()
        labels = self.io_clf(to_infer, padding=True, truncation=True)

        edited_labels = []
        for lab in labels:
            edited = lab["label"]
            edited = edited.replace("LABEL_", "")
            edited = int(edited)+1
            edited_labels.append(edited)

        scores = []
        for lab in labels:
            scores.append(lab["score"])

        results = []
        for lab, scr in zip(edited_labels, scores):
            if scr >= cutoff:
                results.append(lab)
            else:
                results.append(None)

        return results
