#!/bin/bash
cd -- "$(dirname -- "$0")" || exit 1
python3 launch.py
status=$?
if [ "$status" -ne 0 ]; then
  echo "No se pudo iniciar. Revisa el mensaje y LEEME_PRIMERO.md."
  read -r -p "Pulsa Intro para cerrar..." _gaitspm_pause
fi
exit "$status"
