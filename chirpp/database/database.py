import os
from datetime import datetime

import pandas as pd
import dotenv
import sqlalchemy
import yaml

#TODO this will query the database to generate the report for an arbitrary code
#TODO this will need a query language to take an arbitrary dict to build complex queries
class DbQuery:
    def __init__(self):
        pass

    def db_query(self, statement):
        pass

#TODO this will need to import raw, processed and human verified notes will need ways to distinguish
# between them
class DbImport:
    def __init__(self):
        pass

    def db_import(self):
        pass
