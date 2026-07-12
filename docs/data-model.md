# Modelo de datos

> Mapa de entidades para navegar rápido. La fuente de verdad es el código
> (`usuarios/models.py`); este documento traduce la regla **OCULTAR, NO BORRAR**
> del `CLAUDE.md` a nivel de modelo: qué está vivo en la v1 (vitrina de músicos)
> y qué queda dormido para el mediano/largo plazo.
>
> A propósito NO lista campos — eso es `models.py` y driftearía. Aquí van solo
> el estado de cada modelo y las invariantes de negocio que el código no declara.

## Modelos ACTIVOS (v1 — trabajar aquí)

### `Usuario` (AbstractUser custom)
- **Para qué:** cuenta de acceso; login por email o username (`EmailBackend`).
- **Invariantes:** `USERNAME_FIELD = 'email'`. Email y username únicos
  **case-insensitive a nivel de BD** (constraints de la migración 0025);
  `UsuarioManager` normaliza el email a minúsculas en toda vía de creación.
  En v1 todo registro nuevo queda con `tipo_usuario='musico'` (forzado
  server-side en `RegistroForm.save()`).
  `terminos_aceptados_en` (B2) acredita el consentimiento: lo sella
  `RegistroForm.save()`; nullable porque las cuentas previas no lo tienen.
  La **eliminación de cuenta** (B3) es soft-delete con anonimización:
  `is_active=False`, email/username → `eliminado-<pk>…` (libera el email
  real para re-registro), nombre/teléfono/dirección/foto borrados y
  portafolio despublicado. La supresión llega hasta el **contenido** del
  portafolio: biografía, formación, enlaces a las cuentas del músico y los
  **archivos de multimedia** (que sobreviven a la despublicación) se borran,
  no solo se ocultan. La fila nunca se borra (integridad referencial).

### `PerfilMusico`
- **Para qué:** datos personales/privados del músico (teléfono, privacidad).
- **Invariantes:** OneToOne con `Usuario`; se crea automáticamente en el
  registro. El **teléfono vive aquí, no en `Usuario`** — los templates deben
  leer `usuario.perfil_musico.telefono`.

### `Portafolio` (+ `PortafolioInstrumento`, `PortafolioGenero`, `Multimedia`)
- **Para qué:** la vitrina pública del músico — el corazón de la v1.
- **Invariantes:** OneToOne con `Usuario` (accessor `usuario.portafolio`);
  se auto-crea cuando el músico entra a su sección. `slug` único, generado del
  username al crear y **congelado** (la URL pública depende de él).
  `activo=True` es requisito para toda visibilidad pública: búsqueda, home y
  el perfil público por username (el propietario sigue viendo lo suyo).
  `show_email`/`show_telefono` controlan el contacto visible al público
  (opt-in del músico).

### Catálogos: `Instrumento`, `Genero`, `NivelExperiencia`, `Ubicacion`
- **Para qué:** vocabulario normalizado para perfiles y búsqueda.
- **Invariantes:** `nombre` único en los cuatro. **Única fuente de verdad:
  las migraciones de datos.** La 0019 siembra el catálogo base (portable
  SQLite/Postgres) y la **0030** (auditoría D2) lo eleva al catálogo rico
  chileno y normaliza lo ya sembrado: categoría `Viento`→`Vientos`, género
  `Electronic`→`Electrónica`, sin `Charango` duplicado, sin genéricos que el
  catálogo desglosa. El comando `poblar_catalogos` (que divergía de la
  migración) **se eliminó**. `Instrumento`/`Genero` nacieron `managed=False`:
  en una BD nueva sus tablas las crea un `RunPython` portable en la migración
  **0011** (antes de los modelos que les apuntan con FK — requisito de
  PostgreSQL); la 0019 conserva un guard idéntico e idempotente.

### `ContactoMusico`
- **Para qué:** el contacto mediado de visitantes → músicos; el instrumento de
  validación del proyecto (ROADMAP §5).
- **Invariantes:** FK a `PerfilMusico` (related `contactos`); `remitente_usuario`
  **nullable** — la bisagra para cuentas de contratista en v2. Embudo `estado`:
  ENVIADO→VISTO ocurre automático al abrir "Mis contactos" (sella `visto_en`);
  RESPONDIDO/CONVERTIDO los marca el músico a mano — **nunca automatizar
  `convertido`**. `ip_remitente` alimenta el límite anti-spam (5/hora por IP)
  y se **anonimiza a los 30 días** (command `aplicar_retencion_datos`, B4 —
  plazo documentado en /privacidad/); el contenido del contacto no se toca.
  El email del músico jamás se renderiza en el HTML público; el aviso por email
  respeta `recibir_notificaciones_email` y lleva Reply-To del visitante.

### `GeneracionBioIA`
- **Para qué:** registro de cada uso del asistente de IA de biografías
  (ROADMAP §8) — alimenta el límite de generaciones/día y mide adopción.
- **Invariantes:** FK a `Usuario`; una fila por generación (las 2 variantes de
  una llamada cuentan como una). El límite diario se calcula contando filas
  de hoy en la vista; el borrador elegido viaja por sesión y **nunca** se
  escribe directo en `Portafolio.biografia`.

### `SolicitudRecuperacionPassword`
- **Para qué:** rate limit de la recuperación de contraseña (auditoría A4):
  3/hora por email destino y 5/hora por IP, contando filas en BD (mismo
  patrón que `ContactoMusico`).
- **Invariantes:** se crea una fila por CADA solicitud, exista o no la cuenta
  (registrar solo cuentas reales delataría qué emails existen). Al exceder el
  límite la respuesta no cambia: se degrada en silencio (sin email). Las
  filas pierden utilidad pasada la ventana de 1 hora; el command
  `aplicar_retencion_datos` (B4) las elimina a los 30 días.

### Tablas de terceros: `axes_*` (django-axes, auditoría A4)
- Bloqueo de fuerza bruta del login: 5 intentos fallidos por usuario+IP →
  1 hora de bloqueo. Las gestiona django-axes con sus propias migraciones
  (`AccessAttempt`, `AccessLog`, `AccessFailureLog`); config en
  `settings/base.py` (bloque AXES_*).

## Modelos DIFERIDOS (presentes en el código — no construir sobre ellos, no borrar)

> Diferidos por el pivote a vitrina de un solo lado. Modelos y migraciones
> intactos; rutas comentadas y UI oculta (marcadores `DIFERIDO v1`). Tienen
> **bugs conocidos que se corrigen AL REACTIVAR** — lista en `ROADMAP.md` §9.

| Modelo | Antes servía a… | Vuelve en… |
|---|---|---|
| `PerfilEmpleador` | perfil del lado contratante | mediano plazo |
| `OfertaLaboral` (+ `OfertaInstrumento`, `OfertaGenero`) | ofertas laborales | mediano plazo |
| `Postulacion` | postulación de músico a oferta | mediano plazo |
| `Invitacion` | invitación directa empleador → músico | mediano plazo |
| `Testimonio` | referencias laborales y testimonios | largo plazo |
| `Notificacion` | notificaciones in-app (solo empleadores; dormida) | con las ofertas |
