"""Run circuits on real IBM quantum hardware and keep a local record of the results.

Credentials come from QISKIT_IBM_TOKEN and QISKIT_IBM_INSTANCE, set either in
the environment or in the project's .env file. They are never written anywhere.
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from dotenv import dotenv_values

PROJECT_DIR = Path(__file__).parent
ENV_FILE = PROJECT_DIR / ".env"
RESULTS_FILE = PROJECT_DIR / "ibm_results.json"

CREDENTIAL_KEYS = ("QISKIT_IBM_TOKEN", "QISKIT_IBM_INSTANCE")
# Values from .env.example that mean the user has not filled the file in yet.
PLACEHOLDERS = {"", "your-api-key-here", "your-instance-crn-here"}

FINAL_STATUSES = {"DONE", "ERROR", "CANCELLED"}


def credentials():
    """Return (token, instance), or None if either is missing.

    Read on every call, so edits to .env apply without restarting the app.
    Real environment variables take precedence over the .env file.
    """
    values = {**dotenv_values(ENV_FILE), **os.environ}
    token, instance = (str(values.get(key) or "").strip() for key in CREDENTIAL_KEYS)
    if token in PLACEHOLDERS or instance in PLACEHOLDERS:
        return None
    return token, instance


def connect(token, instance):
    from qiskit_ibm_runtime import QiskitRuntimeService

    return QiskitRuntimeService(channel="ibm_quantum_platform", token=token, instance=instance)


def submit(service, circuit, shots):
    """Send a measured circuit to the least busy real backend. Returns (job_id, backend name)."""
    from qiskit.transpiler import generate_preset_pass_manager
    from qiskit_ibm_runtime import SamplerV2

    backend = service.least_busy(
        operational=True, simulator=False, min_num_qubits=circuit.num_qubits
    )
    hardware_circuit = generate_preset_pass_manager(
        optimization_level=1, backend=backend
    ).run(circuit)
    job = SamplerV2(mode=backend).run([hardware_circuit], shots=shots)
    return job.job_id(), backend.name


def job_status(service, job_id):
    job = service.job(job_id)
    status = job.status()
    message = job.error_message() if status == "ERROR" else None
    return status, message


def job_counts(service, job_id):
    return service.job(job_id).result()[0].join_data().get_counts()


def cancel(service, job_id):
    service.job(job_id).cancel()


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load_store():
    """Return {"pending": job or None, "results": [finished runs, oldest first]}."""
    try:
        store = json.loads(RESULTS_FILE.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        store = {}
    return {"pending": store.get("pending"), "results": store.get("results", [])}


def save_store(store):
    # Write to a temporary file first, so a crash never leaves half a JSON file.
    temporary = RESULTS_FILE.with_suffix(".tmp")
    temporary.write_text(json.dumps(store, indent=2))
    temporary.replace(RESULTS_FILE)
