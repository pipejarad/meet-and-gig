"""Sitemaps de la vitrina (auditoría C4).

Cubre el canal de adquisición de la v1: home, directorio de músicos y todos
los portafolios activos. Los despublicados (activo=False) no existen para
los buscadores, igual que en las vistas (B3/C3).
"""
from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from .models import Portafolio


class EstaticasSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.6

    def items(self):
        return ['inicio', 'listar_portafolios']

    def location(self, item):
        return reverse(item)


class PortafoliosSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.8

    def items(self):
        return Portafolio.objects.filter(activo=True).order_by('pk')

    def lastmod(self, portafolio):
        return portafolio.fecha_actualizacion

    def location(self, portafolio):
        return reverse('ver_portafolio', kwargs={'slug': portafolio.slug})


SITEMAPS = {
    'estaticas': EstaticasSitemap,
    'portafolios': PortafoliosSitemap,
}
