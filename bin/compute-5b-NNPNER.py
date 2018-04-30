import nltk
from comp_ents import *

import os
import ft
import sys
import pickle

import narch.anticloze as AC
import narch.SER as SER
import narch.corenlp as CNLP
import narch.presence as PRZ
import narch.display

from comp_ents import *

from pprint import pprint


###########
# Prelims #
###########


# Some shit ripped out of SEC

print "Loading holdout data..."
print "(This takes a little bit--lots of crap.)"

path, dirs, files = os.walk(sys.argv[1]).next()
#files = files[:2] #DEBUG MODE
ho_dumps = []

##############
# DO A THING #
##############

NER_targets = {"PERSON", "LOCATION", "ORGANIZATION"}

def NNP_entities(doc):
    cnlp = doc["cnlp"]
    proc = SER.get_proc(doc)

    candidate_locs = []
    for i,sentence in enumerate(cnlp["sentences"]):
        for j,word in enumerate(sentence["words"]):
            print word[1]["NamedEntityTag"]
            if word[1]["PartOfSpeech"] in {"NNP"} \
                    and word[1]["NamedEntityTag"] not in NER_targets:
                candidate_locs.append((i,j,word[0]))

    entities = SER.expand_entities(candidate_locs, proc["dep_raw"])

    # goes through--puts entities in reverse max order. if one entity is
    # contained in another larger one, delete the smaller.
    entities = sorted(entities, key = lambda E: -len(E))
    for i, entity in enumerate(entities):
        for w in entity:
            tag_to_del = []
            for j, fentity in enumerate(entities[i+1:]):
                if w in fentity: 
                    #print "Deleting",entities[j+i+1]
                    #print "because of",entities[i]
                    tag_to_del.append(j+i+1)

            tag_to_del.sort()
            tag_to_del.reverse()
            for z in tag_to_del:
                del entities[z]


    entities = [tuple([t for s,w,t in sorted(NP)]) for NP in entities]
    return set(entities)



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

        entities = NNP_entities(doc)
        
        print doc["doc-id"]
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


