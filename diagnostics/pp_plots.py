import numpy as np
import matplotlib.pyplot as plt
import pandas as pd


def PP_vals(PIT_values, alphas):
    """Compute alpha quantiles of the PIT-distribution P(PIT_values <= alpha):
    where P is the distribution of the target distribution (empirical approx)

    inputs:
    - PIT_values: numpy array of PIT values of a given estimator 
    computed for samples of the target distribution
    - alphas: numpy array of values to evaluate the PP-vals
    """
    z = [np.mean(PIT_values <= alpha) for alpha in alphas]
    return z


def PP_plot_1D(
    PIT_values, alphas, r_alpha_learned = None, colors=["blue"], labels=["Target"], title="PIT-distribution"
):
    """ 1D PP-plot: distribution of the PIT vs. uniform distribution
        It shows the deviation to the identity function and thus 
        allows to evaluate how well the given (estimated) distribution 
        matches the samples from the target distribution. 

    inputs:
        - PIT_values: list of numpy arrays of PIT values of given estimators
            computed for samples of the target distribution
        - alphas: numpy array of values to evaluate the PP-vals
        - r_alpha_learned: regressed quantile values for local PIT
    """
    # plot identity function
    fig = plt.figure()
    lims = [np.min([0, 0]),np.max([1, 1])]
    plt.plot(lims, lims, "--", color='black', alpha=0.75)
    
    for i, Z in enumerate(PIT_values):
        # compute quantiles P_{target}(PIT_values <= alpha)
        pp_vals = PP_vals(Z, alphas)  
        # Plot the quantiles as a function of alpha
        plt.plot(alphas, pp_vals, color=colors[i], label=labels[i])
    
    if r_alpha_learned is not None:
        fig = pd.Series(r_alpha_learned).plot(
            style=".", color="red", markersize=7, label="Learned"
        )
    
    plt.legend()
    plt.ylabel(r"$\alpha$-quantile $r_{\alpha}(x_0)$")
    plt.xlabel(r"$\alpha$")
    plt.title(title)
    plt.show()


def compare_pp_plots_regression(r_alpha_learned, true_pit_values, x_evals, nb_train_samples, labels):
    for j,x_eval in enumerate(x_evals):
        # plot identity function
        lims = [np.min([0, 0]),np.max([1, 1])]
        plt.plot(lims, lims, "--", color='black', alpha=0.75)
        
        # compute quantiles P_{target}(PIT_values <= alpha)
        alphas = np.linspace(0,0.999,100)
        pp_vals = PP_vals(true_pit_values[j], alphas)  
        # Plot the true quantiles as a function of alpha
        plt.plot(alphas, pp_vals, color='blue', label='True')
        
        colors = ['green', 'purple', 'orange', 'red', 'pink', 'yellow']
        for i,r_alpha in enumerate(r_alpha_learned[j][:len(labels)]):
            if labels[i] in labels:
                fig = pd.Series(r_alpha).plot(
                    style=".", color=colors[i], markersize=5, label=labels[i]+f' (n={nb_train_samples})'
                )
            
        plt.legend()
        plt.ylabel(r"$\alpha$-quantile $r_{\alpha}(x_0)$")
        plt.xlabel(r"$\alpha$")
        plt.title(r"Local PIT-distribution of the flow at $x_0$ = "+str(x_eval.numpy()))
        plt.show()