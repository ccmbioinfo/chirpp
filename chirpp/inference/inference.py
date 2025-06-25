import os
import subprocess
import time

from transformers import (pipeline, AutoModelForSequenceClassification,
                          AutoTokenizer)

#TODO needs it's own class to be passed to inference, this will do chunking and embedding
from chonkie import SemanticChunker
from chonkie import Model2VecEmbeddings
from model2vec import StaticModel


import openai
import certifi
import requests
import jsonschema
from tqdm import tqdm



class NoModelError(Exception):
    pass

class LlamaCppServer:
    def __init__(self, binary_path, model_dict=None, host = "localhost", port = 8080):
        """Initialize Llama.cpp server manager.

        Args:
            binary_path (str): Path to llama.cpp server binary
            model_path (str): Path to the model file
            host (str): Server host (default: localhost)
            port (int): Server port (default: 8080)
        """
        self.current_directory = os.path.abspath(os.getcwd())
        self.binary_path = binary_path
        if not isinstance(model_dict, dict):
            raise ValueError("model_dict must be a dictionary.Describin the gguf path and its alias")
        for alias, path in model_dict.items():
            self.model_cmd=[]
            if not os.path.exists(path):
                raise FileNotFoundError(f"Model file not found for alias '{alias}': {path}")
            else:
                self.model_cmd.extend(["-m", os.path.abspath(path), "--alias", alias])

        self.host = host
        self.port = port
        self.process = None
        self.base_url = "{}://{}:{}/"
        os.chdir(os.path.abspath(self.binary_path))

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

    def prepare_user_prompt(self, prompt, note):
        return "\n".join([prompt, note])

    def start_server(self, n_ctx=4096, n_threads= 4, ssl_cert= None, ssl_key= None) -> bool:
        """Start the Llama.cpp server with specified parameters.

        Args:
            n_ctx (int): Context size (default: 2048)
            n_threads (int): Number of threads (default: 4)
            ssl_cert (Optional[str]): Path to SSL certificate file
            ssl_key (Optional[str]): Path to SSL key file

        Returns:
            bool: True if server started successfully, False otherwise
        """
        if self.process is not None:
            print("Server is already running")
            return False

        cmd = [
            "./llama-server",
            *self.model_cmd,  # Unpack model command arguments
            "--host", self.host,
            "--port", str(self.port),
            "--ctx-size", str(n_ctx),
            "--threads", str(n_threads),
        ]

        if ssl_cert and ssl_key:
            cmd.extend(["--ssl-cert", ssl_cert, "--ssl-key", ssl_key])
            protocol="https"
        else:
            protocol="http"

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
                    self.url=self.base_url.format(protocol, self.host, self.port)
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

    def single_inference(self, model, sys_prompt, prompt, note, max_tokens: int = 512, temperature: float = 0.7):
        """Run single inference request.

        Args:
            prompt (str): Input prompt
            max_tokens (int): Maximum tokens to generate (default: 512)
            temperature (float): Sampling temperature (default: 0.7)

        Returns:
            Dict: Inference result with validated JSON output
        """
        user_prompt=self.prepare_user_prompt(prompt, note)
        messages=[
                    {"role":"system", "content":sys_prompt},
                    {"role": "user", "content": user_prompt}
        ]
        client=openai.OpenAI(
            base_url=self.url,
            api_key="key" # not needed for localhost
        )

        try:
            response = client.chat.completions.create(
                model=model,  # Model name is irrelevant for local Llama.cpp server
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
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

    def batch_inference(self, sys_prompt, prompt, notes, max_tokens= 90, temperature= 0.7):
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
            result = self.single_inference(sys_prompt, prompt, note, max_tokens, temperature)
            results.append(result)
        return results

    def is_server_running(self):
        """Check if the server is running.

        Returns:
            bool: True if server is running, False otherwise
        """
        if self.process is None:
            return False
        try:
            response = requests.get(f"{self.base_url}/health", verify=certifi.where())
            return response.status_code == 200
        except requests.ConnectionError:
            return False


class Inference:
    def __init__(self, config, device="cpu", server: LlamaCppServer = None):
        """Initialize Inference class with configuration.

        Args:
            config (dict): Configuration dictionary
        """
        self.config = config
        self.server = server
        self.pipeline_device= device


    def load_pipeline(self, model, num_labels=None):
        """Load classification pipeline."""
        if model is None:
            raise NoModelError("No model provided for inference pipeline.")
        model = AutoModelForSequenceClassification.from_pretrained(model, num_labels=num_labels)
        tokenizer = AutoTokenizer.from_pretrained(model, padding="max_length", truncation=True)
        pipe = pipeline("text-classification", model=model, tokenizer=tokenizer, device=self.device)
        return pipe

    def run_pipeline(self, pipeline, notes, label_dict=None, cutoff=0.8):
        num_labels=len(label_dict.keys()) if label_dict else None
        pipe = self.load_pipeline(pipeline, notes, num_labels)
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


    def server_inference(self, params):
        pass

    def chunk_notes(self):
        pass

    def get_embeddings(self, notes):
        pass



