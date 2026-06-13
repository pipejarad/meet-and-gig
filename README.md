# Meet & Gig 🎵

**Vitrina digital para músicos independientes chilenos.** Conecta a quienes hacen música
en vivo con quienes los contratan —bares, restaurantes, hoteles, productoras y eventos—
combatiendo la informalidad laboral del rubro.

[![Django](https://img.shields.io/badge/Django-4.2-092E20.svg?logo=django)](https://djangoproject.com)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB.svg?logo=python&logoColor=white)](https://python.org)
[![Bootstrap](https://img.shields.io/badge/Bootstrap-4-7952B3.svg?logo=bootstrap&logoColor=white)](https://getbootstrap.com)
[![Deploy](https://img.shields.io/badge/Deploy-Railway-0B0D0E.svg?logo=railway&logoColor=white)](https://railway.app)

---

## Tabla de contenidos

- [¿Qué es?](#qué-es)
- [Alcance de la v1](#alcance-de-la-v1)
- [Funcionalidades](#funcionalidades)
- [Stack tecnológico](#stack-tecnológico)
- [Arquitectura](#arquitectura)
- [Estructura del proyecto](#estructura-del-proyecto)
- [Instalación local](#instalación-local)
- [Variables de entorno](#variables-de-entorno)
- [Rutas principales](#rutas-principales)
- [Tests](#tests)
- [Despliegue en Railway](#despliegue-en-railway)
- [Principios y restricciones](#principios-y-restricciones)
- [Documentación del repositorio](#documentación-del-repositorio)
- [Autor](#autor)

---

## ¿Qué es?

Meet & Gig nace de un problema concreto: gran parte de los músicos independientes en Chile
trabaja sin contrato y de forma informal. La plataforma les da una **vitrina profesional
pública** —su portafolio— y un canal de **contacto mediado** para que quienes buscan música
en vivo lleguen a ellos sin fricción.

El proyecto tiene un doble objetivo: ser una **pieza de portafolio profesional** y **validar
la idea con usuarios reales**. La prioridad declarada es *velocidad a producción por sobre
perfección arquitectónica*.

---

## Alcance de la v1

> El código se construyó originalmente como un marketplace de **dos lados** (músicos y
> empleadores). La v1 **pivotó a una vitrina de un solo lado: solo músicos.** Los módulos
> del segundo lado siguen en el repositorio pero ocultos.

**Activo en la v1:**

- Autenticación de músicos.
- Perfil privado + portafolio público del músico.
- Búsqueda y filtrado de portafolios.
- Contacto mediado de visitantes hacia músicos.
- Asistente de IA para redactar la biografía del portafolio.

**Diferido (presente en el código, oculto de la UI — regla _ocultar, no borrar_):**

- Perfil de empleador.
- Ofertas laborales, postulaciones e invitaciones.
- Referencias y testimonios laborales.
- Notificaciones in-app (la única notificación viva en la v1 es el email al músico cuando
  recibe un contacto).

Los módulos diferidos conservan modelos y migraciones intactos; solo se retiran de la
navegación y las rutas (marcadores `DIFERIDO v1` en el código). Vuelven en el mediano/largo
plazo. El detalle de qué modelo está vivo y cuál dormido está en
[`docs/data-model.md`](docs/data-model.md).

---

## Funcionalidades

### 🔐 Autenticación

- Registro con email único y validación de contraseña.
- Login con **email o username** mediante backend personalizado (`usuarios.backends.EmailBackend`).
- Recuperación de contraseña por enlace con token.
- Email y username únicos **case-insensitive a nivel de base de datos**; el email se
  normaliza a minúsculas en toda vía de creación.

### 👤 Perfil y portafolio del músico

- `PerfilMusico`: datos privados (teléfono, preferencias de privacidad), creado
  automáticamente al registrarse.
- `Portafolio`: la vitrina pública —biografía, formación, experiencia, instrumentos,
  géneros, multimedia y enlaces sociales (YouTube, Spotify, SoundCloud, Instagram…)—.
  Soporta variantes: solista, banda, proyecto, productora.
- URL pública por **slug congelado** (`/portafolio/<slug>/`); requiere `activo=True` para
  ser visible.
- El músico decide qué datos de contacto se muestran al público (`show_email`,
  `show_telefono`, opt-in).

### 🔍 Búsqueda

- Búsqueda y filtrado de portafolios por instrumentos, géneros, ubicación y experiencia,
  apoyada en catálogos normalizados.

### 📇 Catálogos normalizados

- Instrumentos (por categoría, incluye folclore chileno), géneros musicales, niveles de
  experiencia y comunas de Chile, normalizados para perfiles y búsqueda.
- Se siembran automáticamente al migrar (migraciones de datos `0019` + `0030`): esa es la
  **única fuente de verdad** del catálogo. No hay comando de seed aparte.

### 💬 Contacto mediado

Visitantes **no autenticados** contactan a un músico vía formulario público
(`/portafolio/<slug>/contactar/`); el músico gestiona el embudo en "Mis contactos".

- *"Mediado = medido, no controlado":* el email del músico **nunca** se expone en el HTML;
  el correo se maneja del lado del servidor y lleva `Reply-To` del visitante para que el
  músico responda directo.
- Embudo medido por estados: **enviado → visto → respondido → convertido**. El paso a
  `visto` es automático; `respondido` y `convertido` los marca el músico a mano (es el
  instrumento de validación del proyecto).
- Anti-spam mínimo: honeypot + límite de 5 contactos/hora por IP.

### ✨ Asistente de IA para biografías

- Genera **borradores** de biografía (2 variantes) a partir de un formulario de preguntas
  predefinidas; el músico **edita y aprueba** en el editor del portafolio (nunca autopublica).
- Usa la API de Anthropic con un modelo económico (`claude-haiku-4-5`, configurable).
- Es **opcional**: sin `ANTHROPIC_API_KEY` el asistente se desactiva solo, con un aviso
  amable, sin romper nada del resto del sitio.
- Límite de generaciones por día y por músico.

---

## Stack tecnológico

| Capa | Tecnología |
|---|---|
| Backend | Django 4.2 (patrón MVT) · Python 3.11 |
| Base de datos | SQLite (desarrollo) · PostgreSQL (producción, vía `dj`/`environ` y `DATABASE_URL`) |
| Frontend | Bootstrap 4 · HTML5 · CSS3 · JavaScript |
| Estáticos | WhiteNoise (comprimido con manifest) |
| Media | `django-storages` sobre S3-compatible (Cloudflare R2 / Backblaze B2) |
| Servidor de aplicación | Gunicorn |
| Hosting | Railway |
| IA | API de Anthropic (`anthropic` SDK) para el asistente de biografías |
| Testing | pytest + Django test runner |
| Localización | `es-CL`, zona horaria `America/Santiago` |

---

## Arquitectura

- **App principal:** `usuarios` concentra autenticación, perfiles, portafolios, búsqueda,
  contacto mediado y el asistente de IA.
- **Settings divididos por entorno** (`meetandgig/settings/`):
  - `base.py` — configuración compartida.
  - `development.py` — `DEBUG=True`, SQLite, email a consola. Es el **default de `manage.py`**.
  - `production.py` — `DEBUG=False`, PostgreSQL, SMTP real, HTTPS forzado, media en S3.
    Es el **default de `wsgi.py`/`asgi.py`**.
- **Servicios aislados:** la integración con la IA vive en `usuarios/services/bio_ia.py`,
  de modo que cambiar de modelo o proveedor no toca vistas ni templates.
- **Modelo de datos:** ~16 modelos centrados en `Usuario` → `PerfilMusico` / `Portafolio`,
  más catálogos y `ContactoMusico`. El mapa completo (activo vs. diferido) está en
  [`docs/data-model.md`](docs/data-model.md).

---

## Estructura del proyecto

```
meet-and-gig/
├── meetandgig/                 # Configuración del proyecto Django
│   ├── settings/               # base.py · development.py · production.py
│   ├── urls.py                 # Incluye usuarios.urls en la raíz
│   ├── static/                 # Estáticos del proyecto (CSS, JS, vendor)
│   └── wsgi.py / asgi.py       # Entry points (default: settings.production)
├── usuarios/                   # App principal
│   ├── models.py               # Modelos (activos + diferidos)
│   ├── views.py                # Vistas de auth, perfil, portafolio, contacto
│   ├── forms.py                # Formularios con validación
│   ├── admin.py                # Admin personalizado
│   ├── backends.py             # EmailBackend (login por email o username)
│   ├── signals.py              # Auto-creación de perfil/portafolio
│   ├── services/
│   │   └── bio_ia.py           # Asistente de IA de biografías (aislado)
│   ├── management/commands/    # marcar_invitaciones_expiradas, aplicar_retencion_datos
│   ├── migrations/
│   └── templates/usuarios/     # Templates de la app
├── templates/
│   ├── base.html               # Layout base con navbar dinámico
│   └── emails/                 # Plantillas de correo
├── tests/                      # Suite pytest (unit, integration, factories)
├── docs/                       # Documentación del proyecto (ver más abajo)
├── .env.example                # Plantilla de variables de entorno
├── requirements.txt            # Dependencias de producción
├── requirements-dev.txt        # Dependencias de desarrollo
├── Procfile / railway.json     # Configuración de despliegue
├── runtime.txt                 # Versión de Python (3.11)
├── CLAUDE.md                   # Contexto y reglas de trabajo del repo
├── ROADMAP.md                  # Plan de producto y decisiones
└── manage.py
```

---

## Instalación local

**Requisitos:** Python 3.11 y Git.

```bash
# 1. Clonar el repositorio
git clone https://github.com/pipejarad/meet-and-gig.git
cd meet-and-gig

# 2. Crear y activar el entorno virtual
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Crear el archivo .env a partir de la plantilla
cp .env.example .env
# Edita .env y define al menos SECRET_KEY (es obligatorio incluso en desarrollo).
# Genera una con:
#   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# 5. Aplicar migraciones (usa SQLite en desarrollo)
# Las migraciones de datos siembran los catálogos completos (instrumentos por
# categoría, géneros, niveles y comunas) — no hay comando de seed aparte.
python manage.py migrate

# 6. Crear un superusuario (opcional, para el admin)
python manage.py createsuperuser

# 7. Levantar el servidor de desarrollo
python manage.py runserver
```

La aplicación queda disponible en `http://127.0.0.1:8000/`. En desarrollo los correos se
imprimen en la consola (no se envían), así que el flujo de recuperación de contraseña y el
aviso de contacto se pueden inspeccionar ahí mismo.

---

## Variables de entorno

Todas se documentan en [`.env.example`](.env.example). Resumen:

| Variable | Obligatoria | Notas |
|---|---|---|
| `SECRET_KEY` | Siempre | Sin ella el proyecto no arranca, ni en desarrollo. |
| `ALLOWED_HOSTS` | Producción | Separados por coma. |
| `DATABASE_URL` | Producción | `postgres://usuario:password@host:5432/db`. En desarrollo se usa SQLite. |
| `CSRF_TRUSTED_ORIGINS` | Producción | Origen completo (`https://…`); obligatorio detrás del proxy de Railway. |
| `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_USE_TLS`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` | Producción | SMTP real. |
| `DEFAULT_FROM_EMAIL`, `SITE_URL` | Recomendadas | Remitente y URL base para enlaces de correo. |
| `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_STORAGE_BUCKET_NAME`, `AWS_S3_ENDPOINT_URL`, `AWS_S3_REGION_NAME` | Opcional | Media en R2/B2. Si el bucket está vacío, la media va al disco local. |
| `ANTHROPIC_API_KEY` | Opcional | Sin ella, el asistente de IA se desactiva con un aviso. |
| `BIO_IA_MODELO` | Opcional | Modelo del asistente; por defecto `claude-haiku-4-5`. |

> **Los secretos siempre van en variables de entorno**, nunca en el repositorio.

---

## Rutas principales

Las URLs cuelgan de la raíz (la app `usuarios` se incluye en `/`):

| Ruta | Descripción |
|---|---|
| `/` | Página de inicio |
| `/registro/` · `/login/` · `/logout/` | Autenticación |
| `/recuperar-password/` | Recuperación de contraseña |
| `/buscar/` · `/musicos/` | Búsqueda de portafolios |
| `/portafolio/<slug>/` | Portafolio público del músico |
| `/portafolio/<slug>/contactar/` | Formulario de contacto mediado |
| `/perfil/<username>/` | Perfil público por username |
| `/mis-contactos/` | Bandeja de contactos recibidos (músico autenticado) |
| `/portafolio/asistente-bio/` | Asistente de IA de biografías |
| `/admin/` | Panel de administración (requiere superusuario) |

---

## Tests

La suite vive en `tests/` (`unit/`, `integration/`, `factories/`) y se ejecuta con pytest;
la configuración está en `pytest.ini`.

```bash
pytest                          # Toda la suite
pytest tests/unit               # Solo tests unitarios
python manage.py test           # Alternativa con el runner de Django
```

---

## Despliegue en Railway

- **PostgreSQL** como add-on: inyecta `DATABASE_URL` automáticamente.
- **Settings de producción:** define `DJANGO_SETTINGS_MODULE=meetandgig.settings.production`.
- **Migraciones** en el pre-deploy y **`collectstatic`** en el arranque (ver `railway.json`).
- **Estáticos** servidos por WhiteNoise; **HTTPS** lo termina el proxy de Railway
  (`SECURE_PROXY_SSL_HEADER` ya está configurado).
- **Filesystem efímero:** el disco de Railway **no persiste** entre deploys. La media subida
  por los usuarios debe ir a almacenamiento S3-compatible (Cloudflare R2 o Backblaze B2)
  configurando las variables `AWS_*`. Sin ellas, los archivos se pierden en cada deploy.

---

## Principios y restricciones

Reglas no negociables del proyecto (ver `CLAUDE.md` y `ROADMAP.md` para el detalle):

- **Ocultar, no borrar.** Los módulos diferidos (empleador, ofertas, postulaciones,
  invitaciones, referencias) se retiran de la UI pero conservan modelos y migraciones; no se
  construye sobre ellos hasta reactivarlos.
- **La plataforma es intermediario**, no empleador ni parte del contrato. No se agrega lógica
  que la posicione como empleadora.
- **Nunca custodia de dinero propia.** Si en el futuro hay pagos, irán por una pasarela
  licenciada con *split payment*; el dinero no pasa por cuentas de la plataforma (riesgo
  regulatorio: Ley Fintech 21.521 / CMF).
- **El refactor viene después de validar con usuarios**, no antes: no se persigue perfección
  arquitectónica sin tracción.

---

## Documentación del repositorio

| Archivo | Para qué sirve |
|---|---|
| [`CLAUDE.md`](CLAUDE.md) | Contexto, alcance vigente y reglas de trabajo del repositorio. |
| [`ROADMAP.md`](ROADMAP.md) | Plan de producto, decisiones estratégicas y razonamiento. |
| [`docs/data-model.md`](docs/data-model.md) | Mapa de modelos: qué está activo y qué diferido. |
| [`.env.example`](.env.example) | Referencia completa de variables de entorno. |

---

## Autor

**Felipe Jara** — [@pipejarad](https://github.com/pipejarad)

- LinkedIn: [Felipe Jara](https://www.linkedin.com/in/felipe-jara-6582a3100/)
- Email: jarad.felipe@gmail.com
</content>
</invoke>
