# Sickkids ED CHIRPP processing pipeline

This is the database branch of the pipeline, here I will develop the code to host a PostgreSQL database with 
tsvector full text search capabilities on the patient notes. The `database` folder will contain all the necassary 
classes to hold all the information. 

The inital database instance **will not** contan information about users or who modified what as there will not be 
an opportunity to do so. In the current schema there is only one `Boolean` column to determine whether an ED case 
(positive or negative) has been human reviewed. 

This database will eventually will hold all the necessary information for a full interface for the CHIRPP team. It 
is still very specific to epic and how their notes are structured. 

## Full text search

Based on prior experience I think reliance on regex and `like` statements is not robust enough for a decent full 
text search capability. This is by design a low volume (in terms of # of requests) space only a handful of people 
will ever interact with this database. PostgreSQL has an extension that's called `ts_vector` that allow for full 
text search and indexing based on [gin]() index. This has previously been shown to rival [elasticsearch]() in terms 
of performance and accuracy with much less memory footprint. While still allowing regular `O log(n)` search speed on 
other db columns. 

## TODO

1. generate database schema
2. generate import scripts
3. refactor `generate_report.py` to use the database
4. generate export scripts for a given date interval (based on ED presentation)
5. generate scripts for keyword search along with other parameters (see below)
6. generate an api endpoint for running the scripts above
7. Dockerize

There is probably some more intermediate steps that I'm forgetting 