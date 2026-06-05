from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, Http404
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.urls import reverse, reverse_lazy
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, UpdateView, DetailView
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.utils import timezone
from .forms import (
    RegistroForm, LoginForm, RecuperarPasswordForm, CambiarPasswordForm, 
    PerfilMusicoForm, PerfilEmpleadorForm, PortafolioForm, CrearOfertaLaboralForm,
    PostulacionForm, SolicitudReferenciaForm, ResponderReferenciaForm, TestimonioDirectoForm
)
from .models import Usuario, PerfilMusico, PerfilEmpleador, Portafolio, OfertaLaboral, Postulacion, Notificacion, Invitacion, Testimonio


def inicio(request):
    portafolios_destacados = Portafolio.objects.filter(
        activo=True,
        disponible_para_gigs=True
    ).select_related('usuario', 'ubicacion').prefetch_related(
        'portafolio_instrumentos__instrumento',
        'portafolio_generos__genero'
    ).order_by('-fecha_actualizacion')[:6]
    
    stats = {
        'total_musicos': Usuario.objects.filter(tipo_usuario='musico').count(),
        'total_empleadores': Usuario.objects.filter(tipo_usuario='empleador').count(),
        'total_portafolios': Portafolio.objects.filter(activo=True).count(),
        'total_ofertas': OfertaLaboral.objects.filter(estado='publicada').count(),
        'total_usuarios': Usuario.objects.count(),
    }
    
    context = {
        'portafolios_destacados': portafolios_destacados,
        'stats': stats,
    }
    
    return render(request, 'usuarios/inicio.html', context)


def registro_view(request):
    if request.user.is_authenticated:
        return redirect('inicio')
        
    if request.method == 'POST':
        form = RegistroForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                user = form.save()
                # En v1 todo registro es músico; crear su perfil de inmediato para
                # que el perfil público exista desde el primer día (la vitrina).
                PerfilMusico.objects.get_or_create(usuario=user)
                messages.success(
                    request,
                    f'¡Bienvenido {user.username}! Tu cuenta ha sido creada exitosamente.'
                )
                # Especificar el backend para el login
                login(request, user, backend='usuarios.backends.EmailBackend')
                return _redirect_by_user_type(user)
            except Exception as e:
                messages.error(request, 'Ocurrió un error al crear la cuenta. Intenta nuevamente.')
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = RegistroForm()
    
    return render(request, 'usuarios/registro.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('inicio')
        
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'¡Bienvenido de vuelta, {user.username}!')
            return _redirect_by_user_type(user)
        else:
            messages.error(request, 'Email o contraseña incorrectos.')
    else:
        form = LoginForm()
    
    return render(request, 'usuarios/login.html', {'form': form})


def logout_view(request):
    if request.user.is_authenticated:
        username = request.user.username
        logout(request)
        messages.info(request, f'Hasta luego, {username}. Has cerrado sesión correctamente.')
    return redirect('login')


def _redirect_by_user_type(user):
    """
    Función helper para redirigir usuarios según su tipo.
    Sigue el principio DRY para evitar duplicación de lógica.
    """
    if user.tipo_usuario == 'musico':
        # TODO: Implementar estas vistas en próximos tickets  
        return redirect('inicio')  # Temporal hasta crear perfil_musico_crear
    else:
        # TODO: Implementar estas vistas en próximos tickets
        return redirect('inicio')  # Temporal hasta crear perfil_empleador_crear


def recuperar_password_view(request):
    if request.user.is_authenticated:
        return redirect('inicio')
        
    if request.method == 'POST':
        form = RecuperarPasswordForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = Usuario.objects.get(email__iexact=email)
                _send_password_reset_email(request, user)
            except Usuario.DoesNotExist:
                # Respuesta idéntica exista o no la cuenta, para no revelar
                # qué emails están registrados (enumeración de usuarios).
                pass
            messages.success(
                request,
                'Si el email está registrado, te enviamos un enlace de recuperación. '
                'Revisa tu bandeja de entrada.'
            )
            return redirect('login')
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = RecuperarPasswordForm()
    
    return render(request, 'usuarios/recuperar_password.html', {'form': form})


def cambiar_password_view(request, uidb64, token):
    if request.user.is_authenticated:
        return redirect('inicio')
    
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = Usuario.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, Usuario.DoesNotExist):
        user = None

    if user is None or not default_token_generator.check_token(user, token):
        messages.error(request, 'El enlace de recuperación es inválido o ha expirado.')
        return redirect('recuperar_password')

    if request.method == 'POST':
        form = CambiarPasswordForm(user, request.POST)
        if form.is_valid():
            form.save()
            messages.success(
                request, 
                'Tu contraseña ha sido cambiada exitosamente. Ya puedes iniciar sesión.'
            )
            return redirect('login')
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = CambiarPasswordForm(user)

    return render(request, 'usuarios/cambiar_password.html', {'form': form})


def _send_password_reset_email(request, user):
    """
    Función helper para enviar email de recuperación de contraseña.
    Mantiene la lógica de envío centralizada siguiendo DRY.
    """
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    
    reset_url = request.build_absolute_uri(
        reverse('cambiar_password', kwargs={'uidb64': uid, 'token': token})
    )
    
    subject = 'Recuperación de contraseña - Meet & Gig'
    message = f"""
Hola {user.username},

Has solicitado recuperar tu contraseña en Meet & Gig.

Haz clic en el siguiente enlace para cambiar tu contraseña:
{reset_url}

Si no solicitaste este cambio, puedes ignorar este email.

Saludos,
El equipo de Meet & Gig
"""
    
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )


@login_required
def editar_perfil_musico(request):
    if request.user.tipo_usuario != 'musico':
        messages.error(request, 'Solo los músicos pueden acceder a esta sección.')
        return redirect('inicio')
    
    try:
        perfil = request.user.perfil_musico
    except PerfilMusico.DoesNotExist:
        perfil = None
    
    if request.method == 'POST':
        form = PerfilMusicoForm(request.POST, request.FILES, instance=perfil, usuario=request.user)
        if form.is_valid():
            perfil = form.save()
            
            if form.cleaned_data.get('foto_perfil'):
                messages.success(request, '✅ Perfil e imagen actualizados exitosamente.')
            else:
                messages.success(request, '✅ Perfil actualizado exitosamente.')
            
            return redirect('editar_perfil_musico')
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = PerfilMusicoForm(instance=perfil, usuario=request.user)
    
    context = {
        'form': form,
        'perfil': perfil,
        'usuario': request.user,
        'es_nuevo_perfil': perfil is None
    }
    
    return render(request, 'usuarios/editar_perfil_musico.html', context)


@login_required 
def ver_mi_perfil(request):
    if request.user.tipo_usuario != 'musico':
        messages.error(request, 'Solo los músicos tienen perfil público.')
        return redirect('inicio')
    
    try:
        perfil = request.user.perfil_musico
    except PerfilMusico.DoesNotExist:
        messages.info(
            request, 
            'Aún no has creado tu perfil de músico. ¡Complétalo para que otros puedan encontrarte!'
        )
        return redirect('editar_perfil_musico')
    
    context = {
        'perfil': perfil,
        'usuario': request.user,
        'es_mi_perfil': True
    }
    
    return render(request, 'usuarios/ver_perfil_musico.html', context)


class EmpleadorRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        if request.user.tipo_usuario != 'empleador':
            raise PermissionDenied("Solo los empleadores pueden acceder a esta página.")
        
        return super().dispatch(request, *args, **kwargs)


class CrearPerfilEmpleadorView(LoginRequiredMixin, EmpleadorRequiredMixin, CreateView):
    model = PerfilEmpleador
    form_class = PerfilEmpleadorForm
    template_name = 'usuarios/crear_perfil_empleador.html'
    success_url = reverse_lazy('perfil_empleador')

    def dispatch(self, request, *args, **kwargs):
        if hasattr(request.user, 'perfil_empleador'):
            return redirect('editar_perfil_empleador')
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.usuario = self.request.user
        messages.success(self.request, 'Perfil de empleador creado exitosamente.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Crear Perfil de Empleador'
        context['boton_texto'] = 'Crear Perfil'
        return context


class EditarPerfilEmpleadorView(LoginRequiredMixin, EmpleadorRequiredMixin, UpdateView):
    model = PerfilEmpleador
    form_class = PerfilEmpleadorForm
    template_name = 'usuarios/editar_perfil_empleador.html'
    success_url = reverse_lazy('perfil_empleador')

    def get_object(self):
        return get_object_or_404(PerfilEmpleador, usuario=self.request.user)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, 'Perfil actualizado exitosamente.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Editar Perfil de Empleador'
        context['boton_texto'] = 'Actualizar Perfil'
        return context


@login_required
def perfil_empleador_view(request):
    if request.user.tipo_usuario != 'empleador':
        raise PermissionDenied("Solo los empleadores pueden ver esta página.")
    
    try:
        perfil = request.user.perfil_empleador
    except PerfilEmpleador.DoesNotExist:
        return redirect('crear_perfil_empleador')
    
    context = {
        'perfil': perfil,
        'usuario': request.user
    }
    return render(request, 'usuarios/perfil_empleador.html', context)


@login_required
def notificaciones_empleador_view(request):
    """Vista para mostrar notificaciones del empleador"""
    if request.user.tipo_usuario != 'empleador':
        messages.error(request, 'Solo los empleadores pueden ver notificaciones.')
        return redirect('inicio')
    
    try:
        perfil_empleador = request.user.perfil_empleador
    except PerfilEmpleador.DoesNotExist:
        return redirect('crear_perfil_empleador')
    
    notificaciones = perfil_empleador.notificaciones.all().select_related(
        'postulacion', 'oferta_laboral', 'postulacion__musico'
    ).order_by('-fecha_creacion')
    
    stats = {
        'total': notificaciones.count(),
        'no_leidas': notificaciones.filter(leida=False).count(),
        'canceladas': notificaciones.filter(tipo='postulacion_cancelada').count(),
    }
    
    context = {
        'notificaciones': notificaciones,
        'stats': stats,
        'titulo_pagina': 'Notificaciones'
    }
    
    return render(request, 'usuarios/notificaciones_empleador.html', context)


@login_required
def marcar_notificacion_leida_view(request, notificacion_id):
    """Vista para marcar una notificación como leída"""
    if request.user.tipo_usuario != 'empleador':
        messages.error(request, 'Solo los empleadores pueden gestionar notificaciones.')
        return redirect('inicio')
    
    notificacion = get_object_or_404(
        Notificacion, 
        id=notificacion_id, 
        empleador=request.user.perfil_empleador
    )
    
    notificacion.marcar_como_leida()
    
    return redirect('notificaciones_empleador')


# ================================================
# VISTAS DEL PORTAFOLIO MÚSICO
# ================================================

@login_required
def ver_mi_portafolio(request):
    """Vista que redirige al músico a su portafolio unificado"""
    if request.user.tipo_usuario != 'musico':
        raise PermissionDenied("Solo los músicos pueden ver esta página.")
    
    try:
        portafolio = Portafolio.objects.get(usuario=request.user)
    except Portafolio.DoesNotExist:
        # Crear portafolio básico si no existe
        from usuarios.models import NivelExperiencia, Ubicacion
        
        nivel_default = NivelExperiencia.objects.filter(nombre='Principiante').first() or NivelExperiencia.objects.first()
        ubicacion_default = Ubicacion.objects.filter(nombre='Santiago').first() or Ubicacion.objects.first()
            
        portafolio = Portafolio.objects.create(
            usuario=request.user,
            biografia='',
            años_experiencia=1,
            nivel_experiencia=nivel_default,
            ubicacion=ubicacion_default,
            disponible_para_gigs=True,
        )
        messages.success(request, 'Se ha creado tu portafolio básico. ¡Complétalo para destacar!')
    
    return redirect('ver_portafolio', slug=portafolio.slug)


@login_required
def editar_portafolio_musico(request):
    """Vista para editar el portafolio del músico"""
    if request.user.tipo_usuario != 'musico':
        raise PermissionDenied("Solo los músicos pueden editar portafolios.")
    
    try:
        portafolio = Portafolio.objects.get(usuario=request.user)
        created = False
    except Portafolio.DoesNotExist:
        # Obtener valores por defecto
        from usuarios.models import NivelExperiencia, Ubicacion
        
        nivel_default = NivelExperiencia.objects.filter(nombre='Principiante').first()
        ubicacion_default = Ubicacion.objects.filter(nombre='Santiago').first()
        
        if not nivel_default:
            nivel_default = NivelExperiencia.objects.first()
        if not ubicacion_default:
            ubicacion_default = Ubicacion.objects.first()
            
        portafolio = Portafolio.objects.create(
            usuario=request.user,
            biografia='',
            años_experiencia=1,
            nivel_experiencia=nivel_default,
            ubicacion=ubicacion_default,
            disponible_para_gigs=True,
        )
        created = True
    
    es_creacion = created or not any([
        portafolio.biografia, 
        portafolio.formacion_musical,
        portafolio.website_personal
    ])
    
    if request.method == 'POST':
        form = PortafolioForm(request.POST, instance=portafolio)
        if form.is_valid():
            form.save()
            mensaje = 'Portafolio creado exitosamente.' if es_creacion else 'Portafolio actualizado exitosamente.'
            messages.success(request, mensaje)
            return redirect('ver_mi_portafolio')
    else:
        form = PortafolioForm(instance=portafolio)
    
    titulo = 'Crear Mi Portafolio Musical' if es_creacion else 'Editar Mi Portafolio Musical'
    
    context = {
        'form': form,
        'portafolio': portafolio,
        'titulo': titulo,
        'es_creacion': es_creacion
    }
    return render(request, 'usuarios/editar_portafolio_musico.html', context)


def ver_perfil_musico(request, username):
    """Vista pública del perfil de un músico"""
    usuario = get_object_or_404(Usuario, username=username, tipo_usuario='musico')
    
    try:
        perfil = usuario.perfil_musico
    except PerfilMusico.DoesNotExist:
        raise Http404("Este músico no tiene un perfil disponible.")
    
    context = {
        'perfil': perfil,
        'usuario': usuario,
        'es_mi_perfil': request.user.is_authenticated and request.user == usuario,
        'titulo': f'Perfil de {usuario.get_full_name() or usuario.username}'
    }
    return render(request, 'usuarios/ver_perfil_musico.html', context)


def buscar_portafolios(request):
    """Vista de búsqueda y listado de portafolios musicales"""
    from django.core.paginator import Paginator
    from django.db.models import Q
    from .models import Instrumento, Genero, NivelExperiencia, Ubicacion
    
    portafolios = Portafolio.objects.filter(activo=True).select_related(
        'usuario', 'ubicacion', 'nivel_experiencia'
    ).prefetch_related(
        'portafolio_instrumentos__instrumento',
        'portafolio_generos__genero'
    )
    
    # Obtener parámetros de búsqueda
    query = request.GET.get('q', '')
    instrumento_id = request.GET.get('instrumento', '')
    genero_id = request.GET.get('genero', '')
    ubicacion_id = request.GET.get('ubicacion', '')
    nivel_id = request.GET.get('nivel_experiencia', '')
    disponible = request.GET.get('disponible', '')
    tarifa_min = request.GET.get('tarifa_min', '')
    tarifa_max = request.GET.get('tarifa_max', '')
    ordenar = request.GET.get('orden', 'recientes')
    
    # Filtros de búsqueda por texto
    if query:
        portafolios = portafolios.filter(
            Q(usuario__first_name__icontains=query) |
            Q(usuario__last_name__icontains=query) |
            Q(usuario__username__icontains=query) |
            Q(biografia__icontains=query) |
            Q(formacion_musical__icontains=query)
        )
    
    # Filtros por instrumento (M2M)
    if instrumento_id:
        portafolios = portafolios.filter(
            portafolio_instrumentos__instrumento_id=instrumento_id
        ).distinct()
    
    # Filtros por género (M2M)
    if genero_id:
        portafolios = portafolios.filter(
            portafolio_generos__genero_id=genero_id
        ).distinct()
    
    # Filtros por ubicación (FK)
    if ubicacion_id:
        portafolios = portafolios.filter(ubicacion_id=ubicacion_id)
    
    # Filtros por nivel de experiencia (FK)
    if nivel_id:
        portafolios = portafolios.filter(nivel_experiencia_id=nivel_id)
    
    # Filtro por disponibilidad
    if disponible == 'true':
        portafolios = portafolios.filter(disponible_para_gigs=True)
    
    # Filtros por rango de tarifas
    if tarifa_min:
        try:
            portafolios = portafolios.filter(tarifa_base__gte=int(tarifa_min))
        except ValueError:
            pass
    
    if tarifa_max:
        try:
            portafolios = portafolios.filter(tarifa_base__lte=int(tarifa_max))
        except ValueError:
            pass
    
    # Ordenamiento
    if ordenar == 'nombre':
        portafolios = portafolios.order_by('usuario__first_name', 'usuario__last_name')
    elif ordenar == 'experiencia':
        portafolios = portafolios.order_by('-años_experiencia')
    elif ordenar == 'tarifa_asc':
        portafolios = portafolios.filter(tarifa_base__isnull=False).order_by('tarifa_base')
    elif ordenar == 'tarifa_desc':
        portafolios = portafolios.filter(tarifa_base__isnull=False).order_by('-tarifa_base')
    else:  # 'recientes' por defecto
        portafolios = portafolios.order_by('-fecha_actualizacion')
    
    # Paginación
    paginator = Paginator(portafolios, 12)
    page_number = request.GET.get('page')
    portafolios_page = paginator.get_page(page_number)
    
    # Obtener opciones para filtros
    instrumentos = Instrumento.objects.all().order_by('nombre')
    generos = Genero.objects.all().order_by('nombre')
    ubicaciones = Ubicacion.objects.filter(activo=True).order_by('nombre')
    niveles_experiencia = NivelExperiencia.objects.all().order_by('orden')
    
    context = {
        'portafolios': portafolios_page,
        'instrumentos': instrumentos,
        'generos': generos,
        'ubicaciones': ubicaciones,
        'niveles_experiencia': niveles_experiencia,
        'filtros_aplicados': {
            'query': query,
            'instrumento_id': instrumento_id,
            'genero_id': genero_id,
            'ubicacion_id': ubicacion_id,
            'nivel_id': nivel_id,
            'disponible': disponible,
            'tarifa_min': tarifa_min,
            'tarifa_max': tarifa_max,
            'ordenar': ordenar,
        },
        'total_resultados': paginator.count,
        'titulo': 'Buscar Músicos',
    }
    
    return render(request, 'usuarios/buscar_portafolios.html', context)


class PortafolioUnificadoView(DetailView):
    model = Portafolio
    template_name = 'usuarios/portafolio_publico.html'
    slug_field = 'slug'
    context_object_name = 'portafolio'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        portafolio = self.get_object()
        
        # Detectar si el usuario es propietario del portafolio
        context['es_propietario'] = (
            self.request.user.is_authenticated and 
            self.request.user == portafolio.usuario
        )
        
        # Incluir referencias visibles (solo aprobadas y directas)
        context['referencias_visibles'] = portafolio.testimonios.filter(
            estado__in=['aprobado', 'directo'],
            activo=True
        ).order_by('-fecha_publicacion')
        
        # SEO data
        nombre_completo = portafolio.usuario.get_full_name() or portafolio.usuario.username
        context['seo_title'] = f"{nombre_completo} - Músico en Meet&Gig"
        biografia_truncada = portafolio.biografia[:160] if portafolio.biografia else "Músico profesional en Meet&Gig"
        context['seo_description'] = biografia_truncada
        context['seo_keywords'] = self._generate_keywords(portafolio)
        context['canonical_url'] = self.request.build_absolute_uri()
        
        return context
    
    def _generate_keywords(self, portafolio):
        keywords = []
        try:
            keywords.extend([inst.nombre for inst in portafolio.instrumentos.all()])
            keywords.extend([gen.nombre for gen in portafolio.generos.all()])
        except Exception:
            keywords.extend(['músico', 'música'])
            
        if portafolio.ubicacion:
            keywords.append(f"músico {portafolio.ubicacion}")
        
        keywords.extend(['meet&gig', 'portafolio musical'])
        
        return ", ".join(keywords[:10])


def buscar_ofertas_view(request):
    """Vista pública para buscar ofertas laborales (accesible a músicos)"""
    from .models import Instrumento, Genero, Ubicacion, NivelExperiencia
    
    ofertas = OfertaLaboral.objects.filter(
        estado='publicada'
    ).select_related(
        'empleador__usuario', 'ubicacion', 'nivel_experiencia_minimo'
    ).prefetch_related(
        'oferta_instrumentos__instrumento',
        'oferta_generos__genero'
    ).order_by('-fecha_publicacion')
    
    # Aplicar filtros de búsqueda (mismo patrón que buscar_portafolios)
    query = request.GET.get('q', '').strip()
    instrumentos_ids = request.GET.getlist('instrumentos')
    generos_ids = request.GET.getlist('generos')
    ubicacion_id = request.GET.get('ubicacion')
    nivel_id = request.GET.get('experiencia')
    presupuesto_min = request.GET.get('presupuesto_min')
    presupuesto_max = request.GET.get('presupuesto_max')
    fecha_evento_desde = request.GET.get('fecha_evento_desde')
    fecha_evento_hasta = request.GET.get('fecha_evento_hasta')
    fecha_publicacion_desde = request.GET.get('fecha_publicacion_desde')
    orden = request.GET.get('orden', 'fecha_desc')

    # Búsqueda por texto en título y descripción
    if query:
        ofertas = ofertas.filter(
            Q(titulo__icontains=query) | Q(descripcion__icontains=query)
        )

    # Filtros por instrumentos (M2M múltiple)
    if instrumentos_ids:
        ofertas = ofertas.filter(
            oferta_instrumentos__instrumento_id__in=instrumentos_ids
        ).distinct()

    # Filtros por géneros (M2M múltiple)
    if generos_ids:
        ofertas = ofertas.filter(
            oferta_generos__genero_id__in=generos_ids
        ).distinct()

    # Filtros por ubicación (FK)
    if ubicacion_id:
        ofertas = ofertas.filter(ubicacion_id=ubicacion_id)

    # Filtros por nivel de experiencia (FK)
    if nivel_id:
        ofertas = ofertas.filter(nivel_experiencia_minimo_id=nivel_id)
    
    # Filtros por presupuesto
    if presupuesto_min:
        try:
            ofertas = ofertas.filter(
                Q(presupuesto_minimo__gte=int(presupuesto_min)) |
                Q(presupuesto_maximo__gte=int(presupuesto_min)) |
                Q(presupuesto_a_convenir=True)
            )
        except ValueError:
            pass

    if presupuesto_max:
        try:
            ofertas = ofertas.filter(
                Q(presupuesto_maximo__lte=int(presupuesto_max)) |
                Q(presupuesto_a_convenir=True)
            )
        except ValueError:
            pass

    # Filtros por fecha del evento
    if fecha_evento_desde:
        try:
            from datetime import datetime
            fecha_desde = datetime.strptime(fecha_evento_desde, '%Y-%m-%d').date()
            ofertas = ofertas.filter(fecha_evento__date__gte=fecha_desde)
        except ValueError:
            pass

    if fecha_evento_hasta:
        try:
            from datetime import datetime
            fecha_hasta = datetime.strptime(fecha_evento_hasta, '%Y-%m-%d').date()
            ofertas = ofertas.filter(fecha_evento__date__lte=fecha_hasta)
        except ValueError:
            pass

    # Filtros por fecha de publicación
    if fecha_publicacion_desde:
        try:
            from datetime import datetime
            fecha_pub_desde = datetime.strptime(fecha_publicacion_desde, '%Y-%m-%d').date()
            ofertas = ofertas.filter(fecha_publicacion__date__gte=fecha_pub_desde)
        except ValueError:
            pass

    # Solo ofertas vigentes (fecha límite no vencida)
    ofertas = ofertas.filter(
        Q(fecha_limite_postulacion__gt=timezone.now()) |
        Q(fecha_limite_postulacion__isnull=True)
    )

    # Aplicar ordenamiento
    if orden == 'fecha_desc':
        ofertas = ofertas.order_by('-fecha_publicacion')
    elif orden == 'fecha_asc':
        ofertas = ofertas.order_by('fecha_publicacion')
    elif orden == 'presupuesto_desc':
        ofertas = ofertas.order_by('-presupuesto_maximo', '-presupuesto_minimo')
    elif orden == 'presupuesto_asc':
        ofertas = ofertas.order_by('presupuesto_minimo', 'presupuesto_maximo')
    elif orden == 'evento_desc':
        ofertas = ofertas.order_by('-fecha_evento')
    elif orden == 'evento_asc':
        ofertas = ofertas.order_by('fecha_evento')
    else:
        ofertas = ofertas.order_by('-fecha_publicacion')
    
    # Catálogos para filtros
    instrumentos = Instrumento.objects.all().order_by('categoria', 'nombre')
    generos = Genero.objects.all().order_by('nombre')
    ubicaciones = Ubicacion.objects.filter(activo=True).order_by('region', 'nombre')
    niveles = NivelExperiencia.objects.all().order_by('orden')
    
    context = {
        'ofertas': ofertas,
        'instrumentos': instrumentos,
        'generos': generos,
        'ubicaciones': ubicaciones,
        'niveles': niveles,
        'query': query,
        'filtros_activos': {
            'instrumentos': instrumentos_ids,
            'generos': generos_ids,
            'ubicacion': ubicacion_id,
            'nivel': nivel_id,
            'presupuesto_min': presupuesto_min,
            'presupuesto_max': presupuesto_max,
            'fecha_evento_desde': fecha_evento_desde,
            'fecha_evento_hasta': fecha_evento_hasta,
            'fecha_publicacion_desde': fecha_publicacion_desde,
            'orden': orden,
        },
        'titulo_pagina': 'Explorar Ofertas Laborales'
    }
    
    return render(request, 'usuarios/ofertas_publicas.html', context)


# VISTAS PARA OFERTAS LABORALES (Sprint 3)
@login_required
def crear_oferta_laboral_view(request):
    """Vista para crear ofertas laborales (solo empleadores)"""
    
    # Verificar que sea empleador
    if request.user.tipo_usuario != 'empleador':
        messages.error(request, 'Solo los empleadores pueden crear ofertas laborales.')
        return redirect('inicio')
    
    # Verificar que tenga perfil de empleador
    try:
        perfil_empleador = request.user.perfil_empleador
    except PerfilEmpleador.DoesNotExist:
        messages.error(request, 'Debes completar tu perfil de empleador antes de crear ofertas.')
        return redirect('crear_perfil_empleador')
    
    if request.method == 'POST':
        form = CrearOfertaLaboralForm(request.POST)
        if form.is_valid():
            oferta = form.save(commit=True, empleador=perfil_empleador)
            messages.success(
                request, 
                f'Oferta "{oferta.titulo}" creada exitosamente como borrador. Puedes publicarla cuando esté lista.'
            )
            return redirect('ver_mis_ofertas')
    else:
        form = CrearOfertaLaboralForm()
    
    context = {
        'form': form,
        'perfil_empleador': perfil_empleador,
        'titulo_pagina': 'Crear Nueva Oferta Laboral'
    }
    
    return render(request, 'usuarios/crear_oferta_laboral.html', context)


@login_required 
def ver_mis_ofertas_view(request):
    """Vista para que empleadores vean sus ofertas laborales"""
    
    if request.user.tipo_usuario != 'empleador':
        messages.error(request, 'Solo los empleadores pueden acceder a esta sección.')
        return redirect('inicio')
    
    try:
        perfil_empleador = request.user.perfil_empleador
        ofertas = OfertaLaboral.objects.filter(empleador=perfil_empleador).order_by('-fecha_creacion')
    except PerfilEmpleador.DoesNotExist:
        messages.error(request, 'Debes completar tu perfil de empleador.')
        return redirect('crear_perfil_empleador')
    
    context = {
        'ofertas': ofertas,
        'perfil_empleador': perfil_empleador,
        'titulo_pagina': 'Mis Ofertas Laborales'
    }
    
    return render(request, 'usuarios/mis_ofertas.html', context)


@login_required 
def detalle_oferta_view(request, slug):
    """Vista de detalle de una oferta laboral"""
    oferta = get_object_or_404(OfertaLaboral, slug=slug)
    postulacion_existente = None
    puede_postularse = False
    
    # Verificar permisos y estado para empleadores
    if request.user.tipo_usuario == 'empleador':
        if oferta.empleador != request.user.perfil_empleador:
            messages.error(request, 'No tienes permisos para ver esta oferta.')
            return redirect('ver_mis_ofertas')
    
    # Para músicos, verificar si pueden postularse y si ya se postularon
    elif request.user.tipo_usuario == 'musico':
        # Verificar si ya se postuló
        try:
            postulacion_existente = Postulacion.objects.get(
                oferta_laboral=oferta,
                musico=request.user
            )
        except Postulacion.DoesNotExist:
            # Verificar si puede postularse
            puede_postularse = (
                oferta.estado == 'publicada' and 
                oferta.esta_vigente() and
                hasattr(request.user, 'portafolio') and
                Postulacion.objects.filter(
                    oferta_laboral=oferta,
                    estado='aceptada'
                ).count() < oferta.cupos_disponibles
            )
    
    context = {
        'oferta': oferta,
        'titulo_pagina': oferta.titulo,
        'postulacion_existente': postulacion_existente,
        'puede_postularse': puede_postularse,
    }
    
    return render(request, 'usuarios/detalle_oferta.html', context)


@login_required
def postular_oferta_view(request, slug):
    """Vista para que músicos se postulen a una oferta laboral"""
    oferta = get_object_or_404(OfertaLaboral, slug=slug)
    
    # Verificar que sea músico
    if request.user.tipo_usuario != 'musico':
        messages.error(request, 'Solo los músicos pueden postularse a ofertas laborales.')
        return redirect('detalle_oferta', slug=slug)
    
    # Verificar que tenga portafolio
    if not hasattr(request.user, 'portafolio'):
        messages.error(
            request, 
            'Debes completar tu portafolio antes de postularte a ofertas laborales.'
        )
        return redirect('crear_portafolio_musico')
    
    # Verificar si ya se postuló
    if Postulacion.objects.filter(oferta_laboral=oferta, musico=request.user).exists():
        messages.warning(request, 'Ya te has postulado a esta oferta anteriormente.')
        return redirect('detalle_oferta', slug=slug)
    
    if request.method == 'POST':
        form = PostulacionForm(
            request.POST,
            musico=request.user,
            oferta=oferta
        )
        
        if form.is_valid():
            postulacion = form.save()
            
            # Enviar notificación al empleador (Ticket 4.4)
            enviar_notificacion_nueva_postulacion(postulacion)
            
            messages.success(
                request,
                f'¡Te has postulado exitosamente a "{oferta.titulo}"! '
                f'El empleador revisará tu postulación y te contactará si eres seleccionado.'
            )
            return redirect('detalle_oferta', slug=slug)
        else:
            # Si hay errores, mostrarlos
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
    else:
        form = PostulacionForm(musico=request.user, oferta=oferta)
    
    context = {
        'form': form,
        'oferta': oferta,
        'titulo_pagina': f'Postularse a "{oferta.titulo}"'
    }
    
    return render(request, 'usuarios/postular_oferta.html', context)


@login_required
def editar_oferta_view(request, slug):
    """Vista para editar una oferta laboral existente"""
    oferta = get_object_or_404(OfertaLaboral, slug=slug)
    
    if request.user.tipo_usuario != 'empleador':
        messages.error(request, 'Solo los empleadores pueden editar ofertas.')
        return redirect('inicio')
    
    if oferta.empleador != request.user.perfil_empleador:
        messages.error(request, 'No tienes permisos para editar esta oferta.')
        return redirect('ver_mis_ofertas')
    
    if oferta.estado == 'cerrada':
        messages.error(request, 'No puedes editar una oferta cerrada.')
        return redirect('detalle_oferta', slug=slug)
    
    if request.method == 'POST':
        form = CrearOfertaLaboralForm(request.POST, instance=oferta)
        if form.is_valid():
            oferta_editada = form.save(commit=False)
            if oferta.estado == 'publicada':
                oferta_editada.estado = 'borrador'
                messages.info(request, 'La oferta ha vuelto a estado borrador debido a los cambios realizados.')
            oferta_editada.save()
            form.save_m2m()
            
            messages.success(request, 'Oferta editada exitosamente.')
            return redirect('detalle_oferta', slug=oferta_editada.slug)
    else:
        form = CrearOfertaLaboralForm(instance=oferta)
    
    context = {
        'form': form,
        'oferta': oferta,
        'titulo_pagina': f'Editar: {oferta.titulo}',
        'es_edicion': True
    }
    
    return render(request, 'usuarios/crear_oferta_laboral.html', context)


@login_required
def publicar_oferta_view(request, slug):
    """Vista para publicar una oferta (cambiar de borrador a publicada)"""
    oferta = get_object_or_404(OfertaLaboral, slug=slug)
    
    if request.user.tipo_usuario != 'empleador':
        messages.error(request, 'Solo los empleadores pueden publicar ofertas.')
        return redirect('inicio')
    
    if oferta.empleador != request.user.perfil_empleador:
        messages.error(request, 'No tienes permisos para publicar esta oferta.')
        return redirect('ver_mis_ofertas')
    
    if oferta.estado != 'borrador':
        messages.warning(request, 'Solo se pueden publicar ofertas en estado borrador.')
        return redirect('detalle_oferta', slug=slug)
    
    oferta.estado = 'publicada'
    oferta.save()
    
    messages.success(request, f'¡Oferta "{oferta.titulo}" publicada exitosamente!')
    return redirect('detalle_oferta', slug=slug)


@login_required
def cerrar_oferta_view(request, slug):
    """Vista para cerrar una oferta laboral"""
    oferta = get_object_or_404(OfertaLaboral, slug=slug)
    
    if request.user.tipo_usuario != 'empleador':
        messages.error(request, 'Solo los empleadores pueden cerrar ofertas.')
        return redirect('inicio')
    
    if oferta.empleador != request.user.perfil_empleador:
        messages.error(request, 'No tienes permisos para cerrar esta oferta.')
        return redirect('ver_mis_ofertas')
    
    if oferta.estado not in ['publicada', 'borrador']:
        messages.warning(request, 'Solo se pueden cerrar ofertas publicadas o en borrador.')
        return redirect('detalle_oferta', slug=slug)
    
    if request.method == 'POST':
        oferta.estado = 'cerrada'
        oferta.save()
        messages.success(request, f'Oferta "{oferta.titulo}" cerrada exitosamente.')
        return redirect('detalle_oferta', slug=slug)
    
    return render(request, 'usuarios/confirmar_cerrar_oferta.html', {
        'oferta': oferta,
        'titulo_pagina': f'Cerrar: {oferta.titulo}'
    })


@login_required
def reabrir_oferta_view(request, slug):
    """Vista para reabrir una oferta laboral cerrada"""
    oferta = get_object_or_404(OfertaLaboral, slug=slug)
    
    if request.user.tipo_usuario != 'empleador':
        messages.error(request, 'Solo los empleadores pueden reabrir ofertas.')
        return redirect('inicio')
    
    if oferta.empleador != request.user.perfil_empleador:
        messages.error(request, 'No tienes permisos para reabrir esta oferta.')
        return redirect('ver_mis_ofertas')
    
    if oferta.estado != 'cerrada':
        messages.warning(request, 'Solo se pueden reabrir ofertas cerradas.')
        return redirect('detalle_oferta', slug=slug)
    
    if request.method == 'POST':
        oferta.estado = 'publicada'
        oferta.save()
        messages.success(request, f'¡Oferta "{oferta.titulo}" reabierta exitosamente! Ahora está visible para músicos nuevamente.')
        return redirect('detalle_oferta', slug=slug)
    
    return render(request, 'usuarios/confirmar_reabrir_oferta.html', {
        'oferta': oferta,
        'titulo_pagina': f'Reabrir: {oferta.titulo}'
    })


@login_required
def gestionar_postulaciones_view(request, slug):
    """Vista para que empleadores vean y gestionen postulaciones de una oferta"""
    oferta = get_object_or_404(OfertaLaboral, slug=slug)
    
    if request.user.tipo_usuario != 'empleador':
        messages.error(request, 'Solo los empleadores pueden gestionar postulaciones.')
        return redirect('inicio')
    
    if oferta.empleador != request.user.perfil_empleador:
        messages.error(request, 'No tienes permisos para gestionar postulaciones de esta oferta.')
        return redirect('ver_mis_ofertas')
    
    postulaciones = oferta.postulaciones.all().select_related(
        'musico', 'portafolio', 'portafolio__ubicacion'
    ).prefetch_related(
        'portafolio__portafolio_instrumentos__instrumento',
        'portafolio__portafolio_generos__genero'
    ).order_by('-fecha_postulacion')
    
    # Estadísticas
    stats = {
        'total': postulaciones.count(),
        'pendientes': postulaciones.filter(estado='pendiente').count(),
        'aceptadas': postulaciones.filter(estado='aceptada').count(),
        'rechazadas': postulaciones.filter(estado='rechazada').count(),
        'en_revision': postulaciones.filter(estado='en_revision').count(),
        'canceladas': postulaciones.filter(estado='cancelada').count(),
    }
    
    context = {
        'oferta': oferta,
        'postulaciones': postulaciones,
        'stats': stats,
        'titulo_pagina': f'Postulaciones - {oferta.titulo}'
    }
    
    return render(request, 'usuarios/gestionar_postulaciones.html', context)


@login_required
def procesar_postulacion_view(request, slug, postulacion_id):
    """Vista para aceptar/rechazar una postulación específica"""
    oferta = get_object_or_404(OfertaLaboral, slug=slug)
    postulacion = get_object_or_404(Postulacion, id=postulacion_id, oferta_laboral=oferta)
    
    if request.user.tipo_usuario != 'empleador':
        messages.error(request, 'Solo los empleadores pueden procesar postulaciones.')
        return redirect('inicio')
    
    if oferta.empleador != request.user.perfil_empleador:
        messages.error(request, 'No tienes permisos para procesar postulaciones de esta oferta.')
        return redirect('ver_mis_ofertas')
    
    if request.method != 'POST':
        messages.error(request, 'Método no permitido.')
        return redirect('gestionar_postulaciones', slug=slug)
    
    accion = request.POST.get('accion')
    notas = request.POST.get('notas', '').strip()
    
    if accion not in ['aceptar', 'rechazar', 'en_revision']:
        messages.error(request, 'Acción no válida.')
        return redirect('gestionar_postulaciones', slug=slug)
    
    # Validar que se puede aceptar (control de cupos)
    if accion == 'aceptar':
        postulaciones_aceptadas = Postulacion.objects.filter(
            oferta_laboral=oferta,
            estado='aceptada'
        ).count()
        
        if postulaciones_aceptadas >= oferta.cupos_disponibles:
            messages.error(
                request,
                f'No se puede aceptar más postulaciones. La oferta ya tiene {oferta.cupos_disponibles} cupos ocupados.'
            )
            return redirect('gestionar_postulaciones', slug=slug)
    
    # Procesar la acción
    estado_anterior = postulacion.estado
    
    if accion == 'aceptar':
        postulacion.estado = 'aceptada'
        mensaje_exito = f'Postulación de {postulacion.musico.get_full_name()} aceptada exitosamente.'
    elif accion == 'rechazar':
        postulacion.estado = 'rechazada'
        mensaje_exito = f'Postulación de {postulacion.musico.get_full_name()} rechazada.'
    elif accion == 'en_revision':
        postulacion.estado = 'en_revision'
        mensaje_exito = f'Postulación de {postulacion.musico.get_full_name()} marcada como en revisión.'
    
    # Agregar notas del empleador
    if notas:
        postulacion.notas_empleador = notas
    
    postulacion.save()
    
    # Enviar notificación al músico sobre el resultado (Ticket 4.5)
    if accion in ['aceptar', 'rechazar'] and estado_anterior != postulacion.estado:
        enviar_notificacion_resultado_postulacion(
            postulacion=postulacion, 
            aceptada=(accion == 'aceptar')
        )
    
    # Verificar si la oferta debe cerrarse automáticamente
    if accion == 'aceptar':
        postulaciones_aceptadas_nuevas = Postulacion.objects.filter(
            oferta_laboral=oferta,
            estado='aceptada'
        ).count()
        
        if postulaciones_aceptadas_nuevas >= oferta.cupos_disponibles:
            oferta.estado = 'cerrada'
            oferta.save()
            mensaje_exito += f' La oferta se ha cerrado automáticamente al completar {oferta.cupos_disponibles} cupos.'
    
    messages.success(request, mensaje_exito)
    return redirect('gestionar_postulaciones', slug=slug)


@login_required
def mis_postulaciones_view(request):
    """Vista para que el músico vea sus postulaciones"""
    if request.user.tipo_usuario != 'musico':
        messages.error(request, 'Solo los músicos pueden ver sus postulaciones.')
        return redirect('inicio')
    
    # Obtener todas las postulaciones del músico
    postulaciones = Postulacion.objects.filter(
        musico=request.user
    ).select_related(
        'oferta_laboral', 
        'oferta_laboral__empleador',
        'oferta_laboral__ubicacion'
    ).order_by('-fecha_postulacion')
    
    # Estadísticas
    stats = {
        'total': postulaciones.count(),
        'pendientes': postulaciones.filter(estado='pendiente').count(),
        'en_revision': postulaciones.filter(estado='en_revision').count(),
        'aceptadas': postulaciones.filter(estado='aceptada').count(),
        'rechazadas': postulaciones.filter(estado='rechazada').count(),
        'canceladas': postulaciones.filter(estado='cancelada').count(),
    }
    
    context = {
        'postulaciones': postulaciones,
        'stats': stats,
        'titulo_pagina': 'Mis Postulaciones'
    }
    
    return render(request, 'usuarios/mis_postulaciones.html', context)


@login_required
def cancelar_postulacion_view(request, postulacion_id):
    """Vista para cancelar una postulación"""
    if request.user.tipo_usuario != 'musico':
        messages.error(request, 'Solo los músicos pueden cancelar postulaciones.')
        return redirect('inicio')
    
    postulacion = get_object_or_404(Postulacion, id=postulacion_id, musico=request.user)
    
    # Verificar que la postulación se pueda cancelar
    if postulacion.estado == 'cancelada':
        messages.warning(request, 'Esta postulación ya está cancelada.')
        return redirect('mis_postulaciones')
    
    if postulacion.estado == 'aceptada':
        messages.error(
            request, 
            'No puedes cancelar una postulación que ya ha sido aceptada. '
            'Contacta directamente al empleador si necesitas retirarte.'
        )
        return redirect('mis_postulaciones')
    
    if postulacion.estado == 'rechazada':
        messages.warning(request, 'No puedes cancelar una postulación que ya ha sido rechazada.')
        return redirect('mis_postulaciones')
    
    if request.method == 'POST':
        # Cancelar la postulación
        postulacion.estado = 'cancelada'
        postulacion.fecha_actualizacion = timezone.now()
        postulacion.save()
        
        messages.success(
            request, 
            f'Has cancelado tu postulación a "{postulacion.oferta_laboral.titulo}" exitosamente.'
        )
        return redirect('mis_postulaciones')
    
    context = {
        'postulacion': postulacion,
        'titulo_pagina': 'Cancelar Postulación'
    }
    
    return render(request, 'usuarios/cancelar_postulacion.html', context)


# VISTAS PARA INVITACIONES DIRECTAS (Ticket 3.8 - FASE 2)

@login_required
def enviar_invitacion_view(request, portafolio_slug):
    """Vista para que empleadores envíen invitaciones directas a músicos"""
    portafolio = get_object_or_404(Portafolio, slug=portafolio_slug)
    
    if request.user.tipo_usuario != 'empleador':
        messages.error(request, 'Solo los empleadores pueden enviar invitaciones.')
        return redirect('inicio')
    
    try:
        perfil_empleador = request.user.perfil_empleador
    except PerfilEmpleador.DoesNotExist:
        messages.error(request, 'Debes completar tu perfil de empleador primero.')
        return redirect('crear_perfil_empleador')
    
    # Obtener ofertas activas del empleador
    ofertas_activas = perfil_empleador.ofertas_laborales.filter(
        estado='publicada'
    ).order_by('-fecha_creacion')
    
    if not ofertas_activas.exists():
        messages.error(request, 'No tienes ofertas laborales activas para enviar invitaciones.')
        return redirect('ver_mis_ofertas')
    
    if request.method == 'POST':
        oferta_id = request.POST.get('oferta_laboral')
        mensaje_invitacion = request.POST.get('mensaje_invitacion', '').strip()
        tarifa_ofrecida = request.POST.get('tarifa_ofrecida')
        
        # Validaciones
        if not oferta_id:
            messages.error(request, 'Debes seleccionar una oferta laboral.')
            return redirect('enviar_invitacion', portafolio_slug=portafolio_slug)
        
        try:
            oferta = ofertas_activas.get(id=oferta_id)
        except OfertaLaboral.DoesNotExist:
            messages.error(request, 'La oferta seleccionada no es válida.')
            return redirect('enviar_invitacion', portafolio_slug=portafolio_slug)
        
        if not mensaje_invitacion:
            messages.error(request, 'El mensaje de invitación es obligatorio.')
            return redirect('enviar_invitacion', portafolio_slug=portafolio_slug)
        
        # Validar tarifa si se proporcionó
        tarifa_ofrecida_int = None
        if tarifa_ofrecida:
            try:
                tarifa_ofrecida_int = int(tarifa_ofrecida)
                if tarifa_ofrecida_int <= 0:
                    raise ValueError("La tarifa debe ser mayor a 0")
                
                # Validar que la tarifa ofrecida sea al menos igual a la tarifa base del músico
                if portafolio.tarifa_base and tarifa_ofrecida_int < portafolio.tarifa_base:
                    messages.error(
                        request, 
                        f'La tarifa ofrecida debe ser al menos {portafolio.tarifa_base:,} CLP '
                        f'(tarifa base del músico). Has ofrecido {tarifa_ofrecida_int:,} CLP.'
                    )
                    return redirect('enviar_invitacion', portafolio_slug=portafolio_slug)
                    
            except (ValueError, TypeError):
                messages.error(request, 'La tarifa ofrecida debe ser un número válido mayor a 0.')
                return redirect('enviar_invitacion', portafolio_slug=portafolio_slug)
        
        # Verificar que no exista ya una invitación pendiente
        invitacion_existente = Invitacion.objects.filter(
            oferta_laboral=oferta,
            musico=portafolio.usuario,
            estado='pendiente'
        ).first()
        
        if invitacion_existente:
            messages.warning(request, f'Ya tienes una invitación pendiente para {portafolio.usuario.get_full_name()} en esta oferta.')
            return redirect('enviar_invitacion', portafolio_slug=portafolio_slug)
        
        # Verificar que no exista una postulación ya
        postulacion_existente = Postulacion.objects.filter(
            oferta_laboral=oferta,
            musico=portafolio.usuario
        ).first()
        
        if postulacion_existente:
            messages.warning(request, f'{portafolio.usuario.get_full_name()} ya se ha postulado a esta oferta.')
            return redirect('enviar_invitacion', portafolio_slug=portafolio_slug)
        
        # Verificar que la oferta tenga cupos disponibles
        if oferta.get_cupos_restantes() <= 0:
            messages.error(request, 'Esta oferta ya no tiene cupos disponibles.')
            return redirect('enviar_invitacion', portafolio_slug=portafolio_slug)
        
        # Crear la invitación
        try:
            invitacion = Invitacion.objects.create(
                oferta_laboral=oferta,
                musico=portafolio.usuario,
                empleador=perfil_empleador,
                portafolio=portafolio,
                mensaje_invitacion=mensaje_invitacion,
                tarifa_ofrecida=tarifa_ofrecida_int
            )
            
            messages.success(
                request, 
                f'Invitación enviada exitosamente a {portafolio.usuario.get_full_name()} para la oferta "{oferta.titulo}".'
            )
            return redirect('portafolio_publico', slug=portafolio_slug)
            
        except Exception as e:
            messages.error(request, 'Ocurrió un error al enviar la invitación. Inténtalo nuevamente.')
            return redirect('enviar_invitacion', portafolio_slug=portafolio_slug)
    
    # GET request - mostrar formulario
    context = {
        'portafolio': portafolio,
        'ofertas_activas': ofertas_activas,
        'titulo_pagina': f'Invitar a {portafolio.usuario.get_full_name()}'
    }
    
    return render(request, 'usuarios/enviar_invitacion.html', context)


@login_required
def mis_invitaciones_enviadas_view(request):
    """Vista para que empleadores vean las invitaciones que han enviado"""
    if request.user.tipo_usuario != 'empleador':
        messages.error(request, 'Solo los empleadores pueden ver esta página.')
        return redirect('inicio')
    
    try:
        perfil_empleador = request.user.perfil_empleador
    except PerfilEmpleador.DoesNotExist:
        messages.error(request, 'Debes completar tu perfil de empleador primero.')
        return redirect('crear_perfil_empleador')
    
    # Filtros
    estado_filtro = request.GET.get('estado', '')
    oferta_filtro = request.GET.get('oferta', '')
    
    invitaciones = perfil_empleador.invitaciones_enviadas.all().select_related(
        'musico', 'oferta_laboral', 'portafolio'
    ).order_by('-fecha_invitacion')
    
    if estado_filtro:
        invitaciones = invitaciones.filter(estado=estado_filtro)
    
    if oferta_filtro:
        try:
            oferta_id = int(oferta_filtro)
            invitaciones = invitaciones.filter(oferta_laboral_id=oferta_id)
        except (ValueError, TypeError):
            pass
    
    # Estadísticas
    stats = {
        'total': invitaciones.count(),
        'pendientes': invitaciones.filter(estado='pendiente').count(),
        'aceptadas': invitaciones.filter(estado='aceptada').count(),
        'rechazadas': invitaciones.filter(estado='rechazada').count(),
        'expiradas': invitaciones.filter(estado='expirada').count(),
        'canceladas': invitaciones.filter(estado='cancelada').count(),
    }
    
    # Ofertas para el filtro
    ofertas_para_filtro = perfil_empleador.ofertas_laborales.filter(
        estado='publicada'
    ).order_by('-fecha_creacion')
    
    context = {
        'invitaciones': invitaciones,
        'stats': stats,
        'ofertas_para_filtro': ofertas_para_filtro,
        'estado_filtro': estado_filtro,
        'oferta_filtro': oferta_filtro,
        'titulo_pagina': 'Mis Invitaciones Enviadas'
    }
    
    return render(request, 'usuarios/mis_invitaciones_enviadas.html', context)


@login_required
def cancelar_invitacion_view(request, invitacion_id):
    """Vista para que empleadores cancelen invitaciones pendientes"""
    invitacion = get_object_or_404(Invitacion, id=invitacion_id)
    
    if request.user.tipo_usuario != 'empleador':
        messages.error(request, 'Solo los empleadores pueden cancelar invitaciones.')
        return redirect('inicio')
    
    if invitacion.empleador != request.user.perfil_empleador:
        messages.error(request, 'No tienes permisos para cancelar esta invitación.')
        return redirect('mis_invitaciones_enviadas')
    
    if not invitacion.puede_ser_cancelada():
        messages.error(request, 'Esta invitación ya no puede ser cancelada.')
        return redirect('mis_invitaciones_enviadas')
    
    if request.method == 'POST':
        try:
            invitacion.cancelar()
            messages.success(
                request, 
                f'Invitación a {invitacion.musico.get_full_name()} cancelada exitosamente.'
            )
        except Exception as e:
            messages.error(request, 'Ocurrió un error al cancelar la invitación.')
        
        return redirect('mis_invitaciones_enviadas')
    
    context = {
        'invitacion': invitacion,
        'titulo_pagina': 'Cancelar Invitación'
    }
    
    return render(request, 'usuarios/cancelar_invitacion.html', context)


# ===========================================
# TICKET 3.8 - FASE 3: Dashboard para músicos
# ===========================================

@login_required
def mis_invitaciones_recibidas_view(request):
    """Vista para que los músicos vean sus invitaciones recibidas"""
    
    # Verificar que el usuario sea músico
    if not hasattr(request.user, 'portafolio'):
        messages.error(request, 'Solo los músicos pueden acceder a esta sección.')
        return redirect('ver_mi_perfil')
    
    # Obtener todas las invitaciones recibidas por este músico
    invitaciones = Invitacion.objects.filter(
        musico=request.user
    ).select_related(
        'empleador', 
        'oferta_laboral',
        'postulacion_creada'
    ).order_by('-fecha_invitacion')
    
    # Separar por estado para mejor organización
    invitaciones_pendientes = invitaciones.filter(estado='pendiente')
    invitaciones_aceptadas = invitaciones.filter(estado='aceptada')
    invitaciones_rechazadas = invitaciones.filter(estado='rechazada')
    invitaciones_canceladas = invitaciones.filter(estado='cancelada')
    
    # Estadísticas para el dashboard
    stats = {
        'total': invitaciones.count(),
        'pendientes': invitaciones_pendientes.count(),
        'aceptadas': invitaciones_aceptadas.count(),
        'rechazadas': invitaciones_rechazadas.count(),
        'canceladas': invitaciones_canceladas.count(),
    }
    
    context = {
        'invitaciones_pendientes': invitaciones_pendientes,
        'invitaciones_aceptadas': invitaciones_aceptadas,
        'invitaciones_rechazadas': invitaciones_rechazadas,
        'invitaciones_canceladas': invitaciones_canceladas,
        'stats': stats,
        'titulo_pagina': 'Mis Invitaciones Recibidas',
        'descripcion_pagina': 'Gestiona las invitaciones que has recibido de empleadores'
    }
    
    return render(request, 'usuarios/mis_invitaciones_recibidas.html', context)


@login_required
def responder_invitacion_view(request, invitacion_id):
    """Vista para que los músicos respondan a invitaciones (aceptar/rechazar)"""
    
    # Verificar que el usuario sea músico
    if not hasattr(request.user, 'portafolio'):
        messages.error(request, 'Solo los músicos pueden responder invitaciones.')
        return redirect('ver_mi_perfil')
    
    # Obtener la invitación
    invitacion = get_object_or_404(
        Invitacion, 
        id=invitacion_id,
        musico=request.user
    )
    
    # Verificar que la invitación esté pendiente
    if invitacion.estado != 'pendiente':
        messages.error(request, 'Esta invitación ya ha sido respondida.')
        return redirect('mis_invitaciones_recibidas')
    
    # Verificar que la oferta laboral esté activa
    if invitacion.oferta_laboral.estado != 'publicada':
        messages.error(request, 'Esta oferta laboral ya no está disponible.')
        return redirect('mis_invitaciones_recibidas')
    
    if request.method == 'POST':
        accion = request.POST.get('accion')
        mensaje_respuesta = request.POST.get('mensaje_respuesta', '').strip()
        
        try:
            if accion == 'aceptar':
                # Verificar nuevamente antes de aceptar
                if not invitacion.puede_ser_aceptada():
                    messages.error(request, 'La invitación no puede ser aceptada en este momento.')
                    return redirect('mis_invitaciones_recibidas')
                
                # Aceptar la invitación (crea automáticamente una postulación)
                postulacion = invitacion.aceptar(mensaje_respuesta)
                
                messages.success(
                    request,
                    f'¡Invitación aceptada! Se ha creado tu postulación para "{invitacion.oferta_laboral.titulo}".'
                )
                
                # Redirigir al detalle de la oferta para ver la postulación creada
                return redirect('detalle_oferta', slug=invitacion.oferta_laboral.slug)
                
            elif accion == 'rechazar':
                # Rechazar la invitación
                invitacion.rechazar(mensaje_respuesta)
                
                messages.success(
                    request,
                    f'Invitación rechazada. El empleador ha sido notificado.'
                )
                
                return redirect('mis_invitaciones_recibidas')
                
            else:
                messages.error(request, 'Acción no válida.')
                
        except Exception as e:
            messages.error(request, f'Error al procesar la respuesta: {str(e)}')
    
    context = {
        'invitacion': invitacion,
        'titulo_pagina': f'Responder Invitación - {invitacion.oferta_laboral.titulo}',
        'descripcion_pagina': f'Invitación de {invitacion.empleador.usuario.get_full_name()}'
    }
    
    return render(request, 'usuarios/responder_invitacion.html', context)


# SISTEMA DE REFERENCIAS LABORALES (Sprint 4)

@login_required
def solicitar_referencia(request, portafolio_id):
    """Vista para que músicos soliciten referencias laborales"""
    portafolio = get_object_or_404(Portafolio, id=portafolio_id)
    
    # Solo el propietario del portafolio puede solicitar referencias
    if request.user != portafolio.usuario:
        raise PermissionDenied("No tienes permisos para solicitar referencias para este portafolio.")
    
    if request.method == 'POST':
        form = SolicitudReferenciaForm(request.POST, portafolio=portafolio)
        if form.is_valid():
            testimonio = form.save()
            
            # Enviar email de solicitud
            try:
                enviar_email_solicitud_referencia(testimonio)
                messages.success(
                    request, 
                    f'Solicitud de referencia enviada a {testimonio.autor_nombre} ({testimonio.autor_email}). '
                    'Te notificaremos cuando respondan.'
                )
            except Exception as e:
                # La solicitud se guardó pero falló el email
                if settings.DEBUG:
                    # En desarrollo, mostrar el error específico
                    messages.error(
                        request,
                        f'Solicitud guardada, pero no se pudo enviar el email. Error: {str(e)}'
                    )
                else:
                    # En producción, mensaje genérico
                    messages.warning(
                        request,
                        'Solicitud guardada, pero no se pudo enviar el email. '
                        'Podrás contactar manualmente al empleador.'
                    )
            
            return redirect('portafolio_publico', slug=portafolio.slug)
    else:
        form = SolicitudReferenciaForm(portafolio=portafolio)
    
    context = {
        'form': form,
        'portafolio': portafolio,
        'titulo_pagina': 'Solicitar Referencia Laboral',
        'descripcion_pagina': f'Solicita una referencia para tu portafolio'
    }
    
    return render(request, 'usuarios/solicitar_referencia.html', context)


def responder_referencia(request, token):
    """Vista para que empleadores respondan solicitudes de referencia"""
    testimonio = get_object_or_404(Testimonio, token_solicitud=token, estado='pendiente')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'aprobar':
            form = ResponderReferenciaForm(request.POST, instance=testimonio)
            if form.is_valid():
                form.save()
                
                # TODO: Crear notificación para el músico cuando tengamos modelo apropiado
                # Notificacion.objects.create(
                #     usuario_destino=testimonio.portafolio.usuario,
                #     tipo='referencia_aprobada',
                #     titulo='Referencia aprobada',
                #     mensaje=f'{testimonio.autor_nombre} ha enviado tu referencia laboral.',
                #     leida=False
                # )
                
                messages.success(request, 'Referencia enviada exitosamente. ¡Gracias!')
                return render(request, 'usuarios/referencia_enviada.html', {
                    'testimonio': testimonio,
                    'accion': 'aprobada'
                })
        
        elif action == 'rechazar':
            testimonio.estado = 'rechazado'
            testimonio.fecha_respuesta = timezone.now()
            testimonio.save()
            
            # TODO: Crear notificación para el músico cuando tengamos modelo apropiado
            # Notificacion.objects.create(
            #     usuario_destino=testimonio.portafolio.usuario,
            #     tipo='referencia_rechazada',
            #     titulo='Solicitud de referencia declinada',
            #     mensaje=f'{testimonio.autor_nombre} ha declinado proporcionar la referencia solicitada.',
            #     leida=False
            # )
            
            messages.info(request, 'Solicitud de referencia declinada.')
            return render(request, 'usuarios/referencia_enviada.html', {
                'testimonio': testimonio,
                'accion': 'rechazada'
            })
    else:
        form = ResponderReferenciaForm(instance=testimonio)
    
    context = {
        'form': form,
        'testimonio': testimonio,
        'musico': testimonio.portafolio.usuario,
        'portafolio': testimonio.portafolio,
        'titulo_pagina': f'Referencia para {testimonio.portafolio.usuario.get_full_name()}',
        'descripcion_pagina': 'Proporciona una referencia laboral'
    }
    
    return render(request, 'usuarios/responder_referencia.html', context)


@login_required
def gestionar_referencias(request):
    """Vista para que músicos gestionen sus referencias"""
    if request.user.tipo_usuario != 'musico':
        raise PermissionDenied("Solo los músicos pueden acceder a esta página.")
    
    try:
        portafolio = request.user.portafolio
    except Portafolio.DoesNotExist:
        messages.warning(request, 'Debes completar tu portafolio antes de gestionar referencias.')
        return redirect('editar_portafolio_musico')
    
    # Obtener todas las referencias
    referencias_pendientes = Testimonio.objects.filter(
        portafolio=portafolio,
        estado='pendiente'
    ).order_by('-fecha_solicitud')
    
    referencias_aprobadas = Testimonio.objects.filter(
        portafolio=portafolio,
        estado='aprobado'
    ).order_by('-fecha_respuesta')
    
    referencias_rechazadas = Testimonio.objects.filter(
        portafolio=portafolio,
        estado='rechazado'
    ).order_by('-fecha_respuesta')
    
    testimonios_directos = Testimonio.objects.filter(
        portafolio=portafolio,
        estado='directo'
    ).order_by('-fecha_publicacion')
    
    context = {
        'portafolio': portafolio,
        'referencias_pendientes': referencias_pendientes,
        'referencias_aprobadas': referencias_aprobadas,
        'referencias_rechazadas': referencias_rechazadas,
        'testimonios_directos': testimonios_directos,
        'titulo_pagina': 'Gestionar Referencias',
        'descripcion_pagina': 'Administra tus referencias laborales y testimonios'
    }
    
    return render(request, 'usuarios/gestionar_referencias.html', context)


@login_required
def agregar_testimonio_directo(request):
    """Vista para agregar testimonios directamente (sin solicitud)"""
    if request.user.tipo_usuario != 'musico':
        raise PermissionDenied("Solo los músicos pueden agregar testimonios.")
    
    try:
        portafolio = request.user.portafolio
    except Portafolio.DoesNotExist:
        messages.warning(request, 'Debes completar tu portafolio antes de agregar testimonios.')
        return redirect('editar_portafolio_musico')
    
    if request.method == 'POST':
        form = TestimonioDirectoForm(request.POST, portafolio=portafolio)
        if form.is_valid():
            testimonio = form.save()
            messages.success(request, 'Testimonio agregado exitosamente.')
            return redirect('gestionar_referencias')
    else:
        form = TestimonioDirectoForm(portafolio=portafolio)
    
    context = {
        'form': form,
        'portafolio': portafolio,
        'titulo_pagina': 'Agregar Testimonio',
        'descripcion_pagina': 'Agrega un testimonio directo a tu portafolio'
    }
    
    return render(request, 'usuarios/agregar_testimonio.html', context)


def enviar_email_solicitud_referencia(testimonio):
    """Función auxiliar para enviar email de solicitud de referencia"""
    subject = f'Solicitud de referencia laboral de {testimonio.portafolio.usuario.get_full_name()}'
    
    # URL segura para responder
    url_respuesta = f"{settings.SITE_URL}/referencias/responder/{testimonio.token_solicitud}/"
    
    context = {
        'testimonio': testimonio,
        'musico': testimonio.portafolio.usuario,
        'portafolio': testimonio.portafolio,
        'url_respuesta': url_respuesta,
    }
    
    html_message = render_to_string('emails/solicitud_referencia.html', context)
    plain_message = render_to_string('emails/solicitud_referencia.txt', context)
    
    send_mail(
        subject=subject,
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[testimonio.autor_email],
        html_message=html_message,
        fail_silently=False
    )


# ===================================================================
# FUNCIONES DE NOTIFICACIÓN - SPRINT 4 TICKETS 4.4 y 4.5
# ===================================================================

def enviar_notificacion_nueva_postulacion(postulacion):
    """
    Envía notificación por email al empleador cuando recibe una nueva postulación
    Ticket 4.4: Notificar postulación a empleador
    """
    try:
        empleador = postulacion.oferta_laboral.empleador.usuario
        musico = postulacion.musico
        
        # URLs para el email (usando URLs que sabemos que funcionan)
        url_oferta = f"http://127.0.0.1:8000/ofertas/{postulacion.oferta_laboral.slug}/"
        url_admin_postulaciones = "http://127.0.0.1:8000/admin/usuarios/postulacion/"
        url_portafolio = f"http://127.0.0.1:8000/portafolio/{musico.username}/"
        
        # Contexto para los templates
        context = {
            'empleador': empleador,
            'postulacion': postulacion,
            'musico': musico,
            'oferta': postulacion.oferta_laboral,
            'url_oferta': url_oferta,
            'url_admin_postulaciones': url_admin_postulaciones,
            'url_portafolio': url_portafolio,
        }
        
        # Renderizar templates
        subject = f"📧 Nueva postulación para '{postulacion.oferta_laboral.titulo}' - Meet & Gig"
        html_message = render_to_string('emails/nueva_postulacion.html', context)
        plain_message = render_to_string('emails/nueva_postulacion.txt', context)
        
        # Enviar email
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[empleador.email],
            html_message=html_message,
            fail_silently=False
        )
        
        # Crear notificación en base de datos para empleador
        Notificacion.objects.create(
            empleador=empleador.perfil_empleador,
            tipo='nueva_postulacion',
            titulo=f"Nueva postulación para '{postulacion.oferta_laboral.titulo}'",
            mensaje=f"{musico.get_full_name()} se ha postulado para tu oferta laboral.",
            postulacion=postulacion,
            oferta_laboral=postulacion.oferta_laboral
        )
        
        return True
        
    except Exception as e:
        # Log del error (en producción usar logging proper)
        print(f"Error enviando notificación nueva postulación: {str(e)}")
        return False


def enviar_notificacion_resultado_postulacion(postulacion):
    """
    Envía notificación por email al músico sobre el resultado de su postulación
    Ticket 4.5: Notificar resultado de postulación al músico
    """
    try:
        musico = postulacion.musico
        
        # Determinar si fue aceptada o rechazada
        aceptada = postulacion.estado == 'aceptada'
        
        # URLs para el email (usando URLs que sabemos que funcionan)
        url_mis_postulaciones = "http://127.0.0.1:8000/mis-postulaciones/"
        url_oferta = f"http://127.0.0.1:8000/ofertas/{postulacion.oferta_laboral.slug}/"
        url_ofertas = "http://127.0.0.1:8000/ofertas/"
        url_portafolio = f"http://127.0.0.1:8000/portafolio/{musico.username}/"
        
        # Contexto para los templates
        context = {
            'musico': musico,
            'postulacion': postulacion,
            'oferta': postulacion.oferta_laboral,
            'empleador': postulacion.oferta_laboral.empleador.usuario,
            'url_mis_postulaciones': url_mis_postulaciones,
            'url_oferta': url_oferta,
            'url_ofertas': url_ofertas,
            'url_portafolio': url_portafolio,
        }
        
        if aceptada:
            # Email de postulación aceptada
            subject = f"🎉 ¡Postulación aceptada para '{postulacion.oferta_laboral.titulo}'! - Meet & Gig"
            html_template = 'emails/postulacion_aceptada.html'
            txt_template = 'emails/postulacion_aceptada.txt'
            notif_tipo = 'postulacion_aceptada'
            notif_titulo = f"¡Postulación aceptada para '{postulacion.oferta_laboral.titulo}'!"
            notif_mensaje = f"Tu postulación ha sido aceptada. ¡Felicidades!"
        else:
            # Email de postulación rechazada
            subject = f"📄 Resultado de postulación para '{postulacion.oferta_laboral.titulo}' - Meet & Gig"
            html_template = 'emails/postulacion_rechazada.html'
            txt_template = 'emails/postulacion_rechazada.txt'
            notif_tipo = 'postulacion_rechazada'
            notif_titulo = f"Resultado de postulación para '{postulacion.oferta_laboral.titulo}'"
            notif_mensaje = f"El empleador ha tomado una decisión sobre tu postulación."
        
        # Renderizar templates
        html_message = render_to_string(html_template, context)
        plain_message = render_to_string(txt_template, context)
        
        # Enviar email
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[musico.email],
            html_message=html_message,
            fail_silently=False
        )
        
        # Para músicos, no tenemos un modelo de notificación en BD por ahora
        # Solo enviamos el email
        # En futuras versiones se podría crear un modelo de notificación universal
        
        return True
        
    except Exception as e:
        # Log del error (en producción usar logging proper)
        print(f"Error enviando notificación resultado postulación: {str(e)}")
        return False


@login_required
def aceptar_referencia(request, testimonio_id):
    """Vista para que el músico acepte una referencia pendiente"""
    if request.user.tipo_usuario != 'musico':
        raise PermissionDenied("Solo los músicos pueden gestionar referencias.")
    
    testimonio = get_object_or_404(
        Testimonio, 
        id=testimonio_id, 
        portafolio__usuario=request.user,
        estado='pendiente'
    )
    
    if request.method == 'POST':
        # Cambiar estado a aprobado
        testimonio.estado = 'aprobado'
        testimonio.fecha_respuesta = timezone.now()
        testimonio.save()
        
        messages.success(
            request, 
            f'Has aceptado la referencia de {testimonio.autor_nombre}. Ahora será visible en tu portafolio público.'
        )
        
        # Enviar email de confirmación al autor de la referencia
        try:
            enviar_notificacion_respuesta_referencia(testimonio, aceptada=True)
        except Exception as e:
            messages.warning(request, 'Referencia aceptada, pero hubo un problema enviando la notificación por email.')
        
        return redirect('gestionar_referencias')
    
    context = {
        'testimonio': testimonio,
        'accion': 'aceptar',
        'titulo_pagina': 'Aceptar Referencia',
    }
    
    return render(request, 'usuarios/confirmar_accion_referencia.html', context)


@login_required  
def rechazar_referencia(request, testimonio_id):
    """Vista para que el músico rechace una referencia pendiente"""
    if request.user.tipo_usuario != 'musico':
        raise PermissionDenied("Solo los músicos pueden gestionar referencias.")
    
    testimonio = get_object_or_404(
        Testimonio, 
        id=testimonio_id, 
        portafolio__usuario=request.user,
        estado='pendiente'
    )
    
    if request.method == 'POST':
        # Cambiar estado a rechazado
        testimonio.estado = 'rechazado'
        testimonio.fecha_respuesta = timezone.now()
        testimonio.save()
        
        messages.info(
            request, 
            f'Has rechazado la referencia de {testimonio.autor_nombre}. No será visible en tu portafolio.'
        )
        
        # Enviar email de notificación al autor de la referencia
        try:
            enviar_notificacion_respuesta_referencia(testimonio, aceptada=False)
        except Exception as e:
            messages.warning(request, 'Referencia rechazada, pero hubo un problema enviando la notificación por email.')
        
        return redirect('gestionar_referencias')
    
    context = {
        'testimonio': testimonio,
        'accion': 'rechazar',
        'titulo_pagina': 'Rechazar Referencia',
    }
    
    return render(request, 'usuarios/confirmar_accion_referencia.html', context)


@login_required
def ocultar_referencia(request, testimonio_id):
    """Vista para ocultar/mostrar una referencia aprobada del portafolio público"""
    if request.user.tipo_usuario != 'musico':
        raise PermissionDenied("Solo los músicos pueden gestionar referencias.")
    
    testimonio = get_object_or_404(
        Testimonio, 
        id=testimonio_id, 
        portafolio__usuario=request.user,
        estado__in=['aprobado', 'directo']
    )
    
    if request.method == 'POST':
        # Alternar visibilidad
        testimonio.activo = not testimonio.activo
        testimonio.save()
        
        if testimonio.activo:
            messages.success(
                request, 
                f'La referencia de {testimonio.autor_nombre} ahora es visible en tu portafolio público.'
            )
        else:
            messages.info(
                request, 
                f'Has ocultado la referencia de {testimonio.autor_nombre} de tu portafolio público. Puedes mostrarla nuevamente cuando quieras.'
            )
        
        return redirect('gestionar_referencias')
    
    context = {
        'testimonio': testimonio,
        'accion': 'ocultar' if testimonio.activo else 'mostrar',
        'titulo_pagina': 'Ocultar Referencia' if testimonio.activo else 'Mostrar Referencia',
    }
    
    return render(request, 'usuarios/confirmar_accion_referencia.html', context)


@login_required
def eliminar_referencia(request, testimonio_id):
    """Vista para eliminar permanentemente una referencia"""
    if request.user.tipo_usuario != 'musico':
        raise PermissionDenied("Solo los músicos pueden gestionar referencias.")
    
    testimonio = get_object_or_404(
        Testimonio, 
        id=testimonio_id, 
        portafolio__usuario=request.user
    )
    
    if request.method == 'POST':
        autor_nombre = testimonio.autor_nombre
        testimonio.delete()
        
        messages.warning(
            request, 
            f'Has eliminado permanentemente la referencia de {autor_nombre}.'
        )
        
        return redirect('gestionar_referencias')
    
    context = {
        'testimonio': testimonio,
        'accion': 'eliminar',
        'titulo_pagina': 'Eliminar Referencia',
    }
    
    return render(request, 'usuarios/confirmar_accion_referencia.html', context)


def enviar_notificacion_respuesta_referencia(testimonio, aceptada=True):
    """
    Envía email de notificación al autor de la referencia cuando el músico responde
    """
    try:
        musico = testimonio.portafolio.usuario
        
        # URLs para el contexto (usar settings.SITE_URL si está disponible)
        url_portafolio = None
        if aceptada and hasattr(settings, 'SITE_URL'):
            url_portafolio = f"{settings.SITE_URL}/portafolio/{testimonio.portafolio.slug}/"
        
        # Contexto para los templates
        context = {
            'testimonio': testimonio,
            'musico': musico,
            'aceptada': aceptada,
            'url_portafolio': url_portafolio,
        }
        
        if aceptada:
            # Email de referencia aceptada
            subject = f"✅ {musico.get_full_name()} aceptó tu referencia - Meet & Gig"
            html_template = 'emails/referencia_aceptada.html'
            txt_template = 'emails/referencia_aceptada.txt'
        else:
            # Email de referencia rechazada
            subject = f"📝 Respuesta a tu referencia de {musico.get_full_name()} - Meet & Gig"
            html_template = 'emails/referencia_rechazada.html'
            txt_template = 'emails/referencia_rechazada.txt'
        
        # Renderizar templates
        html_message = render_to_string(html_template, context)
        plain_message = render_to_string(txt_template, context)
        
        # Enviar email
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[testimonio.autor_email],
            html_message=html_message,
            fail_silently=False
        )
        
        return True
        
    except Exception as e:
        print(f"Error enviando notificación respuesta referencia: {str(e)}")
        return False
