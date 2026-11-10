# Results from real IBM quantum hardware

Two one-qubit circuits were run from the Qubit Visualizer app on IBM's real quantum computer `ibm_fez`. The app chose it automatically as the least busy available backend. Each circuit was also run on the noiseless Qiskit Aer simulator for comparison.

## Runs

| Circuit | Backend | Job ID | Submitted (UTC) | Finished (UTC) |
| --- | --- | --- | --- | --- |
| \|0⟩ → H | `ibm_fez` | `dbpp2doou4as73cu1dtg` | 2026-11-10 20:45:45 | 2026-11-10 20:46:02 |
| \|0⟩ → X | `ibm_fez` | `dbpp4b0ou4as73cu1g30` | 2026-11-10 21:52:44 | 2026-11-10 21:53:00 |

## Counts (1024 shots each)

| Circuit | Outcome | Ideal (Aer simulator) | Real (`ibm_fez`) |
| --- | --- | --- | --- |
| H | 0 | 526 (51.4%) | 502 (49.0%) |
| H | 1 | 498 (48.6%) | 522 (51.0%) |
| X | 0 | 0 (0.0%) | 40 (3.9%) |
| X | 1 | 1024 (100.0%) | 984 (96.1%) |

## What the results show

- **H:** the exact answer is 50/50. With 1024 shots, random sampling alone moves a 50% result by about ±1.6 percentage points (one standard deviation). Both the simulator (51.4%) and the hardware (49.0%) fall inside that range, so this run doesn't separate hardware noise from ordinary chance.
- **X:** the exact answer is 1 on every shot, and the simulator gave exactly that. The hardware read 0 on 40 of 1024 shots (3.9%). These are hardware errors. Common causes on superconducting qubits are T1 relaxation, where the excited |1⟩ state decays to |0⟩ before or during readout, and readout assignment error, where the measurement misreads the state. This run doesn't measure how much each one contributed.

## Method

- **App:** circuits were built in the app from the gate buttons, with `measure_all()` added.
- **Hardware run:** `qiskit-ibm-runtime` 0.52.0 chose the least busy operational backend with `QiskitRuntimeService.least_busy`. The circuit was transpiled for that backend with `generate_preset_pass_manager(optimization_level=1)` and run with `SamplerV2` at 1024 shots.
- **Ideal run:** the same circuit ran on Qiskit Aer 0.18.2's `AerSimulator` at 1024 shots.
- **Source data:** the app saves each finished run to a local `ibm_results.json`. This page was written from that file.
