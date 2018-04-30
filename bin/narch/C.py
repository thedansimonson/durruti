"""
C Approximation

Not the language--C indicates counts in C&J08/09.

For example,
    C(e(search, ag)) indicates the number of times search, with an associated
    agent, appear in a document.
OR
    C(e(search, ag), e(arrest, pat)) indicates the number of times "search" and 
    "arrest" both appear with the same coreferring entity as "ag" and "pat."

PMI is defined in terms of C. 
"""
import ft
from itertools import combinations
from string import whitespace
from pprint import pprint

# ARG CLEAN-UP STUFF #

# words
def relevant_verbs(word):
    """
    a built-in condition for relevant words: returns True if word is a verb.

    Words come in the form, from CoreNLPpython
    [raw, {bunch of metadata: values...}]
    """
    raw_word, word_data = word
    return True if word_data["PartOfSpeech"][:2] == "VB" else False

def sentential_relevant_words(words, condition):
    """
    Identify words (indices, really) from a sentence that are relevant.
    e.g. that they meet condition
    """
    relevant = [(i,w) for i,w in enumerate(words) if condition(w)]
    return relevant

def relevant_words(sentences, condition, lemmatize = True):
    """
    Identify words (indices, really) from a document that are relevant.
    e.g. that they meet condition
    """
    doc_relevant = []
    for i, sentence in enumerate(sentences):
        relevant = sentential_relevant_words(sentence["words"], condition)
        relevant = [(i, j, w) for j,w in relevant]
        if lemmatize:
            lemma = lambda j: sentence["words"][j][1]["Lemma"]
            relevant = [(i,j,lemma(j)) for i,j,w in relevant]
        doc_relevant.extend(relevant)
    return doc_relevant

def agglodep(word, raw_deps, agglotag = u"prt"):
    """
    Attaches the token at the end of the dependency relationship "agglotag" to
    word. I hope you've lemmatized.
    """
    #index of sentence, index of word in sentence, lemma
    w_s, w_i, lemma = word

    rel_deps = [I for I,(d, (s,i,v), (t,j,u)) in enumerate(raw_deps) 
                                                        if d == agglotag and
                                                           s == w_s and
                                                           i == w_i]
    if not rel_deps: return word
    else: return (w_s, w_i, "_".join([lemma]+
            [u for d, (s,i,v), (t,j,u) in [raw_deps[i] for i in rel_deps]]))

################
# dependencies #
################

def make_dep_sane(x): 
    "THIS WAS A LAMBDA BUT PYTHON LAMBDA IS SHIT LAMBDA"
    #this is weird, but you can blame their shitty conventions
    #this was just:
    #w,i = x.split("-")
    #46-year-old-11 broke the simple version
    #who uses word characters as index separators
    #fucking asshole

    crap = x.split("-")
    i = crap[-1]
    w = "-".join(crap[:-1])

    return (int(i)-1,w)

def dep_norm(sent_i, dep):
    """
    Indexed dependencies are returned in a stupid format.
    ["relation", "word_a-i+1", "word_b-i+1"]
    I shit you not. They give the index of the word after the word. No clue
    why someone in their right mind would return the words that way, but
    this fixes that, and splits stuff up, turns it into a dictionary.

    Ok, maybe I have a bit of a clue. The ROOT of the sentence is 0, not
    -1, offsetting all the words by 1. Still stupid.
    """
    rel, a, b = dep
    a,b = [(sent_i,i,w) for i,w in [make_dep_sane(x) for x in [a,b]]]
    return (rel, a, b)

def dep_collapse(deps, coll_table):
    "Collapses dependencies."
    eax = []
    for d,a,b in deps:
        d = d.split("_")[0]
        if d in coll_table: 
            d = coll_table[d]
        else:
            #print d, "not in collapse table. taking default behavior"
            d = coll_table["_DEFAULT"]
        
        if d != "null": eax.append((d,a,b))

    return eax


def load_dep_collapse(fstream):
    raw = [r.strip(whitespace) for r in fstream.read().split("\n") if r]
    table = []
    for row in raw:
         table.append(tuple([e.strip(whitespace) for e in row.split(":")]))

    return dict(table)


#########
# coref #
#########

def descend_dependencies(indexed_words, dependencies):
    """
    A second technique for retrieving the head of an XP.

    climb_dependencies almost does what I want it to. But not really.
    There's a lot of problems with genitives and proper nouns. 

    So, this does two things, in this order:
        (1) Removes dependencies inside the XP indexed_words
        (2) Removes dependencies that don't point to the XP.
    We should be left with one dependency, if all goes well. 

    """
    indices = [(sent, i) for sent,i, w in indexed_words]
    OK = lambda r: r[:2] in indices

    #Keep only dependencies that are XP_external
    #(There's a better word for this from posets but I can't find the damn
    # word.)
    XP_external = lambda d: OK(d[2])
    deps = [d for d in dependencies if XP_external(d)]

    #Remove XP_internal dependencies
    XP_internal = lambda d: OK(d[1])
    deps = [d for d in deps if not XP_internal(d)]

    
    #We better have one damn word left

    return deps

def climb_dependencies(indexed_words, dependencies):
    """
    A first technique for retrieving the head of an NP.

    Moves between indexed_words via dependencies until only one 
    indexed word remains to find the ROOT word or HEAD.

    Assumes that it's a tree. If it's not a tree, it will fail. (Recursion 
    depth)
    """
    #to start off easy, if there's one word, we know it's the root
    if len(indexed_words) == 1: return indexed_words[0]

    #remove dependencies not amongst indexed_words; they're irrelevant
    indices = [(sent, i) for sent,i, w in indexed_words]
    OK = lambda r: r[:2] in indices
    deps = [(rel, a, b) for rel,a,b in dependencies if OK(a) and OK(b)]
    recover = lambda i: indexed_words[indices.index(i)]

    #print indices

    #invert the dependencies, and remove the attached word strings
    inverse_dep = {b[:2]: a[:2] for rel,a,b in deps}
    """
    #full recursive hill-climb mode
    climber = lambda word: inverse_dep[word] if word in inverse_dep else word
    root = iterate_climb(indices, climber)
    if root == -1: 
        pprint(indexed_words)
        pprint(dependencies)
        raise Exception("EXPLOSION IN CLIMB_DEPENDENCIES. PANIC.")
    return indexed_words[indices.index(root)]
    """

    #awesome clever mode
    b,a = inverse_dep.keys(), inverse_dep.values()
    #print b
    #print a
    b = set(b)
    roots = list(set([node for node in a if node not in b]))
    #print "climb!", roots
    if len(roots) == 1: return recover(roots[0])
    else:
        #I had a fall back here where I sought the head with a top down
        #approach. After looking at the outputs, though, it seems these 
        #else cases are best thrown away. In this application, they are
        # poss, nn, amod, dep
        #stuff that, upon further inspection, aren't relevant here.

        #an example:
        #[(21, 17), (21, 18)]
        #[(u'nn', (21, 21, u'wave'), (21, 17, u'New')), 
        # (u'nn', (21, 21, u'wave'), (21, 18, u'York'))]
        #The coreference here is "New York," not "wave," so ascending
        #to "wave" is stupid.

        #print "words", indexed_words
        #print "deps", dependencies
        #raise Exception("WHAT")
        #print "descend!", descend_dependencies(indexed_words, dependencies)
        #raw_input("Acknowledge this nonsense")
        return False


def iterate_climb(words,climber):
    "Old recursive hill-climb for climb dependencies. Cute, but stupid."
    print words
    words = list(set(map(climber, words)))
    if len(words) == 1: return words[0]

    try:
        return iterate_climb(words, climber)
    except:
        return -1


def coref_flatten(chain, deps):
    """Flattens a single coref chain
    
    They come in a weird format. An example:
    [[[u'Two other precinct officers', 10, 3, 0, 4],
      [u'Lieut. Joseph McGrann', 10, 7, 5, 8]],
     [[u'Lieut. Joseph McGrann and Officer Charles Davis',10,7,5,12],
      [u'Lieut. Joseph McGrann', 10, 7, 5, 8]],
     [[u'Joseph McGrann', 10, 7, 6, 8],
      [u'Lieut. Joseph McGrann', 10, 7, 5, 8]],
     [[u'him', 10, 4, 14, 15],
      [u'Lieut. Joseph McGrann', 10, 7, 5, 8]]]

    Originally, in coref_flatten_old, I tried extracting ANY dependency with 
    ANY token in the coreference chain, but this has a bunch of problems, the
    biggest being that it grabs dependencies inside the phrase. This is a 
    bad example of that, but anything with a relative clause really threw a 
    monkey wrench in the mix.

    Instead, I'm grabbing the head of each member of the chain, then
    turning that into the tuple. To do this, I'm traversing up the 
    dependencies between members of each hoop until there's no more
    traversing to do.
    """

    top = []
    for link in chain: 
        new_link = []
        for hoop in link:
            words, sent, wtf_is_this, start, stop = hoop
            
            indexed_words = [(sent,i,words) for i in range(start,stop)]
            head = climb_dependencies(indexed_words, deps)
            
            if head: new_link.append(head)
        
        top.extend(new_link)
    return list(set(top))

def coref_flatten_old(chain):
    """
    THIS METHOD IS STUPID AND DOESN'T WORK DUE TO EXTREMELY LONG DPs
    Flattens a single coref chain
    
    They come in a weird format. An example:
    [
        [[u'civil defense recruits', 5, 5, 13, 16], 
         [u'civil defense recruits', 0, 6, 74, 77]],
        [[u'civil defense recruits', 6, 3, 21, 24], 
         [u'civil defense recruits', 0, 6, 74, 77]]
    ]
    Note the redundancy. This takes the redundant central, singletonizes it,
    effectively flattening the whole set.

    I've also adopted this convention of frontloading coordinates. It's a good
    idea from a design standpoint, but bad from a "being harmonious with the
    thing giving me data" standpoint.

    Actually, I know why I adopted it--because enumerate() does it that way.
    Typical. CoreNLPPython is so apythonic.

    The output will be like this:

    [
        (0, 74, u'civil defense recruits'),
        (0, 75, u'civil defense recruits'),
        (0, 76, u'civil defense recruits'),

        (5, 13, u'civil defense recruits'),
        (5, 14, u'civil defense recruits'),
        (5, 15, u'civil defense recruits'),

        
        (6, 21, u'civil defense recruits'),
        (6, 22, u'civil defense recruits'),
        (6, 23, u'civil defense recruits'),
    ]
    
    Looks stupid, but I have my reasons. The internal structure of the DP/NP
    is not required. It only needs to know what indices are referred to by
    the indexeddependencies. All other structure is extraneous. We're turning
    a salad into V8 because I don't have a fork.

    """

    top = []
    for link in chain: 
        new_link = []
        for hoop in link:
            words, sent, wtf_is_this, start, stop = hoop
            #notice that no filtering takes place here--I don't grab the head
            #of the phrase or anything like that. this is intentional.
            #the filtering occurs implictly via the verb--the dependency
            #between the verb and the head should be captured, and any
            #extraneous stuff left out.

            #In other words, imagine the DP/NP is being shoved into a blender.
            #what was once a salad is now V8. It loses its internal structure,
            #but represents a consistent whole across the document.
            #For our purposes, this should work. 
            new_link.extend([(sent,i,words) for i in range(start,stop)])
        
        top.extend(new_link)
    return list(set(top))

################
# chain typing #
################
# Determines chain-typing like in Chambers and Jurafsky 2009

def get_cnlp(coref, sentences):
    """
    CoreNLP results for coreference chain coref.
    """
    cnlps = []
    for word in coref:
        i, j, word_string = word
        cnlp = sentences[i]["words"][j][1]
        cnlps.append(cnlp)
    return cnlps

person_lemmas = {"he", "him", 
             "she", "her", 
             "you", "yourself", "yourselves",
             "yours","your",
             "himself","herself","themselves",
             "who", "whom",
             "Mr.", "Mrs.", #why not?
             }

people_lemmas = {"they","them","themselves"}

self_lemmas = {"our", "ours", "ourselves",
               "I","me","we","us","my","mine",}

thing_lemmas = {"it", "its", "itself", "this", "that", "those"}

pn_lemmas = person_lemmas | people_lemmas | self_lemmas | thing_lemmas

pronoun_groups = {"PERSON": person_lemmas,
                  "PEOPLE": people_lemmas,
                  "SELF":   self_lemmas,
                  "THING":  thing_lemmas}

TYPE_ERROR = "TYPE_ERROR"

def singlitate(mset):
    "I just made a word up! Reduces mset if unambiguous, False otherwise"
    if len(mset) == 1:
        mset = mset[0][0]
    else:
        mset = False
    return mset
    
HN_counter = {}

def coref_kinda_flat(chain):
    """
    A rehash of coref_flatten_old--the algorithm was mostly what I needed for
    chain typing, so I took it. 
    """

    #some preliminary flattening
    anchor = "scope this!"
    temp_chain = []
    for link in chain: 
        hoop, anchor = link
        temp_chain.append(hoop)
    temp_chain.append(anchor)
    
    #expansion
    top = []
    for hoop in temp_chain:
        words, sent, wtf_is_this, start, stop = hoop
        new_link = [(sent,i,words) for i in range(start,stop)]
        top.append(new_link)
    
    return top 

def get_head_space(coref, sentences, whole_dps):
    """
    I'm calling the "head space" of a DP the space > its determiner and <= its
    head. Why? Keywords that play major role in the defining the entity are 
    likely to be found here. That comes into play in determining a coref type
    for a coref chain.

    DET > [A, NN]* <= NN

    Examples:
        the [suave detective] who caught the bad guy
        the police department's [Doctor Steve Brule]
        [Mayor Giuliani]
    """
    #create a table to lookup whole-dp
    wdp_lookup = {}
    for d, dp in enumerate(whole_dps):
        wdp_lookup.update([((sent,i), d) for sent,i,raw in dp])
    
    #extraction step
    head_spaces = []
    for head_link in coref:
        sent,i,raw = head_link
        if (sent,i) in wdp_lookup:
            dp_coords = whole_dps[wdp_lookup[(sent,i)]]
        else:
            print "wtf"
        
        h_coords = [(tent,j,w) for tent,j,w in dp_coords \
                                if j <= i and sent==tent]

        head_space = zip(h_coords, get_cnlp(h_coords, sentences))
        head_space = [(uent,j,cnlp) for (uent,j,w),cnlp in head_space]

        hs_pos = [w["PartOfSpeech"] for s,j,w in head_space]
        start = 0 if "DT" not in hs_pos else hs_pos.index("DT")+1
        head_space = head_space[start:]
        
        head_spaces.append(head_space)

    return head_spaces



def coref_type(coref_bundle, sentences, pref_types = False):
    """
    Determines the argument filler type as per Chambers and Jurafsky 2009, with
    some variants.

    (0) If possible, it prefers spec_types. It looks for these, left of the 
        head nouns in each DP. If 
    (1) Next, it tries the named entity recognizer for unambiguous results.
    (2) Next, it uses the single most frequent non-pronominal lemma.
    (3) Next, it uses the pronouns to make a last ditch choice.
    (4) In a last ditch effort, it chooses the shortest head noun in the 
        coreference chain.
    (5) At this point, it concludes there's no valid type.

    Args:
        coref = a flattened coreference chain
        sentences = the CoreNLP output "sentences"
        pref_types = default False, 
                     if specified, a tuple
                     (target_words, whole_dps)
                     where
                        target_words = a list of preferred head nouns
                        whole_dps = the rest of each dp outside its coref
    """

    max_counts = lambda D: max_set(D.items(), lambda x: x[1])
    # pre-requirement
    coref,c_raw = coref_bundle
    try:
        cnlps = get_cnlp(coref, sentences)
    except:
        return TYPE_ERROR
    #print "\n\n"
    #pprint(coref) 
    
    #(0) Apply the pre-counted list of HNs. If one of the most common head 
    #       nouns appears left of the head, it is the type.
    if pref_types:
        #Get the proper nouns left of the head
        dp_wholes = coref_kinda_flat(c_raw)
        
        head_spaces = get_head_space(coref, sentences, dp_wholes)
        head_squished = [w for s,i,w in sum(head_spaces,[])]
        #head_squished = [w for w in head_squished if pref_types(w["Lemma"])]
        head_squished = [w for w in head_squished if pref_types(w)]
        
        lemmas = ft.histo(ft.indexBy("Lemma", head_squished))
        hell_yea = max_counts(lemmas)

        if len(hell_yea) == 1:
             return hell_yea[0][0].lower()

    #(1-X) preparation 
    # we gotta dig deeper for these

    #get corenlp output for each word, and get the parts out we want
    NEcounts = ft.histo(ft.indexBy("NamedEntityTag", cnlps))
    Lcounts_all = ft.histo(ft.indexBy("Lemma", cnlps))
    Lcounts = dict([l for l in Lcounts_all.items() if l[0] not in pn_lemmas])

    #get the max_set of Named Entity counts and Lemma counts
    NE_crap = {"O", "MISC"}
    NE_crapless = dict([l for l in NEcounts.items() if l[0] not in NE_crap])
    NE_max = max_counts(NE_crapless)
    L_max = max_counts(Lcounts)
    
    #head noun counting
    # (this is done as a weird side effect--a slightly cleaned up version is
    #   applied as the first step here.)
    temp = singlitate(L_max)
    if temp in HN_counter: HN_counter[temp] += 1
    else: HN_counter[temp] = 1

    #pprint(NE_max)
    #pprint(Lcounts)
    #print "\n"

    #Data extraction is finally done.


    #(1) If we have a solid NE instance, return that.
    NE_max = singlitate(NE_max)
    NE_max = NE_max if NE_max not in NE_crap else False
    if NE_max: return NE_max
    
    
    #(3) We're really hurtin now. It tries to build a type based on pn.
    L_max_pn = set([pn for pn, c in max_counts(Lcounts_all)])
    #L_max_pn = singlitate(L_max_pn)
    
    #THIS NEEDS SOME TWEAKING
    for pn_tag in pronoun_groups:
        if L_max_pn & pronoun_groups[pn_tag]: return pn_tag
    
    #EMERGENCY ATTTEMPT
    return "THINGY"

    #(2) Is there a single most frequent, non-pn lemma? Return that.
    L_max = singlitate(L_max)
    if L_max: return L_max.lower()
    
    #(4) Real desperate here.
    # take the shortest head, all lowercase:
    if L_max_pn: 
        worst = min(L_max_pn, key=lambda s: len(s)).lower()
        print "Selecting, possibly, the worst possible choice"
        print L_max_pn
        print worst
        print "\n"
        return worst


    #(5) Ut-oh
    print "WARNING: No type for this poor fellow:"
    pprint(coref)
    pprint(NEcounts)
    pprint(NE_max)
    pprint(Lcounts)
    pprint(L_max)
    print "oh, and"
    pprint(L_max_pn)
    print "\n"
    return "NO-VALID-TYPE"



    


def max_set(stuff, key):
    """Python built in max is dumb, in that just chooses some random
    maximum when there's a tie for max. 

    This returns the set of things tied for the max value, and the empty
    set if there's nuttin.
    """
    if not stuff: return []

    output = {}
    for shit in stuff:
        k = key(shit)
        if k in output: output[k].append(shit)
        else: output[k] = [shit]
     
    return output[max(output)]




############################################
# DOCUMENT-LOCAL MANIPULATIONS/EXTRACTIONS #
############################################

#we don't need the string at the end, it's just holding us back
remove_strings = lambda L: [(sent, i) for sent,i, w in L]
#never let extraneous strings hold you back

def extract_cn(corefs, words, deps, conjunctions, whole_chains=False, types=[]):
    """
    Extract the joint counts C(e(w,d), e(v,g)) for all w,d and v,g in a doc.
    
    'C(e(x, d), e(y, f)) is the number of times the two events e(x, d) and 
    e(y, f) had a coreferring entity filling the values of the dependencies 
    d and f.'

    In other words, it counts how many times something is both a d to an x
    and an f to a y. Like,
        John murdered Sandy, so the cops arrested him.
    John is a subject to murder and an object to arrested, so 
        C(e(murder, subject), e(arrest, object)) += 1

    Args:
        corefs = coreference chains
        words = relevant words for extraction
        deps = dependencies
        conjunctions = number of combinations of verbs in a chain to count
        whole_chains = instead of returning combinations of vd pairs, just
                        return the chains
        tags = if a tag is to be included with the data, wraps the vd n-tuples
                in another tuple with the tag
    """
    #debuc refers to debuccalization--a linguistic process where 
    #voiceless stops become glottal fricatives. the word means "the process of
    #chopping off the head"
    debuc_words = remove_strings(words)
    word_table = [{"coord":(i,j), "lemma":l} for i,j,l in words]
    worddex = ft.indexBy("coord", word_table)
    lemma = lambda i,j: worddex[(i,j)][0]["lemma"]
    
    pairs = []
    if not types: types = [False]*len(corefs)
    for chain, typ in zip(corefs, types):
        debuc_chain = remove_strings(chain) 

        # Find dependencies related to chain
        relevant_dep = []
        for dep in deps:
            rel, a_full, b_full = dep
            a,b = remove_strings([a_full,b_full])
            if a in debuc_chain or b in debuc_chain:
                # Find dependencies that are relevant
                if a in debuc_words: tar = a_full
                elif b in debuc_words: tar = b_full
                else: tar = False
                
                # Produce pairs and append
                if tar:
                    i,j,raw_string = tar
                    relevant_dep.append((lemma(i,j), rel))

        #Combinatorics--for generating joint probability distributions
        #Use append to retain the source of the collocations
        #pairs.append([x for x in combinations(relevant_dep, conjunctions)])

        #Use extend to collapse all collocations into a single list
        if not whole_chains:
            comb = combinations(set(relevant_dep), conjunctions)
            if not typ:
                pairs.extend([tuple(sorted(x)) for x in comb])
            else:
                pairs.extend([(tuple(sorted(x)), typ) for x in comb])
                
        elif whole_chains:
            #for whole chains mode, we don't do that. 
            pairs.append(set(relevant_dep))
        else:
            raise Exception("Impossible!")

    return pairs

def extract_c(*args):
    "The version that hides the arbitatariness of p(a,b,...n)"
    args = list(args)
    args.append(1)
    output = extract_cn(*args)
    #output = [x for x, in output] #unpack singleton tuples from combin
    return output

def extract_cj(*args, **kwargs):
    "The version that hides the arbitatariness of p(a,b,...n)"
    args = list(args)
    args.append(2)
    return extract_cn(*args, **kwargs)

#################
# DATA-CLEANING #
#################
# Sometimes you need bleach. Sometimes you need a flamethrower.

def remove_redundant(dependencies):
    """"
    This is intended for the cleaners argument of extract_cn.

    So I was a moron, and never removed some redundant data from the corpus
    before co-reference. This worked out a bit gnarly; pairs like this
    have been showing up. 
    (((u'do', u'aux'), (u'do', u'rcmod')),
          8.671361343047339,
          0.714857142857143,
          6.1938295307481),
    So because they both appear with the same coreferent, and they repeat,
    they're getting a high pmi. This is bullshit.

    These are, I suspect, because of a bug in the corpus extractor mixing 
    with a bug in CoreNLPPython (just turn the double line breaks into periods,
    that would be sensible! (maybe I should have read the manual)), where text
    joined together without a period, but with double linebreaks, behaves
    like a single sentence. This happens at the beginning of documents; maybe
    else where, that's for tweaking as applied.


    (never mind, this doesn't seem to be the cause of the bug, if one at all.
    Never the less, this ought to be implemented anyway.)
    """
    
    dep_table = [{"pair": (a[-1], b[-1]), 
                  "original_pair": (a,b),
                  "distance_distance": a[1]-b[1],
                  "rel": rel} for rel,a,b in dependencies]
    depdex = ft.indexBy("pair", dep_table)
    for verb in depdex:
        if len(depdex[verb]) >= 2:
            pprint(depdex[verb])
    
    return dependencies


def target_deps(dependencies, flattener):
    "Processes dependencies through flattener."

    return deps

# COMBINE DATA-STRUCTURES #
# I doubt these are necessary.

def combine_c(A,B):
    "Combines two Cs into a new C."

def combine_cj(A,B):
    "Combines two joint Cs into a new joint C."

# CONDENSE #

def condense_c(data):
    "Turns data into a structure ready for approximate_p"
    data_table = [{"pair": d} for d in data] #creates a free table
    datadex = ft.indexBy("pair", data_table) #creates a dex
    return ft.histo(datadex) #converts the dex to counts

def condense_cj(data):
    "Turns data into a structure ready for approximate_pj"
    #the process is mostly similar, but requires some preprocessing
    data = [tuple(sorted(d)) for d in data] #this triangularizes the data
    return condense_c(data)

# PROBABILITIES #

def curried_p(c_data):
    numerator = sum(c_data.values())
    #I hope the closure doesn't fuck this up
    return lambda wd_ps: approximate_p(c_data, numerator, wd_ps)

def approximate_p(c_data, numerator, wd_pairs):
    """
    Approximate p with c_data. 
    
    This ought to be curried. (wd_pair will be the only arg post-facto)

    Args:
        c_data = counts of each wd_pair
        numerator = sum(counts) -- as an arg, it can be optimized better
        wd_pair = whose probability is returned. oughtta be a tuple of pairs.

    """
    #ensure appropriate order
    #print "numer",numerator
    wd_pairs = tuple(sorted(wd_pairs))
    if wd_pairs not in c_data: return 0.0
    else: return float(c_data[wd_pairs])/numerator


