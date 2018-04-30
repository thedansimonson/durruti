"""
Schematic Entity Retrieval 
"""
import C 
import os
import ft
import re
import sys
from copy import copy
from pprint import pprint

#sys.setrecursionlimit(2000)

__location__ = os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__)))

#load supporting data
dep_path = os.path.join(__location__, 'dependency-collapse-list.txt')
fstream = open(dep_path)
dep_coll_table = C.load_dep_collapse(fstream)
fstream.close()


def dictpath(data, path):
    return data[path[0]] if len(path) == 1 else dictpath(data[path[0]], path[1:])

def get_proc(doc):
    "Gets all events and role fillers from a doc"
    dump = doc["cnlp"]
    
    # This was ripped out of compute-1
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
    #words = [w for w in words if w[2] not in stoplist]
    
    return {"dep_raw": dep_raw, 
            "dependencies": dependencies,
            "words": words}
    
def expand_entities(E,dep_raw):
    "Obtain entire subtree with root of e"
    depdex = ft.indexBy(1, dep_raw)
    return sum([expand([e],depdex) for e in E],[])

barriers = re.compile("prep.*|conj.*")

def expand(E, depdex, recursive_digging = True):
    E_out = copy(E)
    buried = []
    while E:
        deps = sum([depdex[e] for e in E if e in depdex],[])
        
        #this probably seems weird, but it's to remove loops in the graph
        # should they exist (and I think they do). This way, we only handle
        # dependencies once for a point, then boom, never again.
        for e in E: 
            if e in depdex: del depdex[e]

        # create barriers--that is, stuff in a PP should be a separate entity
        # for our purposes
        deptypedex = ft.indexBy(0, deps)
        bartypes = set([t for t in deptypedex if barriers.match(t)])
        localtypes = set(deptypedex) - bartypes
        buried.extend(sum([[f for d,e,f in deptypedex[t]] for t in bartypes],[]))
        deps = sum([deptypedex[t] for t in localtypes],[])

        E = [f for d,e,f in deps]
        E_out.extend(E)
    if recursive_digging:
        return [E_out] + sum([expand([e], depdex) for e in buried],[])
    else:
        return [E_out]
   
token_exclusions = {"Mr.","Mrs."}

def approp_filter(entity, nlproc):
    output = []
    for loc in entity:
        sent_i, word_i, token = loc
        #the [1] is the position of the properties dict for that token
        pos = nlproc["sentences"][sent_i]["words"][word_i][1]["PartOfSpeech"]
        net = nlproc["sentences"][sent_i]["words"][word_i][1]["NamedEntityTag"]
        if pos not in {"NNP"}: continue
        if net in {"DATE"}: continue

        if token in token_exclusions: continue
        
        output.append(loc)
    return output


def extract_entities(doc, schemas, retain_coords = False):
    "Get all *untyped* entities from a doc using a provided schema"
    proc = get_proc(doc)

    
    # Get relevant events
    print "Retrieving events..."
    events = []
    for schema in schemas: 
        sevents_raw, schains = schema
        sevents = [v for v,R in sevents_raw]
        sevents = [(s,w, v) for s,w, v in proc["words"] if v in sevents]
        events.extend(sevents)
    
    
    # Get relevant dependencies
    print "Obtaining relevant dependencies"
    coord_eq = lambda w,d: w[:2] in {d[1][:2], d[2][:2]}
    real_deps = [d for d in proc["dependencies"] if \
                    any([coord_eq(e,d) for e in events])]

    entities = [e for d,v,e in real_deps]

    # Possible--peruse coref for fixins.

    #expand entities to all their nodes
    print "Getting entitites"
    entities = expand_entities(entities, proc["dep_raw"])

    # filter for NNPs
    print "Clean up"
    entities = [approp_filter(e, doc["cnlp"]) for e in entities]
    entities = [e for e in entities if e] # clean up empties
    

    #flatten
    if not retain_coords:
        entities = [tuple([t for s,w,t in sorted(NP)]) for NP in entities]
    
    print "entities retrieved"

    return set(entities)





