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
- **Invariantes:** `nombre` único en los cuatro. Seed en la migración 0019
  (portable SQLite/Postgres) y en el comando `poblar_catalogos`.
  `Instrumento`/`Genero` nacieron `managed=False`: en una BD nueva sus tablas
  las crea la migración 0019, no un `CreateModel`.

### `ContactoMusico`
- **Para qué:** el contacto mediado de visitantes → músicos; el instrumento de
  validación del proyecto (ROADMAP §5).
- **Invariantes:** FK a `PerfilMusico` (related `contactos`); `remitente_usuario`
  **nullable** — la bisagra para cuentas de contratista en v2. Embudo `estado`:
  ENVIADO→VISTO ocurre automático al abrir "Mis contactos" (sella `visto_en`);
  RESPONDIDO/CONVERTIDO los marca el músico a mano — **nunca automatizar
  `convertido`**. `ip_remitente` alimenta el límite anti-spam (5/hora por IP).
  El email del músico jamás se renderiza en el HTML público; el aviso por email
  respeta `recibir_notificaciones_email` y lleva Reply-To del visitante.

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
