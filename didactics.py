"""Mensajes docentes ligados a los controles, sin alterar la física del motor."""
from physics import WAVELENGTH_NU1_UM, WAVELENGTH_NU2_UM, WAVELENGTH_NU3_UM
from simulation import SimulationMode


def band_explanation(wavelength_um: float, mode: str) -> tuple[str, str]:
    """Describe la banda seleccionada con los mismos umbrales que el escritorio."""
    if abs(wavelength_um - WAVELENGTH_NU2_UM) < 1.2:
        title = 'ν₂ · Flexión · banda IR activa'
        body = ('Cerca de 15 µm (≈667 cm⁻¹), la flexión rompe la geometría lineal. '
                'El momento dipolar cambia durante la vibración (∂μ/∂Q ≠ 0), '
                'por lo que el modelo asigna una probabilidad alta de absorción.')
    elif abs(wavelength_um - WAVELENGTH_NU3_UM) < 0.8:
        title = 'ν₃ · Estiramiento asimétrico · banda IR activa'
        body = ('Cerca de 4.26 µm (≈2347 cm⁻¹), un enlace C=O se alarga mientras '
                'el otro se acorta. El dipolo cambia (∂μ/∂Q ≠ 0) y el modelo '
                'representa una banda intensa de absorción.')
    elif abs(wavelength_um - WAVELENGTH_NU1_UM) < 0.8:
        title = 'ν₁ · Estiramiento simétrico · transición fundamental IR inactiva'
        body = ('Cerca de 7.50 µm (≈1333 cm⁻¹), ambos enlaces cambian de longitud '
                'en fase. Sus dipolos se cancelan y ∂μ/∂Q = 0 para este modo. '
                'Las colas de otras bandas activas pueden causar absorción débil '
                'en la vista atmosférica; no se simula una banda fundamental ν₁.')
    else:
        title = 'Fuera de las bandas IR activas principales'
        body = ('La longitud de onda no coincide con los centros de ν₂ o ν₃. '
                'La absorción del perfil ilustrativo es menor, aunque las colas '
                'de las bandas pueden producir encuentros absorbidos.')
    if mode == SimulationMode.SINGLE_MOLECULE:
        body += (' En la vista molecular se fuerza la vibración como demostración '
                 'manual, sin absorción de un fotón. Esto permite observar también ν₁.')
    return title, body


def mode_label(mode_name: str) -> str:
    return {
        'NONE': 'Sin vibración seleccionada',
        'BENDING': 'ν₂ · Flexión',
        'ASYMMETRIC_STRETCH': 'ν₃ · Estiramiento asimétrico',
        'SYMMETRIC_STRETCH': 'ν₁ · Estiramiento simétrico',
    }.get(mode_name, mode_name)
