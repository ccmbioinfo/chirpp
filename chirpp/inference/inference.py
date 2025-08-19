import os
import subprocess
import time
import json

from transformers import (pipeline, AutoModelForSequenceClassification,
                          AutoModelForCausalLM, AutoTokenizer)

import pandas as pd
import torch
from chonkie import SemanticChunker
from chonkie import Model2VecEmbeddings
from model2vec import StaticModel

import openai
import certifi
import requests
import jsonschema
from tqdm import tqdm

from chirpp.inference.utils import *

class NoModelError(Exception):
    pass

# this is here but not sure how useful it's going to qwen3 4b does ok with coming up with positive keywords but not so much
# with negative ones, there still needs to be some human input here. I have seen a lot of models struggle with the concept.
class KeywordGenerator:
    def __init__(self, model_name, prompt, cache_dir=None):
        self.model_name = model_name
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name, cache_dir=cache_dir)
        self.model = AutoModelForCausalLM.from_pretrained(self.model_name, cache_dir=cache_dir)
        self.prompt = prompt

    def parse(self, text, weights=True):
        messages = [
            {"role": "system", "content": self.prompt},
            {"role": "user", "content": text}
        ]
        text = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )
        model_inputs = self.tokenizer([text], return_tensors="pt").to(model.device)

        # conduct text completion
        generated_ids = self.model.generate(
            **model_inputs,
            max_new_tokens=500
        )
        output_ids = generated_ids[0][len(model_inputs.input_ids[0]):].tolist()

        content = self.tokenizer.decode(output_ids, skip_special_tokens=True)
        content=json.loads(content)
        if weights:
            return content
        else:
            return list(content.keys())

    def __str__(self):
        return f"Keyword generator for ts vector search via {self.model_name}"

    def __repr__(self):
        return f"Keyword generator for ts vector search via {self.model_name}"


class LlamaCppServer:
    def __init__(self, config, binary_path):
        """Initialize Llama.cpp server manager.

        Args:
            binary_path (str): Path to llama.cpp server binary
            model_path (str): Path to the model file
            host (str): Server host (default: localhost)
            port (int): Server port (default: 8080)
        """
        self.current_directory = os.path.abspath(os.getcwd())

        self.binary_path = binary_path
        self.model_dict = config["models"]
        self.host = config["host"]
        self.port = config["port"]
        self.context=config["context_length"]

        cmd = [
            self.model_dict,
            "--host", self.host,
            "--port", str(self.port),
            "--ctx-size", str(self.model_dict["context_length"]),
            "--threads", str(self.model_dict["threads"]),
        ]
        if self.config["ssl_cert"] and self.config["ssl_key"]:
            cmd.extend(["--ssl-cert", self.config["ssl_cert"],
                        "--ssl-key", self.config["ssl_key"]])
            self.protocol="https"
        else:
            self.protocol="http"

        self.process = None
        self.url = f"{self.protocol}://{self.host}:{self.port}"

        # JSON schema for inference output validation
        self.inference_schema = {
            "type": "object",
            "properties": {
                "choices": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "message": {
                                "type": "object",
                                "properties": {
                                    "content": {"type": "string"}
                                },
                                "required": ["content"]
                            }
                        },
                        "required": ["message"]
                    }
                }
            },
            "required": ["choices"]
        }

    def start_server(self, model) -> bool:
        """
        start llama.cpp server with a given model
        :param model: model dict from self config
        :return:
        """
        if self.process is not None:
            print("Server is already running")
            return False
        os.chdir(os.path.abspath(self.binary_path))

        model_cmd = ["-m", os.path.abspath(self.model_dict[model]["model"]), "--alias", model]
        cmd=self.cmd.extend(model_cmd)

        try:
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # Wait for server to start (with timeout)
            timeout = 30
            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    response = requests.get(f"{self.url}/health", verify=certifi.where())
                    if response.status_code == 200:
                        print("Server started successfully")
                        os.chdir(self.current_directory)
                        return True
                except requests.ConnectionError:
                    time.sleep(1)
            print("Server failed to start within timeout")
            self.stop_server()
            os.chdir(self.current_directory)
            return False
        except Exception as e:
            os.chdir(self.current_directory)
            print(f"Failed to start server: {str(e)}")
            return False

    def stop_server(self) -> bool:
        """Stop the Llama.cpp server.

        Returns:
            bool: True if server stopped successfully, False otherwise
        """
        if self.process is None:
            print("No server is running")
            return False

        try:
            self.process.terminate()
            self.process.wait(timeout=10)
            self.process = None
            print("Server stopped successfully")
            return True
        except Exception as e:
            print(f"Failed to stop server: {str(e)}")
            return False

    def single_inference(self, model, note):
        """Run single inference request.

        Args:
            prompt (str): Input prompt
            max_tokens (int): Maximum tokens to generate (default: 512)
            temperature (float): Sampling temperature (default: 0.7)

        Returns:
            Dict: Inference result with validated JSON output
        """
        user_prompt=prepare_user_prompt(self.model_dict["model"]["prompt"], note)
        messages=[
                    {"role":"system", "content":self.model_dict["system_prompt"]},
                    {"role": "user", "content": user_prompt}
        ]
        client=openai.OpenAI(
            base_url=self.url,
            api_key="key" # not needed for localhost
        )

        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=self.model_dict["model"]["max_tokens"],
                temperature=self.model_dict["model"]["temperature"],
                stream=False
            )
            result = response.to_dict()

            # Validate JSON schema
            jsonschema.validate(instance=result, schema=self.inference_schema)

            # Simplify output to {"summary_text": <text>} format
            simplified_result = result["choices"][0]["message"]["content"]
            return simplified_result

        except (openai.APIError, jsonschema.ValidationError) as e:
            return {"error": f"Inference failed: {str(e)}"}

    def batch_inference(self, model, notes):
        """Run batch inference requests.

        Args:
            prompts (List[str]): List of input prompts
            max_tokens (int): Maximum tokens to generate (default: 512)
            temperature (float): Sampling temperature (default: 0.7)

        Returns:
            List[Dict]: List of inference results with validated JSON output
        """
        results = []
        for note in tqdm(notes, unit=" Notes", desc="Processing: "):
            result = self.single_inference(model, note)
            results.append(result)
        return results

    def is_server_running(self):
        """Check if the server is running.

        Returns:
            bool: True if server is running, False otherwise
        """

        response = requests.get(f"{self.url}/health", verify=certifi.where())
        return response.status_code == 200

class SemanticChunking:
    def __init__(self, chunking_model, embedding_model, chunk_size, min_sentences, threshold):
        """

        :param chunking_mode:
        :param embedding_model:
        """
        self.chunking_model = Model2VecEmbeddings(chunking_model)
        self.embedding_model = StaticModel.from_pretrained(embedding_model)
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
        embeddings = self.embedding_model.encode(texts)
        return embeddings

# TODO moving model dict here and will init llamacpp server with it
class Inference:
    def __init__(self, config, device="cpu"):
        """
        Initialize inference class instance, the chunking method is the same for both llamaccp and transformers pipelines
        usage
        :param config: config parameters, see chirpp.inference.config.py
        :param device: cuda or cpu
        """

        self.pipeline_device = device

        # this leaves the option to use llamacpp with and without gpu, my setup does not
        # have a gpu, so I will use the cpu version of the model
        if "server" in config.keys():
            self.server = LlamaCppServer(config["server"])
        else:
            self.server = None

        self.chunker = SemanticChunker(chunking_model=config["chunking"]["model"],
                                       embedding_model=config["embedding"]["model"],
                                       chunk_size=config["chunking"]["chunk_size"],
                                       min_sentences=config["chunking"]["min_sentences"],
                                       threshold=config["chunking"]["threshold"])

    def load_pipeline(self, model, model_type="classification", num_labels=None):
        """
        Load a text classification or causal language model pipeline.
        :param model: the model secification is defined in the config file
        :param model_type: this is either classification or causal, the only causal model is the summarization one.
        :param num_labels: for classification models this is the number of labels
        :return:
        """
        if model is None:
            raise NoModelError("No model provided for inference pipeline.")
        tokenizer = AutoTokenizer.from_pretrained(model, padding="max_length", truncation=True)

        if model_type == "classification":
            model = AutoModelForSequenceClassification.from_pretrained(model, num_labels=num_labels)
            pipe = pipeline("text-classification", model=model, tokenizer=tokenizer, device=self.device)
        elif model_type == "causal":
            model=AutoModelForCausalLM.from_pretrained(model)
            pipe = pipeline(
                "text-generation",
                model=model,
                torch_dtype=torch.bfloat16,
                device_map="auto",
            )
        else:
            raise NotImplementedError(f"Model {model_type} is not supported.")

        return pipe

    def run_classification_pipeline(self, model, notes, label_dict=None, cutoff=0.8):
        """
        Run classification pipeline on notes this depends on whether the llamacpp method is being used, regadless chirpp +/-
        will be a transformers pipeline due to its efficient
        :param model: the model, this model needs to be present in the path specified in the config file othewise there will be an error
        :param notes: notes, a list
        :param label_dict: label dict, the labels in the model training is not the same as the actual labels in the data
        :param cutoff: anything below this will be either be the negative class or left blank
        :return: list of labels
        """
        num_labels = len(label_dict.keys()) if label_dict else None
        pipe = self.load_pipeline(model, "classification", num_labels)
        labels = pipe(notes)
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

    def run_causal_pipeline(self, pipeline, notes, sys_prompt, task_prompt, model_type="causal",
                            max_tokens=20, temperature=0.7):
        """

        :param pipeline:
        :param notes:
        :param model_type:
        :param sys_prompt:
        :param task_prompt:
        :param max_tokens:
        :param temperature:
        :return:
        """
        pipe=self.load_pipeline(pipeline, model_type=model_type)
        results = []
        for note in notes:
            user_protmpt = prepare_user_prompt(task_prompt, note)
            messages = [
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": user_protmpt},
            ]
            outputs = pipe(
                messages,
                max_new_tokens=max_tokens,
                temperature=temperature,
            )
            output = process_results(outputs[0]["generated_text"][-1])
            results.append(output)
        return results

    def run_pipeline(self, model, notes):
        if model["type"]=="classification":
            results= self.run_classification_pipeline(model["model"], notes, model["labels"], model["cutoff"])
        if model["type"]=="causal":
            results = self.run_causal_pipeline(model["model"], notes, model["system_prompt"],
                                            model["prompt"], model_type=model["type"],
                                            max_tokens=model["max_tokens"],
                                            temperature=model["temperature"])
        return results

    def server_inference(self, model, notes):

        server = self.server.start_server(model=model)
        if server.is_server_running() is False:
            raise RuntimeError("Server failed to start. Check the logs for details.")
        results=server.batch_inference(model=model, notes=notes)
        server.stop_server()
        return results

    def embed_notes(self, notes, chunk=True):
        """Embed notes using the configured embedding model."""
        if self.chunker is None:
            raise ValueError("Chunking model is not set.")
        if chunk:
            chunks = self.chunker.chunk_notes(notes)
        else:
            chunks = notes
        embeddings = self.chunker.get_embeddings(chunks)
        return embeddings

    def get_probs(self, database, start_date, complaint_filter):
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



