from __future__ import division, print_function
import numpy as np
import scipy as sp
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import normalize
from scipy.io import loadmat
import scipy.stats as stats
from scipy.optimize import curve_fit
# plt.style.use('seaborn-poster')
import code
import time

# TODO: update to higher dimensions, see if follows sqrt(t) curve

TAKE_SIGN = False
USE_DO_NOT_ASK = True

def argmax_reward(X, theta, invV, beta, k=1, do_not_ask=None):
    r"""
    Loop over all columns of X to solve this equation:

        \widehat{x} = \arg \min_{x \in X} x^T theta + k x^T V^{-1} x
    """
    inv = np.linalg.inv
    norm = np.linalg.norm
    sqrt = np.sqrt

    # start = time.time()
    # rewards1 = [np.inner(X[:, c], theta) +
               # sqrt(k)*sqrt(np.inner(X[:, c], invV.dot(X[:, c])))
               # for c in range(X.shape[1])]
    # print("naïve approach: {:0.3e}".format(time.time() - start))

    # start = time.time()
    # rewards2 = X.T.dot(theta) + sqrt(k)*sqrt((X * (invV.dot(X))).sum(axis=0))
    # print("matrix approach: {:0.3e}".format(time.time() - start))

    start = time.time()
    rewards = X.T.dot(theta) + sqrt(k)*sqrt(beta)
    # print("beta approach: {:0.3e}".format(time.time() - start))

    # assert np.allclose(rewards1, rewards2)
    # assert np.allclose(rewards2, rewards)
    rewards = np.asarray(rewards)

    if USE_DO_NOT_ASK:
        rewards[do_not_ask] = -np.inf

    # mask = np.ones(rewards.shape[0], dtype=bool)
    # mask[do_not_ask] = False
    # rewards[~mask] = -np.inf
    return X[:, np.argmax(rewards)], np.argmax(rewards)

def reward(x, theta, R=2):
    r = np.inner(x, theta) + R*np.random.randn()
    if TAKE_SIGN:
        return np.sign(r)
    return r

def OFUL(X=None, R=None, theta_hat=None, theta_star=None, invV=None, S=1, T=25,
         d=None, n=None, lambda_=None, PRINT=False):
    """"
    X : x
    R: x
    theta_hat : algorithms, key='theta_hat'
    theta_star : a param the user passes in
    V : 
    S : unused
    T : num_tries
    d : x
    n : x
    lambda_ : can be hard coded for now
    """
    if PRINT:
        print("theta_star = {}".format(theta_star))

    # On NEXT, only save one reward and one arm
    rewards, arms = [], []
    b = np.zeros(d)
    beta = np.ones(n) / lambda_
    print("Arms = \n{}".format(X.T))
    V = lambda_ * np.eye(d)
    rel_errors = []
    for t in 1 + np.arange(T):
        k = R * np.sqrt(d*np.log((1 + t/lambda_) / delta)) + np.sqrt(lambda_)

        x, i_x = argmax_reward(X, theta_hat, invV, beta, k=k,
                               do_not_ask=arms)
        # TODO: this R needs to be tuned!
        rewards += [reward(x, theta_star, R=R)]
        arms += [i_x]
        print("arm pulled = {}".format(i_x))
        # print(t, "-- arm #", i_x, "reward =", r[-1])

        # if PRINT:
            # print((("||x|| = {:0.2}, ||optimal arm|| = {:0.2}, reward(x) = " +
                   # "{:0.2}").format(np.linalg.norm(x), np.linalg.norm(theta_star),
                                    # rewards[-1])))

        u = invV.dot(x)
        invV -= np.outer(u, u) / (1 + np.inner(x, u))
        beta -= (X.T.dot(u))**2 / (1 + beta[i_x])
        # beta_truth = np.diag(X.T.dot(invV).dot(X))
        # beta = beta_truth.copy()
        # print("beta = {}, beta_truth = {}".format(beta, beta_truth))
        # print("{} {}".format(np.inner(x, u), beta[i_x]))

        # to_print = X.T.dot(invV).dot(X)
        # diff =  np.abs(to_print - beta)
        # print("norm(diff) = {}".format(np.linalg.norm(diff)))
        # print("{}".format(np.diag(to_print)))

        b += rewards[-1] * x
        theta_hat = invV.dot(b)


        if PRINT:
            norm = np.linalg.norm
            print("||theta_hat - theta_star|| = {} @ {}".format(norm(theta_hat - theta_star), t)) 
        rel_errors += [norm(theta_hat - theta_star)]
    return theta_hat, np.asarray(rewards), arms, rel_errors

def test_OFUL(theta_star, T=50, PRINT=False):
    R = 2  # the std.dev for a sub-gaussian random variable
    lambda_ = 1/d

    # theta can either be zeros or random
    # initial approximation
    theta_star = np.random.randn(d)
    theta_star /= np.linalg.norm(theta_star)

    r_star = (X.T.dot(theta_star)).max()

    theta_hat = np.random.randn(d)
    theta_hat /= np.linalg.norm(theta_hat)
    # theta_hat = np.zeros(d)

    invV = np.eye(d) / lambda_

    theta_hat, rewards, arms, rel_errors = OFUL(X=X, R=R, theta_hat=theta_hat,
                                    theta_star=theta_star, invV=invV, d=d, n=n, T=T,
                                    lambda_=lambda_, PRINT=PRINT)
    norm = np.linalg.norm
    print("||theta_final - theta_star|| = {}".format(norm(theta_hat -
        theta_star)))
    plt.figure(figsize=(16, 8))
    plt.subplot(1, 3, 1)
    plt.title('Rewards')
    plt.plot(np.cumsum(r_star - rewards))
    plt.ylabel('cumsum(reward_star - rewards)')
    plt.xticks(rotation=90)

    plt.subplot(1, 3, 2)
    plt.title('Relative error between\n truth $\\theta^\\star$ and estimate $\\widehat{\\theta}$')
    plt.ylabel(r'$\|\theta^\star - \widehat{\theta} \|_2$')
    plt.plot(rel_errors)
    plt.xticks(rotation=90)

    plt.subplot(1, 3, 3)
    plt.plot(rewards, 'o')
    print(sum(rewards == 1))
    print(sum(rewards == -1))
    plt.title('Answers at each iteration')
    plt.savefig('take.sign={}_use.do.not.ask={}.png'.format(TAKE_SIGN,
                                                            USE_DO_NOT_ASK))
    plt.show()

    # x_star, _ = argmax_reward(X, theta_star, invV, k=0)
    # rewards_star = [np.inner(X[:, col], theta_star) for col in range(X.shape[1])]
    # # x_star = X[:, np.argmax(rewards_star)]
    # norm = np.linalg.norm
    # reward_star = np.inner(theta_star, x_star)

    # diff = np.linalg.norm(theta_star - theta_hat)

    # return rewards, reward_star, diff, theta_hat

# all for (n, d) = (2, 500)
# np.random.seed(1)  # quick convergence
# np.random.seed(5)
# np.random.seed(42)  # convergence to low reward
# np.random.seed(43)  # again quick convergence
np.random.seed(42)
T = 4000
d, n = (int(5e0), int(1e4))

delta = 0.1  # failure probability

# The optimal parameters
theta_star = np.random.randn(d)
theta_star /= np.linalg.norm(theta_star)

# The arms to pull. The columns are arms, the rows are features
X = np.random.randn(d, n)
X = normalize(X, axis=0)

test_OFUL(theta_star, T=T, PRINT=True)

# plt.figure()
# # plt.plot([reward_star] * len(rewards), '--', label='Maximum reward')
# plt.plot(rewards, label='Rewards @ each iteration')
# plt.plot(theory, label='least squares sqrt fit')
# plt.title('Rewards (d={}, n_arms={})'.format(d, n))
# plt.xlabel('Iteration')
# plt.ylabel('Reward')
# plt.legend(loc='best')
# plt.show()
