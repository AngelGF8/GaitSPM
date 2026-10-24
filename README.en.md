# GaitSPM 1.4.2

Local browser application for kinematic gait analysis with spm1d 0.4.53. Guided and Laboratory modes; Spanish and English UI.

Unzip the complete package. Install Python 3.12, then run `python3 launch.py` (Windows: `py -3 launch.py`) or the included Mac/Windows/Linux launcher. First setup installs dependencies into `.venv` and needs internet. Afterwards the native local mode runs offline at http://127.0.0.1:4173. Keep the console open. Ctrl+C stops the server. Use `--port 4175` if needed.

Eight synthetic datasets, each with 30 cases and 30 controls: FAIS, knee OA, hip OA, multiple sclerosis, hip arthroplasty, ACL reconstruction, hypothetical MS fatigue/recovery, and ACL technical retest. Only kinematics in degrees. The final two preserve subject IDs across repeated conditions and default to analysing the 30 cases. There are 480 distinct simulated participants across all examples. These are not clinical records.

Use Load example, or load the included CSV/XLSX files and apply the mapping. Excel automatically selects Curves_Wide. Review units, IDs, joint mapping and settings before running. Interpretations derive from current results and report actual n, cluster intervals, adjusted p-values and descriptive differences. A nonsignificant result does not demonstrate equivalence. Simulation anchors do not reconstruct published trajectories or clinical effects.

See LEEME_PRIMERO.md, docs/GUIA_EJEMPLOS.md and audit-v1.4/INFORME.md. Numerical, parser, HTTP and offline DOM checks were run; rendered browser/mobile validation was blocked by the environment and remains pending. Optional Streamlit/Pyodide paths and fresh Mac/Windows installations were not tested in this release.

Author: Ángel González de la Flor. GPL v3; third-party notices included. See audit-v1.4.1/INFORME.md for the pre-publication audit.

Version 1.4.2 makes source text I/O explicitly UTF-8. CI now covers Linux, Windows and macOS, including a fresh launcher-created virtual environment and HTTP startup. This does not test browser rendering or desktop double-click behavior. Check the actual run status in GitHub Actions.
