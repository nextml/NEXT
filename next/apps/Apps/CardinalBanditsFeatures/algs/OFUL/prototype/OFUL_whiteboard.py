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

# TODO: update to higher dimensions, see if follows sqrt(t) curve

def argmax_reward(X, theta, V, k=0):
    r"""
    Loop over all columns of X to solve this equation:

        \widehat{x} = \arg \min_{x \in X} x^T theta + k x^T V^{-1} x
    """
    inv = np.linalg.inv
    norm = np.linalg.norm
    rewards = [np.inner(X[:, c], theta) +
               k*np.inner(X[:, c], inv(V).dot(X[:, c]))
               for c in range(X.shape[1])]
    rewards = np.asarray(rewards)
    return X[:, np.argmax(rewards)], np.argmax(rewards)

def reward(x, theta, R=2):
    return np.inner(x, theta) + R*np.random.randn()

def OFUL(X=None, R=None, theta_hat=None, theta_star=None, V=None, S=1, T=25,
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
    for t in 1 + np.arange(T):
        k = R * np.sqrt(d*np.log((1 + t/lambda_) / delta)) + np.sqrt(lambda_)

        x, i_x = argmax_reward(X, theta_hat, V, k=k)
        # TODO: this R needs to be tuned!
        rewards += [reward(x, theta_star, R=0.01*R)]
        arms += [i_x]
        # print(t, "-- arm #", i_x, "reward =", r[-1])

        # if PRINT:
            # print((("||x|| = {:0.2}, ||optimal arm|| = {:0.2}, reward(x) = " +
                   # "{:0.2}").format(np.linalg.norm(x), np.linalg.norm(theta_star),
                                    # rewards[-1])))

        V += np.outer(x, x)
        b += rewards[-1] * x
        theta_hat = np.linalg.inv(V).dot(b)

        if PRINT:
            norm = np.linalg.norm
            print("||theta_hat - theta_star|| = {}".format(norm(theta_hat - theta_star)))
    return theta_hat, np.asarray(rewards), arms

def test_OFUL(theta_star, T=50, PRINT=False):
    R = 2  # the std.dev for a sub-gaussian random variable
    lambda_ = 1/d

    # theta can either be zeros or random
    # initial approximation
    theta_star = np.random.randn(d)
    theta_star /= np.linalg.norm(theta_star)

    theta_hat = np.random.randn(d)
    theta_hat /= np.linalg.norm(theta_hat)
    # theta_hat = np.zeros(d)

    V = lambda_ * np.eye(d)

    theta_hat, rewards, arms = OFUL(X=X, R=R, theta_hat=theta_hat,
                                    theta_star=theta_star, V=V, d=d, n=n, T=T,
                                    lambda_=lambda_, PRINT=PRINT)

    x_star, _ = argmax_reward(X, theta_star, V, k=0)
    rewards_star = [np.inner(X[:, col], theta_star) for col in range(X.shape[1])]
    # x_star = X[:, np.argmax(rewards_star)]
    norm = np.linalg.norm
    reward_star = np.inner(theta_star, x_star)

    diff = np.linalg.norm(theta_star - theta_hat)

    return rewards, reward_star, diff, theta_hat

# all for (n, d) = (2, 500)
# np.random.seed(1)  # quick convergence
# np.random.seed(5)
# np.random.seed(42)  # convergence to low reward
# np.random.seed(43)  # again quick convergence
np.random.seed(42)
T = 50
d, n = (10, 2000)

delta = 0.1  # failure probability

# The optimal parameters
theta_star = np.random.randn(d)
theta_star /= np.linalg.norm(theta_star)

# The arms to pull. The columns are arms, the rows are features
X = np.random.randn(d, n)
X = normalize(X, axis=0)

N_trials = 1
output = [test_OFUL(theta_star, T=T, PRINT=True) for _ in range(N_trials)]
rewards = np.array([o[0] for o in output]).sum(axis=0) / N_trials
reward_star = np.array([o[1] for o in output]).sum() / N_trials
diffs = np.array([o[2] for o in output])
diff = diffs.sum() / N_trials

fn = lambda x, a, b: a*np.sqrt(b*x)

x = np.arange(T)
variables, _ = curve_fit(fn, x, rewards)
theory = fn(x, *variables)

print(r"average ||theta - theta_hat||_2 = {}".format(diff))

# plt.figure()
# plt.subplot(1, 2, 1)
# plt.hist(diffs, bins=20)
# plt.title(r'Histogram of $||\theta - \hat{\theta}||$')
# plt.xlabel(r'$||\theta - \hat{\theta}||$')
# plt.ylabel('Number of occurences')

# plt.subplot(1, 2, 2)
# # plt.plot([reward_star] * len(rewards), '--', label='Maximum reward')
# plt.plot(rewards, label='Rewards @ each iteration')
# plt.plot(theory, label='least squares sqrt fit')
# plt.title('Rewards (d={}, n_arms={})'.format(d, n))
# plt.xlabel('Iteration')
# plt.ylabel('Reward')
# plt.legend(loc='best')
# plt.show()
