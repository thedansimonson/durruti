"""
Generates schemas with a countertraining-based technique.
"""
from pickle import load, dump
import dill
from pprint import pprint
from math import log
import sys
import ft
import json

from narch import C, display 
from narch.generate import ct_2, cj2009, scoring


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
# Prepare Arguments for Countertraining #
#########################################
grown_schemas = {}
for feature_tuple in conditioned_models:
    print "Starting",feature_tuple

    model = conditioned_models[feature_tuple]
    args = model.args
    vars().update(vars(model).items())

    # Create Seeds for Schemas #
    c_counts = ftr_c_counts.items()
    c_counts.sort(key=lambda x: -x[1])
    verbs = [v for ((v,d),),c in c_counts]
    pprint(verbs)
    print "Total verbs:",len(verbs)
    
    if len(verbs) == 0: 
        grown_schemas[feature_tuple] = []
        continue
    
    # Wrap Inducter #
    # -- the procedure for adding a candidate to a schema
    """
    # Commented out because I might need bits of this later. 
    args = {"lambda": Lambda[feature_tuple],
            "p": Prob[feature_tuple],
            "pj": Prob_joint[feature_tuple],
            "all_vd_pairs": set(ftr_cj_counts[feature_tuple]),
            "freq": Freq[feature_tuple],
            "llf": LLF[feature_tuple],
            "types": Types[feature_tuple],
            "feature_tuple": feature_tuple,
            "depset": Depsets[feature_tuple],
            "max_size": 6,
            "beta": 0.10,
            "hyperscore": cj2009.narsim,
            "score": scoring.chainsim_prime,
            "period": feature_tuple, #holdover
            }
    """

    ###########################
    # Begin Induction Process #
    ###########################
    out = display.schema_to_string
    schemas = cj2009.grow_list(args, verbs, schema_to_string = out)

    ###################
    # Post-Processing #
    ###################

    # overwrite the schema role fillers with maximally suitable argument types
    schemas = cj2009.exhaustive_roles(args, schemas)

    grown_schemas[feature_tuple] = schemas

output_fname = OUTPUT_HEAD+OUTPUT_FOOT.format(**vars())
dump(grown_schemas, open(output_fname, "wb"))
