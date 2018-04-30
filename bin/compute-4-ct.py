"""
Generates schemas with a countertraining-based technique.
"""
from pickle import load, dump
from pprint import pprint
from math import log,sqrt
import sys
import ft
import json
import dill

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
for i,feature_tuple in enumerate(conditioned_models):
    print "Starting",feature_tuple

    model = conditioned_models[feature_tuple]
    args = model.args
    vars().update(vars(model).items()) #Injection hell. Sorry. 

    schema_seeds = [S for S in args["make_seeder"](args)]
    
    print len(schema_seeds), "for this feature tuple."

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
            "beta": 0.3,
            "hyperscore": cj2009.narsim,
            "score": scoring.chainsim_prime,
            "period": feature_tuple, #holdover
            }
    """
    #copy class methods from the model box
    inducter = lambda S,v: args["inducter"](args,S,v)
    sim_measure = lambda S,v: args["sim_measure"](args,S,v)

    # Verb Loading Crap Doodle #
    #This was an optimization originally, I believe.
    verbs = list(Depsets)
    
    # Schema Terminator #
    """
    def terminator(S, scores):
        if not scores: return True
        if all([s <= 0.0 for s in  scores.values()]): return True
        return len(S[0]) > 5
    """
    terminator = args["schema_terminator"]

    # Local Candidate Pruner #
    def pruner(S, candidates, scores):
        events, types = S
        prunes = [v for v,R in events] #already inside a schema
        prunes.extend([v for v in scores if scores[v] <= 0.0]) #garbage
        return [can for can in candidates if can not in prunes]

    #########################
    # Begin Countertraining #
    #########################
    schemas = ct_2.countertrain(schema_seeds, inducter, terminator, 
                                sim_measure, 
                                verbs, pruner)

    ###################
    # Post-Processing #
    ###################

    # overwrite the schema role fillers with maximally suitable argument types
    schemas = cj2009.exhaustive_roles(args, schemas)

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
