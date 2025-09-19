import torch
from sentence_transformers import SentenceTransformer, util
from transformers import pipeline, AutoModelForSequenceClassification, AutoTokenizer, AutoModelForSeq2SeqLM, AutoModel

from chonkie import SemanticChunker
from chonkie import Model2VecEmbeddings


class NoModelError(Exception):
    pass

from chirpp.inference.config import *

class SemanticChunking:
    def __init__(self, config):
        """

        :param chunking_mode:
        :param embedding_model:
        """
        self.chunking_model = Model2VecEmbeddings(chunking_model)
        self.embedding_model =
        self.chunk_size=chunk_size
        self.min_sentence=min_sentences
        self.threshold=threshold

    def chunk_notes(self, notes):
        """Chunk notes into semantic segments."""
        chunker = SemanticChunker(
            embedding_model=self.chunking_model,
            threshold=self.threshold,  # Similarity threshold (0-1) or (1-100) or "auto"
            chunk_size=self.chunk_size,  # Maximum tokens per chunk
            min_sentences=self.min_sentences,  # Initial sentences per chunk,
            return_type="texts"  # return a list of strings
        )
        chunks = chunker.chunk(notes) #this is a list of list of strings
        return chunks

    def get_embeddings(self, texts):
        model = SentenceTransformer(self.config["text_embedding_model"]["name"],
                                    **text_embedding_kwargs)
        embeddings = self.embedding_model.encode(texts)
        return embeddings


class Inference:
    """
    This will perform the inference for classification and summarization
    """

    def __init__(self, classification_model, summarization_model, classification_labels,
                 intent_model, intent_labels, substance_model, substance_labels, io_model, io_labels,
                 location_model, location_labels, area_model, area_labels, ampm_model, ampm_labels,
                 embedding_model, device=None):
        """

        :param classification_model:
        :param summarization_model:
        :param classification_labels:
        :param intent_model:
        :param intent_labels:
        :param substance_model:
        :param substance_labels:
        :param io_model:
        :param io_labels:
        :param location_model:
        :param location_labels:
        :param area_model:
        :param area_labels:
        :param ampm_model:
        :param ampm_labels:
        :param embedding_model:
        :param sd_model:
        :param sd_labels:
        :param tasks:
        :param device:
        """
        if device is None:
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        else:
            self.device = device
        self.classification_model = classification_model
        self.summarization_model = summarization_model
        self.classification_labels = classification_labels
        self.intent_model = intent_model
        self.intent_labels = intent_labels
        self.substance_model = substance_model
        self.substance_labels = substance_labels
        self.io_model = io_model
        self.location_model = location_model
        self.location_labels = location_labels
        self.area_model = area_model
        self.area_labels = area_labels
        self.ampm_model = ampm_model
        self.ampm_labels = ampm_labels
        self.embedding_model = embedding_model

    def generate_pipeline(self, model_dir, labels, taks_name, task_type="classification"):
        if model_dir is None:
            raise NoModelError("There is no model for {}".format(taks_name))

        if task_type == "classification":
            model = AutoModelForSequenceClassification.from_pretrained(model_dir)
            tokenizer = AutoTokenizer.from_pretrained(model_dir, padding="max_length", truncation=True)
            pipe = pipeline("text-classification", model=model_dir, tokenizer=tokenizer, device=self.device)
        elif task_type == "summarization":
            model = AutoModelForSeq2SeqLM.from_pretrained(model_dir, num_labels=labels)
            tokenizer = AutoTokenizer.from_pretrained(model_dir, padding="max_length", truncation=True)
            pipe = pipeline("summarization", model=model_dir, tokenizer=tokenizer,
                            device=self.device)
        elif task_type == "embeddings":
            model = AutoModel.from_pretrained(model_dir, add_pooling_layer=False)
            tokenizer=AutoTokenizer.from_pretrained(model_dir, padding="max_length", truncation=True,
                                                    return_tensors='pt', max_length=1024)
            pipe=(model, tokenizer)
        else:
            raise ValueError("invalid task type, it can only be 'classification', 'summarization', or 'embeddings'")
        return pipe

    def classify(self, notes, note_col="Note Text", include_labels=False):
        """
        :param notes: pre processed notes as a pd dataframe
        :param note_col: the column that contains the preprocessed notes
        :param include_labels: whether to inlcude the prediction labels, if false only the probability of being a chirpp
        is returned
        :return: model probabilities of being a chirpp case
        """

        if self.classification_model is not None:
            pipe = self.generate_pipeline(model_dir=self.classification_model,
                                          labels=self.classification_labels,
                                          taks_name="classification", task_type="classification")
        else:
            raise NoModelError("no classification model provided")

        to_infer = notes[~notes[note_col].isnull()][note_col].copy().to_list()
        labels = pipe(to_infer, padding=True, truncation=True)

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

        if self.summarization_model is not None:
            pipe = self.generate_pipeline(model_dir=self.substance_model,
                                          labels=0,
                                          taks_name="summarization", task_type="summarization")
        else:
            raise NoModelError("There is no substance model")

        to_infer = [str(note) for note in notes[note_col].to_list()]
        summaries = pipe(to_infer, truncation=truncation, max_length=max_length)
        summary_texts = []
        for summary in summaries:
            summary_texts.append(summary["summary_text"])

        return summary_texts

    def get_intent(self, notes, notes_col, label_dict, cutoff=0.8):
        """
        run intent classification with the specified model in __init__
        :param notes: dataframe with the notes
        :param notes_col: column where the notes are ideally these are pre-processed
        :param label_dict: label dict to look up chirpp codes to translate from torch labels
        :param cutoff: the model confidence cutoff, anything below that will be left blank
        :return: labels for intent in a list
        """

        if self.intent_model is not None:
            pipe = self.generate_pipeline(model_dir=self.intent_model,
                                          labels=self.intent_labels,
                                          taks_name="intent", task_type="classification")
        else:
            raise NoModelError("There is no intent model")

        to_infer = notes[notes_col].to_list()
        labels = pipe(to_infer, padding=True, truncation=True)

        edited_labels = []
        for lab in labels:
            edited = lab["label"]
            edited = edited.replace("LABEL_", "")
            actual = label_dict[edited]
            edited_labels.append(int(actual))

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

    def get_substance(self, notes, notes_col, cutoff=0.9):
        """
        determine whether substances are mentioned
        :param notes: same as abvoe
        :param notes_col: same as above
        :param cutoff: same as above
        :return: a list of labels
        """

        if self.substance_model is not None:
            pipe = self.generate_pipeline(model_dir=self.substance_model,
                                          labels=self.substance_labels,
                                          taks_name="substance", task_type="classification")
        else:
            raise NoModelError("There is no substance model")

        to_infer = notes[notes_col].to_list()
        labels = pipe(to_infer, padding=True, truncation=True)

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
        if self.io_model is not None:
            pipe = self.generate_pipeline(model_dir=self.io_model,
                                          labels=2,
                                          taks_name="io", task_type="classification")
        else:
            raise NoModelError("There is no io model")

        to_infer = notes[notes_col].to_list()
        labels = pipe(to_infer, padding=True, truncation=True)

        edited_labels = []
        for lab in labels:
            edited = lab["label"]
            edited = edited.replace("LABEL_", "")
            if edited == "0":
                edited = "I"
            else:
                edited = "O"
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

    def get_ampm(self, notes, notes_col, cutoff=0.9):
        """
        
        :param notes:
        :param notes_col:
        :param cutoff:
        :return:
        """
        if self.io_model is not None:
            pipe = self.generate_pipeline(model_dir=self.ampm_model,
                                          labels=self.ampm_labels,
                                          taks_name="ampm", task_type="classification")
        else:
            raise NoModelError("There is no ampm model")

        to_infer = notes[notes_col].to_list()
        labels = pipe(to_infer, padding=True, truncation=True)
        edited_labels = []
        for lab in labels:
            edited = lab["label"]
            edited = edited.replace("LABEL_", "")
            if edited == "0":
                edited = "a"
            else:
                edited = "p"
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

    def get_location(self, notes, notes_col, label_dict, cutoff=0.85):
        """

        :param notes:
        :param notes_col:
        :param label_dict:
        :param cutoff:
        :return:
        """
        if self.io_model is not None:
            pipe = self.generate_pipeline(model_dir=self.location_model,
                                          labels=self.location_labels,
                                          taks_name="location", task_type="classification")
        else:
            raise NoModelError("There is no location model")

        to_infer = notes[notes_col].to_list()
        labels = pipe(to_infer, padding=True, truncation=True)

        edited_labels = []
        for lab in labels:
            edited = lab["label"]
            edited = edited.replace("LABEL_", "")
            actual = label_dict[edited]
            edited_labels.append(int(actual))

        scores = []
        for lab in labels:
            scores.append(lab["score"])

        results = []
        for lab, scr in zip(edited_labels, scores):
            if scr >= cutoff and lab != '0':
                results.append(lab)
            else:
                results.append(None)

        return results

    def get_area(self, notes, notes_col, label_dict, cutoff=0.85):
        """

        :param notes:
        :param notes_col:
        :param label_dict:
        :param cutoff:
        :return:
        """
        if self.io_model is not None:
            pipe = self.generate_pipeline(model_dir=self.area_model,
                                          labels=self.area_labels,
                                          taks_name="area", task_type="classification")
        else:
            raise NoModelError("There is no area model")

        to_infer = notes[notes_col].to_list()
        labels = pipe(to_infer, padding=True, truncation=True)

        edited_labels = []
        for lab in labels:
            edited = lab["label"]
            edited = edited.replace("LABEL_", "")
            actual = label_dict[edited]
            edited_labels.append(int(actual))

        scores = []
        for lab in labels:
            scores.append(lab["score"])

        results = []
        for lab, scr in zip(edited_labels, scores):
            if scr >= cutoff and lab != '0':
                results.append(lab)
            else:
                results.append(None)

        return results

    def get_embeddings(self, notes, notes_col):
        """
        calculate embeddings for the cleaned up note texts this will be part of the full text search and outlier
        detection methods
        :param notes_col: notes, sames as above
        :param tasks: list of tasks to be passed to the model, if None just plain embeddings will be returned
        :return: a dictionary of embeddings where key is the task and the value is the embedding
        """
        if self.io_model is not None:
            pipe = self.generate_pipeline(model_dir=self.io_model,
                                          labels=2,
                                          taks_name="embeddings", task_type="embeddings")
            model = pipe[0].to(self.device)
            tokenizer = pipe[1]
        else:
            raise NoModelError("There is no embedding model")

        notes=notes[notes_col].to_list()
        tokenized=tokenizer(notes, padding=True, truncation=True, return_tensors="pt",
                            max_length=1024)
        tokenized=tokenized.to(self.device)

        with torch.no_grad():
            embeddings = model(**tokenized)[0][:, 0]

        return embeddings.to("cpu")


