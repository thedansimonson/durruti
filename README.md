# Durruti 

*This public release is still under development.*

## Schema Generation Tool

*Durruti* is a set of Python scripts for generating *narrative 
schemas*, generalizations of stories. In particular, this system is the one 
that was used in Simonson (2017), Simonson and Davis (2016), and Simonson and
Davis (2015). Large components of this system where derived directly from
Chambers and Jurafsky (2009,2008)'s descriptions of their systems. 

This library has two fundamental use cases:
* One-click: high-level shell scripts that generate schemas from scratch, fully
    automatically.
* Use the Python scripts and libraries themselves: This is for the bold, who
    want to experiment with changing the schema generation process itself. 

The library is mostly written in pure Python, for good and for ill. This makes
it a little slower but makes debugging and experimental forks easier. 

## Requirements

Generating schemas can be a bit of a memory hog. On the `op1-sem` subcorpus of 
the New York Times Corpus (Simonson 2017, Simonson and Davis 2016)---around
200,000 documents, many of which are quite long---schema generation typically 
consumes 6Gs of RAM. It will typically take less on a smaller corpus, more on
a larger corpus.
This is in part because of a number
of optimizations that cache results so they finish in a reasonable amount of 
time, but also because this was research code, and who the hell has time to 
optimize for memory use when you've got a dissertation to finish.

The other thing you'll need is time. It simply takes a long time to do this
stuff. If your corpus is large, parsing alone can take a while. Schema 
generation can take anywhere between hours and days. 


## Setup




## One-Click Usage

These are still in development.


## Python Use

You can, of course, run the Python scripts directly. If you want to experiment
more with your schemas, this is a good way to do it. The shell scripts provide
a basic outline of the process and commands. 

Each script outputs serialized Python (".pkl" files) to pass data between 
scripts. 

### 01_hyperpickler.py

This joins together documents with their parses and saves them as serialized 
Python 

### compute-2-count.py

This script goes through the hyperpickled target corpus and extracts 
co-referring argument pairs (CAPs) for generating schemas. Contrary to its 
name, it doesn't actually count them. It used to, but things got refactored at
one point, and the name didn't change. This is research code. Deal with it.

Part of the reason this is a separate script, despite being so simple, is that 
it takes a while because of all the file IO.

### compute-3-build-model.py

NOW WE COUNT! Also, this is where the "score" is wrapped up into serialized 
Python. If you wanted to experiment with different scores---relationships 
between pairs of arguments---this is where you would make modifications.

### compute-4-xx.py

This is where you choose a germinator for the score you wrapped up in the 
previous step. Germination refers to the process of actually generating 
schemas. 

### compute-5-xxx.py

These are evaluation scripts. 

### compute-5b-xxx.py

These are baseline scripts, specifically for the NASTEA task, where they 
execute the NASTEA task without using schemas. 


## Citation

Easy, covers everything, cite my dissertation:
    Simonson, D. (2017). Investigations of the Properties of Narrative Schemas. Doctoral Dissertation. Advisor: Davis, A. R. Committee: Zeldes, A. and Chambers, N. Georgetown University, Washington, D.C.

For just the NASTEA task or a discussion of document heterogeneity/homogeneity,
cite:
    Simonson, D. and Davis, A. (2016). NASTEA: Investigating Narrative Schemas through Annotated Entities. In the Second CnewS Workshop, EMNLP 2016, Austin, TX. 

