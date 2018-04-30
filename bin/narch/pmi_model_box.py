from generate import scoring, cj2009, ct_2


class PMI_Model:
    """
    Not really proper OOP. The goal here is to roll everything into an object
    so it can be passed to the next script. 

    Most everything is just sandwiched into self.args

    Had to break this into a separate file because the variable scope 
    was all fucked up sandwiching this in the prior script, and I didn't want
    to run around renaming everything.
    """
    def __init__(self, new_args):
        #inject all this crap into self
        vars(self).update(new_args.items())

        # Seeding Related Lists #
        c_counts = self.ftr_c_counts.items()
        c_counts.sort(key=lambda x: -x[1])
        
        
        self.local_verb_totals = self.ftr_total_v_counts
        self.total_verb_counts = sum(self.local_verb_totals.values())
        # P(v|feature_tuple), basically
        self.prob_v_giv_ftt = {v: float(self.local_verb_totals[v])/self.total_verb_counts 
                                for v in self.local_verb_totals}
        
        self.most_frequent_verbs = [v for v,c in 
                                        sorted(self.local_verb_totals.items(), 
                                            key = lambda x: -x[1])]
        
        #
        # THESE ARE NOT CLASS METHODS
        #   They are functions, defined and intended to be passed as data 
        #   to the schema generation algorithm of interest.
        #
        #   The whole point of this class is to retain a bunch of data and 
        #   structures and pointers and code associated. It's a box, not a 
        #   functional entity. 
        #

        def make_schema_seeder(args):
            depsets = args["depset"]
            for v in self.most_frequent_verbs[:self.number_of_schemas]:
                yield cj2009.schema_init([v], depsets)[0]
        
        # Verb Loading Crap Doodle #
        #This was an optimization originally, I believe.
        self.verbs = list(self.Depsets)
        

        # Wrap Inducter #
        # -- the procedure for adding a candidate to a schema
        def inducter(args,N,v): 
            return ct_2.schema_insert(args, N,(v, self.Depsets[v]))



        # Wrap Similiarty Measure #

        def sim_measure(args, schema, verb):
            return cj2009.narsim(args, schema, verb)
        
        # Set Terminator #
        def set_terminator(schemas):
            #return len(schemas) >= 200
            return False #terminate on exhausted seeder

        # Schema Terminator #
        #def schema_terminator(S, scores = []):
        #    return len(S[0]) > self.max_schema_size
        def schema_terminator(S, scores=None):
            if scores is None: pass
            elif not scores: return True
            elif all([s <= 0.0 for s in  scores.values()]): return True
            return len(S[0]) >= self.max_schema_size


        self.args = {"lambda": self.Lambda,
                "p": self.Prob,
                "pj": self.Prob_joint,
                "all_vd_pairs": set(self.ftr_cj_counts),
                "freq": self.Freq,
                "llf": self.LLF,
                "types": self.Types,
                "feature_tuple": self.feature_tuple,
                "depset": self.Depsets,
                "max_schema_size": self.max_schema_size,
                "number_of_schemas": self.number_of_schemas,
                "beta": self.Beta,
                "hyperscore": cj2009.narsim, #might need deepcopy on this
                "score": scoring.chainsim_prime, #deepcopy?
                "period": self.feature_tuple, #holdover
                "candidates": self.verbs,
                "make_seeder": make_schema_seeder,
                "sim_measure": sim_measure,
                "set_terminator": set_terminator,
                "schema_terminator": schema_terminator,
                "inducter": inducter,
                "weight_pipe": lambda w: 2**w,
                }
