import re
import numpy as np
import pandas as pd

from sqlalchemy import text

def prepare_user_prompt(prompt, note):
    return "\n".join([prompt, note])


def process_results(output_list, out_type=str, summary=False):
    """
    the server returns a bunch of stuff, and only the first portion is the actual output with the desired information and
    structure, I will need to mactch the brackets and clean the ouptut.
    :param output_list: results from the sever
    :param out_type: this will remain string for now, but can be changed to int or float if needed
    :return: a list of dictionaries with cleaned output
    """
    cleaned_output = []
    for item in output_list:
        if summary:
            clean={"summary":item.replace("{'summary':", "").split("}")[0]}
        else:
            match= re.findall(r"\{[^}]*\}", item)[0]
            match=match.replace('"', "").replace("'", "").replace("\'", "").\
                replace("{", "").replace("}", "").split("\n") #this gives a list of strings
            clean={}
            for out in match:
                out=out.split(":")
                if out[1]=="N\\A":
                    out[1]=""
                clean[out[0]]=out_type(out[1].replace(",", "").replace(".0", ""))
        cleaned_output.append(clean)
    return cleaned_output


def cosine_similarity(vec_a, vec_b):
    """
    Calculate the cosine similarity between two vectors, there is no need to overdo it with
    sentence transformers or other dependencies, the number of things that will be colleceted and compared
    will not exceed a few hundred.
    :param vec_a: vector a, in this case the embedding vector from from chunker
    :param vec_b: same as above for a different vector
    :return: the cosine similarity between the two vectors
    """
    a = np.array(vec_a, dtype=float)
    b = np.array(vec_b, dtype=float)
    dot_product = np.dot(a, b)
    return dot_product / (np.linalg.norm(a) * np.linalg.norm(b))

# TODO enable weights, the form could be
# TODO enable searching for sk narrative, not sure if important because we can search notes
def keyword_search(keywords, table, database, ranking_method="ts_rank_cd", normalization=8):
    appropriate_tables={"visits":"phac_narrative_vector", "notes":"notes_ts_vector",
                        "processed_notes":"note_text_ts_vector"}

    vector_column=appropriate_tables[table]

    if table not in appropriate_tables.keys():
        raise ValueError("table must be one of the following: {}".format(", ".join(appropriate_tables)))

    if "in" in keywords.keys():
        in_words="&".join(keywords["in"])
    else:
        in_words=""

    if "not in" in keywords.keys():
        not_in_words="|".join(["!" + word for word in keywords["not in"]])
    else:
        not_in_words=""

    keyword_query="&".join([in_words, not_in_words])

    query=f"""SELECT csn, {ranking_method}({vector_column}, query, {normalization}) as rank
           FROM {table} to_tsquery('english', {keyword_query}) AS query) WHERE {vector_column} @@ query ORDER BY rank DESC"""

    results=database.session.execute(text(query)).fetchall()
    return pd.DataFrame(results, columns=["csn", "rank"])


def semantic_search(embeddings, table, database, similarity_metric="cosine", cutoff=None):
    appropriate_tables = {"chunked_notes": "embeddings", "processed_notes": "embeddings", "visits":"phac_embeddings"}

    vector_column = appropriate_tables[table]

    if table not in appropriate_tables.keys():
        raise ValueError("table must be one of the following: {}".format(", ".join(appropriate_tables)))

    if similarity_metric=="cosine":
        dist="<=>"
    elif similarity_metric=="euclidean":
        dist="<->"
    elif similarity_metric=="dot":
        dist="<#>"
    else:
        raise ValueError("similarity_metric must be one of the following: cosine, euclidean, dot (dot product)")

    query=f"""SELECT csn, {vector_column} AS vector, {dist}({vector_column}, {embeddings}) AS distance from {table}
            ORDER BY distance"""

    if cutoff is not None:
        query+=f" WHERE distance<{cutoff}"

    results = database.session.execute(text(query)).fetchall()
    return pd.DataFrame(results, columns=["csn", "distance"])
