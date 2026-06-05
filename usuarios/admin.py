from django.contrib import admin
from .models import (
    Usuario, PerfilEmpleador, PerfilMusico, Portafolio,
    Instrumento, Genero, NivelExperiencia, Ubicacion,
    PortafolioInstrumento, PortafolioGenero, Multimedia, Testimonio,
    OfertaLaboral, Postulacion, OfertaInstrumento, OfertaGenero,
    Invitacion, Notificacion, ContactoMusico
)


@admin.register(ContactoMusico)
class ContactoMusicoAdmin(admin.ModelAdmin):
    """El embudo de validación del proyecto, medible desde el admin."""
    list_display = ('remitente_nombre', 'musico', 'tipo_necesidad', 'estado', 'creado')
    list_filter = ('estado', 'tipo_necesidad', 'creado')
    search_fields = ('remitente_nombre', 'remitente_email', 'musico__usuario__username')
    readonly_fields = ('creado', 'visto_en', 'ip_remitente')
    date_hierarchy = 'creado'


class PerfilMusicoAdmin(admin.ModelAdmin):
    list_display = (
        'usuario', 'telefono', 'fecha_nacimiento', 
        'recibir_notificaciones_email', 'mostrar_telefono_publico'
    )
    list_filter = (
        'recibir_notificaciones_email', 'mostrar_telefono_publico'
    )
    search_fields = ('usuario__username', 'usuario__email', 'telefono', 'direccion')
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion')
    
    fieldsets = (
        ('Información del Usuario', {
            'fields': ('usuario',)
        }),
        ('Datos Personales', {
            'fields': ('telefono', 'fecha_nacimiento', 'direccion', 'contacto_emergencia')
        }),
        ('Configuraciones de Privacidad', {
            'fields': ('recibir_notificaciones_email', 'mostrar_telefono_publico')
        }),
        ('Metadatos', {
            'fields': ('fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        })
    )


# Inline admin para instrumentos del portafolio
class PortafolioInstrumentoInline(admin.TabularInline):
    model = PortafolioInstrumento
    extra = 1
    fields = ('instrumento', 'es_principal', 'nivel_dominio', 'años_experiencia', 'orden_presentacion')


# Inline admin para géneros del portafolio
class PortafolioGeneroInline(admin.TabularInline):
    model = PortafolioGenero
    extra = 1
    fields = ('genero', 'preferencia', 'años_experiencia', 'orden_presentacion')


# Inline admin para multimedia del portafolio
class MultimediaInline(admin.TabularInline):
    model = Multimedia
    extra = 1
    fields = ('titulo', 'tipo', 'archivo', 'url_externa', 'es_principal', 'orden')


# Inline admin para testimonios del portafolio
class TestimonioInline(admin.TabularInline):
    model = Testimonio
    extra = 1
    fields = ('nombre_cliente', 'empresa_evento', 'testimonio', 'puntuacion', 'verificado')


class PortafolioAdmin(admin.ModelAdmin):
    list_display = (
        'usuario', 'slug', 'nivel_experiencia', 'ubicacion', 
        'disponible_para_gigs', 'activo', 'fecha_creacion'
    )
    list_filter = (
        'nivel_experiencia', 'ubicacion', 'disponible_para_gigs', 
        'activo', 'show_email', 'show_social_links'
    )
    search_fields = ('usuario__username', 'usuario__email', 'slug', 'biografia')
    readonly_fields = ('slug', 'fecha_creacion', 'fecha_actualizacion')
    prepopulated_fields = {}
    
    inlines = [PortafolioInstrumentoInline, PortafolioGeneroInline, MultimediaInline, TestimonioInline]
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('usuario', 'slug', 'biografia')
        }),
        ('Experiencia y Formación', {
            'fields': ('nivel_experiencia', 'años_experiencia', 'formacion_musical', 'ubicacion')
        }),
        ('Enlaces y Redes Sociales', {
            'fields': (
                'website_personal', 'soundcloud_url', 'youtube_url', 
                'spotify_url', 'instagram_url', 'facebook_url', 'video_demo'
            ),
            'classes': ('collapse',)
        }),
        ('Información Comercial', {
            'fields': ('disponible_para_gigs', 'tarifa_base')
        }),
        ('Configuraciones de Visibilidad', {
            'fields': (
                'show_email', 'show_social_links', 'show_education', 
                'show_tarifa', 'show_telefono'
            ),
            'classes': ('collapse',)
        }),
        ('Metadatos', {
            'fields': ('fecha_creacion', 'fecha_actualizacion', 'activo'),
            'classes': ('collapse',)
        })
    )


class PerfilEmpleadorAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'nombre_organizacion', 'tipo_entidad', 'ubicacion')
    search_fields = ('usuario__username', 'nombre_organizacion', 'tipo_entidad')
    
    fieldsets = (
        ('Información del Usuario', {
            'fields': ('usuario',)
        }),
        ('Información de la Organización', {
            'fields': (
                'nombre_organizacion', 'tipo_entidad', 
                'ubicacion', 'contacto_alternativo'
            )
        })
    )


class UsuarioAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'tipo_usuario', 'is_active', 'date_joined')
    list_filter = ('tipo_usuario', 'is_active', 'is_staff')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    readonly_fields = ('date_joined', 'last_login')


# Register your models here.
admin.site.register(Usuario, UsuarioAdmin)
admin.site.register(PerfilEmpleador, PerfilEmpleadorAdmin)
admin.site.register(PerfilMusico, PerfilMusicoAdmin)
admin.site.register(Portafolio, PortafolioAdmin)

# Admin para catálogos normalizados
@admin.register(Instrumento)
class InstrumentoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'categoria', 'portafolios_count')
    list_filter = ('categoria',)
    search_fields = ('nombre', 'categoria')
    ordering = ('categoria', 'nombre')
    
    def portafolios_count(self, obj):
        return obj.portafolioinstrumento_set.count()
    portafolios_count.short_description = 'Portafolios'
    portafolios_count.admin_order_field = 'portafolioinstrumento__count'


@admin.register(Genero)
class GeneroAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion_corta', 'portafolios_count')
    search_fields = ('nombre', 'descripcion')
    ordering = ('nombre',)
    
    def descripcion_corta(self, obj):
        return obj.descripcion[:50] + '...' if len(obj.descripcion) > 50 else obj.descripcion
    descripcion_corta.short_description = 'Descripción'
    
    def portafolios_count(self, obj):
        return obj.portafoliogenero_set.count()
    portafolios_count.short_description = 'Portafolios'


@admin.register(NivelExperiencia)
class NivelExperienciaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion', 'años_rango', 'orden')
    list_filter = ('orden',)
    ordering = ('orden',)
    
    def años_rango(self, obj):
        if obj.años_maximos:
            return f"{obj.años_minimos}-{obj.años_maximos} años"
        return f"{obj.años_minimos}+ años"
    años_rango.short_description = 'Rango años'


@admin.register(Ubicacion)
class UbicacionAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'region', 'pais', 'activo', 'portafolios_count')
    list_filter = ('region', 'pais', 'activo')
    search_fields = ('nombre', 'region')
    ordering = ('orden', 'region', 'nombre')
    
    def portafolios_count(self, obj):
        return obj.portafolio_set.count()
    portafolios_count.short_description = 'Portafolios'

# Registrar modelos adicionales
admin.site.register(PortafolioInstrumento)
admin.site.register(PortafolioGenero)
admin.site.register(Multimedia)
admin.site.register(Testimonio)


# ADMIN PARA OFERTAS LABORALES (Sprint 3)
class OfertaInstrumentoInline(admin.TabularInline):
    model = OfertaInstrumento
    extra = 1
    fields = ('instrumento', 'es_obligatorio', 'prioridad')


class OfertaGeneroInline(admin.TabularInline):
    model = OfertaGenero
    extra = 1
    fields = ('genero', 'prioridad')


# Registrar modelos de ofertas
admin.site.register(OfertaInstrumento)
admin.site.register(OfertaGenero)


# ADMIN PARA INVITACIONES (Ticket 3.8)
@admin.register(Invitacion)
class InvitacionAdmin(admin.ModelAdmin):
    list_display = (
        'empleador', 'musico', 'oferta_laboral', 'estado', 
        'fecha_invitacion', 'fecha_expiracion', 'dias_restantes'
    )
    list_filter = (
        'estado', 'fecha_invitacion', 'empleador', 'oferta_laboral__tipo_contrato'
    )
    search_fields = (
        'musico__username', 'musico__email', 'empleador__nombre_empresa',
        'oferta_laboral__titulo', 'mensaje_invitacion'
    )
    readonly_fields = (
        'fecha_invitacion', 'fecha_respuesta', 'postulacion_creada'
    )
    
    fieldsets = (
        ('Información Principal', {
            'fields': ('oferta_laboral', 'empleador', 'musico', 'portafolio')
        }),
        ('Contenido de la Invitación', {
            'fields': ('mensaje_invitacion', 'tarifa_ofrecida')
        }),
        ('Estado y Control', {
            'fields': ('estado', 'fecha_expiracion')
        }),
        ('Respuesta del Músico', {
            'fields': ('fecha_respuesta', 'mensaje_respuesta'),
            'classes': ('collapse',)
        }),
        ('Metadatos', {
            'fields': ('fecha_invitacion', 'postulacion_creada'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'musico', 'empleador', 'oferta_laboral', 'portafolio', 'postulacion_creada'
        )
    
    def dias_restantes(self, obj):
        """Calcula días restantes para responder"""
        return obj.dias_restantes()
    dias_restantes.short_description = 'Días restantes'


# ADMIN PARA NOTIFICACIONES
@admin.register(Notificacion)
class NotificacionAdmin(admin.ModelAdmin):
    list_display = (
        'empleador', 'tipo', 'titulo', 'leida', 'fecha_creacion'
    )
    list_filter = (
        'tipo', 'leida', 'fecha_creacion'
    )
    search_fields = (
        'empleador__usuario__username', 'empleador__usuario__email', 'titulo', 'mensaje'
    )
    readonly_fields = ('fecha_creacion', 'fecha_lectura')
    
    fieldsets = (
        ('Información Principal', {
            'fields': ('empleador', 'tipo', 'titulo', 'mensaje')
        }),
        ('Enlace', {
            'fields': ('enlace',),
            'classes': ('collapse',)
        }),
        ('Estado', {
            'fields': ('leida', 'fecha_lectura')
        }),
        ('Metadatos', {
            'fields': ('fecha_creacion',),
            'classes': ('collapse',)
        })
    )

    actions = ['marcar_como_leidas', 'marcar_como_no_leidas']

    def marcar_como_leidas(self, request, queryset):
        """Acción para marcar notificaciones como leídas"""
        from django.utils import timezone
        updated = queryset.update(leida=True, fecha_lectura=timezone.now())
        self.message_user(request, f'{updated} notificaciones marcadas como leídas.')
    marcar_como_leidas.short_description = 'Marcar como leídas'

    def marcar_como_no_leidas(self, request, queryset):
        """Acción para marcar notificaciones como no leídas"""
        updated = queryset.update(leida=False, fecha_lectura=None)
        self.message_user(request, f'{updated} notificaciones marcadas como no leídas.')
    marcar_como_no_leidas.short_description = 'Marcar como no leídas'


# ===================================================================
# ADMIN MEJORADO PARA MODERACIÓN - SPRINT 4 TICKET 4.8
# ===================================================================

from django.utils.html import format_html
from django.urls import reverse
from django.contrib.admin import SimpleListFilter


class EstadoPostulacionFilter(SimpleListFilter):
    """Filtro personalizado para estados de postulación"""
    title = 'Estado de Postulación'
    parameter_name = 'estado'

    def lookups(self, request, model_admin):
        return (
            ('pendiente', 'Pendientes'),
            ('en_revision', 'En Revisión'),
            ('aceptada', 'Aceptadas'),
            ('rechazada', 'Rechazadas'),
            ('cancelada', 'Canceladas'),
            ('sin_decision', 'Sin Decisión (Pendientes + En Revisión)'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'sin_decision':
            return queryset.filter(estado__in=['pendiente', 'en_revision'])
        elif self.value():
            return queryset.filter(estado=self.value())
        return queryset


@admin.register(Postulacion)
class PostulacionAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'musico_link', 'oferta_titulo', 'empleador_link', 
        'estado_colored', 'fecha_postulacion', 'tiene_notas', 'acciones_rapidas'
    )
    list_filter = (
        EstadoPostulacionFilter, 'fecha_postulacion', 
        'oferta_laboral__ubicacion', 'oferta_laboral__tipo_contrato'
    )
    search_fields = (
        'musico__username', 'musico__email', 'musico__first_name', 'musico__last_name',
        'oferta_laboral__titulo', 'oferta_laboral__empleador__usuario__email'
    )
    readonly_fields = ('fecha_postulacion',)
    raw_id_fields = ('musico', 'oferta_laboral')
    
    fieldsets = (
        ('Información Principal', {
            'fields': ('musico', 'oferta_laboral', 'estado', 'fecha_postulacion')
        }),
        ('Detalles de la Postulación', {
            'fields': ('mensaje_personalizado', 'tarifa_propuesta')
        }),
        ('Gestión del Empleador', {
            'fields': ('notas_empleador',),
            'classes': ('collapse',)
        })
    )

    actions = [
        'aceptar_postulaciones', 'rechazar_postulaciones', 
        'marcar_en_revision', 'exportar_postulaciones'
    ]

    def musico_link(self, obj):
        """Link al perfil del músico"""
        url = reverse('admin:usuarios_usuario_change', args=[obj.musico.id])
        return format_html('<a href="{}">{}</a>', url, obj.musico.get_full_name())
    musico_link.short_description = 'Músico'

    def empleador_link(self, obj):
        """Link al perfil del empleador"""
        url = reverse('admin:usuarios_usuario_change', args=[obj.oferta_laboral.empleador.usuario.id])
        return format_html('<a href="{}">{}</a>', url, obj.oferta_laboral.empleador.usuario.get_full_name())
    empleador_link.short_description = 'Empleador'

    def oferta_titulo(self, obj):
        """Título de la oferta con link"""
        url = reverse('admin:usuarios_ofertalaboral_change', args=[obj.oferta_laboral.id])
        return format_html('<a href="{}">{}</a>', url, obj.oferta_laboral.titulo[:50])
    oferta_titulo.short_description = 'Oferta'

    def estado_colored(self, obj):
        """Estado con colores"""
        colors = {
            'pendiente': '#ffc107',
            'en_revision': '#17a2b8',
            'aceptada': '#28a745',
            'rechazada': '#dc3545',
            'cancelada': '#6c757d'
        }
        color = colors.get(obj.estado, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_estado_display()
        )
    estado_colored.short_description = 'Estado'

    def tiene_notas(self, obj):
        """Indica si tiene comentarios del empleador"""
        if obj.notas_empleador:
            return format_html('✅ Sí')
        return format_html('❌ No')
    tiene_notas.short_description = 'Comentarios'

    def acciones_rapidas(self, obj):
        """Estado actual y enlace a edición"""
        if obj.estado in ['pendiente', 'en_revision']:
            edit_url = f'/admin/usuarios/postulacion/{obj.id}/change/'
            return format_html(
                '<span style="color: orange;">⏳ {}</span> | '
                '<a class="button" href="{}">✏️ Editar</a>',
                obj.get_estado_display(),
                edit_url
            )
        elif obj.estado == 'aceptada':
            return format_html('<span style="color: green;">✅ Aceptada</span>')
        elif obj.estado == 'rechazada':
            return format_html('<span style="color: red;">❌ Rechazada</span>')
        return format_html('✓ Procesada')
    acciones_rapidas.short_description = 'Estado y Acciones'

    def aceptar_postulaciones(self, request, queryset):
        """Acción para aceptar postulaciones en lote"""
        count = 0
        for postulacion in queryset:
            if postulacion.estado in ['pendiente', 'en_revision']:
                postulacion.estado = 'aceptada'
                postulacion.save()
                # Enviar notificación
                from usuarios.views import enviar_notificacion_resultado_postulacion
                try:
                    enviar_notificacion_resultado_postulacion(postulacion)
                except Exception as e:
                    pass  # Continuar aunque falle el email
                count += 1
        
        self.message_user(request, f'{count} postulaciones aceptadas y notificadas.')
    aceptar_postulaciones.short_description = 'Aceptar postulaciones seleccionadas'

    def rechazar_postulaciones(self, request, queryset):
        """Acción para rechazar postulaciones en lote"""
        count = 0
        for postulacion in queryset:
            if postulacion.estado in ['pendiente', 'en_revision']:
                postulacion.estado = 'rechazada'
                postulacion.save()
                # Enviar notificación
                from usuarios.views import enviar_notificacion_resultado_postulacion
                try:
                    enviar_notificacion_resultado_postulacion(postulacion)
                except Exception as e:
                    pass  # Continuar aunque falle el email
                count += 1
        
        self.message_user(request, f'{count} postulaciones rechazadas y notificadas.')
    rechazar_postulaciones.short_description = 'Rechazar postulaciones seleccionadas'

    def marcar_en_revision(self, request, queryset):
        """Acción para marcar como en revisión"""
        updated = queryset.update(estado='en_revision')
        self.message_user(request, f'{updated} postulaciones marcadas como en revisión.')
    marcar_en_revision.short_description = 'Marcar como en revisión'

    def exportar_postulaciones(self, request, queryset):
        """Exportar postulaciones a CSV"""
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="postulaciones.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'ID', 'Músico', 'Email Músico', 'Oferta', 'Empleador', 
            'Estado', 'Fecha Postulación', 'Tiene Comentarios'
        ])
        
        for postulacion in queryset:
            writer.writerow([
                postulacion.id,
                postulacion.musico.get_full_name(),
                postulacion.musico.email,
                postulacion.oferta_laboral.titulo,
                postulacion.oferta_laboral.empleador.usuario.get_full_name(),
                postulacion.get_estado_display(),
                postulacion.fecha_postulacion.strftime('%Y-%m-%d %H:%M'),
                'Sí' if postulacion.notas_empleador else 'No'
            ])
        
        return response
    exportar_postulaciones.short_description = 'Exportar a CSV'


# ADMIN MEJORADO PARA OFERTAS LABORALES
@admin.register(OfertaLaboral)
class OfertaLaboralAdmin(admin.ModelAdmin):
    list_display = (
        'titulo', 'empleador_link', 'fecha_evento', 'ubicacion', 
        'estado_colored', 'postulaciones_count', 'presupuesto_range', 
        'fecha_creacion'
    )
    list_filter = (
        'estado', 'tipo_contrato', 'ubicacion', 'fecha_evento', 'fecha_creacion'
    )
    search_fields = (
        'titulo', 'descripcion', 'empleador__usuario__email', 
        'empleador__usuario__first_name', 'empleador__usuario__last_name'
    )
    readonly_fields = ('slug', 'fecha_creacion', 'fecha_actualizacion')
    
    fieldsets = (
        ('Información Principal', {
            'fields': ('empleador', 'titulo', 'slug', 'descripcion')
        }),
        ('Detalles del Evento', {
            'fields': ('fecha_evento', 'duracion_estimada', 'ubicacion', 'direccion_evento')
        }),
        ('Términos Comerciales', {
            'fields': (
                'tipo_contrato', 'presupuesto_minimo', 'presupuesto_maximo',
                'cupos_disponibles', 'incluye_transporte', 'incluye_hospedaje',
                'incluye_alimentacion'
            )
        }),
        ('Estado y Configuración', {
            'fields': ('estado', 'fecha_limite_postulacion')
        }),
        ('Metadatos', {
            'fields': ('fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        })
    )

    actions = ['cerrar_ofertas', 'reabrir_ofertas', 'exportar_ofertas']

    def empleador_link(self, obj):
        """Link al perfil del empleador"""
        url = reverse('admin:usuarios_usuario_change', args=[obj.empleador.usuario.id])
        return format_html('<a href="{}">{}</a>', url, obj.empleador.usuario.get_full_name())
    empleador_link.short_description = 'Empleador'

    def estado_colored(self, obj):
        """Estado con colores"""
        colors = {
            'abierta': '#28a745',
            'cerrada': '#dc3545',
            'pausada': '#ffc107'
        }
        color = colors.get(obj.estado, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_estado_display()
        )
    estado_colored.short_description = 'Estado'

    def postulaciones_count(self, obj):
        """Cantidad de postulaciones"""
        count = obj.postulaciones.count()
        if count > 0:
            url = f'/admin/usuarios/postulacion/?oferta_laboral__id__exact={obj.id}'
            return format_html('<a href="{}">{} postulaciones</a>', url, count)
        return '0 postulaciones'
    postulaciones_count.short_description = 'Postulaciones'

    def presupuesto_range(self, obj):
        """Rango de presupuesto"""
        if obj.presupuesto_minimo and obj.presupuesto_maximo:
            return f'${obj.presupuesto_minimo:,} - ${obj.presupuesto_maximo:,}'
        elif obj.presupuesto_minimo:
            return f'${obj.presupuesto_minimo:,}+'
        return 'No especificado'
    presupuesto_range.short_description = 'Presupuesto'

    def cerrar_ofertas(self, request, queryset):
        """Cerrar ofertas seleccionadas"""
        updated = queryset.update(estado='cerrada')
        self.message_user(request, f'{updated} ofertas cerradas.')
    cerrar_ofertas.short_description = 'Cerrar ofertas seleccionadas'

    def reabrir_ofertas(self, request, queryset):
        """Reabrir ofertas seleccionadas"""
        updated = queryset.update(estado='abierta')
        self.message_user(request, f'{updated} ofertas reabiertas.')
    reabrir_ofertas.short_description = 'Reabrir ofertas seleccionadas'

    def exportar_ofertas(self, request, queryset):
        """Exportar ofertas a CSV"""
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="ofertas_laborales.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'ID', 'Título', 'Empleador', 'Fecha Evento', 'Ubicación', 
            'Estado', 'Postulaciones', 'Presupuesto Min', 'Presupuesto Max'
        ])
        
        for oferta in queryset:
            writer.writerow([
                oferta.id,
                oferta.titulo,
                oferta.empleador.usuario.get_full_name(),
                oferta.fecha_evento.strftime('%Y-%m-%d %H:%M'),
                str(oferta.ubicacion),
                oferta.get_estado_display(),
                oferta.postulaciones.count(),
                oferta.presupuesto_minimo or '',
                oferta.presupuesto_maximo or ''
            ])
        
        return response
    exportar_ofertas.short_description = 'Exportar a CSV'
