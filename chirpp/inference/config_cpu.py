from chirpp.inference.prompts import *

inference_config = {
    "pipelines": {
        "classification": {
            "num_labels": 2,
            "include_labels": False,
            "max_length": 512,
            "truncation": True,
            "cutoff": 0.90,
            "model": "./models/distilbert",
            "labels": {'0': False, '1': True}
        },
        "intent": {
            "num_labels": 7,
            "include_labels": False,
            "max_length": 512,
            "truncation": True,
            "cutoff": 0.8,
            "model": "./models/albert_xxl_intent",
            "labels": {'0': '10', '1': '11', '2': '12', '3': '13', '4': '15', '5': '16', '6': '19'}
        }
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

    "server": {
        # main server configurations
        "host": "localhost",
        "port": 8000,
        "binary_path": "llamacpp/",
        "system_prompt": system_prompt,
        "context_length": 4096,
        "threads": 6,
        "ssl_cert" : None,
        "ssl_key" : None,

        # model configurations
        "models": {
            "summarization": {
                "model": "models/summary.gguf",
                "prompt": summary_prompt,
                "max_tokens": 100,
                "temperature": 0.7,
            },
            "location": {
                "model": "models/location.gguf",
                "prompt": location_prompt,
                "max_tokens": 15,
                "temperature": 0.1,
            },
            "area": {
                "model": "models/area.gguf",
                "prompt": area_prompt,
                "max_tokens": 15,
                "temperature": 0.1,
            },
            "substance": {
                "model": "models/substance.gguf",
                "prompt": substance_prompt,
                "max_tokens": 60,
                "temperature": 0.4,
            },
            "am_pm": {
                "model": "models/am_pm.gguf",
                "prompt": ampm_prompt,
                "max_tokens": 15,
                "temperature": 0.1,
            },
            "io": {
                "model": "models/io.gguf",
                "prompt": io_prompt,
                "max_tokens": 15,
                "temperature": 0.1,
            },
            "sports": {
                "model": "models/sports.gguf",
                "prompt": sports_prompt,
                "max_tokens": 15,
                "temperature": 0.1,
            },
            "time": {
                "model": "models/time.gguf",
                "prompt": time_prompt,
                "max_tokens": 15,
                "temperature": 0.1,
            },
            "safety": {
                "model": "models/safety.gguf",
                "prompt": safety_prompt,
                "max_tokens": 90,
                "temperature": 0.4,
            },
        }
    },


    "pos_complaints": ["Oral / Esophageal Foreign Body", "Upper Extremity Injury", "Lower Extremity Injury",
                       "Burn", "Anxiety / Situational Crisis", "Head Injury", "Medical Device Problem",
                       "Depression / Suicidal / Deliberate Self Harm", "Paediatric Disruptive Behaviour",
                       "Laceration/Puncture", "Abrasion", "Neck Trauma", "Noxious Inhalation", "Foreign Body, Nose",
                       "Post-operative Complications", "Overdose Ingestion", "Bizarre Behaviour", "Cast Check",
                       "Foreign Body Ear", "Major Trauma - Penetrating", "Eye Trauma", "Concern For Patient Welfare",
                       "Suture / Staple Removal", "Major Trauma - Blunt", "Foreign Body, Skin",
                       "Violent / Homicidal Behaviour",
                       "Sexual Assault", "Substance Misuse / Intoxication", "Hypothermia",
                       "Traumatic Back / Spine Injury",
                       "Nasal Trauma", "Foreign Body, Eye", "Respiratory Foreign Body", "Bite", "Facial Trauma",
                       "Chemical Exposure, Eye", "Genital Trauma", "Amputation", "Social Problem",
                       "Hallucinations / Delusions",
                       "Insomnia", "Ear Injury", "Chemical Exposure", "Foreign Body in Rectum",
                       "Isolated Chest Trauma - Blunt",
                       "Isolated Abdominal Trauma - Blunt", "Anal / Rectal Trauma", "Multisystem Trauma - Blunt",
                       "Foreign Body, Vagina",
                       "Body Fluid Exposure", "Ring Removal", "Multisystem Trauma - Penetrating", "Near Drowning",
                       "Isolated Abdominal Trauma - Penetrating",
                       "Isolated Chest Trauma - Penetrating", "Substance Withdrawal", "Electrical Injury",
                       "Frostbite / Cold Injury",
                       "Cardiac Arrest (Traumatic)", "Foreign Body in Eye"],

    "final_columns": ["MRN", "Arrival Date", "Note Text", "probs", "summary", "cosine_similarity", "Diagnosis",
                      "Problem List", "Chief Complaint"],

    "time_delta":30,
    "user_chirpp":True,
    "chirpp_col": "CHIRPP Icon"
}
