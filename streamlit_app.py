"""Optional cloud entrypoint. Hosted uploads are processed on the host server."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent / 'app'))
import gaitspm_app

gaitspm_app.main()
