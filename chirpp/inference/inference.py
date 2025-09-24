import re
import json
import pandas as pd
import torch

from transformers import (pipeline, AutoModelForSequenceClassification,
                          AutoTokenizer, AutoModelForCausalLM,
                          StoppingCriteria, StoppingCriteriaList
                          )

from sentence_transformers import SentenceTransformer
from chonkie import SemanticChunker
from chonkie import Model2VecEmbeddings

from chirpp.inference.prompts import prompt_dict

class NoModelError(Exception):
    pass


class StopOnSequence(StoppingCriteria):
    def __init__(self, stop_sequence_ids):
        self.stop_sequence_ids = stop_sequence_ids

    def __call__(self, input_ids, scores, **kwargs):
        # check if the last tokens match the stop sequence
        if input_ids.shape[1] < len(self.stop_sequence_ids):
            return False
        return (input_ids[0, -len(self.stop_sequence_ids):].tolist()
                == self.stop_sequence_ids)

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

    def classify(self):
        model_config=self.models["classification"]
        model=self._get_model(model_config)
        probs=model(self.notes, model_config["labels"])
        results=self._replace_labels(probs, model_config["labels"], model_config["cutoff"])
        return results


    def summarize(self):
        """
        hacky llamacpp output parsing to get the summary, this has a lot more flexibility than the rest of the columns
        because the output is just free text so it doesn't matter if there is a preceeiding or trailing space or anything like
        that.
        :return:
        """
        model_config = self.models["summary"]
        outputs=self._run_causal(model_config)
        summaries=[]
        for item in outputs:
            try:
                sm=json.loads(item)["summary"]
            except:
                sm=item.replace("{", "").replace("}", "").replace("summary", "").replace(":", "")
            finally:
                summaries.append(sm)

        return summaries

    def intent(self):
        model_config = self.models["intent"]
        model = self._get_model(model_config)
        probs = model(self.notes, model_config["labels"])
        results = self._replace_labels(probs, model_config["labels"], model_config["cutoff"])
        return results

    def substance(self):
        """
        parse the llamaccp output for the substance model, this is hacky because the llama outputs while mostly ok
        are not 100% reliable to have correct formatting and sometimes quites are in different placets etc.
        :return:
        """
        model_config = self.models["substance"]
        outputs = self._run_causal(model_config)
        subs=[]
        sub_ids=[]
        for res in outputs:
            subid=[item.lstrip() for item in
             res.replace("}", "").replace("{", "").replace("and ", ",").replace("'", "").split("sub_id:")[
                 1].lower().split(",") if len(item) > 1]
            subid=list(set(subid))
            if len(subid)>1:
                subs.append(1)
                sub_ids.append(sub_ids)
            else:
                subs.append(2)
                sub_ids.append(None)

        return subs, sub_ids


    def safety(self):
        model_config = self.models["safety"]
        outputs = self._run_causal(model_config)
        sd1=[]
        sd2=[]
        sd3=[]
        sd4=[]
        sd5=[]
        for item in outputs:
            try:
                item=json.loads(item["pred"].tolist()[0].replace("'", '"'))
                sd1.append(item["sd1"])
                sd2.append(item["sd2"])
                sd3.append(item["sd3"])
                sd4.append(item["sd4"])
                sd5.append(item["sd5"])
            except:
                item=re.sub(r"\'sd[0-9]\':", "", item).replace("}", "").\
                    replace("{", "").replace(" ", "").replace("'", "").split(",")
                sd1.append(item[0])
                sd2.append(item[1])
                sd3.append(item[2])
                sd4.append(item[3])
                sd5.append(item[4])

        return sd1, sd2, sd3, sd4, sd5

    def io(self):
        model_config = self.models["io"]
        outputs = self._run_causal(model_config)

        # TODO parse
        return outputs

    def time(self):
        model_config = self.models["time"]
        outputs = self._run_causal(model_config)

        # TODO parse
        return outputs

    def date(self):
        model_config = self.models["date"]
        outputs = self._run_causal(model_config)

        # TODO parse
        return outputs

    def ampm(self):
        model_config = self.models["ampm"]
        outputs = self._run_causal(model_config)

        # TODO parse
        return outputs

    def area(self):
        model_config = self.models["area"]
        outputs = self._run_causal(model_config)

        # TODO parse
        return outputs

    def location(self):
        model_config = self.models["location"]
        outputs = self._run_causal(model_config)

        # TODO parse
        return outputs

    def sports(self):
        model_config = self.models["sports"]
        outputs = self._run_causal(model_config)

        # TODO parse
        return outputs

    def chunk(self):
        model_config = self.models["classification"]
        model=self._get_model(model_config)
        chunks=model.chunk(self.notes)
        return chunks

    def embed(self, chunks):
        model_config = self.models["embeddings"]
        model=self._get_model(model_config)
        # this is a list of lists of tuples that is an index and list in the same order as the chunks which are in the
        # same order as the notes, each "chunk" instance is a list of strings
        embeddings=[]
        for text in chunks:
            text_embeddings=model.encode(text).tolist()
            embeddings.append([(index, item) for index, item in enumerate(text_embeddings)])
        # this will return a tensor of shape (n_chunks, embedding_dim) I need to split it
        # and make it something postgres compatible
        return embeddings

    # This is static, I might add something like specify which steps but I am not sure that it's needed
    def pipeline(self):
        pass

    def _get_model(self, config):
        if config["type"] == "classification":
            m = AutoModelForSequenceClassification.from_pretrained(config["model_dir"],
                                                                   config["num_labels"])
            t = AutoTokenizer.from_pretrained(config["model_dir"], padding=config["max_length"],
                                                      truncation=config["truncation"])
            model = pipeline("text-classification", model=m, tokenizer=t, device=self.device)
        elif config["type"] == "causal":
            m=AutoModelForCausalLM.from_pretrained(config["model_dir"], device_map="auto")
            t=AutoTokenizer.from_pretrained(config["model_dir"], padding=config["max_length"],
                                            truncation=config["truncation"])
            model = (m, t)
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

    #I've given up on llamacpp, gguf conversion is a mess, can't get it to work with cuda, I'm done.
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

    def _run_causal(self, config):
        model, tokenizer = self._get_model(config)

        stop_token_ids = tokenizer.encode(config["stop_token"], add_special_tokens=False)
        stopping_criteria = StoppingCriteriaList([StopOnSequence(stop_token_ids)])

        results=[]
        for note in self.notes:
            messages = [
                {"role": "system", "content": prompt_dict["system"]},
                {"role": "user", "content": prompt_dict[config["prompt_name"]] + note}]

            text = tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
            )
            model_inputs = tokenizer([text], return_tensors="pt").to(model.device)

            generated_ids = model.generate(
                **model_inputs,
                max_new_tokens=config["max_tokens"],
                do_sample=True,
                temperature=config["temperature"],
                eos_token_id=tokenizer.eos_token_id,
                stopping_criteria = stopping_criteria
            )
            output_ids = generated_ids[0][len(model_inputs.input_ids[0]):].tolist()
            content = tokenizer.decode(output_ids, skip_special_tokens=True)
            results.append(content)

        return results






