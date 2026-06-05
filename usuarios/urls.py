from django.urls import path
from . import views

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("registro/", views.registro_view, name="registro"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("recuperar-password/", views.recuperar_password_view, name="recuperar_password"),
    path("cambiar-password/<uidb64>/<token>/", views.cambiar_password_view, name="cambiar_password"),
    path("perfil/musico/editar/", views.editar_perfil_musico, name="editar_perfil_musico"),
    path("perfil/musico/", views.ver_mi_perfil, name="ver_mi_perfil"),
    # === DIFERIDO v1 (pivote a vitrina) — perfil de empleador ===
    # Reactivar descomentando. Ver CLAUDE.md (SCOPE v1).
    # path('perfil-empleador/', views.perfil_empleador_view, name='perfil_empleador'),
    # path('perfil-empleador/crear/', views.CrearPerfilEmpleadorView.as_view(), name='crear_perfil_empleador'),
    # path('perfil-empleador/editar/', views.EditarPerfilEmpleadorView.as_view(), name='editar_perfil_empleador'),
    # === FIN DIFERIDO v1 ===
    
    # URLs del portafolio
    path('portafolio/musico/', views.ver_mi_portafolio, name='ver_mi_portafolio'),
    path('portafolio/musico/crear/', views.editar_portafolio_musico, name='crear_portafolio_musico'),
    path('portafolio/musico/editar/', views.editar_portafolio_musico, name='editar_portafolio_musico'),
    
    # URL unificada del portafolio (público + privado)
    path('portafolio/<slug:slug>/', views.PortafolioUnificadoView.as_view(), name='ver_portafolio'),
    path('portafolio/<slug:slug>/', views.PortafolioUnificadoView.as_view(), name='portafolio_publico'),
    
    # URLs del perfil público
    path('perfil/<str:username>/', views.ver_perfil_musico, name='ver_perfil_musico'),
    
    # URLs de búsqueda (Ticket 2.8)
    path('buscar/', views.buscar_portafolios, name='buscar_portafolios'),
    path('musicos/', views.buscar_portafolios, name='listar_portafolios'),
    
    # === DIFERIDO v1 (pivote a vitrina) — ofertas, postulaciones, notificaciones, ===
    # === invitaciones y referencias. Reactivar descomentando. Ver CLAUDE.md (SCOPE v1). ===
    #
    # URLs de ofertas laborales públicas (Ticket 3.2)
    # path('ofertas/', views.buscar_ofertas_view, name='buscar_ofertas'),
    # path('trabajos/', views.buscar_ofertas_view, name='listar_ofertas'),
    #
    # URLs de ofertas laborales privadas (Sprint 3)
    # path('ofertas/nueva/', views.crear_oferta_laboral_view, name='crear_oferta_laboral'),
    # path('ofertas/mis-ofertas/', views.ver_mis_ofertas_view, name='ver_mis_ofertas'),
    # path('ofertas/<slug:slug>/', views.detalle_oferta_view, name='detalle_oferta'),
    # path('ofertas/<slug:slug>/editar/', views.editar_oferta_view, name='editar_oferta'),
    # path('ofertas/<slug:slug>/publicar/', views.publicar_oferta_view, name='publicar_oferta'),
    # path('ofertas/<slug:slug>/cerrar/', views.cerrar_oferta_view, name='cerrar_oferta'),
    # path('ofertas/<slug:slug>/reabrir/', views.reabrir_oferta_view, name='reabrir_oferta'),
    # path('ofertas/<slug:slug>/postular/', views.postular_oferta_view, name='postular_oferta'),
    # path('ofertas/<slug:slug>/postulaciones/', views.gestionar_postulaciones_view, name='gestionar_postulaciones'),
    # path('ofertas/<slug:slug>/postulaciones/<int:postulacion_id>/', views.procesar_postulacion_view, name='procesar_postulacion'),
    #
    # URLs de postulaciones para músicos (Ticket 3.7 FASE 3)
    # path('mis-postulaciones/', views.mis_postulaciones_view, name='mis_postulaciones'),
    # path('postulaciones/<int:postulacion_id>/cancelar/', views.cancelar_postulacion_view, name='cancelar_postulacion'),
    #
    # URLs de notificaciones para empleadores (Ticket 3.7 FASE 4)
    # path('notificaciones/', views.notificaciones_empleador_view, name='notificaciones_empleador'),
    # path('notificaciones/<int:notificacion_id>/marcar-leida/', views.marcar_notificacion_leida_view, name='marcar_notificacion_leida'),
    #
    # URLs de invitaciones directas (Ticket 3.8 FASE 2)
    # path('invitar/<slug:portafolio_slug>/', views.enviar_invitacion_view, name='enviar_invitacion'),
    # path('mis-invitaciones/', views.mis_invitaciones_enviadas_view, name='mis_invitaciones_enviadas'),
    # path('invitaciones/<int:invitacion_id>/cancelar/', views.cancelar_invitacion_view, name='cancelar_invitacion'),
    #
    # URLs de invitaciones para músicos (Ticket 3.8 FASE 3)
    # path('invitaciones-recibidas/', views.mis_invitaciones_recibidas_view, name='mis_invitaciones_recibidas'),
    # path('invitaciones/<int:invitacion_id>/responder/', views.responder_invitacion_view, name='responder_invitacion'),
    #
    # URLs de referencias laborales (Ticket 4.1)
    # path('referencias/solicitar/<int:portafolio_id>/', views.solicitar_referencia, name='solicitar_referencia'),
    # path('referencias/responder/<str:token>/', views.responder_referencia, name='responder_referencia'),
    # path('referencias/gestionar/', views.gestionar_referencias, name='gestionar_referencias'),
    # path('referencias/agregar-testimonio/', views.agregar_testimonio_directo, name='agregar_testimonio_directo'),
    # path('referencias/<int:testimonio_id>/aceptar/', views.aceptar_referencia, name='aceptar_referencia'),
    # path('referencias/<int:testimonio_id>/rechazar/', views.rechazar_referencia, name='rechazar_referencia'),
    # path('referencias/<int:testimonio_id>/ocultar/', views.ocultar_referencia, name='ocultar_referencia'),
    # path('referencias/<int:testimonio_id>/eliminar/', views.eliminar_referencia, name='eliminar_referencia'),
    # === FIN DIFERIDO v1 ===
]
