"""
Use a random walk algorithm to generate schemas pseudorandomly.
"""
import random
from datetime import datetime
from copy import copy
from pprint import pprint

random.seed(19800518)

def weighted_choice(options, weights):
    """
    Select an option from options at random based on the weights given.
    options: list of options
    weights: list of weights associated with options
    """
    thresh = sum(weights)*random.random()
    eax = 0.0
    for option, weight in zip(options,weights):
        eax += weight
        if eax > thresh: return option
    raise Exception("Weighted choice failed to cross thresh.")



def create_schema(args, schema):
    """
    args: dictionary containing all args. necessary args include:
        "sim": similarity score
        "inducter": 
        "schema_terminator": when do we stop
    schema: fully-fledged seed (in schema form) generated by the seeder
    """
    terminate = args["schema_terminator"]
    inducter = args["inducter"]
    sim = args["sim_measure"]
    candidates = copy(args["candidates"])
    wipe = args["weight_pipe"]

    while not terminate(schema):
        
        #compute all similarities.
        #print schema
        can_scores = {c: wipe(sim(args, schema, c)) for c in candidates}
        

        #prepare prob dist and select random event
        can_total = sum(can_scores.values(),0.0)
        new_event = weighted_choice(*zip(*can_scores.items()))
        candidates.remove(new_event)
        
        # add to schema
        schema = inducter(args, schema, new_event)
    
    
    return schema


def create_schemas(args):
    """
    args: dictionary containing all args. necessary args include:
        "inducter": procedure for adding a newly discovered event to a schema
        "make_seeder": generator that produces seeds
        "schema_terminator": func--when a schema is finished
        "sim": similarity score
        "set_terminator": func--when to stop generating schemas
    """

    schemas = []
    terminate = args["set_terminator"]
    seeder = args["make_seeder"](args)
    while not terminate(schemas):
        try:
            seed = seeder.next()
        except StopIteration:
            print "Seeder exhausted. Terminating schema generation."
            break
        print "Generating schema..."
        scoretime = datetime.now()
        schema = create_schema(args, seed)
        print "Newest schema:", schema
        print "Schema gen (seconds):",(datetime.now()-scoretime).total_seconds()
        print "Schemas so far:",len(schemas)
        print 
        schemas.append(schema)
    return schemas
