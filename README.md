# Sickkids ED CHIRPP processing pipeline

This repository contains the processing pipelien of EPIC notes for Canadian government reporting requirements. There are
some assumptions made in this pipeline that may or may not be applicable to other EMRs and even other EPIC instances. 
These issues will be adressed as needed. 

## Hardware requirements

Whiel these script can potentially run on any cpu a gpu is highly reccomended, The minimum I have tried to run this 
pipeline was a RTX3080Ti laptop gpu with 16GB or Vram, that said it never came close to filling up the vram so 8GB 
might be sufficient for inference. Running it without gpu will increase the runtime significantly but I have not tested
by how much. 

## Installation
Conda or miniconda is strongly reccomended for setting up an enviroment for this pipeline as it manages to match 
hardware and software requirements of the machine in use. After creating a conda enviroment with a python version of 
your choosing (only tested on python 3.10 and 3.11. 3.12 might cause some dependency issues with pytorch not sure if 
those have been resolved yet) you can install the requirements in the `requirement.txt` file.  

## Dependencies 

The dependencies are minimal in number but they are big dependencies like pytorch, and transformers. There are also 
some models that needs to be downloaded. 2 of these models are custom fine tuned so contact me for accessing them, 
the other ones are for zero-shot learning for inside/outside and whether something includes sports (not implemented 
in autofill yet, see below). I use the same model with different prompts for those columns, for calculating cosine 
similarities I use sentence transformes `all-mpnet-base-v2` model. This again needs to be download to a location that 
is to be specified in the config file. Currently the cosine similarity is not used in the pipeline but it is there 
for humans to asses the quality of the summarization models. 

## How the pipeline works

There are 3 steps to the pipeline 

### Preprocess

This portion takes the raw notes and preprocessed the provider notes for 2 things, 1) it removes patient name from 
anywhere in the text and 2) removes unwanted sections (see `config.yaml`) from the note to reduce its size and only 
keep relevant sections. The preprocessed notes and some other metadata is then passed to inference

### Inference

This part first classifies each ED presentation using the preprocessed notes above and assigns a probability that 
it is indeed a chirpp case, we then use pre determined chirpp complaints that are known to be almost always chirpp 
cases to find a cutoff value for retrival (nothing is 100% so we aim to minimize the human burden while maximizing 
retrival) rate. The likely positive cases are then used as a proxy to determine the probability cutoff. These 
consitute the positive cases to be further processed. 

After classificaion the positive cases are summarized using the fine tuned `t5-small` model. This generate a maximum 
128 toke summary of the ED provider notes. In some instances the actual note itself is less than 128 tokens and in 
those instances there is a message that is displayed. I have not turned that off but I might in the future. 

Then we calculate the cosine similiarity between the clinical note and the summary as a guide for human review. 

To assist with further autofill (though currently not used), using a hand curated list of Diagnoses I determine 
whether a case involves an injury or not (while it is possible that there is a diagnosis and a differnet more minor 
injury those cases are quite rare). Additionally a zero shot model (`facebook/bart-large-mnli`) is used to 
determine whether the incident took place indoors or outdoors and whether the incident involved any kind of sport 
(very loosely defined). These (and possibly more) will be used in filling in other column in the future. 

### Postprocess

The last step is the post processing. This takes the raw notes and the inference results and merges them into a 
specific format. The output is an excel file, there the first sheet has the negative cases (and therfore none of the 
autofill results) and the second sheet has the positive cases. In the second sheet there are some columns that are 
also filled in a more crude rule based manner. Most substance mentions, indoor/outdoor, disposition and inten 
columns are auto-populated to a large extend. These are not meant to be 100% accurate but just meant to make the 
lives of people a little easier. 

## Modifying the pipeline 

Most of the important pipeline paramerters are passed in the `config.yaml` file. There are other parameters like 
target rules of substance detection or the ED note sectionizer in the preprocess classes, those are in their own 
respective folders. I do not reccoment changing those parameters without good reason. There was a lot of trial and 
error to bring the pipeline to this state, this is especially true for the context rules, there are sometimes 
unintented consequences of changing things like direction or max scope. 

## In the future

There are many remaining columns that needs to be filled by humans, and these pose significant challenges to 
automation mostly because of their implied or unceratin nature. Some of the requirements do not allow for ambiguite 
while others provide too much of it. The main goal is to fill up as much of the form as possible both row and column 
wise. 

There are also additional features that will eventually be implemented as a software platform. These will require 
additional features to be included either in the report or the report generation will be offloaded to he platform 
altogether. 

Please let me know if you have any questions. 