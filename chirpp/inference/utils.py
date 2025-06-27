import re

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