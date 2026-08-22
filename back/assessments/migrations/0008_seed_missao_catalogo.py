from django.db import migrations


INITIAL_MISSIONS = [
    {
        'titulo': 'Construir um projeto demonstrável',
        'descricao': 'Crie uma entrega pequena e pública que prove uma habilidade relevante para seu objetivo.',
        'area_relacionada': 'Portfólio e carreira',
        'competencias_desenvolvidas': ['Projetos e Prova Real', 'Diferenciação'],
        'dificuldade': 'media',
    },
    {
        'titulo': 'Mapear três referências da sua área',
        'descricao': 'Analise três profissionais ou organizações e registre padrões de atuação que você pode aplicar.',
        'area_relacionada': 'Estratégia profissional',
        'competencias_desenvolvidas': ['Visão Estratégica', 'Base Acadêmica'],
        'dificuldade': 'facil',
    },
    {
        'titulo': 'Publicar uma análise autoral',
        'descricao': 'Escreva uma análise curta sobre um problema real da sua área e publique com seu nome.',
        'area_relacionada': 'Comunicação e posicionamento',
        'competencias_desenvolvidas': ['Posicionamento e Networking', 'Comunicação Social'],
        'dificuldade': 'dificil',
    },
]


def seed_missions(apps, schema_editor):
    Missao = apps.get_model('assessments', 'Missao')
    for mission in INITIAL_MISSIONS:
        Missao.objects.get_or_create(
            titulo=mission['titulo'],
            perfil=None,
            defaults=mission,
        )


def remove_seed_missions(apps, schema_editor):
    Missao = apps.get_model('assessments', 'Missao')
    titles = [mission['titulo'] for mission in INITIAL_MISSIONS]
    Missao.objects.filter(titulo__in=titles, perfil=None).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('assessments', '0007_missao_area_relacionada_and_more'),
    ]

    operations = [
        migrations.RunPython(seed_missions, remove_seed_missions),
    ]
