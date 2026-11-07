"""Load Qiskit on a thread that stays alive for the life of the server.

Streamlit runs each rerun of app.py on a new, short-lived thread. If Qiskit is
first imported on such a thread, the next thread that uses it segfaults inside
Qiskit's native allocator. Importing this module before qiskit avoids that.
"""

import importlib
from concurrent.futures import ThreadPoolExecutor

_loader = ThreadPoolExecutor(max_workers=1)
_loader.submit(importlib.import_module, "qiskit_aer").result()
