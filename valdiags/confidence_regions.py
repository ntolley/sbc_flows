import torch
import numpy as np


def hpd_region(
    posterior, prior, param_grid, x, confidence_level, n_p_stars=100_000, tol=0.01
):
    """High Posterior Region for learned flow posterior.
    Code adapted from WALDO git-repo."""
    if posterior is None:
        # actually using prior here; naming just for consistency (should be changed)
        posterior_probs = torch.exp(prior.log_prob(torch.from_numpy(param_grid)))
    else:
        posterior_probs = torch.exp(posterior._log_prob(inputs=param_grid, context=x))
    posterior_probs /= torch.sum(posterior_probs)  # normalize
    p_stars = np.linspace(0.99, 0, n_p_stars)  # thresholds to include or not parameters
    current_confidence_level = 1
    new_confidence_levels = []
    idx = 0
    while np.abs(current_confidence_level - confidence_level) > tol:
        if idx == n_p_stars:  # no more to examine
            break
        new_confidence_level = torch.sum(
            posterior_probs[posterior_probs >= p_stars[idx]]
        ).item()
        new_confidence_levels.append(new_confidence_level)
        if np.abs(new_confidence_level - confidence_level) < np.abs(
            current_confidence_level - confidence_level
        ):
            current_confidence_level = new_confidence_level
        idx += 1
    # all params such that p(params|x) > p_star, where p_star is the last chosen one
    return (
        current_confidence_level,
        param_grid[posterior_probs >= p_stars[idx - 1], :],
        new_confidence_levels,
    )


def waldo_confidence_region(
    posterior_samples, critical_values, param_grid, grid_sample_size
):
    """Calibrated Confidence Set for learned flow posterior using Waldo statistic.
    Code adapted from WALDO git-repo."""

    # compute posterior mean and variance
    posterior_mean = torch.mean(posterior_samples, dim=0)
    posterior_var = torch.cov(torch.transpose(posterior_samples, 0, 1))
    confidence_set_i = []
    for j in range(grid_sample_size):
        # compute waldo stats for every theta in the grid
        obs_statistics = waldo_stats(
            posterior_mean,
            posterior_var,
            param=torch.from_numpy(param_grid[j, :]).float(),
        )
        # compare to critical value
        if obs_statistics <= critical_values[j]:
            confidence_set_i.append(param_grid[j, :].reshape(1, 2))
    confidence_set = np.vstack(confidence_set_i)
    return confidence_set


def waldo_stats(posterior_mean, posterior_var, param):
    stats = torch.matmul(
        torch.matmul(
            torch.t(
                torch.subtract(posterior_mean.reshape(-1, 1), param.reshape(-1, 1))
            ),
            torch.linalg.inv(posterior_var),
        ),
        torch.subtract(posterior_mean.reshape(-1, 1), param.reshape(-1, 1)),
    ).item()
    return stats