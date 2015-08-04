"""
utilsCrowdKernel.py


author: Lalit Jain (lalitkumarj@gmail.com)
edited: 1/18/15

This module has methods that assist with the crowd kernel for pairwise comparisons presented here: 
http://research.microsoft.com/en-us/um/people/adum/publications/2011-crowd-kernel.pdf

If you're trying to COMPUTE an embedding, you might simply call:
    X,emp_loss = computeEmbedding(n,d,S)

You may also consider getLoss to check how well an embedding is performing.
"""

from numpy import *
from numpy.random import *
import numpy.random
from numpy.linalg import *

#eig = numpy.linalg
norm = linalg.norm
floor = math.floor
ceil = math.ceil
realmin = finfo(double).tiny
log = math.log

import time

def main():
    """
    Example of Usage

    Creates some fake data and finds an embedding
    """
    
    # generate some fake data
    n = 30
    d = 2
    m = int(ceil(40*n*d*log(n)))  # number of labels
    
    p = 0.1; # error rate
    
    Strain = []
    Stest = []
    Xtrue = randn(n,d);
    for iter in range(0,m):

        # get random triplet
        q,score = getRandomQuery(Xtrue)

        # align it so it agrees with Xtrue: "q[2] is more similar to q[0] than q[1]"
        query_ordering_disagrees_with_Xtrue = score<0
        if query_ordering_disagrees_with_Xtrue:
            q = [ q[i] for i in [1,0,2]]

        # add some noise
        R = rand()
        if R<p:
            q = [ q[i] for i in [1,0,2]]

        if iter < .9*m:
            Strain.append(q)
        else:
            Stest.append(q)

    # compute embedding 
    X,emp_loss_train = computeEmbedding(n,d,Strain,mu=.01,num_random_restarts=2,epsilon=0,verbose=True)

    # compute loss on test set
    emp_loss_test,hinge_loss_test,log_loss_test = getLoss(X,Stest)

    print
    print 'Training loss = %f,   Test loss = %f' %(emp_loss_train,emp_loss_test)


def getRandomQuery(X):
    """
    Outputs a triplet [i,j,k] chosen uniformly at random from all possible triplets 
    and score = abs( ||x_i - x_k||^2 - ||x_j - x_k||^2 )
    
    Inputs:
        (numpy.ndarray) X : matrix from which n is extracted from and score is derived
        
    Outputs:
        [(int) i, (int) j, (int) k] q : where k in [n], i in [n]-k, j in [n]-k-j
        (float) score : signed distance to current solution (positive if it agrees, negative otherwise)
        
    Usage:
        q,score = getRandomQuery(X)
    """
    n,d = X.shape
    
    i = randint(n)
    j = randint(n)
    while (j==i):
        j = randint(n)
    k = randint(n)
    while (k==i) | (k==j):
        k = randint(n)
    q = [i, j, k]
    
    score = getTripletScore(X,q)

    return q,score

def getTripletScore(X,q):
    """
    Given X,q=[i,j,k] returns score = ||x_j - x_k||^2 - ||x_i - x_k||^2
    If score > 0 then the triplet agrees with the embedding, otherwise it does not 

    Usage:
        score = getTripletScore(X,[3,4,5])
    """
    i,j,k = q

    return dot(X[j],X[j]) -2*dot(X[j],X[k]) + 2*dot(X[i],X[k]) - dot(X[i],X[i])


def getLoss(X,S):
    """
    Returns loss on X with respect to list of triplets S: 1/len(S) \sum_{q in S} loss(X,q).
    Intuitively, q=[i,j,k] "agrees" with X if ||x_j - x_k||^2 > ||x_i - x_k||^2.

    For q=[i,j,k], let s(X,q) = ||x_j - x_k||^2 - ||x_i - x_k||^2
    If loss is hinge_loss then loss(X,q) = max(0,1-s(X,q))
    If loss is emp_loss then loss(X,q) = 1 if s(X,q)<0, and 0 otherwise

    Usage:
        emp_loss, hinge_loss = getLoss(X,S)
    """
    n = X.shape[0]
    d = X.shape[1]

    emp_loss = 0 # 0/1 loss
    hinge_loss = 0 # hinge loss
    log_loss = 0 #log_loss in crowd kernel model
    for q in S:
        loss_ijk = getTripletScore(X,q)
        hinge_loss = hinge_loss + max(0,1. - loss_ijk)
        log_loss = log_loss - log(getCrowdKernelTripletProbability(X[q[0]],X[q[1]],X[q[2]],mu=.01))

        if loss_ijk < 0:
           emp_loss = emp_loss + 1.

    emp_loss = emp_loss/len(S)
    hinge_loss = hinge_loss/len(S)
    log_loss = log_loss/len(S)
    return emp_loss, hinge_loss, log_loss


def getCrowdKernelTripletProbability(b,c,a,mu=0):
    """
    Return the probability of triplet [b,c,a] where a is closer to b than c.

    Namely:
    pabc = (mu + || c - a||^2)/(2*mu + || b - a ||^2+|| c - a ||^2)
    
    Inputs:
    	(numpy.ndarray) a : numpy array
    	(numpy.ndarray) b : numpy array
	(numpy.ndarray) c : numpy array
        (float) mu : regularization parameter
    """
    ca = norm(c-a)
    ba = norm(b-a)
    return (mu+ca*ca)/(2*mu+ba*ba+ca*ca)


def getEntropy(tau):
    """
    Return the entropy of a distribution tau.

    Namely:
    H(tau) = sum -tau[i]*log(tau[i])
    
    Inputs:
    	(numpy.ndarray) tau : numpy array representing a probability distribution
    """
    e = 0
    for i in range(len(tau)):
        if tau[i] > 0:
            e += -1*tau[i]*log(tau[i]) 
    return e
    
def getCrowdKernelTauDistribution(X, S, mu=.01):
    """
    Return the tau distributions for each point [n].
 
    Returns a len(X)xlen(X) two dimensional arrray. The ith row of a is the tau distribution corresponding to the posterior distribution of a.
   
    Inputs:
	(numpy.ndarray) X: current embedding of points
	(list) S: list of triplets
	(float) mu: regularization parameter
    Usage:
    	tau = getCrowdKernelDistribution(X,S) 
    """
    n,d = X.shape
    tau = zeros((n,n))
    # Loop over each query
    for q in S:
        a = q[2]
        # Multiply by the amount the query contributes to each tau
        for i in range(n):
            tau[a,i] = tau[a,i] + log( getCrowdKernelTripletProbability(X[q[0]], X[q[1]], X[i], mu=mu))
                
    # Normalize
    for a in range(n):
        tau[a] = exp(tau[a])
        s = sum(tau[a])
        tau[a] = tau[a]/s
        
    return tau
    
def getGradient(X, S, mu):
    """
    Returns gradient of the log loss of the crowd kernel probability distribution.
    Requires a parameter mu for regularization.
    
    Usage:
        G,avg_grad_row_norm_sq,max_grad_row_norm_sq,avg_row_norm_sq = getGradient(X,S)
    """
    n,d = X.shape
    m = len(S)
    
    G = zeros((n,d))

    log_loss = 0
    for q in S:
        i,j,k = q
        num = max(mu + norm(X[k]-X[j])*norm(X[k]-X[j]) , realmin)#max(mu + D[k,j] , realmin)
        den = max(2*mu + norm(X[k]-X[i])*norm(X[k]-X[i]) + norm(X[k]-X[j])*norm(X[k]-X[j]), realmin)#max(2*mu + D[k,i] + D[k,j], realmin)
        G[i] += 2/den * (X[k]-X[i])
        G[j] += (2/num-2/den)*(X[j]-X[k])
        G[k] += 2/num * (X[k]-X[j])-2/den*(2*X[k]-X[i]-X[j]) 
        log_loss += log(den) - log(num)

    log_loss = log_loss/len(S)
    # Remember, the loss function is the sum of log(1/p^k_ij), this leads to an extra minus sign
    G = -1./len(S) * G
    # compute statistics about gradient used for stopping conditions
    mu = mean(X,0)
    avg_row_norm_sq = 0.
    avg_grad_row_norm_sq = 0.
    max_grad_row_norm_sq = 0.
    norm_grad_sq_0 = 0.

    for i in range(n):
        row_norm_sq = 0
        grad_row_norm_sq = 0
        for j in range(d):
            row_norm_sq += (X[i,j]-mu[j])*(X[i,j]-mu[j])
            grad_row_norm_sq += G[i,j]*G[i,j]
            
        avg_row_norm_sq += row_norm_sq/n
        avg_grad_row_norm_sq += grad_row_norm_sq/n
        max_grad_row_norm_sq = max(max_grad_row_norm_sq,grad_row_norm_sq)

    return G,log_loss,avg_grad_row_norm_sq,max_grad_row_norm_sq,avg_row_norm_sq


def computeEmbedding(n, d, S, mu=.01, num_random_restarts=0,max_num_passes=0,max_norm=0, epsilon=0.01, verbose=False):
    """
    Computes an embedding of n objects in d dimensions usin the triplets of S.
    S is a list of triplets such that for each q in S, q = [i,j,k] means that
    object k should be closer to i than j.

    Inputs:
        (int) n : number of objects in embedding
        (int) d : desired dimension
        (list [(int) i, (int) j,(int) k]) S : list of triplets, i,j,k must be in [n].
    	(float) mu : regularization value 
        (int) num_random_restarts : number of random restarts (nonconvex optimization, may converge to local minima)
        (int) max_num_passes : maximum number of passes over data SGD makes before proceeding to GD (default equals 16)
        (float) max_norm : the maximum allowed norm of any one object (default equals 10*d)
        (float) epsilon : parameter that controls stopping condition, smaller means more accurate (default = 0.01)
        (boolean) verbose : outputs some progress (default equals False)

    Outputs:
        (numpy.ndarray) X : output embedding
        (float) gamma : Equal to a/b where a is max row norm of the gradient matrix and b is the avg row norm of the centered embedding matrix X. This is a means to determine how close the current solution is to the "best" solution.  
    """

    if max_num_passes==0:
        max_num_passes = 32
    
    X_old = None
    emp_loss_old = float('inf')
    num_restarts = -1
    
    while num_restarts < num_random_restarts:
        num_restarts += 1
        
        print "Epoch SGD"
        ts = time.time()
        X,acc = computeEmbeddingWithEpochSGD(n,d,S,mu,max_num_passes=max_num_passes,epsilon=0.,verbose=verbose)
        te_sgd = time.time()-ts
        
        print "Gradient Descent"
        ts = time.time()
        X_new, emp_loss_new, log_loss_new, hinge_loss_new, acc_new = computeEmbeddingWithGD(X, S, mu, max_iters=50, max_norm=max_norm, epsilon=epsilon, verbose=verbose)
        emp_loss_new,hinge_loss_new,log_loss_new = getLoss(X_new,S)
        te_gd = time.time()-ts

        if emp_loss_new<emp_loss_old:
            X_old = X_new
            emp_loss_old = emp_loss_new

        if verbose:
            print "restart %d:   emp_loss = %f,   hinge_loss = %f,   duration=%f+%f" %(num_restarts,emp_loss_new,hinge_loss_new,te_sgd,te_gd)


    return X_old, emp_loss_old

def computeEmbeddingWithEpochSGD(n,d,S,mu, max_num_passes=0,max_norm=0,epsilon=0.01,a0=0.1,verbose=False):
    """
    Performs epochSGD where step size is constant across each epoch, epochs are 
    doubling in size, and step sizes are getting cut in half after each epoch.
    This has the effect of having a step size decreasing like 1/T. a0 defines 
    the initial step size on the first epoch. 

    S is a list of triplets such that for each q in S, q = [i,j,k] means that
    object k should be closer to i than j.

    Inputs:
        (int) n : number of objects in embedding
        (int) d : desired dimension
        (list [(int) i, (int) j,(int) k]) S : list of triplets, i,j,k must be in [n].
    	(float) mu : regularization value 
        (int) max_num_passes : maximum number of passes over data (default equals 16)
        (float) max_norm : the maximum allowed norm of any one object (default equals 10*d)
        (float) epsilon : parameter that controls stopping condition (default = 0.01)
        (float) a0 : inititial step size (default equals 0.1)
        (boolean) verbose : output iteration progress or not (default equals False)

    Outputs:
        (numpy.ndarray) X : output embedding
        (float) gamma : Equal to a/b where a is max row norm of the gradient matrix and b is the avg row norm of the centered embedding matrix X. This is a means to determine how close the current solution is to the "best" solution.  


    Usage:
        X,gamma = computeEmbeddingWithEpochSGD(n,d,S)
    """
    m = len(S)

    # norm of each object is equal to 1 in expectation
    X = randn(n,d)*.0001

    if max_num_passes==0:
        max_iters = 16*m
    else:
        max_iters = max_num_passes*m

    if max_norm==0:
        max_norm = 10.*d


    epoch_length = m
    a = a0
    t = 0
    t_e = 0

    # check losses
    if verbose:
        emp_loss,hinge_loss,log_loss = getLoss(X,S)
        print "iter=%d,   emp_loss=%f,   hinge_loss=%f, log_loss=%f,  a=%f" % (0,emp_loss,hinge_loss,log_loss,a)
    rel_max_grad = None
    while t < max_iters:
        t += 1
        t_e += 1
        
        # check epoch conditions, udpate step size
        if t_e % epoch_length == 0:
            a = a*0.5
            epoch_length = 2*epoch_length
            t_e = 0

            if epsilon>0 or verbose:
                # get losses
                emp_loss,hinge_loss,log_loss = getLoss(X,S)

                # get gradient and check stopping-time statistics
                G,log_loss,avg_grad_row_norm_sq,max_grad_row_norm_sq,avg_row_norm_sq = getGradient(X,S,mu)
                rel_max_grad = sqrt( max_grad_row_norm_sq / avg_row_norm_sq )
                rel_avg_grad = sqrt( avg_grad_row_norm_sq / avg_row_norm_sq )

                if verbose:
                    print "iter=%d,   emp_loss=%f,   hinge_loss=%f,  log_loss=%f,   rel_avg_grad=%f,   rel_max_grad=%f,   a=%f" % (t,emp_loss,hinge_loss,log_loss,rel_avg_grad,rel_max_grad,a)

                if rel_max_grad < epsilon:
                    break

        # get random triplet uniformly at random
        q = S[randint(m)]

        # take gradient step
        i,j,k = q
        num = max(mu + norm(X[k]-X[j])*norm(X[k]-X[j]) , realmin)
        den = max(2*mu + norm(X[k]-X[i])*norm(X[k]-X[i]) + norm(X[k]-X[j])*norm(X[k]-X[j]), realmin)
        grad_i = -1*(2/den * (X[k]-X[i]))
        grad_j = -1*((2/num-2/den)*(X[j]-X[k])) 
        grad_k = -1*(2/num * (X[k]-X[j])-2/den*(2*X[k]-X[i]-X[j])) 
        
        X[i] = X[i] - a*grad_i/len(S)
        X[j] = X[j] - a*grad_j/len(S)
        X[k] = X[k] - a*grad_k/len(S)
        
        # project back onto ball such that norm(X[i])<=max_norm
        for i in q:
           norm_i = norm(X[i])
           if norm_i>max_norm:
               X[i] = X[i] * (max_norm / norm_i)

    return X,rel_max_grad



def computeEmbeddingWithGD(X, S, mu, max_iters=0, max_norm=0, epsilon=0.01, c1=0.0001, rho=.7, verbose=False):
    """
    Performs gradient descent with step size as implemented in stochastic triplet embedding code, namely ckl_x.m 
    See: http://homepage.tudelft.nl/19j49/ste/Stochastic_Triplet_Embedding_files/STE_Release.zip


    S is a list of triplets such that for each q in S, q = [i,j,k] means that
    object k should be closer to i than j.

    Inputs:
        (numpy.ndarray) X : input embedding
        (list [(int) i, (int) j,(int) k]) S : list of triplets, i,j,k must be in [n]. 
        (float) mu : regularization parameter
    	(int) max_iters : maximum number of iterations of SGD (default equals 40*len(S))
    	(float) max_norm : the maximum allowed norm of any one object (default equals 10*d)
    	(float) epsilon : parameter that controls stopping condition, exits if gamma<epsilon (default = 0.01)
        (float) c1 : Amarijo stopping condition parameter (default equals 0.0001)
        (float) rho : Backtracking line search parameter (default equals 0.5)
    	(boolean) verbose : output iteration progress or not (default equals False)

    Outputs:
        (numpy.ndarray) X : output embedding
        (float) emp_loss : output 0/1 error
        (float) hinge_loss : output hinge loss
        (float) gamma : Equal to a/b where a is max row norm of the gradient matrix and b is the avg row norm of the centered embedding matrix X. This is a means to determine how close the current solution is to the "best" solution.  


    Usage:
        X,gamma = computeEmbeddingWithGD(X,S)
    """
    m = len(S)

    n,d = X.shape

    if max_iters==0:
        max_iters = 100

    if max_norm==0:
        max_norm = 10*d

    # check losses
    if verbose:
        emp_loss,hinge_loss,log_loss = getLoss(X,S)
        print "iter=%d,   emp_loss=%f,   hinge_loss=%f, log_loss=%f,   a=%f" % (0,emp_loss,hinge_loss,log_loss,float('nan'))
    alpha = .5*n
    t = 0
    emp_loss_0 = float('inf')
    hinge_loss_0 = float('inf')
    log_loss_0 = float('inf')
    rel_max_grad = float('inf')
    
    while t < max_iters:
        t+=1
        # get gradient and stopping-time statistics
        ts = time.time()
        G,log_loss,avg_grad_row_norm_sq,max_grad_row_norm_sq,avg_row_norm_sq  = getGradient(X, S, mu)
        rel_max_grad = sqrt( max_grad_row_norm_sq / avg_row_norm_sq )
        rel_avg_grad = sqrt( avg_grad_row_norm_sq / avg_row_norm_sq )
        if rel_max_grad < epsilon:
            if verbose:
                print "Exiting because of rel_max_grad=%s"%(rel_max_grad) 
            break
        
        # perform backtracking line search
        alpha = 2*alpha
        ts = time.time()
        emp_loss_0, hinge_loss_0, log_loss_0 = getLoss(X,S)
        norm_grad_sq_0 = avg_grad_row_norm_sq*n
        emp_loss_k, hinge_loss_k, log_loss_k = getLoss(X-alpha*G, S)
        
        inner_t = 0
        while log_loss_k > log_loss_0 - c1*alpha*norm_grad_sq_0:
            alpha = alpha*rho
            emp_loss_k,hinge_loss_k,log_loss_k = getLoss(X-alpha*G,S)
            inner_t += 1
        X  = X - alpha*G

        # project back onto ball such that norm(X[i])<=max_norm
        for i in range(n):
           norm_i = norm(X[i])
           if norm_i>max_norm:
               X[i] = X[i] * (max_norm / norm_i)
        
        # check losses
        if verbose:
            print "iter=%d,   emp_loss=%f,   hinge_loss=%f,   log_loss=%f,   rel_avg_grad=%f,   rel_max_grad=%f,   a=%f,   i_t=%d" % (t,emp_loss_k,hinge_loss_k,log_loss_k,rel_avg_grad,rel_max_grad,alpha,inner_t)

    
    return X,emp_loss_0,hinge_loss_0,log_loss_0,rel_max_grad


if __name__ == "__main__":
    main()
