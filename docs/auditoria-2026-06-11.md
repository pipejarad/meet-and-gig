# Plan de remediación — Auditoría del 11-06-2026

Lee primero `CLAUDE.md` (SCOPE v1 y reglas de trabajo) y `ROADMAP.md`. Este documento
resume una auditoría externa profunda (seguridad, legal, SEO, producto) hecha sobre el
commit `7adf337`. Tu trabajo es ejecutar la remediación por bloques, en el orden indicado.

## Reglas para esta sesión

1. **Verifica antes de tocar.** El código puede haber cambiado desde la auditoría.
   Antes de corregir cada hallazgo, confirma que sigue presente en el código actual.
   Si ya está corregido, márcalo y sigue.
2. **Respeta el SCOPE v1.** No toques los módulos DIFERIDOS (empleadores, ofertas,
   postulaciones, invitaciones, referencias, notificaciones) salvo que un fix lo exija.
3. **Sin refactors oportunistas.** Cada cambio resuelve un hallazgo concreto. Nada más.
4. **Un commit por hallazgo (o por bloque pequeño)**, con mensaje que referencie el
   número del hallazgo (ej: `fix(auth): A3 — MultipleObjectsReturned en EmailBackend`).
5. **Pregunta antes de decidir** entre alternativas con trade-offs (ej: librería vs
   implementación propia). No asumas.
6. Al terminar cada bloque, corre `python manage.py check` y los tests que existan.

---

## BLOQUE A — Seguridad (crítico, primero)

### A1. Django 4.2.20 → Django 5.2 LTS
Django 4.2 LTS llegó a fin de vida (EOL) el 07-04-2026: ya no recibe parches de
seguridad. Migrar a la última 5.2.x en `requirements.txt`.
- Pre-chequeo: confirmar que el Postgres de Railway es ≥14 (Django 5.2 lo exige).
  En local seguimos con SQLite, sin problema.
- Cambio conocido que nos afecta: desde Django 5.0, `forms.URLField` asume `https://`
  por defecto (campos de redes sociales en `usuarios/forms.py`). Verificar comportamiento.
- Revisar release notes 5.0/5.1/5.2 por deprecaciones que usemos; correr la suite y
  `manage.py check --deploy` después.

### A2. Dependencias vulnerables / sucias (`requirements.txt`)
- `Pillow==11.2.1` → `>=11.3` (CVE-2025-48379, heap overflow).
- `sqlparse==0.4.1` → `>=0.5` (DoS conocidos en 0.4.x).
- Eliminar `pytz==2021.1` (Django ≥4 usa `zoneinfo`; verificar que nada lo importe).
- Mover `autopep8` y `pycodestyle` a `requirements-dev.txt` (son herramientas de dev).
- Agregar al final del bloque: correr `pip-audit` y reportar resultado. Recordarle al
  usuario activar Dependabot en GitHub (no es algo que puedas hacer tú desde el repo:
  basta un `.github/dependabot.yml` con ecosistema `pip`, semanal — créalo).

### A3. Bug de bloqueo de cuentas en `usuarios/backends.py` (EmailBackend)
`User.objects.get(Q(email__iexact=u) | Q(username__iexact=u))` lanza
`MultipleObjectsReturned` (→ 500) si el username de un usuario coincide con el email
de otro. El validador por defecto de Django **permite `@` en usernames**, así que un
atacante puede registrarse con username = email de la víctima y bloquearle el login.
Fix en dos capas:
- Backend: buscar primero por `email__iexact`; solo si no existe, por
  `username__iexact`. Mantener la mitigación de timing attack existente.
- `RegistroForm.clean_username` (usuarios/forms.py): rechazar usernames que contengan
  `@` y/o que coincidan (iexact) con un email ya registrado.
- Test de regresión: dos usuarios donde username de uno == email del otro → login de
  la víctima funciona.

### A4. Sin protección de fuerza bruta en login ni en recuperación de contraseña
- Login (`login_view`): proponer `django-axes` (bloqueo por intentos fallidos) o un
  rate limit propio con el mismo patrón del contacto mediado. **Preguntar al usuario
  cuál prefiere antes de implementar** (axes agrega dependencia y tabla; el patrón
  propio es más simple pero más manual).
- `recuperar_password_view` (usuarios/views.py:~130): límite por IP y por email
  destino (ej: 3/hora) para impedir email bombing, reutilizando el patrón de
  `LIMITE_CONTACTOS_POR_IP_HORA`. La respuesta al usuario debe seguir siendo idéntica
  exista o no la cuenta (no romper la protección anti-enumeración existente).

### A5. Rate limit del contacto burlable vía X-Forwarded-For
`_ip_del_request` (usuarios/views.py:~2274) toma el **primer** elemento de XFF, que es
controlado por el cliente: basta enviar un header falso para resetear el límite 5/hora.
En Railway, el valor confiable es el **último** elemento (lo anota su proxy). Cambiar a
`xff.split(',')[-1].strip()` con fallback a `REMOTE_ADDR`, y dejar un comentario de por
qué (es contraintuitivo y alguien lo va a "corregir" de vuelta).

---

## BLOQUE B — Cumplimiento legal (Ley 21.719, vigente 01-12-2026)

La plataforma trata datos personales de usuarios Y de terceros sin cuenta
(`ContactoMusico`: nombre, email, teléfono, IP del visitante). Hoy no existe política
de privacidad, términos de servicio, consentimiento en el registro, ni forma de
eliminar una cuenta.

### B1. Páginas legales
- Crear vistas/templates estáticos: `/terminos/` y `/privacidad/`, linkeados desde el
  footer de `base.html` y desde el registro.
- Redactar **borradores** marcados como "PENDIENTE DE REVISIÓN LEGAL" (el usuario los
  pasará por abogado). Contenido mínimo de los términos: Meet & Gig es intermediario
  tecnológico, NO es empleador ni parte de los acuerdos músico-contratante; licencia
  de uso del contenido que sube el músico; causales de baja. Contenido mínimo de
  privacidad: qué datos se recogen (incluidos los del formulario de contacto y la IP),
  finalidad, plazo de retención, derechos ARCO + portabilidad, contacto para ejercerlos.

### B2. Consentimiento en el registro
Checkbox obligatorio en `RegistroForm` + `registro.html`: "He leído y acepto los
Términos y la Política de Privacidad" (con links). Guardar timestamp de aceptación
(campo nuevo en `Usuario`, migración).

### B3. Eliminación de cuenta
Vista `eliminar_cuenta` (POST con confirmación): `is_active=False` + anonimización de
datos personales (email → hash o placeholder único, nombre, teléfono, foto) y
despublicar portafolio (`activo=False`). Soft-delete es aceptable como v1, pero el
dato personal debe quedar irreconocible.

### B4. Retención de `ContactoMusico`
Management command (mismo patrón que `marcar_invitaciones_expiradas`) que anonimice
`ip_remitente` a los 30 días del envío. Documentar el plazo en la política de
privacidad. Dejar listo para cron de Railway.

---

## BLOQUE C — SEO y vitrina (el canal de adquisición de la v1)

### C1. JSON-LD corrupto en `portafolio_publico.html` (~líneas 41-53)
Las URLs de `sameAs` se interpolan con autoescape HTML: cualquier URL con `&` produce
`&amp;` → JSON inválido → Google descarta el structured data. Construir el dict
completo del JSON-LD en `PortafolioUnificadoView.get_context_data` y renderizarlo con
el filtro `json_script` (o `mark_safe(json.dumps(...))` con todo escapado río arriba).
Eliminar la construcción manual a mano en el template.

### C2. Embed de video frágil (mismo template, ~líneas 581-585)
`slice:'17:'` / `slice:'32:'` solo funciona con dos formatos exactos de URL; se rompe
con `youtube.com` sin www, `m.youtube.com`, shorts y links con `?si=`. Extraer el ID
con regex en el `clean()` de `PortafolioForm` (o un template tag `youtube_id`), validar
dominio real (youtube.com / youtu.be), y embeber `https://www.youtube.com/embed/<id>`.
Si no se puede extraer ID, mostrar link plano como hoy.

### C3. Contenido duplicado: `/perfil/<username>/` vs `/portafolio/<slug>/`
Dos páginas públicas para el mismo músico dividen el SEO. El canónico es el
portafolio. Convertir `ver_perfil_musico` en redirect 301 al portafolio del usuario
(si tiene portafolio activo; si no, 404 como hoy). Revisar y actualizar los links
internos que apunten a `ver_perfil_musico`.

### C4. `sitemap.xml` + `robots.txt`
`django.contrib.sitemaps` con: home, directorio de músicos y todos los portafolios
activos (`lastmod` = `fecha_actualizacion`). `robots.txt` que permita todo salvo
`/admin/`, `/mis-contactos/` y rutas privadas, y apunte al sitemap.

### C5. Social proof inversa en el home
En `inicio.html`/`views.inicio`: ocultar el bloque de estadísticas si
`total_musicos < 50` (umbral como constante). Con números bajos comunica lo contrario
de lo que se busca.

---

## BLOQUE D — Tests e higiene

### D1. Suite de tests muerta
Hay **cero** funciones de test y el andamiaje está roto: `conftest.py` y `pytest.ini`
apuntan a `meetandgig.settings` (ya no existe como módulo; ahora es paquete) y los
fixtures usan campos que los modelos ya no tienen (`PerfilMusico.nombre`,
`tarifa_hora`, etc.). Acción:
- Borrar el andamiaje muerto (conftest gigante, fixtures obsoletos,
  `usuarios/tests/REORGANIZACION_FINAL.md`).
- Escribir una **suite de humo (~15 tests)** del embudo activo v1:
  registro (fuerza tipo musico, crea PerfilMusico, atómico) → login (email y username,
  + regresión A3) → portafolio público (visible si activo, 404 si no, dueño sí lo ve) →
  contacto mediado (crea registro, honeypot descarta, rate limit corta, email con
  Reply-To del visitante) → embudo (enviado→visto al abrir panel, marcar
  respondido/convertido solo por el dueño).
- `pytest.ini` apuntando a `meetandgig.settings.development`.

### D2. Higiene
- Eliminar `mis_postulaciones_debug.html` y revisar `scripts/debug/` (mover a
  `.gitignore` o borrar).
- Catálogos inconsistentes (ya documentado en ROADMAP §9): unificar en la migración de
  datos como única fuente de verdad y alinear/retirar `poblar_catalogos`. Subió de
  prioridad: debe estar resuelto antes de la validación con músicos reales.

---

## Fuera del alcance de Claude Code (recordatorios para el usuario)

- Activar backups automáticos del Postgres en Railway.
- Credenciales Backblaze B2 + `ANTHROPIC_API_KEY` + Resend en variables de Railway.
- Comprar dominio y configurar SPF/DKIM/DMARC antes de invitar músicos (sin esto, los
  emails de contacto caen a spam y el embudo muere en silencio).
- Revisión por abogado de los borradores legales del Bloque B.
- (Opcional) Sentry capa gratis para errores 500 en producción.

## Secuencia

A (completo) → B → C → D. Dentro de cada bloque, en el orden listado. Si un hallazgo
ya no aplica, anótalo y continúa. Al final de cada bloque, entrega un resumen corto de
qué se hizo, qué quedó pendiente y qué decisiones requieren al usuario.
