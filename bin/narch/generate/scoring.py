"""
Formulae and scores for the generation of narrative schemas. 
"""
from math import log
from copy import deepcopy, copy
import ft
import sys
from pprint import pprint
from datetime import datetime
import gc

sys.setrecursionlimit(2000)

def time_start(note):
    return (note, datetime.now())

def time_dump_stop(start):
    "Logs the time on stdout (for optimization)"
    note, beginning = start
    end = datetime.now()
    print note,": ", (end-beginning).total_seconds()
    return True

def pmi(p, pj, wd_pair):
    "Compute pmi for wd_pair."
    a, b = wd_pair
    a, b = (a,), (b,) #generalizes P(args)
    
    numo = pj(wd_pair)
    deno = p(a)*p(b)

    #I could do some L'Hopital's rule thing to argue this
    if deno*numo == 0.0: return 0.0 
    return log(numo/deno, 2)

def discount(c, cj, wd_pair):
    "The discount score from Pantel and Ravichandran (2004)"
    a, b = wd_pair
    a, b = (a,), (b,) #generalizes P(args)

    minibit = min(c(a), c(b))
    
    terms_zeroth = float(cj(wd_pair))/(cj(wd_pair) + 1)
    terms_first  = float(minibit)/(minibit+1)

    return terms_zeroth * terms_first


#####################################
# VERB -> CHAIN SIMILARITY MEASURES #
#####################################

def disp(stuff):
    print stuff
    return stuff

norm = lambda *args: tuple(sorted(list(args)))
norml = lambda arg: norm(*arg)

def pmi_similarity(chain, P, Pj, C, Cj):
    """Computes the similarity between each v in C and all members of chain.
    C&J 2009 call this "chainsim"
    """
    verbdeps = list(C)
    scores = {}
    for verbdep in verbdeps:
        verbdep, = verbdep #norm repackages the tuple
        if verbdep not in chain:
            score = sum([pmi(P,Pj,norm(verbdep,e)) for e in chain])
        else:
            score = 0.0

        if score > 0.0: 
            scores[verbdep] = score

    return scores

# C&J 2009 Stuff #

args_sample = {"lambda": 1.0,
               "p": lambda vd: 0.01,
               "pj": lambda vd: 0.01,
               "freq": {},
               "types": ["PERSON", "ORGANIZATION"]}


def chainsim_prime_slow(A, C, vdpair):
    """
    A = args--contextually dependent functions, etc.
    C = subject chain
    vdpair = candidate vdpair to add to C
    From C&J 2009
    """
    types = A["types"]

    v = vdpair
    sim_inside = lambda t: score09(A,C,t) + sum([sim09(A,(c,v),t) for c in C])

    return max([(sim_inside(t), t) for t in types], key=lambda x:x[0])
    
def score09(args, chain, a):
    score = 0.0
    chain = sorted(list(chain))
    #print
    #print chain
    for i,x in enumerate(chain):
        for j,y in enumerate(chain[i+1:]):
            score += sim09(args, (x,y), a)
    return score

#NLP log(0) = 0
lolog = lambda x: log(x,2) if x else -1.0

# "fuck" is there to protect scope. this has to do with python's variable scope
# etc. Admittedly, the "right" python way to do this at this point would be
# to instantiate a class, but I don't have time for that crap.
pmi_cache_hole = {"fuck":{}}
def sim09(args, com_pair, a):
    period = args["period"]
    # allows purgability
    pmi_cache = pmi_cache_hole["fuck"]

    #DISCOUNT SCORE?
    
    if (period, com_pair) in pmi_cache:
        oops_bad_naming = pmi_cache[(period,com_pair)]
    else:
        p = args["p"]
        pj = args["pj"]
        oops_bad_naming = pmi(p,pj,com_pair)
        pmi_cache[(period,com_pair)] = oops_bad_naming
    
    lmb = args["lambda"]
    freq = args["freq"]
    x,y = com_pair
    freq_arg = ((x,y),a)
    freq_component = lmb*lolog(freq(freq_arg))
    outcrap = oops_bad_naming + freq_component 
    #print com_pair, a
    #print "PMI:", oops_bad_naming
    #print "freq_arg:", freq_arg
    #print "freq_component:", freq_component
    #print outcrap
    return outcrap 


#########################################
# Much faster version of C&J 2009 Stuff #
#########################################

def fancy_types(freq):
    """
    I've had it with this slow chain similarity computation. 
    This should eliminate a lot of un-necessary calculations.
    """
    crap = {}
    for verbdeps, t in freq:
        for vd in verbdeps:
            if vd in crap:  crap[vd].append(t)
            else:           crap[vd] = [t]
    return crap


def trisum(f,L):
    """
    Gets the triangular sum of L -> f(L).
    """
    #chain = sorted(list(chain))
    score = 0.0
    for i,x in enumerate(L):
        for j,y in enumerate(L[i+1:]):
            score += f(x,y)
    return score

# see pmi_cache_hole for explanation of this weirdness
phi_Delta_cache_hole = {"fuck":{}}

def chainsim_prime(A, C, vdpair):
    """
    A = args--contextually dependent functions, etc.
    C = subject chain
    vdpair = candidate vdpair to add to C
    
    Optimized -- originally from C&J 2009, interpreted with modifications
    """

    types = A["types"]     #for event chain construction
    period = A["period"]
    p = A["p"]
    pj = A["pj"]
    llf = A["llf"]
    phi_Delta_cache = phi_Delta_cache_hole["fuck"]

    if period not in phi_Delta_cache: phi_Delta_cache[period] = {}

    v = vdpair
    Q = sorted(list(C)) # the "Quick" version of C
    Qt = tuple(Q)


    pi =        sum([pmi(p,pj, (y,vdpair)) for y in Q])
    pi_Delta = 0.0 #relevant? YOU DECIDE
    #pi_Delta =  trisum(lambda x,y: pmi(p,pj, (x,y)), Q)


    #Q_sub is an optimization
    Q_sub = [tuple(sorted([vdpair,y])) for y in Q]
    Q_sub = [vy for vy in Q_sub if pj(vy) > 0.0]


    #determine the types to be searched
    #compat mode-> #if dict(types) is types else types:
    if vdpair not in types: search_types = ["NULL"]
    else: search_types = set(types[vdpair])


    maximizing = []
    for a in search_types: 
        phi = sum([llf((vy,a)) for vy in Q_sub])

        phi_Delta = 0.0
        # DOUBLE CHECK Qt IS ACTUALLY LOOKING UP THINGS THE WAY IT SHOULD
        if (Qt,a) in phi_Delta_cache: 
            phi_Delta = phi_Delta_cache[period][(Qt,a)]
        else:
            phi_Delta = trisum(lambda x,y: llf((tuple(sorted([x,y])), a)), Q)
            phi_Delta_cache[period][(Qt,a)] = phi_Delta

        maximizing.append(phi+phi_Delta)

    
    scores_types = zip(maximizing, search_types)
    maxscore, maxtype = max(scores_types)
    return (pi + pi_Delta + maxscore, maxtype)


def purge_pmi_cache():
    """
    The pmi_cache gets too bloated on longer runs, especially running against
    a number of different 'periods.' Also purges phi_delta_cache
    
    This cleans out the pmi_cache when ready. Good, especially if you're done
    with a specific period.
    """
    # Saving reference to apply "del"

    del pmi_cache_hole["fuck"]
    del phi_Delta_cache_hole["fuck"]
    gc.collect()

    pmi_cache_hole["fuck"] = {}
    phi_Delta_cache_hole["fuck"] = {}

    # optional todo: 
    # gc.collect() #trigger garbage collection.
