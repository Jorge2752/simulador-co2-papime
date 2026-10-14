# molecule.py
"""
Clase y lógica de la molécula de CO₂.
Soporta estados cinéticos, modos de vibración, cálculo del momento dipolar
y dinámicas de excitación/relajación.
"""

from enum import Enum
import math
import random
from physics import (validate_positive, calculate_spectral_units, MOLECULAR_WEIGHT_CO2,
                     WAVELENGTH_NU1_UM, WAVELENGTH_NU2_UM, WAVELENGTH_NU3_UM)


class MoleculeState(Enum):
    GROUND = 0
    EXCITED_BEND = 1        # ν₂ (~15 µm)
    EXCITED_ASYMMETRIC = 2  # ν₃ (~4.26 µm)
    EXCITED_SYMMETRIC = 3   # ν₁ (~7.5 µm, solo para demostración manual)
    RELAXING = 4


class VibrationMode(Enum):
    NONE = 0
    SYMMETRIC_STRETCH = 1   # ν₁ (7.5 µm) - IR Inactivo
    BENDING = 2             # ν₂ (15 µm) - IR Activo
    ASYMMETRIC_STRETCH = 3  # ν₃ (4.26 µm) - IR Activo


class CO2Molecule:
    def __init__(self, mol_id: int, x: float, y: float, temp_k: float = 300.0):
        self.id = mol_id
        self.x = x
        self.y = y

        # Propiedades de movimiento traslacional y rotacional
        self.vx = 0.0
        self.vy = 0.0
        self.angle = random.uniform(0, 2 * math.pi)  # Orientación molecular en radianes
        self.angular_velocity = random.uniform(-1.5, 1.5)

        # Estado cuántico / vibracional
        self.state = MoleculeState.GROUND
        self.vibration_mode = VibrationMode.NONE
        self.vibration_phase = random.uniform(0, 2 * math.pi)
        self.vibration_freq = 0.0
        self.vibration_amplitude = 0.0

        # Temporizadores e indicadores de interacción
        self.excitation_time = 0.0
        self.excitation_lifetime = 3.5  # Duración promedio antes de desexcitarse
        self.flash_timer = 0.0          # Efecto visual al absorber fotón
        self.emission_flash_timer = 0.0 # Efecto visual al emitir fotón

        # Trayectoria para visualización
        self.trail = []
        self.max_trail_len = 15

        # Asignar velocidad basada en temperatura
        self.set_temperature(temp_k)

    def set_temperature(self, temp_k: float):
        """Ajusta las velocidades según la teoría cinético-molecular (v_rms ~ sqrt(T))."""
        temp_k = validate_positive(temp_k, 'La temperatura', allow_zero=True)
        speed_factor = math.sqrt(temp_k / 300.0) * 25.0
        angle_move = random.uniform(0, 2 * math.pi)
        self.vx = speed_factor * math.cos(angle_move)
        self.vy = speed_factor * math.sin(angle_move)
        self.angular_velocity = random.uniform(-1.5, 1.5) * math.sqrt(temp_k / 300.0)

    def excite(self, mode: VibrationMode, lifetime: float = 3.5):
        """Excita la molécula a un modo vibracional específico."""
        if mode not in (VibrationMode.BENDING, VibrationMode.ASYMMETRIC_STRETCH,
                        VibrationMode.SYMMETRIC_STRETCH):
            raise ValueError('Se requiere un modo vibracional de excitación válido.')
        lifetime = validate_positive(lifetime, 'La vida media visual')
        self.vibration_mode = mode
        self.excitation_time = 0.0
        self.excitation_lifetime = lifetime
        self.flash_timer = 0.4  # Segundos de destello visual de absorción

        if mode == VibrationMode.BENDING:
            self.state = MoleculeState.EXCITED_BEND
            self.vibration_freq = 8.0  # Frecuencia visual exagerada pedagógicamente
            self.vibration_amplitude = 12.0  # Pixeles
        elif mode == VibrationMode.ASYMMETRIC_STRETCH:
            self.state = MoleculeState.EXCITED_ASYMMETRIC
            self.vibration_freq = 14.0
            self.vibration_amplitude = 10.0
        elif mode == VibrationMode.SYMMETRIC_STRETCH:
            self.state = MoleculeState.EXCITED_SYMMETRIC
            self.vibration_freq = 10.0
            self.vibration_amplitude = 10.0

    def relax(self):
        """Devuelve la molécula a su estado fundamental."""
        self.state = MoleculeState.GROUND
        self.vibration_mode = VibrationMode.NONE
        self.vibration_freq = 0.0
        self.vibration_amplitude = 0.0
        self.excitation_time = 0.0

    def update(self, dt: float, box_width: float, box_height: float,
               enable_trans: bool = True, enable_rot: bool = True, enable_vib: bool = True):
        """Actualiza la posición, ángulo y fase vibracional de la molécula."""
        dt = validate_positive(dt, 'El intervalo de tiempo', allow_zero=True)
        if dt == 0:
            return
        self.flash_timer = max(0.0, self.flash_timer - dt)
        self.emission_flash_timer = max(0.0, self.emission_flash_timer - dt)
        if self.state != MoleculeState.GROUND:
            self.excitation_time += dt

        if enable_trans:
            self.x += self.vx * dt
            self.y += self.vy * dt
            self.constrain_to_box(box_width, box_height)

            self.trail.append((self.x, self.y))
            if len(self.trail) > self.max_trail_len:
                self.trail.pop(0)

        # Actualizar rotación
        if enable_rot:
            self.angle += self.angular_velocity * dt
            self.angle %= (2 * math.pi)

        # Actualizar vibración
        if enable_vib and self.vibration_mode != VibrationMode.NONE:
            self.vibration_phase += self.vibration_freq * dt
            self.vibration_phase %= (2 * math.pi)

    def constrain_to_box(self, box_width: float, box_height: float):
        """Reposiciona al redimensionar y sólo refleja velocidades hacia fuera."""
        margin = 50.0
        for coord, velocity, size in (('x', 'vx', box_width), ('y', 'vy', box_height)):
            lower, upper = min(margin, size / 2), max(size - margin, size / 2)
            position, speed = getattr(self, coord), getattr(self, velocity)
            if position < lower:
                setattr(self, coord, lower)
                setattr(self, velocity, abs(speed))
            elif position > upper:
                setattr(self, coord, upper)
                setattr(self, velocity, -abs(speed))

    def get_atom_positions(self, bond_length: float = 28.0) -> dict:
        """Calcula las coordenadas de los átomos Carbono (C) y Oxígenos (O1, O2)."""
        cx, cy = self.x, self.y
        ux = math.cos(self.angle)
        uy = math.sin(self.angle)
        nx = -uy
        ny = ux

        sin_phase = math.sin(self.vibration_phase) * bond_length / 28.0

        d1 = bond_length
        d2 = bond_length
        bend_disp = 0.0
        c_shift_bend = 0.0
        axis_shift = 0.0

        if self.vibration_mode == VibrationMode.SYMMETRIC_STRETCH:
            disp = self.vibration_amplitude * sin_phase
            d1 += disp
            d2 += disp

        elif self.vibration_mode == VibrationMode.ASYMMETRIC_STRETCH:
            disp = self.vibration_amplitude * sin_phase
            d1 += disp
            d2 -= disp
            axis_shift = 2 * 16.0 / 44.0 * disp

        elif self.vibration_mode == VibrationMode.BENDING:
            disp = self.vibration_amplitude * sin_phase
            bend_disp = 12.0 / 44.0 * disp
            c_shift_bend = -32.0 / 44.0 * disp

        # x,y siempre representan el centro de masa (masas visuales 12 y 16).
        cx += axis_shift * ux
        cy += axis_shift * uy
        c_pos = (cx + c_shift_bend * nx, cy + c_shift_bend * ny)
        o1_pos = (cx - d1 * ux + bend_disp * nx, cy - d1 * uy + bend_disp * ny)
        o2_pos = (cx + d2 * ux + bend_disp * nx, cy + d2 * uy + bend_disp * ny)

        return {
            "C": c_pos,
            "O1": o1_pos,
            "O2": o2_pos,
            "u_vector": (ux, uy),
            "n_vector": (nx, ny)
        }

    def get_dipole_moment(self) -> dict:
        """Calcula el vector de momento dipolar instantáneo y la derivada dμ/dQ."""
        pos = self.get_atom_positions()
        cx, cy = pos["C"]
        o1x, o1y = pos["O1"]
        o2x, o2y = pos["O2"]

        q_o = -0.4  # Carga parcial relativa del oxígeno
        mu_x = q_o * (o1x - cx) + q_o * (o2x - cx)
        mu_y = q_o * (o1y - cy) + q_o * (o2y - cy)

        magnitude = math.hypot(mu_x, mu_y)
        is_active = False
        derivative_str = "dμ/dQ = 0 (Inactivo)"

        if self.vibration_mode == VibrationMode.SYMMETRIC_STRETCH:
            is_active = False
            derivative_str = "dμ/dQ = 0  ⇒  IR Inactivo"
        elif self.vibration_mode == VibrationMode.BENDING:
            is_active = True
            derivative_str = "dμ/dQ ≠ 0  ⇒  IR Activo"
        elif self.vibration_mode == VibrationMode.ASYMMETRIC_STRETCH:
            is_active = True
            derivative_str = "dμ/dQ ≠ 0  ⇒  IR Activo"

        return {
            "vector": (mu_x, mu_y),
            "magnitude": magnitude,
            "is_active": is_active,
            "derivative_str": derivative_str
        }

    def get_kinetic_energy(self) -> float:
        """Calcula la energía cinética traslacional + rotacional."""
        v_sq = self.vx**2 + self.vy**2
        rot_sq = 0.5 * (self.angular_velocity**2) * 100.0
        return 0.5 * MOLECULAR_WEIGHT_CO2 * v_sq + rot_sq

    def get_vibrational_energy(self) -> float:
        """Devuelve la energía vibracional asociada al modo actual."""
        wavelength = {
            MoleculeState.EXCITED_BEND: WAVELENGTH_NU2_UM,
            MoleculeState.EXCITED_ASYMMETRIC: WAVELENGTH_NU3_UM,
            MoleculeState.EXCITED_SYMMETRIC: WAVELENGTH_NU1_UM,
        }.get(self.state)
        # Escala pedagógica común a los tres modos; respeta E = hc/λ.
        return 100.0 * calculate_spectral_units(wavelength)['energy_kj_mol'] if wavelength else 0.0
