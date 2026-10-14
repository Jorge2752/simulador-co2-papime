"""Motor del modelo conceptual de CO₂ y radiación IR.

La energía se expresa en unidades de la animación. Las colisiones conservan
energía y momento dentro de esas unidades; no se calcula clima ni temperatura
atmosférica real a partir de este modelo bidimensional.
"""
import math
import random

from physics import (absorption_components, absorption_profile, validate_positive,
                     MOLECULAR_WEIGHT_CO2, WAVELENGTH_NU2_UM,
                     WAVELENGTH_NU3_UM, WAVELENGTH_NU1_UM)
from molecule import CO2Molecule, MoleculeState, VibrationMode
from radiation import RadiationField, PhotonState


class SimulationMode:
    ATMOSPHERIC = 'ATMOSPHERIC'
    SINGLE_MOLECULE = 'SINGLE_MOLECULE'


class SimulationEngine:
    MAX_STEP = 1.0 / 60.0

    def __init__(self, width: float = 750.0, height: float = 500.0):
        self.width = max(120., validate_positive(width, 'El ancho'))
        self.height = max(120., validate_positive(height, 'El alto'))
        self.mode = SimulationMode.ATMOSPHERIC
        self.num_molecules = 25
        self.temperature_k = 300.0
        self.pressure_atm = 1.0
        self.enable_translation = True
        self.enable_rotation = True
        self.enable_vibration = True
        self.show_dipole = False
        self.show_trails = False
        self.is_paused = False
        self.sim_speed = 1.0
        self.molecules = []
        self.radiation = RadiationField(self.width, self.height)
        self.single_molecule = None
        self.reset_simulation()

    def _new_molecule(self, mol_id):
        return CO2Molecule(mol_id, random.uniform(60, self.width - 60),
                           random.uniform(60, self.height - 60), self.temperature_k)

    def reset_simulation(self):
        """Reinicia datos y reloj, conservando controles y estado de pausa."""
        self.radiation.reset()
        self.total_absorptions = 0
        self.total_emissions = 0
        self.collisional_deexcitations = 0
        self.elapsed_time = 0.0
        self._next_molecule_id = self.num_molecules
        self.molecules = [self._new_molecule(i) for i in range(self.num_molecules)]
        self.single_molecule = CO2Molecule(-1, self.width / 2, self.height / 2, 0.0)
        self.single_molecule.angle = 0.0
        self.sync_molecular_demonstration()

    def resize(self, width: float, height: float):
        self.width = max(120., validate_positive(width, 'El ancho'))
        self.height = max(120., validate_positive(height, 'El alto'))
        self.radiation.box_width = self.width
        self.radiation.box_height = self.height
        self.single_molecule.x, self.single_molecule.y = self.width / 2, self.height / 2
        for mol in self.molecules:
            mol.constrain_to_box(self.width, self.height)
            mol.trail.clear()

    def set_molecule_count(self, count: int):
        if not isinstance(count, int) or isinstance(count, bool) or not 1 <= count <= 100:
            raise ValueError('El número de moléculas debe ser un entero entre 1 y 100.')
        self.num_molecules = count
        while len(self.molecules) < count:
            self.molecules.append(self._new_molecule(self._next_molecule_id))
            self._next_molecule_id += 1
        self.molecules = self.molecules[:count]

    def set_temperature(self, temp_k: float):
        self.temperature_k = validate_positive(temp_k, 'La temperatura', allow_zero=True)
        for mol in self.molecules:
            mol.set_temperature(self.temperature_k)

    def set_pressure(self, pressure_atm: float):
        self.pressure_atm = validate_positive(pressure_atm, 'La presión', allow_zero=True)

    def set_wavelength(self, wavelength_um: float):
        self.radiation.set_parameters(wavelength_um, self.radiation.intensity_percent,
                                      self.radiation.is_enabled)
        self.sync_molecular_demonstration()

    def set_simulation_mode(self, mode: str):
        if mode not in (SimulationMode.ATMOSPHERIC, SimulationMode.SINGLE_MOLECULE):
            raise ValueError('Modo de simulación desconocido.')
        self.mode = mode
        self.sync_molecular_demonstration()

    def sync_molecular_demonstration(self):
        """Animación manual persistente: no representa una absorción IR."""
        if self.mode != SimulationMode.SINGLE_MOLECULE:
            return
        wavelength = self.radiation.wavelength_um
        selected = VibrationMode.NONE
        for center, tolerance, mode in (
            (WAVELENGTH_NU2_UM, 1.2, VibrationMode.BENDING),
            (WAVELENGTH_NU3_UM, 0.8, VibrationMode.ASYMMETRIC_STRETCH),
            (WAVELENGTH_NU1_UM, 0.8, VibrationMode.SYMMETRIC_STRETCH),
        ):
            if abs(wavelength - center) < tolerance:
                selected = mode
                break
        if selected == VibrationMode.NONE:
            self.single_molecule.relax()
        else:
            self.single_molecule.excite(selected)
            self.single_molecule.flash_timer = 0.0

    def update(self, dt: float) -> float:
        dt = validate_positive(dt, 'El intervalo de tiempo', allow_zero=True)
        speed = validate_positive(self.sim_speed, 'La velocidad de simulación', allow_zero=True)
        if self.is_paused or dt == 0 or speed == 0:
            return 0.0
        effective_dt = dt * speed
        steps = max(1, math.ceil(effective_dt / self.MAX_STEP))
        step_dt = effective_dt / steps
        for _ in range(steps):
            if self.mode == SimulationMode.SINGLE_MOLECULE:
                self._update_single_molecule(step_dt)
            else:
                self._update_atmospheric_mode(step_dt)
        self.elapsed_time += effective_dt
        return effective_dt

    def _update_single_molecule(self, dt: float):
        self.single_molecule.update(dt, self.width, self.height, enable_trans=False,
                                    enable_rot=False, enable_vib=self.enable_vibration)

    def _update_atmospheric_mode(self, dt: float):
        self.radiation.update(dt)
        for mol in self.molecules:
            mol.update(dt, self.width, self.height, self.enable_translation,
                       self.enable_rotation, self.enable_vibration)
        self._check_photon_molecule_interactions()
        if self.enable_translation:
            self._check_molecule_collisions()
            for mol in self.molecules:
                mol.constrain_to_box(self.width, self.height)
        for mol in self.molecules:
            if mol.state != MoleculeState.GROUND and mol.excitation_time >= mol.excitation_lifetime:
                wavelength = {
                    MoleculeState.EXCITED_BEND: WAVELENGTH_NU2_UM,
                    MoleculeState.EXCITED_ASYMMETRIC: WAVELENGTH_NU3_UM,
                }.get(mol.state)
                # El modo simétrico sólo se excita en la demostración manual.
                if wavelength is not None:
                    self.radiation.spawn_emitted_photon(mol.x, mol.y, wavelength, source_id=mol.id)
                    mol.emission_flash_timer = 0.4
                    self.total_emissions += 1
                    mol.relax()

    def _check_photon_molecule_interactions(self):
        radius = 28.0
        for photon in self.radiation.photons:
            if photon.state != PhotonState.ACTIVE:
                continue
            dx, dy = photon.x - photon.previous_x, photon.y - photon.previous_y
            length_sq = dx * dx + dy * dy
            encounters = []
            for mol in self.molecules:
                if mol.id in photon.encountered_molecules:
                    continue
                # Intersección segmento-círculo: detectar el primer encuentro,
                # incluso si un paso atraviesa completamente la molécula.
                ox, oy = photon.previous_x - mol.x, photon.previous_y - mol.y
                c = ox * ox + oy * oy - radius * radius
                if c <= 0:
                    entry = 0.0
                elif length_sq > 0:
                    b = ox * dx + oy * dy
                    discriminant = b * b - length_sq * c
                    if discriminant < 0:
                        continue
                    entry = (-b - math.sqrt(discriminant)) / length_sq
                    if not 0 <= entry <= 1:
                        continue
                else:
                    continue
                encounters.append((entry, mol.id, mol))
            for _, _, mol in sorted(encounters):
                photon.encountered_molecules.add(mol.id)
                if mol.state != MoleculeState.GROUND:
                    continue
                weights = absorption_components(photon.wavelength_um, self.pressure_atm)
                total = sum(weights.values())
                if random.random() >= min(1., total):
                    continue
                mode = (VibrationMode.BENDING if random.random() < weights['nu2'] / total
                        else VibrationMode.ASYMMETRIC_STRETCH)
                photon.state = PhotonState.ABSORBED
                self.total_absorptions += 1
                if photon.is_incident:
                    self.radiation.photons_absorbed_count += 1
                mol.excite(mode)
                break

    def _check_molecule_collisions(self):
        collision_dist = 40.0
        for i, m1 in enumerate(self.molecules):
            for m2 in self.molecules[i + 1:]:
                dx, dy = m2.x - m1.x, m2.y - m1.y
                dist = math.hypot(dx, dy)
                if dist >= collision_dist:
                    continue
                nx, ny = (dx / dist, dy / dist) if dist > 1e-12 else (1.0, 0.0)
                overlap = 0.5 * (collision_dist - dist)
                m1.x -= nx * overlap
                m1.y -= ny * overlap
                m2.x += nx * overlap
                m2.y += ny * overlap
                relative_normal = (m2.vx - m1.vx) * nx + (m2.vy - m1.vy) * ny
                if relative_normal >= 0:
                    continue  # Ya se separan: no aplicar un segundo impulso.
                released = 0.0
                for mol in (m1, m2):
                    if mol.state != MoleculeState.GROUND and random.random() < min(1., 0.25 * self.pressure_atm):
                        released += mol.get_vibrational_energy()
                        mol.relax()
                        self.collisional_deexcitations += 1
                # Masas iguales: impulso normal elástico más la energía V-T.
                outgoing = math.sqrt(relative_normal**2 + 4 * released / MOLECULAR_WEIGHT_CO2)
                impulse_per_mass = (outgoing - relative_normal) / 2
                m1.vx -= impulse_per_mass * nx
                m1.vy -= impulse_per_mass * ny
                m2.vx += impulse_per_mass * nx
                m2.vy += impulse_per_mass * ny

    def get_statistics(self) -> dict:
        molecules = ([self.single_molecule] if self.mode == SimulationMode.SINGLE_MOLECULE
                     else self.molecules)
        incident = self.radiation.photons_emitted_count
        absorbed = self.radiation.photons_absorbed_count
        return {
            'excited_count': sum(m.state != MoleculeState.GROUND for m in molecules),
            'total_molecules': len(molecules),
            'photons_emitted': incident,
            'photons_absorbed': absorbed,
            'total_absorptions': self.total_absorptions,
            'total_emissions': self.total_emissions,
            'pct_absorbed': 100.0 * absorbed / incident if incident else 0.0,
            'total_kin_energy': sum(m.get_kinetic_energy() for m in molecules),
            'total_vib_energy': sum(m.get_vibrational_energy() for m in molecules),
            'collisional_deexcitations': self.collisional_deexcitations,
            'relative_absorption': absorption_profile(self.radiation.wavelength_um, self.pressure_atm),
        }
