"""Small state adapter shared by the Streamlit UI and its integration tests."""
from collections import deque

from simulation import SimulationEngine


def build_session():
    return {'engine': SimulationEngine(750, 500), 'running': False,
            'history': deque(maxlen=240), 'ticks': 0}


def configure(engine, *, mode, count, temperature, pressure, wavelength,
              intensity, radiation_enabled, translation, rotation,
              vibration, dipole, trails, speed):
    mode_changed = engine.mode != mode
    if engine.mode != mode:
        engine.set_simulation_mode(mode)
    if engine.num_molecules != count:
        engine.set_molecule_count(count)
    if engine.temperature_k != temperature:
        engine.set_temperature(temperature)
    if engine.pressure_atm != pressure:
        engine.set_pressure(pressure)
    if engine.radiation.wavelength_um != wavelength:
        engine.set_wavelength(wavelength)
    if (engine.radiation.intensity_percent != intensity or
            engine.radiation.is_enabled != radiation_enabled):
        engine.radiation.set_parameters(wavelength, intensity, radiation_enabled)
    engine.enable_translation = translation
    engine.enable_rotation = rotation
    engine.enable_vibration = vibration
    engine.show_dipole = dipole
    engine.show_trails = trails
    engine.sim_speed = speed
    return mode_changed


def step(session, duration):
    engine = session['engine']
    if not session['running']:
        return
    engine.update(duration)
    session['ticks'] += 1
    if session['ticks'] % 2 == 0:
        stats = engine.get_statistics()
        session['history'].append((engine.elapsed_time,
                                   stats['total_kin_energy'], stats['total_vib_energy']))
