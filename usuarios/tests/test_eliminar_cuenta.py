"""
Hallazgo B3 (auditoría 11-06-2026): eliminación de cuenta (Ley 21.719).

Soft-delete aceptable en v1, pero el dato personal debe quedar irreconocible:
is_active=False + anonimización (email → placeholder único, nombre, teléfono,
foto) y portafolio despublicado (activo=False). El derecho de supresión llega
hasta el contenido del portafolio: biografía, formación, enlaces a las cuentas
del músico y los archivos de multimedia (que sobreviven a la despublicación).
"""
import io
import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from usuarios.models import Multimedia, PerfilMusico, Portafolio

Usuario = get_user_model()


def _imagen_valida(nombre='multimedia.png'):
    """PNG mínimo válido para poblar un ImageField en los tests."""
    buffer = io.BytesIO()
    Image.new('RGB', (10, 10), 'blue').save(buffer, format='PNG')
    buffer.seek(0)
    return SimpleUploadedFile(nombre, buffer.read(), content_type='image/png')

PASSWORD = 'clave-segura-musico-7'


class EliminarCuentaTests(TestCase):

    def setUp(self):
        # OJO: el username no puede ser 'musico' — su slug chocaría con la
        # ruta reservada portafolio/musico/ (colisión anotada en ROADMAP §9).
        self.usuario = Usuario.objects.create_user(
            username='pedroguitarra',
            email='musico@example.com',
            password=PASSWORD,
            tipo_usuario='musico',
            first_name='Pedro',
            last_name='Pérez',
        )
        PerfilMusico.objects.create(
            usuario=self.usuario,
            telefono='+56911112222',
            direccion='Calle Falsa 123',
        )
        self.portafolio = Portafolio.objects.create(usuario=self.usuario, activo=True)
        self.url = reverse('eliminar_cuenta')

    def _login(self):
        # force_login y no client.login(): este último llama authenticate sin
        # request, que el backend de axes (A4) no acepta.
        self.client.force_login(self.usuario)

    def test_requiere_login(self):
        respuesta = self.client.get(self.url)
        self.assertEqual(respuesta.status_code, 302)
        self.assertIn(reverse('login'), respuesta.url)

    def test_get_muestra_confirmacion_sin_eliminar(self):
        self._login()
        respuesta = self.client.get(self.url)
        self.assertEqual(respuesta.status_code, 200)
        self.usuario.refresh_from_db()
        self.assertTrue(self.usuario.is_active)

    def test_post_desactiva_y_anonimiza(self):
        self._login()
        respuesta = self.client.post(self.url)
        self.assertEqual(respuesta.status_code, 302)

        self.usuario.refresh_from_db()
        self.assertFalse(self.usuario.is_active)
        self.assertNotIn('musico@example.com', self.usuario.email)
        self.assertNotEqual(self.usuario.username, 'pedroguitarra')
        self.assertEqual(self.usuario.first_name, '')
        self.assertEqual(self.usuario.last_name, '')
        self.assertFalse(self.usuario.has_usable_password())

        perfil = self.usuario.perfil_musico
        self.assertEqual(perfil.telefono, '')
        self.assertEqual(perfil.direccion, '')
        self.assertIsNone(perfil.fecha_nacimiento)

        self.portafolio.refresh_from_db()
        self.assertFalse(self.portafolio.activo)

    def test_tras_eliminar_no_se_puede_volver_a_entrar(self):
        self._login()
        self.client.post(self.url)

        # La sesión actual quedó cerrada…
        respuesta = self.client.get(reverse('eliminar_cuenta'))
        self.assertEqual(respuesta.status_code, 302)
        # …y las credenciales antiguas ya no sirven (200 = vuelve al form
        # con error, sin redirect de login exitoso)
        respuesta = self.client.post(
            reverse('login'),
            {'username': 'musico@example.com', 'password': PASSWORD},
        )
        self.assertEqual(respuesta.status_code, 200)

    def test_el_portafolio_publico_desaparece(self):
        slug = self.portafolio.slug
        self._login()
        self.client.post(self.url)
        respuesta = self.client.get(reverse('ver_portafolio', kwargs={'slug': slug}))
        self.assertEqual(respuesta.status_code, 404)

    def test_post_borra_el_contenido_personal_del_portafolio(self):
        # Biografía, formación y enlaces a las cuentas del músico son dato
        # personal: despublicar no basta, hay que borrarlos (Ley 21.719).
        self.portafolio.biografia = 'Soy Pedro, toco cueca en bares de Valparaíso.'
        self.portafolio.formacion_musical = 'Conservatorio de la Universidad de Chile'
        self.portafolio.instagram_url = 'https://instagram.com/pedroguitarra'
        self.portafolio.youtube_url = 'https://youtube.com/@pedroguitarra'
        self.portafolio.website_personal = 'https://pedroguitarra.cl'
        self.portafolio.save()

        self._login()
        self.client.post(self.url)

        self.portafolio.refresh_from_db()
        self.assertEqual(self.portafolio.biografia, '')
        self.assertEqual(self.portafolio.formacion_musical, '')
        self.assertEqual(self.portafolio.instagram_url, '')
        self.assertEqual(self.portafolio.youtube_url, '')
        self.assertEqual(self.portafolio.website_personal, '')

    def test_post_elimina_los_archivos_de_multimedia(self):
        media_tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, media_tmp, ignore_errors=True)
        with override_settings(MEDIA_ROOT=media_tmp):
            media = Multimedia.objects.create(
                portafolio=self.portafolio,
                tipo='imagen',
                titulo='En vivo',
                imagen=_imagen_valida(),
            )
            ruta = media.imagen.name
            self.assertTrue(default_storage.exists(ruta))

            self._login()
            self.client.post(self.url)

            # El registro se va y, con él, el archivo del almacenamiento.
            self.assertFalse(
                Multimedia.objects.filter(portafolio=self.portafolio).exists()
            )
            self.assertFalse(default_storage.exists(ruta))

    def test_el_email_queda_libre_para_un_registro_nuevo(self):
        # Derecho de supresión bien hecho: anonimizar libera el email para
        # que la misma persona pueda registrarse de nuevo si quiere.
        self._login()
        self.client.post(self.url)
        respuesta = self.client.post(reverse('registro'), {
            'username': 'musicodenuevo',
            'email': 'musico@example.com',
            'password1': 'clave-segura-nueva-7',
            'password2': 'clave-segura-nueva-7',
            'acepta_terminos': 'on',
        })
        self.assertEqual(respuesta.status_code, 302)
        self.assertTrue(Usuario.objects.filter(email='musico@example.com').exists())
