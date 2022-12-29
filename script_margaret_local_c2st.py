import submitit

import numpy as np
import pandas as pd
import torch
import time
import torch.distributions as D
from sbi.utils.metrics import c2st_scores
from sklearn.neural_network import MLPClassifier
from sklearn.ensemble import RandomForestClassifier

from diagnostics.localPIT_regression import local_flow_c2st, eval_local_flow_c2st
from diagnostics.pp_plots import PP_vals
from sklearn.model_selection import KFold


from data.data_generators import ConditionalGaussian1d
from data.feature_transforms import first_dim_only

# EXPERIMENT = 'Gaussian1d_localPIT'
EXPERIMENT = 'JR-NMM'
gauss1d_data = torch.load('saved_experiments/Gaussian1d_localPIT/datasets.pkl')
jrnmm_data = torch.load('saved_experiments/JR-NMM/datasets_naive.pkl')


# Data dimensions
DIM = 4 # target data
N_LIST = [3000, 4000, 6000] #[1000, 2000, 5000] #, 10000, 20000, 50000] # calibration dataset size

# Simulated data for clf eval 
data_gen = ConditionalGaussian1d()
x_samples = {}
for n in N_LIST:
    x_samples[n], _ = data_gen.get_joint_data(n=n)

# x_samples = {}
# x_samples[1000] = jrnmm_data['B_double_prime']['x'][:,:,0]
# x_samples[2000] = jrnmm_data[2000]['x'][:,:,0]
# x_samples[5000] = jrnmm_data[5000]['x'][:,:,0]
# x_samples[10000] = jrnmm_data['B_prime']['x'][:,:,0]
# x_samples[20000] = jrnmm_data['B']['x'][:20000,:,0]
# x_samples[50000] = jrnmm_data['B']['x'][:,:,0]


# Flows: trained on 10_000 samples...
maf_good = torch.load('saved_experiments/Gaussian1d_localPIT/maf_good.pkl')
maf_bad = torch.load('saved_experiments/Gaussian1d_localPIT/maf_bad.pkl')
# ... / 50_000 samples
jrnmm_flow = torch.load('saved_experiments/JR-NMM/posteriors_amortized/naive_posterior_nextra_0_single_rec_False_nsim_50000.pkl')

# Reference samples (base distribution)
P = D.MultivariateNormal(loc=torch.zeros(DIM), covariance_matrix=torch.eye(DIM))

# Calibration dataset (used to compute transformed flow samples)
# x_cal, theta_cal = gauss1d_data['cal']
# x_cal, theta_cal = jrnmm_data['B_prime']['x'], jrnmm_data['B_prime']['theta'] # 10_000
x_cal, theta_cal = jrnmm_data['B']['x'][:12500], jrnmm_data['B']['theta'][:12500] # 12_500

# Flow transform 
# flow_values_cal_good = maf_good._transform(theta_cal, context=x_cal)[0].detach().numpy()
# flow_values_cal_bad = maf_bad._transform(theta_cal, context=first_dim_only(x_cal))[0].detach().numpy()
flow_values_cal_jrnmm = jrnmm_flow._transform(theta_cal, context=x_cal)[0].detach().numpy()

null_samples = P.rsample((len(x_cal),)).numpy()

# Observation x_0
x_0 = torch.FloatTensor([[0, 1]])
x_list = torch.load('saved_experiments/JR-NMM/gt_observations/nextra_0/gain_experiment_new.pkl')[1]
x_0_list = [x_list[i][None,:,0] for i in [0,1,2,3,4,5,6,7,8,9,10]]

def get_executor_marg(job_name, timeout_hour=60, n_cpus=40):

    executor = submitit.AutoExecutor(job_name)
    executor.update_parameters(
        timeout_min=180,
        slurm_job_name=job_name,
        slurm_time=f"{timeout_hour}:00:00",
        slurm_additional_parameters={
            "ntasks": 1,
            "cpus-per-task": n_cpus,
            "distribution": "block:block",
        },
    )
    return executor

def eval_classifier_for_lc2st(x_samples, shifts, shift_object = 'mean', clfs=['rf', 'mlp'], n_trials=10):
    nb_samples = len(x_samples)
    P_samples = P.rsample((nb_samples,))
    P_joint = torch.cat([P_samples,x_samples], dim=1)
    clf_method = []
    shift = []
    scores = []
    times = []
    if shift_object == 'mean':
        for clf in clfs:
            clf_class = RandomForestClassifier
            clf_kwargs = {}
            if clf == 'mlp':
                ndim = P_joint.shape[-1]
                clf_class = MLPClassifier
                clf_kwargs = {
                    "activation": "relu",
                    "hidden_layer_sizes": (10 * ndim, 10 * ndim),
                    "max_iter": 1000,
                    "solver": "adam",
                    "early_stopping": True,
                    "n_iter_no_change": 50,
                }
            for m in shifts:
                # for _ in range(n_trials):
                Q = D.MultivariateNormal(loc=torch.FloatTensor([m]*DIM), covariance_matrix=torch.eye(DIM)).rsample((nb_samples,))
                Q_joint = torch.cat([Q,x_samples], axis=1)
                start = time.time()
                cross_val_scores = c2st_scores(P_joint, Q_joint, n_folds=n_trials, clf_class=clf_class, clf_kwargs=clf_kwargs)
                total_cv_time = start - time.time()
                for t in range(n_trials):
                    clf_method.append(clf)
                    shift.append(m)
                    scores.append(cross_val_scores[t])
                    times.append(total_cv_time)
    else:
        for clf in clfs:
            clf_class = RandomForestClassifier
            clf_kwargs = {}
            if clf == 'mlp':
                ndim = P_joint.shape[-1]
                clf_class = MLPClassifier
                clf_kwargs = {
                    "activation": "relu",
                    "hidden_layer_sizes": (10 * ndim, 10 * ndim),
                    "max_iter": 1000,
                    "solver": "adam",
                    "early_stopping": True,
                    "n_iter_no_change": 50,
                }
            for s in shifts:
                # for _ in range(n_trials):
                Q = D.MultivariateNormal(loc=torch.zeros(DIM), covariance_matrix=torch.eye(DIM)*s).rsample((nb_samples,))
                Q_joint = torch.cat([Q,x_samples], axis=1)
                start = time.time()
                cross_val_scores = c2st_scores(P_joint, Q_joint, n_folds=n_trials,clf_class=clf_class, clf_kwargs=clf_kwargs)
                total_cv_time = start-time.time()
                for t in range(n_trials):
                    clf_method.append(clf)
                    shift.append(s)
                    scores.append(cross_val_scores[t])
                    times.append(total_cv_time)
    df = pd.DataFrame({f'{shift_object}_shift': shift, 'accuracy': scores, 'total_cv_time':times, 'classifier':clf_method,})
    filename = f'saved_experiments/{EXPERIMENT}/lc2st_eval_clfs/df_{shift_object}_{nb_samples}.pkl'
    torch.save(df, filename)

def eval_clf_null(x_samples, dim=DIM, n_list = N_LIST, classifiers=['mlp'], n_trials=10):

    alphas = np.linspace(0,1,100)
    pp_vals_dirac = PP_vals([0.5]*1000, alphas)

    nb_samples = []
    probas_stds = []
    test_stats = []
    times = []
    clf_method = []

    for n in n_list:
        Q = D.MultivariateNormal(loc=torch.FloatTensor([0]*dim), covariance_matrix=torch.eye(dim)).rsample((n,))
        kf = KFold(n_splits=n_trials, shuffle=True, random_state=1)
        for clf_name in classifiers:
            start = time.time()
            for t, (train_index, test_index) in enumerate(kf.split(x_samples[n])):
                x_samples_train = x_samples[n][train_index]
                x_samples_test = x_samples[n][test_index]
                Q_train = Q[train_index]
                Q_test = Q[test_index]
                clf = local_flow_c2st(Q_train, x_samples_train, classifier=clf_name)
                std_x = []
                test_stats_x = []
                for i,x_obs in enumerate(x_samples_test):
                    proba = eval_local_flow_c2st(clf, x_obs, dim=dim, n_rounds=1000)
                    pp_vals = pd.Series(PP_vals(proba, alphas))
                    test_stats_x.append(((pp_vals - pp_vals_dirac) ** 2).sum() / len(alphas))
                    std_x.append(np.std(proba))
                probas_stds.append(np.mean(std_x))
                test_stats.append(np.mean(test_stats_x))
                nb_samples.append(n)
    
            total_cv_time = time.time() - start
            for t in range(n_trials):
                times.append(total_cv_time)
                clf_method.append(clf_name)
    df = pd.DataFrame({f'nb_samples': nb_samples, 'probas_std': probas_stds, 'test_stats': test_stats, 'total_cv_time':times, 'classifier':clf_method,})
    filename = f'saved_experiments/{EXPERIMENT}/lc2st_eval_clfs/df_null_std_cv_n_{n_list}_ntrials_{n_trials}_Tstats.pkl'
    torch.save(df, filename)

def score_lc2st_flow(flow_values_cal, x_cal, x_obs, classifier = 'mlp', n_trials=1000, flow_name='maf'):
    dim = flow_values_cal.shape[-1]

    mean = []
    std = []
    probas = []

    for t in range(n_trials):   
        clf = local_flow_c2st(flow_values_cal, x_cal, classifier=classifier)
        probas.append(eval_local_flow_c2st(clf, x_obs[0], dim=dim, n_rounds=1000))
        mean.append(np.mean(probas[t]))
        std.append(np.std(probas[t]))
    torch.save(probas, f'saved_experiments/{EXPERIMENT}/lc2st_results/12500/probas_{flow_name}.pkl')
    torch.save(mean, f'saved_experiments/{EXPERIMENT}/lc2st_results/12500/mean_{flow_name}.pkl')
    torch.save(std, f'saved_experiments/{EXPERIMENT}/lc2st_results/12500/std_{flow_name}.pkl')
    


# executor = get_executor_marg(f"work_eval_lc2st_clfs")
# launch batches
# with executor.batch():
#     print("Submitting jobs...", end="", flush=True)
#     tasks = []
#     for n in N_LIST:
#         for shifts, s_object in zip([[0,0.3,0.6,1,1.5,2,2.5,3,5,10],np.linspace(1,20,10)], ['mean','scale']):
#             kwargs = {
#                 "shifts": shifts,
#                 "shift_object": s_object,
#                 "x_samples": x_samples[n],
#             }
#             tasks.append(executor.submit(eval_classifier_for_lc2st, **kwargs))

# # launch batches
# with executor.batch():
#     print("Submitting jobs...", end="", flush=True)
#     tasks = []
#     for n in N_LIST:
#         kwargs = {
#             "x_samples": x_samples,
#             "n_list": [n],
#             "n_trials": 100
#         }
#         tasks.append(executor.submit(eval_clf_null, **kwargs))

executor = get_executor_marg(f"work_score_lc2st_flow")
# launch batches
with executor.batch():
    print("Submitting jobs...", end="", flush=True)
    tasks = []
    # for name, samples in zip(['good', 'bad', 'null'], [flow_values_cal_good, flow_values_cal_bad, null_samples]):
    #     kwargs = {
    #         "flow_values_cal": samples,
    #         "x_cal": x_cal,
    #         "x_obs": x_0,
    #         "flow_name": name,
    #     }
    #     tasks.append(executor.submit(score_lc2st_flow, **kwargs))
    for x_0, g in zip(x_0_list, np.linspace(-25,25,11,dtype=int)):
        kwargs = {
            "flow_values_cal": flow_values_cal_jrnmm,
            "x_cal": x_cal[:,:,0],
            "x_obs": x_0,
            "flow_name": f'jrnmm_g_{g}',
            "n_trials": 1000,
        }
        tasks.append(executor.submit(score_lc2st_flow, **kwargs))



