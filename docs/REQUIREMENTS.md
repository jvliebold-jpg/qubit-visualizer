# Qubit Visualizer: requirements

## 1. PRD: product requirements

**Goal:** help people understand what a qubit is and what quantum gates do by letting them play with one qubit, see it move, and compare a perfect simulation with a real IBM quantum computer.

**Audience:** complete beginners, students who know some linear algebra, and people who want the full math. One switch adapts the whole app to each group.

**Features:**

- **Gates:** buttons for H, X, Y, Z, S and T, plus Rx, Ry and Rz with an angle slider (0° to 360° in 15° steps).
- **Bloch sphere:** an interactive 3D sphere showing the qubit as an arrow.
- **Gate history:** the gates applied so far, with a Reset button.
- **Measurement:** 1024 shots on the Qiskit Aer simulator, shown as a probability bar chart.
- **Real hardware:** sends the circuit to the least busy real IBM quantum computer and shows ideal vs real results side by side. Shows the job status while it waits, and saves each finished run so the last result appears instantly.
- **Knowledge levels:**
  - Beginner: analogies with no math or notation.
  - Intermediate: Dirac notation and the state formula.
  - Advanced: state vector, gate matrices, Bloch angles, shot noise, and hardware error sources.
- **Flashcards:** at the Beginner and Intermediate levels, 6 concept cards and 7 gate cards. Each flips to show its answer, and gate cards have "Try it" buttons.
- **Notebook:** `qubit_visualizer.ipynb` reproduces the simulator runs and plots the saved hardware results.

**Out of scope for now:** more than one qubit, user accounts, and hosting.

## 2. TRD: technical requirements

| Area | Choice |
| --- | --- |
| Language | Python 3.14 (tested on macOS, Intel) |
| UI framework | Streamlit 1.67 |
| Charts | Plotly 7.1 (3D Bloch sphere, bar charts) |
| Quantum | Qiskit 2.6.2 for circuits and statevectors, and Qiskit Aer 0.18.2 for the simulator |
| Real hardware | qiskit-ibm-runtime 0.52.0: `QiskitRuntimeService` on the `ibm_quantum_platform` channel, `least_busy`, and `SamplerV2` |
| Config | python-dotenv reads IBM credentials from `.env` |
| Notebook | Jupyter, matplotlib, and Qiskit's `plot_bloch_multivector` |
| Testing | Streamlit `AppTest` for app logic; headless Chrome (Playwright) for layout and the full browser flow |

**External APIs:** IBM Quantum Platform only, reached through qiskit-ibm-runtime. Without credentials the app works fully offline, and the hardware button is disabled with a setup hint.

**Constraints:**

- **Thread safety:** Qiskit must first be imported on a thread that stays alive. `qiskit_preload.py` does this, because Qiskit's native allocator crashes when Qiskit is loaded on one of Streamlit's short-lived script threads.
- **Intel Mac install:** `cryptography` is pinned to 48.0.1, because newer releases have no prebuilt wheel for Intel Macs.

## 3. App flow

1. **Open the app.** The user sees the knowledge level switch (Beginner by default), a short introduction, and the qubit's arrow pointing up at 0.
2. **Optional: learn first.** Beginners can open "What is a qubit?" or the flashcards. Pressing a card's "Try it" button applies that gate and shows a toast.
3. **Apply gates.** Each press updates the sphere, the state readout and the gate history. If a gate leaves the arrow unchanged, a note explains why.
4. **Measure.** The app runs 1024 shots on the simulator and draws the bar chart. Adding a gate clears the old chart so it never shows a stale result.
5. **Run on real hardware (optional).** The app picks the least busy IBM computer, submits the job, and checks its status every 15 seconds. When the job finishes, it saves the result and shows ideal vs real bars with a note on why they differ.
6. **Change level at any time.** The explanations change, and the gates and results stay.
7. **Reset** to start again from 0.

## 4. UI/UX brief

- **Look:** a clean, single-page layout. Gates sit on the left, the sphere on the right, then history and measurement, then real hardware. Columns stack on phones.
- **Colors:**
  - Blue (`#2a78d6` light, `#3987e5` dark) for the arrow, primary buttons and simulator bars.
  - Orange (`#eb6834` light, `#d95926` dark) for real-hardware bars.
  - Neutral grays for the sphere and grid.
  - Light and dark themes follow the user's system setting.
- **Typography:** Streamlit's default sans-serif with an 18 px base size. Explanations are 0.95 rem with 1.6 line height, so they are larger than Streamlit's default captions.
- **Components:**
  - Gate buttons at least 3 rem tall, with bold 1.05 rem labels.
  - The level switch is a segmented control.
  - Flashcards are bordered cards with Flip and Try buttons.
  - Charts have direct value labels, a legend when there are two series, and hover tooltips.
  - Wide tables scroll inside their own box instead of the page.
- **Checked:** at laptop (1366 px) and phone (390 px) widths, in light and dark mode. Nothing scrolls sideways, and no math is clipped.

## 5. Backend schema

There is no server database and no user accounts.

| Data | Where it lives | Lifetime |
| --- | --- | --- |
| Gate history, last measurement, flipped cards, angle, knowledge level | Streamlit session state, in server memory per browser tab | Until the tab is closed or the server restarts |
| IBM API key (`QISKIT_IBM_TOKEN`) and instance CRN (`QISKIT_IBM_INSTANCE`) | `.env` in the project folder, git-ignored. `.env.example` is the committed blank template | Until the user edits it |
| Pending job and finished hardware runs | `ibm_results.json` in the project folder, git-ignored | Kept across restarts |
| IBM connection and simulator | Streamlit `cache_resource`, in server memory | Until the server restarts |
| Published hardware results | `docs/hardware_results.md`, committed | Permanent |

**`ibm_results.json` structure:**

```json
{
  "pending": null,
  "results": [
    {
      "job_id": "dbpp4b0ou4as73cu1g30",
      "backend": "ibm_fez",
      "gates": [["X", null]],
      "shots": 1024,
      "submitted_at": "2026-11-10T21:52:44+00:00",
      "finished_at": "2026-11-10T21:53:00+00:00",
      "ideal_counts": {"1": 1024},
      "real_counts": {"0": 40, "1": 984}
    }
  ]
}
```

- **`pending`:** holds the same fields as a result, without `finished_at` and `real_counts`, while a job is running.
- **`gates`:** a list of `[name, degrees]` pairs, where `degrees` is `null` for gates without an angle.
- **Writes:** go to a temporary file that is then renamed, so a crash never leaves half a file.

Credentials are read from `.env` on every use and are never written to disk, logged, or shown on screen.

## 6. Implementation plan

**Built so far, in order:**

1. The core app: gates, Bloch sphere, history, reset, and simulator measurement. This included fixing a Qiskit crash under Streamlit's threads.
2. README with screenshot and run instructions, tested on a clean clone.
3. Real IBM hardware: `.env` credentials, least busy backend, SamplerV2, status polling, cancel, saved results, and the ideal vs real chart.
4. Real runs of H and X on `ibm_fez`, published in `docs/hardware_results.md`.
5. Knowledge levels and flashcards. Every gate matrix and physics claim is checked against Qiskit by an automated test.
6. Readability: larger text and buttons, more spacing, and checks at laptop and phone widths.
7. This document and the Jupyter notebook.

**Possible next steps (not built):**

- **Repo tests:** add the automated tests to the repo, with a `pytest` command and CI.
- **Two qubits:** CNOT, entanglement, and a Bell-state demo.
- **Calibration data:** save the backend's T1, T2 and readout error with each hardware run, so Advanced users can compare them with the results.
- **Hosting:** deploy to Streamlit Community Cloud, with the IBM feature reading credentials from Streamlit secrets instead of `.env`.
- **Accessibility:** keyboard shortcuts for the gates, and a text description of the sphere for screen readers.
