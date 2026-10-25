#!/bin/bash
cd -- "$(dirname -- "$0")" || exit 1
python3 launch.py
status=$?
if [ "$status" -ne 0 ]; then
  echo "Could not start. Check the error message and README.md."
  read -r -p "Press Enter to close..." _gaitspm_pause
fi
exit "$status"
