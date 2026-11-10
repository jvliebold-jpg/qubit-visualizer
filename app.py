"""Qubit Visualizer: apply gates to one qubit and watch it move on the Bloch sphere."""

import math
from datetime import datetime, timezone

import numpy as np
import plotly.graph_objects as go
import streamlit as st

import qiskit_preload  # noqa: F401  Must stay above the qiskit imports.
from qiskit import QuantumCircuit, transpile
from qiskit.quantum_info import Pauli, Statevector
from qiskit_aer import AerSimulator

import ibm_hardware
from content import (
    ADVANCED,
    BEGINNER,
    CONCEPT_CARDS,
    GATE_CARDS,
    GATE_MATRIX,
    GATE_TEXT,
    HARDWARE_NOTE,
    INTERMEDIATE,
    INTRO,
    LEVELS,
    UNCHANGED_HINT,
    WHAT_IS_A_QUBIT,
)

SHOTS = 1024
FIXED_GATES = ["H", "X", "Y", "Z", "S", "T"]
ROTATION_GATES = ["Rx", "Ry", "Rz"]

# Chart colors, chosen separately for Streamlit's light and dark themes.
LIGHT_COLORS = {
    "accent": "#2a78d6",
    "accent2": "#eb6834",
    "text": "#0b0b0b",
    "muted": "#52514e",
    "line": "#b9b8b2",
    "sphere": "#8a8a84",
}
DARK_COLORS = {
    "accent": "#3987e5",
    "accent2": "#d95926",
    "text": "#f0efec",
    "muted": "#c3c2b7",
    "line": "#5c5b56",
    "sphere": "#a8a79f",
}

# Sphere labels: (x, y, z, text). Beginners see plain 0 and 1 at the poles only.
PLAIN_LABELS = [(0, 0, 1.2, "0"), (0, 0, -1.2, "1")]
DIRAC_LABELS = [
    (0, 0, 1.2, "|0⟩"),
    (0, 0, -1.2, "|1⟩"),
    (1.15, 0, 0, "|+⟩"),
    (-1.15, 0, 0, "|−⟩"),
    (0, 1.15, 0, "|+i⟩"),
    (0, -1.15, 0, "|−i⟩"),
]


def build_circuit(history):
    """Turn the gate history into a one-qubit Qiskit circuit."""
    circuit = QuantumCircuit(1)
    for gate, degrees in history:
        if degrees is None:
            getattr(circuit, gate.lower())(0)
        else:
            getattr(circuit, gate.lower())(math.radians(degrees), 0)
    return circuit


def bloch_vector(state):
    """Return the (x, y, z) point on the Bloch sphere for a state."""
    return np.array([state.expectation_value(Pauli(axis)).real for axis in "XYZ"])


def bloch_angles(point):
    """Return (theta, phi) in degrees. Phi is None at the poles, where it is undefined."""
    x, y, z = point
    theta = math.degrees(math.acos(max(-1.0, min(1.0, z))))
    if math.hypot(x, y) < 1e-9:
        return theta, None
    return theta, math.degrees(math.atan2(y, x)) % 360


def gate_label(gate, degrees):
    return gate if degrees is None else f"{gate}({degrees}°)"


def history_text(history, level):
    start = "Start (0)" if level == BEGINNER else "|0⟩"
    if not history:
        return f"{start}, no gates"
    return f"{start} → " + " → ".join(f"`{gate_label(*step)}`" for step in history)


def format_amplitude(value, minus="−"):
    real, imag = round(value.real, 3) + 0.0, round(value.imag, 3) + 0.0
    if imag == 0:
        return f"{real:g}".replace("-", minus)
    if real == 0:
        return f"{imag:g}i".replace("-", minus)
    sign = "+" if imag > 0 else minus
    return f"({real:g} {sign} {abs(imag):g}i)".replace("-", minus)


def format_state(state):
    alpha, beta = state.data
    terms = [
        (format_amplitude(amplitude), ket)
        for amplitude, ket in ((alpha, "|0⟩"), (beta, "|1⟩"))
        if abs(amplitude) > 5e-4
    ]
    return " + ".join(f"{amplitude} {ket}" for amplitude, ket in terms).replace("+ −", "− ")


def bloch_figure(point, colors, labels):
    x, y, z = point

    # Faint globe with an equator and two meridians for depth.
    theta, phi = np.mgrid[0 : math.pi : 40j, 0 : 2 * math.pi : 40j]
    sphere = go.Surface(
        x=np.sin(theta) * np.cos(phi),
        y=np.sin(theta) * np.sin(phi),
        z=np.cos(theta),
        opacity=0.12,
        colorscale=[[0, colors["sphere"]], [1, colors["sphere"]]],
        showscale=False,
        hoverinfo="skip",
    )
    circle = np.linspace(0, 2 * math.pi, 120)
    zeros = np.zeros_like(circle)
    rings = [
        (np.cos(circle), np.sin(circle), zeros),
        (np.cos(circle), zeros, np.sin(circle)),
        (zeros, np.cos(circle), np.sin(circle)),
    ]
    axes = [
        ([-1, 1], [0, 0], [0, 0]),
        ([0, 0], [-1, 1], [0, 0]),
        ([0, 0], [0, 0], [-1, 1]),
    ]
    guides = [
        go.Scatter3d(
            x=gx,
            y=gy,
            z=gz,
            mode="lines",
            line={"color": colors["line"], "width": 2},
            hoverinfo="skip",
        )
        for gx, gy, gz in rings + axes
    ]

    label_trace = go.Scatter3d(
        x=[label[0] for label in labels],
        y=[label[1] for label in labels],
        z=[label[2] for label in labels],
        mode="text",
        text=[label[3] for label in labels],
        textfont={"color": colors["text"], "size": 18},
        hoverinfo="skip",
    )

    # The shaft stops short of the surface so the cone forms the arrow's tip.
    shaft = go.Scatter3d(
        x=[0, 0.88 * x],
        y=[0, 0.88 * y],
        z=[0, 0.88 * z],
        mode="lines",
        line={"color": colors["accent"], "width": 8},
        hoverinfo="skip",
    )
    tip = go.Cone(
        x=[x],
        y=[y],
        z=[z],
        u=[x],
        v=[y],
        w=[z],
        anchor="tip",
        sizemode="raw",
        sizeref=0.16,
        colorscale=[[0, colors["accent"]], [1, colors["accent"]]],
        showscale=False,
        hovertemplate=f"x = {x:.3f}<br>y = {y:.3f}<br>z = {z:.3f}<extra></extra>",
    )

    hidden_axis = {
        "visible": False,
        "range": [-1.35, 1.35],
        "showspikes": False,
    }
    figure = go.Figure([sphere, *guides, label_trace, shaft, tip])
    figure.update_layout(
        height=480,
        margin={"l": 0, "r": 0, "t": 0, "b": 0},
        paper_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        scene={
            "xaxis": hidden_axis,
            "yaxis": hidden_axis,
            "zaxis": hidden_axis,
            "aspectmode": "cube",
            "bgcolor": "rgba(0,0,0,0)",
            "camera": {"eye": {"x": 1.3, "y": 0.78, "z": 0.39}},
        },
    )
    return figure


def probability_figure(series, colors, outcome_labels):
    """Bar chart of measured probabilities. `series` is a list of (name, counts, color)."""
    grouped = len(series) > 1
    figure = go.Figure()
    for name, counts, color in series:
        shots = [counts.get(outcome, 0) for outcome in ("0", "1")]
        total = sum(counts.values())
        probabilities = [count / total for count in shots]
        figure.add_bar(
            name=name,
            x=outcome_labels,
            y=probabilities,
            width=None if grouped else 0.45,
            marker={"color": color, "cornerradius": 4},
            text=[f"{p:.1%}" for p in probabilities],
            textposition="outside",
            textfont={"color": colors["text"], "size": 16},
            cliponaxis=False,
            customdata=shots,
            hovertemplate=(
                f"{name}<br>%{{x}}: %{{customdata}} of {total} shots (%{{y:.1%}})"
                "<extra></extra>"
            ),
        )
    figure.update_layout(
        height=320 if grouped else 300,
        margin={"l": 8, "r": 8, "t": 48 if grouped else 28, "b": 24},
        showlegend=grouped,
        legend={
            "orientation": "h",
            "x": 0,
            "y": 1.02,
            "yanchor": "bottom",
            "font": {"color": colors["text"]},
        },
        bargap=0.3,
        bargroupgap=0.06,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": colors["muted"], "size": 14},
        yaxis={
            "title": "Probability",
            "automargin": True,
            "range": [0, 1],
            "tickformat": ".0%",
            "gridcolor": colors["line"],
            "gridwidth": 1,
            "zeroline": False,
        },
        # Category, so plain "0" and "1" labels aren't read as numbers on a numeric axis.
        xaxis={
            "type": "category",
            "automargin": True,
            "tickfont": {"size": 17, "color": colors["text"]},
        },
    )
    return figure


@st.cache_resource
def simulator():
    return AerSimulator()


def add_gate(gate, degrees=None):
    st.session_state.history.append((gate, degrees))
    st.session_state.counts = None


def reset():
    st.session_state.history = []
    st.session_state.counts = None


def simulate(history):
    circuit = build_circuit(history)
    circuit.measure_all()
    backend = simulator()
    return backend.run(transpile(circuit, backend), shots=SHOTS).result().get_counts()


def measure():
    st.session_state.counts = simulate(st.session_state.history)


def try_action(action):
    """Run a flashcard's "Try it" action: apply a gate, or measure."""
    if action == "measure":
        measure()
        st.toast("Measured 1024 shots. See the Measurement section.")
        return
    degrees = st.session_state.angle if action in ROTATION_GATES else None
    add_gate(action, degrees)
    st.toast(f"Applied {gate_label(action, degrees)}. Watch the arrow below.")


def toggle_card(card_id):
    st.session_state.flipped ^= {card_id}


def action_label(action):
    if action == "measure":
        return "Try it: Measure"
    if action in ROTATION_GATES:
        return f"Try {action}({st.session_state.angle}°)"
    return f"Try it: {action}"


def flashcard(card):
    flipped = card["id"] in st.session_state.flipped
    with st.container(border=True):
        st.markdown(f"##### {card['title']}")
        if flipped:
            st.write(card["explanation"])
            st.markdown(f"**Everyday picture:** {card['analogy']}")
        else:
            st.markdown(f"*{card['question']}*")
        with st.container(horizontal=True):
            st.button(
                "Show question" if flipped else "Flip to see the answer",
                key=f"flip_{card['id']}",
                on_click=toggle_card,
                args=(card["id"],),
            )
            for action in card["actions"]:
                st.button(
                    action_label(action),
                    key=f"try_{card['id']}_{action}",
                    type="primary",
                    on_click=try_action,
                    args=(action,),
                )


def card_grid(cards):
    for row_start in range(0, len(cards), 3):
        for column, card in zip(st.columns(3), cards[row_start : row_start + 3]):
            with column:
                flashcard(card)


def show_state(state, point, level):
    """The readout under the sphere, with as much detail as the level calls for."""
    prob_zero, prob_one = state.probabilities()
    if level == BEGINNER:
        zero_metric, one_metric = st.columns(2)
        zero_metric.metric("Chance of 0", f"{prob_zero:.0%}")
        one_metric.metric("Chance of 1", f"{prob_one:.0%}")
        return

    if level == INTERMEDIATE:
        st.markdown(f"**State:** |ψ⟩ = {format_state(state)}")
        zero_metric, one_metric = st.columns(2)
        zero_metric.metric("Chance of reading 0", f"{prob_zero:.1%}")
        one_metric.metric("Chance of reading 1", f"{prob_one:.1%}")
        return

    alpha, beta = state.data
    st.latex(
        r"|\psi\rangle = \begin{pmatrix}"
        + format_amplitude(alpha, minus="-")
        + r"\\"
        + format_amplitude(beta, minus="-")
        + r"\end{pmatrix}"
    )
    rows = ["| Basis | Amplitude | Magnitude | Phase | Probability |", "| --- | --- | --- | --- | --- |"]
    for ket, amplitude, probability in (("\\|0⟩", alpha, prob_zero), ("\\|1⟩", beta, prob_one)):
        phase = f"{math.degrees(np.angle(amplitude)):.1f}°" if abs(amplitude) > 5e-4 else "n/a"
        rows.append(
            f"| {ket} | {format_amplitude(amplitude)} | {abs(amplitude):.3f} | {phase} "
            f"| {probability:.1%} |"
        )
    st.markdown("\n".join(rows))

    theta, phi = bloch_angles(point)
    theta_metric, phi_metric = st.columns(2)
    theta_metric.metric("Polar angle θ", f"{theta:.1f}°")
    phi_metric.metric("Azimuth φ", "undefined" if phi is None else f"{phi:.1f}°")
    x, y, z = point
    st.caption(
        f"Bloch vector (x, y, z) = ({x:.3f}, {y:.3f}, {z:.3f}). θ = 2·arccos|α| and "
        "φ = arg β − arg α. The sphere ignores global phase, so the overall phase of α "
        "does not move the arrow."
    )


@st.cache_resource(show_spinner=False)
def ibm_service(token, instance):
    return ibm_hardware.connect(token, instance)


def run_on_hardware(credentials):
    history = list(st.session_state.history)
    circuit = build_circuit(history)
    circuit.measure_all()
    job_id, backend = ibm_hardware.submit(ibm_service(*credentials), circuit, SHOTS)
    store = ibm_hardware.load_store()
    store["pending"] = {
        "job_id": job_id,
        "backend": backend,
        "gates": history,
        "shots": SHOTS,
        "submitted_at": ibm_hardware.now(),
        "ideal_counts": simulate(history),
    }
    ibm_hardware.save_store(store)


def local_time(timestamp):
    return datetime.fromisoformat(timestamp).astimezone().strftime("%b %d, %H:%M")


JOB_STATUS_TEXT = {
    "INITIALIZING": "IBM is preparing your job.",
    "QUEUED": "Waiting in line for the quantum computer.",
    "RUNNING": "Running on the quantum computer now.",
}


@st.fragment(run_every=15)
def pending_job_panel(credentials):
    """Check a submitted job every 15 seconds and save its result when it finishes."""
    store = ibm_hardware.load_store()
    pending = store["pending"]
    if pending is None:
        return
    if credentials is None:
        st.warning(
            f"Job `{pending['job_id']}` is still open, but the IBM credentials are missing "
            "from .env, so the app can't check on it."
        )
        return

    try:
        service = ibm_service(*credentials)
        status, message = ibm_hardware.job_status(service, pending["job_id"])
        if status == "DONE":
            pending["real_counts"] = ibm_hardware.job_counts(service, pending["job_id"])
    except Exception as error:
        st.warning(f"Couldn't check the job status. Trying again in 15 seconds. ({error})")
        return

    if status in ibm_hardware.FINAL_STATUSES:
        # Re-read the file: another open tab may have saved this job while we were checking.
        store = ibm_hardware.load_store()
        if (store["pending"] or {}).get("job_id") != pending["job_id"]:
            st.rerun()
        if status == "DONE":
            pending["finished_at"] = ibm_hardware.now()
            store["results"].append(pending)
        else:
            st.session_state.ibm_error = f"The job ended with status {status}. {message or ''}"
        store["pending"] = None
        ibm_hardware.save_store(store)
        st.rerun()

    waited = datetime.now(timezone.utc) - datetime.fromisoformat(pending["submitted_at"])
    minutes = int(waited.total_seconds() // 60)
    waited_text = "under a minute" if minutes == 0 else f"{minutes} min"
    st.info(
        f"**{status.title()}:** {JOB_STATUS_TEXT.get(status, '')}  \n"
        f"`{pending['backend']}` · job `{pending['job_id']}` · "
        f"waited {waited_text}. Checks again every 15 seconds."
    )
    if st.button("Cancel job"):
        try:
            ibm_hardware.cancel(service, pending["job_id"])
        except Exception as error:
            st.session_state.ibm_error = f"IBM didn't confirm the cancel: {error}"
        store["pending"] = None
        ibm_hardware.save_store(store)
        st.rerun()


st.set_page_config(page_title="Qubit Visualizer", page_icon="⚛️", layout="wide")

# Readability: taller buttons with bolder labels, explanations larger than Streamlit's
# default caption size, and more room between sections.
st.html(
    """
    <style>
    .stButton button { min-height: 3rem; padding: 0.5rem 1.1rem; }
    .stButton button p { font-size: 1.05rem; font-weight: 600; }
    [data-testid="stCaptionContainer"] { font-size: 0.95rem; line-height: 1.6; }
    [data-testid="stMarkdownContainer"] p { line-height: 1.6; }
    hr { margin: 2.5rem 0 !important; }
    /* Wide tables scroll inside their own box instead of the whole page on phones. */
    [data-testid="stMarkdownContainer"] table { display: block; overflow-x: auto; }
    /* Gate matrices must fit their narrow columns at the larger font size. */
    [data-testid="stColumn"] .katex-display > .katex { font-size: 1em; }
    </style>
    """
)

st.session_state.setdefault("history", [])
st.session_state.setdefault("counts", None)
st.session_state.setdefault("ibm_error", None)
st.session_state.setdefault("flipped", set())
st.session_state.setdefault("angle", 90)

colors = DARK_COLORS if st.context.theme.type == "dark" else LIGHT_COLORS

st.title("Qubit Visualizer")
level = st.segmented_control(
    "Knowledge level", LEVELS, default=BEGINNER, required=True, key="level"
)
st.write(INTRO[level])

if level == BEGINNER:
    with st.expander("What is a qubit?"):
        st.markdown(WHAT_IS_A_QUBIT)

if level in (BEGINNER, INTERMEDIATE):
    with st.expander("Learn with flashcards"):
        st.caption("Flip a card to see the answer. Gate cards have buttons to try the gate.")
        concepts_tab, gates_tab = st.tabs(["Concepts", "Gates"])
        with concepts_tab:
            card_grid(CONCEPT_CARDS)
        with gates_tab:
            card_grid(GATE_CARDS)

history = st.session_state.history
state = Statevector(build_circuit(history))
point = bloch_vector(state)
prob_zero, prob_one = state.probabilities()
outcome_labels = ["0", "1"] if level == BEGINNER else ["|0⟩", "|1⟩"]

gates_column, sphere_column = st.columns([5, 6], gap="large")


def gate_explanation(gate):
    st.caption(GATE_TEXT[level][gate])
    # Rotation matrices are too wide for a column; they are shown below the buttons.
    if level == ADVANCED and gate not in ROTATION_GATES:
        st.latex(GATE_MATRIX[gate])


with gates_column:
    st.subheader("Gates")
    for row_start in range(0, len(FIXED_GATES), 3):
        for column, gate in zip(st.columns(3), FIXED_GATES[row_start : row_start + 3]):
            with column:
                st.button(
                    gate, key=f"gate_{gate}", width="stretch", on_click=add_gate, args=(gate,)
                )
                gate_explanation(gate)

    st.subheader("Turn by any angle" if level == BEGINNER else "Rotations")
    angle = st.slider("Angle (degrees)", min_value=0, max_value=360, step=15, key="angle")
    for column, gate in zip(st.columns(3), ROTATION_GATES):
        with column:
            st.button(
                f"{gate}({angle}°)",
                key=f"gate_{gate}",
                width="stretch",
                on_click=add_gate,
                args=(gate, angle),
            )
            gate_explanation(gate)
    if level == ADVANCED:
        for gate in ROTATION_GATES:
            st.latex(GATE_MATRIX[gate])

with sphere_column:
    st.subheader("Your qubit's arrow" if level == BEGINNER else "Bloch sphere")
    st.plotly_chart(
        bloch_figure(point, colors, PLAIN_LABELS if level == BEGINNER else DIRAC_LABELS),
        key="bloch",
        theme=None,
    )
    if level == BEGINNER:
        st.caption(
            "Up is 0, down is 1. Drag to look around the globe. The view resets when the "
            "arrow moves."
        )
    else:
        st.caption("Drag to rotate, scroll to zoom. The view resets when the arrow moves.")

    if history:
        previous = bloch_vector(Statevector(build_circuit(history[:-1])))
        if np.allclose(previous, point, atol=1e-9):
            st.info(UNCHANGED_HINT[level].format(gate=gate_label(*history[-1])))

    show_state(state, point, level)

st.divider()

history_column, measure_column = st.columns([5, 6], gap="large")

with history_column:
    st.subheader("Gate history")
    if history:
        st.markdown(history_text(history, level))
    else:
        st.caption(
            "No gates yet. The arrow points up, at 0."
            if level == BEGINNER
            else "No gates yet. The qubit is in |0⟩."
        )
    st.button("Reset", on_click=reset, disabled=not history)

with measure_column:
    st.subheader("Measurement")
    st.button(
        f"Measure ({SHOTS} shots)",
        type="primary",
        on_click=measure,
    )
    counts = st.session_state.counts
    if counts is None:
        if level == BEGINNER:
            st.caption(
                "Each shot is like slapping a spinning coin onto the table: it lands on 0 or 1. "
                f"Doing it {SHOTS} times shows the chances. Your gates stay as they are, so "
                "you can keep going afterwards."
            )
        elif level == INTERMEDIATE:
            st.caption(
                "Each shot prepares your qubit from scratch and reads it once as 0 or 1. "
                "Your circuit stays as it is, so you can keep adding gates afterwards."
            )
        else:
            st.caption(
                f"Samples {SHOTS} shots in the computational (Z) basis on AerSimulator. Each "
                "shot re-prepares the state, so the circuit is not collapsed."
            )
    else:
        st.plotly_chart(
            probability_figure(
                [("Simulator", counts, colors["accent"])], colors, outcome_labels
            ),
            key="measurement",
            theme=None,
        )
        if level == BEGINNER:
            st.caption(
                f"Expected chances: {prob_zero:.0%} for 0 and {prob_one:.0%} for 1. Each batch "
                "of shots lands close to these, but not exactly."
            )
        elif level == INTERMEDIATE:
            st.caption(
                f"Exact odds: {prob_zero:.1%} for 0 and {prob_one:.1%} for 1. "
                "Real shots land near these but not exactly on them, so measuring again "
                "gives slightly different bars."
            )
        else:
            sigma = math.sqrt(prob_zero * prob_one / SHOTS)
            st.caption(
                f"Expected P(0) = |α|² = {prob_zero:.3f}, with a 1σ shot-noise spread of "
                f"±{sigma:.3f} for {SHOTS} shots (binomial)."
            )

st.divider()

hardware_column, comparison_column = st.columns([5, 6], gap="large")
ibm_credentials = ibm_hardware.credentials()
ibm_store = ibm_hardware.load_store()

with hardware_column:
    st.subheader("Real IBM quantum computer")
    st.write(
        "Send your circuit to a real quantum computer at IBM. The app picks the least "
        f"busy one and runs {SHOTS} shots."
    )
    if ibm_credentials is None:
        st.info(
            "To turn this on, add your IBM Quantum API key and instance CRN to the "
            "`.env` file in the project folder. The README explains how."
        )
    if st.button(
        "Run on real IBM quantum computer",
        type="primary",
        disabled=ibm_credentials is None or ibm_store["pending"] is not None,
    ):
        st.session_state.ibm_error = None
        try:
            with st.spinner("Connecting to IBM Quantum and picking a computer..."):
                run_on_hardware(ibm_credentials)
        except Exception as error:
            st.session_state.ibm_error = f"Couldn't submit the job: {error}"
        st.rerun()
    st.caption(
        f"Runs the circuit in Gate history: {history_text(history, level)}. This uses a few "
        "seconds of your IBM Quantum time. Waiting in the queue can take minutes or hours, "
        "and you can close the page while you wait."
    )
    if st.session_state.ibm_error:
        st.error(st.session_state.ibm_error)
    pending_job_panel(ibm_credentials)

with comparison_column:
    results = ibm_store["results"]
    if results:
        last = results[-1]
        ideal_name = "Perfect simulator" if level == BEGINNER else "Ideal (simulator)"
        st.markdown(
            f"**Last real result** on `{last['backend']}` · "
            f"{history_text(last['gates'], level)}"
        )
        st.plotly_chart(
            probability_figure(
                [
                    (ideal_name, last["ideal_counts"], colors["accent"]),
                    (f"Real ({last['backend']})", last["real_counts"], colors["accent2"]),
                ],
                colors,
                outcome_labels,
            ),
            key="hardware_comparison",
            theme=None,
        )
        st.caption(
            f"Finished {local_time(last['finished_at'])} · job `{last['job_id']}` · "
            f"{len(results)} real run{'s' if len(results) != 1 else ''} saved in "
            f"`{ibm_hardware.RESULTS_FILE.name}`"
        )
    else:
        st.caption("No real results yet. Your first finished run will appear here.")
    st.info(HARDWARE_NOTE[level])
