import itertools
from abc import ABC

import numpy as np

from UQpy.utilities.GrassmannPoint import GrassmannPoint
from UQpy.utilities.kernels.baseclass.Kernel import Kernel


class GrassmannianKernel(Kernel, ABC):
    """This is a blueprint for Euclidean kernels implemented in the :py:mod:`kernels` module ."""

    def calculate_kernel_matrix(self, points: list[GrassmannPoint], p: int = None):
        """
        Compute the kernel matrix given a list of points on the Grassmann manifold.

        :param points: Points projected on the Grassmann manifold
        :param p: Number of independent p-planes of each Grassmann point.
        :return: :class:`ndarray`
        """
        nargs = len(points)
        # Define the pairs of points to compute the entries of the kernel matrix.
        indices = range(nargs)
        pairs = list(itertools.combinations_with_replacement(indices, 2))

        # Estimate entries of the kernel matrix.
        kernel = np.zeros((nargs, nargs))
        for id_pair in range(np.shape(pairs)[0]):
            i = pairs[id_pair][0]  # Point i
            j = pairs[id_pair][1]  # Point j
            if not p:
                xi = points[i]
                xj = points[j]
            else:
                xi = GrassmannPoint(points[i].data[:, :p])
                xj = GrassmannPoint(points[j].data[:, :p])

            # RiemannianDistance.check_rows(xi, xj)
            kernel[i, j] = self.kernel_entry(xi, xj)
            kernel[j, i] = kernel[i, j]

        return kernel
