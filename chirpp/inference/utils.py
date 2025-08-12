import re
import numpy as np

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


def cosine_similarity_numpy(vec_a, vec_b):
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