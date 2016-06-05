function  [reward, arms_pulled] = oful_caf(X, T, labels, X0, opts)
% input: 
% X: data (d by N)
% T: total running time
% labels: rewards of X (N by 1)
% X0: initial point (d by 1)
% opts: tuning parameters, include fiels "ridge" for ridge regression,
% "R" for radius, and "delta" for noise var, all set to 1 by defult
% 
% output: 
% reward: rewards from time 1 to T (1 by T)
% at: indices of arms pulled from time 1 to T (1 by T)


d = size(X,1);  % ambient dimension
N = size(X,2);  % number of actions (arms)


if ~isfield(opts,'ridge') % tuning parameter for ridge regression
    ridge = 1;
else
    ridge = opts.ridge;
end
if ~isfield(opts,'R') % tuning parameter for search radius
    R = 1;
else
    % The same R as in initExp
    R = opts.R;
end
if ~isfield(opts,'delta') % tuning parameter for noise variance
    delta = 1;
else
    delta = opts.delta;
end


if N < d
    reward = zeros(1,T);
    arms_pulled = zeros(1,T);
    W = 1/ridge*(X'*X);
    alpha = diag(W);
    
    beta = X'*X0;
    valid_inds = 1:N;
    S_hat = 1;
    
    % This loop is at each time step (i.e., process 
    for t = 1:T
        Kt = R*sqrt(d*log( (1 + t/ridge)/delta))+sqrt(ridge).*S_hat;
        [~,max_index] = max(alpha(valid_inds)*sqrt(Kt)+beta(valid_inds));
        arms_pulled(t) = valid_inds(max_index);
        
        %reward(t) = sum(labels(:,at(t))) - 1;
        reward(t) = 2*labels(arms_pulled(t)) - 1;
        
        beta = beta + reward(t)*W(:,arms_pulled(t)) - W(:,arms_pulled(t))*beta(arms_pulled(t))/(1+W(arms_pulled(t),arms_pulled(t))) - W(:,arms_pulled(t))*W(arms_pulled(t),arms_pulled(t))/(1 + W(arms_pulled(t),arms_pulled(t)));
        Wold = W;
        for ii = 1:N
            for jj = 1:N
                W(ii,jj) = Wold(ii,jj) - (Wold(ii, arms_pulled(t))*Wold(arms_pulled(t),jj))/(1+Wold(arms_pulled(t),arms_pulled(t)));
            end
        end
        alpha = diag(W);
        valid_inds = setdiff(valid_inds,arms_pulled(t));
    end
else
    valid_inds = 1:N;
    % indst is Xk
    % reward is Xsum_i in OFUL.py
    reward = zeros(1,T);
    arms_pulled = zeros(1,T);
    %est_err = zeros(1,T);
    invVt = eye(d)/ridge;
    b = zeros(d,1);
    
    beta = zeros(1,N);
    for k = 1:N
        beta(k) = X(:,k)'*X(:,k)/ridge;
    end
    
    theta_t = X0;
    
    
    S_hat = 1;
    
    % One loop for one question
    for t = 1:T
        
        Kt = R*sqrt(d*log( (1 + t/ridge)/delta))+sqrt(ridge).*S_hat;
        
        term1 = Kt.*sqrt(beta);
        term2 = theta_t'*X;
        
        [~,max_index] = max(term1(valid_inds)+term2(valid_inds));
        max_index = valid_inds(max_index);
        Xt = X(:,max_index);
        
        arms_pulled(t) = max_index;
        
        %reward(t) = sum(labels(:,at(t))) - 1;
        % We have a reward -- a user has answered a question
        reward(t) = 2*labels(arms_pulled(t)) - 1;
        
        % Xt is a vector; which arm was pulled. All the features of that arm
        b = b + reward(t).*Xt;
        val = invVt*Xt;
        val2 = Xt'*val;
        beta = beta - ((X'*val).^2)'./(1 + val2);
        invVt = invVt - (val*val')./(1 + val2);

        % Final computation we need to make
        theta_t = invVt*b;
        
        valid_inds = setdiff(valid_inds, arms_pulled(t));
        S_hat = 1;
    end
end
