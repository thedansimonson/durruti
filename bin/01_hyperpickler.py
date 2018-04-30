"""
Hyperpickler -- retuned for ECB parses from the elections bit
"""
from pprint import pprint
import pickle
import sys
import re
import os
import json
import cnlp_parsing as cnlp
from copy import copy

cfg = json.load(open(sys.argv[1]))

NLPROC_SOURCE =     cfg["NLPROC_PATH"]
TARGET_DUMP =       cfg["TARGET_DUMP"]
USE_EVERYTHING =    cfg["USE_EVERYTHING"]


# Load Corpus Data (from raw)
for path,_,files in os.walk(cfg["DATA_PATH"]):
    raw_corpus_data = []
    for fname in files:
        full_path = os.sep.join([cfg["DATA_PATH"], fname])
        raw_text = open(full_path).read()
        
        raw_corpus_data.append({"filename":fname,
                             "raw_text":raw_text,
                            })



POSITIVE_FLAG = "void"

# Build Parse File Index
# This lets the system load up the relevant parse locations.
print "Preparing index of parse locations..."
parse_file_rx = re.compile("^(.+\\.txt)\\.xml$")
parse_file_index = {}

for path,dirs,files in os.walk(NLPROC_SOURCE):
    print path
    for f in files:
        f_match = parse_file_rx.match(f)
        if f_match:
            nyt_id, = f_match.groups()
            parse_file_index[nyt_id] = os.sep.join([path,f])
        else: print "Match failed:",f
    print "Files so far:",len(parse_file_index)

print "parse_file_index size:",len(parse_file_index)
print list(parse_file_index)[:10]


# Functions used in NYT Crawl

def dump(stuff, stuffs):
    ""
    print "Dumping "+`stuffs`
    fstream = open(os.sep.join([TARGET_DUMP,
                                "dur-data-hyperpickled_%s.pkl"%`stuffs`]), "wb")
    pickle.dump(stuff, fstream)
    fstream.close()

def ident(doc):
    doc["doc-id"] = doc["filename"] #replacing the doc-id with hashes
    return doc

stuffs = 0
stuff_len = 1000 
stuff = []

for doc in raw_corpus_data:
    doc = copy(ident(doc)) # copy is to help with memory leakage (hopefully)
    if POSITIVE_FLAG in doc or USE_EVERYTHING:
        
        try:
            xmls = open(parse_file_index[doc["filename"]]).read()
        except:
            print "FAILED:", doc
            print "Parse path not found! (Path doesn't exist, or doc-id not in index)"
            print doc["filename"]
            continue

        try:
            outdict = cnlp.parse_parser_xml_results(xmls)
            doc["cnlp"] = outdict
        except Exception as e:
            #print xmls
            print "FAILED:",doc["filename"]
            print "XML failed to parse properly."
            #raise e
            continue

        stuff.append(doc)
    
    if len(stuff) % (stuff_len / 10) == 0: print len(stuff)
    if len(stuff) > stuff_len:
        #it's happening again
        
        dump(stuff, stuffs)

        stuffs += 1 
        stuff = []

dump(stuff, stuffs)

        

