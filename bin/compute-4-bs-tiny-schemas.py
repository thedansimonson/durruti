"""
Generates schemas with random walks.

New version: (will eventually) require compute-3 pre-processed components
"""
from pickle import load, dump
import dill
from pprint import pprint
from math import log,sqrt
import sys
import ft
import json

from narch import C, display 
from narch.generate import random_walk, cj2009, scoring, ct_2
from collections import defaultdict
from copy import deepcopy


ARGS_FNAME = sys.argv[1]
cfg = json.load(open(ARGS_FNAME))


MODEL_FNAME = (sys.argv[2] if "INPUT_FILENAME" not in cfg or 
                                               not cfg["INPUT_FILENAME"] 
                            else cfg["INPUT_FILENAME"])

MODEL_FNAME_SHORT = MODEL_FNAME.split("/")[-1]

conditioned_models = dill.load(open(MODEL_FNAME))
OUTPUT_HEAD = cfg["OUTPUT_HEAD"]
OUTPUT_FOOT = cfg["OUTPUT_FOOT"]


#########################################
# Prepare Arguments for Random Walk     #
#########################################
grown_schemas = {}
for i,feature_tuple in enumerate(conditioned_models):
    print "Starting",feature_tuple
    
    model = conditioned_models[feature_tuple]
    args = model.args


    ########################
    # Synthesize This Shit #
    ########################
    
    schemas = []
    

    caps = list(model.ftr_cj_counts)
    for i,cap in enumerate(caps):
        print i,cap
        ((v,d),(w,e)) = cap
        vdeps = args["depset"][v]
        wdeps = args["depset"][w]
        events = [(v,vdeps),(w,wdeps)]
        chains = [(list(cap), [])]
        schemas.append((events, chains))
     

    ###################
    # Post-Processing #
    ###################

    # overwrite the schema role fillers with maximally suitable argument types
    #schemas = cj2009.exhaustive_roles(args, schemas)

    grown_schemas[feature_tuple] = schemas
    print "Generation for",feature_tuple,"complete."
    print i+1,"/",len(conditioned_models), "feature tuples."

    #TODO: This is really a pmi specific issue and belongs wrapped in args
    #       from the prior script, but I don't really have time to regenerate
    #       all those damn models.
    #
    #       This won't break with other model types, but I can see the need for
    #       a post-iteration clean-up hook. 
    scoring.purge_pmi_cache()
    print "pmi_cache purged"

output_fname = OUTPUT_HEAD+OUTPUT_FOOT.format(**vars())
dump(grown_schemas, open(output_fname, "wb"))
