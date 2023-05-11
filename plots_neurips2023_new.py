import numpy as np
import matplotlib.pyplot as plt

import matplotlib.pyplot as plt
from tueplots import fonts, axes
import matplotlib.gridspec as gridspec

import pandas as pd
import torch

from scipy.stats import binom, uniform

from valdiags.graphical_valdiags import (
    PP_vals,
    eval_space_with_proba_intensity,
    pp_plot_c2st,
)

# ======== FIGURE 1 ========== #
METRICS_DICT = {
    "acc_single_class": {
        "label": r"$\hat{t}_{\mathrm{Acc}_0}$",
        "color": "red",
        "linestyle": "--",
    },
    "acc_ref": {
        "label": r"$\hat{t}_{\mathrm{Acc}}$",
        "color": "red",
        "linestyle": "-",
    },
    "reg_single_class": {
        "label": r"$\hat{t}_{\mathrm{Reg}_0}$",
        "color": "orange",
        "linestyle": "--",
    },
    "reg_ref": {
        "label": r"$\hat{t}_{\mathrm{Reg}}$",
        "color": "orange",
        "linestyle": "-",
    },
    "max_single_class": {
        "label": r"$\hat{t}_{\mathrm{Max}_0}$",
        "color": "blue",
        "linestyle": "--",
    },
    "max_ref": {
        "label": r"$\hat{t}_{\mathrm{Max}}$",
        "color": "blue",
        "linestyle": "-",
    },
}


def plot_plot_c2st_single_eval_shift(
    shift_list,
    t_stats_dict,
    TPR_dict,
    TPR_std_dict,
    shift_name,
    dim,
    h0_label,
    clf_name,
):
    # plt.rcParams.update(figsizes.neurips2022(nrows=1, ncols=3, height_to_width_ratio=1))
    plt.rcParams["figure.figsize"] = (10, 5)
    plt.rcParams.update(fonts.neurips2022())
    plt.rcParams.update(axes.color(base="black"))
    plt.rcParams["legend.fontsize"] = 23.0
    plt.rcParams["xtick.labelsize"] = 23.0
    plt.rcParams["ytick.labelsize"] = 23.0
    plt.rcParams["axes.labelsize"] = 23.0
    plt.rcParams["font.size"] = 23.0
    plt.rcParams["axes.titlesize"] = 27.0

    fig, axs = plt.subplots(
        nrows=1, ncols=2, sharex=True, sharey=False, constrained_layout=True
    )
    # plot theoretical H_0 value for t-stats
    axs[0].plot(
        shift_list,
        [0.5] * len(shift_list),
        color="black",
        linestyle="--",
        label=r"$t \mid \mathcal{H}_0$",
    )
    for t_stat_name, t_stats in t_stats_dict.items():
        if "max" in t_stat_name:
            continue
        if "reg" in t_stat_name:
            t_stats = np.array(t_stats) + 0.5
            METRICS_DICT[t_stat_name]["label"] += r" (+0.5)"
        axs[0].plot(
            shift_list,
            t_stats,
            label=METRICS_DICT[t_stat_name]["label"],
            color=METRICS_DICT[t_stat_name]["color"],
            linestyle=METRICS_DICT[t_stat_name]["linestyle"],
            alpha=0.8,
        )
        axs[1].plot(
            shift_list,
            TPR_dict[t_stat_name],
            label=METRICS_DICT[t_stat_name]["label"],
            color=METRICS_DICT[t_stat_name]["color"],
            linestyle=METRICS_DICT[t_stat_name]["linestyle"],
            alpha=0.8,
            zorder=100,
        )
        err = np.array(TPR_std_dict[t_stat_name])
        axs[1].fill_between(
            shift_list,
            np.array(TPR_dict[t_stat_name]) - err,
            np.array(TPR_dict[t_stat_name]) + err,
            alpha=0.15,
            color=METRICS_DICT[t_stat_name]["color"],
        )
    if shift_name == "variance":
        axs[0].set_xlabel(r"$\sigma^2$")
        axs[1].set_xlabel(r"$\sigma^2$")
    else:
        axs[0].set_xlabel(f"{shift_name} shift")
        axs[1].set_xlabel(f"{shift_name} shift")

    # axs[0].set_ylabel("test statistic")
    axs[0].set_ylim(0.38, 1.01)
    axs[0].set_yticks([0.5, 1.0])
    axs[0].legend()
    axs[0].set_title("Optimal Bayes (statistics)")
    # axs[1].set_ylabel("empirical power")
    axs[1].set_yticks([0.0, 0.5, 1.0])
    axs[1].set_ylim(-0.02, 1.02)
    axs[1].set_title(f"{clf_name}-C2ST (power)")

    # plt.suptitle(f"{h0_label}")


# ======== FIGURE 2 ========== #

METHODS_DICT = {
    r"oracle C2ST ($\hat{t}_{Acc}$)": {
        "test_name": "c2st",
        "t_stat_name": "accuracy",
        "color": "grey",
        "linestyle": "-",
        "marker": "o",
        "markersize": 6,
    },
    r"oracle C2ST ($\hat{t}_{Reg}$)": {
        "test_name": "c2st",
        "t_stat_name": "mse",
        "color": "darkgrey",
        "linestyle": "-",
        "marker": "o",
        "markersize": 6,
    },
    r"L-C2ST ($\hat{t}_{Reg0}$)": {
        "test_name": "lc2st",
        "t_stat_name": "mse",
        "color": "orange",
        "linestyle": "-",
        "marker": "o",
        "markersize": 6,
    },
    r"L-C2ST-NF ($\hat{t}_{Reg0}$)": {
        "test_name": "lc2st_nf",
        "t_stat_name": "mse",
        "color": "orange",
        "linestyle": "-.",
        "marker": "*",
        "markersize": 10,
    },
    r"L-C2ST-NF-perm ($\hat{t}_{Reg0}$)": {
        "test_name": "lc2st_nf_perm",
        "t_stat_name": "mse",
        "color": "darkorange",
        "linestyle": "-.",
        "marker": "o",
        "markersize": 6,
    },
    r"L-C2ST ($\hat{t}_{Max0}$)": {
        "test_name": "lc2st",
        "t_stat_name": "div",
        "color": "blue",
        "linestyle": "-",
        "marker": "o",
        "markersize": 6,
    },
    r"L-C2ST-NF ($\hat{t}_{Max0}$)": {
        "test_name": "lc2st_nf",
        "t_stat_name": "div",
        "color": "blue",
        "linestyle": "-.",
        "marker": "*",
        "markersize": 10,
    },
    r"L-C2ST-NF-perm ($\hat{t}_{Max0}$)": {
        "test_name": "lc2st_nf_perm",
        "t_stat_name": "div",
        "color": "darkblue",
        "linestyle": "-.",
        "marker": "o",
        "markersize": 6,
    },
    "L-HPD": {
        "test_name": "lhpd",
        "t_stat_name": "mse",
        "color": "#3BA071",
        "linestyle": "-",
        "marker": "x",
        "markersize": 6,
    },
    "SBC": {
        "test_name": "sbc",
        "colors": ["#E697A1", "#E95b88", "#C92E45", "#490816"],
    },
}

avg_result_keys = {
    "TPR": "reject",
    "p_value_mean": "p_value",
    "p_value_std": "p_value",
    "t_stat_mean": "t_stat",
    "t_stat_std": "t_stat",
    "run_time_mean": "run_time",
    "run_time_std": "run_time",
}


def plot_sbibm_results_n_train(
    results_n_train,
    results_n_cal,
    methods_reg,
    methods_all,
    n_train_list,
    n_cal_list,
    plot_p_value=False,
):
    # plt.rcParams.update(figsizes.neurips2022(nrows=1, ncols=3, height_to_width_ratio=1))
    plt.rcParams["figure.figsize"] = (32, 5)
    plt.rcParams.update(fonts.neurips2022())
    plt.rcParams.update(axes.color(base="black"))
    plt.rcParams["legend.fontsize"] = 15.0
    plt.rcParams["xtick.labelsize"] = 23.0
    plt.rcParams["ytick.labelsize"] = 23.0
    plt.rcParams["axes.labelsize"] = 23.0
    plt.rcParams["font.size"] = 23.0
    plt.rcParams["axes.titlesize"] = 27.0

    fig, axs = plt.subplots(
        nrows=1, ncols=3, sharex=True, sharey=False, constrained_layout=True
    )
    # ==== t_stats of L-C2ST(-NF) w.r.t to oracle ====

    # plot theoretical H_0 value for reg t-stats
    axs[0].plot(
        np.arange(len(n_train_list)),
        np.ones(len(n_train_list)) * 0.0,
        "--",
        color="black",
        label=r"theoretical $t \mid \mathcal{H}_0$",
    )
    # plot estimated T values
    # for i, methods in enumerate([methods_acc, methods_reg]): # t_Max is not used in the paper
    for method in methods_reg:
        if (
            "perm" in method  # the permuation test is only used for the null hypothesis
            or "L-HPD" in method  # HPD does not have a comparable t-statistic
        ):
            continue
        test_name = METHODS_DICT[method]["test_name"]
        t_stat_name = METHODS_DICT[method]["t_stat_name"]

        axs[0].plot(
            np.arange(len(n_train_list)),
            results_n_train[test_name]["t_stat_mean"][t_stat_name],
            label=method,
            color=METHODS_DICT[method]["color"],
            linestyle=METHODS_DICT[method]["linestyle"],
            marker=METHODS_DICT[method]["marker"],
            markersize=METHODS_DICT[method]["markersize"],
            alpha=0.8,
        )
        err = np.array(results_n_train[test_name]["t_stat_std"][t_stat_name])
        axs[0].fill_between(
            np.arange(len(n_train_list)),
            np.array(results_n_train[test_name]["t_stat_mean"][t_stat_name]) - err,
            np.array(results_n_train[test_name]["t_stat_mean"][t_stat_name]) + err,
            alpha=0.2,
            color=METHODS_DICT[method]["color"],
        )
    axs[0].legend()  # loc="lower left")
    axs[0].legend()  # loc="lower left")
    axs[0].set_xticks(
        np.arange(len(n_train_list)), [r"$10^2$", r"$10^3$", r"$10^4$", r"$10^5$"]
    )
    axs[0].set_ylabel("test statistic")
    axs[0].set_ylim(0.48, 1.02)
    axs[0].set_yticks([0.5, 0.75, 1.0])
    axs[0].set_ylabel("test statistic")
    axs[0].set_ylim(-0.01, 0.26)
    axs[0].set_yticks([0.0, 0.12, 0.25])
    axs[0].set_xlabel(r"$N_{\mathrm{train}}$")

    if plot_p_value:
        # ==== p-value of all methods w.r.t to oracle ===

        # plot alpha-level
        axs[1].plot(
            np.arange(len(n_train_list)),
            np.ones(len(n_train_list)) * 0.05,
            "--",
            color="black",
            label="alpha-level: 0.05",
        )

        # plot estimated p-values
        for method in methods_all:
            if "Max" in method:
                continue  # t_Max is not used in the paper

            test_name = METHODS_DICT[method]["test_name"]
            t_stat_name = METHODS_DICT[method]["t_stat_name"]
            axs[1].plot(
                np.arange(len(n_train_list)),
                results_n_train[test_name]["p_value_mean"][t_stat_name],
                label=method,
                color=METHODS_DICT[method]["color"],
                linestyle=METHODS_DICT[method]["linestyle"],
                marker=METHODS_DICT[method]["marker"],
                markersize=METHODS_DICT[method]["markersize"],
                alpha=0.8,
            )
            low = np.array(results_n_train[test_name]["p_value_min"][t_stat_name])
            high = np.array(results_n_train[test_name]["p_value_max"][t_stat_name])
            axs[1].fill_between(
                np.arange(len(n_train_list)),
                low,
                high,
                alpha=0.2,
                color=METHODS_DICT[method]["color"],
            )
        axs[1].legend(loc="upper left")
        axs[1].set_xticks(
            np.arange(len(n_train_list)), [r"$10^2$", r"$10^3$", r"$10^4$", r"$10^5$"]
        )
        # axs[1].set_xlabel(r"$N_{\mathrm{train}}$")
        axs[1].set_ylabel("p-value (min / max)")

    else:
        # plot rejection rate of all methods w.r.t to oracle
        for method in methods_all:
            if "Max" in method:
                continue  # t_Max is not used in the paper

            test_name = METHODS_DICT[method]["test_name"]
            t_stat_name = METHODS_DICT[method]["t_stat_name"]

            axs[1].plot(
                np.arange(len(n_train_list)),
                results_n_train[test_name]["TPR"][t_stat_name],
                # label=method,
                color=METHODS_DICT[method]["color"],
                linestyle=METHODS_DICT[method]["linestyle"],
                marker=METHODS_DICT[method]["marker"],
                markersize=METHODS_DICT[method]["markersize"],
                alpha=0.8,
            )
            # add std over runs

        # axs[1][1].legend(loc="lower left")
        axs[1].set_xticks(
            np.arange(len(n_train_list)), [r"$10^2$", r"$10^3$", r"$10^4$", r"$10^5$"]
        )
        axs[1].set_ylim(-0.04, 1.04)
        axs[1].set_yticks([0, 0.5, 1])
        axs[1].set_xlabel(r"$N_{\mathrm{train}}$")
        axs[1].set_ylabel("rejection rate")

    # plot emp power as function of n_cal
    for axi, result_name in zip([axs[2], axs[3]], ["TPR", "FPR"]):
        for method in methods_all:
            if "Max" in method:
                continue
            test_name = METHODS_DICT[method]["test_name"]
            t_stat_name = METHODS_DICT[method]["t_stat_name"]
            axi.plot(
                np.arange(len(n_cal_list)),
                results_n_cal[result_name]["mean"][method][t_stat_name],
                # label=method,
                color=METHODS_DICT[method]["color"],
                linestyle=METHODS_DICT[method]["linestyle"],
                marker=METHODS_DICT[method]["marker"],
                markersize=METHODS_DICT[method]["markersize"],
                alpha=0.8,
            )
            err = np.array(results_n_cal[result_name]["std"][method][t_stat_name])
            axi.fill_between(
                np.arange(len(n_cal_list)),
                np.array(results_n_cal[result_name]["mean"][method][t_stat_name]) - err,
                np.array(results_n_cal[result_name]["mean"][method][t_stat_name]) + err,
                alpha=0.2,
            )
        # add emp power as function of n_cal
        axi.set_xlabel(r"N_{\mathrm{cal}}")
        axi.set_xticks(
            np.arange(len(n_cal_list)),
            [r"$100$", r"$500$", r"$1000$", r"$2000$", r"$5000$", r"$10000$"],
        )
    axs[2].set_ylabel(r"power (TPR)")
    axs[2].set_ylim(-0.04, 1.04)
    axs[2].set_yticks([0, 0.5, 1])

    axs[3].set_ylabel(r"type I error (FPR)")
    axs[3].set_ylim(-0.04, 0.14)
    axs[3].set_yticks([0, 0.05, 0.1])

    return fig


### ======== FIGURE 3 ========== ###


def global_coverage_pp_plots(
    multi_PIT_values,
    alphas,
    sbc_ranks,
    labels_sbc,
    colors_sbc=METHODS_DICT["SBC"]["colors"],
    colors_pit=None,
    labels_pit=None,
    ylabel_pit=r"empirical $r_{i,\alpha} = \mathbb{P}(P_{i}\leq \alpha)$",
    ylabel_sbc=r"empirical CDF",
    confidence_int=True,
    conf_alpha=0.05,
    n_trials=1000,
    hpd_ranks=None,
):
    # plt.rcParams.update(figsizes.neurips2022(nrows=1, ncols=3, height_to_width_ratio=1))
    plt.rcParams["figure.figsize"] = (10, 5)
    plt.rcParams.update(fonts.neurips2022())
    plt.rcParams.update(axes.color(base="black"))
    plt.rcParams["legend.fontsize"] = 18.0
    plt.rcParams["legend.title_fontsize"] = 18.0
    plt.rcParams["xtick.labelsize"] = 23.0
    plt.rcParams["ytick.labelsize"] = 23.0
    plt.rcParams["axes.labelsize"] = 23.0
    plt.rcParams["font.size"] = 23.0
    plt.rcParams["axes.titlesize"] = 27.0

    if multi_PIT_values is None:
        n_cols = 2
        ax_sbc = 0
        ax_hpd = 1
        plt.rcParams["figure.figsize"] = (10, 5)
    else:
        n_cols = 3
        ax_sbc = 1
        ax_hpd = 2
        plt.rcParams["figure.figsize"] = (15, 5)

    fig, axs = plt.subplots(
        nrows=1, ncols=n_cols, sharex=True, sharey=True, constrained_layout=False
    )

    for i, ax in enumerate(axs):
        # plot identity function
        lims = [np.min([0, 0]), np.max([1, 1])]
        ax.plot(lims, lims, "--", color="black", alpha=0.75)
        if confidence_int:
            if i == 0:
                conf_alpha = conf_alpha / len(sbc_ranks[0])  # bonferonni correction
            # Construct uniform histogram.
            N = len(sbc_ranks)
            u_pp_values = {}
            for t in range(n_trials):
                u_samples = uniform().rvs(N)
                u_pp_values[t] = pd.Series(PP_vals(u_samples, alphas))
            lower_band = pd.DataFrame(u_pp_values).quantile(q=conf_alpha / 2, axis=1)
            upper_band = pd.DataFrame(u_pp_values).quantile(
                q=1 - conf_alpha / 2, axis=1
            )

            ax.fill_between(alphas, lower_band, upper_band, color="grey", alpha=0.3)

        ax.set_aspect("equal")

    # global pit
    if multi_PIT_values is not None:
        for i, Z in enumerate(multi_PIT_values):
            # compute quantiles P_{target}(PIT_values <= alpha)
            pp_vals = PP_vals(Z, alphas)
            # Plot the quantiles as a function of alpha
            axs[0].plot(
                alphas, pp_vals, color=colors_pit[i], label=labels_pit[i], linewidth=2
            )

        axs[0].set_yticks([0.0, 0.5, 1.0])
        axs[0].set_ylabel(ylabel_pit)
        axs[0].set_xlabel(r"$\alpha$")
        axs[0].set_title("Global PIT")
        axs[0].legend(loc="upper left")

    # sbc ranks
    for i in range(len(sbc_ranks[0])):
        sbc_cdf = np.histogram(sbc_ranks[:, i], bins=len(alphas))[0].cumsum()
        axs[ax_sbc].plot(
            alphas,
            sbc_cdf / sbc_cdf.max(),
            color=colors_sbc[i],
            label=labels_sbc[i],
            linewidth=2,
        )

    axs[ax_sbc].set_yticks([0.0, 0.5, 1.0])
    axs[ax_sbc].set_ylabel(ylabel_sbc)
    axs[ax_sbc].set_ylim(0, 1)
    axs[ax_sbc].set_xlim(0, 1)
    # axs[ax_sbc].set_xlabel(r"posterior rank $\theta_i$")
    axs[ax_sbc].set_title("SBC")
    axs[ax_sbc].legend(
        loc="upper left",
        title=r"$\mathrm{SBC}(\theta_i,x)$",
    )

    # hpd_values
    if hpd_ranks is not None:
        alphas = torch.linspace(0.0, 1.0, len(hpd_ranks))
        axs[ax_hpd].plot(
            alphas,
            hpd_ranks,
            color=METHODS_DICT["L-HPD"]["color"],
            label=r"$\mathrm{HPD}(\mathbf{\theta}, x)$",
        )
        # axs[ax_hpd].set_ylabel("empirical CDF")  # MC-est. $\mathbb{P}(HPD \leq \alpha)$
        axs[ax_hpd].set_ylim(0, 1)
        axs[ax_hpd].set_xlim(0, 1)
        # axs[ax_hpd].set_xlabel(r"$\alpha$")
        axs[ax_hpd].set_title("Expected HPD")
        axs[ax_hpd].legend(loc="upper left")

    return fig


def local_coverage_gain_plots(
    gain_dict,
    t_stats_obs,
    t_stats_obs_null,
    gain_list_pp_plots,
    probas_obs,
    probas_obs_null,
    p_values_obs,
    methods=[r"L-C2ST-NF ($\hat{t}_{Reg0}$)"],
    colors_g0=["#32327B", "#3838E2", "#52A9F5"],
):
    # plt.rcParams.update(
    #     figsizes.neurips2022(nrows=2, ncols=3, height_to_width_ratio=1,)
    # )
    plt.rcParams["figure.figsize"] = (10, 10)
    plt.rcParams.update(fonts.neurips2022())
    plt.rcParams.update(axes.color(base="black"))
    plt.rcParams["legend.fontsize"] = 23.0
    plt.rcParams["xtick.labelsize"] = 23.0
    plt.rcParams["ytick.labelsize"] = 23.0
    plt.rcParams["axes.labelsize"] = 23.0
    plt.rcParams["font.size"] = 23.0
    plt.rcParams["axes.titlesize"] = 27.0

    fig = plt.figure(figsize=(10, 10), constrained_layout=True)
    gs = gridspec.GridSpec(2, 3)

    ax = fig.add_subplot(gs[0, :])

    ax0 = fig.add_subplot(gs[1, 0])
    ax1 = fig.add_subplot(gs[1, 1], sharex=ax0)
    ax2 = fig.add_subplot(gs[1, 2], sharex=ax0)
    axes1 = [ax0, ax1, ax2]

    for ax1 in [ax1, ax2]:
        ax1.set_yticklabels([])
        ax1.set_xticks([0.0, 0.5, 1.0])

    # test statistics
    gain_list_t_stats = list(gain_dict.keys())
    for method in methods:
        method_name = METHODS_DICT[method]["test_name"]
        t_stat_name = METHODS_DICT[method]["t_stat_name"]
        t_stats = np.array(
            [
                t_stats_obs[method_name][t_stat_name][i]
                for i in range(len(gain_list_t_stats))
            ]
        )
        t_stats_null_low = np.array(
            [
                np.quantile(t_stats_obs_null[method_name][g][t_stat_name], q=0.05 / 2)
                for g in gain_list_t_stats
            ]
        )
        t_stats_null_high = np.array(
            [
                np.quantile(
                    t_stats_obs_null[method_name][g][t_stat_name], q=1 - 0.05 / 2
                )
                for g in gain_list_t_stats
            ]
        )
        ax.fill_between(
            gain_list_t_stats,
            t_stats_null_low,
            t_stats_null_high,
            alpha=0.3,
            color="grey",
        )
        # if t_stat_name == "mse":
        #     t_stats = t_stats + 0.5
        ax.plot(
            gain_list_t_stats,
            t_stats,
            label=method,
            color=METHODS_DICT[method]["color"],
            linestyle=METHODS_DICT[method]["linestyle"],
            marker=METHODS_DICT[method]["marker"],
            markersize=METHODS_DICT[method]["markersize"],
            alpha=0.8,
        )
    ax.plot(
        gain_list_t_stats,
        np.ones(len(gain_list_t_stats)) * 0.0,
        "--",
        color="black",
        label=r"theoretical $\mathcal{H}_0$",
    )

    ax.yaxis.set_tick_params(which="both", labelleft=True)
    ax.set_xticks(gain_list_t_stats)
    # ax.set_yticks(
    #     np.round(
    #         np.linspace(0, np.max(t_stats_obs["lc2st_nf"].values), 5, endpoint=False), 2
    #     )
    # )

    ax.set_xlabel(r"$g_0$")
    ax.set_ylabel(r"$\hat{t}(x_0)$")

    ax.set_title("Local Test statistics")

    # pp-plots
    method = r"L-C2ST-NF ($\hat{t}_{Reg0}$)"
    method_name = METHODS_DICT[method]["test_name"]
    t_stat_name = METHODS_DICT[method]["t_stat_name"]
    probas_obs = probas_obs[method_name]
    probas_obs_null = probas_obs_null[method_name]
    p_values_obs = p_values_obs[method_name][t_stat_name]
    for n, (axs1, g) in enumerate(zip(axes1, gain_list_pp_plots)):
        pp_plot_c2st(
            ax=axs1,
            probas=[probas_obs[g]],
            probas_null=probas_obs_null[g],
            colors=[colors_g0[n]],
            labels=[""],
        )
        axs1.text(
            0.0,
            0.9,
            r"$g_0=$" + f"{g}",  # + "\n" + r"$p-value=$" + f"{p_values_obs[num_g]}",
            fontsize=23,
        )
        plt.setp(axs1.spines.values(), color=colors_g0[n])

        # axs1.set_xlabel(r"$\alpha$", fontsize=23)
        if n == 1:
            axs1.set_title(
                r"Local PP-plots"  # for class 0: $1-\hat{d}(Z,x_0), Z\sim \mathcal{N}(0,1)$"
            )
            # axs1.legend(loc="lower right")
    axes1[0].set_ylabel("empirical CDF")
    axes1[0].set_yticks([0.0, 0.5, 1.0])

    handles_1 = ax.get_legend_handles_labels()
    handles_2 = axs1.get_legend_handles_labels()
    ax.legend(
        handles=handles_1[0] + handles_2[0],
        # title="1D-plots for",
        loc="upper right",
        # bbox_to_anchor=ax.get_position().get_points()[1]
        # + np.array([1.6, -0.08]),
    )

    # plt.subplots_adjust(wspace=None, hspace=0.4)

    for ax1 in axes1:
        ax1.set_aspect("equal")
    # ax.set_aspect("equal")
    # for j in [0, 2]:
    #     axes[0][j].set_visible(False)
    ax.set_xlim(-20.1, 20.1)
    # fig.align_ylabels()

    return fig


# Simulator parameters
PARAMETER_DICT = {
    0: {"label": r"$C$", "low": 10.0, "high": 300.0, "ticks": [100, 250]},
    1: {"label": r"$\mu$", "low": 50.0, "high": 500.0, "ticks": [200, 400]},
    2: {"label": r"$\sigma$", "low": 100.0, "high": 5000.0, "ticks": [1000, 3500]},
    3: {"label": r"$g$", "low": -22.0, "high": 22.0, "ticks": [-20, 0, 20]},
}


def plot_pairgrid_with_groundtruth_and_proba_intensity_lc2st(
    posterior,
    theta_gt,
    observation,
    trained_clfs_lc2st,
    scores_fn_lc2st,
    probas_null_obs_lc2st,
    n_samples=10000,
    n_bins=20,
):
    plt.rcParams["figure.figsize"] = (9, 9)
    plt.rcParams.update(fonts.neurips2022())
    plt.rcParams.update(axes.color(base="black"))
    plt.rcParams["legend.fontsize"] = 23.0
    plt.rcParams["xtick.labelsize"] = 23.0
    plt.rcParams["ytick.labelsize"] = 23.0
    plt.rcParams["axes.labelsize"] = 23.0
    plt.rcParams["font.size"] = 23.0
    plt.rcParams["axes.titlesize"] = 27.0

    fig, axs = plt.subplots(
        nrows=4, ncols=4, sharex=False, sharey=False, constrained_layout=False
    )

    samples_z = posterior._flow._distribution.sample(n_samples).detach()
    observation_emb = posterior._flow._embedding_net(observation)
    samples_theta = posterior._flow._transform.inverse(samples_z, observation_emb)[
        0
    ].detach()

    _, probas = scores_fn_lc2st(
        P=None,
        Q=None,
        x_P=None,
        x_Q=None,
        x_eval=observation[:, :, 0],
        P_eval=samples_z,
        trained_clfs=trained_clfs_lc2st,
    )

    for i in range(4):
        eval_space_with_proba_intensity(
            probas=probas,
            probas_null=probas_null_obs_lc2st,
            P_eval=samples_theta[:, i].numpy().reshape(-1, 1),
            dim=1,
            z_space=False,
            n_bins=n_bins,
            ax=axs[i][i],
            show_colorbar=False,
        )

        # plot ground truth dirac
        axs[i][i].axvline(x=theta_gt[i], ls="--", c="black", linewidth=1)

        for j in range(i + 1, 4):
            eval_space_with_proba_intensity(
                probas=probas,
                probas_null=probas_null_obs_lc2st,
                P_eval=samples_theta[:, [i, j]].numpy(),
                dim=2,
                z_space=False,
                n_bins=n_bins,
                ax=axs[j][i],
                show_colorbar=False,
                scatter=False,
            )
            # plot points
            axs[j][i].scatter(theta_gt[i], theta_gt[j], color="black", s=8)

            axs[i][j].set_visible(False)

    cmap = plt.cm.get_cmap("bwr")
    from matplotlib import cm

    plt.subplots_adjust(bottom=0.1, right=0.8, top=0.9)
    cax = plt.axes([0.82, 0.1, 0.075, 0.8])
    plt.colorbar(
        cm.ScalarMappable(cmap=cmap),
        cax=cax,
        label=r"L-C2ST class-0 probability: $1-\hat{d}(Z ; x_0)$",
    )

    fig.suptitle(
        r"Pair-plots of $q_{\phi}(\theta \mid x_0)$: "
        + "\n"
        + r"$\Theta = T_{\phi}(Z ; x_0), \quad Z\sim \mathcal{N}(0,\mathbf{1}_4)$",
        y=1.0,
    )

    # set value range
    axs[0][0].set_yticks([])
    axs[3][3].set_xticks(PARAMETER_DICT[3]["ticks"])

    for j in range(4):
        if j != 0:
            axs[j][0].set_ylabel(PARAMETER_DICT[j]["label"])
            axs[j][0].set_xlim(PARAMETER_DICT[0]["low"], PARAMETER_DICT[0]["high"])
            axs[j][0].set_xticks(PARAMETER_DICT[0]["ticks"])
        axs[3][j].set_xlabel(PARAMETER_DICT[j]["label"])
        for i in range(4):
            if j != 3:
                axs[j][i].set_xticklabels([])
            if i != 0:
                axs[j][i].set_yticklabels([])
            if i != j:
                axs[j][i].set_ylim(PARAMETER_DICT[j]["low"], PARAMETER_DICT[j]["high"])
                axs[j][i].set_yticks(PARAMETER_DICT[j]["ticks"])

            axs[j][i].set_xlim(PARAMETER_DICT[i]["low"], PARAMETER_DICT[i]["high"])
            axs[j][i].set_xticks(PARAMETER_DICT[i]["ticks"])

    return fig
