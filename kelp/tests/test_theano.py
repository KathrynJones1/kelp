import numpy as np
import pymc3 as pm
import pymc3_ext as pmx
import astropy.units as u

from ..core import Model
from ..registries import Planet, Filter


def test_cython_vs_theano():
    from ..theano.theano import thermal_phase_curve
    # These parameters have been chi-by-eye "fit" to the Spitzer/3.6 um PC
    f = 0.68
    planet = Planet.from_name('HD 189733')
    filt = Filter.from_name('IRAC 1')
    filt.bin_down(5)
    C_ml = [[0],
            [0, 0.18, 0]]
    m = Model(
        -0.8, 0.575, 4.5, 0, C_ml, 1,
        planet=planet,
        filt=filt
    )
    xi = np.linspace(-np.pi, np.pi, 100)

    # Set resolution of grid points on sphere:
    n_phi = 100
    n_theta = 10
    phi = np.linspace(-2 * np.pi, 2 * np.pi, n_phi)
    theta = np.linspace(0, np.pi, n_theta)
    theta2d, phi2d = np.meshgrid(theta, phi)

    cython_phase_curve = m.thermal_phase_curve(xi, f=f).flux

    with pm.Model():
        thermal_pc, T = thermal_phase_curve(
            xi, -0.8, 4.5, 0.575, 0.18, planet.T_s, planet.a, planet.rp_a, 0,
            theta2d, phi2d, filt.wavelength.to(u.m).value, filt.transmittance, f
        )

        theano_phase_curve = 1e6 * pmx.eval_in_model(thermal_pc)

    np.testing.assert_allclose(
        cython_phase_curve, theano_phase_curve, atol=5
    )
