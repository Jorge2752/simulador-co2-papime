"""Adaptación inicial del simulador educativo de CO₂ para Streamlit.

Ejecutar: streamlit run app.py
El estado del motor se guarda por sesión de navegador, sin objetos globales compartidos.
"""
import streamlit as st

from app_helpers import build_session, configure, step
from didactics import band_explanation, mode_label
from physics import calculate_spectral_units
from simulation import SimulationMode
from web_view import energy_svg, scene_svg, spectrum_svg


FRAME_SECONDS = 0.1  # Tiempo del modelo por cuadro; la velocidad real depende del servidor.


def advance(session, duration=FRAME_SECONDS):
    step(session, duration)


st.set_page_config(page_title='Simulador de CO₂ · Laboratorio de Termodinámica',
                   page_icon='🌍', layout='wide')
st.title('Simulador de CO₂ y radiación infrarroja')
st.caption('Laboratorio de Termodinámica · Proyecto PAPIME PE101026')
st.info('Modelo didáctico bidimensional. Las energías de movimiento se muestran en unidades '
        'del modelo; la animación no calcula una predicción del clima.')

if 'co2_lab' not in st.session_state:
    st.session_state.co2_lab = build_session()
session = st.session_state.co2_lab
engine = session['engine']

with st.sidebar:
    st.header('Controles')
    show_theory = st.checkbox('Mostrar explicaciones breves', value=True,
                              help='Muestra u oculta las notas de teoría junto a los controles y las gráficas.')
    mode_choice = st.radio('Modo', ['Atmósfera', 'Molécula individual'], horizontal=True)
    mode = (SimulationMode.ATMOSPHERIC if mode_choice == 'Atmósfera'
            else SimulationMode.SINGLE_MOLECULE)
    count = st.slider('Moléculas', 1, 100, int(engine.num_molecules),
                      disabled=mode == SimulationMode.SINGLE_MOLECULE,
                      help='Más moléculas ofrecen más oportunidades de encuentro con fotones y de colisión. '
                           'El conteo del dibujo no equivale a una concentración en ppm.')
    temperature = st.slider('Temperatura (K)', 150, 400, int(engine.temperature_k),
                            disabled=mode == SimulationMode.SINGLE_MOLECULE,
                            help='La temperatura fija la escala inicial de las velocidades; '
                                 'no es una lectura de la temperatura final del gas.')
    if show_theory and mode == SimulationMode.ATMOSPHERIC:
        st.caption('**Temperatura y movimiento:** al aumentar T, el modelo asigna '
                   'mayor rapidez inicial: v ∝ √T.')
    pressure = st.slider('Presión (atm)', 0.5, 3.0, float(engine.pressure_atm), 0.1,
                         help='En este modelo modifica el ancho de las bandas y la probabilidad '
                              'de relajación por colisión; no comprime el recinto ni cambia su población.')
    if show_theory:
        st.caption('**Presión y bandas:** una mayor presión ensancha el perfil ilustrativo. '
                   'En la vista atmosférica también favorece la relajación por colisiones.')
    if 'wavelength_control' not in st.session_state:
        st.session_state.wavelength_control = float(engine.radiation.wavelength_um)
    st.subheader('Bandas IR de referencia')
    for buttons in ((('ν₃ · 4.26 µm', 4.26, 'Estiramiento asimétrico; IR activo'),
                     ('ν₁ · 7.50 µm', 7.50, 'Estiramiento simétrico; IR inactivo')),
                    (('ν₂ · 15.0 µm', 15.0, 'Flexión; IR activo'),
                     ('10.0 µm', 10.0, 'Fuera de las bandas principales'))):
        cols = st.columns(2)
        for col, (label, value, explanation) in zip(cols, buttons):
            col.button(label, help=explanation, use_container_width=True,
                       on_click=lambda x=value: setattr(st.session_state, 'wavelength_control', x))
    wavelength = st.slider('Longitud de onda (µm)', 2.0, 25.0,
                           step=0.01, key='wavelength_control',
                           help='La energía por fotón es E = hc/λ. La absorción depende también '
                                'de la coincidencia con una transición vibracional permitida.')
    if show_theory:
        st.caption('**Energía del fotón:** E = hν = hc/λ. Una longitud de onda menor '
                   'corresponde a mayor energía por fotón.')
    intensity = st.slider('Intensidad de radiación (%)', 0, 100,
                          int(engine.radiation.intensity_percent),
                          disabled=mode == SimulationMode.SINGLE_MOLECULE,
                          help='Controla el número de fotones de la fuente por unidad de tiempo del modelo. '
                               'La escala es relativa y no está expresada en W/m².')
    if show_theory and mode == SimulationMode.ATMOSPHERIC:
        st.caption('**Intensidad y flujo:** al aumentarla llegan más fotones; '
                   'si λ permanece fija, la energía de cada uno no cambia.')
    radiation_enabled = st.checkbox('Activar radiación IR',
                                    value=engine.radiation.is_enabled,
                                    disabled=mode == SimulationMode.SINGLE_MOLECULE)
    with st.expander('Movimiento y vista'):
        translation = st.checkbox('Traslación', value=engine.enable_translation,
                                  disabled=mode == SimulationMode.SINGLE_MOLECULE)
        rotation = st.checkbox('Rotación', value=engine.enable_rotation,
                               disabled=mode == SimulationMode.SINGLE_MOLECULE)
        vibration = st.checkbox('Animar vibración', value=engine.enable_vibration,
                                help='Detiene el dibujo de la vibración; en la vista atmosférica '
                                     'siguen activas la absorción y la relajación.')
        dipole = st.checkbox('Mostrar momento dipolar', value=engine.show_dipole,
                             help='La flecha verde representa el dipolo instantáneo. Para una transición '
                                  'vibracional fundamental activa en IR, el dipolo debe cambiar con la vibración.')
        trails = st.checkbox('Mostrar trayectorias', value=engine.show_trails,
                             disabled=mode == SimulationMode.SINGLE_MOLECULE)
        speed = st.slider('Velocidad del modelo', 0.2, 3.0, float(engine.sim_speed), 0.1)

mode_changed = configure(engine, mode=mode, count=count, temperature=temperature,
                         pressure=pressure, wavelength=wavelength, intensity=intensity,
                         radiation_enabled=radiation_enabled, translation=translation,
                         rotation=rotation, vibration=vibration, dipole=dipole,
                         trails=trails, speed=speed)
if mode_changed:
    session['history'].clear()
    session['ticks'] = 0

units = calculate_spectral_units(engine.radiation.wavelength_um)
st.caption(f"ν̄ = {units['wavenumber_cm']:.1f} cm⁻¹ · "
           f"ν = {units['frequency_thz']:.1f} THz · "
           f"E = {units['energy_ev']:.3f} eV ({units['energy_kj_mol']:.1f} kJ/mol)")
title, explanation = band_explanation(engine.radiation.wavelength_um, engine.mode)
st.markdown(f'**{title}**')
st.write(explanation)
st.caption('Nota cuántica: los estados vibracionales son discretos; la amplitud '
           'del dibujo está exagerada para hacer visible el movimiento.')

play_col, reset_col, step_col = st.columns([1, 1, 1])
if play_col.button('Iniciar / Pausar',
                   type='primary', use_container_width=True):
    session['running'] = not session['running']
if reset_col.button('Reiniciar', use_container_width=True):
    engine.reset_simulation()
    session['history'].clear()
    session['ticks'] = 0
    session['running'] = False
if step_col.button('Avanzar 0.1 s', use_container_width=True,
                   disabled=session['running']):
    session['running'] = True
    advance(session)
    session['running'] = False


@st.fragment(run_every=FRAME_SECONDS if session['running'] else None)
def live_view():
    advance(session)
    stats = engine.get_statistics()
    st.caption('Estado: en marcha' if session['running'] else 'Estado: en pausa')
    st.image(scene_svg(engine), width='stretch', alt='Moléculas de CO₂ y fotones infrarrojos')
    if engine.mode == SimulationMode.ATMOSPHERIC:
        m1, m2, m3, m4 = st.columns(4)
        m1.metric('Tiempo simulado', f'{engine.elapsed_time:.1f} s',
                  help='Reloj del modelo. No representa la escala temporal real de una vibración molecular.')
        m2.metric('Moléculas excitadas', f"{stats['excited_count']}/{stats['total_molecules']}",
                  help='Cantidad excitada en este instante. Puede bajar por reemisión o por colisiones; '
                       'no es el total acumulado de absorciones.')
        m3.metric('Fotones incidentes', stats['photons_emitted'],
                  help='Total generado por la fuente desde el reinicio. No incluye los fotones reemitidos.')
        m4.metric('Absorción incidente', f"{stats['pct_absorbed']:.1f} %",
                  help='100 × fotones de la fuente absorbidos / fotones incidentes. '
                       'Con cero incidentes se muestra 0.0 %.')
        st.caption(f"Fotones de fuente absorbidos: {stats['photons_absorbed']} · "
                   f"Absorciones totales: {stats['total_absorptions']} · "
                   f"Reemisiones: {stats['total_emissions']} · "
                   f"Relajaciones V–T: {stats['collisional_deexcitations']}")
        if show_theory:
            st.caption('**De la luz al movimiento:** absorber IR puede excitar una vibración. '
                       'La molécula puede reemitir un fotón o transferir energía vibracional '
                       'a movimiento traslacional durante una colisión (V–T).')
    else:
        name = mode_label(engine.single_molecule.vibration_mode.name)
        st.caption(f'Demostración manual · 1 molécula · sin flujo de fotones · {name}.')
        st.metric('Tiempo simulado', f'{engine.elapsed_time:.1f} s')
        if show_theory:
            st.caption('**Vibración y dipolo:** ν₂ y ν₃ cambian el momento dipolar y son activos en IR. '
                       'En ν₁ los dipolos se cancelan. Aquí se fuerza el movimiento para observarlo, '
                       'incluso cuando la transición fundamental es IR inactiva.')
    c1, c2 = st.columns(2)
    with c1:
        st.image(spectrum_svg(engine.pressure_atm, engine.radiation.wavelength_um),
                 width='stretch', alt='Espectro de absorción relativo')
        st.caption('Bandas ilustrativas: ν₃ cerca de 4.26 µm y ν₂ cerca de 15 µm. '
                   'El modo ν₁ de 7.50 µm es inactivo en la absorción dipolar fundamental.')
        if show_theory:
            st.caption('**Cómo leer el espectro:** los máximos señalan longitudes de onda '
                       'favorables para la absorción. La curva es el perfil relativo del modelo; '
                       'el porcentaje observado también depende de los encuentros con las moléculas.')
    with c2:
        if session['history']:
            st.image(energy_svg(session['history']), width='stretch',
                     alt='Evolución de energía cinética y vibracional')
        else:
            st.caption('Inicia la simulación para ver la evolución de la energía.')
        st.caption('Las energías cinética y vibracional usan las unidades del modelo.')
        if show_theory:
            st.caption('**Cómo leer la energía:** azul indica movimiento y rojo excitación vibracional. '
                       'Una relajación V–T transforma vibración en traslación. La escala se reajusta '
                       'y la gráfica no incluye la energía de los fotones.')


live_view()
if show_theory:
    with st.expander('Prueba estas ideas'):
        st.markdown('- Compara **15.0 µm y 10.0 µm** con los demás controles iguales: '
                    '¿qué longitud de onda produce mayor absorción?')
        st.markdown('- Mantén λ fija y cambia la **intensidad**: '
                    '¿varía la energía por fotón o la cantidad de fotones incidentes?')
        st.markdown('- Tras excitar moléculas, **apaga la fuente IR sin reiniciar**: '
                    '¿siguen apareciendo reemisiones o relajaciones V–T?')
        st.caption('Para comparar, reinicia antes de cada condición, usa el mismo tiempo simulado '
                   'y repite las corridas: los encuentros son aleatorios.')
with st.expander('Mostrar física: ecuaciones y límites del modelo'):
    st.markdown('**Energía de un fotón:** E = hν = hc/λ. Al disminuir la longitud '
                'de onda, aumenta la energía del fotón. El número de onda es ν̄ = 1/λ '
                '(con las unidades convertidas a cm⁻¹).')
    st.markdown('**Absorción ilustrativa:** la probabilidad del modelo usa dos bandas '
                'cualitativas del CO₂ y se modifica con la presión.')
    st.write(f"Longitud de onda seleccionada: {units['wavelength_um']:.2f} µm · "
             f"Número de onda: {units['wavenumber_cm']:.1f} cm⁻¹ · "
             f"Energía por mol: {units['energy_kj_mol']:.2f} kJ/mol.")
    st.markdown('**Moléculas:** la temperatura inicial modifica la velocidad según √T; '
                'las colisiones transfieren energía en las unidades visuales del modelo. '
                'La geometría y los tiempos de la animación están simplificados con fines docentes.')
    st.markdown('**Regla de selección:** una transición vibracional fundamental es '
                'activa en infrarrojo cuando ∂μ/∂Q ≠ 0. En el CO₂ del modelo, '
                'ν₂ (flexión) y ν₃ (estiramiento asimétrico) son activas; '
                'ν₁ (estiramiento simétrico) es inactiva.')
    st.markdown('**Relajación por colisión:** CO₂* + M → CO₂ + M + ΔE cinética. '
                'El modelo visualiza esta transferencia vibración–traslación (V–T).')
    st.markdown('**Referencia teórica:** I = I₀ exp[−σ(λ)nL] es la ley de Beer–Lambert. '
                'La simulación no ajusta esa ley ni usa secciones eficaces medidas.')
    st.caption('El espectro, las probabilidades, velocidades y tiempos son aproximaciones '
               'pedagógicas. La gráfica de energía muestra solo energía molecular en '
               'unidades del modelo; no incluye la energía de los fotones. La fuente, '
               'reemisión y cambios de controles intercambian energía con el sistema. '
               'No es un modelo climático cuantitativo.')
    st.markdown('**Para consultar:** [energía de los fotones · NASA]'
                '(https://imagine.gsfc.nasa.gov/science/toolbox/emspectrum2.html), '
                '[frecuencias vibracionales del CO₂ · NIST]'
                '(https://cccbdb.nist.gov/compvibs3x.asp?basis=8&casno=124389&charge=0&method=4).')
