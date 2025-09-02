from django.core.management.base import BaseCommand
from core.models import Restaurante, Produto, OpcaoPersonalizacao, ItemPersonalizacao


class Command(BaseCommand):
    help = 'Popula personalizações para o produto Marmita Executiva'

    def handle(self, *args, **options):
        # Buscar o restaurante pizzaria-teste
        try:
            restaurante = Restaurante.objects.get(slug='pizzaria-teste')
        except Restaurante.DoesNotExist:
            self.stdout.write(self.style.ERROR('Restaurante "pizzaria-teste" não encontrado'))
            return

        # Buscar ou criar o produto Marmita Executiva
        produto, created = Produto.objects.get_or_create(
            restaurante=restaurante,
            slug='marmita-executiva',
            defaults={
                'nome': 'Marmitex Executiva',
                'descricao': '2 opções de misturas (assado/frito/cozido/massa). 4 opções de acompanhamentos (risoto/refogada/frita). Acompanha arroz, feijão e salada simples.',
                'preco': 35.00,
                'categoria': restaurante.categorias.first(),  # Usar a primeira categoria disponível
                'disponivel': True,
                'permite_observacoes': True,
                'tempo_preparo': 20,
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f'Produto "{produto.nome}" criado com sucesso'))
        else:
            self.stdout.write(f'Produto "{produto.nome}" já existe')

        # Limpar personalizações existentes
        produto.opcoes_personalizacao.all().delete()

        # Criar opção de personalização: MISTURAS / PROTEÍNAS
        opcao_proteinas = OpcaoPersonalizacao.objects.create(
            produto=produto,
            nome='MISTURAS / PROTEÍNAS',
            tipo='checkbox',  # Múltipla escolha como no exemplo
            obrigatorio=True,
            quantidade_minima=2,  # Mínimo 2 proteínas
            quantidade_maxima=3,  # Máximo 3 proteínas
            ordem=1
        )

        # Lista de proteínas/misturas do exemplo
        proteinas = [
            'ALMÔNDEGA',
            'BIFE À ROLE',
            'CHURRASCO BOVINO',
            'CORAÇÃO',
            'COSTELINHA SUÍNA FRITA',
            'TULIPINHA DE FRANGO',
            'DOBRADINHA',
            'FILÉ FRANGO GRELHADO',
            'FILÉ FRANGO EMPANADO',
            'FILÉ FRANGO À PARMEGIANA',
            'LASANHA BERINJELA',
            'LASANHA PRESUNTO E QUEIJO',
        ]

        # Criar itens de proteína
        for i, proteina in enumerate(proteinas, 1):
            ItemPersonalizacao.objects.create(
                opcao=opcao_proteinas,
                nome=proteina,
                preco_adicional=0.00,  # Sem custo adicional por ser parte do prato
                ordem=i
            )

        # Criar opção de acompanhamentos  
        opcao_acompanhamentos = OpcaoPersonalizacao.objects.create(
            produto=produto,
            nome='ACOMPANHAMENTOS',
            tipo='checkbox',  # Múltipla escolha
            obrigatorio=True,
            quantidade_minima=1,  # Mínimo 1 acompanhamento
            quantidade_maxima=4,  # Máximo 4 acompanhamentos
            ordem=2
        )

        # Lista de acompanhamentos
        acompanhamentos = [
            'RISOTO DE CAMARÃO',
            'BATATA REFOGADA',
            'BATATA FRITA',
            'LEGUMES REFOGADOS',
            'FAROFA',
            'POLENTA FRITA',
        ]

        # Criar itens de acompanhamento
        for i, acompanhamento in enumerate(acompanhamentos, 1):
            ItemPersonalizacao.objects.create(
                opcao=opcao_acompanhamentos,
                nome=acompanhamento,
                preco_adicional=0.00,  # Sem custo adicional
                ordem=i
            )

        # Criar opção de adicionais (opcionais)
        opcao_adicionais = OpcaoPersonalizacao.objects.create(
            produto=produto,
            nome='ADICIONAIS',
            tipo='checkbox',
            obrigatorio=False,
            quantidade_minima=0,  # Opcional
            quantidade_maxima=3,  # Máximo 3 adicionais
            ordem=3
        )

        # Lista de adicionais com preços
        adicionais = [
            ('OVO FRITO', 2.00),
            ('QUEIJO COALHO', 3.00),
            ('BACON', 4.00),
            ('VINAGRETE', 1.00),
            ('MOLHO ESPECIAL', 1.50),
        ]

        # Criar itens adicionais
        for i, (adicional, preco) in enumerate(adicionais, 1):
            ItemPersonalizacao.objects.create(
                opcao=opcao_adicionais,
                nome=adicional,
                preco_adicional=preco,
                ordem=i
            )

        self.stdout.write(
            self.style.SUCCESS(
                f'Personalizações criadas com sucesso para "{produto.nome}":\n'
                f'- {opcao_proteinas.itens.count()} proteínas/misturas\n'
                f'- {opcao_acompanhamentos.itens.count()} acompanhamentos\n'
                f'- {opcao_adicionais.itens.count()} adicionais'
            )
        )