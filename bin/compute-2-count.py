"""
Just the counting bit that happens before model building.

This is a short script, but slow. Got really annoying in previous iterations.

(Pulled out of compute-4 scripts, essentially.)

Input: a list of document dictionaries, themselves containing CAPs
Output: counts of each CAP in the corpus, essentially.
    {feature: {different count types...} }
"""
import ft, sys, pickle
from narch import C
import json
from random import shuffle, seed

seed(19800518)

###################
# Load Precursors #
###################
def disp(crap):
    pprint(crap)
    return crap



########################################################
# Specify Map of Arguments from parms-2-*.json to vars #
########################################################
#

ARGS_FNAME = sys.argv[1]
cfg = json.load(open(ARGS_FNAME))
MODE = cfg["MODE"]

SCORE_FNAME = (sys.argv[2] if "INPUT_FILENAME" not in cfg or 
                                               not cfg["INPUT_FILENAME"] 
                            else cfg["INPUT_FILENAME"])
print SCORE_FNAME


FEATURE_CHOICES = cfg["FEATURE_CHOICES"]
OUTPUT_FILENAME = cfg["OUTPUT_FILENAME"]+"-D{0:03d}-B{1:03d}.pkl"

# To turn off DEP downsampling, see the template for a neat func. 
DEP_BINFUNC = eval(cfg["DEP_BINFUNC"])

DOWNSAMPLE_BRE = cfg["DOWNSAMPLE_BRE"]
if DOWNSAMPLE_BRE:
    BRE_BINSIZE = cfg["BRE_BINSIZE"]
    BRE_XVALIDATIONS = cfg["BRE_XVALIDATIONS"]




fstream = open(SCORE_FNAME,"rb")
doc_counts = pickle.load(fstream)
fstream.close()


#print "RUNNING IN TEST MODE"
#doc_counts = doc_counts[:100]

####################
# Feature Division #
####################

def ftr_combin(*args):
    "Builds hashable features for data points"
    disjuncts = []
    for arg in args:
        # For explicity non-iterable types, the feature itself is the only 
        # values available, so it gets wrapped in a list.
        if any([type(arg) is t for t in [str,unicode,int,float]]):
            disjuncts.append([arg])
        else:
            # Otherwise, we're assuming it's iterable, and itself represents
            # the disjuncts that express possible feature values.
            disjuncts.append(arg)
    ft_stubs = [[f] for f in disjuncts[0]]
    for opts in disjuncts[1:]:
        ft_stubs = sum([[stub+[opt] for stub in ft_stubs] for opt in opts],[])
    return map(tuple, ft_stubs)
        


FTR_LOC = "ftr_loc"

if MODE == "topical":
    # old alternatives
    #feature_choices = ["cat-nyt-op"]
    #feature_choices = ["cat-match"]
    feature_choices = FEATURE_CHOICES
elif MODE == "flat":
    print "Running in FLAT MODE. Tagging documents for flat..."
    prog = len(doc_counts)
    for i,d in enumerate(doc_counts):
        if i % (prog/10) == 0: print i,"/",prog
        d["flat"] = ["flat"]
    feature_choices = ["flat"]

print "Tagging ftr_loc..."
doc_counts = ft.tag(doc_counts, FTR_LOC, ftr_combin, args=feature_choices)
print "Preparing multidex..."
doc_countsdex = ft.multidex(doc_counts, FTR_LOC)
#FTR_LOC gets used as the loop driver below


######################
# MAIN COUNTING LOOP #
######################

# Shuffles all the data around--sampling is done via list slicing, 
# this makes it random.
for feat in doc_countsdex: shuffle(doc_countsdex[feat])
original_sizes = {feat: len(doc_countsdex[feat]) for feat in doc_countsdex}

DEP_i = 0



# THIS IS THE DEP LOOP
while doc_countsdex:

    ################
    # BUILD COUNTS #
    ################


    combos_search = list(doc_countsdex)
    #combos_search = [('Crime and Criminals',)]
    #combos_search = list(doc_countsdex)[:10] # TEST MODE

    print "FTR_LOC values:"
    print list(doc_countsdex)

    if not DOWNSAMPLE_BRE:
        BRE_BINSIZE = 0
        BRE_XVALIDATIONS = 1
    
    for BRE_i in range(0, BRE_XVALIDATIONS):
        condensed_counts = {}

        for feature_tuple in combos_search:
            local_counts = {}
            dcd_local = doc_countsdex[feature_tuple]

            #seems stupid to recalculate binsize on each iteration, but tbh
            #this is the best way to do it. 
            # think about it if you don't believe me
            binsizereal = (BRE_BINSIZE if int(BRE_BINSIZE) is BRE_BINSIZE else
                           int(BRE_BINSIZE*len(dcd_local)))
            
            # Slice out the omitted piece 
            o_start, o_stop = (binsizereal*BRE_i, binsizereal*(BRE_i+1))
            print o_start, o_stop
            dcd_retained = dcd_local[0:o_start]+dcd_local[o_stop:]

            # ACTUALLY DO THE COUNTING FOR WHICH THIS SCRIPT IS NAMED
            print "Start: ", feature_tuple
            def get(k):
                "update from slow version"
                #get = lambda k: sum([d[k] for d in dcd_retained],[])
                output = []
                for d in dcd_retained:
                    output.extend(d[k])
                return output
            print "Obtaining and condensing counts..."
            print "Singletons..."
            local_counts["c_counts"] = C.condense_c(get("c_single"))
            print "freq..."
            freq_raw = get("freq_joint")
            local_counts["freq_raw"] = freq_raw
            local_counts["freq"] = C.condense_c(freq_raw)
            print "Joint counts..."
            local_counts["cj_counts"] = C.condense_c([c for c,t in freq_raw])
            print
            
            local_counts["config"] = sys.argv[1]

            condensed_counts[feature_tuple] = local_counts
        
        # Save Result
        outdump = {"condensed_counts": condensed_counts,
                   "BRE_i": BRE_i,
                   "DEP_i": DEP_i}
        pickle.dump(outdump, 
                        open(OUTPUT_FILENAME.format(DEP_i,BRE_i),"wb"))
    
    # Do DEP Downsample
    for feat in combos_search:
        current_size = len(doc_countsdex[feat])
        slice_size = DEP_BINFUNC(original_sizes[feat], current_size)
        if slice_size > current_size:
            del doc_countsdex[feat]
        else:
            doc_countsdex[feat] = doc_countsdex[feat][slice_size:]

    DEP_i += 1 #updates the filename, basically
                               

    


