# Catálogos: una sola fuente de verdad (auditoría D2).
#
# Hasta ahora coexistían DOS sembradores divergentes: la migración 0019
# (10 instrumentos / 10 géneros, categoría 'Viento' en singular, género
# 'Electronic' en inglés) y el comando poblar_catalogos (catálogo rico
# chileno: ~56 instrumentos en 5 categorías, 15 géneros, categoría 'Vientos'
# en plural, 'Electrónica' en español, con 'Charango' duplicado). Correr
# ambos dejaba el catálogo mezclado y con duplicados semánticos.
#
# Esta migración consolida el catálogo rico como fuente única (el comando se
# elimina) y normaliza lo que la 0019 ya sembró en producción. Es segura
# sobre el estado limpio de prod (solo 0019) y sobre una BD fresca:
#  - renombra la categoría 'Viento' -> 'Vientos';
#  - consolida el género 'Electronic' -> 'Electrónica';
#  - añade los instrumentos/géneros del catálogo rico (get_or_create);
#  - elimina los instrumentos genéricos que el catálogo rico desglosa
#    (Guitarra, Bajo, Saxofón, Flauta, Teclado) SOLO si ningún portafolio
#    los referencia, para no perder datos de músicos existentes.
from django.db import migrations

# Instrumentos del catálogo rico (Charango solo en Cuerdas, sin duplicar).
INSTRUMENTOS = {
    'Cuerdas': [
        'Guitarra Clásica', 'Guitarra Eléctrica', 'Guitarra Acústica',
        'Bajo Eléctrico', 'Bajo Acústico', 'Violín', 'Viola', 'Violonchelo',
        'Contrabajo', 'Charango', 'Cuatro Venezolano', 'Mandolina',
        'Banjo', 'Ukulele',
    ],
    'Vientos': [
        'Flauta Traversa', 'Flauta Dulce', 'Clarinete', 'Saxofón Alto',
        'Saxofón Tenor', 'Trompeta', 'Trombón', 'Tuba', 'Corno Francés',
        'Quena', 'Zampoña', 'Armónica', 'Oboe', 'Fagot',
    ],
    'Percusión': [
        'Batería', 'Cajón Peruano', 'Congas', 'Bongos', 'Timbales',
        'Djembe', 'Bombo Legüero', 'Pandero', 'Maracas', 'Claves',
        'Güiro', 'Campanas Tubulares', 'Xilófono',
    ],
    'Teclas': [
        'Piano', 'Piano Eléctrico', 'Teclado Sintetizador', 'Órgano',
        'Acordeón', 'Bandoneón', 'Clavecín', 'Melódica',
    ],
    'Folclore Chileno': [
        'Guitarra Folclórica', 'Bombo Nortino', 'Kultrun', 'Trutruca',
        'Rabel', 'Tormento', 'Acordeón de Botones',
    ],
}

# Genéricos de la 0019 que el catálogo rico desglosa. Se eliminan para no
# duplicar (p. ej. 'Guitarra' junto a 'Guitarra Eléctrica'). Los genéricos
# que el catálogo rico mantiene idénticos (Violín, Violonchelo, Trompeta,
# Batería, Piano) NO están aquí.
GENERICOS_A_RETIRAR = ['Guitarra', 'Bajo', 'Saxofón', 'Flauta', 'Teclado']

GENEROS = [
    ('Rock', 'Género caracterizado por el uso de guitarras eléctricas, bajo y batería'),
    ('Pop', 'Música popular contemporánea con estructuras melódicas pegajosas'),
    ('Jazz', 'Género que se caracteriza por la improvisación y la complejidad armónica'),
    ('Blues', 'Género vocal e instrumental basado en el uso de notas de blues'),
    ('Folclore Chileno', 'Música tradicional de Chile: cueca, tonada y vals chileno'),
    ('Nueva Canción', 'Movimiento musical latinoamericano de contenido social y político'),
    ('Cumbia', 'Género musical y baile folclórico tradicional de Colombia'),
    ('Salsa', 'Género bailable resultante de la síntesis del son cubano'),
    ('Reggae', 'Género musical desarrollado por primera vez en Jamaica'),
    ('Electrónica', 'Música que emplea instrumentos electrónicos y tecnología'),
    ('Clásica', 'Música culta, clásica, docta o erudita'),
    ('Bolero', 'Género de origen cubano, muy popular en toda América Latina'),
    ('Tango', 'Género musical y danza nacida en Argentina y Uruguay'),
    ('Bossa Nova', 'Género brasileño derivado del samba e influido por el jazz'),
    ('Reggaetón', 'Género procedente de Puerto Rico de finales de los años 1990'),
]


def normalizar(apps, schema_editor):
    Instrumento = apps.get_model('usuarios', 'Instrumento')
    Genero = apps.get_model('usuarios', 'Genero')
    PortafolioInstrumento = apps.get_model('usuarios', 'PortafolioInstrumento')
    PortafolioGenero = apps.get_model('usuarios', 'PortafolioGenero')

    # 1. Normalizar categoría 'Viento' (0019) -> 'Vientos' (catálogo rico).
    Instrumento.objects.filter(categoria='Viento').update(categoria='Vientos')

    # 2. Sembrar el catálogo rico de instrumentos (idempotente).
    for categoria, nombres in INSTRUMENTOS.items():
        for nombre in nombres:
            Instrumento.objects.get_or_create(
                nombre=nombre, defaults={'categoria': categoria}
            )

    # 3. Retirar genéricos desglosados, solo si no los referencia un portafolio.
    for nombre in GENERICOS_A_RETIRAR:
        generico = Instrumento.objects.filter(nombre=nombre).first()
        if generico and not PortafolioInstrumento.objects.filter(instrumento=generico).exists():
            generico.delete()

    # 4. Consolidar el género 'Electronic' (0019) en 'Electrónica' (rico).
    electronic = Genero.objects.filter(nombre='Electronic').first()
    if electronic:
        electronica = Genero.objects.filter(nombre='Electrónica').exclude(pk=electronic.pk).first()
        if electronica:
            # Ya existe el canónico: mover referencias que no dupliquen y borrar.
            ya_tienen = set(
                PortafolioGenero.objects.filter(genero=electronica)
                .values_list('portafolio_id', flat=True)
            )
            PortafolioGenero.objects.filter(genero=electronic).exclude(
                portafolio_id__in=ya_tienen
            ).update(genero=electronica)
            PortafolioGenero.objects.filter(genero=electronic).delete()
            electronic.delete()
        else:
            electronic.nombre = 'Electrónica'
            electronic.save()

    # 5. Sembrar el catálogo rico de géneros (idempotente).
    for nombre, descripcion in GENEROS:
        Genero.objects.get_or_create(
            nombre=nombre, defaults={'descripcion': descripcion}
        )


def reversar(apps, schema_editor):
    # No-op: revertir no des-siembra catálogos (mismo criterio que la 0019).
    # Quitar los datos sembrados podría romper referencias de portafolios.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('usuarios', '0029_usuario_terminos_aceptados_en'),
    ]

    operations = [
        migrations.RunPython(normalizar, reversar),
    ]
