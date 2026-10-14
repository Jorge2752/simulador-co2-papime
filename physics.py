"""Constantes y espectro cualitativo del CO₂; no sustituye datos HITRAN.

Las bandas Lorentzianas en longitud de onda son una aproximación visual,
con anchuras e intensidades pedagógicas, no secciones eficaces medidas.
"""
import math
import numpy as np

SPEED_OF_LIGHT = 2.99792458e8
PLANCK_CONSTANT = 6.62607015e-34
AVOGADRO_NUMBER = 6.02214076e23
ELECTRON_VOLT = 1.602176634e-19
BOLTZMANN_CONSTANT = 1.380649e-23
MOLECULAR_WEIGHT_CO2 = 44.01
EQUILIBRIUM_BOND_LENGTH = 1.16e-10

# Centros redondeados para los controles educativos (µm).
WAVELENGTH_NU1_UM = 7.50
WAVELENGTH_NU2_UM = 15.00
WAVELENGTH_NU3_UM = 4.26
WAVENUMBER_NU1 = 10000.0 / WAVELENGTH_NU1_UM
WAVENUMBER_NU2 = 10000.0 / WAVELENGTH_NU2_UM
WAVENUMBER_NU3 = 10000.0 / WAVELENGTH_NU3_UM


def validate_positive(value: float, name: str, allow_zero: bool = False) -> float:
    value = float(value)
    if not math.isfinite(value) or value < 0 or (value == 0 and not allow_zero):
        raise ValueError(f'{name} debe ser finito y {"no negativo" if allow_zero else "positivo"}.')
    return value


def calculate_spectral_units(lambda_um: float) -> dict:
    lambda_um = validate_positive(lambda_um, 'La longitud de onda')
    frequency_hz = SPEED_OF_LIGHT / (lambda_um * 1e-6)
    energy_joules = PLANCK_CONSTANT * frequency_hz
    return {
        'wavelength_um': lambda_um,
        'wavenumber_cm': 10000.0 / lambda_um,
        'frequency_thz': frequency_hz / 1e12,
        'energy_ev': energy_joules / ELECTRON_VOLT,
        'energy_kj_mol': energy_joules * AVOGADRO_NUMBER / 1000.0,
        'energy_joules': energy_joules,
    }


def absorption_components(lambda_um: float, pressure_atm: float = 1.0) -> dict:
    """Contribuciones de ν₂ y ν₃; ν₁ no tiene transición dipolar fundamental.

    Las colas de las bandas activas pueden aportar absorción débil cerca de
    7.5 µm; no se añade un pico artificial de estiramiento simétrico.
    """
    lambda_um = validate_positive(lambda_um, 'La longitud de onda')
    pressure_atm = validate_positive(pressure_atm, 'La presión', allow_zero=True)
    broadening = 1.0 + 0.35 * (pressure_atm - 1.0)
    gamma2, gamma3 = 0.60 * broadening, 0.22 * broadening
    return {
        'nu2': gamma2**2 / ((lambda_um - WAVELENGTH_NU2_UM)**2 + gamma2**2),
        'nu3': 0.92 * gamma3**2 / ((lambda_um - WAVELENGTH_NU3_UM)**2 + gamma3**2),
    }


def absorption_profile(lambda_um: float, pressure_atm: float = 1.0) -> float:
    return min(1.0, sum(absorption_components(lambda_um, pressure_atm).values()))


def generate_spectrum_data(lambda_min: float = 2.0, lambda_max: float = 25.0,
                           steps: int = 500, pressure_atm: float = 1.0):
    validate_positive(lambda_min, 'El límite inferior')
    validate_positive(lambda_max, 'El límite superior')
    if lambda_max <= lambda_min:
        raise ValueError('El límite superior debe exceder el inferior.')
    if not isinstance(steps, int) or isinstance(steps, bool) or steps < 2:
        raise ValueError('Se requieren al menos dos puntos enteros.')
    lambdas = np.linspace(lambda_min, lambda_max, steps)
    absorptions = np.array([absorption_profile(l, pressure_atm) for l in lambdas])
    return lambdas, absorptions
