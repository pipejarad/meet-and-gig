"""
Hallazgo A5 (auditoría 11-06-2026): _ip_del_request tomaba el PRIMER elemento
de X-Forwarded-For, que escribe el cliente — bastaba un header falso para
evadir el rate limit del contacto (y, tras A4, los de login y recuperación).
Detrás del proxy de Railway el valor confiable es el ÚLTIMO elemento, que
anexa el propio proxy.
"""
from django.test import RequestFactory, SimpleTestCase

from usuarios.views import _ip_del_request


class IpDelRequestTests(SimpleTestCase):

    def setUp(self):
        self.factory = RequestFactory()

    def _request(self, **meta):
        request = self.factory.get('/')
        request.META.update(meta)
        return request

    def test_toma_el_ultimo_elemento_de_xff(self):
        request = self._request(HTTP_X_FORWARDED_FOR='198.51.100.1, 203.0.113.7')
        self.assertEqual(_ip_del_request(request), '203.0.113.7')

    def test_un_xff_falsificado_por_el_cliente_no_oculta_la_ip_real(self):
        # El cliente puede mandar X-Forwarded-For con lo que quiera; el proxy
        # de Railway anexa al FINAL la IP de la conexión real.
        request = self._request(
            HTTP_X_FORWARDED_FOR='1.1.1.1, 2.2.2.2, 203.0.113.7'
        )
        self.assertEqual(_ip_del_request(request), '203.0.113.7')

    def test_sin_xff_usa_remote_addr(self):
        request = self._request()
        self.assertEqual(_ip_del_request(request), '127.0.0.1')

    def test_xff_malformado_cae_a_remote_addr(self):
        # GenericIPAddressField validaría el valor al guardar ContactoMusico:
        # basura en XFF no debe romper el guardado ni desactivar el límite.
        request = self._request(HTTP_X_FORWARDED_FOR='no-soy-una-ip')
        self.assertEqual(_ip_del_request(request), '127.0.0.1')

    def test_ipv6_es_aceptada(self):
        request = self._request(HTTP_X_FORWARDED_FOR='2001:db8::1')
        self.assertEqual(_ip_del_request(request), '2001:db8::1')
