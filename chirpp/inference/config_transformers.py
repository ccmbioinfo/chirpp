from chirpp.inference.prompts import *


# the difference between config_cpu and config_gpu is that config_cpu we are using llamaccp for inference
# for the llama modelsl in a gpu instances we will just use the instruction fine tuned models as is.
# depending on the depolyment that means we will need to change the files in the models folder and need to
# provide instructions for where to get them.


inference_config = {
    "pipelines": {
        "classification": {
            "type": "classification",
            "num_labels": 2,
            "include_labels": False,
            "max_length": 512,
            "truncation": True,
            "cutoff": 0.90,
            "model": "./models/distilbert",
            "labels": {'0': False, '1': True}
        },
        "intent": {
            "type": "classification",
            "num_labels": 7,
            "include_labels": False,
            "max_length": 512,
            "truncation": True,
            "cutoff": 0.8,
            "model": "./models/albert_xxl_intent",
            "labels": {'0': '10', '1': '11', '2': '12', '3': '13', '4': '15', '5': '16', '6': '19'}
        },
        "summarization": {
            "type": "causal",
            "model": "models/summary",
            "prompt": summary_prompt,
            "max_tokens": 100,
            "temperature": 0.7,
        },
        "location": {
            "type": "causal",
            "model": "models/location",
            "prompt": location_prompt,
            "max_tokens": 15,
            "temperature": 0.1,
        },
        "area": {
            "type": "causal",
            "model": "models/area",
            "prompt": area_prompt,
            "max_tokens": 15,
            "temperature": 0.1,
        },
        "substance": {
            "type": "causal",
            "model": "models/substance",
            "prompt": substance_prompt,
            "max_tokens": 60,
            "temperature": 0.4,
        },
        "am_pm": {
            "type": "causal",
            "model": "models/am_pm",
            "prompt": ampm_prompt,
            "max_tokens": 15,
            "temperature": 0.1,
        },
        "io": {
            "type": "causal",
            "model": "models/io",
            "prompt": io_prompt,
            "max_tokens": 15,
            "temperature": 0.1,
        },
        "sports": {
            "type": "causal",
            "model": "models/sports",
            "prompt": sports_prompt,
            "max_tokens": 15,
            "temperature": 0.1,
        },
        "time": {
            "model": "models/time",
            "prompt": time_prompt,
            "max_tokens": 15,
            "temperature": 0.1,
        },
        "safety": {
            "type": "causal",
            "model": "models/safety",
            "prompt": safety_prompt,
            "max_tokens": 90,
            "temperature": 0.4,
        },
    },

    "chunking": {
        "chunk_size": 128,
        "min_sentences": 1,
        "threshold": 0.5,
        "model": "./models/m2v_model",
    },

    "embedding": {
        "model": "models/m2v_model",
    },
}