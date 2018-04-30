"""
Uses anti-cloze to evaluate generated schemas ability to retrieve information.

Running this piece of crap:
    python compute-5-anti-close-features.py CONFIG_PATH MODE SCHEMAS.pkl


python compute-5-nastea.py ../subcorporizer_5/op1_semantic.json topical schemas-ch-op1-sem-topical.pkl 

python compute-5-nastea.py ../subcorporizer_5/op1_semantic.json flat schemas-ch-op1-sem-flat.pkl 


Counter-trained:
python compute-5-nastea.py ../subcorporizer_5/op1_semantic.json topical schemas-ct-op1-sem-topical.pkl 

python compute-5-nastea.py ../subcorporizer_5/op1_semantic.json flat schemas-ct-op1-sem-flat.pkl 
#TODO: SOMETHING WRONG WITH THIS LAST ONE--FLAT KEY AT TOP LEVEL NOT SAVED PROPERLY

"""
import pickle
import sys
import ft

import os
from pprint import pprint
import nltk
from math import sqrt
import json

import narch.anticloze as AC
import narch.SER as SER
import narch.corenlp as CNLP
import narch.presence as PRZ
import narch.compare as NCMP
import narch.display

import random

from comp_ents import * #originally part of this script, so fuck off

cfg = json.load(open(sys.argv[1]))
HOLDOUT_PATH = cfg["HOLDOUT_PATH"]

random.seed(19800518)

###########
# Prelims #
###########

print "Loading schemas..."

MODE = sys.argv[2]
SCHEMAS_PATH = sys.argv[3]
SCORE_MODE = "instance"
SCORE_MODE = "canonical"
print SCHEMAS_PATH
schemas = pickle.load(open(SCHEMAS_PATH))
print "Filtering out one-off schemas"
schemas = {f:[(e,v) for e,v in schemas[f] if len(e) > 1] for f in schemas}

# Some shit ripped out of SEC

print "Loading holdout data..."
print "(This takes a little bit--lots of crap.)"

path, dirs, files = os.walk(HOLDOUT_PATH).next()

#files = files[:10] #TODO: DEBUG MODE (TURN THIS SHIT OFF)
#print "IN DEBUG MODE"

print "Holdout files are sampled randomly in this mode"
print "No control for category currently."
print "Total number of holdout files:",len(files)
ho_dumps = []
for f in files:
    fstream = open(os.sep.join([path,f]))
    data = pickle.load(fstream)
    sample_index = random.randint(0,len(data)-1)
    print "Size:",len(data), "Sampling:",sample_index
    try:
        ho_dumps.append(data[sample_index])
    except Exception as e:
        print "Failure to sample."
        print data
    fstream.close()
#ho_dumps = sum([pickle.load(open(os.sep.join([path,f]))) for f in files],[])

# goofy bit here. 
ho_hold = ho_dumps
ho_dumps = [d["raw"] for d in ho_dumps]
for hod,hold in zip(ho_dumps,ho_hold):
    hod["freq_joint"] = hold["freq_joint"]
del ho_hold


def spew(x):
    print x
    return x

print "Tokenizing people, locations, orgs..."
metatags = ["people", "locations", "orgs"]
#metatags = ["people"]
toker = nltk.tokenize.WordPunctTokenizer()
for tag in metatags:
    ho_dumps = ft.tag(ho_dumps, "tokenized_%s" % tag, 
                  lambda N: [toker.tokenize(n) if n else "*NONE*" for n in N], [tag])

ho_dumps = ft.tag(ho_dumps, "entities", lambda *args: sum(args,[]), 
                  ["tokenized_%s" % tag for tag in metatags])

#########################
# Feature Determination #
#########################
#
# Stuff for making sure our schemas align with our data.
#

if MODE == "topical":
    feature_values = list(schemas)
    def go_doc(doc, feature):
        cat, = feature #wrapped in tuples, I forget why
        return cat in doc["online_producer"] 
elif MODE == "flat":
    feature_values = [("flat",)]
    def go_doc(doc,feature):
        return True
else:
    raise Exception("Please provide mode as arg 2: 'topical' or 'flat' ")



######################
# Entity Equivalence # 
######################
#
# MOVED TO comp_ents.py
#

# THIS DAMN THING BETTER STAY PARALLEL OR THERE'S GONNA BE HELL TO PAY

f1_all_values = {}

for feature_value in feature_values:
    wrapped_schemas = [PRZ.wrap_schema(s) for s in schemas[feature_value]]

    f1_n = {"schemas": schemas[feature_value],
            "hashes":  map(NCMP.hash_schema, schemas[feature_value])}
    for n in range(1,50,1):
        F1s = []
        precs = []
        recs = []
        elect_schema_hashes = []
        presences_all = []
        pres_mags_all = []
        for doc in ho_dumps:
            if not doc["entities"]:
                print "No entities for this document."
                continue

            if not go_doc(doc, feature_value): continue
            
            doc = CNLP.prep_tokens(doc)
            
            if SCORE_MODE == "canonical":
                presences = [PRZ.canonicality_factors(doc,S) \
                                for S in wrapped_schemas]
                pres_mags = [i for d,i in presences]
                pres_mags = [d for d,i in presences]
                pres_mags = [d*i for d,i in presences]
            elif SCORE_MODE == "instance":
                presences = [PRZ.instantiation_factors(doc,S) \
                                for S in wrapped_schemas]
                pres_mags = [sqrt(sum([p[x]**2 for x in p],0.0)) 
                                for p in presences]


            scored = sorted(zip(pres_mags, schemas[feature_value]), 
                                        key=lambda x: -x[0])
            
            print sorted(pres_mags)

            #pprint([(m,narch.display.schema_to_string(S)) for m,S in scored])

            elect_schemas = [S for m,S in scored[:n]]
                        #if m >= threshold_min and m <= threshold_max]

            print doc["doc-id"]
            entities = SER.extract_entities(doc,elect_schemas)
            pprint(entities)
            pprint(doc["entities"])
            
            eq_RE = entity_set_eq(entities, doc["entities"])
            eq_ER = entity_set_eq(doc["entities"], entities)

            FP = len(entities) - eq_RE
            FN = len(doc["entities"]) - eq_ER
            quasiTP = entity_intersect(entities, doc["entities"])

            prec = quasiTP/(quasiTP+FP) if FP > 0.0 else 1.0
            rec =  quasiTP/(quasiTP+FN) if quasiTP > 0.0 else 0.0
            F1 = 2*(prec*rec)/(prec+rec) if prec > 0.0 else 0.0
            
            presences_all.append(presences)
            pres_mags_all.append(pres_mags)
            precs.append(prec)
            recs.append(rec)
            F1s.append(F1)
            elect_schema_hashes.append(map(NCMP.hash_schema, elect_schemas))
                    #[S["raw_schema"] for S in elect_schemas]))

            print "eq(R,E):", eq_RE 
            print "eq(E,R):", eq_ER
            print "FP:", FP
            print "FN:", FN
            print "intersect(E,R)"
            print quasiTP
            print
            print "prec:", prec
            print "rec: ", rec
            print "F1:  ", F1 
            print
            print
        
        average_prec = sum(precs)/len(precs)
        average_recs = sum(recs)/len(recs)
        average_F1 = sum(F1s)/len(F1s)
        print "Average F1:", average_F1 
                
        F1 = 2*(average_prec*average_recs)/(average_prec+average_recs)
        f1_n[n] = {"F1_avg":average_F1,
                "F1_micro": F1,
                "prec_avg":average_prec, 
                "rec_avg":average_recs,
                "precs": precs,
                "recs":  recs,
                "presences_all": presences_all,
                "pres_mags_all": pres_mags_all,
                "elect_schema_hashes": elect_schema_hashes,
                }
    f1_all_values[feature_value] = f1_n

metaopts = "".join([o[0] for o in metatags])#for the filename
pickle.dump(f1_all_values, 
            open("anti-cloze-%s-%s_%s_%s.pkl" % (SCORE_MODE,
                                                 metaopts,
                                                 MODE,
                                                 SCHEMAS_PATH), "wb"))










