# Chripp project automation

This repository is the collective code for the chirpp automation project for Sickkids. Below are some guidelines and
suggestions for how to collaborate effectively. Please let me know if you have other ideas and suggestions.

# Project Scope

There are several goals for this project they are listed below in decreasing importance (please feel free to commment
and improve)

+ Determining chirpp + cases
+ Summarization of clinical notes
+ Autocoding body parts
+ Autocoding location (indoor/outdoor, area, place)
+ Autocoding safety equipment
+ Autocoding substances
+ Disposition (this is partially done using the complaints and diagnoses)
+ Determining intent

This list is subject to change.

At least in my mind the first 2 aims will be accomplished by fine-tuning an LLM (large language model) maybe with the
help of a rule based pre-processing, the rest we will try to accomplish by using rule based methods (i.e. spacy,
scispacy etc.). Each of us will have specific tasks, please create a project for what areas you are responsible for
under the projects tab. This way we can keep track of who is doing what.

For each aim please create a folder with a name that describes what the task is and see below for some guidelines for
how to collaborate and use the same repository.

# Guidelines

Here are some basic guidelines that I find helpful when collaborating on a coding project with multiple people. Feel
free to make suggestions and propose changes to the document. The aim of the repository is to keep track of our progress
and make sure things are working properly and there is clear, precise and effective communication between team members
and everyone is (including myself) is held accountable for their roles.

## Creating a local git repo

Github is built on top of git. Git is a popular code version control system that tracks your edits to files and whether
new files are added or old ones are delelted. To create a git repository in a directory of your choosing

```bash
cd mydirectory
git init
```

this will create a blank git repository and you will be in the `main` branch.

Better yet clone this repository using:

```bash
git clone https://github.com/celalp/chirpp
```

This branch is reserved for the "production" code and things will not be added here until they are tested and ready to
go. You can create a new branch by:

```bash
git branch new_branch
```

you can switch between branches using:

```bash
git checkout old_branch
```

to add new files/folder to your git repository use:

```bash
git add new_file.py
```

to commit use:

```bash
git commit -m "commit message"
```

See below for more guidelines on branching, commit pushes and pull requests.

You can configure your remote repository with:

```bash
git remote add origin https://github.com/celalp/chirpp.git
```

and you can push using

```bash
git push -u origin <branch name>
```

Please create a `.gitignore` file to keep the unwanted from being added and commited to the repository. 

## Structure

Based on people experience this will be a mainly python repository. Therefore we should stick to some basic norms to
make our lives easier when we are reading each others code. This section is about how the repository is structured, for
how the code should be see below.

Find a clear but short name for your task obviously `myawesomecode` is not an appropritae name for a folder or python
code but neither is `scibertsummarizerforclinicalnotesbasedonpreviouscomments`. Something like `summarizer` is a much
better choice. While naming folders and files try and be as explicit as possible so if your code does not summarize but
select sections of notes `section_selector` might be more suitable.

Within each folder there should be at least one python module with the same name, this module will contain the main code
that does the task. This does not mean that it will contain **all** the code related to the task. Have a clear separtion
of different kinds of things each module does and try to contain each of these in their respective module. You can
make this as a CLI script that is callable with arguments (see below) or you can choose to include another file
(this can be python or bash -let's keep things standard, if you use bash please set `-oe pipefail`).

For processing data, and general manipulation tasks create a module called `utils.py` this will contain the utilities
that are helper functions and classes but do not perform the main task. For example: a function that takes all the
tab (`\t`) and converts them to new lines (`\n`) will be in the utils.

There is no limit to how many modules you can create but one helpful rule I find is to focus on the task not on the
code. Each task should get its own module that is then imported by the main module.

In addition to code your folder should also contain a `README.md` that is properly formatted in markdown style (like
this README). This
document will include:

+ A brief summary of what the task(s) is (are)
+ How they are accomplished
+ list of 3rd party modules
+ detailed description of modules
+ usage instructions for main classes

Additionally please include a requirements.txt (not a `setup.py`) within your folder. If applicable also include
versions of packages. If your code requires non-python dependencies include instructions as to how to set up the
environment.

If you are using conda you can choose to inlcude an `enviroment.yaml`. Please use these names in and not something else
to make sure that we are all in the same page.

## Code style

This is a python project so at the very least we will stick to PEP8 guides with 120 characters per line (we can change
that if you'd like).

Each function/class should contain detailed docstring that has at the very least the following information

+ What does the function do use common sense in describing the function, if the task is simple the description can be
  simple
+ parameters and types, we can use reST style docstrings
+ outputs

for inputs like `*args` and `**kwargs` describe how they might be used and how they are passed to different functions
inside the function.

Avoid lambdas unless the task is extremely simple, same goes for list comprehensions. There is no performance
cost/benefit but a `for` loop is much easier to read.

For classes use CamelCase, for functions use lowercase. In classes there should be a docstring for the class as well as
class methods like so:

```python

class NewClass:
    """
    this class does something awesome
    """

    def __init__(self, input1, input2):
        """
        initiate a new instance of NewClass with some basic calculations and some other things
        param: self:, self NewClass
        param: input1: an input1
        param: input2 an input2
        type: input1: pandas DataFrame
        type: input2: bool
        return: a dict of different awesome results
        rtype: dict
        """
        pass

    def method1(self, *args, **kwargs):
        pass

```

Feel free to structure your code however you wish as long as it's well documented. That said try and avoid exotic cases
python inheritance cases and global variables and scoping out variables using `global`. Each function/class should be
self contained and any input(s) it relies on should be passed during function call.

Use common sense when you are structuring your code, if you really need Subclassing go for it, if you really need mixins
that's ok too but with complexity comes side effects and convoluted code. If you think you need some of these
features please feel free to reach out and we can discuss if we can have a simpler architecture.

### Lazy vs Eager eval

Try and write your code as lazy as possible. Nothing should be calculated/processed/edited unless that method is
explicitly called. If you want method chaining that's ok too but make sure that you really need it.

### Dunder ("\_\_") methods and operator overloading

If you choose you can set up `__str__` and `__repr__` methods of your classes and subclasses. If you want to do
operator overloading please have a good reason to do so and make sure that it is well documented in your code and
README.

### Errors and Exceptions

Please code as defensively as possible. There are a lot of built-in exceptions that you can use to catch errors that
you can foresee happening like a `FileNotFoundError`. Feel free to create your own exceptions like so:

```python
class NewException(Exception):
    pass
```

### Threading and multicore processing

Currently, I think we are all using python 3.10. While python does allow multithreaded applications with the
`threading` module it is complicated to use. You can choose to multi core processing but please provide arguments
(see below) to allow user to set up the number of cores that can be used. While performing multiprocessing keep in
mind that your RAM usage basically multiplies with the number of cores you are using. Be mindful and don't crash the
VM (not a big deal it just would take a bit for me to reset and everyone will be kicked out until the reset is done).

### Arguments and settings

For simple CLI arguments use the `argparse` module. This is an extremely flexible module and you can have subparsers
for different modes of analysis. Please do not use a 3rd parth module like `click`. There is no need to increase the
number of dependencies.

If your code requires extensive parameters (it might for experimentation) you can have a `json` or a `yaml` file to
keep these values as a key:value store. Make sure that this file location is NOT hardcoded but rather passed as an
argument in the callable script.

### Testing

You can choose to use a testing module for your code or not. In either case please create a `tests` folder and in
this folder have an example input and an output for your code with specific parameters. Specify the parameters
either with a README in this folder or in a config file as described above.

## Issues/collaboration

For simple questions and communications Teams is fine for things that are code specific please create an issue and
tag who you think is responsible or can help you with the issue. If you are tagged please try to respond in a
reasonable time scale.

## When to save, when to commit, when to branch

Save your work regularly, commit sparingly. When you first start the project create a branch that you will be
working in and stick to that branch (or branches, up to you). Please do not edit other peoples' branches but instead
create a pull request if you think you can help them.

### Commit guides

When you are done with a feature (like a function, a readme, a config file etc.) you are ready to commit. Committing
is not for saving but for sharing. Each commit needs to address one thing. If you have done multiple things they
need to be multiple commits. With each commit please provide a reasonable explanation of what you did with the
commit message. This will help us track when things were edited and what the results were.

### Push guides

As long as you are following the guidelines above you can push to your branches as much as you want. Github tracks
your git repo so if you have done multiple commits a single push will show up as multiple commits on the remote repo
as well.

### Pull requests

If you want to contribute to someone else's code please create a pull request unless you are actively working with
that person. The tagged person will then review the code and will approve or edit as they see fit. Save for the
simplest of taskt please keep the discussion within the issues section so we all know what's going on.

I'm excited to work with you all on this project and sorry for the wall of text. I hope this was not all boring for
you and it will be a good learning experience for all of us. Please let me know if you run into git issues and need 
some config help. 