"""Visualizaciones SVG de solo lectura para el motor de simulación."""
import math

from molecule import MoleculeState
from radiation import PhotonState


def _line(x1, y1, x2, y2, color, width=2, extra=""):
    return (f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'stroke="{color}" stroke-width="{width}" {extra}/>')


def _circle(x, y, radius, color, extra=""):
    return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{radius}" fill="{color}" {extra}/>'


def scene_svg(engine):
    """Dibuja moléculas y fotones sin cambiar el estado del modelo."""
    width, height = engine.width, engine.height
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width:g} {height:g}" '
             'role="img" aria-label="Animación de moléculas de CO₂ y fotones infrarrojos" '
             'style="width:100%;height:auto;border-radius:12px;background:#101c2b">',
             f'<rect x="1" y="1" width="{width-2:g}" height="{height-2:g}" '
             'rx="12" fill="#101c2b" stroke="#637184" stroke-width="2"/>']
    molecules = ([engine.single_molecule] if engine.mode == 'SINGLE_MOLECULE'
                 else engine.molecules)
    if engine.mode == 'ATMOSPHERIC':
        for photon in engine.radiation.photons:
            if photon.state == PhotonState.ACTIVE:
                parts.append(_circle(photon.x, photon.y, 4, '#facc15' if photon.is_incident else '#fb923c'))
    for mol in molecules:
        if engine.show_trails and engine.mode == 'ATMOSPHERIC' and len(mol.trail) > 1:
            trail = ' '.join(f'{x:.1f},{y:.1f}' for x, y in mol.trail)
            parts.append(f'<polyline points="{trail}" fill="none" stroke="#53738c" stroke-width="1.5"/>')
        p = mol.get_atom_positions()
        c, o1, o2 = p['C'], p['O1'], p['O2']
        parts.extend([_line(*c, *o1, '#b9c5d6', 3), _line(*c, *o2, '#b9c5d6', 3)])
        excited = mol.state != MoleculeState.GROUND
        if mol.flash_timer > 0 or mol.emission_flash_timer > 0:
            parts.append(_circle(mol.x, mol.y, 36, 'none', 'stroke="#facc15" stroke-width="2"'))
        parts.append(_circle(*c, 8, '#313b4c', 'stroke="#dbe4ee" stroke-width="1.5"'))
        for ox, oy in (o1, o2):
            parts.append(_circle(ox, oy, 10, '#e87575' if excited else '#db5c67'))
        if engine.show_dipole:
            mu = mol.get_dipole_moment()['vector']
            mag = math.hypot(*mu)
            if mag > 1e-5:
                length = min(32, 2 * mag)
                ex = mol.x + length * mu[0] / mag
                ey = mol.y + length * mu[1] / mag
                parts.append(_line(mol.x, mol.y, ex, ey, '#4ade80', 2,
                                   'marker-end="url(#arrow)"'))
    parts.insert(2, '<defs><marker id="arrow" markerWidth="7" markerHeight="7" '
                 'refX="5" refY="3" orient="auto"><path d="M0 0 L6 3 L0 6" '
                 'fill="none" stroke="#4ade80"/></marker></defs>')
    parts.append('</svg>')
    return ''.join(parts)


def spectrum_svg(pressure, wavelength):
    from physics import absorption_profile

    points = []
    for i in range(251):
        wave = 2 + 23 * i / 250
        points.append(f'{42 + 610 * i / 250:.1f},{160 - 135 * absorption_profile(wave, pressure):.1f}')
    marker = 42 + 610 * (wavelength - 2) / 23
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 195" role="img" '
            f'aria-label="Absorción relativa de CO₂ frente a longitud de onda; selección {wavelength:.2f} micrómetros" '
            'style="width:100%;height:auto;background:#f7fafc;border-radius:8px">'
            '<text x="42" y="17" font-size="13" fill="#263238">Absorción relativa</text>'
            '<line x1="42" y1="160" x2="652" y2="160" stroke="#64748b"/>'
            f'<polyline points="{" ".join(points)}" fill="none" stroke="#047a8c" stroke-width="2.5"/>'
            f'<line x1="{marker:.1f}" y1="24" x2="{marker:.1f}" y2="160" '
            'stroke="#b45309" stroke-width="2" stroke-dasharray="5 4"/>'
            '<text x="42" y="181" font-size="12" fill="#334155">2 µm</text>'
            '<text x="605" y="181" font-size="12" fill="#334155">25 µm</text></svg>')


def energy_svg(history):
    if not history:
        return '<p>Inicia la simulación para ver la evolución de la energía.</p>'
    entries = list(history)[-120:]
    maxima = max(max(k, v) for _, k, v in entries) or 1
    def coords(index):
        return ' '.join(f'{42+610*i/max(1,len(entries)-1):.1f},{160-132*row[index]/maxima:.1f}'
                        for i, row in enumerate(entries))
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 195" role="img" '
            'aria-label="Evolución de energía cinética y vibracional en unidades del modelo" '
            'style="width:100%;height:auto;background:#f7fafc;border-radius:8px">'
            '<text x="42" y="17" font-size="13" fill="#263238">Energía (unidades del modelo)</text>'
            '<line x1="42" y1="160" x2="652" y2="160" stroke="#64748b"/>'
            f'<polyline points="{coords(1)}" fill="none" stroke="#2563eb" stroke-width="2"/>'
            f'<polyline points="{coords(2)}" fill="none" stroke="#e11d48" stroke-width="2"/>'
            '<text x="42" y="181" font-size="12" fill="#2563eb">● Cinética</text>'
            '<text x="145" y="181" font-size="12" fill="#e11d48">● Vibracional</text></svg>')
