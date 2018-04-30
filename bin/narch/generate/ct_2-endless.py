"""
Generate narrative schemas based on PMI. Closely related Chambers and 
Jurafsky (2009)'s approach to schema generation. 

Schema are represented by a dictionary such that:
    {"events": [(verb, dependency options), ... ]
     "chains": [(verbdep list, types), ... ]}

"""
import scoring
from pprint import pprint

def countertrain(schemas, inducter, sim, candidates):
    """
    Generate schemas with a countertraining-style generation process.

    Args:
        seeds = seeds for schemas in training process
        P = probability function: one arg, verb tuple
        Pj = joint probability function: one arg, verb tuple
    """

    while candidates:

        # Produce Similarities #
        simtables = []
        for schema in schemas:
            simtables.append({can: sim(schema, can) for can in candidates})
        
        # Produce Broadnesses #
        # Why broadness, as opposed to number of selections? Broadness 
        # it disposes of less useful information incorporates near 
        # selections, making it more stable.
        broadtable = {can: 0.0 for can in candidates}
        for schema, simscores in zip(schemas,simtables):
            for can in simscores:
                broadtable[can] += simscores[can]
        BT = {can: broadtable[can]/len(schemas) for can in candidates}
        
        # Adjust Scores Based on Broadnesses #
        finals = [{can: sco[can] - BT[can] for can in candidates}\
                                           for sco in simtables]
        
        pprint(zip(schemas,finals))
        print "~~~~~~~~~~#ROUND#~~~~~~~~~~\n\n\n"

        # Induce New Schemas #
        new_schemas = []
        for schema, final in zip(schemas, finals):
            inductee,score = max(final.items(), key=lambda x: x[1])
            new_schemas.append(inducter(schema, inductee))
        schemas = new_schemas
        
        # Move Toward Termination Conditions #
        
        #trim the candidate list
        healthy = {can: any([S[can] > 0.0 for S in finals]) for can in candidates}
        candidates = [can for can,ok in healthy.items() if ok]
                

    return schemas
            





            
        
