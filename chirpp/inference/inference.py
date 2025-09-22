import pandas as pd
import torch

from transformers import (pipeline, AutoModelForSequenceClassification,
                          AutoTokenizer)

from sentence_transformers import SentenceTransformer
from llama_cpp import Llama
from chonkie import SemanticChunker
from chonkie import Model2VecEmbeddings

from chirpp.inference.prompts import prompt_dict

class NoModelError(Exception):
    pass

class SemanticChunking:
    def __init__(self, chunking_model, chunk_size=100, min_sentences=1,
                 threshold=0.8):
        """

        :param chunking_model:
        :param chunk_size:
        :param min_sentences:
        :param threshold:
        :param text_embedding_kwargs
        """
        self.chunking_model = Model2VecEmbeddings(chunking_model)
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

class Inference:
    """
    This will perform the inference for classification and summarization
    """

    def __init__(self, model_dict, notes, device=None):
        """
        init method, specify pipeline parameters for classification and summarization
        :param classification_model: model directory for the trained classification model
        :param summarization_model: model directory for summarization model
        :param num_labels: number of labels to infer this has to match the training data
        :param device: whether to use gpu or cpu, if None will default to whatever gpu torch finds or cpu
        """
        if device is None:
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        else:
            self.device = device
        self.models=model_dict
        self.notes=notes

    #TODO return tuple, 0/1 chirpp or not and the actual probs
    def classify(self):
        model_config=self.models["classification"]
        model=self._get_model(model_config)
        probs=model(self.notes, model_config["labels"])
        results=self._replace_labels(probs, model_config["labels"], model_config["cutoff"])
        return results


    def summarize(self):
        model_config = self.models["summary"]
        outputs=self._run_llama(model_config)

        # TODO parse
        return outputs

    def intent(self):
        model_config = self.models["intent"]
        model = self._get_model(model_config)
        probs = model(self.notes, model_config["labels"])
        results = self._replace_labels(probs, model_config["labels"], model_config["cutoff"])
        return results

    def substance(self):
        model_config = self.models["substance"]
        outputs = self._run_llama(model_config)

        # TODO parse
        return outputs

    def io(self):
        model_config = self.models["io"]
        outputs = self._run_llama(model_config)

        # TODO parse
        return outputs

    def time(self):
        model_config = self.models["time"]
        outputs = self._run_llama(model_config)

        # TODO parse
        return outputs

    def date(self):
        model_config = self.models["date"]
        outputs = self._run_llama(model_config)

        # TODO parse
        return outputs

    def ampm(self):
        model_config = self.models["ampm"]
        outputs = self._run_llama(model_config)

        # TODO parse
        return outputs

    def area(self):
        model_config = self.models["area"]
        outputs = self._run_llama(model_config)

        # TODO parse
        return outputs

    def safety(self):
        model_config = self.models["safety"]
        outputs = self._run_llama(model_config)

        # TODO parse
        return outputs

    def location(self):
        model_config = self.models["location"]
        outputs = self._run_llama(model_config)

        # TODO parse
        return outputs

    def sports(self):
        model_config = self.models["sports"]
        outputs = self._run_llama(model_config)

        # TODO parse
        return outputs

    def chunk(self):
        model_config = self.models["classification"]
        model=self._get_model(model_config)
        chunks=model.chunk(self.notes)
        return chunks

    #TODO
    def embed(self, chunks):
        model_config = self.models["embeddings"]
        model=self._get_model(model_config)
        # this is a list of lists of ndarrays in the same order as the chunks which are in the
        # same order as the notes
        embeddings=[]
        for text in chunks:
            text_embeddings=model.encode(text, convert_to_tensor=False)
            embeddings.append(text_embeddings)
        # this will return a tensor of shape (n_chunks, embedding_dim) I need to split it
        # and make it something postgres compatible
        return embeddings

    # This is fixed, I might add something like specify which steps but I am not sure that it's needed
    def pipeline(self):
        pass

    def _get_model(self, config):
        if config["type"] == "classification":
            m = AutoModelForSequenceClassification.from_pretrained(config["model_dir"],
                                                                   config["num_labels"])
            t = AutoTokenizer.from_pretrained(config["model_dir"], padding=config["max_length"],
                                                      truncation=config["truncation"])
            model = pipeline("text-classification", model=m, tokenizer=t, device=self.device)
        elif config["type"] == "gguf":
            model=Llama(model_path=config["model_dir"], n_ctx=4096, n_gpu_layers=0,
                        n_threads=config["n_threads"])
        elif config["type"] == "chunking":
            model=SemanticChunking(chunking_model=config["model"],
                                   chunk_size=config["chunk_size"],
                                   min_sentences=config["min_sentences"],
                                   threshold=config["threshold"])
        elif config["type"] == "embeddings":
            model=SentenceTransformer(config["model_dir"])

        return model

    def _replace_labels(self, preds, label_dict, cutoff):

        edited_labels=[]
        for lab in preds:
            edited = lab["label"]
            edited = edited.replace("LABEL_", "")
            actual=label_dict[edited]
            edited_labels.append(int(actual))

        scores=[]
        for lab in preds:
            scores.append(lab["score"])

        results=[]
        for lab, scr in zip(edited_labels, scores):
            if scr >= cutoff:
                results.append(lab)
            else:
                results.append(None)
        return results

    def _run_llama(self, config):
        model = self._get_model(config)
        messages = [
            {"role": "system", "content": prompt_dict["system"]},
            {"role": "user", "content": None},
        ]

        results = []
        for note in self.notes:
            messages[1]["content"] = prompt_dict[config["prompt_name"]] + note
            output = model.create_chat_completion(messages=messages)
            results.append(output["choices"][0]["message"]["content"])

        return results

    def _get_probs(self, database, start_date, complaint_filter):
        """
        Get the minimum probability of a visit based on chief complaints and start date.
        :param database:
        :param start_date:
        :param complaint_filter:
        :return:
        """
        probs = pd.read_sql(
            f"select min(probs) from visits where chief_complaint in {','.join(complaint_filter)} and arrival_date >= '{start_date}'",
            con=database.engine)

        return probs[0]



