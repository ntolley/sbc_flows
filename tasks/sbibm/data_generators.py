import torch
import numpy as np

from copy import deepcopy
from tqdm import tqdm

from .npe_utils import inv_flow_transform_obs, sample_from_npe_obs
from joblib import Parallel, delayed


def generate_task_data(
    n_samples,
    task,
    num_observation_list,
    observation_list=None,
    sample_from_joint=True,
    sample_from_reference=True,
    paralellize=False,
):
    """Generate data for a given task.
    This data is fixed and independent of the used sbi-algorithm.

    Args:
        n_samples (int): Number of samples to generate
        task (str): sbibm task name
        num_observation_list: List of observation numbers for which we want to sample
            from the reference posterior.
        observation_list: List of observations for which we want to sample
            from the reference posterior. If None, the observations are loaded
            using the observation numbers.
            DEFAULT: None
        sample_from_joint (bool): If True, samples from the joint distribution
            (prior x simulator) are generated.
            DEFAULT: True
        sample_from_reference (bool): If True, samples from the reference posterior
            are generated.
            DEFAULT: True
        paralellize (bool): If True, the reference data generation is paralellized over observations.
            DEFAULT: False
    """

    # Get simulator and prior
    task = deepcopy(task)
    simulator = task.get_simulator()
    prior = task.get_prior()

    # Generate data from joint
    if sample_from_joint:
        theta = prior(num_samples=n_samples)
        x = simulator(theta)
    else:
        theta = None
        x = None

    # Generate data from reference posterior
    if sample_from_reference:
        print("Samples from reference posterior:")
        reference_posterior_samples = {}

        if observation_list is None:
            observation_list = [None] * len(num_observation_list)

        if num_observation_list is None:
            num_observation_list = [None] * len(observation_list)

        def sample(num_obs):
            print(num_obs)
            try:
                ref_samples = task._sample_reference_posterior(
                    num_samples=n_samples,
                    num_observation=num_obs,
                    observation=None,
                )
            except TypeError:
                ref_samples = task._sample_reference_posterior(
                    num_samples=n_samples,
                    num_observation=num_obs,
                )
            except ValueError:
                print("Observation not available. Generating new observation.")
                seed = task.observation_seeds[-1] + 1 + num_obs
                task._save_observation_seed(num_obs, seed)
                np.random.seed(seed)
                torch.manual_seed(seed)
                theta = prior(num_samples=1)
                task._save_true_parameters(num_obs, theta)
                observation = simulator(theta)
                task._save_observation(num_obs, observation)

                ref_samples = task._sample_reference_posterior(
                    num_samples=n_samples,
                    num_observation=num_obs,
                    observation=observation,
                )

            return ref_samples

        if paralellize:
            list_results = Parallel(
                n_jobs=len(num_observation_list), verbose=50, backend="loky"
            )(delayed(sample)(num_obs) for num_obs in num_observation_list)
            print(list_results)
            for num_obs, result in zip(num_observation_list, list_results):
                reference_posterior_samples[num_obs] = result
        else:
            for i, (num_obs, obs) in enumerate(
                zip(num_observation_list, observation_list)
            ):
                print()
                print(f"Observation {i+1}")
                if num_obs is None:
                    num_obs = i + 1
                    try:
                        reference_posterior_samples[
                            num_obs
                        ] = task._sample_reference_posterior(
                            num_samples=n_samples, num_observation=None, observation=obs
                        )
                    except AssertionError:
                        print(
                            f"Observation {num_obs} not available. Using observation {num_obs-1} instead."
                        )
                        reference_posterior_samples[
                            num_obs
                        ] = reference_posterior_samples[num_obs - 1]
                else:
                    reference_posterior_samples[num_obs] = sample(num_obs)

    else:
        reference_posterior_samples = None

    return reference_posterior_samples, theta, x


def generate_npe_data_for_c2st(
    npe,
    base_dist_samples,
    reference_posterior_samples,
    observation_list,
    nf_case=True,
):
    """Generate data for a given task and npe-flow that is used in the C2ST(-NF) methods.
            - sample from the npe at given observations (using the forward flow transformation)
                (C2ST compares them to the reference posterior samples),
            - compute inverse npe-flow-transformation on reference posterior samples
                (C2ST-NF compares them to the samples from the base distribution (normal))
        This data is dependent on the flow defining the npe.

    Args:
        npe (sbi.DirectPosterior): neural posterior estimator (normalizing flow).
        base_dist_samples (torch.Tensor): samples from the base distribution of the
            flow. This is used to generate flow samples.
        reference_posterior_samples (dict): dict of samples from the reference posterior
            for the considered observations. The dict keys are the observation numbers.
            The dict values are torch tensors of shape (n_samples, dim)
        observation_list (list): list of observations the reference posterior samples correspond to.
            observation = task.get_observation(num_observation)
    """
    npe_samples_obs = {}
    reference_inv_transform_samples = {}
    for i, observation in tqdm(
        enumerate(observation_list),
        desc="Computing npe-dependant samples for every observation x_0",
    ):
        # Set default x_0 for npe
        npe.set_default_x(observation)
        # Sample from npe at x_0
        npe_samples_obs[i + 1] = sample_from_npe_obs(
            npe=npe, observation=observation, base_dist_samples=base_dist_samples
        )
        # Compute inverse flow transformation of npe on reference posterior samples at x_0
        if nf_case and reference_posterior_samples is not None:
            reference_inv_transform_samples[i + 1] = inv_flow_transform_obs(
                reference_posterior_samples[i + 1],
                observation,
                npe.posterior_estimator,
            )
        else:
            reference_inv_transform_samples[i + 1] = None
    return npe_samples_obs, reference_inv_transform_samples


def generate_npe_data_for_lc2st(
    npe,
    base_dist_samples,
    joint_samples,
    nf_case=True,
):
    """Generate data for a given task and npe that is used in the LC2ST(-NF) methods.
        - sample from the npe for every observation x in `joint_samples` (using the forward-flow transformation).
            (LC2ST compares them to the joint samples [theta, x]),
        - compute inverse npe-flow-transformation on the joint samples
            (LC2ST-NF compares them to the samples from the base distribution (z),
            concatenated with x: [z,x])
    This data is dependent on the flow.

    Args:
        npe (sbi.DirectPosterior): neural posterior estimator.
        joint_samples (dict[torch.Tensor]): dict of samples from the joint distribution of the
            flow: {'theta':theta, 'x':x} where
                - theta is a torch.Tensor of shape (n_samples, dim)
                - x is a torch.Tensor of shape (n_samples, dim_x)
        base_dist_samples (torch.Tensor): samples from the base distribution of the
            npe-flow. This is used to generate flow samples.
            of shape (n_samples, dim)
    """
    npe_samples_joint = []
    inv_transform_samples_joint = []
    for theta, x, z in tqdm(
        zip(joint_samples["theta"], joint_samples["x"], base_dist_samples),
        desc=f"Computing npe-dependant samples for every x in joint dataset",
    ):
        x, theta, z = x[None, :], theta[None, :], z[None, :]

        # Sample from flow
        npe_samples_joint.append(
            sample_from_npe_obs(npe=npe, observation=x, base_dist_samples=z)
        )
        # Compute inverse flow transformation of flow on joint samples
        if nf_case:
            # Set default x for npe
            npe.set_default_x(x)
            # compute inverse flow transformation of flowon (theta, x)
            inv_transform_samples_joint.append(
                inv_flow_transform_obs(
                    theta,
                    x,
                    npe.posterior_estimator,
                )
            )
    npe_samples_joint = torch.stack(npe_samples_joint)[:, 0, :]
    if nf_case:
        inv_transform_samples_joint = torch.stack(inv_transform_samples_joint)[:, 0, :]
    else:
        inv_transform_samples_joint = None

    return npe_samples_joint, inv_transform_samples_joint
