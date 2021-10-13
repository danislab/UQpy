from typing import Union
from typing import Optional
from beartype import beartype

from UQpy.utilities.ValidationTypes import RandomStateType, PositiveInteger
from UQpy.distributions import *
from UQpy.utilities.Utilities import process_random_state
import numpy as np
import logging


class MonteCarloSampling:
    """
    Perform Monte Carlo sampling (MCS) of random variables.

    **Input:**

    * **distributions** ((list of) ``Distribution`` object(s)):
        Probability distribution of each random variable. Must be an object (or a list of objects) of the
        ``Distribution`` class.

    * **samples_number** (`int`):
        Number of samples to be drawn from each distribution.

        The ``run`` method is automatically called if `samples_number` is provided. If `samples_number` is not provided,
        then the ``MonteCarloSampling`` object is created but samples are not generated.

    * **random_state** (None or `int` or ``numpy.random.RandomState`` object):
        Random seed used to initialize the pseudo-random number generator. Default is None.

        If an integer is provided, this sets the seed for an object of ``numpy.random.RandomState``. Otherwise, the
        object itself can be passed directly.

    **Attributes:**

    * **samples** (`ndarray` or `list`):
        Generated samples.

        If a list of ``DistributionContinuous1D`` objects is provided for ``distributions``, then `samples` is an
        `ndarray` with ``samples.shape=(samples_number, len(distributions))``.

        If a ``DistributionContinuous1D`` object is provided for ``distributions`` then `samples` is an array with
        `samples.shape=(samples_number, 1)``.

        If a ``DistributionContinuousND`` object is provided for ``distributions`` then `samples` is an array with
        ``samples.shape=(samples_number, ND)``.

        If a list of mixed ``DistributionContinuous1D`` and ``DistributionContinuousND`` objects is provided then
        `samples` is a list with ``len(samples)=samples_number`` and ``len(samples[i]) = len(distributions)``.

    * **samplesU01** (`ndarray` (`list`)):
        Generated samples transformed to the unit hypercube.

        This attribute exists only if the ``transform_u01`` method is invoked by the user.


    **Methods**

    **run** *(samples_number, random_state)*
        Execute the random sampling in the ``MonteCarloSampling`` class.

        The ``run`` method is the function that performs random sampling in the ``MonteCarloSampling`` class. If
        `samples_number` is provided, the ``run`` method is automatically called when the ``MonteCarloSampling`` object
        is defined. The user may also call the ``run`` method directly to generate samples. The ``run`` method of the
        ``MonteCarloSampling`` class can be  invoked many times and each time the generated samples are appended to the
        existing samples.

        **Input:**

        * **samples_number** (`int`):
            Number of samples to be drawn from each distribution.

            If the ``run`` method is invoked multiple times, the newly generated samples will be appended to the
            existing samples.

        * **random_state** (None or `int` or ``numpy.random.RandomState`` object):
            Random seed used to initialize the pseudo-random number generator. Default is None.

            If an integer is provided, this sets the seed for an object of ``numpy.random.RandomState``. Otherwise, the
            object itself can be passed directly.

        **Output/Returns:**

        The ``run`` method has no returns, although it creates and/or appends the `samples` attribute of the
        ``MonteCarloSampling`` class.

    **transform_u01** *()*
    Transform random samples to uniform on the unit hypercube.

        **Input:**

        The ``transform_u01`` method is an instance method that perform the transformation on an existing
        ``MonteCarloSampling`` object. It takes no input.

        **Output/Returns:**

        The ``transform_u01`` method has no returns, although it creates and/or appends the `samplesU01` attribute of
        the ``MonteCarloSampling`` class.
    """
    @beartype
    def __init__(self,
                 distributions: Union[Distribution, list[Distribution]],
                 samples_number: Optional[int] = None,
                 random_state: RandomStateType = None):
        self.logger = logging.getLogger(__name__)
        self.random_state = process_random_state(random_state)

        self.list = False
        self.array = False
        self._process_distributions(distributions)

        self.samples = None
        self.x = None
        self.samplesU01 = None
        self.samples_number = samples_number

        # Run Monte Carlo sampling
        if samples_number is not None:
            self.run(samples_number=self.samples_number, random_state=self.random_state)

    def _process_distributions(self, distributions):
        if isinstance(distributions, list):
            add_continuous_1d = 0
            add_continuous_nd = 0
            for i in range(len(distributions)):
                if not isinstance(distributions[i], Distribution):
                    raise TypeError('UQpy: A UQpy.Distribution object must be provided.')
                if isinstance(distributions[i], DistributionContinuous1D):
                    add_continuous_1d = add_continuous_1d + 1
                elif isinstance(distributions[i], DistributionND):
                    add_continuous_nd = add_continuous_nd + 1
            if add_continuous_1d == len(distributions):
                self.list = False
                self.array = True
            else:
                self.list = True
                self.array = False
            self.dist_object = distributions
        else:
            self.dist_object = distributions
            self.list = False
            self.array = True

    @beartype
    def run(self, samples_number: PositiveInteger, random_state: RandomStateType = None):

        # Check if a random_state is provided.
        self.random_state = process_random_state(random_state) if random_state is not None else self.random_state

        self.logger.info('UQpy: Running Monte Carlo Sampling.')

        if isinstance(self.dist_object, list):
            temp_samples = list()
            for i in range(len(self.dist_object)):
                if hasattr(self.dist_object[i], 'rvs'):
                    temp_samples.append(self.dist_object[i].rvs(nsamples=samples_number,
                                                                random_state=self.random_state))
                else:
                    raise ValueError('UQpy: rvs method is missing.')
            self.x = list()
            for j in range(samples_number):
                y = list()
                for k in range(len(self.dist_object)):
                    y.append(temp_samples[k][j])
                self.x.append(np.array(y))
        else:
            if hasattr(self.dist_object, 'rvs'):
                temp_samples = self.dist_object.rvs(nsamples=samples_number, random_state=self.random_state)
                self.x = temp_samples

        if self.samples is None:
            if isinstance(self.dist_object, list) and self.array is True:
                self.samples = np.hstack(np.array(self.x)).T
            else:
                self.samples = np.array(self.x)
        else:
            # If self.samples already has existing samples, append the new samples to the existing attribute.
            if isinstance(self.dist_object, list) and self.array is True:
                self.samples = np.concatenate([self.samples, np.hstack(np.array(self.x)).T], axis=0)
            elif isinstance(self.dist_object, Distribution):
                self.samples = np.vstack([self.samples, self.x])
            else:
                self.samples = np.vstack([self.samples, self.x])
        self.samples_number = len(self.samples)

        self.logger.info('UQpy: Monte Carlo Sampling Complete.')

    def transform_u01(self):

        if isinstance(self.dist_object, list) and self.array is True:
            zi = np.zeros_like(self.samples)
            for i in range(self.samples_number):
                z = self.samples[i, :]
                for j in range(len(self.dist_object)):
                    if hasattr(self.dist_object[j], 'cdf'):
                        zi[i, j] = self.dist_object[j].cdf(z[j])
                    else:
                        raise ValueError('UQpy: All distributions must have a cdf method.')
            self.samplesU01 = zi

        elif isinstance(self.dist_object, Distribution):
            if hasattr(self.dist_object, 'cdf'):
                zi = np.zeros_like(self.samples)
                for i in range(self.samples_number):
                    z = self.samples[i, :]
                    zi[i, :] = self.dist_object.cdf(z)
                self.samplesU01 = zi
            else:
                raise ValueError('UQpy: All distributions must have a cdf method.')

        elif isinstance(self.dist_object, list) and self.list is True:
            temp_samples_u01 = list()
            for i in range(self.samples_number):
                z = self.samples[i][:]
                y = [None] * len(self.dist_object)
                for j in range(len(self.dist_object)):
                    if hasattr(self.dist_object[j], 'cdf'):
                        zi = self.dist_object[j].cdf(z[j])
                    else:
                        raise ValueError('UQpy: All distributions must have a cdf method.')
                    y[j] = zi
                temp_samples_u01.append(np.array(y))
            self.samplesU01 = temp_samples_u01
