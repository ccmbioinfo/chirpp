import spacy
import torch

import chirpp.database.database
from chirpp.database.database import DataBase

class Query:
    def __init__(self, database:chirpp.database.database.DataBase, detail_level=1):
        pass

    def get_chirpp_columns(self, query:str):
        pass

    def extract_keywords(self, query:str):
        pass

    def get_csns(self, query:str):
        pass

    def filter_csns(self, query:str):
        pass

    def rerank(self, query:str):
        pass

    def __call__(self, query:str):
        pass