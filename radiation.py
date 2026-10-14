"""Fotones de una fuente IR y fotones reemitidos por las moléculas."""
from enum import Enum
import math
import random
from physics import validate_positive


class PhotonState(Enum):
    ACTIVE = 0
    ABSORBED = 1
    EMITTED = 2  # Reservado por compatibilidad; la procedencia se guarda en is_incident.
    OUT_OF_BOUNDS = 3


class Photon:
    def __init__(self, x: float, y: float, wavelength_um: float,
                 direction_rad: float = 0.0, is_incident: bool = True):
        self.x, self.y = x, y
        self.previous_x, self.previous_y = x, y
        self.wavelength_um = validate_positive(wavelength_um, 'La longitud de onda')
        self.direction = direction_rad
        self.is_incident = is_incident
        # Un ensayo de absorción por encuentro, independiente de los FPS.
        self.encountered_molecules = set()
        self.speed = 220.0
        self.vx = self.speed * math.cos(direction_rad)
        self.vy = self.speed * math.sin(direction_rad)
        self.state = PhotonState.ACTIVE
        self.phase = random.uniform(0, 2 * math.pi)
        self.wave_amplitude = 6.0

    def update(self, dt: float, box_width: float, box_height: float):
        if self.state != PhotonState.ACTIVE:
            return
        self.previous_x, self.previous_y = self.x, self.y
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.phase = (self.phase + 20.0 / self.wavelength_um * dt) % (2 * math.pi)
        if not (-10 <= self.x <= box_width + 10 and -10 <= self.y <= box_height + 10):
            self.state = PhotonState.OUT_OF_BOUNDS


class RadiationField:
    def __init__(self, box_width: float, box_height: float):
        self.box_width, self.box_height = box_width, box_height
        self.is_enabled = True
        self.wavelength_um = 15.0
        self.intensity_percent = 50.0
        self.reset()

    def reset(self):
        self.photons = []
        self.spawn_timer = 0.0
        self.photons_emitted_count = 0  # Sólo los procedentes de la fuente.
        self.photons_absorbed_count = 0  # Sólo fotones incidentes absorbidos.
        self.photons_reemitted_count = 0

    def set_parameters(self, wavelength_um: float, intensity_percent: float, enabled: bool):
        wavelength = validate_positive(wavelength_um, 'La longitud de onda')
        intensity = validate_positive(intensity_percent, 'La intensidad', allow_zero=True)
        if intensity > 100:
            raise ValueError('La intensidad debe estar entre 0 y 100 %.')
        self.wavelength_um, self.intensity_percent = wavelength, intensity
        self.is_enabled = bool(enabled)

    def update(self, dt: float):
        dt = validate_positive(dt, 'El intervalo de tiempo', allow_zero=True)
        if dt == 0:
            return
        self.photons = [p for p in self.photons if p.state == PhotonState.ACTIVE]
        for p in self.photons:
            p.update(dt, self.box_width, self.box_height)
        if not self.is_enabled or self.intensity_percent <= 0:
            self.spawn_timer = 0.0
            return
        spawn_rate = self.intensity_percent / 100.0 * 18.0
        spawn_interval = 1.0 / spawn_rate
        self.spawn_timer += dt
        while self.spawn_timer + 1e-12 >= spawn_interval:
            self.spawn_timer = max(0.0, self.spawn_timer - spawn_interval)
            y_pos = random.uniform(30, self.box_height - 30)
            p = Photon(0.0, y_pos, self.wavelength_um)
            # Distribuir nacimientos dentro del paso para evitar ráfagas artificiales.
            p.update(self.spawn_timer, self.box_width, self.box_height)
            self.photons.append(p)
            self.photons_emitted_count += 1

    def spawn_emitted_photon(self, x: float, y: float, wavelength_um: float, source_id=None):
        p = Photon(x, y, wavelength_um, random.uniform(0, 2 * math.pi), is_incident=False)
        if source_id is not None:
            p.encountered_molecules.add(source_id)
        self.photons.append(p)
        self.photons_reemitted_count += 1
        return p
