# Publicación y comprobaciones de GitHub

Repositorio: https://github.com/AngelGF8/GaitSPM

La versión 1.4.1 se publicó en el commit `0aa1b92b61f991d09fac43c49998c1e8accca044`. Los 279 archivos se verificaron contra el ZIP auditado. La ejecución https://github.com/AngelGF8/GaitSPM/actions/runs/40104797708 terminó correctamente: 23 pruebas Python y ocho recorridos DOM, incluida la carga HTTP del CSV externo MovementRx.

La versión 1.4.2 añade UTF-8 explícito y una prueba de arranque del lanzador. El workflow ejecuta una instalación limpia y la batería en Linux, Windows y macOS. El resultado de cada commit debe consultarse en Actions; la existencia del workflow no implica éxito.

Los informes `audit-v1.4/` y `audit-v1.4.1/` conservan el estado histórico de sus revisiones. Las pruebas HTTP y DOM no comprueban renderizado en navegador, selector de archivos ni apertura mediante doble clic. Esa revisión visual sigue pendiente.
