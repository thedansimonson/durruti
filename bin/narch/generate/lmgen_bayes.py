"""
Language Model GENerative: Bayesian

A very similar method to C&J 2009, but Bayesian and generative, thereby 
yielding (presumably) different results. 

"""

def P_v_giv_S(args, S, v):
    """probability of an event given a schema S

    This is broken because the computer is impossible.
    """
    print "S",S
    print "v",v
    events, chains = S
    
    slotsubs = []
    for vd in [(v,d) for d in args["depset"][v]]:
        chainsubs = []
        for chain in chains:
            #compute c in C_s
            P_c = args["P(c)"](chain)
            P_r = args["p"](vd)
            P_cr = P_c_giv_v(args, chain,vd)
            chainsubs.append(P_cr*P_r/P(c))
        slotsubs.append(max(chainsubs))
    
    print v,":",S
    score = reduce(lambda x,y: x*y, slotsubs)
    print score
    print

    return score



def P_c_giv_v(args, chain, vd):
    "probability of verbdep pair given a chain"
    lmb = args["lambda"]
    counts = args["counts"]
    counts_joint = args["counts_joint"]
    freq = args["freq"]
    types = lambda x: args["types"][x] if x in args["types"] else []

    deno = float(len(chain) * counts((vd,)) * (1.0+lmb)**2)
    if deno <= 0.0: return (0.0, None)
    numo = 0.0
    for we in chain:
        cap   = tuple(sorted([we,vd]))
        numo += counts_joint(cap)

        typescans  = set(types(vd)) & set(types(we))

        typescores = [freq((cap,a)) for a in typescans]
        if not typescores: typemaxscore, typemax = 0.0, None
        else: typemaxscore, typemax = max(zip(typescores,typescans))
        numo += lmb*typemaxscore

    score = numo/deno
    return (score,typemax)




