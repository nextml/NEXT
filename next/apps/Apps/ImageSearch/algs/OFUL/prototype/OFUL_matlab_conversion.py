import numpy as np

# I just converted the matlab function, and these are inputs to the function
# I defined them to show "variable not defined" errors
X, T, labels, X0, opts = [1] * 5

ridge = 1
delta = 1
R = 1
d = X.shape[0]
N = X.shape[1]

# The case where N > d (we only have a couple colors, many shoes)
valid_inds = range(N)

reward = np.zeros(T)
arms_pulled = np.zeros(T)
invVt = np.eye(d) / ridge
b = np.zeros(d)

beta = np.zeros(N)
for i in range(N):
    beta[i] = X[:, i].T.dot(X[:, i]) / ridge

theta_t = X0.copy()
S_hat = 1

for t in range(T):
    Kt = R * np.sqrt(d * np.log((1 + t/ridge)/delta)) + np.sqrt(ridge) * S_hat
    term1 = Kt * np.sqrt(beta)
    term2 = theta_T.T @ X

    # Possible bug: is this list concat or actual addition?
    max_index = np.argmax(term1[valid_inds] + term2[valid_inds])
    max_index = valid_inds[max_index]
    Xt = X[:, max_index].copy()
    arms_pulled[t] = max_index

    ## Now this is processAnswer, right?
    reward[t] = 2*labels[arms_pulled[t]] - 1

    b += reward[t] * Xt
    val = invVt.dot(Xt)
    val2 = Xt.T.dot(val)
    beta -= ((X.T.dot(val))**2).T / (1 + val2)
    invVt -= (val.dot(val.T)) / (1 + val2)
    theta_t = invVt.dot(b)

    valid_inds = list(set(valid_inds) - set(arms_pulled[t]))
    S_hat = 1
