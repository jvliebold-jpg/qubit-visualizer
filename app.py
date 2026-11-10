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

SHOTS = 1024

FIXED_GATES = {
    "H": "**Hadamard.** Makes a superposition: from |0⟩ the qubit becomes a 50/50 mix of 0 and 1.",
    "X": "**Quantum NOT.** Swaps 0 and 1. It is a half-turn around the X axis.",
    "Y": "**Flip with a twist.** Swaps 0 and 1 and also shifts the phase. A half-turn around Y.",
    "Z": "**Phase flip.** Keeps the odds of 0 and 1 but flips the phase. A half-turn around Z.",
    "S": "**Quarter turn.** Rotates 90° around Z. The odds stay the same, only the phase changes.",
    "T": "**Eighth turn.** Rotates 45° around Z. A finer phase step than S.",
}

ROTATION_GATES = {
    "Rx": "Turns the arrow around the **X** axis by your angle. This changes the odds of 0 and 1.",
    "Ry": "Turns the arrow around the **Y** axis by your angle. This also changes the odds.",
    "Rz": "Turns the arrow around the **Z** axis by your angle. Only the phase changes.",
}

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


def gate_label(gate, degrees):
    return gate if degrees is None else f"{gate}({degrees}°)"


def history_text(history):
    if not history:
        return "|0⟩ (no gates)"
    return "|0⟩ → " + " → ".join(f"`{gate_label(*step)}`" for step in history)


def format_amplitude(value):
    real, imag = round(value.real, 3) + 0.0, round(value.imag, 3) + 0.0
    if imag == 0:
        return f"{real:g}"
    if real == 0:
        return f"{imag:g}i"
    return f"({real:g} {'+' if imag > 0 else '−'} {abs(imag):g}i)"


def format_state(state):
    alpha, beta = state.data
    terms = [
        (format_amplitude(amplitude), ket)
        for amplitude, ket in ((alpha, "|0⟩"), (beta, "|1⟩"))
        if abs(amplitude) > 5e-4
    ]
    return " + ".join(f"{amplitude} {ket}" for amplitude, ket in terms).replace("+ -", "− ")


def bloch_figure(point, colors):
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

    labels = go.Scatter3d(
        x=[0, 0, 1.22, -1.22, 0, 0],
        y=[0, 0, 0, 0, 1.22, -1.22],
        z=[1.2, -1.2, 0, 0, 0, 0],
        mode="text",
        text=["|0⟩", "|1⟩", "|+⟩", "|−⟩", "|+i⟩", "|−i⟩"],
        textfont={"color": colors["text"], "size": 15},
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
    figure = go.Figure([sphere, *guides, labels, shaft, tip])
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
            "camera": {"eye": {"x": 1.0, "y": 0.6, "z": 0.3}},
        },
    )
    return figure


def probability_figure(series, colors):
    """Bar chart of measured probabilities. `series` is a list of (name, counts, color)."""
    grouped = len(series) > 1
    figure = go.Figure()
    for name, counts, color in series:
        shots = [counts.get(outcome, 0) for outcome in ("0", "1")]
        total = sum(counts.values())
        probabilities = [count / total for count in shots]
        figure.add_bar(
            name=name,
            x=["|0⟩", "|1⟩"],
            y=probabilities,
            width=None if grouped else 0.45,
            marker={"color": color, "cornerradius": 4},
            text=[f"{p:.1%}" for p in probabilities],
            textposition="outside",
            textfont={"color": colors["text"], "size": 14},
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
        font={"color": colors["muted"]},
        yaxis={
            "title": "Probability",
            "automargin": True,
            "range": [0, 1],
            "tickformat": ".0%",
            "gridcolor": colors["line"],
            "gridwidth": 1,
            "zeroline": False,
        },
        xaxis={"automargin": True, "tickfont": {"size": 15, "color": colors["text"]}},
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

st.session_state.setdefault("history", [])
st.session_state.setdefault("counts", None)
st.session_state.setdefault("ibm_error", None)

colors = DARK_COLORS if st.context.theme.type == "dark" else LIGHT_COLORS

history = st.session_state.history
state = Statevector(build_circuit(history))
point = bloch_vector(state)
prob_zero, prob_one = state.probabilities()

st.title("Qubit Visualizer")
st.write(
    "A qubit starts at |0⟩, the top of the sphere. Press gates to move its arrow, "
    "then measure to see what you would actually read out."
)

gates_column, sphere_column = st.columns([5, 6], gap="large")

with gates_column:
    st.subheader("Gates")
    gate_names = list(FIXED_GATES)
    for row_start in range(0, len(gate_names), 3):
        for column, gate in zip(st.columns(3), gate_names[row_start : row_start + 3]):
            with column:
                st.button(
                    gate, key=f"gate_{gate}", width="stretch", on_click=add_gate, args=(gate,)
                )
                st.caption(FIXED_GATES[gate])

    st.subheader("Rotations")
    angle = st.slider("Angle (degrees)", min_value=0, max_value=360, value=90, step=15)
    for column, (gate, explanation) in zip(st.columns(3), ROTATION_GATES.items()):
        with column:
            st.button(
                f"{gate}({angle}°)",
                key=f"gate_{gate}",
                width="stretch",
                on_click=add_gate,
                args=(gate, angle),
            )
            st.caption(explanation)

with sphere_column:
    st.subheader("Bloch sphere")
    st.plotly_chart(bloch_figure(point, colors), key="bloch", theme=None)
    st.caption("Drag to rotate, scroll to zoom. The view resets when the arrow moves.")

    if history:
        previous = bloch_vector(Statevector(build_circuit(history[:-1])))
        if np.allclose(previous, point, atol=1e-9):
            st.info(
                f"{gate_label(*history[-1])} ran, but the arrow stayed put. It already "
                "points along the axis this gate turns around, or the turn was 0° or 360°. "
                "Try pressing H first, then this gate."
            )

    st.markdown(f"**State:** |ψ⟩ = {format_state(state)}")
    zero_metric, one_metric = st.columns(2)
    zero_metric.metric("Chance of reading 0", f"{prob_zero:.1%}")
    one_metric.metric("Chance of reading 1", f"{prob_one:.1%}")

st.divider()

history_column, measure_column = st.columns([5, 6], gap="large")

with history_column:
    st.subheader("Gate history")
    if history:
        st.markdown(history_text(history))
    else:
        st.caption("No gates yet. The qubit is in |0⟩.")
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
        st.caption(
            "Each shot prepares your qubit from scratch and reads it once as 0 or 1. "
            "Your circuit stays as it is, so you can keep adding gates afterwards."
        )
    else:
        st.plotly_chart(
            probability_figure([("Simulator", counts, colors["accent"])], colors),
            key="measurement",
            theme=None,
        )
        st.caption(
            f"Exact odds: {prob_zero:.1%} for 0 and {prob_one:.1%} for 1. "
            "Real shots land near these but not exactly on them, so measuring again "
            "gives slightly different bars."
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
        f"Runs the circuit in Gate history: {history_text(history)}. This uses a few "
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
        st.markdown(
            f"**Last real result** on `{last['backend']}` · {history_text(last['gates'])}"
        )
        st.plotly_chart(
            probability_figure(
                [
                    ("Ideal (simulator)", last["ideal_counts"], colors["accent"]),
                    (f"Real ({last['backend']})", last["real_counts"], colors["accent2"]),
                ],
                colors,
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
    st.info(
        "**Why don't the real bars match?** A real qubit is a tiny physical object that "
        "picks up noise from its surroundings. It slowly loses its quantum state, which is "
        "called decoherence. Its gates are slightly imperfect, and reading it out sometimes "
        "mistakes a 0 for a 1. So real results land a few percent away from the ideal ones. "
        "The simulator has none of these problems."
    )
