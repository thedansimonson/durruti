"""
CoreNLP Loader

Loads CoreNLP parses from pickles. 
"""
from pickle import load
import re
import os

group_names = ["period", "dump"]
fn_regex = re.compile(r"nyt_police_([\-\d]+)_dump-([\d]+).pkl")

def fn_parser(fname):
    "Parse a filename into its constituent parts."
    fname = fname.split(os.sep)[-1]
    fn_parse = fn_regex.match(fname)
    if not fn_parse: 
        print fname, "WARNING: filename failed to parse"
        return False

    return dict(zip(group_names, fn_parse.groups()))


def loader(fstream):
    "Loads the filestream and appends metadata"
    metadata = fn_parser(fstream.name)
    if not metadata: return False

    data = load(fstream)

    return data
    
def prep_tokens(doc):
    "Adds tokens and token coordinates to doc. Dead simple."

    token_i = 0
    tokens = []
    lemmas = []
    posses = []
    struc_to_token = {}
    token_to_struc = {}

    for i,sentence in enumerate(doc["cnlp"]["sentences"]):
        for j,word in enumerate(sentence["words"]):
            raw_word, props = word

            tokens.append(raw_word)
            lemmas.append(props["Lemma"]) #maybe extend instead?
            posses.append(props["PartOfSpeech"])

            struc_coord = (i,j)
            token_coord = token_i
            struc_to_token[struc_coord] = token_coord
            token_to_struc[token_coord] = struc_coord

            token_i += 1

    
    doc["tokens"] = tokens
    doc["lemmas"] = lemmas
    doc["struc_to_token"] = struc_to_token
    doc["token_to_struc"] = token_to_struc
    doc["pos"] = posses

    return doc
