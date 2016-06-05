from __future__ import division
import numpy as np
import matplotlib.pyplot as plt
from scipy.io import loadmat
import pickle
import os, sys
import seaborn as sns
norm = np.linalg.norm

def get_matrix_from_url(url):
    import requests
    response = requests.get(url)
    d = eval(response.text)
    return np.array(d['features_all'])

results_file = "./2016-05-25/i_hats_[u'OFUL']_500_use_reward_to_choose.pkl"
results = pickle.load(open(results_file, 'rb'))

if not 'features_matrix.npy' in os.listdir('.'):
    home_dir = '/Users/scott/'
    X = loadmat(home_dir + 'Dropbox/Public/features_allshoes_8_normalized.mat')
    X = X['features_all'].T
    X = np.save('features_matrix.npy', X)
else:
    X = np.load('features_matrix.npy')

i_hats = results['i_hats']
answers = results['rewards']
x_star = X[:, results['i_star']].copy()

theta_star = x_star
reward_star = X.T.dot(theta_star).max()

x_hats = X[:, i_hats].copy()

theta_hats = []
rewards = []
lambda_ = 1 / x_star.shape[0]
invV = np.eye(x_star.shape[0]) / lambda_
for t in np.arange(x_hats.shape[1]):
    arm = X[:, i_hats[t]].copy()
    u = invV.dot(arm)
    invV -= np.outer(u, u) / (1 + np.inner(arm, u))
    theta_hat = invV.dot(answers[t]*arm)
    rewards += [np.inner(theta_hat, arm)]
    theta_hats += [theta_hat.tolist()]

# each row in theta_hats is a theta_hat, makes for loop below nice
theta_hats = np.array(theta_hats)

# The errors between each arm pull
# TODO: this is only a *guess* on how to generate the truth

# The error from the estimate, the sum of arms
diffs = np.array([x_star - theta_hat for theta_hat in theta_hats])
norm_diffs = norm(diffs, axis=1)

plt.figure(figsize=(12, 5))
plt.subplot(1, 3, 1)
# plt.plot([reward_star]*len(rewards))
plt.plot(np.cumsum(reward_star - rewards))
plt.xlabel('Iteration $i$')
plt.ylabel('Reward')
plt.title('Rewards at each iteration')

plt.subplot(1, 3, 2)
plt.plot(norm_diffs, 'o-')
plt.title('Relative error between true \narm vector and estimated arm vector')
plt.xlabel('Iteration $i$')
plt.ylabel(r'$\|\theta^\star - \widehat{\theta}_i\|_2$')

plt.subplot(1, 3, 3)
plt.title('Rewards at each iteration $(\pm 1)$')
plt.plot(answers)
plt.xlabel('Iteration $i$')
plt.ylabel('Answer')
plt.show()
