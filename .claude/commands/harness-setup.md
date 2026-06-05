---
description: Personalizar el harness recién instalado a este proyecto (rellena placeholders, matriz de impacto, hook)
---

El usuario acaba de instalar el claude-harness-kit en este proyecto con su
`install.sh`. La estructura ya existe (`CLAUDE.md`, `docs/`, slash commands,
el hook `scripts/check-docs-before-push.sh`) pero con **placeholders
genéricos sin rellenar**. Tu trabajo ahora es **personalizar esa estructura
a este proyecto real** — no construir nada desde cero, el esqueleto ya está.

No apliques cambios a ciegas. Adapta a lo que veas. Si algo del kit no encaja
con este proyecto, dilo y propón una alternativa. Habla en lenguaje natural,
sin tecnicismos; si usas términos como "hook" o "regex", explícalos.

## Fase 1 — Verificar e investigar (no modifiques nada todavía)

1. Confirma qué dejó el kit: `CLAUDE.md`, `TASKS.md`, `BUGS.md`,
   `CHANGELOG.md`, `docs/`, `.claude/commands/`, `scripts/check-docs-before-push.sh`.
2. Entiende el proyecto: estructura de carpetas, lenguaje y frameworks, README
   si existe, historia de Git (últimos commits, ¿rama `develop` además de
   `main`?).
3. Si el proyecto ya tenía código y docs antes del kit, trátalos como fuente
   de verdad a verificar: lo que escribas debe reflejar el **estado actual del
   código**. Si una doc vieja contradice el código, **gana el código** y
   señálalo.
4. Da un resumen breve de lo que encontraste y espera confirmación del usuario
   antes de seguir.

## Fase 2 — Entrevista mínima (una pregunta a la vez)

Pregunta solo lo que no puedas deducir del código:

- "En una o dos frases, ¿qué hace este proyecto?"
- "¿Es personal, de equipo, o lo usarán terceros?"
- "¿Rama principal `main` o `develop`?"
- "¿Hay reglas que quieras que respete siempre?" (tests, dependencias, estilo
  de commits)
- Si parece un proyecto grande (equipo, producción, tickets con ID, rama
  develop): "¿Usas alguna colección de skills de workflow (como
  agent-skills de Addy Osmani) para planificar features? Si es así, este
  harness se concentra en mantener tu documentación sincronizada; la
  planificación la cubre esa otra herramienta."

## Fase 3 — Personalizar (di qué pondrás antes de cada cambio; muéstralo al terminar)

1. **`CLAUDE.md`** — reemplaza TODOS los `<placeholders>` con datos reales:
   qué es el proyecto, stack, estado, rama, las reglas de la entrevista. En la
   **matriz de impacto**, cambia las rutas de ejemplo por las **rutas reales**
   de este proyecto. Mantén el archivo bajo 250 líneas; si sobra detalle,
   muévelo a `docs/` y enlázalo.

2. **El hook `scripts/check-docs-before-push.sh`** — ajusta la variable
   `doc_sensitive_regex` para que matchee los nombres reales de los archivos
   sensibles a documentación de este proyecto (es case-insensitive). Explica
   en lenguaje natural qué hace el hook antes de tocarlo.

3. **`docs/`** — rellena los archivos que apliquen con contenido real. **Borra
   los que no apliquen** en vez de dejarlos vacíos. Agrega otros si hacen falta.

4. **Slash command** — revisa que `/sync-docs` tenga sentido aquí (es el
   único comando que aporta el kit: verifica docs contra código antes de
   subir cambios). Si el usuario no usa Claude Code, dile cómo correr esa
   verificación a mano. La planificación de features (specs, planes) la
   cubren herramientas de workflow externas como agent-skills, no este kit.

## Fase 4 — Verificación final

1. Si rellenaste docs desde el código, compáralas una segunda vez contra el
   código real y reporta discrepancias.
2. Confirma que `CLAUDE.md` quedó bajo 250 líneas.
3. Confirma que la matriz de impacto y el regex del hook usan rutas/nombres
   reales, no los de ejemplo.
4. Si tocaste `.gitignore` para versionar `.claude/`, explica el cambio.

## Fase 5 — Explicar cómo usar esto

Resumen de 15-25 líneas: qué archivos quedaron y para qué, qué debe hacer el
usuario en el día a día, qué haces tú automáticamente, qué pasa si un hook
bloquea un push y cómo desbloquear, y cómo cambiar las reglas más adelante.
Cuéntalo como a un colega que no estuvo en la conversación.

Empieza con la Fase 1.
