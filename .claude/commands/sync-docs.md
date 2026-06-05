---
description: Verificar y actualizar la documentación afectada antes de subir cambios
---

Vas a verificar que la documentación esté al día con los cambios de código.
Pasos:

1. Obtén el diff contra la rama principal (ver CLAUDE.md para cuál es).
2. Para cada archivo de código modificado, aplica la **matriz de impacto**
   del CLAUDE.md: identifica qué documento debería revisarse.
3. Para cada documento afectado, compáralo con el código real y propónme
   las actualizaciones concretas (no las apliques sin mostrarlas).
4. Aplica las que yo apruebe.
5. **IMPORTANTE — tras mi aprobación, ejecuta vía Bash tool:**

   ```
   mkdir -p .claude && touch .claude/.docs-checked
   ```

   Esto registra que la documentación fue verificada y desbloquea el push.
   Sin este paso, el hook de verificación seguirá bloqueando `git push`.
