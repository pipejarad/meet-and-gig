from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, SetPasswordForm
from django.core.exceptions import ValidationError
from django.utils import timezone
from PIL import Image
from .models import (Usuario, PerfilMusico, PerfilEmpleador, Portafolio,OfertaLaboral, OfertaInstrumento, OfertaGenero, Postulacion, Testimonio, ContactoMusico)


def validate_image_file(image):
    """Valida que el archivo de imagen sea válido y tenga un tamaño apropiado"""
    if image:
        # Validar tamaño de archivo (máximo 5MB)
        if image.size > 5 * 1024 * 1024:
            raise ValidationError("La imagen no puede ser mayor a 5MB.")
        
        # Validar que sea una imagen válida
        try:
            img = Image.open(image)
            # Techo de píxeles ANTES de decodificar: una "decompression bomb"
            # (pocos KB que se expanden a cientos de MB) agotaría la memoria.
            ancho, alto = img.size
            if ancho * alto > 25_000_000:  # ~25 megapíxeles
                raise ValidationError("La imagen es demasiado grande (máximo 25 megapíxeles).")
            img.verify()
        except ValidationError:
            raise
        except Exception:
            raise ValidationError("El archivo debe ser una imagen válida (JPG, PNG, GIF).")
        
        # Validar dimensiones mínimas
        image.seek(0)  # Reset el puntero del archivo
        img = Image.open(image)
        width, height = img.size
        if width < 100 or height < 100:
            raise ValidationError("La imagen debe tener al menos 100x100 píxeles.")
        
        # Validar formato
        if img.format.lower() not in ['jpeg', 'jpg', 'png', 'gif']:
            raise ValidationError("Solo se permiten archivos JPG, PNG o GIF.")
    
    return image


class RegistroForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'correo@ejemplo.com'
        }),
        error_messages={
            'required': 'El email es obligatorio.',
            'invalid': 'Ingresa un email válido.',
        }
    )
    
    # DIFERIDO v1 (pivote a vitrina): el selector no se renderiza en el template y
    # save() fuerza 'musico'. Para reactivar empleadores: required=True, quitar el
    # forzado en save() y restaurar el campo en registro.html.
    tipo_usuario = forms.ChoiceField(
        choices=Usuario.TIPO_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        error_messages={
            'required': 'Debes seleccionar un tipo de usuario.',
        }
    )
    
    foto_perfil = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        }),
        validators=[validate_image_file],
        help_text='Imagen de perfil (máx. 5MB, mín. 100x100px, formatos: JPG, PNG, GIF)'
    )
    
    password1 = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingresa tu contraseña'
        })
    )
    
    password2 = forms.CharField(
        label='Confirmar contraseña',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirma tu contraseña'
        })
    )
    
    username = forms.CharField(
        label='Nombre de usuario',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nombre de usuario único'
        })
    )

    class Meta:
        model = Usuario
        fields = ['username', 'email', 'tipo_usuario', 'foto_perfil', 'password1', 'password2']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email:
            return email
            
        if Usuario.objects.filter(email__iexact=email).exists():
            raise ValidationError("Este email ya está registrado.")
        return email.lower()

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if not username:
            return username

        # Un username con '@' puede hacerse pasar por el email de otra cuenta
        # y bloquearle el login (hallazgo A3): el backend de autenticación
        # busca por ambos campos.
        if '@' in username:
            raise ValidationError("El nombre de usuario no puede contener '@'.")

        if Usuario.objects.filter(username__iexact=username).exists():
            raise ValidationError("Este nombre de usuario ya está en uso.")

        # Defensa en profundidad por si la regla del '@' se relajara: nunca
        # permitir un username que coincida con un email ya registrado.
        if Usuario.objects.filter(email__iexact=username).exists():
            raise ValidationError("Este nombre de usuario no está disponible.")

        return username

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email'].lower()
        user.tipo_usuario = 'musico'  # DIFERIDO v1: solo se registran músicos
        if commit:
            user.save()
        return user


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label='Email o nombre de usuario',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'correo@ejemplo.com o nombre de usuario'
        })
    )
    
    password = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Tu contraseña'
        })
    )


class RecuperarPasswordForm(forms.Form):
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'correo@ejemplo.com'
        }),
        error_messages={
            'required': 'El email es obligatorio.',
            'invalid': 'Ingresa un email válido.',
        }
    )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email:
            return email
            
        return email.lower()


class CambiarPasswordForm(SetPasswordForm):
    new_password1 = forms.CharField(
        label='Nueva contraseña',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingresa tu nueva contraseña'
        }),
        help_text='Tu contraseña debe tener al menos 8 caracteres.'
    )
    
    new_password2 = forms.CharField(
        label='Confirmar nueva contraseña',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirma tu nueva contraseña'
        })
    )


class PerfilMusicoForm(forms.ModelForm):
    first_name = forms.CharField(
        max_length=30,
        required=True,
        label='Nombre',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        label='Apellido',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    foto_perfil = forms.ImageField(
        required=False,
        label="Foto de perfil",
        help_text="Imagen de perfil (máx. 5MB, mín. 100x100px, formatos: JPG, PNG, GIF)",
        widget=forms.FileInput(attrs={'class': 'form-control'}),
        validators=[validate_image_file]
    )

    class Meta:
        model = PerfilMusico
        fields = [
            'telefono', 'fecha_nacimiento', 'direccion',
            'recibir_notificaciones_email', 'mostrar_telefono_publico'
        ]
        
        widgets = {
            'telefono': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+56912345678'
            }),
            'fecha_nacimiento': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'direccion': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Dirección completa'
            }),
            'recibir_notificaciones_email': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'mostrar_telefono_publico': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
    
    def __init__(self, *args, **kwargs):
        self.usuario = kwargs.pop('usuario', None)
        super().__init__(*args, **kwargs)
        
        if self.usuario:
            self.fields['first_name'].initial = self.usuario.first_name
            self.fields['last_name'].initial = self.usuario.last_name
            if hasattr(self.usuario, 'foto_perfil') and self.usuario.foto_perfil:
                self.fields['foto_perfil'].initial = self.usuario.foto_perfil
    
    def clean_telefono(self):
        telefono = self.cleaned_data.get('telefono', '')
        if telefono and len(telefono.replace(' ', '').replace('+', '').replace('-', '')) < 8:
            raise forms.ValidationError('El teléfono debe tener al menos 8 dígitos.')
        return telefono
    
    def save(self, commit=True):
        perfil = super().save(commit=False)
        
        if not perfil.usuario_id:
            perfil.usuario = self.usuario
        
        if commit:
            perfil.save()
            
            if self.usuario:
                self.usuario.first_name = self.cleaned_data.get('first_name', '')
                self.usuario.last_name = self.cleaned_data.get('last_name', '')
                
                # Manejar foto_perfil
                if self.cleaned_data.get('foto_perfil'):
                    self.usuario.foto_perfil = self.cleaned_data['foto_perfil']
                
                self.usuario.save()
        
        return perfil


class PortafolioForm(forms.ModelForm):
    # Campos M2M personalizados para instrumentos
    instrumento_principal = forms.ModelChoiceField(
        queryset=None,
        required=True,
        label='Instrumento Principal',
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text='Selecciona tu instrumento principal'
    )
    
    instrumentos_secundarios = forms.ModelMultipleChoiceField(
        queryset=None,
        required=False,
        label='Instrumentos Secundarios',
        widget=forms.CheckboxSelectMultiple(),
        help_text='Selecciona otros instrumentos que domines (máximo 5)'
    )
    
    # Campos M2M personalizados para géneros
    generos_musicales = forms.ModelMultipleChoiceField(
        queryset=None,
        required=True,
        label='Géneros Musicales',
        widget=forms.CheckboxSelectMultiple(),
        help_text='Selecciona los géneros que tocas (máximo 8)'
    )

    biografia = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Cuéntanos sobre tu trayectoria musical, experiencias destacadas, influencias...',
            'maxlength': 1000
        })
    )
    
    formacion_musical = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Estudios formales, cursos, talleres, profesores destacados...',
            'maxlength': 500
        })
    )
    
    tarifa_base = forms.IntegerField(
        required=False,
        min_value=0,  # Validación del lado del servidor
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '150000',
            'step': '1000',
            'min': '0'
        }),
        help_text='Tarifa base por presentación en pesos chilenos (CLP, sin decimales)'
    )

    class Meta:
        model = Portafolio
        fields = [
            'biografia', 'formacion_musical', 'años_experiencia',
            'nivel_experiencia', 'ubicacion', 'website_personal', 'soundcloud_url',
            'youtube_url', 'spotify_url', 'instagram_url', 'facebook_url',
            'video_demo', 'disponible_para_gigs', 'tarifa_base',
            'show_email', 'show_social_links', 'show_education', 'show_tarifa', 'show_telefono'
        ]
        
        widgets = {
            'biografia': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Cuéntanos sobre tu trayectoria musical...',
                'maxlength': 1000
            }),
            'formacion_musical': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Estudios musicales, cursos, talleres...'
            }),
            'nivel_experiencia': forms.Select(attrs={'class': 'form-select'}),
            'ubicacion': forms.Select(attrs={'class': 'form-select'}),
            'años_experiencia': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '80'
            }),
            'website_personal': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://tu-sitio-web.com'
            }),
            'soundcloud_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://soundcloud.com/tu-perfil'
            }),
            'youtube_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://youtube.com/tu-canal'
            }),
            'spotify_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://open.spotify.com/artist/...'
            }),
            'instagram_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://instagram.com/tu-usuario'
            }),
            'facebook_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://facebook.com/tu-pagina'
            }),
            'video_demo': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://youtube.com/watch?v=...'
            }),
            'disponible_para_gigs': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'tarifa_base': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '1000',
                'placeholder': '150000'
            }),
            'show_email': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'show_social_links': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'show_education': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'show_tarifa': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'show_telefono': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Obtener querysets para los campos M2M
        from .models import Instrumento, Genero
        
        self.fields['instrumento_principal'].queryset = Instrumento.objects.all()
        self.fields['instrumentos_secundarios'].queryset = Instrumento.objects.all()
        self.fields['generos_musicales'].queryset = Genero.objects.all()
        
        # Si estamos editando, prellenar los campos M2M
        if self.instance.pk:
            # Instrumento principal
            principal = self.instance.portafolio_instrumentos.filter(es_principal=True).first()
            if principal:
                self.fields['instrumento_principal'].initial = principal.instrumento
                
            # Instrumentos secundarios
            secundarios = self.instance.portafolio_instrumentos.filter(es_principal=False)
            self.fields['instrumentos_secundarios'].initial = [
                pi.instrumento for pi in secundarios
            ]
            
            # Géneros
            generos = self.instance.portafolio_generos.all()
            self.fields['generos_musicales'].initial = [
                pg.genero for pg in generos
            ]
    
    def clean_generos_musicales(self):
        generos = self.cleaned_data.get('generos_musicales')
        if generos and len(generos) > 8:
            raise ValidationError("No puedes seleccionar más de 8 géneros musicales.")
        return generos

    def clean_instrumentos_secundarios(self):
        instrumentos = self.cleaned_data.get('instrumentos_secundarios')
        if instrumentos and len(instrumentos) > 5:
            raise ValidationError("No puedes seleccionar más de 5 instrumentos secundarios.")
        return instrumentos
    
    def clean_años_experiencia(self):
        años = self.cleaned_data.get('años_experiencia')
        if años is not None and años > 80:
            raise ValidationError("Los años de experiencia no pueden exceder 80.")
        return años

    def save(self, commit=True):
        # Guardar el portafolio principal
        portafolio = super().save(commit=commit)
        
        if commit:
            # Limpiar relaciones existentes
            portafolio.portafolio_instrumentos.all().delete()
            portafolio.portafolio_generos.all().delete()
            
            # Manejar instrumento principal
            instrumento_principal = self.cleaned_data.get('instrumento_principal')
            if instrumento_principal:
                from .models import PortafolioInstrumento
                PortafolioInstrumento.objects.create(
                    portafolio=portafolio,
                    instrumento=instrumento_principal,
                    es_principal=True,
                    prioridad=1
                )
            
            # Manejar instrumentos secundarios
            instrumentos_secundarios = self.cleaned_data.get('instrumentos_secundarios')
            if instrumentos_secundarios:
                from .models import PortafolioInstrumento
                for i, instrumento in enumerate(instrumentos_secundarios, start=2):
                    PortafolioInstrumento.objects.create(
                        portafolio=portafolio,
                        instrumento=instrumento,
                        es_principal=False,
                        prioridad=i
                    )
            
            # Manejar géneros musicales
            generos = self.cleaned_data.get('generos_musicales')
            if generos:
                from .models import PortafolioGenero
                for i, genero in enumerate(generos, start=1):
                    PortafolioGenero.objects.create(
                        portafolio=portafolio,
                        genero=genero,
                        prioridad=i
                    )
        
        return portafolio


class PerfilEmpleadorForm(forms.ModelForm):
    first_name = forms.CharField(
        max_length=30,
        required=True,
        label='Nombre',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        label='Apellido',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    foto_perfil = forms.ImageField(
        required=False,
        label='Foto de perfil',
        widget=forms.FileInput(attrs={'class': 'form-control'}),
        validators=[validate_image_file],
        help_text='Imagen de perfil (máx. 5MB, mín. 100x100px, formatos: JPG, PNG, GIF)'
    )

    class Meta:
        model = PerfilEmpleador
        fields = [
            'nombre_organizacion', 'tipo_entidad', 'descripcion',
            'email_corporativo', 'telefono', 'contacto_alternativo',
            'ubicacion', 'direccion_completa', 'sitio_web',
            'linkedin_url', 'facebook_url', 'instagram_url',
            'año_fundacion', 'tamaño_organizacion'
        ]
        widgets = {
            'nombre_organizacion': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo_entidad': forms.Select(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'email_corporativo': forms.EmailInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'contacto_alternativo': forms.TextInput(attrs={'class': 'form-control'}),
            'ubicacion': forms.TextInput(attrs={'class': 'form-control'}),
            'direccion_completa': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'sitio_web': forms.URLInput(attrs={'class': 'form-control'}),
            'linkedin_url': forms.URLInput(attrs={'class': 'form-control'}),
            'facebook_url': forms.URLInput(attrs={'class': 'form-control'}),
            'instagram_url': forms.URLInput(attrs={'class': 'form-control'}),
            'año_fundacion': forms.NumberInput(attrs={'class': 'form-control'}),
            'tamaño_organizacion': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial = user.last_name
            self.fields['foto_perfil'].initial = user.foto_perfil

    def save(self, commit=True):
        perfil = super().save(commit=False)
        
        if commit:
            user = perfil.usuario
            user.first_name = self.cleaned_data['first_name']
            user.last_name = self.cleaned_data['last_name']
            
            if self.cleaned_data['foto_perfil']:
                user.foto_perfil = self.cleaned_data['foto_perfil']
            
            user.save()
            perfil.save()
        
        return perfil

    def clean_año_fundacion(self):
        año = self.cleaned_data.get('año_fundacion')
        if año and (año < 1800 or año > timezone.now().year):
            raise forms.ValidationError('El año de fundación debe estar entre 1800 y el año actual.')
        return año


# FORMULARIOS PARA OFERTAS LABORALES (Sprint 3)
class CrearOfertaLaboralForm(forms.ModelForm):
    """Formulario para crear ofertas laborales"""
    
    instrumentos = forms.ModelMultipleChoiceField(
        queryset=None,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=False,
        label='Instrumentos requeridos',
        help_text='Selecciona los instrumentos que necesitas para esta oferta'
    )
    
    generos = forms.ModelMultipleChoiceField(
        queryset=None,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=False,
        label='Géneros musicales preferidos',
        help_text='Selecciona los géneros musicales que mejor se adapten a la oferta'
    )

    class Meta:
        model = OfertaLaboral
        fields = [
            'titulo', 'descripcion', 'requisitos', 'tipo_contrato',
            'fecha_evento', 'duracion_estimada', 'presupuesto_minimo',
            'presupuesto_maximo', 'presupuesto_a_convenir', 'ubicacion',
            'nivel_experiencia_minimo', 'cupos_disponibles',
            'fecha_limite_postulacion', 'instrumentos', 'generos'
        ]
        
        widgets = {
            'titulo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Guitarrista para evento corporativo'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Describe en detalle la oportunidad laboral, el tipo de evento, ambiente de trabajo, etc.'
            }),
            'requisitos': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Especifica requisitos técnicos, experiencia mínima, equipos necesarios, etc.'
            }),
            'tipo_contrato': forms.Select(attrs={'class': 'form-select'}),
            'fecha_evento': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'duracion_estimada': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 3 horas, 2 días, 1 mes'
            }),
            'presupuesto_minimo': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '50000',
                'min': '0'
            }),
            'presupuesto_maximo': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '150000',
                'min': '0'
            }),
            'presupuesto_a_convenir': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'ubicacion': forms.Select(attrs={'class': 'form-select'}),
            'nivel_experiencia_minimo': forms.Select(attrs={'class': 'form-select'}),
            'cupos_disponibles': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'value': '1'
            }),
            'fecha_limite_postulacion': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
        }
        
        labels = {
            'titulo': 'Título de la oferta',
            'descripcion': 'Descripción detallada',
            'requisitos': 'Requisitos específicos',
            'tipo_contrato': 'Tipo de contrato',
            'fecha_evento': 'Fecha y hora del evento',
            'duracion_estimada': 'Duración estimada',
            'presupuesto_minimo': 'Presupuesto mínimo (CLP)',
            'presupuesto_maximo': 'Presupuesto máximo (CLP)',
            'presupuesto_a_convenir': 'Presupuesto a convenir',
            'ubicacion': 'Ubicación',
            'nivel_experiencia_minimo': 'Nivel de experiencia mínimo',
            'cupos_disponibles': 'Número de cupos disponibles',
            'fecha_limite_postulacion': 'Fecha límite para postular',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from .models import Instrumento, Genero, Ubicacion, NivelExperiencia
        
        self.fields['instrumentos'].queryset = Instrumento.objects.all().order_by('categoria', 'nombre')
        self.fields['generos'].queryset = Genero.objects.all().order_by('nombre')
        self.fields['ubicacion'].queryset = Ubicacion.objects.filter(activo=True).order_by('region', 'nombre')
        self.fields['nivel_experiencia_minimo'].queryset = NivelExperiencia.objects.all().order_by('orden')

    def clean(self):
        cleaned_data = super().clean()
        presupuesto_minimo = cleaned_data.get('presupuesto_minimo')
        presupuesto_maximo = cleaned_data.get('presupuesto_maximo')
        presupuesto_a_convenir = cleaned_data.get('presupuesto_a_convenir')
        fecha_evento = cleaned_data.get('fecha_evento')
        fecha_limite = cleaned_data.get('fecha_limite_postulacion')
        tipo_contrato = cleaned_data.get('tipo_contrato')

        if not presupuesto_a_convenir and not presupuesto_minimo and not presupuesto_maximo:
            raise forms.ValidationError(
                'Debes especificar un presupuesto o marcar "Presupuesto a convenir".'
            )

        if presupuesto_minimo and presupuesto_maximo:
            if presupuesto_minimo >= presupuesto_maximo:
                raise forms.ValidationError(
                    'El presupuesto mínimo debe ser menor al máximo.'
                )

        if fecha_evento and fecha_evento <= timezone.now():
            raise forms.ValidationError(
                'La fecha del evento debe ser en el futuro.'
            )

        if fecha_limite and fecha_limite <= timezone.now():
            raise forms.ValidationError(
                'La fecha límite de postulación debe ser en el futuro.'
            )

        if fecha_evento and fecha_limite and fecha_limite >= fecha_evento:
            raise forms.ValidationError(
                'La fecha límite de postulación debe ser anterior a la fecha del evento.'
            )

        if tipo_contrato == 'evento_unico' and not fecha_evento:
            raise forms.ValidationError(
                'Para eventos únicos debes especificar la fecha y hora del evento.'
            )

        return cleaned_data

    def save(self, commit=True, empleador=None):
        oferta = super().save(commit=False)
        
        if empleador:
            oferta.empleador = empleador
        
        if commit:
            oferta.save()
            
            # Guardar relaciones M2M con instrumentos
            instrumentos = self.cleaned_data.get('instrumentos', [])
            for i, instrumento in enumerate(instrumentos, 1):
                OfertaInstrumento.objects.create(
                    oferta_laboral=oferta,
                    instrumento=instrumento,
                    es_obligatorio=True,
                    prioridad=i
                )
            
            # Guardar relaciones M2M con géneros
            generos = self.cleaned_data.get('generos', [])
            for i, genero in enumerate(generos, 1):
                OfertaGenero.objects.create(
                    oferta_laboral=oferta,
                    genero=genero,
                    prioridad=i
                )
        
        return oferta


class PostulacionForm(forms.ModelForm):
    """Formulario para que músicos se postulen a ofertas laborales"""
    
    class Meta:
        model = Postulacion
        fields = ['mensaje_personalizado', 'tarifa_propuesta']
        
    mensaje_personalizado = forms.CharField(
        max_length=1000,
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Cuéntanos por qué eres el músico ideal para esta oferta... (opcional)',
            'maxlength': 1000
        }),
        label='Mensaje para el empleador',
        help_text='Opcional: Destaca tu experiencia relevante para esta oferta (máx. 1000 caracteres)'
    )
    
    tarifa_propuesta = forms.IntegerField(
        required=False,
        min_value=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: 150000',
            'min': 1
        }),
        label='Tu tarifa propuesta (CLP)',
        help_text='Opcional: Propón tu tarifa para esta oferta en pesos chilenos'
    )

    def __init__(self, *args, **kwargs):
        self.musico = kwargs.pop('musico', None)
        self.oferta = kwargs.pop('oferta', None)
        super().__init__(*args, **kwargs)
        
        # Validar que tenemos los datos necesarios
        if not self.musico or not self.oferta:
            raise ValueError("PostulacionForm requiere músico y oferta")

    def clean(self):
        cleaned_data = super().clean()
        
        # Validación: El usuario debe ser músico
        if self.musico.tipo_usuario != 'musico':
            raise forms.ValidationError('Solo los músicos pueden postularse a ofertas laborales.')
        
        # Validación: El músico debe tener portafolio
        if not hasattr(self.musico, 'portafolio'):
            raise forms.ValidationError(
                'Debes completar tu portafolio antes de postularte a ofertas laborales.'
            )
        
        # Validación: La oferta debe estar publicada
        if self.oferta.estado != 'publicada':
            raise forms.ValidationError('Esta oferta no está disponible para postulaciones.')
        
        # Validación: La oferta debe estar vigente
        if not self.oferta.esta_vigente():
            raise forms.ValidationError('Esta oferta ya no acepta postulaciones.')
        
        # Validación: No debe existir postulación previa
        if Postulacion.objects.filter(oferta_laboral=self.oferta, musico=self.musico).exists():
            raise forms.ValidationError('Ya te has postulado a esta oferta anteriormente.')
        
        # Validación: Verificar cupos disponibles
        postulaciones_aceptadas = Postulacion.objects.filter(
            oferta_laboral=self.oferta,
            estado='aceptada'
        ).count()
        
        if postulaciones_aceptadas >= self.oferta.cupos_disponibles:
            raise forms.ValidationError('Esta oferta ya no tiene cupos disponibles.')
        
        return cleaned_data

    def save(self, commit=True):
        postulacion = super().save(commit=False)
        postulacion.oferta_laboral = self.oferta
        postulacion.musico = self.musico
        postulacion.portafolio = self.musico.portafolio
        postulacion.tipo_postulacion = 'espontanea'
        postulacion.estado = 'pendiente'
        
        if commit:
            postulacion.save()
        
        return postulacion


# SISTEMA DE REFERENCIAS LABORALES (Sprint 4)

class SolicitudReferenciaForm(forms.ModelForm):
    """Formulario para que músicos soliciten referencias laborales"""
    
    class Meta:
        model = Testimonio
        fields = [
            'tipo', 'autor_nombre', 'autor_email', 'autor_cargo', 
            'autor_organizacion', 'proyecto_evento', 'fecha_inicio_colaboracion',
            'fecha_fin_colaboracion', 'duracion_colaboracion', 'mensaje_solicitud'
        ]
        
        widgets = {
            'tipo': forms.Select(
                attrs={
                    'class': 'form-select',
                },
                choices=[
                    ('referencia_laboral', 'Referencia laboral'),
                    ('testimonio_cliente', 'Testimonio de cliente'),
                ]
            ),
            'autor_nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: María González'
            }),
            'autor_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'maria@empresa.com'
            }),
            'autor_cargo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Directora de Eventos'
            }),
            'autor_organizacion': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Eventos Musicales SpA'
            }),
            'proyecto_evento': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Concierto de Año Nuevo 2024'
            }),
            'fecha_inicio_colaboracion': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'fecha_fin_colaboracion': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'duracion_colaboracion': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 3 meses, 1 año, evento único'
            }),
            'mensaje_solicitud': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Mensaje personalizado para el empleador...'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        self.portafolio = kwargs.pop('portafolio', None)
        super().__init__(*args, **kwargs)
        
        # Campos requeridos para referencias laborales
        self.fields['autor_email'].required = True
        self.fields['autor_nombre'].required = True
        self.fields['proyecto_evento'].required = True
        
        # Ayudas contextuales
        self.fields['autor_email'].help_text = 'Email válido para enviar la solicitud de referencia'
        self.fields['mensaje_solicitud'].help_text = 'Explica brevemente tu relación laboral y por qué solicitas esta referencia'
    
    def clean_autor_email(self):
        """Validar que el email sea válido"""
        email = self.cleaned_data.get('autor_email')
        if email:
            # Verificar que no sea el mismo email del músico
            if self.portafolio and email.lower() == self.portafolio.usuario.email.lower():
                raise ValidationError("No puedes solicitar una referencia a ti mismo.")
        return email
    
    def clean(self):
        """Validaciones cruzadas"""
        cleaned_data = super().clean()
        fecha_inicio = cleaned_data.get('fecha_inicio_colaboracion')
        fecha_fin = cleaned_data.get('fecha_fin_colaboracion')
        
        # Validar fechas lógicas
        if fecha_inicio and fecha_fin:
            if fecha_inicio > fecha_fin:
                raise ValidationError("La fecha de inicio debe ser anterior a la fecha de fin.")
            
            # No permitir fechas muy futuras
            if fecha_inicio > timezone.now().date():
                raise ValidationError("La fecha de inicio no puede ser futura.")
        
        return cleaned_data
    
    def save(self, commit=True):
        """Guardar con configuración automática para solicitud"""
        testimonio = super().save(commit=False)
        testimonio.portafolio = self.portafolio
        testimonio.estado = 'pendiente'
        testimonio.fecha_solicitud = timezone.now()
        
        if commit:
            testimonio.save()
        
        return testimonio


class ResponderReferenciaForm(forms.ModelForm):
    """Formulario para que empleadores respondan solicitudes de referencia"""
    
    class Meta:
        model = Testimonio
        fields = ['texto', 'verificado']
        
        widgets = {
            'texto': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Escribe tu referencia sobre el trabajo realizado por este músico...'
            }),
            'verificado': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['texto'].required = True
        self.fields['texto'].help_text = 'Escribe una referencia honesta sobre el trabajo del músico'
        self.fields['verificado'].help_text = 'Confirmo que esta referencia es veraz'
        self.fields['verificado'].label = 'Confirmo que esta referencia es veraz'
    
    def clean_texto(self):
        """Validar contenido del testimonio"""
        texto = self.cleaned_data.get('texto')
        if texto:
            if len(texto.strip()) < 50:
                raise ValidationError("La referencia debe tener al menos 50 caracteres.")
            if len(texto.strip()) > 500:
                raise ValidationError("La referencia no puede exceder 500 caracteres.")
        return texto
    
    def save(self, commit=True):
        """Guardar con estado aprobado"""
        testimonio = super().save(commit=False)
        testimonio.estado = 'aprobado'
        testimonio.fecha_respuesta = timezone.now()
        
        if commit:
            testimonio.save()
        
        return testimonio


class TestimonioDirectoForm(forms.ModelForm):
    """Formulario para agregar testimonios directamente (sin solicitud)"""
    
    class Meta:
        model = Testimonio
        fields = [
            'tipo', 'autor_nombre', 'autor_cargo', 'autor_organizacion',
            'texto', 'proyecto_evento', 'fecha_inicio_colaboracion',
            'fecha_fin_colaboracion', 'duracion_colaboracion'
        ]
        
        widgets = {
            'tipo': forms.Select(attrs={
                'class': 'form-select'
            }),
            'autor_nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del autor'
            }),
            'autor_cargo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Cargo/Posición'
            }),
            'autor_organizacion': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Empresa/Organización'
            }),
            'texto': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Testimonio...'
            }),
            'proyecto_evento': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Proyecto o evento'
            }),
            'fecha_inicio_colaboracion': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'fecha_fin_colaboracion': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'duracion_colaboracion': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Duración de la colaboración'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        self.portafolio = kwargs.pop('portafolio', None)
        super().__init__(*args, **kwargs)
        
        self.fields['autor_nombre'].required = True
        self.fields['texto'].required = True
    
    def save(self, commit=True):
        """Guardar como testimonio directo"""
        testimonio = super().save(commit=False)
        testimonio.portafolio = self.portafolio
        testimonio.estado = 'directo'
        
        if commit:
            testimonio.save()
        
        return testimonio


class ContactoMusicoForm(forms.ModelForm):
    """Formulario público del contacto mediado (ROADMAP §5).

    `sitio_web` es un honeypot: invisible para humanos (oculto en el template);
    si llega con contenido, el envío se descarta sin avisar al bot.
    """

    sitio_web = forms.CharField(
        required=False,
        label='Sitio web',
        widget=forms.TextInput(attrs={'autocomplete': 'off', 'tabindex': '-1'}),
    )

    class Meta:
        model = ContactoMusico
        fields = ['remitente_nombre', 'remitente_email', 'remitente_telefono',
                  'tipo_necesidad', 'mensaje']
        widgets = {
            'remitente_nombre': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Tu nombre'}),
            'remitente_email': forms.EmailInput(attrs={
                'class': 'form-control', 'placeholder': 'tu@correo.cl'}),
            'remitente_telefono': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': '+56 9 1234 5678 (opcional)'}),
            'tipo_necesidad': forms.Select(attrs={'class': 'form-select'}),
            'mensaje': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 5,
                'placeholder': 'Cuéntale qué necesitas: fecha, lugar, tipo de evento u oportunidad…'}),
        }

    def es_spam(self):
        """True si el honeypot vino con contenido (solo válido tras is_valid())."""
        return bool(self.cleaned_data.get('sitio_web'))


class AsistenteBioForm(forms.Form):
    """Formulario estructurado del asistente de IA (ROADMAP §8).

    Preguntas predefinidas, no chat libre: calidad consistente y sin espacio
    para que el modelo invente datos.
    """

    nombre = forms.CharField(
        label='Nombre artístico', max_length=120,
        widget=forms.TextInput(attrs={'class': 'form-control'}))
    generos = forms.CharField(
        label='Géneros musicales', max_length=200, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control',
                                      'placeholder': 'Ej: rock latino, funk, balada'}))
    formato = forms.CharField(
        label='Formato e instrumentos', max_length=200, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control',
                                      'placeholder': 'Ej: solista con guitarra y loop station'}))
    experiencia = forms.CharField(
        label='Años de experiencia', max_length=60, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 8 años'}))
    destacados = forms.CharField(
        label='Presentaciones o logros destacados', required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2,
                                     'placeholder': 'Ej: residencia los viernes en Bar X, telonero de Y en 2024'}))
    eventos = forms.CharField(
        label='Disponible para', max_length=200, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control',
                                      'placeholder': 'Ej: matrimonios, bares, eventos de empresa'}))
    unico = forms.CharField(
        label='¿Qué te hace único?', required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2,
                                     'placeholder': 'Ej: repertorio a pedido del público, set 100% en vivo sin pistas'}))
