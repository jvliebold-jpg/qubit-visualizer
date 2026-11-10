# Qubit Visualizer

An interactive way to learn how quantum gates work. Apply gates to a single qubit, watch its state move on a 3D Bloch sphere, then measure it on the Qiskit simulator.

![Qubit Visualizer at the Beginner level after applying H and T, showing the knowledge level switch, the qubit's arrow on a globe and a measurement bar chart](docs/screenshot.png)

## Features

- **Gates:** H, X, Y, Z, S and T, plus Rx, Ry and Rz with an angle slider
- **Bloch sphere:** an interactive 3D view you can rotate and zoom
- **Gate history:** the gates applied so far, with a Reset button
- **Measurement:** 1024 shots on the Qiskit Aer simulator, shown as a probability bar chart
- **Knowledge levels:** switch between three levels at the top of the page
  - **Beginner:** everyday analogies with no math or notation, a "What is a qubit?" intro, and just the chances of 0 and 1
  - **Intermediate:** Dirac notation, the state formula, and what each gate does to the arrow
  - **Advanced:** the full complex state vector, gate matrices, Bloch angles θ and φ, shot-noise error bars, and hardware error sources (T1, T2, readout error)
- **Flashcards:** at the Beginner and Intermediate levels, cards on six concepts and seven gates; flip a card to see the answer, and gate cards have "Try it" buttons
- **Real hardware:** run the circuit on a real IBM quantum computer and compare it with the ideal result

## Run it

You need Python and Git. The app was tested on Python 3.14 on macOS.

```bash
git clone https://github.com/jvliebold-jpg/qubit-visualizer.git
cd qubit-visualizer
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/streamlit run app.py
```

Streamlit prints a local address, usually http://localhost:8501. Open it in your browser if it doesn't open by itself. Press `Ctrl+C` in the terminal to stop the app.

## Try this

1. Press **H**. The arrow moves to the equator, giving a 50/50 chance of reading 0 or 1.
2. Press **Measure** and check that the two bars are close to 50%.
3. Press **H** again, then **Measure**. The arrow is back at |0⟩, so every shot reads 0.
4. Press **Reset**, then **Z**. The arrow stays put because it already lies on the Z axis.

## Run on a real IBM quantum computer

The app can send your circuit to the least busy real IBM quantum computer and show the result next to the ideal simulator result. You need a free [IBM Quantum Platform](https://quantum.cloud.ibm.com) account.

1. Copy the template: `cp .env.example .env`
2. On the IBM Quantum Platform dashboard, create an API key and paste it after `QISKIT_IBM_TOKEN=` in `.env`.
3. On the Instances page, copy your instance's CRN (it starts with `crn:v1:`) and paste it after `QISKIT_IBM_INSTANCE=`.
4. Press **Run on real IBM quantum computer** in the app. You don't need to restart it.

Results from the real runs we've done are in [docs/hardware_results.md](docs/hardware_results.md).

`.env` is listed in `.gitignore`, so your key is never committed. Each finished run is saved to `ibm_results.json`, and the app shows the latest one right away when it starts, which is handy for demos. Queues can take minutes or hours, and you can close the page while you wait.

## Notebook

[`qubit_visualizer.ipynb`](qubit_visualizer.ipynb) runs H and X on the Aer simulator, shows their Bloch spheres, and plots the real `ibm_fez` results next to the ideal ones, with a short explanation at each step. It is saved with all outputs, so you can read it on GitHub without running anything.

To run it yourself, install Jupyter into the same virtual environment, then open the notebook. You can also open it in VS Code.

```bash
.venv/bin/python -m pip install jupyter
.venv/bin/jupyter notebook qubit_visualizer.ipynb
```

## How it works

Each press adds a gate to the history, and the app rebuilds a one-qubit Qiskit circuit from that history. The sphere and the probabilities come from the circuit's exact statevector. Measuring runs the same circuit on `AerSimulator`, so the bars show real sampling noise around the exact odds.

Each measurement starts again from the full circuit, so measuring doesn't collapse the qubit in the app. You can keep adding gates afterwards.

## Project files

| File | Purpose |
| --- | --- |
| `app.py` | The Streamlit app |
| `content.py` | The text for each knowledge level, and the flashcards |
| `qubit_visualizer.ipynb` | Notebook comparing simulator and real hardware results |
| `docs/REQUIREMENTS.md` | Product, technical, flow, design, data and plan overview |
| `docs/hardware_results.md` | Results from the real IBM runs |
| `ibm_hardware.py` | Connects to IBM Quantum, submits jobs and saves results |
| `.env.example` | Template for your IBM credentials |
| `qiskit_preload.py` | Loads Qiskit on a long-lived thread to prevent a crash under Streamlit. Keep its import above the Qiskit imports in `app.py`. |
| `requirements.txt` | Pinned dependencies |
| `.streamlit/config.toml` | Accent colors for the light and dark themes |

## Known limitation

The sphere returns to its default view whenever the arrow moves, because Streamlit rebuilds the chart when its data changes.
