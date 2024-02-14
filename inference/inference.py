import torch
from sentence_transformers import SentenceTransformer, util
from transformers import pipeline, AutoModelForSequenceClassification, AutoTokenizer, AutoModelForSeq2SeqLM


class NoModelError(Exception):
    pass


class Inference:
    """
    This will perform the inference for classification and summarization
    """

    def __init__(self, classification_model, summarization_model, zshot_model, num_labels, device=None):
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
            classification_dir = classification_model
            model = AutoModelForSequenceClassification.from_pretrained(classification_dir, num_labels=num_labels)
            tokenizer = AutoTokenizer.from_pretrained(classification_dir, padding="max_length")
            self.clf = pipeline("text-classification", model=model, tokenizer=tokenizer, device=device)
        else:
            raise NoModelError("no classification model provided")

        if summarization_model is not None:
            summarization_dir = summarization_model
            model = AutoModelForSeq2SeqLM.from_pretrained(summarization_dir)
            tokenizer = AutoTokenizer.from_pretrained(summarization_dir, padding="max_length", truncation=True)
            self.summarizer = pipeline("summarization", model=model, tokenizer=tokenizer, device=device)
        else:
            raise NoModelError("no summarization model provided")

        if zshot_model is not None:
            self.zhot_pipeline = pipeline("zero-shot-classification", zshot_model, device=device)
        else:
            raise NoModelError("no zero shot model provided")

    def classify(self, notes, note_col="Note Text", include_labels=False):
        """

        :param notes:
        :param note_col:
        :param include_labels:
        :return:
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

    def zshot(self, notes, candidate_labels):
        preds = self.zhot_pipeline(notes, candidate_labels=candidate_labels)
        labels = [pred["labels"][0] for pred in preds]
        probs = [pred["scores"][0] for pred in preds]
        return labels, probs

    def is_injury(self, diags, injlist):
        """
        determine if this is an injury, this is here because it is not a column of the report, autofill is only
        concerned about filling in report columns
        :param diags: list of diagnosis from EPIC
        :param injlist: list of keywords that indicate injury, this is part of config.yaml
        :return: a boolean list
        """
        yes_no = []
        for diag in diags:
            is_inj = False
            for item in diag.split(" "):
                item = item.lower()
                for inj in injlist:
                    if item in injlist:
                        is_inj = True
            yes_no.append(is_inj)

        return yes_no
