# Meet & Gig — Roadmap y Decisiones de Producto

> Documento de referencia. Consolida las decisiones estratégicas y de diseño tomadas
> para llevar Meet & Gig a producción y escalarlo por etapas.
> Pensado para tenerlo en el repo y alimentar sesiones de Claude Code.

---

## 1. Qué es Meet & Gig (estado actual)

Plataforma para conectar músicos independientes chilenos con quienes los contratan
(bares, restaurantes, hoteles, productoras, eventos). Nace de una problemática real:
gran parte de los músicos trabaja sin contrato y de manera informal.

**Stack:** Django 4.2 · SQLite (dev) / PostgreSQL (prod) · Bootstrap 4 · Python 3.9 · pytest
**Repo:** github.com/pipejarad/meet-and-gig
**Arquitectura:** MVT de Django · app principal `usuarios` · ~16 modelos · 30+ templates · 25+ endpoints

Ya construido: autenticación, perfil privado + portafolio público del músico, perfil de
empleador, ofertas laborales, postulaciones, invitaciones, notificaciones básicas,
referencias laborales, panel admin.

**El cuello de botella no es falta de producto, es que nada está lanzado ni validado.**
La estrategia es restar (ocultar lo que no es central) y lanzar, no seguir construyendo.

---

## 2. El pivote: de marketplace de dos lados a vitrina de un lado

La v1 deja de ser un marketplace de dos lados y pasa a ser una **vitrina**: un solo tipo
de usuario (el músico, en sus variantes — solista, banda, proyecto, productora) que sube y
muestra su material. Cualquier visitante, sin registrarse, puede navegar y contactar.

Por qué: elimina el arranque en frío ("la fiesta vacía") de un marketplace de dos lados.
No se necesitan empleadores para que la plataforma tenga sentido — basta con músicos que
valga la pena mostrar. Es la jugada de **empezar como directorio antes de ser mercado**.
Precedente directo: GigSalad (el líder global, ~USD 12M/año) empezó exactamente así.

El pivote es un ejercicio de **ocultar más, no construir más**: el portafolio público del
músico ya existe y *es* la vitrina.

### Decisión de scope sobre lo ya construido

| Módulo existente | Decisión v1 | Razón |
|---|---|---|
| Auth (músico) | Mantener | Puerta de entrada |
| Perfil + portafolio público del músico | Mantener | La vitrina, el corazón de la oferta |
| Perfil de empleador | **Diferir / ocultar** | El lado demanda llega en mediano plazo |
| Ofertas laborales | **Diferir** | Pertenecen al lado empleador |
| Postulaciones + invitaciones | **Diferir** | Mecanismo de marketplace de dos lados |
| Notificaciones | Simplificar | Solo email en eventos clave |
| Referencias laborales | **Ocultar** | Nadie tiene referencias al lanzar (arranque en frío). Se reactivan en largo plazo |

"Ocultar" = quitar de la navegación/UI sin borrar modelos ni migraciones. Reactivable después.

---

## 3. Contexto competitivo (resumen)

- **EchoMusic (Chile)** — competidor más cercano. Activo (eventos vigentes a 2026). Hoy
  enfocado en ticketing, crowdfunding y marketplace de artistas para *eventos puntuales*,
  no en empleo recurrente. Más de 1.300 artistas. Incubado en 3IE/USM.
- **MúsicosParaEventos.cl (Chile)** — agencia curada, no marketplace self-service.
- **GigSalad / The Bash / Encore / Gigstarter** — marketplaces sólidos pero en
  EE.UU./Canadá/UK/Europa; no sirven Chile; foco en eventos, no en empleo recurrente.
- **Sonnar (México/LATAM)** — arrancó fuerte en 2020, sin señales de actividad reciente.
  Cautionary tale: llegar a mercado importa, pero retener y transaccionar es lo que define.
- **Booking-Agent.io** — herramienta IA para que el músico encuentre venues (lado oferta).

**Diferenciación de Meet & Gig:** el ángulo **laboral recurrente** con locales/bares/
hoteles, no el evento puntual. Nadie en Chile resuelve eso hoy.

---

## 4. Plan en tres horizontes

### CORTO — Vitrina / tracción
Un solo lado. Músicos se listan; el público navega y contacta vía formulario mediado.
- Entregables: deploy + contacto mediado + asistente IA de bios.
- Monetización: ninguna (o test suave de "destacado" para músicos).
- Métrica clave: perfiles creados, visitas a perfiles, contactos iniciados.
- **Valida:** apetito de oferta + interés de audiencia. (NO valida demanda monetizable.)

### MEDIANO — Intermediación
Aparecen las cuentas de "contratista" con beneficios reales.
- Entregables: cuentas de contratista + modelo freemium + **consulta legal fintech**.
- Monetización: freemium (suscripción/beneficios del lado demanda).
- Métrica clave: contactos convertidos en pegas reales, recurrencia.
- **Valida:** demanda monetizable.

### LARGO — Transacción y confianza
Se integra el pago mediado y la infraestructura de confianza.
- Entregables: split payment + escrow + política de cancelación + disputas +
  generación de boletas de honorarios (SII) + reactivar referencias.
- Monetización: **comisión por transacción** (ingreso principal) + suscripciones.
- **Valida:** la tesis original (formalizar el trabajo informal) hecha producto. Defensibilidad.

> Decisión pendiente: ¿de qué lado se monetiza principalmente? Comisión a la demanda
> (Encore/The Bash) vs. visibilidad a la oferta (Gigstarter). Inclinación: comisión.

---

## 5. Diseño: contacto mediado (pieza nueva de la v1)

> ✅ **Construido el 05-06-2026**: modelo `ContactoMusico` (migración 0026), formulario
> público con honeypot + límite de 5/hora por IP, panel "Mis contactos" con el embudo
> (ENVIADO→VISTO automático al abrir el panel; RESPONDIDO/CONVERTIDO los marca el músico),
> email de aviso con Reply-To del visitante, y admin para medir el embudo.

**Principio:** "mediado" = **medido**, no controlado. En v1, captura siempre el dato y
mantén baja la fricción; aprieta el control (mensajería interna, límites) después. El
riesgo real ahora no es la filtración (que aún no monetizas) sino que los primeros y
escasos contactos se mueran de fricción.

**Privacidad:** el email del músico nunca se expone en el HTML público. El formulario hace
POST a la plataforma; el correo del músico se guarda del lado del servidor.

**Anti-spam (mínimo):** campo honeypot + límite por IP. Captcha (Cloudflare Turnstile)
solo si aparece spam real.

### Modelo

```python
class ContactoMusico(models.Model):
    class Estado(models.TextChoices):
        ENVIADO     = "enviado", "Enviado"
        VISTO       = "visto", "Visto"
        RESPONDIDO  = "respondido", "Respondido"
        CONVERTIDO  = "convertido", "Convertido en trabajo"

    # A quién se contacta — apuntar al modelo real de perfil de músico
    musico = models.ForeignKey("PerfilMusico", on_delete=models.CASCADE,
                               related_name="contactos")

    # Quién contacta — anónimo en v1, vinculable a cuenta en v2
    remitente_usuario  = models.ForeignKey(User, on_delete=models.SET_NULL,
                                           null=True, blank=True)
    remitente_nombre   = models.CharField(max_length=120)
    remitente_email    = models.EmailField()
    remitente_telefono = models.CharField(max_length=30, blank=True)

    # El mensaje
    mensaje        = models.TextField()
    tipo_necesidad = models.CharField(max_length=60, blank=True)

    # Medición del embudo
    estado   = models.CharField(max_length=20, choices=Estado.choices,
                                default=Estado.ENVIADO)
    creado   = models.DateTimeField(auto_now_add=True)
    visto_en = models.DateTimeField(null=True, blank=True)

    # Trazabilidad / anti-spam
    ip_remitente = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ["-creado"]
```

Dos decisiones que lo hacen escalable sin reescritura:
- **`remitente_usuario` FK nulo:** el mismo modelo sirve para contactos anónimos (v1) y
  para cuentas de contratista autenticadas (v2). Es la bisagra corto→mediano plazo.
- **`estado` (embudo):** el instrumento de validación. `CONVERTIDO` lo marca el músico
  ("¿esto se transformó en una pega?"). Esa tasa de conversión prueba la tesis del proyecto.

### Flujo
Visitante en portafolio → "Contactar" → formulario → backend valida (honeypot), guarda
`ContactoMusico`, envía email al músico → músico ve el mensaje (marca `VISTO`) → más tarde
marca el resultado (`CONVERTIDO` o no).

---

## 6. Modelo de ingresos

**La mediación de pago es el motor principal, no un beneficio más.** Cobrar comisión por
transacción alinea incentivos: la plataforma gana solo cuando músico y contratante ganan.

**Matiz clave:** comisión y suscripción freemium son **parcialmente sustitutos**, no
necesariamente acumulables. Cobrar por los dos lados suma fricción. Liderar con comisión;
usar freemium solo para extras de visibilidad y herramientas.

### Freemium — qué hace un contratista pagado que el visitante anónimo no puede
Lado demanda: publicar una necesidad para que los músicos postulen (invertir el flujo),
contactos ilimitados/prioritarios, filtros avanzados, historial de contactos (mini-CRM),
sello de verificado, y acceso al **pago mediado con protección** (el imán que empuja a
crear cuenta — nadie transfiere a un desconocido por WhatsApp).
Lado oferta (músicos): perfil destacado, más espacio de portafolio, analítica de visitas.
(El asistente de IA mejor dejarlo gratis: mejora la calidad de toda la vitrina.)

---

## 7. Regulación y riesgo operacional (Chile)

> No es asesoría legal. Validar con abogado especialista en fintech ANTES de construir pagos.

**Ley Fintech (Ley 21.521), fiscalizada por la CMF.** Uno de los giros regulados es la
"custodia/salvaguarda de dinero por cuenta de terceros". **Riesgo:** si la plataforma
recibe la plata del cliente, la retiene y luego la transfiere al músico, podría caer en esa
actividad regulada (inscripción en el Registro de Prestadores de Servicios Financieros de
la CMF; operar sin inscripción es infracción grave).

**Atajo:** no tocar nunca la plata. Usar una pasarela con **split payment (pago dividido)**
ya licenciada, que reparte automáticamente entre el músico y la comisión sin que el dinero
pase por la cuenta de la plataforma. La pasarela hace la custodia y cumple; la app orquesta.
- Marketplace / split: **Mercado Pago Marketplace, Stripe Connect, Kushki, Payku**.
- Suscripciones recurrentes (freemium): **Flow**.
- Analogía: no ser el banco (regulado, pesado), ser el notario (da fe, no guarda la plata).

**Estatus de la plataforma = INTERMEDIARIO, no empleador ni parte del contrato.** Protege
de responsabilidad por el evento y de obligaciones laborales. Va explícito en los términos.

**Ángulo laboral/tributario (= la tesis hecha producto):** el músico independiente emite
**boleta de honorarios al SII**; la plataforma puede ayudar a generarla y registrarla. La
comisión de la plataforma se factura aparte.

### Escenarios → dónde se resuelven
- **Músico no llega / tarde / accidente:** dinero retenido en escrow hasta confirmar el
  servicio; si no se entrega, reembolso; calificaciones generan rendición de cuentas.
- **Cliente cancela a última hora:** política de cancelación escalonada (estilo Airbnb).
- **Problemas técnicos / recinto sin equipo:** fuera del control de la plataforma; un
  "rider"/checklist acordado *antes* reduce disputas; los términos lo aclaran.
- (Encore ofrece seguro de responsabilidad como precedente para más adelante.)

---

## 8. Diseño: asistente de IA del portafolio

> ✅ **Construido el 05-06-2026** (Modo 1 + prefill desde el portafolio): servicio aislado
> `usuarios/services/bio_ia.py` con `claude-haiku-4-5` (configurable vía `BIO_IA_MODELO`),
> 2 variantes por generación + botón regenerar, límite de 5 generaciones/día (modelo
> `GeneracionBioIA`), human-in-the-loop (la variante elegida se carga como borrador en el
> editor del portafolio; el músico la edita y guarda — nunca se autopublica). Sin
> `ANTHROPIC_API_KEY` el asistente se desactiva con aviso. ~US$0.003 por generación.

**Problema que resuelve:** el músico es bueno tocando y malo describiéndose; el "Sobre mí"
vacío es la causa #1 de portafolios flojos → menos contactos → abandono. Sube la calidad de
la oferta y la tasa de perfiles completados.

**Tres modos de entrada, secuenciados por dificultad:**
1. **Formulario / preguntas predefinidas → bio.** El más fácil. ES LA v1 de la feature.
2. **Contexto textual del material** (títulos, enlaces a Spotify/YouTube, tags) en el
   prompt. Casi gratis. v1.5. (No requiere que la IA "escuche" el audio.)
3. **Entender audio/video de verdad** (multimodal). Caro y complejo. Futuro (v2).

**Principios:**
- **Human-in-the-loop:** la IA redacta un borrador, el músico edita y aprueba. Nunca
  autopublicar (evita "AI slop" y preserva la voz del músico).
- **Formulario estructurado > chat libre** (calidad consistente).
- **El prompt es el producto** (tono: profesional pero cercano, español de Chile, conciso,
  resaltar lo *contratable*).
- **No inventar datos** que el músico no entregó.
- **Costo:** modelo económico (Claude Haiku alcanza), generar solo al apretar botón,
  límite de generaciones/día por músico. API key en variable de entorno.
- UX: generar 2 variantes + botón "regenerar"; el músico elige.

### Esqueleto (servicio aislado para poder cambiar fuente/modelo sin tocar la UI)

```python
# services/bio_ia.py
import anthropic
client = anthropic.Anthropic()  # lee ANTHROPIC_API_KEY del entorno

SYSTEM = """Eres un periodista musical que escribe biografías de perfil
para una plataforma chilena que conecta músicos con quienes los contratan.
Escribe en español de Chile, tono profesional pero cercano, 80-120 palabras,
en tercera persona. Destaca lo que hace contratable al músico. Evita clichés.
Usa SOLO los datos entregados; no inventes presentaciones ni credenciales.
Devuelve solo el texto de la biografía, sin títulos ni comillas."""

def generar_bio(respuestas: dict, contexto_material: str = "") -> str:
    prompt = f"""Datos del músico:
- Nombre artístico: {respuestas.get('nombre')}
- Géneros: {respuestas.get('generos')}
- Formato e instrumentos: {respuestas.get('formato')}
- Años de experiencia: {respuestas.get('experiencia')}
- Presentaciones destacadas: {respuestas.get('destacados')}
- Disponible para: {respuestas.get('eventos')}
- Qué lo hace único: {respuestas.get('unico')}
{f'Material publicado: {contexto_material}' if contexto_material else ''}

Escribe la biografía."""
    msg = client.messages.create(
        model="claude-haiku-4-5",   # confirmar el modelo vigente en docs.claude.com
        max_tokens=400, system=SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text
```

Forward-compat: con la firma `generar_bio(respuestas, contexto_material)`, sumar el Modo 3
(multimodal) solo cambia lo que alimenta `contexto_material`; la UI no se mueve.

---

## 9. Plan de implementación de la v1 (deploy)

Ordenado por dependencia. ~1 semana de trabajo enfocado, sin features nuevas (salvo el
contacto mediado y, opcional, el asistente de IA).

- **Bloque 0 — Adelgazar.** Ocultar referencias de la navegación; reducir notificaciones a
  2 eventos clave. Sin borrar modelos/migraciones. Para el pivote: ocultar también empleador,
  ofertas, postulaciones, invitaciones.
- **Bloque 1 — Seguridad de config.** ✅ *Avanzado:* settings separados en
  base/development/production con `django-environ` (`SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS` y
  credenciales vía variables de entorno). Pendiente: revisar valores de producción al desplegar.
- **Bloque 2 — Base de datos.** PostgreSQL (add-on de Railway inyecta `DATABASE_URL`).
  Correr migraciones temprano (SQLite→Postgres puede tropezar con tipos).
- **Bloque 3 — Estáticos y media.** Estáticos: **WhiteNoise** (evita S3). Media (uploads):
  almacenamiento externo S3-compatible (Cloudflare R2 / Backblaze) vía `django-storages`
  — el disco de Railway es efímero. Punto técnico más delicado.
- **Bloque 4 — Email real.** Proveedor transaccional (Resend / Brevo). SMTP en variables de
  entorno. Probar recuperación de contraseña + las notificaciones.
- **Bloque 5 — Deploy a Railway.** Gunicorn (Procfile/comando de inicio), `requirements.txt`
  al día, variables cargadas. HTTPS automático en el subdominio de Railway.
- **Bloque 6 — Smoke test.** Recorrer el loop completo en producción con cuentas de prueba
  antes de invitar a nadie.

> Nuevo en la v1 (pivote): ✅ **contacto mediado construido** (sección 5). ✅ **asistente
> de IA construido** (sección 8). El dominio (`meetandgig.cl`) NO bloquea el lanzamiento.

### Pendientes de la auditoría técnica (04-06-2026)

Auditoría en 5 dimensiones (correctness, templates/URLs, seguridad, modelos/migraciones,
config/deploy). **Ya corregido:** Bloque 0 + bugs funcionales de la vitrina (teléfono
público, SEO del portafolio, enumeración de usuarios, copys del pivote) y preparación
para Postgres (migración 0019 portable; unicidad case-insensitive de email/username +
`UsuarioManager` que normaliza). Lo que sigue queda pendiente:

**Al hacer los Bloques 3-5 (config de deploy) — bloqueantes de producción:**
✅ *Resuelto el 05-06-2026* — la config quedó lista para Railway:
- [x] `SECURE_PROXY_SSL_HEADER` + `CSRF_TRUSTED_ORIGINS` en `production.py`.
- [x] `STATICFILES_DIRS` movido a `base.py` (collectstatic en producción: 895 archivos,
      antes 125). WhiteNoise con manifest comprimido + middleware en `base.py`.
- [x] `requirements.txt`: `psycopg[binary]`, `whitenoise`, `gunicorn`,
      `django-storages[s3]`; eliminado `djangorestframework`. (`dj-database-url` no
      hace falta — `env.db()` ya resuelve `DATABASE_URL`.)
- [x] `LOGGING` a stdout en `production.py`.
- [x] `wsgi.py`/`asgi.py` ahora asumen `settings.production` por defecto (fail-safe);
      `manage.py` sigue en development. `Procfile` creado.
- [x] Media en R2 vía `STORAGES` condicionado a `AWS_*` (variables en `.env.example`).
- [x] **Desplegado en Railway el 05-06-2026**: proyecto `meetandgig` con Postgres
      (27 migraciones + seeds aplicados), variables cargadas, dominio
      `web-production-fdd47.up.railway.app` operativo. `migrate` corre en pre-deploy
      y `collectstatic` en el startCommand (el pre-deploy es un contenedor efímero
      separado — los estáticos generados ahí se descartan).
- [ ] Pendiente de credenciales del usuario: API key de Resend (Bloque 4 — OJO:
      sin dominio propio, Resend solo envía al correo del dueño de la cuenta;
      comprar `meetandgig.cl` antes de invitar músicos reales), credenciales R2
      (media persistente) y `ANTHROPIC_API_KEY` (opcional). Instalar la GitHub App
      de Railway para auto-deploy en cada push (hoy se despliega con `railway up`).

**Mejoras medianas:** ✅ *Resueltas el 05-06-2026:*
- [x] Límite de 25 megapíxeles en `validate_image_file` (anti decompression bomb) y
      `DATA_UPLOAD_MAX_MEMORY_SIZE` en settings.
- [x] `transaction.atomic` en `registro_view` (usuario + perfil se crean juntos o nada).
- [x] `/perfil/<username>/` respeta `Portafolio.activo` (404 al público si está
      despublicado; el propietario sigue viéndolo).
- [x] Slug de `Portafolio` con reintento ante IntegrityError (race con multi-worker).
- [x] Enlaces muertos del dropdown ("Configuración", "Mi Perfil" del else) comentados.
- [x] `PortafolioUnificadoView` con `select_related`/`prefetch_related` y keywords desde
      las relaciones prefeteadas; sin doble `get_object()`.

**Bugs en módulos DIFERIDOS — corregir AL REACTIVARLOS, no antes:**
- [ ] `views.py` ~1217: llama `enviar_notificacion_resultado_postulacion(postulacion=…,
      aceptada=…)` pero la función solo acepta `postulacion` → TypeError 500 al
      aceptar/rechazar postulaciones.
- [ ] `marcar_invitaciones_expiradas.py` y `admin.py:232`: usan `nombre_empresa`; el
      campo real de `PerfilEmpleador` es `nombre_organizacion` → AttributeError.
- [ ] `admin.py`: la acción "Reabrir ofertas" asigna estado `'abierta'`, que no existe
      en los choices → las ofertas quedan invisibles para los listados.
- [ ] Emails de postulaciones/invitaciones con URLs hardcodeadas `http://127.0.0.1:8000`.
- [ ] `Testimonio.token_solicitud` sin `unique=True` (links de aprobación de referencias).

---

## 10. Validación: no lanzar y esperar

Un marketplace es una fiesta: si llegas y no hay nadie, te vas (recordar a Sonnar). El día
del lanzamiento habrá cero usuarios. La Fase 2 NO es "lanzo y espero": es **arranque manual
de liquidez** — conseguir a mano los primeros 10–15 músicos y cargar sus portafolios, y
golpear puertas de 3–4 locales concretos. Ese empujón inicial separa el marketplace que
arranca del que muere vacío.

---

## 11. Decisiones / temas abiertos

- ¿Monetización principal: comisión (demanda) o visibilidad (oferta)? (Inclinación: comisión.)
- Nombre del perfil de contratista (algo más "artístico" que "empleador").
- Diseño en detalle de las cuentas de contratista (campos, diferencias vs. visitante/músico,
  conexión con `ContactoMusico`). ← próximo tema de diseño.
- "Productora" puede estar en los dos lados (ofrece servicios y contrata). Definir al diseñar tipos.
- Consulta legal fintech antes de construir pagos (hito de mediano plazo).
- Rediseño de frontend (landing inspirada en Behance/Dribbble) vía Google Stitch + MCP.
- Compra de dominio `meetandgig.cl` (investigar costo).
