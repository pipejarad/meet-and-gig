"""
Hallazgo C3 (auditoría 11-06-2026): contenido duplicado.

/perfil/<username>/ y /portafolio/<slug>/ eran dos páginas públicas para el
mismo músico y dividían el SEO. La canónica es el portafolio:
ver_perfil_musico pasa a ser un redirect 301 (si hay portafolio activo;
si no, 404 como hoy).
"""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from usuarios.models import Portafolio

Usuario = get_user_model()


class PerfilRedirectTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.musico = Usuario.objects.create_user(
            username='pedroguitarra',
            email='pedro@example.com',
            password='clave-segura-7',
            tipo_usuario='musico',
        )
        cls.portafolio = Portafolio.objects.create(usuario=cls.musico, activo=True)
        cls.url = reverse('ver_perfil_musico', kwargs={'username': 'pedroguitarra'})

    def test_redirige_301_al_portafolio(self):
        respuesta = self.client.get(self.url)
        self.assertEqual(respuesta.status_code, 301)
        self.assertEqual(
            respuesta.url,
            reverse('ver_portafolio', kwargs={'slug': self.portafolio.slug}),
        )

    def test_sin_portafolio_404(self):
        Usuario.objects.create_user(
            username='sinportafolio',
            email='sin@example.com',
            password='clave-segura-7',
            tipo_usuario='musico',
        )
        respuesta = self.client.get(
            reverse('ver_perfil_musico', kwargs={'username': 'sinportafolio'})
        )
        self.assertEqual(respuesta.status_code, 404)

    def test_portafolio_inactivo_404_para_visitantes(self):
        Portafolio.objects.filter(pk=self.portafolio.pk).update(activo=False)
        respuesta = self.client.get(self.url)
        self.assertEqual(respuesta.status_code, 404)

    def test_portafolio_inactivo_el_dueno_si_es_redirigido(self):
        # El dueño llega a su portafolio despublicado como vista previa
        Portafolio.objects.filter(pk=self.portafolio.pk).update(activo=False)
        self.client.force_login(self.musico)
        respuesta = self.client.get(self.url)
        self.assertEqual(respuesta.status_code, 301)

    def test_username_inexistente_404(self):
        respuesta = self.client.get(
            reverse('ver_perfil_musico', kwargs={'username': 'nadie'})
        )
        self.assertEqual(respuesta.status_code, 404)
