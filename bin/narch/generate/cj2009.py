"""
Generate narrative schemas based on PMI. Closely related Chambers and 
Jurafsky (2009)'s approach to schema generation. 

Schema are represented by a dictionary such that:
    {"events": [(verb, dependency options), ... ]
     "chains": [(verbdep list, types), ... ]}

"""
import scoring
from pprint import pprint
from copy import copy
from datetime import datetime
import ct_2

def narsim(A, N, verb, score = scoring.chainsim_prime):
    "The scoring used for adding verbs to schema."
    D = A["depset"]
    beta = A["beta"]

    events, chains = N
    #events = N["events"] # [(v, deps), ... ]
    #chains = N["chains"] # [(verbdeps, types) ...]

    #possible optimization?
    # not amazing, but it shaves about 20% off the time.
    vd_universe = A["all_vd_pairs"]
    candidate_pairs = [sum([[tuple(sorted([vd, (verb,d)])) for d in D[verb]] \
                            for vd in chain],[]) \
                            for chain,roles in chains]
    worthwhile = [any([vdp in vd_universe for vdp in can_chain])\
                    for can_chain in candidate_pairs]
    if not any(worthwhile): return beta*len(D[verb])
    
    # actual computation
    dep_scores = []
    for d in D[verb]:
        scores = [score(A, chain, (verb, d))\
            for (chain, types),worthy in zip(chains,worthwhile) if worthy]
        scores, types = map(list, zip(*scores))
        dep_scores.append(max([beta, max(scores)]))

    return sum(dep_scores)

    
def schema_init(verbs, depsets):
    """
    Initialize a schema from a list of verbs.

    The intuition:
        we initialize a schema from a single verb. So, for buttered:
            He buttered the toast with the knife.
        we have
        MAN buttered FOOD *INSTRUMENT
    Were this schema grown:
        MAN ate FOOD

    The verb "buttered" indicated quite nicely the slots available.  
    """
    inited = []
    for verb in verbs:
        depset = depsets[verb]
        events = [(verb, depset)]
        chains = [([(verb,dep)], []) for dep in depset]
        inited.append((events,chains))
    return inited

def schema_insert(A, N, new_event, score = scoring.chainsim_prime):
    """
    Add a verb to a schema--optimize its verb fits.

    Chain assignment > beta measure. Doesn't actively avoid conflating
    bound arguments.
    
    Args:
        A = dict of args (stupid, I know), "beta" required, and those for
            score
        N = a narrative schema--a tuple, of events and chains
        new_event = a verb to be inserted into the schema
    """
    beta = A["beta"]

    events, chains = N
    events.append(new_event)

    verb, depset = new_event
    
    for vd in [(verb, d) for d in depset]:
        # Chain-splitting revisions go here. Dangling arguments are used
        # to start new chains.
        scores = [(i,score(A,c,vd))for i,(c,types) in enumerate(chains)]
        scores = [(i,s,t) for i,(s,t) in scores]
        besti, b_score, b_type = max(scores, key = lambda x: x[1])
        
        if b_score > len(chains[besti])*beta:
            chains[besti][0].append(vd)     #add to chain
            chains[besti][1].append(b_type) #add to types
        else:
            print "No sufficiently high score. Chain split."
            chains.append(([vd], []))

    return (events,chains)


def schema_insert_dumb(A, N, new_event, score = scoring.chainsim_prime):
    """A dumb insertion method that assumes all SUBJ / OBJ / PREP belong 
        together for baselines."""
    
    beta = A["beta"]

    events, chains = N
    events.append(new_event)

    verb, depset = new_event
    
    for vd in [(verb, d) for d in depset]:
        # Chain-splitting revisions go here. Dangling arguments are used
        # to start new chains.
        scores = [(i,c[0][1] == vd[1],"crap")for i,(c,types) in enumerate(chains)]
        besti, b_score, b_type = max(scores, key = lambda x: x[1])
        
        chains[besti][0].append(vd)     #add to chain
        chains[besti][1].append(b_type) #add to types

    return (events,chains)
    

def grow_list(A, verbs, schema_to_string = pprint):
    """Build narrative schema by adding verbs one at a time.
    (original C&J 2009 technique)

        A = lots of annoying little args
        verbs = candidate verbs to add to schema
    """
    beta = A["beta"]
    MAX_SIZE = A["max_schema_size"]

    depsets = A["depset"]
    complete_schemata = []
    
    schemata = schema_init([verbs[0]], depsets)
    verbs = verbs[1:]
    def new_schema(v):
        schemata.extend(schema_init([v], depsets))

    for verb in verbs:
        precomp =[(A["hyperscore"](A, N, verb, score=A["score"]), N, i) 
                        for i,N in enumerate(schemata)]
        
        if not precomp:
            new_schema(verb)
            continue
        
        score, N, i = max(precomp)
        
        if score <= len(depsets[verb])*beta:
            print "No fit for ",verb
            new_schema(verb)
        else:
            print "Best fit for",verb
            print schema_to_string(N)
            print score
            print


            schemata[i] = ct_2.schema_insert(A, N, (verb, depsets[verb]), 
                                             score=A["score"])

        if len(schemata[i][0]) >= MAX_SIZE: 
            complete_schemata.append(schemata[i])
            schemata.remove(schemata[i])
        
        print "Verb:", verb
        print "Current number of schemas:",len(schemata)
        print "Complete schemas:", len(complete_schemata)
        print 

    complete_schemata.extend(schemata) # leftovers?
    return complete_schemata

#idk why this is here
dep_invert = {"SUBJ": "OBJ", "OBJ": "SUBJ", "PREP": "SUBJ"}


#I put this here, but I'm not sure why it's here.
def realize_links(links):
    """
    Make this:
        [(a,b), (b,c), (d,c), (f,g), (g,h)]
    Into this:
        [a,b,c,d]
        [f,g,h]
    """
    #build a local graph of nodes
    universe = sorted(set(sum([list(x) for x in links],[])))
    linked = lambda x,y: (x,y) in links or (y,x) in links
    graph = {x:[y for y in universe if linked(x,y)] for x in universe}
    
    output_lists = []
    while graph:
        next_node = list(graph)[0]
        new_list = []
        buffer = [next_node]
        while buffer:
            #exploit information from next buffer
            if buffer[0] in graph:
                buffer.extend(graph[buffer[0]])
                del graph[buffer[0]]
                
                #save current node and move
                new_list.append(buffer[0])
            del buffer[0]

        output_lists.append(new_list)
    
    return output_lists
    

def exhaustive_roles(A, schemas, score = scoring.score09):
    """
    Overwrite the roles given at insertion; instead, provide all non-zero
    scored role fillers.
    """
    print "Computing complete role assignment lists."
    new_schemas = []
    for i,schema in enumerate(schemas):
        print i,"/",len(schemas),"schemas"
        events, chains = schema
        new_chains = []
        for chain in chains:
            slots, old_roles = chain
            actual_types = set(sum([A["types"][vd]\
                            for vd in slots if vd in A["types"]],[]))
            new_roles = []
            for a in actual_types: #A["types"]:
                a_score = score(A, slots, a)
                #print a, a_score
                if a_score > 0.0: new_roles.append((a,copy(a_score)))
            
            #originally produced shitton of roles, lots of one-hitters
            #that's sorta boring, so I'm filtering out roles not just that are
            #less than zero, but also greater than the minimum value
            if new_roles:
                cutoff = min([s for r,s in new_roles])
                new_roles = [(r,s) for r,s in new_roles if s > cutoff]

            new_chains.append((slots, new_roles))
        new_schemas.append((events, new_chains))
    return new_schemas




