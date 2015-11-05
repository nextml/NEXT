"""
Info.py

author: Kevin Jamieson (kevin.g.jamieson@gmail.com)
edited: 2/17/15

This file is used a resource the provides information like a description of this app, the
supported algorithms and default parameters. This is NOT somewhere to retrieve experiment-specific information.
"""

def get_about():
    """
    Returns description of app
    """
    about_str = (
"""The Dueling bandits problem was introduced in
"The K-armed Dueling Bandits Problem" by Yue et. al. in 2009. While that paper considers a 
regret framework, we consider here an exploration problem like what is considered in 
"Generic exploration and k-armed voting bandits" by Urvoy et al in 2013. Note the difference
between a Condorcet versus Borda rule, the latter of which we consider here. This kind of problem
has been implemented in practice on allourideas.org. Algorithms solving this problem are managed 
by DuelingBanditsPureExploration.py

Description:
Consider n alternatives from which we can choose any two and observe a random outcome decribing
the winner of 'dueling' these two alternatives. We wish to discover the 'best' alterantive using 
these outcomes using the Borda rule (note, there are many voting rules in the literature). 
To quantify what we mean by 'best', consider an n-by-n matrix P where the (i,j)th entry decribes 
the probability that alterantive i will beat j in a duel (by convention P(i,i) = 0.5 for all i). 
If we define s(i) = sum_{j=1}^n P(i,j) then the objective is to discover argmax_{i \in [n]} s(i)
with high probability using as few duels as possible. That is, for some input delta \in (0,1), 
a valid algorithm for this problem is guaranteed to output the 'best' arm with prob. at least 1-delta.

Use case:
Consider a design contest where thousands of designs are input by participants and people are 
invited to rate these designs, the winner of which will win some prize money and used for some purpose.
It would be impossible for someone to look at all the suggestions so they can only look at a subset. 
We could ask users to rate a selected bunch of designs on some scale (e.g. 1-5 stars) but people 
have very different calibrations and its not clear what a score-4 design means. Thus, we will show 
a user two different designs and ask a user to choose which one they prefer, and repeat. The algorithm
decides which two to show at any given time and how to decide a winner. A getQuery request sends two indices
to choose from, the processAnswer reports which answer was selected.""")
    return about_str

def get_default_instructions():
    instructions_str = "Please select the item that is most appropriate."
    return instructions_str

def get_default_debrief():
    debrief = "Thank you for participating"
    return debrief_str

def get_default_num_tries():
    num_tries = 100
    return num_tries

def get_implemented_algs():
    """
    Returns list of algorithms that are fully operational and implemented for this app
    """
    return ['BR_LilUCB','BR_Random','BR_SuccElim','BeatTheMean','BR_Thompson','BR_LilUCB_b2','BR_Random_b2','BR_Thompson_b2']


def get_default_alg_list():
    """
    If an alg_list is not specified, these are the parameters are the default parameters that 
    govern which algorithms are run and how they are evaluated
    """

    supported_alg_ids = get_implemented_algs()
    alg_list = []
    for alg_id in supported_alg_ids:
        alg_item = {}
        alg_item['proportion'] = 1./len(supported_alg_ids)
        alg_item['alg_id'] = alg_id
        alg_item['alg_label'] = alg_id
        alg_item['test_alg_label'] = alg_id
        alg_item['params'] = {}
        alg_list.append(alg_item)

    return alg_list