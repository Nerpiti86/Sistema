# CONTRATO BASH NERISOFT / SISTEMA — v3

## Contexto fijo

Repositorio remoto:

```text
https://github.com/Nerpiti86/Sistema
```

Repositorio local Windows:

```text
D:\NeriSoft\Sistema
```

Comando inicial obligatorio en Git Bash:

```bash
cd /d/NeriSoft/Sistema || exit 1
```

Rama única de trabajo:

```text
main
```

No se crean branches.

---

## Regla principal de trabajo

Todo cambio se trabaja así:

```text
validar repo
→ modificar
→ validar estático
→ testear
→ commit
→ push
→ revisar remoto
→ seguir
```

La fuente de verdad después de cada paso es:

```text
origin/main
```

---

## Reglas Git obligatorias

Antes de tocar código:

```bash
git branch --show-current
git fetch origin main
git rev-list --left-right --count origin/main...HEAD
git status --short
```

Condiciones para una subtarea normal:

```text
rama actual = main
behind = 0
ahead = 0
working tree limpio
```

Si `behind != 0`, frenar.

Si `ahead != 0`, frenar, salvo que el script sea específicamente para pushear commits pendientes.

Si hay dirty local inesperado, frenar.

Excepción válida:

```text
Si el usuario pide explícitamente commitear arreglos locales existentes,
el script puede permitir dirty local y commitearlo.
```

---

## Reglas de Bash

* Usar Bash.
* No usar colores ANSI.
* No usar clip.exe.
* No usar /tmp.
* Usar carpeta logs/.
* Agregar logs/ a .git/info/exclude si no existe.
* Dejar terminal abierta al final.
* Preservar exit code con función finalizar().
* No usar `read` como única pausa.
* No crear branches.

---

## Logs

Siempre:

```bash
mkdir -p logs
if ! grep -qx "logs/" .git/info/exclude 2>/dev/null; then
  echo "logs/" >> .git/info/exclude
fi

stamp="$(date +%Y%m%d_%H%M%S)"
log="logs/<nombre_descriptivo>_${stamp}.txt"
```

Backups de archivos existentes:

```bash
cp ruta/archivo "logs/archivo_${stamp}.bak"
```

Los backups quedan en logs/ y no se commitean.

---

## Tests

Los tests son obligatorios cuando corresponda, pero no bloquean commit/push.

Si pasan:

```text
commit normal
```

Si fallan:

```text
commit WIP
```

Formato:

```bash
set +e
python -m pytest -q <tests-dirigidos> | tee -a "$log"
tests_codigo="${PIPESTATUS[0]}"
set -e

set +e
python -m pytest -q | tee -a "$log"
suite_codigo="${PIPESTATUS[0]}"
set -e
```

---

## Commit

Si tests dirigidos y suite pasan:

```bash
git commit -m "<mensaje>"
```

Si alguno falla:

```bash
git commit -m "WIP <mensaje>"
```

Después:

```bash
git push origin main
git fetch origin main
git rev-list --left-right --count origin/main...HEAD
git status --short
```

Debe quedar:

```text
0 0
working tree limpio
```

---

## Reglas de arquitectura

Repository:

```text
puede usar SQL
puede usar get_db
```

Service:

```text
sin SQL
sin get_db
```

Routes:

```text
sin SQL
sin get_db
```

Templates:

```text
sin lógica de negocio
```

Dinero:

```text
INTEGER
no REAL
no float
```

Formato visible:

```text
fechas: DD/MM/YYYY
importes: 9.999,99
```

Templates no deben mostrar centavos crudos.

---

# PLANTILLA BASE FUNCIONAL PARA SUBTAREA NORMAL

```bash
cd /d/NeriSoft/Sistema || exit 1
set -e
set -o pipefail

OBJETIVO_PRINCIPAL="<OBJETIVO PRINCIPAL>"
SUBTAREA="<SUBTAREA PUNTUAL>"
LOG_BASE="<nombre_descriptivo>"
MENSAJE_COMMIT="<mensaje de commit>"

ARCHIVOS_STAGE=(
  "ruta/archivo_1.py"
  "ruta/archivo_2.html"
)

TESTS_DIRIGIDOS=(
  "tests/test_algo.py"
)

finalizar() {
  codigo="$?"
  set +e
  echo
  echo "Codigo de salida: $codigo"
  echo "Script terminado."
  echo
  echo "Queda una terminal Bash abierta. Podes revisar el resultado."
  if [ -r /dev/tty ]; then
    exec bash -i < /dev/tty > /dev/tty 2>&1
  fi
  exec bash -i
}

trap finalizar EXIT

echo "============================================================"
echo "OBJETIVO PRINCIPAL"
echo "============================================================"
echo "$OBJETIVO_PRINCIPAL"
echo
echo "Regla: no cambiar de objetivo hasta cerrar este circuito."
echo

echo "============================================================"
echo "SUBTAREA"
echo "============================================================"
echo "$SUBTAREA"
echo

echo "1) VALIDACION GIT"
echo "------------------------------------------------------------"
rama="$(git branch --show-current)"
echo "Rama actual: $rama"

if [ "$rama" != "main" ]; then
  echo "ERROR: no estas en main."
  exit 1
fi

git fetch origin main

echo
echo "Ahead/behind origin/main...HEAD:"
ab="$(git rev-list --left-right --count origin/main...HEAD)"
echo "$ab"

behind="$(echo "$ab" | awk '{print $1}')"
ahead="$(echo "$ab" | awk '{print $2}')"

if [ "$behind" != "0" ]; then
  echo "ERROR: local esta behind. No sigo."
  exit 1
fi

if [ "$ahead" != "0" ]; then
  echo "ERROR: local tiene commits no pusheados. No sigo."
  exit 1
fi

echo
echo "2) ESTADO INICIAL"
echo "------------------------------------------------------------"
git status --short

if [ -n "$(git status --porcelain)" ]; then
  echo "ERROR: hay dirty local inesperado. No sigo."
  exit 1
fi

mkdir -p logs
if ! grep -qx "logs/" .git/info/exclude 2>/dev/null; then
  echo "logs/" >> .git/info/exclude
fi

stamp="$(date +%Y%m%d_%H%M%S)"
log="logs/${LOG_BASE}_${stamp}.txt"

echo
echo "3) BACKUP"
echo "------------------------------------------------------------"
for archivo in "${ARCHIVOS_STAGE[@]}"; do
  if [ -f "$archivo" ]; then
    nombre="$(basename "$archivo")"
    cp "$archivo" "logs/${nombre}_${stamp}.bak"
    echo "Backup: logs/${nombre}_${stamp}.bak"
  fi
done

echo
echo "4) CAMBIO"
echo "------------------------------------------------------------"
# APLICAR CAMBIO ACA.
# Recomendado: usar python - <<'PY' para reemplazos controlados.
# No dejar este bloque vacio en scripts reales.

echo
echo "5) VALIDACION ESTATICA"
echo "------------------------------------------------------------"
python - <<'PY' | tee -a "$log"
from pathlib import Path

# Validaciones especificas de la subtarea.
# Ejemplo:
# texto = Path("ruta/archivo.py").read_text(encoding="utf-8")
# assert "algo_esperado" in texto

print("Validacion estatica OK")
PY

echo
echo "6) COMPILE"
echo "------------------------------------------------------------"
set +e
python -m compileall "${ARCHIVOS_STAGE[@]}" | tee -a "$log"
compile_codigo="${PIPESTATUS[0]}"
set -e

echo "Compile codigo: $compile_codigo" | tee -a "$log"

echo
echo "7) TESTS DIRIGIDOS NO BLOQUEANTES"
echo "------------------------------------------------------------"
if [ "${#TESTS_DIRIGIDOS[@]}" -gt 0 ]; then
  set +e
  python -m pytest -q "${TESTS_DIRIGIDOS[@]}" | tee -a "$log"
  tests_codigo="${PIPESTATUS[0]}"
  set -e
else
  tests_codigo="0"
  echo "Sin tests dirigidos definidos." | tee -a "$log"
fi

echo
echo "8) SUITE COMPLETA NO BLOQUEANTE"
echo "------------------------------------------------------------"
set +e
python -m pytest -q | tee -a "$log"
suite_codigo="${PIPESTATUS[0]}"
set -e

echo "Tests dirigidos codigo: $tests_codigo" | tee -a "$log"
echo "Suite completa codigo: $suite_codigo" | tee -a "$log"

echo
echo "9) STAGE EXPLICITO"
echo "------------------------------------------------------------"
git add "${ARCHIVOS_STAGE[@]}"

echo
echo "10) DIFF STAGED"
echo "------------------------------------------------------------"
git diff --cached --stat | tee -a "$log"
git diff --cached -- "${ARCHIVOS_STAGE[@]}" | tee -a "$log"

echo
echo "11) COMMIT"
echo "------------------------------------------------------------"
if git diff --cached --quiet; then
  echo "No hay cambios staged para commitear." | tee -a "$log"
else
  if [ "$compile_codigo" = "0" ] && [ "$tests_codigo" = "0" ] && [ "$suite_codigo" = "0" ]; then
    git commit -m "$MENSAJE_COMMIT" | tee -a "$log"
  else
    git commit -m "WIP $MENSAJE_COMMIT" | tee -a "$log"
  fi
fi

echo
echo "12) PUSH"
echo "------------------------------------------------------------"
git push origin main | tee -a "$log"

echo
echo "13) ESTADO FINAL"
echo "------------------------------------------------------------"
git status --short | tee -a "$log"

echo
echo "14) AHEAD/BEHIND FINAL"
echo "------------------------------------------------------------"
git fetch origin main
final_ab="$(git rev-list --left-right --count origin/main...HEAD)"
echo "$final_ab" | tee -a "$log"

echo
echo "15) ULTIMOS COMMITS"
echo "------------------------------------------------------------"
git log -8 --oneline | tee -a "$log"

echo
echo "16) VALIDACION FINAL"
echo "------------------------------------------------------------"
final_status="$(git status --porcelain)"

if [ "$final_ab" != "0	0" ] && [ "$final_ab" != "0 0" ]; then
  echo "ERROR: remoto/local no quedaron alineados." | tee -a "$log"
  exit 1
fi

if [ -n "$final_status" ]; then
  echo "ERROR: working tree no quedo limpio." | tee -a "$log"
  git status --short | tee -a "$log"
  exit 1
fi

echo "OK: subtarea cerrada contra origin/main." | tee -a "$log"
echo "Log: $log"

exit 0
```

---

# PLANTILLA ESPECIAL PARA COMMITEAR DIRTY LOCAL EXPLICITO

Usar solo cuando el usuario dice algo como:

```text
hice arreglos yo, commiteemos y pusheemos
```

```bash
cd /d/NeriSoft/Sistema || exit 1
set -e
set -o pipefail

OBJETIVO_PRINCIPAL="Comitear y pushear arreglos locales existentes"
SUBTAREA="Subir dirty local autorizado por el usuario"
LOG_BASE="commit_arreglos_locales"
MENSAJE_COMMIT="Ajustar UI de filtros en libros contables"

TESTS_DIRIGIDOS=(
  "tests/test_libros_contables_pantalla.py"
  "tests/test_libros_contables_mayor_cuenta_pantalla.py"
)

finalizar() {
  codigo="$?"
  set +e
  echo
  echo "Codigo de salida: $codigo"
  echo "Script terminado."
  echo
  echo "Queda una terminal Bash abierta. Podes revisar el resultado."
  if [ -r /dev/tty ]; then
    exec bash -i < /dev/tty > /dev/tty 2>&1
  fi
  exec bash -i
}

trap finalizar EXIT

echo "============================================================"
echo "OBJETIVO PRINCIPAL"
echo "============================================================"
echo "$OBJETIVO_PRINCIPAL"
echo

echo "============================================================"
echo "SUBTAREA"
echo "============================================================"
echo "$SUBTAREA"
echo

echo "1) VALIDACION GIT"
echo "------------------------------------------------------------"
rama="$(git branch --show-current)"
echo "Rama actual: $rama"

if [ "$rama" != "main" ]; then
  echo "ERROR: no estas en main."
  exit 1
fi

mkdir -p logs
if ! grep -qx "logs/" .git/info/exclude 2>/dev/null; then
  echo "logs/" >> .git/info/exclude
fi

stamp="$(date +%Y%m%d_%H%M%S)"
log="logs/${LOG_BASE}_${stamp}.txt"

git fetch origin main

echo
echo "Ahead/behind origin/main...HEAD:"
ab="$(git rev-list --left-right --count origin/main...HEAD)"
echo "$ab" | tee -a "$log"

behind="$(echo "$ab" | awk '{print $1}')"
ahead="$(echo "$ab" | awk '{print $2}')"

if [ "$behind" != "0" ]; then
  echo "ERROR: local esta behind. No sigo para no pisar remoto." | tee -a "$log"
  exit 1
fi

echo
echo "2) ESTADO LOCAL"
echo "------------------------------------------------------------"
git status --short | tee -a "$log"

if [ -z "$(git status --porcelain)" ] && [ "$ahead" = "0" ]; then
  echo "No hay cambios locales ni commits pendientes para pushear." | tee -a "$log"
  exit 0
fi

echo
echo "3) STAGE DE DIRTY LOCAL AUTORIZADO"
echo "------------------------------------------------------------"
git add -A

echo
echo "4) DIFF STAGED"
echo "------------------------------------------------------------"
git diff --cached --stat | tee -a "$log"
git diff --cached | tee -a "$log"

echo
echo "5) TESTS NO BLOQUEANTES"
echo "------------------------------------------------------------"
if [ "${#TESTS_DIRIGIDOS[@]}" -gt 0 ]; then
  set +e
  python -m pytest -q "${TESTS_DIRIGIDOS[@]}" | tee -a "$log"
  tests_codigo="${PIPESTATUS[0]}"
  set -e
else
  tests_codigo="0"
  echo "Sin tests dirigidos definidos." | tee -a "$log"
fi

echo "Tests codigo: $tests_codigo" | tee -a "$log"

echo
echo "6) COMMIT"
echo "------------------------------------------------------------"
if git diff --cached --quiet; then
  echo "No hay cambios staged para commitear." | tee -a "$log"
else
  if [ "$tests_codigo" = "0" ]; then
    git commit -m "$MENSAJE_COMMIT" | tee -a "$log"
  else
    git commit -m "WIP $MENSAJE_COMMIT" | tee -a "$log"
  fi
fi

echo
echo "7) PUSH"
echo "------------------------------------------------------------"
git push origin main | tee -a "$log"

echo
echo "8) ESTADO FINAL"
echo "------------------------------------------------------------"
git status --short | tee -a "$log"

echo
echo "9) AHEAD/BEHIND FINAL"
echo "------------------------------------------------------------"
git fetch origin main
final_ab="$(git rev-list --left-right --count origin/main...HEAD)"
echo "$final_ab" | tee -a "$log"

echo
echo "10) ULTIMOS COMMITS"
echo "------------------------------------------------------------"
git log -8 --oneline | tee -a "$log"

echo
echo "11) VALIDACION FINAL"
echo "------------------------------------------------------------"
final_status="$(git status --porcelain)"

if [ "$final_ab" != "0	0" ] && [ "$final_ab" != "0 0" ]; then
  echo "ERROR: remoto/local no quedaron alineados." | tee -a "$log"
  exit 1
fi

if [ -n "$final_status" ]; then
  echo "ERROR: working tree no quedo limpio." | tee -a "$log"
  git status --short | tee -a "$log"
  exit 1
fi

echo "OK: arreglos locales commiteados y pusheados contra origin/main." | tee -a "$log"
echo "Log: $log"

exit 0
```
