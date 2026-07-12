"""
Hallazgo D2 (auditoría 11-06-2026): catálogo normalizado de fuente única.

Blinda el resultado de la migración 0030: si alguien reintrodujera el
comando poblar_catalogos divergente o rompiera la normalización, estos tests
fallan. Verifican el estado del catálogo sembrado por las migraciones de
datos (corren sobre la BD de test, que aplicó todas las migraciones).
"""
from django.test import TestCase

from usuarios.models import Genero, Instrumento, Ubicacion


class CatalogoNormalizadoTests(TestCase):

    def test_la_categoria_de_vientos_esta_en_plural(self):
        self.assertFalse(Instrumento.objects.filter(categoria='Viento').exists())
        self.assertTrue(Instrumento.objects.filter(categoria='Vientos').exists())

    def test_el_genero_electronica_esta_en_espanol(self):
        self.assertFalse(Genero.objects.filter(nombre='Electronic').exists())
        self.assertTrue(Genero.objects.filter(nombre='Electrónica').exists())

    def test_charango_no_esta_duplicado(self):
        self.assertEqual(Instrumento.objects.filter(nombre='Charango').count(), 1)

    def test_no_quedan_genericos_que_el_catalogo_desglosa(self):
        genericos = ['Guitarra', 'Bajo', 'Saxofón', 'Flauta', 'Teclado']
        self.assertFalse(Instrumento.objects.filter(nombre__in=genericos).exists())

    def test_catalogo_rico_sembrado(self):
        # Catálogo chileno: las 5 categorías y muestras representativas.
        categorias = set(Instrumento.objects.values_list('categoria', flat=True))
        self.assertEqual(
            categorias,
            {'Cuerdas', 'Vientos', 'Percusión', 'Teclas', 'Folclore Chileno'},
        )
        for nombre in ['Guitarra Eléctrica', 'Cajón Peruano', 'Charango', 'Quena']:
            self.assertTrue(Instrumento.objects.filter(nombre=nombre).exists(), nombre)
        for nombre in ['Folclore Chileno', 'Cumbia', 'Reggaetón']:
            self.assertTrue(Genero.objects.filter(nombre=nombre).exists(), nombre)

    def test_ubicaciones_completas_de_chile(self):
        # Las 80 comunas de la 0019 (las 16 regiones), no las 16 del comando.
        self.assertEqual(Ubicacion.objects.count(), 80)
