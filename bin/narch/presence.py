"""
Measures of schema presence. For a particular doc/schema vector, use
'local_schema_presence'.

"""
import ft,re

verb_rx = re.compile("V.*")
def doc_Match(doc, schema):
    events = set(schema["events"])
    lemmas = enumerate(zip(doc["lemmas"], doc["pos"]))
    return [(i,l) for i,(l,p) in lemmas if l in events and verb_rx.match(p)]

############################################
# Measure Canonicality (original presence) #
############################################

def canonicality_factors(doc, schema):
    """
    Provided a doc and a schema, gives a tuple of the components of 
    canonicality (density and inverse dispersion of events).
    
    This is the "document-normalized" measure. For the schema-normalized 
    measure, use instantiation_factors.
    
    
    WARNING: doc must be preprocessed with narch.corenlp.prep_tokens
    """
    matches = doc_Match(doc,schema)
    if not matches: return (0.0,0.0)
    
    #hard-coded choice here
    sentential = lambda x: doc["token_to_struc"][x[0]][0]
    lemmantic = lambda x: x[0]
    unpack = sentential
    
    #sentential converts lemma position to sentence position automatically
    #so this doesn't need to be changed when unpack changes
    DOCLEN = unpack((len(doc["lemmas"])-1,))+1

    
    density = float(len(matches)) / DOCLEN

    d = lambda l,m: abs(l - m)
    matches = set(map(unpack,matches))
    minimum_distance = lambda l: min([DOCLEN]+\
                                [d(l,m) for m in set(matches) - {l}])
    inv_dispersion = float(len(matches)) / sum(map(minimum_distance,matches))

    return (density, inv_dispersion)


#########################
# Measure Instantiation #
#########################

def instantiation_factors(doc, schema):
    ""
    # extract caps from schema
    events, chains = schema["raw_schema"]
    
    schema_caps = []
    for slots,args in chains:
        slots = sorted(slots)
        for i,slot in enumerate(slots):
            for tlot in slots[i:]:
                schema_caps.append((slot,tlot))

    
    # extract caps from doc
    doc_caps = [cap for cap,t in doc["freq_joint"] if cap in schema_caps]
    
    CAP = "CAP"
    counts = ft.histo(ft.indexBy(CAP,[{CAP: x} for x in doc_caps]))

    return counts
 



def total_schema_presence(docs, schemas):
    "This is deprecated. I don't think any scripts use this."
    for doc in docs:
        presmags = []
        for schema in schemas:
            vec = canonicality_factors(doc,schema)
            presmags.append(sqrt(sum([x**2 for x in vec]))) 
        doc["schema_presence"] = str(sum(presmags)/float(len(presmags)))[:5]
    return (docs,)


def wrap_schema(schema):
    "Pulls raw details out for easier use in other stuff."
    events, chains = schema
    flat_actors = sum([a for S,a in chains],[])
    flat_events = [e for e,S in events]

    return {"raw_schema": schema,
            "actors": flat_actors,   
            "events": flat_events}
    
