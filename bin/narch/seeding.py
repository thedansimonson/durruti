"""
Functions for modification/filter/selecting seed chains for narrative 
chain generation.

This is in two parts: manipulators and filters. 
    Manipulators alter the contents of chains.
    Filters alter chains themselves.
This distinction may not be 
"""
from string import whitespace
from math import sqrt
from pprint import pprint

#from sklearn.cluster import Ward
from sklearn.feature_extraction import DictVectorizer

#############################
# MANIPULATOR KEY FUNCTIONS #
#############################

def manipulate_all(data, with_this):
    """Alters chain contents.

    Args:
        with_this(wd) = function--for a worddep pair, returns...
            False if the item is to be removed from the chain
            wd' -- some altered or identical version -- if otherwise
    """
    new_chains = []
    for chain in data:
        new_chain = [wd for wd in [with_this(wd) for wd in chain] if wd]
        new_chains.append(new_chain)

    return new_chains

def manipulate_with(this):
    "Currier"
    return lambda D: manipulate_all(D, this)


#########################
# STOPLIST MANIPULATION #
#########################

def load_stoplist(fstream):
    """Loads a stoplist from a file.
    # are comments
    whitespace is stripped
    empty lines are removed
    """
    raw = fstream.read()

    lines = raw.split("\n")
    lines = [r.split("#")[0] for r in lines] #remove comments
    lines = [r.strip(whitespace) for r in lines]
    lines = [r for r in lines if r] #remove empty lines

    return set(lines)


#wd = worddep pair (a tuple), sl = stoplist
#sl supplied varies by need
rem_words   = lambda wd,sl: wd if wd[0] in sl else False
rem_dep     = lambda wd,sl: wd if wd[1] in sl else False
rem_worddep = lambda wd,sl: wd if wd    in sl else False

def remove_stop(stoplist, worddep, condition):
    "The killer"
    return condition(worddep, stoplist)


def stoplister(stoplist, con):
    "The currier"
    return lambda vd: remove_stop(stoplist, vd, condition=con)

#########################
# DEPENDENCY COLLAPSING #
#########################

# DO I REALLY NEED TO DO THIS? I CAN EXPERIMENT WITH THIS LATER

def collapse_dep(collapse_map, verbdep):
    
    return verbdep

def collapser(collapse_map):
    return lambda vd: collapse_dep(collapse_map, vd)


###########
# FILTERS #
###########

#I'm not doing the same abstraction with filters as I am for coreference-
#based filtering.

##################
# SIMPLE FILTERS #
##################

def lt_eq(x, chains):
    "Keep chains >= x / Remove chains shorter than x"
    return [c for c in chains if len(c) >= x]

setnorm = lambda s: tuple(sorted(s))
def rem_dup(chains):
    """Python sets can't contain python sets. So this just go hella complex.
    """
    return map(set, set(map(setnorm, chains)))
    

#####################################
# HEIRARCHICAL CLUSTERING FILTERING #
#####################################

# I'm gonna get this damn thing up and running, then come back to this.
# Once you have a large number of chains, this gets too slow.
# Use skluster

def dot(a,b):
    a,b = dict(a), dict(b)
    return sum([a[d]*b[d] if d in b else 0.0 for d in a])

pythagorean = lambda a: sqrt(sum([a[d]**2 for d in a]))

def norm_vec(a):
    a = dict(a)
    deno = pythagorean(a)
    a = {d: a[d]/deno for d in a}
    return a

def cos_sim(a,b):
    ""
    return dot(a,b)/(pythagorean(a)*pythagorean(b))

def vectorize_chain(chain):
    return {vd: 1.0 for vd in chain}


def centroid(vectors):
    "compute the centroid of a bunch of vectors"
    cent = {}
    for vector in vectors:
        for d in vector:
            if d in cent:
                cent[d] += vector[d]
            else:
                cent[d]  = vector[d]
    cent = {d: cent[d]/len(vectors) for d in cent}
    return cent

#doesn't really hash dicts, but makes them into something that can be
dict_hash = lambda d: hash(tuple(sorted(d.items())))

def get_distances(clusters):
    "Compute the distances between all clusters"

    distances = [[((dict_hash(ci[0]),dict_hash(cj[0])), cos_sim(ci[0],cj[0])) 
                        for cj in clusters[:i]] for ci in clusters]
    distances = sum(distances, [])

    return distances

def new_distances(old_clusters, new_cluster):
    pass
    
    


def cluster(chains, target_size):
    chains = map(vectorize_chain, chains)
    raise Exception("This function intentionally left broke. Use skluster.")

    #[centroid, [members]]
    #each chain starts with its own cluster
    clusters = sorted([[c, [c]] for c in chains])
    distances = get_distances(clusters)

    def merge(i,j):
        "Because the vectors aren't hashable, this is a careful index merge"
        i,j = tuple(sorted([i,j]))

        ci, I = clusters[i] #centroid, members
        cj, J = clusters[j]

        clusters.remove(clusters[j])
        clusters.remove(clusters[i])

        
        New = I+J
        c = centroid(New)
        new_cluster = [c,New]

        distances.extend(new_distances(clusters, new_cluster))
        clusters.append(new_cluster)


    while len(clusters) > target_size:
        #this is painfully suboptimal, but I have to make sacrifices sometimes
        cords, dist = max(distances, key=lambda x: x[1])
        
        print cords,"merged"
        i,j = cords
        merge(i,j)

        pprint(clusters[-1]) #new cluster
    
    return clusters
        
        
#Sample chains from the clusters.

def extract_centroids(clusters):
    "Return the centroid from each cluster"
    return [c[0] for c in clusters]

def extract_medoids(clusters):
    "Take member of each cluster nearest to its centroid"
    medoids = []
    for cluster in clusters:
        centroid, members = tuple(cluster)

        distances = [(m, cos_sim(m, centroid)) for m in members]
        m, dist = max(distances, key=lambda x: x[1])

        medoids.append(m)

    return medoids

def longest_examples(clusters):
    """The longest event chain from each cluster should provide the most
    information about the cluster. 
    """
    samples = []
    for cluster in clusters:
        centroid, members = tuple(cluster)
        samples.append(max(members, key=len))
        
    return samples

def random_sample(clusters, len_func):
    "Take a random sample of each cluster as a function of its length."

        
def devec(vectors):
    "Return vectors to normal"
    return [set(vec.keys()) for vec in vectors]


#############################
# H-CLUSTERING WITH SKLEARN #
#############################

# The above attempt at agglomerative clustering was a failure--too slow.
# And then I broke it, and I'm fail at version control. 
# But this is faster and gets the job done.

veclord = DictVectorizer(sparse = False)

def skluster(chains, target_size):
    "Cluster chains with the sklearn library. God I hope this fucking works."
    clusterlord = Ward(n_clusters=target_size)
    
    chains = map(vectorize_chain, chains)
    skains = veclord.fit_transform(chains)
    
    print "Well, this too shall pass?"

    predictions = clusterlord.fit_predict(skains)
    
    clusters = {c: [] for c in set(predictions)}
    for prediction, chain in zip(predictions, chains):
        clusters[prediction].append(chain)

    centroid_centralized = []
    for cluster in clusters:
        cluster = clusters[cluster]
        centroid_centralized.append([centroid(cluster), cluster])

    return centroid_centralized
        

#####################
# SINGLETON SEEDING #
#####################

def singleton_frequency(c_counts, target_size):
    """Gives seed chains from most frequent cj_counts.
    
    """
    ranked = sorted(c_counts.items(), key = lambda x: x[1])
    seeds = ranked[-target_size:]
    seeds = [{s} for (s,),c in seeds] #the seeds are packed in 1-tuples. see C
    return seeds 

