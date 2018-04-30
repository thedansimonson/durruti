"""
Generate narrative schemas based on PMI. Closely related Chambers and 
Jurafsky (2009)'s approach to schema generation. 

Schema are represented by a dictionary such that:
    {"events": [(verb, dependency options), ... ]
     "chains": [(verbdep list, types), ... ]}

"""
import scoring
from pprint import pprint
from datetime import datetime


def countertrain(schemas, inducter, schema_terminator, 
                    sim, 
                candidates, candidate_pruner):
    """
    Generate schemas with a countertraining-style generation process.

    Args:
        schemas
    """
    complete_schemas = []
    while candidates and schemas:
        
        print "\nCountertraining: Start iteration."
        
        # Produce Similarities #
        scoretime = datetime.now()
        simtables = []
        for schema in schemas:
            simtables.append({can: sim(schema, can) for can in candidates})
        print "Scoretime:",(datetime.now()-scoretime).total_seconds()
        
        # Produce Broadnesses #
        # Why broadness, as opposed to number of selections? Broadness 
        # it disposes of less useful information incorporates near 
        # selections, making it more stable.
        broadtable = {can: 0.0 for can in candidates}
        for schema, simscores in zip(schemas,simtables):
            for can in set(simscores):
                broadtable[can] += simscores[can]
        BT = {can: broadtable[can]/len(schemas) for can in candidates}
        
        # Adjust Scores Based on Broadnesses #
        finals = [{can: sco[can] - BT[can] for can in candidates}\
                                           for sco in simtables]
        
        #pprint(zip(schemas,finals))
        #print "~~~~~~~~~~#ROUND#~~~~~~~~~~\n\n\n"
        
        # Prune Candidates as Prescribed #
        cantable = []
        for schema, final in zip(schemas, finals):
            cantable.append(candidate_pruner(schema, candidates, final))
        
        finals = [{w: s for w,s in f.items() if w in cans} \
                        for f,cans in zip(finals,cantable)]
        
        # Move Toward Termination Conditions #
        #graduate schemas
        complete_indices = []
        for i,(schema,final) in enumerate(zip(schemas,finals)):
            if schema_terminator(schema, final):
                complete_indices.append(i)
        complete_indices.sort(key = lambda x: -x) #protects ordering 

        for i in complete_indices:
            complete_schemas.append(schemas[i]) #prepare for export
            del schemas[i]  # remove from training
            del finals[i]   # also needs to be removed
            del cantable[i] # this too probably

        # Grow Remaining Schemas #
        new_schemas = []
        for schema, final, cans in zip(schemas, finals, cantable):
            inductee,score = max(final.items(), key=lambda x: x[1])
            new_schemas.append(inducter(schema, inductee))
        schemas = new_schemas
    
    return complete_schemas



            
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
    
    # Add the Event to the Event Portion of the Schema Tuple #
    events, chains = N
    events.append(new_event)
    

    # Add Thematic Roles to the Events #
    verb, depset = new_event
    verbdeps = [(verb, d) for d in depset]
    
    scorepile = [] #all scores are gathered here, 
                   #prevents a self-referential chain like D dress D, etc.

    for vd in verbdeps:
        scores = [(i,score(A,c,vd))for i,(c,types) in enumerate(chains)]
        scores = [(vd,i,s,t) for i,(s,t) in scores]
        scorepile.extend(scores)
    
    scorepile.sort(key=lambda x: -x[2])
    """
    print "INSERTION IN PROGRESS"
    print "schema"
    pprint(N)
    print "event"
    pprint(new_event)
    print "\nscorepile"
    pprint(scorepile)
    print
    print
    #"""

    while scorepile:
        next_addition = scorepile[0]
        scorepile = scorepile[1:]
        verbdep, besti, b_score, b_type = next_addition 
        
        # If there is no best role filler, we create a new chain in the 
        # schema.
        if b_score > len(chains[besti])*beta:
            chains[besti][0].append(verbdep)     #add to chain
            chains[besti][1].append(b_type) #add to types

            scorepile = [(vd,i,s,t) for vd,i,s,t in scorepile if i != besti]

        else:
            chains.append(([verbdep], []))
        
        #remove all scores related to verbdep
        scorepile = [(vd,i,s,t) for vd,i,s,t in scorepile if vd != verbdep]

    return (events,chains)





            
        
