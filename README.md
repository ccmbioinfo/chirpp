# Sickkids ED CHIRPP processing pipeline

This repos is still work in progress, here are some guidelines as to how to use this repo:
You can follow along run_example.ipynb to see how to use the pipeline interactively. This is for an older version 
where we assume that we have an excel file that has been exported from EPIC. Things have changed slightly since then.
Now we do get some text files daily from the epic servers for cases that happened 3 days ago. These are in the VM 
(see below)

## Important files/folders

All the pre-trained models should be in the models folder. I have moved these models to the vm and I will share 
their location in a separate email. 

## How to set up the enviroment

The current enviroment.yaml is bloated. There is another yaml file called enviroment_cpu.yaml, this will install the 
dependencies for cpu processing only. Considering there is no cpu access for the vm this should be enough for now. I 
am adding sqlachemy to the list so we can start building the database as well. 

```python
conda env create -f enviroment_cpu.yaml
```

This will create a conda envrionment named `chirpp` and after the initial setup (this may take a while) you can 
activate the env with `conda activate chirpp`. I am also working on a setuy.py file for dependency installation but 
that method does not cover non-python dependencies (like cuda libraries for the ai models) so that might never happen.

In my mind `setup.py` only exists to make the package pip installable and callable from the command line like any 
other package to facilitate automation. After the environment creation you can activate it with `conda activate 
chirpp_cpu` after that if you would like you can install the chirpp_code package using `pip install .`. This will 
install the chirpp_code package like any other pip package and the generate_report.py script should be available 
from the command line anywhere. 

Keep in mind that you will need to activate the conda enviroment first to be able to use the package. 

## Known issues

Currently the substance id code does not work. I will push a fix for it in the near future. Any additional and 
tested autofill functions will be added slowly as well. 

## Where are the epic files?

They are in the same VM that we have used last summer. I have deleted your user accounts. I will try to create them 
before I leavebut I will also share the location and the account that these files are uploaded to. I will try to 
organize this as much as I can. I will also change the file permissions so you can have access, this also means that 
you can delete/modify things please be careful and do not modify the raw data. Whenever you are working on a file 
please make a copy and work on the copy, leave the original in the `/home/epic/chirpp` folder.

The IP for the VM is `172.20.4.169`. You can access the vm using a simple ssh tunnel. 

## Hardware requirements

Whiel these script can potentially run on any cpu a gpu is highly reccomended, The minimum I have tried to run this 
pipeline was a RTX3080Ti laptop gpu with 16GB or Vram, that said it never came close to filling up the vram so 8GB 
might be sufficient for inference. Running it without gpu will increase the runtime significantly but I have not tested
by how much. 

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

### Adding new features

If you want to add new features to the pipeline do not add them to the pipeline branch. Please create a new branch 
or overwrite and existing branch and make your changes. When you are done create a pull request and I will review 
the code. Whenever possible please test your code. Currently we do not have an automated testing method and test 
cases. We can use one of the daily notes for a simple test case and use something like `pytest`. If you do not have 
an idea for a feature and would like to contribute please consider adding unit test. 

For other methods please make your additions to the appropriate section of the pipeline (pre/post process or 
inference). The additions to the main classes should be miminal. You can add functions to `utils.py` in each of the 
step directories or create additional python modules to be called by the main class. Please the `master` branch for 
instructions on how to use classes and general guidelines on the code.  


## TODO

There are several features that are missing form this pipeline below is a short list of what I have in mind feel 
free to expand the list as appropriate

+ Autofilling more columns 
+ Creating a database of all the processed and raw notes
+ Automating the pipeline runs with a cron job
+ Moving/deleting old files after they have been imported to database
+ An S3 or S3 like storage solution to download files after they have been processed
+ A search functionality to search for specific keywords and terms
+ A UI for interacting with the database. 

## ROADMAP

The most important goal right now is automating the pipeline and getting the results daily. The next step is 
importing all the results to a database. For this I have PostgreSQL in mind for several reasons. It is quite feature 
complete and has extensions that allow for full text search that rivals elasticsearch in speed w/o the memory 
constraints. Setting up the database and the full text extension is another important one that I can use help with. 
For more information on that please see [here](https://www.postgresql.org/docs/current/textsearch.html)

After the database is setup the next phase will include adding logging to the database so we can keep track of what 
has been searched and used. This will be essential in the fututre if we want to build a web UI for other to search 
the database and maybe even do the coding on the database in real time.