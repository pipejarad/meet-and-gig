# CLAUDE.md — Meet & Gig

Contexto para trabajar en este repositorio. Léelo antes de proponer o hacer cambios.

> Lo que NO está aquí (stack, versiones, modelos, endpoints, estructura de carpetas) lo
> descubres leyendo el código. Este archivo contiene solo lo que el código **no te puede
> decir**: la intención, el scope vigente, las reglas de trabajo y las decisiones que aún
> no están implementadas.

---

## Qué es y qué objetivo persigue ahora

Plataforma que conecta músicos independientes chilenos con quienes los contratan. Nace de
combatir la informalidad laboral en la música. Dos objetivos: que sea pieza de portafolio
profesional y validar la idea con usuarios reales.

**Prioridad: velocidad a producción por sobre perfección arquitectónica.**

---

## ⚠️ SCOPE v1 — LÉELO PRIMERO

El código fue construido como un marketplace de DOS lados (músicos y empleadores). **La v1
pivotó a una VITRINA de UN solo lado: solo músicos.** No te guíes por lo que sugiere el
código existente (te haría asumir un marketplace de dos lados); guíate por esto:

**ACTIVO en v1 — trabaja aquí:**
- Autenticación.
- Perfil + portafolio público del músico (incluye variantes: solista, banda, proyecto, productora).
- Contacto mediado de visitantes hacia músicos (construido — ver reglas más abajo).

**DIFERIDO pero presente en el código — NO construir sobre esto, NO borrarlo:**
- Perfil de empleador.
- Ofertas laborales.
- Postulaciones e invitaciones.
- Referencias laborales (vuelven en el largo plazo).
- El sistema de notificaciones existente está ligado a postulaciones/invitaciones, así que
  queda dormido. En v1 la **única notificación activa** es el email al músico cuando recibe
  un contacto.

**Regla clave: OCULTAR, NO BORRAR.** Los módulos diferidos se sacan de la navegación y la
UI, pero se conservan modelos y migraciones intactos. Vuelven en el mediano/largo plazo.

---

## Reglas de trabajo

- **No refactorices código que funciona si no te lo pido.** El refactor está planificado
  para *después* de validar con usuarios (Fase 3), no ahora. No persigas perfección
  arquitectónica antes de tener tracción.
- Antes de agregar cualquier feature, confirma que cae dentro del SCOPE v1 de arriba. Si
  no estás seguro, pregunta antes de construir.
- Secretos (`SECRET_KEY`, credenciales, API keys) **siempre** en variables de entorno,
  nunca en el repo.
- La fuente de verdad del plan completo (con razonamiento y esqueletos de código) es
  `ROADMAP.md` en la raíz. Si algo aquí contradice tu lectura del código, asume que el
  código está desactualizado respecto a la intención y pregúntame antes de avanzar.

---

## Contacto mediado (construido) — reglas que deben mantenerse

Visitantes **no autenticados** contactan a músicos vía formulario público
(`/portafolio/<slug>/contactar/`); el músico gestiona el embudo en "Mis contactos".
Principios vigentes — no romperlos al evolucionar la feature:
- **"Mediado = medido, no controlado":** captura el dato y mantén baja la fricción. NO
  construyas mensajería interna compleja todavía. El email de aviso lleva Reply-To del
  visitante para que el músico responda por correo directo.
- El email del músico **NUNCA** se expone en el HTML público; el formulario hace POST a la
  plataforma y el correo se maneja del lado del servidor.
- FK de usuario **nullable** (`remitente_usuario`): es la bisagra para vincular futuras
  cuentas de contratista sin reescribir el modelo.
- Campo `estado` (enviado / visto / respondido / convertido) mide el embudo; el
  `convertido` lo marca el músico ("¿se transformó en una pega?") y **no debe
  automatizarse**: es el instrumento de validación del proyecto.
- Anti-spam mínimo: honeypot + límite por IP (5/hora). Captcha solo si aparece spam real.

---

## Diseño nuevo a construir (aún NO está en el código)

### Asistente de IA del portafolio (corto plazo / v1.5)
Genera la biografía del músico a partir de un formulario de preguntas predefinidas.
- La IA produce un **borrador**; el músico **edita y aprueba**. Nunca autopublicar.
- Formulario estructurado (no chat libre). Instruir al modelo a **no inventar datos**.
- Modelo económico, API key en variable de entorno, límite de generaciones/día por músico.
- Construir como servicio aislado (`generar_bio(respuestas, contexto_material)`) para
  poder cambiar la fuente o el modelo después sin tocar la UI.

→ Esqueleto del servicio y el prompt en `ROADMAP.md` §8.

---

## Contexto de despliegue (Railway)

- PostgreSQL como add-on (inyecta `DATABASE_URL`; usar `dj-database-url`).
- **Filesystem efímero:** los archivos subidos (media del portafolio) NO persisten entre
  deploys. La media va a almacenamiento externo S3-compatible (Cloudflare R2) vía
  `django-storages`. No asumas que el disco local guarda nada permanente.
- Estáticos → **WhiteNoise** (no montar S3 para esto).
- Gunicorn como servidor de aplicación. HTTPS lo da Railway en su subdominio.

---

## Restricciones duras (no negociables)

- **Nunca construir custodia de dinero propia.** Si en el futuro se implementan pagos, van
  por una pasarela licenciada con *split payment* (Mercado Pago Marketplace / Stripe
  Connect / Kushki / Payku). El dinero no debe pasar por cuentas de la plataforma (riesgo
  regulatorio: Ley Fintech 21.521 / CMF). Es un tema futuro, pero no implementes nada que
  lo contradiga.
- La plataforma es **intermediario, no empleador ni parte del contrato.** No agregues
  lógica que posicione a la plataforma como empleador.

---

## Matriz de impacto (si tocas X, revisa Y)

> Le dice al agente (y al hook anti-drift) qué documentación revisar según qué
> parte del código se tocó. El hook bloquea `git push` solo en lo más sensible
> (ver `scripts/check-docs-before-push.sh`); esta tabla es la guía completa.

| Si tocaste…                                       | Revisa actualizar…                                           |
|---------------------------------------------------|--------------------------------------------------------------|
| `*/models.py`, `*/migrations/`                    | `docs/data-model.md` (mapa de modelos activo / diferido)     |
| `*/views.py`, `*/urls.py`                         | flujos en `ROADMAP.md`                                       |
| Servicio nuevo (`generar_bio`, email de contacto) | `ROADMAP.md` (§5 contacto mediado, §8 asistente IA)          |
| Cliente externo (R2, pasarela de pago, API IA)    | sección Despliegue / Restricciones duras de este `CLAUDE.md` |
| Nueva variable de entorno                         | `.env.example` (y cargarla en Railway al desplegar)          |
| Bug encontrado o arreglado                        | `ROADMAP.md` §9 (pendientes de la auditoría técnica)         |
