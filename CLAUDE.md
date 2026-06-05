# CLAUDE.md — Meet & Gig

Guía de contexto para sesiones de desarrollo con Claude. Leer antes de cualquier tarea.

---

## 1. Descripción del proyecto

**Meet & Gig** es un marketplace laboral musical chileno que conecta:
- **Músicos** (tipo `musico`): crean portafolio público, postulan a ofertas, reciben invitaciones directas y acumulan referencias laborales.
- **Empleadores** (tipo `empleador`): publican ofertas, buscan músicos, invitan directamente y gestionan postulaciones.

El ciclo central es: empleador publica oferta → músico postula (o recibe invitación directa) → empleador acepta/rechaza → oferta se cierra automáticamente al completar cupos.

---

## 2. Stack técnico

| Componente | Versión / Detalle |
|---|---|
| Python | 3.9.6 |
| Django | 4.2.20 |
| Base de datos | SQLite (solo desarrollo) |
| Imágenes | Pillow 11.2.1 |
| REST Framework | djangorestframework 3.12.4 — **instalado pero sin uso** |
| Email | `console.EmailBackend` en dev — SMTP real en producción |
| Frontend | Templates Django + Bootstrap (CSS) + Font Awesome (iconos) |
| Idioma / TZ | `es-cl` / `America/Santiago` |
| Autenticación | Custom `AbstractUser` + `EmailBackend` (login por email o username) |

---

## 3. Arquitectura

**Una sola app Django**: toda la lógica está en `usuarios/`. No hay apps separadas.

```
meet-and-gig/
├── .env                     # Variables de entorno locales (NO commitear, en .gitignore)
├── .env.example             # Plantilla con todas las variables necesarias (sí commitear)
├── meetandgig/              # Config del proyecto
│   ├── settings/
│   │   ├── base.py          # Configuración común a todos los entornos
│   │   ├── development.py   # DEBUG=True, SQLite, email consola
│   │   └── production.py    # DEBUG=False, PostgreSQL, SMTP, headers de seguridad
│   ├── urls.py              # Incluye usuarios.urls en raíz
│   └── static/              # Archivos estáticos del proyecto
├── usuarios/                # Única app — toda la lógica del negocio
│   ├── models.py            # ~1350 líneas — todos los modelos
│   ├── views.py             # Todas las vistas (funcionales + CBV)
│   ├── forms.py             # Todos los formularios
│   ├── urls.py              # ~40 rutas
│   ├── signals.py           # post_save en Postulacion e Invitacion
│   ├── backends.py          # EmailBackend custom
│   ├── admin.py             # Admin completo con acciones bulk y exportar CSV
│   └── management/commands/
│       ├── poblar_catalogos.py              # Seed de catálogos normalizados
│       └── marcar_invitaciones_expiradas.py # Debe correrse como cron
├── templates/
│   ├── base.html            # Layout base
│   └── emails/              # 4 templates: nueva_postulacion, postulacion_aceptada,
│                            #   postulacion_rechazada, solicitud_referencia
├── tests/                   # ⚠️ Solo __init__.py — sin tests implementados
│   ├── factories/
│   ├── unit/
│   └── integration/
├── scripts/                 # Utilidades de desarrollo y debug
├── media/                   # Uploads de usuarios (runtime, no commitear)
└── CONTEXT.md               # Análisis detallado de arquitectura y deuda técnica
```

Patrón: **MVT estándar de Django**. Vistas funcionales con `@login_required` + CBVs (`CreateView`, `UpdateView`, `DetailView`) con mixins custom (`EmpleadorRequiredMixin`).

---

## 4. Modelos clave

Todos en `usuarios/models.py`. 18 modelos en total.

### Usuarios y perfiles
| Modelo | Descripción |
|---|---|
| `Usuario` | AbstractUser custom; `USERNAME_FIELD = 'email'`; campo `tipo_usuario` ('musico'\|'empleador') |
| `PerfilMusico` | Datos privados/admin del músico (teléfono, fecha nacimiento, config privacidad). OneToOne → Usuario |
| `PerfilEmpleador` | Datos de la organización (nombre, tipo entidad, ubicación, redes). OneToOne → Usuario |

### Catálogos normalizados (seeds vía `poblar_catalogos`)
| Modelo | Descripción |
|---|---|
| `Instrumento` | Catálogo de instrumentos (nombre, categoría) |
| `Genero` | Catálogo de géneros musicales |
| `NivelExperiencia` | Niveles ordenados con rango de años (principiante → experto) |
| `Ubicacion` | Ciudades/regiones de Chile con orden de presentación |

### Portafolio del músico (perfil público)
| Modelo | Descripción |
|---|---|
| `Portafolio` | Perfil público del músico. OneToOne → Usuario. Slug auto-generado desde username |
| `PortafolioInstrumento` | M2M Portafolio×Instrumento con metadata: `es_principal`, `prioridad`, `años_experiencia` |
| `PortafolioGenero` | M2M Portafolio×Genero con `prioridad` |
| `Multimedia` | Imágenes locales + embeds (YouTube/Vimeo/SoundCloud/Spotify) del portafolio |
| `Testimonio` | Referencias laborales con estados (pendiente/aprobado/rechazado/directo) y token de solicitud por email |

### Sistema de empleo (Sprint 3)
| Modelo | Descripción |
|---|---|
| `OfertaLaboral` | Oferta de empleador. FK → PerfilEmpleador. Slug auto-generado. Estados: borrador/publicada/cerrada/cancelada |
| `OfertaInstrumento` | M2M OfertaLaboral×Instrumento (obligatorio/deseable) |
| `OfertaGenero` | M2M OfertaLaboral×Genero con prioridad |
| `Postulacion` | Músico postula a oferta. unique_together (oferta, musico). Tipos: espontanea/invitacion |
| `Invitacion` | Empleador invita músico. Expira en 7 días. Al aceptar → crea Postulacion automáticamente |
| `Notificacion` | Notificaciones para empleadores (solo). Creadas por signals en Postulacion e Invitacion |

### Relaciones clave
```
Usuario ──OneToOne──► PerfilMusico
Usuario ──OneToOne──► PerfilEmpleador
Usuario ──OneToOne──► Portafolio
         └─── M2M ──► Instrumento (via PortafolioInstrumento)
         └─── M2M ──► Genero (via PortafolioGenero)
         └─── FK ───► NivelExperiencia
         └─── FK ───► Ubicacion

PerfilEmpleador ──FK──► OfertaLaboral ──FK──► Postulacion ◄──FK── Usuario(musico)
                                       └───► Invitacion  ◄──FK── Usuario(musico)
                                       └───► Notificacion ──FK──► PerfilEmpleador

Invitacion ──OneToOne──► Postulacion (postulacion_creada, se crea al aceptar)
```

---

## 5. Flujos principales

### Auth
- Registro: `RegistroForm` (email + username + tipo_usuario + foto_perfil opcional) → login automático → redirige a `inicio` (⚠️ TODO: debería ir a crear perfil según tipo)
- Login: por email o username (`EmailBackend` busca con `Q(email__iexact=...) | Q(username__iexact=...)`)
- Recuperar contraseña: `default_token_generator` + email con link firmado → cambio de password

### Perfiles y portafolio
1. Músico edita `PerfilMusico` (datos privados) en `/perfil/musico/editar/`
2. Músico crea/edita `Portafolio` (público) en `/portafolio/musico/crear/` o `/portafolio/musico/editar/`
3. Portafolio público visible sin auth en `/portafolio/<slug>/`
4. Empleador crea `PerfilEmpleador` en `/perfil-empleador/crear/` (CBV)

### Ofertas laborales
```
Empleador crea oferta (borrador) → publica → músicos buscan en /ofertas/
→ músico postula → empleador gestiona en /ofertas/<slug>/postulaciones/
→ acepta postulación → signal verifica cupos → cierra oferta si completa
```

### Invitaciones directas
```
Empleador ve portafolio → /invitar/<portafolio_slug>/ → crea Invitacion
→ músico ve en /invitaciones-recibidas/ → acepta (Invitacion.aceptar())
→ se crea Postulacion automáticamente → signal notifica al empleador
```
La invitación expira a los 7 días. El management command `marcar_invitaciones_expiradas` debe correrse como cron para marcar expiradas.

### Referencias/Testimonios
```
Músico solicita → email con token único → contacto responde en /referencias/responder/<token>/
→ músico aprueba/rechaza en /referencias/gestionar/
```
También: músico agrega testimonio directo (estado `directo`, visible de inmediato sin aprobación).

### Notificaciones (solo empleadores)
- Creadas por signals `post_save` en `Postulacion` e `Invitacion`
- Tipos: nueva_postulacion, postulacion_cancelada, invitacion_aceptada/rechazada/expirada
- Sin push/WebSockets — se cargan al visitar `/notificaciones/`

---

## 6. URLs importantes

```python
# Públicas (sin auth)
/                                    # inicio — portafolios destacados + stats
/buscar/  o  /musicos/               # búsqueda de portafolios
/ofertas/  o  /trabajos/             # búsqueda de ofertas
/portafolio/<slug>/                  # portafolio público del músico
/perfil/<username>/                  # perfil público del músico

# Auth
/registro/                           # registro nuevo usuario
/login/                              # login
/logout/                             # logout
/recuperar-password/                 # solicitar reset
/cambiar-password/<uidb64>/<token>/  # cambiar password con token

# Músico (requiere tipo='musico')
/perfil/musico/editar/               # editar datos privados
/portafolio/musico/crear/            # crear portafolio
/portafolio/musico/editar/           # editar portafolio
/mis-postulaciones/                  # ver postulaciones propias
/invitaciones-recibidas/             # ver invitaciones recibidas
/invitaciones/<id>/responder/        # aceptar/rechazar invitación
/referencias/gestionar/              # gestionar referencias propias

# Empleador (requiere tipo='empleador')
/perfil-empleador/crear/             # crear perfil de organización
/ofertas/nueva/                      # crear oferta
/ofertas/mis-ofertas/                # ver ofertas propias
/ofertas/<slug>/editar/              # editar oferta
/ofertas/<slug>/publicar/            # publicar (borrador → publicada)
/ofertas/<slug>/cerrar/              # cerrar oferta
/ofertas/<slug>/postulaciones/       # gestionar postulaciones
/invitar/<portafolio_slug>/          # invitar músico directamente
/notificaciones/                     # ver notificaciones

# Admin
/admin/                              # Django admin — completo con acciones bulk y exportar CSV
```

---

## 7. Comandos útiles

```bash
# Servidor de desarrollo
python manage.py runserver

# Migraciones
python manage.py makemigrations
python manage.py migrate

# Poblar catálogos (EJECUTAR después de migrate en entorno nuevo)
python manage.py poblar_catalogos

# Marcar invitaciones expiradas (configurar como cron en producción)
python manage.py marcar_invitaciones_expiradas

# Crear superusuario
python manage.py createsuperuser

# Tests (estructura vacía — no hay tests implementados aún)
python manage.py test
# o
pytest  # requiere conftest.py en raíz (existe)

# Shell con contexto del proyecto
python manage.py shell

# Colectar estáticos (solo para producción)
python manage.py collectstatic
```

---

## 8. Estado actual

### Funciona completamente
- Registro, login/logout, recuperación de contraseña (email por consola en dev)
- CRUD de perfiles: músico (privado) y empleador (organización)
- Portafolio completo: instrumentos, géneros, multimedia, testimonios, visibilidad granular
- Búsqueda de portafolios y ofertas
- CRUD completo de ofertas laborales con ciclo de estados
- Postulaciones: crear, cancelar, gestionar, aceptar/rechazar con cierre automático de oferta
- Invitaciones directas con expiración y auto-creación de postulación al aceptar
- Sistema de notificaciones para empleadores (vía signals)
- Sistema de referencias con token por email (solicitar, responder, aprobar/rechazar)
- Admin Django completo con filtros, acciones bulk y exportar CSV

### Incompleto / con deuda
- `_redirect_by_user_type` siempre redirige a `inicio` — TODO: llevar a crear perfil según tipo
- **Tests vacíos** — estructura creada pero sin implementación (cobertura = 0%)
- Notificaciones para músicos **no implementadas** (solo existen para empleadores)
- DRF instalado sin ningún endpoint REST
- Multimedia del portafolio: modelo completo, gestión en vistas puede ser parcial
- Sin paginación en búsquedas

### Drift en admin.py (⚠️ genera errores en Django Admin)
`admin.py` referencia campos eliminados en migraciones — causarán errores si se usan esos inlines/fieldsets:
- `PortafolioInstrumentoInline`: `nivel_dominio`, `orden_presentacion` (no existen)
- `PortafolioGeneroInline`: `preferencia`, `años_experiencia`, `orden_presentacion` (no existen)
- `MultimediaInline`: `archivo`, `url_externa`, `es_principal` (modelo tiene `imagen`, `url`)
- `TestimonioInline`: `nombre_cliente`, `empresa_evento`, `testimonio`, `puntuacion` (campos renombrados/eliminados)
- `PerfilMusicoAdmin`: `contacto_emergencia` (eliminado en migración 0012)
- `OfertaLaboralAdmin`: `direccion_evento`, `incluye_transporte/hospedaje/alimentacion` (no existen)

---

## 9. Pendientes para producción

```python
# Variables de entorno requeridas (actualmente hardcodeadas en settings.py)
SECRET_KEY=<generar con: python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())">
DEBUG=False
ALLOWED_HOSTS=tudominio.com,www.tudominio.com
DATABASE_URL=postgres://user:pass@host:5432/dbname

# Email (consola → SMTP real)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.sendgrid.net  # o SES, Mailgun, etc.
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=...
EMAIL_HOST_PASSWORD=...
DEFAULT_FROM_EMAIL=noreply@meetandgig.com

# Media files en producción
# Configurar S3 (django-storages) o equivalente para MEDIA_ROOT
```

**Checklist de producción:**
- [x] ~~Usar `python-decouple` o `django-environ` para leer `.env`~~ — implementado con `django-environ==0.11.2`
- [ ] Cambiar SQLite → PostgreSQL
- [ ] `python manage.py collectstatic`
- [ ] Configurar SMTP real para emails
- [ ] Configurar cron para `marcar_invitaciones_expiradas` (sugerido: cada hora)
- [ ] Configurar servidor web (Gunicorn + Nginx o equivalente)
- [ ] Corregir drift en `admin.py` (campos eliminados referenciados en inlines)
- [ ] Implementar tests antes de deploy

---

## 10. Convenciones del proyecto

### Estilo de código
- **Español** para nombres de variables, comentarios, mensajes al usuario y nombres de modelos
- **Inglés** no se usa — todo en español incluyendo `verbose_name` en modelos
- Decoradores `@login_required` para vistas funcionales; mixins (`LoginRequiredMixin`, `EmpleadorRequiredMixin`) para CBVs
- Validación de tipo de usuario al inicio de cada vista: `if request.user.tipo_usuario != 'musico': ...`
- Flash messages vía `django.contrib.messages` para feedback al usuario
- Slugs auto-generados en `save()` del modelo (Portafolio y OfertaLaboral)

### Organización de lógica de negocio
- **Business logic en modelos**: `Invitacion.aceptar()`, `Invitacion.rechazar()`, `OfertaLaboral.verificar_y_cerrar_si_completa()`, etc.
- **Signals en `signals.py`**: solo para side-effects (crear notificaciones, cerrar ofertas)
- **Helpers privados en views**: funciones con `_` prefijo (`_redirect_by_user_type`, `_send_password_reset_email`)
- Formularios con validación de imagen en `forms.py` (tamaño máx 5MB, dimensiones mín 100×100)

### Tests
- Estructura en `tests/` con subdirectorios `unit/`, `integration/`, `factories/` — todos vacíos
- `conftest.py` existe en raíz (para pytest)
- `usuarios/tests_sprint_4_notificaciones.py` existe fuera de la estructura estándar
- **Usar pytest** (no `unittest` puro) según la presencia de `conftest.py`
- Al crear tests, usar factories (en `tests/factories/`) para fixtures
- No mockear la BD — usar SQLite en tests (ya configurado)

### Migraciones
- 24 migraciones en `usuarios/migrations/` — historial largo con varios campos eliminados
- Nombradas descriptivamente en algunas: `0012_eliminar_contacto_emergencia`, `0023_ticket_4_1_sistema_referencias`
- Al agregar campos, considerar el drift existente en `admin.py`

### Patterns a seguir al agregar funcionalidad
1. Agregar modelo en `models.py` con `verbose_name` en español
2. Crear migración
3. Agregar formulario en `forms.py`
4. Agregar vista en `views.py` (funcional con `@login_required` o CBV con mixin)
5. Registrar URL en `usuarios/urls.py`
6. Registrar en `admin.py` (verificar que los campos referenciados existan)
7. Crear template en `usuarios/templates/usuarios/`
