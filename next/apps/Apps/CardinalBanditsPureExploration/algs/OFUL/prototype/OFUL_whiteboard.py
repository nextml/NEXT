import numpy as np
import scipy as sp
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import normalize
from scipy.io import loadmat
import scipy.stats as stats
# plt.style.use('seaborn-poster')

def argmax_reward(X, theta, V, k=0):
    r"""
    Loop over all columns of X to solve this equation:

        \widehat{x} = \arg \min_{x \in X} x^T theta + k x^T V^{-1} x
    """
    inv = np.linalg.inv
    rewards = [np.inner(X[:, c], theta) +
               k*np.inner(X[:, c], inv(V).dot(X[:, c]))
               for c in range(X.shape[1])]
    rewards = np.asarray(rewards)
    return X[:, np.argmax(rewards)], np.argmax(rewards)

def reward(x, theta, R=2):
    # TODO: change R in here
    return np.inner(x, theta) + R*np.random.randn()

def OFUL(X=None, R=None, theta_hat=None, theta_star=None, V=None, S=1, T=25,
         d=None, n=None, PRINT=False):
    if PRINT:
        print("theta_star = {}".format(theta_star))

    rewards, arms = [], []
    b = np.zeros(d)
    for t in 1 + np.arange(T):
        k = R * np.sqrt(d*np.log((1 + t/lambda_) / delta)) + np.sqrt(lambda_)

        x, i_x = argmax_reward(X, theta_hat, V, k=k)
        # TODO: change this 0 to R!
        rewards += [reward(x, theta_star, R=0.1*R)]
        arms += [i_x]
        # print(t, "-- arm #", i_x, "reward =", r[-1])
        print(np.linalg.norm(x), np.linalg.norm(theta_star), rewards[-1])

        V += np.outer(x, x)
        # TODO: looking at .m file, the line below differs
        # maybe b += b reward(t) .* X[:, reward_ind]. Changing this doesn't
        # seem to matter :/
        # b += r[-1] * x
        b += V.dot(x)
        theta_hat = np.linalg.inv(V).dot(b)
        # theta_hat /= np.linalg.norm(theta_hat)

        # if PRINT:
        # print("theta = {}, x = {}, k = {}".format(theta_hat, x, k_t))
    return theta_hat, np.asarray(rewards), arms

# all for (n, d) = (2, 500)
# np.random.seed(1)  # quick convergence
# np.random.seed(5)
# np.random.seed(42)  # convergence to low reward
# np.random.seed(43)  # again quick convergence
d, n = (2, 1000)

# The arms to pull. The columns are arms, the rows are features
X = np.random.randn(d, n)
X = normalize(X, axis=0)

delta = 0.1  # failure probability

# The optimal parameters
theta_star = np.random.randn(d)
theta_star /= np.linalg.norm(theta_star)
theta_star = X[:, 0]

R = 2  # the std.dev for a sub-gaussian random variable
lambda_ = 1/d

# theta can either be zeros or random
# initial approximation
theta_hat = np.random.randn(d)
# theta_hat /= np.linalg.norm(theta_hat)
theta_hat = np.zeros(d)

# positive: 1
# negative: 2
# zero: 0

V = lambda_ * np.eye(d)

theta_hat, rewards, arms = OFUL(X=X, R=R, theta_hat=theta_hat,
                                theta_star=theta_star, V=V, d=d, n=n, T=150,
                                PRINT=True)

x_star, _ = argmax_reward(X, theta_star, V, k=0)
rewards_star = [np.inner(X[:, col], theta_star) for col in range(X.shape[1])]
# x_star = X[:, np.argmax(rewards_star)]
norm = np.linalg.norm
reward_star = np.inner(theta_star, x_star)

# print(X)
# print(theta_star)
# print(reward_star)
# print(X.T @ theta_star)

plt.figure()
plt.plot([reward_star] * len(rewards), '--')
plt.plot(rewards)
plt.show()
