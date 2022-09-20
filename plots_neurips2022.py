import matplotlib.pyplot as plt
from tueplots import figsizes, fonts, fontsizes


import numpy as np
import pandas as pd
import torch
import seaborn as sns

from scipy.stats import binom

from diagnostics.pp_plots import PP_vals
from diagnostics.multi_local_test import get_lct_results


def multi_global_consistency(
    multi_PIT_values,
    alphas,
    sbc_ranks,
    labels,
    colors,
    ylabel_pit=r"empirical $r_{i,\alpha}$",
    ylabel_sbc="empirical CDF",
):
    # plt.rcParams.update(figsizes.neurips2022(nrows=1, ncols=3, height_to_width_ratio=1))
    plt.rcParams["figure.figsize"] = (12, 6)
    plt.rcParams.update(fonts.neurips2022())
    plt.rcParams["legend.fontsize"] = 15.0
    plt.rcParams["xtick.labelsize"] = 15.0
    plt.rcParams["ytick.labelsize"] = 15.0
    plt.rcParams["axes.labelsize"] = 15.0
    plt.rcParams["font.size"] = 15.0
    plt.rcParams["axes.titlesize"] = 18.0

    fig, axes = plt.subplots(
        nrows=1, ncols=2, sharex=True, sharey=True, constrained_layout=False
    )

    for i, ax in enumerate(axes):
        if i > 1:
            ax.set_visible(False)
        # plot identity function
        lims = [np.min([0, 0]), np.max([1, 1])]
        ax.plot(lims, lims, "--", color="black", alpha=0.75)

        # Construct uniform histogram.
        N = len(multi_PIT_values[0])
        nbins = len(alphas)
        hb = binom(N, p=1 / nbins).ppf(0.5) * np.ones(nbins)
        hbb = hb.cumsum() / hb.sum()
        # avoid last value being exactly 1
        hbb[-1] -= 1e-9

        lower = [binom(N, p=p).ppf(0.005) for p in hbb]
        upper = [binom(N, p=p).ppf(0.995) for p in hbb]

        # Plot grey area with expected ECDF.
        ax.fill_between(
            x=np.linspace(0, 1, nbins),
            y1=np.repeat(lower / np.max(lower), 1),
            y2=np.repeat(upper / np.max(lower), 1),
            color="grey",
            alpha=0.3,
        )
        ax.set_aspect("equal")

    # sbc ranks
    for i in range(len(sbc_ranks[0])):
        sbc_cdf = np.histogram(sbc_ranks[:, i], bins=len(alphas))[0].cumsum()
        axes[0].plot(alphas, sbc_cdf / sbc_cdf.max(), color=colors[i], label=labels[i])

    axes[0].set_ylabel(ylabel_sbc)
    axes[0].set_xlabel("ranks")
    axes[0].set_title("SBC")
    axes[0].legend(title="1D-plots for", loc="upper left")

    # global pit
    for i, Z in enumerate(multi_PIT_values):
        # compute quantiles P_{target}(PIT_values <= alpha)
        pp_vals = PP_vals(Z, alphas)
        # Plot the quantiles as a function of alpha
        axes[1].plot(alphas, pp_vals, color=colors[i], label=labels[i])

    axes[1].set_ylabel(ylabel_pit)
    axes[1].set_xlabel(r"$\alpha$")
    axes[1].set_title("Global PIT")
    return fig


def multi_local_consistency(
    lct_path_list,
    gain_list,
    colors,
    labels,
    colors_g0=["#32327B", "#3838E2", "#52A9F5"],
):

    # plt.rcParams.update(
    #     figsizes.neurips2022(nrows=2, ncols=3, height_to_width_ratio=1,)
    # )
    plt.rcParams["figure.figsize"] = (20, 8)
    plt.rcParams.update(fonts.neurips2022())
    plt.rcParams["legend.fontsize"] = 15.0
    plt.rcParams["xtick.labelsize"] = 15.0
    plt.rcParams["ytick.labelsize"] = 15.0
    plt.rcParams["axes.labelsize"] = 15.0
    plt.rcParams["font.size"] = 15.0
    plt.rcParams["axes.titlesize"] = 18.0

    fig, axes = plt.subplots(
        nrows=2, ncols=5, constrained_layout=False, sharex="row", sharey="row"
    )

    for ax in axes:
        ax[-2].set_visible(False)
        ax[-1].set_visible(False)

    # axes1 = subfigs[0].subplots(nrows=1, ncols=3)

    # test statistics
    df_lct_results = get_lct_results(lct_path_list, pvalues=False)
    df_lct_results.index = gain_list
    for i in range(1, 5):
        axes[0][1].plot(
            gain_list,
            df_lct_results[f"dim_{i}"],
            marker="o",
            markersize=1,
            color=colors[i - 1],
            label=labels[i - 1],
            linewidth=1,
        )

    axes[0][1].yaxis.set_tick_params(which="both", labelleft=True)
    axes[0][1].set_xticks([gain_list[i] for i in [0, 2, 4, 6, 8]])
    axes[0][1].set_yticks(
        np.round(np.linspace(0, np.max(df_lct_results.values), 5, endpoint=False), 2)
    )

    axes[0][1].set_xlabel(r"$g_0$")
    axes[0][1].set_ylabel(r"$T_i(x_0)$")
    # axes1[1].legend()
    handles = axes[0][1].get_legend_handles_labels()
    axes[0][1].legend(
        handles=handles[0],
        title="1D-plots for",
        # loc="upper right",
        bbox_to_anchor=axes[0][1].get_position().get_points()[1]
        + np.array([1.6, -0.08]),
    )

    axes[0][1].set_title("Local Test statistics")

    # pp-plots
    # axes = subfigs[1].subplots(nrows=1, ncols=3, sharex=True, sharey=True)

    for n, (x0, g0) in enumerate(zip([0, 4, 8], [-20, 0, 20])):
        r_alpha_x0 = torch.load(lct_path_list[x0])["r_alpha_learned"]
        # plot identity function
        lims = [np.min([0, 0]), np.max([1, 1])]
        axes[1][n].plot(lims, lims, "--", color="black", alpha=0.75)
        # plot pp-plots
        for i in range(1, 5):
            axes[1][n].plot(
                np.linspace(0, 1, 100),
                pd.Series(r_alpha_x0[f"dim_{i}"]),
                color=colors[i - 1],
                marker="o",
                markersize=1,
                linestyle="",
            )
        axes[1][n].set_xlabel(r"$\alpha$", fontsize=15)
        if n == 1:
            axes[1][n].set_title("Local PP-plots", y=-0.3)
        axes[1][n].text(0.05, 0.95, r"$g_0=$" + f"{g0}", fontsize=15)
        plt.setp(axes[1][n].spines.values(), color=colors_g0[n])
    axes[1][0].set_ylabel(r"$\hat{r}_{i,\alpha}(x_0)$")

    for ax in axes[1]:
        ax.set_aspect("equal")
        ax.set_aspect("equal")
        ax.set_aspect("equal")

    # for ax in axes1:
    #     ax.set_aspect("equal")

    for j in [0, 2]:
        axes[0][j].set_visible(False)

    return fig


def plot_pairgrid_with_groundtruth(
    posteriors, theta_gt, color_dict, handles, context, n_samples=10000, title=None
):
    plt.rcParams["figure.figsize"] = (20, 8)
    plt.rcParams.update(fonts.neurips2022())
    plt.rcParams["legend.fontsize"] = 15.0
    plt.rcParams["xtick.labelsize"] = 15.0
    plt.rcParams["ytick.labelsize"] = 15.0
    plt.rcParams["axes.labelsize"] = 15.0
    plt.rcParams["font.size"] = 15.0
    plt.rcParams["axes.titlesize"] = 18.0

    modes = list(posteriors.keys())
    dfs = []
    for n in range(len(posteriors)):
        posterior = posteriors[modes[n]]
        if modes[n] == "prior":
            samples = posterior.sample(n_samples, context=context[modes[n]])
        else:
            samples = posterior.sample(n_samples, context=context[modes[n]])
        df = pd.DataFrame(
            samples.detach().numpy(), columns=[r"$C$", r"$\mu$", r"$\sigma$", r"$g$"]
        )
        df["mode"] = modes[n]
        dfs.append(df)

    joint_df = pd.concat(dfs, ignore_index=True)

    g = sns.PairGrid(
        joint_df, hue="mode", palette=color_dict, diag_sharey=False, corner=True
    )
    g.fig.set_size_inches(6, 6)

    g.map_lower(sns.kdeplot, linewidths=1)
    g.map_diag(sns.kdeplot, shade=True, linewidths=1)

    g.axes[1][0].set_xlim(10.0, 300.0)  # C
    g.axes[1][0].set_ylim(50.0, 500.0)  # mu
    # g.axes[1][0].set_xticks([])

    g.axes[2][0].set_xlim(10.0, 300.0)  # C
    g.axes[2][0].set_ylim(100.0, 5000.0)  # sigma
    # g.axes[2][0].set_xticks([])

    g.axes[2][1].set_xlim(50.0, 500.0)  # mu
    g.axes[2][1].set_ylim(100.0, 5000.0)  # sigma
    # g.axes[2][1].set_xticks([])

    g.axes[3][0].set_xlim(10.0, 300.0)  # C
    g.axes[3][0].set_ylim(-20.0, 20.0)  # gain
    g.axes[3][0].set_yticks([-20, 0, 20])

    g.axes[3][1].set_xlim(50.0, 500.0)  # mu
    g.axes[3][1].set_ylim(-20.0, 20.0)  # gain
    g.axes[3][1].set_xticks([200, 400])

    g.axes[3][2].set_xlim(100.0, 5000.0)  # sigma
    g.axes[3][2].set_ylim(-20.0, 20.0)  # gain
    g.axes[3][2].set_xticks([2000, 4000])

    g.axes[3][3].set_xlim(-20.0, 20.0)  # gain

    if theta_gt is not None:
        # get groundtruth parameters
        for gt in theta_gt:
            C, mu, sigma, gain = gt

            # plot points
            g.axes[1][0].scatter(C, mu, color="black", zorder=2, s=8)
            g.axes[2][0].scatter(C, sigma, color="black", zorder=2, s=8)
            g.axes[2][1].scatter(mu, sigma, color="black", zorder=2, s=8)
            g.axes[3][0].scatter(C, gain, color="black", zorder=2, s=8)
            g.axes[3][1].scatter(mu, gain, color="black", zorder=2, s=8)
            g.axes[3][2].scatter(sigma, gain, color="black", zorder=2, s=8)

            # plot dirac
            g.axes[0][0].axvline(x=C, ls="--", c="black", linewidth=1)
            g.axes[1][1].axvline(x=mu, ls="--", c="black", linewidth=1)
            g.axes[2][2].axvline(x=sigma, ls="--", c="black", linewidth=1)
            g.axes[3][3].axvline(x=gain, ls="--", c="black", linewidth=1)

    plt.legend(
        handles=handles,
        title=title,
        bbox_to_anchor=(1.1, 4.3),
        # loc="upper right",
    )
    g.fig.suptitle("Local pair-plots", y=1.05)

    return g

