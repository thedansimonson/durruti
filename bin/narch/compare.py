"""
Comparison between schemas with documents intervening. 

Dan Simonson, 2014

"""
from pprint import pprint
from display import schema_to_string

#########################################
# Doc-based comparison.                 #
#   (an implementation of Tony's idea)  #
#########################################
#
# rank 

# schema-to-doc scoring methods #

def inverse_doclen(S, doc):
    """Weight event-chain matches inversely with document length.
    S = narrative schema, a tuple of E,C 
    doc = a list of sets of verb-dependency pairs from a real document
    """
    
    E, n_chains = S
    n_chains = map(set, [args for args, types in n_chains])
   
    scores = []
    doc = [c for c in doc if c]
    doclen = len(doc)
    
    for e_chain in doc:
        best_match = float(max([len(n & e_chain) for n in n_chains]))/doclen
        scores.append(best_match)

    #takes the best match--we don't want to penalize for mismatches
    #if the schema fits something in the document, we're happy
    return float(sum(scores))/len(scores) if scores else None
    #return max(scores) if scores else None

# schema-to-schema similarity #
def fraction_match(S,T):
    "Return the fraction of events of S that match those in T."
    E,chains = S
    F,chainz = T
    
    remove_types = lambda X: [v for v,t in X]
    E = remove_types(E)
    F = remove_types(F)
    overlap = set(E) & set(F) 
    
    #I don't wanna penalize against small schema if one is shorter. If we
    #have len(S) == 3 and len(T) == 6, and the len(overlap) is 3, we have 
    #a perfect match. That's why min gets used here.
    norm = min(map(len,[E,F]))
    
    return float(len(overlap))/norm

# actual scoring #

def via_docs(schemas, docs, scorer):
    """
    Compare schemas via docs.

    Args:
    schemas = narrative schemas of the form handled by 
        gen_schema.schema_to_string
    docs = docs dumped out by corenlp_python
    scorer = compares a schema to a document
    """
    
    scores = []
    for S in schemas:
        subscores = [scorer(S,d) for d in docs]
        subscores = [s for s in subscores if s is not None]
        score = sum(subscores,0.0)/len(docs)
        scores.append(score)
    return scores


def rank_arrange(anchors, shifters, similarity):
    """
    Return the number of re-arrangements required to align two sets of schema,
        ordered by similarity. 

    Args:
    anchors/shifters = (score, schema) pairs
        anchors stay fixed while shifters move

    """
    #sort by scores, effectively, then dump them.
    anchors = [S for s,S in sorted(anchors)]
    shifters = [S for s,S in sorted(shifters)]
    
    #returns the index of the best-fitting anchor for S
    best_fit = lambda S: \
        max([(similarity(S,T),i) for i,T in enumerate(anchors)])[1]
    shifters = [(best_fit(S), S) for S in shifters]
    swapperations = 0
    
    #print "***** ANCHORS *****"
    #pprint(zip(range(0,len(anchors)), anchors))
    #print "***** SHIFTERS *****"
    #pprint(shifters)

    doing_stuff = True
    while doing_stuff:
        doing_stuff = False
        for i in range(0,len(shifters)-1):
            this,below = shifters[i],shifters[i+1]

            #I think this right
            if this[0] > below[0]: 
                shifters[i], shifters[i+1] = shifters[i+1], shifters[i]
                swapperations += 1
                doing_stuff = True

        #print "FRAME*"
        #pprint(shifters)

    print
    return swapperations



def hash_schema(schema, use_verbs = True, use_chains = False):
    "Create a hash of a schema based on its composition."
    
    events, chains = schema

    if use_chains: 
        raise Exception("Chains aren't implemented yet in schema hashes.")
    else:
        chain_factor = 1

    if use_verbs:
        verb_factor = hash("".join(sorted([v for v,c in events])))
            
    else: 
        verb_factor = 1

    return verb_factor*chain_factor
    

def jaccard_eventive(schema,tchema):
    "Jaccard between two schemas w.r.t. their events"
    events, chains = schema
    fvents, dhains = tchema
    
    events = set([v for v,c in events])
    fvents = set([v for v,c in fvents])

    return float(len(events & fvents)) / len(events | fvents)
    

def jaccard_fuzzy_superset(schemas, tchemas, comparison):
    """
    Do a fuzzy Jaccard coefficient computation for two sets of schemas.
    """

    fuzzy_intersect_mag = lambda A,B,k: sum([max([k(a,b) for a in A]) 
                                              for b in B]) 


    intersect = fuzzy_intersect_mag(schemas,tchemas,comparison)

    return float(intersect) / (len(schemas) + len(tchemas) - intersect)


def jaccard_fuzzy_superset_verbose(schemas, tchemas, comparison):
    """
    Do a fuzzy Jaccard coefficient computation for two sets of schemas.
    """

    fuzzy_intersect_mag = lambda A,B,k: sum([max([k(a,b) for a in A]) 
                                              for b in B]) 
    def fuzzy_intersect_mag(A,B,k):
        for b in B:
            a_scores = []
            for a in A:
                a_scores.append(k(a,b))
            a_max = max(a_scores)
            a_index = a_scores.index(a_max)
            a = A[a_index]

            print "Best match a for b"
            print "a_max:", a_max
            print "a_index:", a_index
            print "a:"
            print schema_to_string(a)
            print "b:"
            print schema_to_string(b)
            print

        return 


    intersect = fuzzy_intersect_mag(schemas,tchemas,comparison)

    return float(intersect) / (len(schemas) + len(tchemas) - intersect)
