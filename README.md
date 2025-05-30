# Sickkids ED CHIRPP processing pipeline

This is the current production and dev pipeline for the chirpp data processing. The data dump is performed by chirpp team
daily into a CCM provisioned vm and the pipeline `chirpp/generatate_report.py` is run whenever there is a new file uploaded.

The aim of this codebase is to help chirpp team classify and code notes and reduce the burden on the staff while allowing for other
research related questions to be asked such as outlier detection (new emerging trends) and full text searches of notes based on 
pg vector and note embeddings as well as other columns. 

## Pipeline Features

The main pipeline is outlied in the `chirpp/generate_report.py` and the execution of the pipeline in to shell scripts under the 
`chirpp` directory. Below are the main features of the pipeline and how they are implemented in the script above 

Due to their large size the models are not stored in this repository but are within the HPC environment. These might be migrated into 
git lfs in the future. 

### Chirpp case classification

This is done by a simple `distilbert-base-uncased` model that is fine tuned on historical data. The classificaiton is binary `0`
for negative and `1` for positive cases. Currently there is no distinction between canonical chirpp cases vs cases that are added
later on like mental health cases w/o injuries or medical device problems. These might get separated in the future. Upon inference
the probabilities are compared to a set of cases where the chief complaint is guaranteed to be a chirpp case (like fracture of any kind)
A cutoff is dynamically selected to include notes that pass the criteria. This works very well when there are a large collection of notes (i.e. a
month's worth) but may not work so well on a single day data. 

### Summarization

Currently, the summarization is performed a **very** lightweight T5-small model. This model has been trained again on historical data 
and does ok in capturing the essence of the incident. However in cases where the notes are very short of there is no information the model 
hallucinates (these are very small number of cases). Another issue we are facing is, while the model captures the essence of the incident
sometimes the summary is worded peculiarly or with many grammatical mistakes. This is partly due to the mistakes that are abundant in the 
hastily written doctor notes. There is ongoing work on RLHF based training on better (and larger) models to take over T5-small

### Intent
This is performed by a fine-tuned `albert-xxl` model. The wrapper scripts restricts the models to pre-defined confidences. In cases
(this is especially true for multi class instances) where the model is not so sure the section is left blank. 

### AM/PM
This one like many others is a `distilbert-base-uncased` model binary fine tuned with a strict confidence cutoff

### Location 
Same as above, here we are not trying to predict many many possible codes but instead the model is fine tuned to return one of the 
most common 10 codes and 0 if it's not one of them. This on average manages to fill out 40% of the column. 

### Area
Same as above but done with 15 of the most common codes. These numbers are picked so that we cover about 90-95% of the cases but in 
reality with the strict confidence cutoff it comes down to 40-45% when we want the model to be >95% accurate

### inside/outside
Same as AM/PM

### Substance use
This is a 2 step process a fine-tuned `distilbert-base-uncased` determines if substances were involved in the case and a 
`medspacy-ner` with specific hand-crafted `TargetRule` instances searched for keywords in a context-dependent manner. As a base
model both substance use and safety devices use spacy's `en-core-web-trf` model

### Safety devices

Using a similar method to above there are hand crafted rules that the same 

### Embedding generation

### Database export

All of this data, notes as written and the outputs of pipelines lives in a PostgreSQL database within the CCM provisioned VM

#### Database Schema

## Pipeline classes

### PreProcess

### Inference

### PostProcess

### Database

## Usage

## Missing features

### Research events

### Full text search script

### Outlier detection

## Improvements




