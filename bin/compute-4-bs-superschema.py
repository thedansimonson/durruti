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

    (seed,),verbs = list(model.ftr_c_counts)[0], list(model.ftr_c_counts)[1:]
    print seed
    schema = cj2009.schema_init([seed[0]], args["depset"])[0]
    print schema
    for (v,d), in verbs:
        print v
        
        #Dumb insertion
        schema = cj2009.schema_insert_dumb(args, 
                                            schema, 
                                            (v, args["depset"][v]), 
                                            score = args["score"])

        #Proper insertion (old)
        #schema = cj2009.schema_insert(args, schema, (v, args["depset"][v]), 
        #    score = args["score"])
     
    schemas = [schema]

    ###################
    # Post-Processing #
    ###################

    # overwrite the schema role fillers with maximally suitable argument types
    #schemas = cj2009.exhaustive_roles(args, schemas)
    # (off, too slow)

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
