# CONTEXT.md — Meet & Gig

## 1. Qué hace la aplicación y para quién

**Meet & Gig** es un marketplace laboral musical enfocado en Chile que conecta:
- **Músicos** (freelance): crean portafolios profesionales y postulan a ofertas o reciben invitaciones directas.
- **Empleadores** (empresas, restaurantes, hoteles, eventos, organizaciones): publican ofertas laborales, buscan músicos y los invitan directamente.

Flujo central: empleador publica oferta → músico postula o recibe invitación → empleador gestiona postulaciones → músicos acumulan referencias/testimonios en su portafolio.

---

## 2. Arquitectura de modelos

Toda la lógica vive en la app `usuarios/`. No hay otras apps Django.

### Modelos de usuario y perfiles
```
Usuario (AbstractUser)
├── tipo_usuario: 'musico' | 'empleador'
├── USERNAME_FIELD = 'email'           ← login por email
├── foto_perfil (ImageField)
├── → PerfilMusico (OneToOne)          ← datos privados/admin del músico
└── → PerfilEmpleador (OneToOne)       ← datos públicos de la organización
```

### Catálogos normalizados
```
Instrumento      (nombre, categoria)
Genero           (nombre, descripcion)
NivelExperiencia (nombre, orden, años_minimos, años_maximos)
Ubicacion        (nombre, region, pais, orden, activo)
```
Poblados vía management command `poblar_catalogos`.

### Portafolio del músico (perfil público)
```
Portafolio (OneToOne → Usuario)
├── slug (único, auto-generado desde username)
├── biografia, formacion_musical, años_experiencia
├── nivel_experiencia → NivelExperiencia
├── ubicacion → Ubicacion
├── tarifa_base (CLP), disponible_para_gigs
├── flags: show_email, show_social_links, show_education, show_tarifa, show_telefono
├── enlaces: soundcloud_url, youtube_url, spotify_url, instagram_url, facebook_url, website_personal
├── → PortafolioInstrumento (M2M con metadata: es_principal, prioridad, años_experiencia)
├── → PortafolioGenero (M2M con prioridad)
├── → Multimedia (imágenes locales + embeds de YouTube/Vimeo/SoundCloud/Spotify)
└── → Testimonio (referencias y testimonios con sistema de aprobación)
```

### Testimonio / Referencias (Ticket 4.1)
```
Testimonio
├── portafolio → Portafolio
├── autor_usuario → Usuario (opcional, si es usuario registrado)
├── estado: 'pendiente' | 'aprobado' | 'rechazado' | 'directo'
├── tipo: 'referencia_laboral' | 'testimonio_cliente' | 'recomendacion_general'
├── token_solicitud (auto-generado para links de aprobación por email)
└── campos: texto, proyecto_evento, fecha_inicio/fin_colaboracion
```

### Ofertas laborales
```
OfertaLaboral (→ PerfilEmpleador)
├── slug (único, auto-generado)
├── estado: 'borrador' | 'publicada' | 'cerrada' | 'cancelada'
├── tipo_contrato: evento_unico | contrato_temporal | indefinido | freelance | colaboracion
├── presupuesto_minimo / presupuesto_maximo / presupuesto_a_convenir
├── cupos_disponibles (cierra automáticamente al completarse vía signal)
├── nivel_experiencia_minimo → NivelExperiencia
├── ubicacion → Ubicacion
├── → OfertaInstrumento (instrumentos requeridos, obligatorio/deseable)
└── → OfertaGenero (géneros preferidos)
```

### Postulaciones e Invitaciones
```
Postulacion (OfertaLaboral × Usuario músico)
├── portafolio → Portafolio
├── tipo_postulacion: 'espontanea' | 'invitacion'
├── estado: pendiente | en_revision | aceptada | rechazada | cancelada
├── unique_together: (oferta_laboral, musico)
└── tarifa_propuesta, mensaje_personalizado, notas_empleador

Invitacion (OfertaLaboral × músico × PerfilEmpleador)
├── portafolio → Portafolio (el que motivó la invitación)
├── estado: pendiente | aceptada | rechazada | expirada | cancelada
├── fecha_expiracion (7 días por defecto)
├── postulacion_creada → Postulacion (OneToOne, se crea al aceptar)
└── unique_together: (oferta_laboral, musico)
```

### Notificaciones (solo para empleadores)
```
Notificacion (→ PerfilEmpleador)
├── tipo: nueva_postulacion | postulacion_cancelada | oferta_completada |
│        invitacion_aceptada | invitacion_rechazada | invitacion_expirada
├── FK opcionales: postulacion, oferta_laboral, invitacion
└── leida (bool), fecha_lectura
```

**Signals activos** (`signals.py`):
- `post_save(Postulacion)` → cierra oferta si se completan cupos; crea notificación al cancelar.
- `post_save(Invitacion)` → crea notificación al aceptar, rechazar o expirar.

---

## 3. Flujos principales

### Auth
1. Registro: `RegistroForm` → crea `Usuario` + redirige a inicio (TODO: debería redirigir a creación de perfil).
2. Login por email: `EmailBackend` custom + `LoginForm`.
3. Recuperar contraseña: email con token (`default_token_generator`) → URL firmada → cambio.
4. Email backend en **modo consola** (imprime en terminal, no envía emails reales).

### Perfiles
- **Músico**: `PerfilMusico` (datos privados) + `Portafolio` (datos públicos). Son dos entidades separadas.
- **Empleador**: `PerfilEmpleador` (datos de organización). CBVs: `CrearPerfilEmpleadorView`, `EditarPerfilEmpleadorView`.
- Portafolio público accesible por `/portafolio/<slug>/` sin autenticación.

### Ofertas laborales
1. Empleador crea oferta (estado: `borrador`).
2. Publica (`/ofertas/<slug>/publicar/`).
3. Músicos buscan en `/ofertas/` o `/trabajos/`.
4. Músico postula desde `/ofertas/<slug>/postular/`.
5. Empleador gestiona en `/ofertas/<slug>/postulaciones/`.
6. Al aceptar postulación: signal verifica si se completaron cupos → cierra oferta automáticamente.

### Invitaciones directas
1. Empleador navega a portafolio de músico → `/invitar/<portafolio_slug>/`.
2. Crea `Invitacion` con mensaje, tarifa ofrecida y oferta asociada.
3. Músico ve invitaciones en `/invitaciones-recibidas/`.
4. Aceptar → llama a `Invitacion.aceptar()` → crea `Postulacion` automáticamente.
5. Signal notifica al empleador del resultado.

### Referencias
1. Músico solicita referencia a contacto externo por email (token único).
2. Contacto responde vía `/referencias/responder/<token>/` (sin login).
3. Músico aprueba/rechaza en `/referencias/gestionar/`.
4. También puede agregar testimonios directos (estado: `directo`, visible de inmediato).

---

## 4. Estado actual del código

### Funciona
- Registro, login/logout, recuperación de contraseña.
- Creación y edición de perfiles (músico y empleador).
- Portafolio público con instrumentos, géneros, multimedia y testimonios.
- Búsqueda de portafolios y ofertas.
- CRUD completo de ofertas laborales (borrador → publicar → cerrar/reabrir).
- Postulaciones (crear, cancelar, gestionar, aceptar/rechazar).
- Sistema de invitaciones directas con expiración automática.
- Notificaciones en tiempo de solicitud (sin WebSockets, solo al cargar página).
- Sistema de referencias con token por email.
- Management command `marcar_invitaciones_expiradas` para expiración por batch.
- Admin de Django configurado (`admin.py`).

### Incompleto / pendiente
- `_redirect_by_user_type` redirige siempre a `'inicio'` con TODO comment — no dirige a creación de perfil tras registro.
- Tests en `tests/unit/`, `tests/integration/` y `tests/factories/` están **vacíos** (solo `__init__.py`).
- `tests_sprint_4_notificaciones.py` existe en `usuarios/` pero fuera de la estructura estándar de tests.
- DRF instalado pero **ningún endpoint REST implementado**.
- Notificaciones para **músicos** no implementadas (solo para empleadores).
- Multimedia del portafolio: modelo completo pero la gestión en views/templates puede ser parcial.
- No hay paginación en búsquedas de portafolios u ofertas.

---

## 5. Deudas técnicas evidentes

| Prioridad | Deuda |
|-----------|-------|
| **Crítica** | `SECRET_KEY` hardcodeada en `settings.py` (valor inseguro expuesto en git) |
| **Crítica** | `DEBUG = True` sin configuración de producción ni `.env` / `django-environ` |
| **Alta** | SQLite como única BD — no apto para producción concurrente |
| **Alta** | Email backend = consola — no envía emails reales en ningún entorno |
| **Alta** | Tests vacíos — cobertura cero sobre lógica de negocio crítica |
| **Media** | App monolítica: todo en `usuarios/` — modelos, vistas, forms, signals en archivos únicos gigantes (`models.py` ~1350 líneas, `views.py` similar) |
| **Media** | `_redirect_by_user_type` redirige a inicio en lugar de al onboarding por tipo |
| **Media** | `marcar_invitaciones_expiradas` requiere cron externo, no configurado |
| **Media** | Scripts debug duplicados en raíz del proyecto (`debug_*.py`, `verificar_*.py`) y en `scripts/` |
| **Baja** | DRF instalado sin uso — dependencia sin propósito actual |
| **Baja** | `requirements.txt` mezcla deps de producción y desarrollo (autopep8, pycodestyle) |
| **Baja** | No hay `STATIC_ROOT` preparado ni `collectstatic` para producción |
| **Baja** | Dos URLs con el mismo path y view (`portafolio/<slug>/` duplicado en urls.py líneas 23-24) |

---

## 6. Stack y dependencias clave

| Componente | Tecnología |
|------------|-----------|
| Framework | Django 4.2.20 |
| BD | SQLite (desarrollo) — sin configuración para PostgreSQL/MySQL |
| Auth | `AbstractUser` custom + `EmailBackend` custom |
| Imágenes | Pillow 11.2.1 |
| API REST | djangorestframework 3.12.4 (instalado, sin uso) |
| Email | Console backend (desarrollo únicamente) |
| Frontend | Templates Django + Bootstrap/Tailwind (base.html) + Font Awesome (iconos) |
| Idioma/TZ | `es-cl` / `America/Santiago` |
| Python | 3.x (no especificado en requirements) |
| Despliegue | No configurado (WSGI presente, sin Gunicorn/Nginx config) |

### Estructura de directorios relevante
```
meet-and-gig/
├── meetandgig/          # Configuración del proyecto (settings, urls, wsgi)
│   └── static/          # Archivos estáticos del proyecto
├── usuarios/            # Única app — toda la lógica
│   ├── models.py        # ~1350 líneas: todos los modelos
│   ├── views.py         # Todas las vistas
│   ├── forms.py         # Todos los formularios
│   ├── urls.py          # 40+ rutas
│   ├── signals.py       # Señales post_save
│   ├── backends.py      # EmailBackend
│   ├── admin.py         # Registro admin
│   └── management/commands/
│       ├── poblar_catalogos.py           # Seeds de catálogos
│       └── marcar_invitaciones_expiradas.py  # Tarea programada manual
├── templates/
│   ├── base.html
│   └── emails/          # 4 templates de email
├── tests/               # Estructura vacía
├── scripts/             # Scripts de utilidad/debug
└── media/               # Uploads de usuarios (runtime)
```
