import os

model_dir="./models/"

inference_config = {
    "classification": {
        "type": "classification",
        "num_labels": 2,
        "include_labels": False,
        "max_length": 512,
        "truncation": True,
        "cutoff": 0.90,
        "model": os.paths.abspath(os.path.join(model_dir, "distilbert")),
        "labels": {'0': False, '1': True}
    },
    "intent": {
        "type": "classification",
        "num_labels": 7,
        "include_labels": False,
        "max_length": 512,
        "truncation": True,
        "cutoff": 0.8,
        "model": os.path.abspath(os.path.join(model_dir, "albert_xxl_intent")),
        "labels": {'0': '10', '1': '11', '2': '12', '3': '13', '4': '15', '5': '16', '6': '19'}
    },
    "chunking": {
        "chunk_size": 128,
        "min_sentences": 1,
        "threshold": 0.5,
        "model": os.path.abspath(os.path.join(model_dir, "m2v_model")),
    },
    "embedding":{
        "type":"sentencetransformer",
        "model": os.path.abspath(os.path.join(model_dir, "qwen_3_embed_06"))
    },
    "summarization":{
        #TODO
    },
    "time":{
        #TODO
    },
    "date":{
        #TODO
    },
    "area":{
        #TODO
    },
    "location":{
        #TODO
    },
    "substance":{
        #TODO
    },
    "safety":{
        #TODO
    },
    "io":{

    },
    "sports":{

    },
    "disposition":{

    }
}

