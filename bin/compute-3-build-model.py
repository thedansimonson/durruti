"""
Build the PMI based model you've always dreamed of!

(This is basically the "pmi-model" only component of previous iterations.)
"""

import ft, sys, pickle, dill
from narch.generate import scoring, cj2009
from narch import C
from narch.pmi_model_box import PMI_Model
from math import log
from collections import defaultdict
import json


#############
# LOAD DATA #
#############

#TODO: Thread Metainfo

ARGS_FNAME = sys.argv[1]
cfg = json.load(open(ARGS_FNAME))


COUNTS_FNAME = (sys.argv[2] if "INPUT_FILENAME" not in cfg or 
                                               not cfg["INPUT_FILENAME"] 
                            else cfg["INPUT_FILENAME"])
LAMBDA = cfg["LAMBDA"]
BETA = cfg["BETA"]
MAX_SCHEMA_SIZE = cfg["MAX_SCHEMA_SIZE"]
NUMBER_OF_SCHEMAS = cfg["NUMBER_OF_SCHEMAS"]
OUTPUT_HEAD = cfg["OUTPUT_HEAD"]
OUTPUT_FOOT = cfg["OUTPUT_FOOT"]

# Special note for these settings #
# If a verb is below minimum c_counts, then the respective cj_counts 
# will be deleted as well.
C_COUNTS_MIN = cfg["C_COUNTS_MIN"] if "C_COUNTS_MIN" in cfg else 0



source_data = pickle.load(open(COUNTS_FNAME,"rb"))
condensed_counts = source_data["condensed_counts"] 
combos_search = list(condensed_counts)


##############
# DO A THING #
##############
for_export = {
                "ftr_c_counts":         {},
                "ftr_cj_counts":        {},
                "ftr_freq":             {},
                "ftr_total_v_counts":   {},
                "Prob":                 {},
                "Prob_joint":           {},
                "Freq":                 {},
                "LLF_table":            {},
                "LLF":                  {}, #lambda*log(freq(...))
                "Lambda":               {},
                "Beta":                 {},
                "c_counts_min":         {},
                "max_schema_size":      {},
                "number_of_schemas":    {},
                "Types":                {},
                "Depsets":              {},
            }

#inject the above into the namespace (e.g. turn them into variables for the 
#   loop). This seems a strange way to define variables, but it ensures they're
#   "tagged" later for export to the next script.
vars().update(for_export.items())


###########################
# Patch for compatability #
###########################

class default_closure:
    """
    Mimics the "lambda x: d[x] if x in d else default" closure I used 
    previously--but currently doesn't port properly. This should survive
    the pickle.
    """
    def __init__(self, actual_dict, default):
        self.data = actual_dict
        self.default = default

    def __call__(self, query):
        return self.data[query] if query in self.data else self.default


for feature_tuple in combos_search:
    
    print "START",feature_tuple
    
    print "Recovering data from dump..."
    
    get = lambda f: condensed_counts[feature_tuple][f]
    c_counts = get("c_counts")
    cj_counts = get("cj_counts")
    freq_raw = get("freq_raw")
    freq = get("freq")
    

    # Verb Counts for Seeding 
    print "Counting verbs for seeding..."
    verb_count_dex = ft.indexBy("verb",[{"verb": v, "counts": c} 
                                for ((v,d),),c in c_counts.items()])
    local_verb_totals = {v: sum([C["counts"] for C in verb_count_dex[v]]) 
                          for v in verb_count_dex}
    local_verb_max = {v: max([C["counts"] for C in verb_count_dex[v]]) 
                          for v in verb_count_dex}
    verb_below_min = set([v for v,c in local_verb_max.items() if c < C_COUNTS_MIN])
    
    print "Total verb types:", len(local_verb_totals)
    print "Total verb types to remove:", len(verb_below_min)
    print "Removing verbs that appeared an estimated less than",C_COUNTS_MIN,"..."
    
    for c_point in list(c_counts):
        (v,d), = c_point
        if v in verb_below_min: del c_counts[c_point]

    for cj_point in list(cj_counts):
        (v,d),(w,e) = cj_point
        if {v,w} & verb_below_min: del cj_counts[cj_point]

    for freq_point in list(freq):
        ((v,d),(w,e)),t = freq_point
        if {v,w} & verb_below_min: del freq[freq_point]

    for v in list(local_verb_totals):
        if v in verb_below_min: del local_verb_totals[v]
    
    
    ftr_c_counts[feature_tuple] = c_counts
    ftr_cj_counts[feature_tuple] = cj_counts
    ftr_freq[feature_tuple] = freq
    ftr_total_v_counts[feature_tuple] = local_verb_totals

    print "Doing the rest of this prep shit."

    verbdex = ft.indexBy(0, [v for v, in list(c_counts)])
    Depsets[feature_tuple] = {v: [d for w,d in verbdex[v]] for v in verbdex}

    Prob[feature_tuple]  = C.curried_p(c_counts)
    Prob_joint[feature_tuple] = C.curried_p(cj_counts)
    #Freq[feature_tuple] = C.curried_p(freq)
    Freq[feature_tuple] = default_closure(freq, 0.0)
    
    Lambda[feature_tuple] = LAMBDA 
    Beta[feature_tuple] = BETA
    max_schema_size[feature_tuple] = MAX_SCHEMA_SIZE
    number_of_schemas[feature_tuple] = NUMBER_OF_SCHEMAS
    c_counts_min[feature_tuple] = C_COUNTS_MIN

    #TODO: Parameterize type choices.
    Types[feature_tuple] = ["PERSON", "ORGANIZATION"]
    Types[feature_tuple] = list(set([t for pair,t in freq]))
    Types[feature_tuple] = scoring.fancy_types(freq)
    
    lmb = Lambda[feature_tuple]
    llf = lambda pp: lmb*log(Freq[feature_tuple](pp),2) \
                        if Freq[feature_tuple](pp) > 0.0 else -1.0

    LLF_table[feature_tuple] = {pp: llf(pp) for pp in freq}
    """
    LLF[feature_tuple] = lambda pp: LLF_table[feature_tuple][pp] \
                                if pp in LLF_table[feature_tuple] else -1.0
    """

    LLF[feature_tuple] = default_closure(LLF_table[feature_tuple], -1.0)


    print len(Types[feature_tuple]),"types total."
    print

print "Computing general verb totals..."
general_verb_totals = {v: sum([ftr_total_v_counts[ftr][v] 
                               if v in ftr_total_v_counts[ftr] else 0 
                                    for ftr in ftr_total_v_counts])
                                    for v in set(sum([list(D) 
                                    for D in ftr_total_v_counts.values()],[]))}
total_verbs = sum(general_verb_totals.values())

#P(v)
prob_v = {v: float(general_verb_totals[v])/total_verbs 
                        for v in general_verb_totals}

print "Total verbs:",total_verbs

conditioned_models = {}
for feature in combos_search:
    #bubble up the scope of all features in for_export
    local_data = {f: for_export[f][feature] for f in for_export}
    local_data["feature_tuple"] = feature
    conditioned_models[feature] = PMI_Model(local_data)


output_fname = OUTPUT_HEAD+OUTPUT_FOOT.format(**vars())
dill.dump(conditioned_models, open(output_fname,"wb"))
