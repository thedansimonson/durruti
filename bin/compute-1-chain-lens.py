"""
Use a subcorporizer_4 config file to launch counting. Provides:
    TARGET_DUMP
    HOLDOUT_PATH

python compute-1-count-flat-holdout.py /home/emperor/Desktop/School/subcorporizer_4/kw1-1.json

python compute-1-cap-extract.py /home/emperor/Desktop/School/diss-engines/subcorporizer_5/op1_semantic.json

python compute-1-cap-extract.py /home/emperor/Desktop/School/diss-engines/20_LN-subcorporizer/LNTH_2.json
"""


from narch import corenlp, C, seeding
import os
import ft
import sys
from pprint import pprint
from random import randint
import random

import json

from pickle import dump as pickle_dump
import pickle


#extract count data from coreference chains
cfg = json.load(open(sys.argv[1]))
coref_dumps = cfg["TARGET_DUMP"]
USE_HOLDOUT = cfg["USE_HOLDOUT"]
HOLDOUT_PATH = cfg["HOLDOUT_PATH"]
UINDEX_KEY = cfg["UNIQUE_INDEX"] #This was new at the LNTH step. op1/kw1 lack this param (should be "doc-id" for them though.).
path, dirs, dump_fnames = os.walk(coref_dumps).next()

if cfg["USE_HOLDOUT"]:
    print "HOLDOUT ACTIVE"
else: 
    print "HOLDOUT INACTIVE"


if cfg["TEST_MODE"]: 
    print "WARNING: TEST MODE. FIX THAT SHIT IN THE CONFIG IF YOU DON'T LIKE IT."
    dump_fnames = [dump_fnames[0]]

#feature values establish these dicts
Prob = {}
Prob_joint = {}

Counts = {}
Counts_joint = {}
Freq = {}

coref_empties = 0
files_done = 0


#load supporting data
fstream = open("dependency-collapse-list.txt")
dep_coll_table = C.load_dep_collapse(fstream)
fstream.close()

fstream = open("stopwords.txt")
stoplist = seeding.load_stoplist(fstream)
fstream.close()

###################
# TYPING FUNCTION #
###################
# For some word w, f(w) in {True, False} 
# True if the word's type should be included in the list of types for a 
# narrative chain.

#(accept everything!)
best_types = lambda w: True

# newer best types 
target_POS = {"NN", "NNS"}
best_types = lambda w: w["PartOfSpeech"] in target_POS


#######################
# FEATURE DEFINITIONS #
#######################

def online_producer(doc):
    return doc["online_producer"] if "online_producer" in doc else []
    
def doc_id(doc):
    return doc[UINDEX_KEY]
    
def lda(doc):
    #for actually implementing this, run LDA over docs first
    return doc["lda_distro"]

def flat(doc):
    return "flat"

def cat_match(doc):
    return doc["cat_match"]



feature_options = {"doc-id": doc_id,
                   "cat-nyt-op": online_producer,
                   "cat-lda": lda,
                   "cat-match": cat_match,
                   "flat": flat}

feature_choices = ["doc-id", "cat-nyt-op"]
feature_choices = ["doc-id", "cat-match"]
feature_choices = ["flat"]
feature_choices = cfg["FEATURE_CHOICES"]

feature_defs = [feature_options[choice] for choice in feature_choices]

MODE = "-".join(feature_choices)

random.seed(19800518)

total_files = len(dump_fnames)
files_done = 0
data_eax = []
all_chains = {}

for dump in dump_fnames:
    files_done += 1
    dump_fname = dump
    print dump, ":", files_done, "/", total_files
    dump_fs = open(os.sep.join([path, dump]))
    superdump = pickle.load(dump_fs)
    dump_fs.close()
    
    # set aside a tenth of this dump for holdout
    random.shuffle(superdump) 
    if USE_HOLDOUT: holdout = lambda i: i > len(superdump)/10 * 9
    else:           holdout = lambda i: False
    holdout_data = []
    
    print "Starting count phase..."
    
    for j,quasidump in enumerate(superdump):
        
        ################
        # Counts Phase #
        ################

        print quasidump[UINDEX_KEY], "running."
        dump = quasidump["cnlp"]
        if "sentences" not in dump: continue
        if "coref" not in dump: continue

        dependencies = dump["sentences"]
        dependencies = [s["indexeddependencies"] for s in dependencies]
        dependencies = [[C.dep_norm(i,d) for d in s] \
                        for i,s in enumerate(dependencies)]
        #dependencies[0] = C.remove_redundant(dependencies[0]) #corpus bug?
        dependencies = sum(dependencies, [])
        
        dep_raw = dependencies
        dependencies = C.dep_collapse(dependencies, dep_coll_table)
        
        #digs out words for us, cause words cross sentences boundaries
        words = C.relevant_words(dump["sentences"], C.relevant_verbs)
        words = [w for w in words if w[2] not in stoplist]
        words = [C.agglodep(w,dep_raw) for w in words]

        corefs = dump["coref"]
        corefs = [(C.coref_flatten(co,dep_raw), co) for co in corefs]
        #corefs = [(c,craw) for c,craw in corefs if len(c) > 4]
        
        for c,craw in corefs:
            if len(c) in all_chains: all_chains[len(c)]+=1
            else: all_chains[len(c)] = 1

        for c,craw in corefs:
            print "post-flattened:",c
            print "original:",craw
            print

        print
        print
        print

print "***DONE***"
fstream = open(cfg["COUNTS_TYPED_PATH"]%MODE,"wb")
pickle_dump(data_eax, fstream)
fstream.close()
    

fstream = open(cfg["COUNTS_HEADS_PATH"]%MODE,"wb")
pickle_dump(C.HN_counter, fstream)
fstream.close()



