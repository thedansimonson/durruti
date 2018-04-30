from generate import cj2009 # This is for schema_to_string only, TEMP FIX
from pprint import pprint

default_role_labels = ["SUBJ", "OBJ", "PREP"]
chain_names = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

def schema_struc(chain_names,events,chains,role_labels=default_role_labels):
    """
    Builds a schema struc -- a structure convenient for building renderings
    of schemas. 
    """
    struc = {}
    for e in events:
        verb, slots = e
        struc[verb] = {s: "_" if s in slots else "" for s in role_labels}
    
    var_roles = {}
    for var, chain in zip(chain_names, chains):
        filled, roles = chain
        var_roles[var] = roles
        for v,r in filled:
            struc[v][r] = var if roles else "_"

    return (struc, var_roles)
    

#THIS IS A TEMP FIX--UPDATE THE DAMN REFERENCES
# AND CUT AND PASTE THE FUCKING CODE
default_role_labels = ["SUBJ", "OBJ", "PREP"]
def schema_to_string(schema, role_labels = default_role_labels):
    """
    Printing the schema is a little opaque. This prints them pretty. 

    Maybe the structure is too opaque. Maybe that was a bad design choice.
    """
    chain_names = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    events, chains = schema
    
    #create a more convenient chain structure for printing
    struc = {}
    for e in events:
        verb, slots = e
        struc[verb] = {s: "_" if s in slots else "" for s in role_labels}
    
    var_roles = {}
    for var, chain in zip(chain_names, chains):
        filled, roles = chain
        var_roles[var] = roles
        for v,r in filled:
            struc[v][r] = var if roles else "_"

    #arrange into an output string
    rows = []
    for verb in struc:
        row = "\t".join([struc[verb]["SUBJ"],
                   verb,
                   struc[verb]["OBJ"],
                   struc[verb]["PREP"]])
        rows.append(row)

    for var in var_roles:
        rows.append(var+"="+str(var_roles[var]))

    return "\n".join(rows)


#optimized for TIKZ, but could be scaled for other things
SETTINGS = {"text_align": "left",
            "x_role_space":   1.2,
            "y_verb_space":   0.75,
            "x_schema_space": 5.1}

SHAPES = ["rectangle", "circle", "triup", "tridown"]
COLORS = ["red", "blue", "green", "yellow"]

def schema_arranger(schema, role_labels = default_role_labels):
    """
    Prepares an individual schema for representation in a figure.

    To do this it:
        * computes coordinates for all marks: role shapes and verbs

    This does not:
        - produce TIKZ--
    """
    struc, var_roles = schema_struc(chain_names,*schema)
    
    # this will factor in later
    roles = [(V,types) for V,types in var_roles.items() if types]
    roles.sort(key = lambda T: -len(T[1]))
    
    var_repr = dict(zip([V for V,types in roles], zip(SHAPES,COLORS)))
    var_repr["_"] = ("rectangle", "gray")

    ordered_struc = struc.items()
    # just saving it for now
    
    slot_offset = {"SUBJ": -1, "OBJ": 1, "PREP": 1.7}
    slot_offset = {s:i*SETTINGS["x_role_space"] for s,i in slot_offset.items()}

    drawables = []
    for j,(verb,slots) in enumerate(ordered_struc):
        #create verb
        verb_y = j*SETTINGS["y_verb_space"]
        drawables.append({"type": "text", "content": verb,
                          "pos": (0, verb_y),
                          })

        #include the argument slots
        for arg,var in slots.items():
            if not var: continue
            shape,color = var_repr[var]
            drawables.append({"type": shape, "color": color,
                              "pos": (slot_offset[arg],verb_y)})
        
    return drawables

    
def schemas_diagram(schemas, role_labels = default_role_labels):
    "Creates all drawables for all schemas; arranges them."

    #create drawable arrangements for each schema
    schemas = map(schema_arranger, schemas)
    drawables = []
    
    # shift every drawable of every schema by the schema position and flatten
    for i,schema in enumerate(schemas):
        drawables.append({"type":"comment/break", "comment":"Schema Start"})
        for drawable in schema:
            pos_x, pos_y = drawable["pos"]
            drawable["pos"] = (pos_x + i*SETTINGS["x_schema_space"], pos_y)
            drawables.append(drawable)
    return drawables

RECSIZE = 0.25
def tikz_rec_data(datum):
    "Special function for creating the tuple for a tikz rectangle"
    X,Y = datum["pos"]
    minus_corner = (X-RECSIZE, Y-RECSIZE)
    plus_corner = (X+RECSIZE, Y+RECSIZE)
    return (datum["color"], str(minus_corner), str(plus_corner))

def tikz_triup_data(datum,offset=RECSIZE):
    X,Y = datum["pos"]
    top = (X, Y+offset)
    left= (X-offset, Y-offset)
    right = (X+offset, Y-offset)
    return (datum["color"], top, left, right)

def tikz_tridown_data(datum):
    return tikz_triup_data(datum,offset=-RECSIZE)

# generates shapes for tikz
TIKZ_TYPE_GEN = {"text": lambda d: "\\node at %s {%s};" % \
                                (str(d["pos"]), str(d["content"])),
                 "rectangle": lambda d: "\\draw [fill=%s] %s rectangle %s;" %\
                                tikz_rec_data(d),
                 "circle": lambda d: "\\draw [fill=%s] %s circle [radius=%s];"%\
                                (d["color"], str(d["pos"]), str(RECSIZE)),
                 "triup": lambda d: "\\draw [fill=%s] %s -- %s -- %s;" %\
                                tikz_triup_data(d),
                 "tridown": lambda d: "\\draw [fill=%s] %s -- %s -- %s;" %\
                                tikz_tridown_data(d),
                 "comment/break": lambda d: "\n%"+d["comment"]
                }

def schemas_to_tikz(schemas, role_labels = default_role_labels):
    """
    Generates a figure for LaTeX and Tikz that represents the schemas
    provided.
    """
    drawables = schemas_diagram(schemas)
    
    print "sanity?"
    tikz_cmds = [TIKZ_TYPE_GEN[dble["type"]](dble) for dble in drawables]
    start = "\\begin{tikzpicture}\n"
    stop = "\n\\end{tikzpicture}"

    tikz_cmds = [start] + tikz_cmds + [stop]

    return "\n".join(tikz_cmds)

