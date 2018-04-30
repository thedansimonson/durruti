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
HOLDOUT_PATH_DEV = cfg["HOLDOUT_PATH_DEV"]
HOLDOUT_PATH_TEST = cfg["HOLDOUT_PATH_TEST"]
UINDEX_KEY = cfg["UNIQUE_INDEX"] #This was new at the LNTH step. op1/kw1 lack this param (should be "doc-id" for them though.).
# if you want specific strings to be types in the schemas, use this argument
KW_EXACT = cfg["KEYWORD_TYPES"] if "KEYWORD_TYPES" in cfg else [] 
KW_EXACT += [k.lower() for k in KW_EXACT] 
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

if KW_EXACT:
    best_types = lambda w: (w["PartOfSpeech"] in target_POS or 
                            w["Lemma"] in KW_EXACT)


#######################
# FEATURE DEFINITIONS #
#######################

def online_producer(doc):
    return doc["online_producer"] if "online_producer" in doc else []

def electoral_period_func(doc):
    return doc["electoral_period"]

def source_func(doc):
    return doc["source"]
    
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
                   "flat": flat,
                   "electoral_period": electoral_period_func,
                   "source": source_func}

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
for dump in dump_fnames:
    files_done += 1
    dump_fname = dump
    print dump, ":", files_done, "/", total_files
    dump_fs = open(os.sep.join([path, dump]))
    superdump = pickle.load(dump_fs)
    dump_fs.close()
    
    # set aside 2 / 10ths: 1/10 for dev, 1/10 for test
    random.shuffle(superdump) 
    if USE_HOLDOUT: holdout = lambda i: i > len(superdump)/10 * 8
    else:           holdout = lambda i: False
    holdout_data_dev = []
    holdout_data_test = []
    
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
        corefs = [(c,craw) for c,craw in corefs if len(c) > 4]
        coref_types = \
            [C.coref_type((c,c_raw), dump["sentences"], best_types) \
            for c,c_raw in corefs]

        if C.TYPE_ERROR in coref_types:
            print "Error in coref_types"
            print coref_types
            print "This document will be ignored."
            print 
            continue
        
        try:
            corefs, craws = zip(*corefs)
        except:
            print "Error in corefs"
            pprint(corefs)
            print coref_types
            print "this happened",coref_empties,"times"
            coref_empties+=1
            continue

        """ 
        for chain, typ in zip(corefs, coref_types):
            print typ
            pprint(chain)
            print "\n\n"
        """
        #these args are used for all the extractions
        extraction_args = (corefs, words, dependencies)

        c_single = C.extract_c(*extraction_args)
        c_joint = C.extract_cj(*extraction_args)
        freq_joint = C.extract_cj(*extraction_args, types = coref_types)

        ###############################
        # Feature Determination Phase # 
        ###############################
        
        featlocs = dict(zip(feature_choices,
                        [feat(quasidump) for feat in feature_defs]))

        ##############
        # Save Phase #
        ##############

        doc_data = {"c_single": c_single,
                    "c_joint": "extract from freq_joint",
                    "freq_joint": freq_joint,
                    UINDEX_KEY: quasidump[UINDEX_KEY]}
        if holdout(j):
            doc_data["raw"] = quasidump
            doc_data["corefs"] = corefs
            doc_data["words"] = words
            doc_data["deps"] = dependencies
            doc_data.update(featlocs.items())
            if j%2 == 0:
                holdout_data_dev.append(doc_data)
            else:
                holdout_data_test.append(doc_data)
        else:
            doc_data.update(featlocs.items())
            data_eax.append(doc_data)
    
    if USE_HOLDOUT:
        print "Saving holdout..."
        feature_names = "_".join(feature_choices)
        fname_args = (str(feature_names),str(dump_fname))
        foxhole = HOLDOUT_PATH_DEV + ("holdout-dev-%s-%s.pkl" % fname_args)
        fxstream = open(foxhole,"wb")
        pickle.dump(holdout_data_dev,fxstream)
        fxstream.close()

        feature_names = "_".join(feature_choices)
        fname_args = (str(feature_names),str(dump_fname))
        foxhole = HOLDOUT_PATH_TEST + ("holdout-test-%s-%s.pkl" % fname_args)
        fxstream = open(foxhole,"wb")
        pickle.dump(holdout_data_test,fxstream)
        fxstream.close()

    #pprint(c_single_eax)
    print "STATS:",dump
    print "data_eax:",len(data_eax)
    #c_counts = C.condense_c(c_single_eax)
    #cj_counts = C.condense_c(c_joint_eax)
    #freq = C.condense_c(freq_joint_eax)

    #Prob[period]  = C.curried_p(c_counts)
    #Prob_joint[period] = C.curried_p(cj_counts)


print "***DONE***"
fstream = open(cfg["COUNTS_TYPED_PATH"]%MODE,"wb")
pickle_dump(data_eax, fstream)
fstream.close()
    

fstream = open(cfg["COUNTS_HEADS_PATH"]%MODE,"wb")
pickle_dump(C.HN_counter, fstream)
fstream.close()



