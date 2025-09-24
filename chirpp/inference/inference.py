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


def get_probs(database, end_date, complaint_filter, time_delta=30):
    """
    get the chirpp dynamic cutoff based on the previous month
    :param database: chirpp.database.Database instance
    :param end_date: this is the min date for the month, we are only looking at the previous month
    :param complaint_filter: fixed list of chief complaints to filter on
    :param time_delta: how many days back to look, default is 30
    :return: float of the min probability for the given chief complaints in the previous month based on the distilbert model
    """
    #TODO this is not correct, need to add an end date filter as well
    start_date=pd.to_datetime(end_date)+pd.Timedelta(days=time_delta)
    probs = pd.read_sql(
        f'select min(probs) from visits where chief_complaint in {','.join(complaint_filter)} and arrival_date >= \'{start_date} and arrival_date <= \'{end_date}\'',
        con=database.engine)

    return probs[0]


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

    def __init__(self, model_dict, device=None):
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

    def classify(self, notes):
        model_config=self.models["classification"]
        model=self._get_model(model_config)
        probs=model(notes, model_config["labels"])
        results=self._replace_labels(probs, model_config["labels"], model_config["cutoff"])
        return results


    def summarize(self, notes):
        """
        hacky llamacpp output parsing to get the summary, this has a lot more flexibility than the rest of the columns
        because the output is just free text so it doesn't matter if there is a preceeiding or trailing space or anything like
        that.
        :return:
        """
        model_config = self.models["summary"]
        outputs=self._run_causal(model_config, notes)
        summaries=[]
        for item in outputs:
            try:
                sm=json.loads(item)["summary"]
            except:
                sm=item.replace("{", "").replace("}", "").replace("summary", "").replace("'", "").replace(":", "")
            finally:
                summaries.append(sm)

        return summaries

    def intent(self, notes):
        model_config = self.models["intent"]
        model = self._get_model(model_config)
        intents = model(notes, model_config["labels"])
        results = self._replace_labels(intents, model_config["labels"], model_config["cutoff"])
        return results

    def substance(self, notes):
        """
        parse the llamaccp output for the substance model, this is hacky because the llama outputs while mostly ok
        are not 100% reliable to have correct formatting and sometimes quites are in different placets etc.
        :return:
        """
        model_config = self.models["substance"]
        outputs = self._run_causal(model_config, notes)
        subs=[]
        sub_ids=[]
        for res in outputs:
            try:
                res = re.findall(r"\{[^}]*\}", res)[0].split("\n")
                s = res[0].split(":")[1].replace(",", "")
                i = res[1].split(":")[1].replace("}", "")
                if i == "N\\A":
                    i = None
            except:
                s = None
                i = None
            finally:
                subs.append(s)
                sub_ids.append(i)
        return subs, sub_ids

    #TODO this is a little heavy handed I should be able to extract more gracefully
    def safety(self, notes):
        model_config = self.models["safety"]
        outputs = self._run_causal(model_config, notes)
        sd1=[]
        sd2=[]
        sd3=[]
        sd4=[]
        sd5=[]
        for res in outputs:
            try:
                res = re.findall(r"\{[^}]*\}", res)[0].split("\n")
                s1= res[0].split(":")[1]
                s2 = res[1].split(":")[1]
                s3 = res[2].split(":")[1]
                s4 = res[3].split(":")[1]
                s5 = res[4].split(":")[1].replace("}", "")
                if s1=="-1":
                    s2, s3, s4, s5 = None, None, None, None
                if s2=="N\\A":
                    s2=None
                if s3=="N\\A":
                    s3=None
                if s4=="N\\A":
                    s4=None
                if s5=="N\\A":
                    s5=None
            except:
                s1=None
                s2=None
                s3=None
                s4=None
                s5=None
            finally:
                sd1.append(s1)
                sd2.append(s2)
                sd3.append(s3)
                sd4.append(s4)
                sd5.append(s5)
        return sd1, sd2, sd3, sd4, sd5


    def io(self, notes):
        model_config = self.models["io"]
        outputs = self._run_causal(model_config, notes)
        io=[]
        i=None
        for res in outputs:
            try:
                i=res.split(":")[1].replace("}", "")
            except:
                i=None
            finally:
                io.append(i)
        return io

    def time(self, notes):
        model_config = self.models["time"]
        outputs = self._run_causal(model_config, notes)
        hrs=[]
        mins=[]
        h=None
        m=None
        for res in outputs:
            try:
                s=res.split(":")
                h=s[1].replace(".0", "")
                m=s[2].replace("0", "").replace("}", "")
                if h=="99":
                    h=None
                if m=="99":
                    m=None
            except:
                h=None
                m=None
            finally:
                hrs.append(h)
                mins.append(m)

        return hrs, mins

    def date(self, notes):
        model_config = self.models["date"]
        outputs = self._run_causal(model_config, notes)
        dates=[]
        d=None
        for res in outputs:
            try:
                d=res.split(":")[1].replace("}", "")
                if d=="99":
                    d=None
            except:
                d=None
            finally:
                dates.append(d)
        return dates

    def ampm(self, notes):
        model_config = self.models["ampm"]
        outputs = self._run_causal(model_config, notes)
        ampm=[]
        a=None
        for res in outputs:
            try:
                a=res.split(":")[1].replace("}", "")
                if a=="0":
                    a=None
            except:
                a=None
            finally:
                ampm.append(a)
        return ampm

    def area(self, notes):
        model_config = self.models["area"]
        outputs = self._run_causal(model_config, notes)
        area=[]
        a=None
        for res in outputs:
            try:
                a=res.split(":")[1].replace("}", "")
                if a=="0":
                    a=None
            except:
                a=None
            finally:
                area.append(a)
        return area

    def location(self, notes):
        model_config = self.models["location"]
        outputs = self._run_causal(model_config, notes)
        location=[]
        for res in outputs:
            try:
                l=res.split(":")[1].replace("}", "")
                if l=="0":
                    l=None
            except:
                l=None
            finally:
                location.append(l)
        return location

    def sports(self, notes):
        model_config = self.models["sports"]
        outputs = self._run_causal(model_config, notes)
        sports=[]
        s=None
        for res in outputs:
            try:
                s=res.split(":")[1].replace("}", "")
            except:
                s=None
            finally:
                sports.append(s)
        return sports

    def chunk(self, notes):
        model_config = self.models["chunking"]
        model=self._get_model(model_config)
        chunks=model.chunk(notes)
        return chunks

    def embed(self, notes):
        model_config = self.models["embeddings"]
        model=self._get_model(model_config)
        # this is a list of lists of tuples that is an index and list in the same order as the chunks which are in the
        # same order as the notes, each "chunk" instance is a list of strings
        embeddings=[]
        for text in notes:
            text_embeddings=model.encode(text).tolist()
            embeddings.append([(index, item) for index, item in enumerate(text_embeddings)])
        # this will return a tensor of shape (n_chunks, embedding_dim) I need to split it
        # and make it something postgres compatible
        return embeddings


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
    def _run_llama(self, config, notes):
        model = self._get_model(config)
        messages = [
            {"role": "system", "content": prompt_dict["system"]},
            {"role": "user", "content": None},
        ]

        results = []
        for note in notes:
            messages[1]["content"] = prompt_dict[config["prompt_name"]] + note
            output = model.create_chat_completion(messages=messages)
            results.append(output["choices"][0]["message"]["content"])

        return results

    def _run_causal(self, config, notes):
        model, tokenizer = self._get_model(config)

        stop_token_ids = tokenizer.encode(config["stop_token"], add_special_tokens=False)
        stopping_criteria = StoppingCriteriaList([StopOnSequence(stop_token_ids)])

        results=[]
        for note in notes:
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






