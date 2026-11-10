"""The app's words for each knowledge level, and the Learn flashcards.

Beginner text uses no math or Dirac notation. Every level must stay physically correct.
"""

BEGINNER, INTERMEDIATE, ADVANCED = "Beginner", "Intermediate", "Advanced"
LEVELS = (BEGINNER, INTERMEDIATE, ADVANCED)

INTRO = {
    BEGINNER: (
        "Think of a qubit as an arrow on a globe. Pointing up means 0, pointing down means 1, "
        "and anywhere in between is a mix of both. Press the gate buttons to turn the arrow, "
        "then measure to see which answers you get."
    ),
    INTERMEDIATE: (
        "A qubit starts at |0⟩, the top of the sphere. Press gates to move its arrow, "
        "then measure to see what you would actually read out."
    ),
    ADVANCED: (
        "A pure single-qubit state |ψ⟩ = α|0⟩ + β|1⟩ is a point on the Bloch sphere. Apply "
        "gates, inspect the state vector and Bloch angles, and sample measurements in the "
        "computational (Z) basis."
    ),
}

WHAT_IS_A_QUBIT = """
A normal computer **bit** is like a light switch: it is either off (0) or on (1).

A **qubit** is more like an arrow that can point anywhere on a globe. Up is 0, down is 1,
and every other direction is a mix of the two.

When you **measure** a qubit, it has to choose: you always see a plain 0 or 1. Where the
arrow pointed decides the chances. An arrow on the equator gives 0 half the time and 1 half
the time. Measuring also changes the qubit: afterwards, the arrow points at the answer you saw.
"""

GATE_TEXT = {
    BEGINNER: {
        "H": "From 0 or 1, it starts the coin spinning for a 50/50 chance, and a second press undoes it.",
        "X": "Flips 0 and 1, like a light switch.",
        "Y": "Flips 0 and 1 too, with an extra hidden twist.",
        "Z": "Turns the globe half a turn on its stand, so the chances stay the same.",
        "S": "Turns the globe a quarter turn on its stand, so the chances stay the same.",
        "T": "Turns the globe an eighth of a turn on its stand, so the chances stay the same.",
        "Rx": "Tips the arrow by the angle you pick, which can change the chances.",
        "Ry": "Tips the arrow in a different direction by the angle you pick, which can change the chances.",
        "Rz": "Turns the globe on its stand by the angle you pick, so the chances stay the same.",
    },
    INTERMEDIATE: {
        "H": "**Hadamard.** Moves the arrow from |0⟩ at the top to |+⟩ on the equator: a 50/50 superposition. A half-turn around the axis halfway between X and Z.",
        "X": "**Quantum NOT.** Swaps |0⟩ and |1⟩. A half-turn around the X axis.",
        "Y": "**Flip with a twist.** Swaps |0⟩ and |1⟩ and also changes the phase. A half-turn around the Y axis.",
        "Z": "**Phase flip.** Keeps the odds of 0 and 1 but flips the phase. A half-turn around the Z axis.",
        "S": "**Quarter turn.** Rotates 90° around Z. The odds stay the same, only the phase changes.",
        "T": "**Eighth turn.** Rotates 45° around Z. A finer phase step than S.",
        "Rx": "Turns the arrow around the **X** axis by your angle. This can change the odds of 0 and 1.",
        "Ry": "Turns the arrow around the **Y** axis by your angle. This can change the odds too.",
        "Rz": "Turns the arrow around the **Z** axis by your angle. Only the phase changes.",
    },
    ADVANCED: {
        "H": "π rotation about (x̂ + ẑ)/√2. Maps the Z basis to the X basis.",
        "X": "π rotation about x̂. Bit flip.",
        "Y": "π rotation about ŷ. Bit and phase flip, Y = iXZ.",
        "Z": "π rotation about ẑ. Phase flip.",
        "S": "√Z. Equals Rz(π/2) up to a global phase.",
        "T": "√S. Equals Rz(π/4) up to a global phase.",
        "Rx": "Rotation by θ about x̂.",
        "Ry": "Rotation by θ about ŷ. Real amplitudes stay real.",
        "Rz": "Rotation by θ about ẑ. Changes only the relative phase.",
    },
}

# Qiskit's conventions. tests check these against qiskit.quantum_info.Operator.
GATE_MATRIX = {
    "H": r"H = \tfrac{1}{\sqrt{2}}\begin{pmatrix}1 & 1\\ 1 & -1\end{pmatrix}",
    "X": r"X = \begin{pmatrix}0 & 1\\ 1 & 0\end{pmatrix}",
    "Y": r"Y = \begin{pmatrix}0 & -i\\ i & 0\end{pmatrix}",
    "Z": r"Z = \begin{pmatrix}1 & 0\\ 0 & -1\end{pmatrix}",
    "S": r"S = \begin{pmatrix}1 & 0\\ 0 & i\end{pmatrix}",
    "T": r"T = \begin{pmatrix}1 & 0\\ 0 & e^{i\pi/4}\end{pmatrix}",
    "Rx": r"R_x(\theta) = \begin{pmatrix}\cos\frac{\theta}{2} & -i\sin\frac{\theta}{2}\\ -i\sin\frac{\theta}{2} & \cos\frac{\theta}{2}\end{pmatrix}",
    "Ry": r"R_y(\theta) = \begin{pmatrix}\cos\frac{\theta}{2} & -\sin\frac{\theta}{2}\\ \sin\frac{\theta}{2} & \cos\frac{\theta}{2}\end{pmatrix}",
    "Rz": r"R_z(\theta) = \begin{pmatrix}e^{-i\theta/2} & 0\\ 0 & e^{i\theta/2}\end{pmatrix}",
}

UNCHANGED_HINT = {
    BEGINNER: (
        "{gate} ran, but the arrow stayed put. This gate turns the arrow around the "
        "direction it already points, or the turn was 0° or 360°. Try pressing H first, "
        "then this gate."
    ),
    INTERMEDIATE: (
        "{gate} ran, but the arrow stayed put. It already points along the axis this gate "
        "turns around, or the turn was 0° or 360°. Try pressing H first, then this gate."
    ),
    ADVANCED: (
        "{gate} left the Bloch vector unchanged: the state is an eigenstate of this gate, "
        "so only a global phase changed, or θ is a multiple of 360°."
    ),
}

HARDWARE_NOTE = {
    BEGINNER: (
        "**Why are the real bars a little off?** Real quantum computers make small mistakes "
        "because they're very sensitive. A tiny bit of heat or vibration can nudge the qubit, "
        "like a spinning coin wobbling when someone bumps the table. The simulator is a "
        "perfect computer, so it never makes these mistakes."
    ),
    INTERMEDIATE: (
        "**Why don't the real bars match?** A real qubit is a tiny physical object that picks "
        "up noise from its surroundings. It slowly loses its quantum state, which is called "
        "decoherence. Its gates are slightly imperfect, and reading it out sometimes mistakes "
        "a 0 for a 1. So real results land a few percent away from the ideal ones. The "
        "simulator has none of these problems."
    ),
    ADVANCED: (
        "**Error sources.** Decoherence limits how long a qubit holds its state. T1 (energy "
        "relaxation) is the time scale for |1⟩ to decay to |0⟩, and T2 (dephasing) is the "
        "time scale for the relative phase to randomize. Gates carry small calibration errors, "
        "and readout error means the measured outcome is sometimes misassigned. After an X "
        "gate, wrong 0s come mainly from T1 decay and readout error. After an H gate, "
        "dephasing leaves the Z-basis counts unchanged, so the remaining errors are small next "
        "to shot noise."
    ),
}

# Each card: id, title, question (front), explanation and analogy (back), and the
# actions its "Try it" buttons perform: gate names, or "measure".
CONCEPT_CARDS = [
    {
        "id": "bit_vs_qubit",
        "title": "Bit vs qubit",
        "question": "What makes a qubit different from a normal bit?",
        "explanation": (
            "A bit is always exactly 0 or 1. A qubit can point anywhere on a globe: up is 0, "
            "down is 1, and every direction in between is a mix of both."
        ),
        "analogy": (
            "A bit is a light switch, either off or on. A qubit is an arrow that can point "
            "anywhere on a globe."
        ),
        "actions": [],
    },
    {
        "id": "superposition",
        "title": "Superposition",
        "question": "What does it mean for a qubit to be in between 0 and 1?",
        "explanation": (
            "When the arrow points somewhere between up and down, the qubit is in a "
            "superposition: a combination of 0 and 1 that isn't decided yet. Measuring it "
            "forces a choice."
        ),
        "analogy": "A coin spinning in the air is not heads or tails yet.",
        "actions": [],
    },
    {
        "id": "measurement",
        "title": "Measurement",
        "question": "What happens when you look at a qubit?",
        "explanation": (
            "Measuring makes the qubit give a plain 0 or 1. Where the arrow pointed sets the "
            "chances, and afterwards the qubit stays on the answer you saw. To see the "
            "chances, you prepare it and measure it many times."
        ),
        "analogy": (
            "Slapping a spinning coin onto the table: it has to land heads or tails."
        ),
        "actions": [],
    },
    {
        "id": "phase",
        "title": "Phase",
        "question": "Two arrows give the same chances. Can they still be different?",
        "explanation": (
            "Yes. Phase is which way the arrow faces around the equator. A standard 0-or-1 "
            "measurement can't see it, but it matters when you apply more gates, because it "
            "decides how the qubit's waves combine."
        ),
        "analogy": (
            "Two level compass needles pointing different ways: they're at the same height, "
            "but they face different directions."
        ),
        "actions": [],
    },
    {
        "id": "interference",
        "title": "Interference",
        "question": "How do quantum computers make the right answer stand out?",
        "explanation": (
            "Qubit states behave like waves. When waves combine, some parts cancel and some "
            "add up. Quantum algorithms arrange their gates so wrong answers cancel and the "
            "right one grows. Press H twice: the two paths to 1 cancel, so you always get 0."
        ),
        "analogy": (
            "Ripples in a pond: where two crests meet the wave grows, and where a crest meets "
            "a trough they cancel."
        ),
        "actions": [],
    },
    {
        "id": "noise",
        "title": "Why real hardware is noisy",
        "question": "Why do real quantum computers make mistakes?",
        "explanation": (
            "Qubits are extremely sensitive. A tiny bit of heat, vibration or stray signal "
            "nudges the arrow, and over time the qubit loses its state. That's why real "
            "results land a little off, and why IBM keeps its qubits colder than outer space."
        ),
        "analogy": "A coin spinning on a table: any tiny bump knocks it over.",
        "actions": [],
    },
]

GATE_CARDS = [
    {
        "id": "card_h",
        "title": "H gate",
        "question": "How do you start the coin spinning?",
        "explanation": (
            "H moves the arrow from the top of the globe to the equator, which gives a "
            "50/50 chance of 0 or 1. Press it again and the arrow goes back."
        ),
        "analogy": "Flicking a coin so it spins.",
        "actions": ["H"],
    },
    {
        "id": "card_x",
        "title": "X gate",
        "question": "How do you flip a qubit?",
        "explanation": "X swaps 0 and 1: up becomes down, and down becomes up.",
        "analogy": "Flipping a light switch, or turning a coin over.",
        "actions": ["X"],
    },
    {
        "id": "card_y",
        "title": "Y gate",
        "question": "What is a flip with a twist?",
        "explanation": (
            "Y swaps 0 and 1 like X does, and it also flips the phase. You can see the "
            "difference when the arrow starts on the equator: try H, then Y, and compare "
            "with H, then X."
        ),
        "analogy": "Turning a coin over and giving it a half-spin at the same time.",
        "actions": ["Y"],
    },
    {
        "id": "card_z",
        "title": "Z gate",
        "question": "How do you mark an answer without changing the odds?",
        "explanation": (
            "Z turns the arrow halfway around the globe's up-down axis. The chances of 0 and "
            "1 stay the same, but the phase flips. Algorithms use this to mark the right "
            "answer so that interference can make it grow. Press H first to see it move."
        ),
        "analogy": "Turning a globe half a turn on its stand.",
        "actions": ["Z"],
    },
    {
        "id": "card_s_t",
        "title": "S and T gates",
        "question": "Can you turn the arrow in smaller steps?",
        "explanation": (
            "S turns the arrow a quarter of the way around the up-down axis, and T an eighth. "
            "The chances stay the same. They're used to fine-tune the phase."
        ),
        "analogy": "Turning the globe on its stand by a quarter or an eighth of a turn.",
        "actions": ["S", "T"],
    },
    {
        "id": "card_rotations",
        "title": "Rx, Ry and Rz",
        "question": "What if you want to turn by any angle?",
        "explanation": (
            "Rx, Ry and Rz turn the arrow around three different axes by any angle you set "
            "with the slider. Rx and Ry can change the chances. Rz only changes the phase."
        ),
        "analogy": "Three knobs that each turn the arrow by any amount.",
        "actions": ["Rx", "Ry", "Rz"],
    },
    {
        "id": "card_measure",
        "title": "Measure",
        "question": "How do you read a qubit?",
        "explanation": (
            "Measuring is peeking: the qubit must pick 0 or 1. One peek gives one answer, so "
            "you repeat it many times (1024 here) to see the chances."
        ),
        "analogy": (
            "Slapping the spinning coin onto the table over and over, and counting heads and "
            "tails."
        ),
        "actions": ["measure"],
    },
]
