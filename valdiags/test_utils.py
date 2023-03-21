# Utils for hypothesis testing:
# - compute p-value
# - evaluate hypothesis test

import numpy as np


def compute_pvalue(t_stat_est, t_stats_null):
    """Computes the p-value of a hypothesis test as the empirical estimate of:
                    
        p = Prob(T > \hat{T} | H0) 
        
        which represents the probability of making a type 1 error, i.e. the probability 
        of falsly rejecting the null hypothesis (H0).

    Args:
        t_stat_est (float): test statistic \hat{T} estimated on observed data.
        t_stats_null (list or array): a sample {ti} of the test statistic drawn under (H0): 
            --> t_i ~ T|(H0).

    Returns:
        float: empirical p-value: 1/n * \sum_{i=1}^n 1_{t_i > \hat{T}}, ti ~ T|(H0).
    """
    return (t_stat_est < np.array(t_stats_null)).mean()


def eval_htest(t_stats_estimator, metrics, conf_alpha=0.05, **kwargs):
    """ Evaluates a hypothesis test at a given significance level.

    Args:
        t_stats_estimator (function):  
            - takes as input a list of metrics that will give an estimate
            of the corresponding test statistics when computed on an observed data sample.
            - returns objects taken as inputs in `compute_pvalue` (i.e. test statistic
            estimated on observed data and drawn under the null hypothesis)
        metrics (list of str): contains the names of the metrics used in `t_stats_estimator`
        conf_alpha (float, optional): significance level of the test, yielding a confidence level
            of 1 - conf_alpha. Defaults to 0.05.
        kwargs: additional inputs to `t_stats_estimator`: True rejected, False otherwise.

    Returns:
        dict: contains the result of the hypothesis test for each metric
    """
    reject = {}
    t_stat_data, t_stats_null = t_stats_estimator(metrics=metrics, **kwargs)
    for m in metrics:
        p_value = compute_pvalue(t_stat_data[m], t_stats_null[m])
        reject[m] = p_value < conf_alpha  # True = reject

    return reject
