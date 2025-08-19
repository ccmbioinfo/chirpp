
import numpy as np
from smolagents import Tool

from chirpp.database.database import DataBase
from chirpp.inference.inference import KeywordGenerator
from chirpp.inference.utils import semantic_search, keyword_search

schema=[]
with open("schema.txt") as f:
    for line in f:
        schema.append(line.strip())

schema="\n".join(schema)

class KeywordSearchTool(Tool):
    name="keyword_search"
    description="""
    Given a list of dictionary of keywords and a table to search search for the rows that contain the 
    keywords that are under the 'IN' key and do not contain the keywords that are under the 'NOT IN' key.
    
    for example the dictionary might look like this:
    keywords={"IN": ["keyword1", "keyword2"], "NOT IN": ["keyword3", "keyword4"]}
    """

    inputs={
        "keywords": {
            "type":"dict",
            "description": """dictionary of keywords to search for and not search for the query will return rows that contain 
                           the words under the 'IN' key and do not contain the words under the 'NOT IN' key, either of them 
                           can be an empty list if so they will not be searched"""
        },
        "database": {
            "type": "DataBase",
            "description": """database to search in, this is a custom class that contains all the information that is needed to perform
            search, no additional connection information is needed the forward method takes care of it."""

        },
        "table": {
            "type": "str",
            "description": """table to search in that is in the database, the forward methods will look for a table that is compatible otherwise
                           will throw a ValuError"""
        },
        "ranking_method":{
            "type":"str",
            "description": """method to rank the results, this can be ts_vector or ts_vector_cd the forward method
            will look for a method that is compatible otherwise will throw a ValuError"""

        },
        "normalization":{
            "type":"int",
            "description": """normalization value to use for the ranking method, the database will take care of it ranking methods"""
        }
    }

    output_type= "list"

    def forward(self, keywords: dict, database: DataBase, table: str, ranking_method: str):
        results=keyword_search(keywords, table, database, ranking_method)
        return results


class SemanticSearchTool(Tool):
    name="semantic_search"
    description = """Given a vector of embeddings and a database table to search in find the rows that are semantically most
    similar to the vector using the distance/similarity metric specified in function call"""

    inputs = {
        "embeddings": {
            "type": "np.ndarray",
            "description": """a numpy array of embeddings, the embeddings are the output of the embedding model, if the dimentions do not mathc
            then the forward method will throw a ValueError"""
        },
        "database": {
            "type": "DataBase",
            "description": """database to search in, this is a custom class that contains all the information that is needed to perform
                search, no additional connection information is needed the forward method takes care of it."""

        },
        "table": {
            "type": "str",
            "description": """table to search in that is in the database, the forward methods will look for a table that is compatible otherwise
                               will throw a ValueError"""
        },
        "similarity_metric": {
            "type": "str",
            "description": """name of the distance metric to use, the methods will be passed to the database to perform the calculation, 
            if the method is not found then the forward method will throw a ValueError"""
        },
        "cutoff":{
            "type":"float",
            "description":"""cutoff value to use for the distance metric, if the distance is greater than the cutoff then the row is not returned"""
        }
    }

    output_type="list"

    def forward(self, embeddings: np.ndarray, database: DataBase, table: str, similarity_metric: str, cutoff: float):
        results=semantic_search(embeddings, table, database, similarity_metric, cutoff)
        return results

class KeywordGeneratorTool(Tool):
    name = "keyword_generator"
    description = """Given an nlp query genereate keywords for keyword search with or without weights for tsvector, currently 
                   we can only generate positive keywords"""
    inputs = {
        "model":{
            "type":"str",
            "description": """name of the model to use for keyword generation"""
        },
        "prompt":{
            "type":"str",
            "description": """system prompt to use for keyword generation"""
        },
        "cache_dir":{
            "type":"str",
            "description": """path to cache directory to use for the model"""
        },
        "query": {
            "type": "str",
            "description": """query to generate keywords for"""
        },
        "weights": {
            "type": "bool",
            "description": """whether to use return weights  for tsvector or not"""
        }
    }
    output_type = "dict or list"

    def forward(self, model, prompt, query, cache_dir=None, weights=False):
        generator=KeywordGenerator(model, prompt, cache_dir)
        results=generator.parse(query, weights)
        return results


