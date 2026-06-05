#!/usr/bin/env bash
# Hook PreToolUse de referencia — v0.6
# Bloquea git push SOLO si: (a) hay cambios doc-sensibles sin verificar.
# Resuelve: typo-en-README no bloquea; tag/delete pushes no bloquean;
# portable Mac/Linux; mensaje con escape manual.
set -eo pipefail

input="$(cat)"

# Parse del comando desde JSON stdin (jq preferido, sed como fallback)
if command -v jq >/dev/null 2>&1; then
  command=$(printf '%s' "$input" | jq -r '.tool_input.command // empty' 2>/dev/null)
else
  command=$(printf '%s' "$input" | grep -oE '"command"[[:space:]]*:[[:space:]]*"[^"]*"' | sed -E 's/.*"command"[[:space:]]*:[[:space:]]*"//; s/"$//' | head -1)
fi

# Solo interceptar git push
case "$command" in
  *"git push"*) ;;
  *) exit 0 ;;
esac

# BLOQUEANTE 3 (ronda previa): permitir pushes que no llevan código
# (tags, borrado de rama)
case "$command" in
  *"--tags"*|*"--delete"*|*" :"*) exit 0 ;;
esac

marker=".claude/.docs-checked"
last_commit_time=$(git log -1 --format=%ct 2>/dev/null || echo 0)
[ "$last_commit_time" = "0" ] && exit 0

# BLOQUEANTE 1: determinar archivos no pusheados y solo seguir si tocan docs
upstream=$(git rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>/dev/null || echo "")
if [ -n "$upstream" ]; then
  changed=$(git diff --name-only "$upstream"...HEAD 2>/dev/null || true)
else
  changed=$(git diff-tree --no-commit-id --name-only -r --root HEAD 2>/dev/null || true)
fi

# Patrones doc-sensibles — personalizado para Meet & Gig (Django):
# modelo de datos (models/migrations) y lógica de negocio (services).
doc_sensitive_regex='(models|migrations|services)'

if [ -z "$changed" ] || ! printf '%s' "$changed" | grep -qiE "$doc_sensitive_regex"; then
  exit 0   # nada doc-sensible -> permitir sin exigir marker
fi

# mtime portable Mac/Linux (BLOQUEANTE ronda previa)
get_mtime() {
  case "$(uname)" in
    Darwin) stat -f %m "$1" 2>/dev/null ;;
    *) stat -c %Y "$1" 2>/dev/null ;;
  esac
}

if [ ! -f "$marker" ]; then
  printf 'BLOQUEADO: cambios doc-sensibles sin verificar. Ejecuta /sync-docs.\n' >&2
  printf 'Escape manual: mkdir -p .claude && touch .claude/.docs-checked\n' >&2
  exit 2
fi

marker_time=$(get_mtime "$marker"); marker_time=${marker_time:-0}
if [ "$marker_time" -lt "$last_commit_time" ]; then
  printf 'BLOQUEADO: commits doc-sensibles posteriores a la verificacion. Ejecuta /sync-docs.\n' >&2
  printf 'Escape manual: mkdir -p .claude && touch .claude/.docs-checked\n' >&2
  exit 2
fi

exit 0
