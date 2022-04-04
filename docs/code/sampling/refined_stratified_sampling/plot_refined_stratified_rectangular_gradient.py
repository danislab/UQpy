"""

Rectangular Refined Stratified Sampling - Gradient Enhanced Refinement
=======================================================================

In this example, Stratified sampling is used to generate samples from Uniform distribution and sample expansion is done
adaptively using Refined Stratified Sampling.
"""

#%% md
#
# Import the necessary libraries. Here we import standard libraries such as numpy, matplotlib and other necessary
# library for plots, but also need to import the :class:`.TrueStratifiedSampling`, :class:`.RefinedStratifiedSampling`
# and :class:`.Kriging` class from :py:mod:`UQpy`.

#%%
import shutil

from UQpy.sampling import TrueStratifiedSampling, RefinedStratifiedSampling
from UQpy.surrogates import GaussianProcessRegression
from UQpy.run_model.RunModel import RunModel
from UQpy.distributions import Uniform
import matplotlib.pyplot as plt
from matplotlib import cm
from matplotlib.ticker import LinearLocator, FormatStrFormatter
import numpy as np
from UQpy.sampling.stratified_sampling.strata import RectangularStrata
from UQpy.utilities.MinimizeOptimizer import MinimizeOptimizer

#%% md
#
# Create a distribution object.

#%%

marginals = [Uniform(loc=0., scale=1.), Uniform(loc=0., scale=1.)]

#%% md
#
# Create a strata object.

#%%

strata = RectangularStrata(strata_number=[4, 4])

#%% md
#
# Run stratified sampling.

#%%

x = TrueStratifiedSampling(distributions=marginals, strata_object=strata, nsamples_per_stratum=1, random_state=1)
initial_samples=x.samples.copy()

#%% md
#
# This plot shows the samples and strata generated by the :class:`.TrueStratifiedSampling` class.

#%%

fig1 = x.strata_object.plot_2d()
plt.title("STS samples U(0,1) and space stratification")
plt.plot(x.samples[:16, 0], x.samples[:16, 1], 'ro')
plt.xlim([0, 1])
plt.ylim([0, 1])
plt.show()

#%% md
#
# RunModel class is used to estimate the function value at sample points generated using
# :class:`.TrueStratifiedSampling` class.

#%%

rmodel = RunModel(model_script='local_python_model_function.py', vec=False)

#%% md
#
# This figure shows the actual function defined in python model script.

#%%

rmodel1 = RunModel(model_script='local_python_model_function.py', vec=False)
rmodel1.run(samples=x.samples)
num = 100
x1 = np.linspace(0, 1, num)
x2 = np.linspace(0, 1, num)
x1v, x2v = np.meshgrid(x1, x2)
y_act = np.zeros([num, num])
r1model = RunModel(model_script='local_python_model_function.py')
for i in range(num):
    for j in range(num):
        r1model.run(samples=np.array([[x1v[i, j], x2v[i, j]]]), append_samples=False)
        y_act[i, j] = r1model.qoi_list[0]

fig1 = plt.figure()
ax1 = fig1.gca(projection='3d')
# Plot for estimated values
surf = ax1.plot_surface(x1v, x2v, y_act, cmap=cm.coolwarm, linewidth=0, antialiased=False)
# Customize the z axis.
ax1.set_zlim(-1, 15)
ax1.zaxis.set_major_locator(LinearLocator(10))
ax1.zaxis.set_major_formatter(FormatStrFormatter('%.02f'))
# Add a color bar which maps values to colors.
fig1.colorbar(surf, shrink=0.5, aspect=5)
plt.show()

#%% md
#
# :class:`.Kriging` class generated a surrogate model using :class:`.TrueStratifiedSampling` samples and function value
# at those points.

#%%

from UQpy.surrogates.gaussian_process.regression_models import LineaRegression
from UQpy.surrogates.gaussian_process.kernels import RBF

bounds = [[10**(-3), 10**3], [10**(-3), 10**2], [10**(-3), 10**2]]
K = GaussianProcessRegression(regression_model=LineaRegression(), kernel=RBF(),
                              optimizer=MinimizeOptimizer(method="L-BFGS-B", bounds=bounds),
                              hyperparameters=[1, 1, 0.1], optimizations_number=20)
K.fit(samples=x.samples, values=rmodel1.qoi_list)
print(K.hyperparameters)

#%% md
#
# This figure shows the surrogate model generated using :class:`.Kriging` class from initial samples.

#%%

num = 25
x1 = np.linspace(0, 1, num)
x2 = np.linspace(0, 1, num)
x1v, x2v = np.meshgrid(x1, x2)
y = np.zeros([num, num])
for i in range(num):
    for j in range(num):
        y[i, j] = K.predict(np.array([x1v[i, j], x2v[i, j]]))

fig2 = plt.figure()
ax2 = fig2.gca(projection='3d')
# Plot for estimated values
kr = ax2.plot_wireframe(x1v, x2v, y, color='Green', label='Kriging interpolate')

# Plot for scattered data
ID = ax2.scatter3D(x.samples[:, 0], x.samples[:, 1], rmodel1.qoi_list, color='Red', label='Input data')
plt.legend(handles=[kr, ID])
plt.show()

#%% md
#
# A :class:`.RefinedStratifiedSampling` class object is initiated by using the :class:`.TrueStratifiedSampling`,
# :class:`.RunModel` and :class:`.Kriging` object.

#%%

from UQpy.sampling import GradientEnhancedRefinement
refinement = GradientEnhancedRefinement(strata=strata, runmodel_object=rmodel, surrogate=K)
z = RefinedStratifiedSampling(stratified_sampling=x, refinement_algorithm=refinement, random_state=2)

#%% md
#
# After initiating the :class:`.RefinedStratifiedSampling` class object, new samples are generated using the
# :code:`refinedStratifiedSampling.sample` method.

#%%

z.run(nsamples=50)

#%% md
#
# This figure shows the final samples generated using :class:`.RefinedStratifiedSampling` class, where red dots shows
# the initial samples.

#%%

fig3 = strata.plot_2d()
plt.xlim([0, 1])
plt.ylim([0, 1])
plt.plot(initial_samples[:, 0], initial_samples[:, 1], 'ro')
plt.plot(z.samplesU01[:, 0], z.samplesU01[:, 1], 'gx')
plt.show()

#%% md
#
# :class:`.Kriging` class is used to generate a surrogate model using final samples from
# :class:`.RefinedStratifiedSampling` class.

#%%

hyperparameters=K.hyperparameters.tolist()
K2 = GaussianProcessRegression(regression_model=LineaRegression(), kernel=RBF(),
                               optimizer=MinimizeOptimizer(method="L-BFGS-B"),
                               hyperparameters=hyperparameters,
                               noise=False)
K2.fit(samples=z.samples, values=rmodel.qoi_list)

#%% md
#
# This figure shows the final surrogate model, generated using 200 samples.

#%%

y = np.zeros([num, num])
for i in range(num):
    for j in range(num):
        y[i, j] = K2.predict(np.array([x1v[i, j], x2v[i, j]]))

plt.clf()
fig4 = plt.figure()
a4 = fig4.gca(projection='3d')
# Plot for estimated values
kr = a4.plot_wireframe(x1v, x2v, y, color='Green', label='Kriging interpolate')

# Plot for scattered data
ID = a4.scatter3D(z.samples[:, 0], z.samples[:, 1], rmodel.qoi_list, color='Red', label='Input data')
plt.legend(handles=[kr, ID])
plt.show()

shutil.rmtree(rmodel.model_dir)
shutil.rmtree(r1model.model_dir)
shutil.rmtree(rmodel1.model_dir)

