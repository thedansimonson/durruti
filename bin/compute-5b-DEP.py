"""
Uses anti-cloze to evaluate generated schemas ability to retrieve information.
"""
import pickle
import sys
import ft
import os

from pprint import pprint

import nltk

from math import sqrt

import narch.anticloze as AC
import narch.SER as SER
import narch.corenlp as CNLP
import narch.presence as PRZ
import narch.display

from comp_ents import * #originally part of this script, so fuck off

###########
# Prelims #
###########


# Some shit ripped out of SEC

print "Loading holdout data..."
print "(This takes a little bit--lots of crap.)"

path, dirs, files = os.walk(sys.argv[1]).next()
#files = files[:2] #DEBUG MODE
ho_dumps = []

######################
# Entity Equivalence # 
######################
#
# MOVED TO comp_ents.py
#

def quasischema(doc):
    """Turns all of the verb roots into a something like a 'schema' so a 
        schematic extractor can get everything.
    """
    events = set(sum([[f for d,s,f in sentence["dependencies"]] \
                         for sentence in doc["cnlp"]["sentences"]],[]))
    
    fauxevents = [(e,[]) for e in events]
    return (fauxevents, [])


F1s = []
precs = []
recs = []


for i,fname in enumerate(files):
    print "Starting file ",i,"/",len(files)
    fstream = open(os.sep.join([path,fname]))
    docs = pickle.load(fstream)
    fstream.close()

    docs = [d["raw"] for d in docs]

    print "Tokenizing people, locations, orgs..."
    metatags = ["people", "locations", "orgs"]
    toker = nltk.tokenize.WordPunctTokenizer()
    for tag in metatags:
        docs = ft.tag(docs, "tokenized_%s" % tag, 
                      lambda N: [toker.tokenize(n) if n else "*NONE*" 
                                    for n in N], [tag])

    docs = ft.tag(docs, "entities", lambda P,L,O: P+L+O, 
                      ["tokenized_%s" % tag for tag in metatags])

    for doc in docs:
        if not doc["entities"]:
            print "No entities for this document."
            continue
        
        doc = CNLP.prep_tokens(doc)
        
        elect_schemas = [quasischema(doc)]

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

        precs.append(prec)
        recs.append(rec)
        F1s.append(F1)

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


prec_avg = sum(precs)/len(precs)
rec_avg = sum(recs)/len(recs)
F1 = 2*(prec_avg*rec_avg)/(prec_avg+rec_avg)

average_F1 = sum(F1s)/len(F1s)
print "Average F1:", average_F1 
print "Micro F1:", F1

#pickle.dump(f1_n, open("threshold-heatmap_pres-mag_dxi.pkl", "wb"))










