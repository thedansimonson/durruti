import re

PUNCT = "[(),.\\-]"
exclude_tokens_rx = re.compile("|".join([PUNCT]))
content = lambda X: [t for t in X if not exclude_tokens_rx.match(t)]

def entity_eq(A,B):
    A = [t.strip(".").lower() for t in content(A)]
    B = [t.strip(".").lower() for t in content(B)]
    if not A: return False
    return float(sum([a in B for a in A]))/len(A) >= 0.2

def entity_set_eq(A,B):
    if not B: return 0.0
    return float(sum([max([entity_eq(a,b) for b in B]) for a in A]))

def entity_intersect(A,B):
    if not B: return 0.0
    return float(sum([max([entity_eq(a,b) and entity_eq(b,a) \
                    for b in B]) for a in A]))

