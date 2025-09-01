from django.core.management.base import BaseCommand
from core.models import Produto, OpcaoPersonalizacao, ItemPersonalizacao, Restaurante
import uuid

class Command(BaseCommand):
    help = 'Popula o banco com opções de personalização para produtos de teste'

    def handle(self, *args, **options):
        self.stdout.write('Iniciando população de dados de personalização...')
        
        # Buscar restaurante de teste
        restaurante = Restaurante.objects.filter(slug='pizzaria-teste').first()
        if not restaurante:
            self.stdout.write(
                self.style.ERROR('Restaurante "pizzaria-teste" não encontrado!')
            )
            return
        
        # Buscar produto existente
        produto_pizza = Produto.objects.filter(
            restaurante=restaurante,
            slug='pizza-margherita'
        ).first()
        
        if produto_pizza:
            self.stdout.write(f'Configurando personalização para: {produto_pizza.nome}')
            self.configurar_pizza(produto_pizza)
        
        # Criar produto de marmita executiva como exemplo
        self.criar_marmita_executiva(restaurante)
        
        self.stdout.write(
            self.style.SUCCESS('Dados de personalização criados com sucesso!')
        )
    
    def configurar_pizza(self, produto):
        """Configura opções de personalização para pizza"""
        
        # Limpar opções existentes
        produto.opcoes_personalizacao.all().delete()
        
        # Opção 1: Tamanho (obrigatório)
        opcao_tamanho = OpcaoPersonalizacao.objects.create(
            produto=produto,
            nome='Tamanho',
            tipo='radio',
            obrigatorio=True,
            ordem=1
        )
        
        ItemPersonalizacao.objects.create(
            opcao=opcao_tamanho,
            nome='Pequena (25cm)',
            preco_adicional=0.00,
            ordem=1
        )
        
        ItemPersonalizacao.objects.create(
            opcao=opcao_tamanho,
            nome='Média (30cm)',
            preco_adicional=5.00,
            ordem=2
        )
        
        ItemPersonalizacao.objects.create(
            opcao=opcao_tamanho,
            nome='Grande (35cm)',
            preco_adicional=10.00,
            ordem=3
        )
        
        # Opção 2: Borda (opcional)
        opcao_borda = OpcaoPersonalizacao.objects.create(
            produto=produto,
            nome='Borda',
            tipo='radio',
            obrigatorio=False,
            ordem=2
        )
        
        ItemPersonalizacao.objects.create(
            opcao=opcao_borda,
            nome='Sem borda',
            preco_adicional=0.00,
            ordem=1
        )
        
        ItemPersonalizacao.objects.create(
            opcao=opcao_borda,
            nome='Borda de Catupiry',
            preco_adicional=4.00,
            ordem=2
        )
        
        ItemPersonalizacao.objects.create(
            opcao=opcao_borda,
            nome='Borda de Chocolate',
            preco_adicional=3.50,
            ordem=3
        )
        
        # Opção 3: Adicionais (múltipla escolha)
        opcao_adicionais = OpcaoPersonalizacao.objects.create(
            produto=produto,
            nome='Ingredientes Extras',
            tipo='checkbox',
            obrigatorio=False,
            ordem=3
        )
        
        ingredientes = [
            ('Queijo Extra', 3.00),
            ('Azeitona', 2.00),
            ('Tomate Cherry', 2.50),
            ('Manjericão', 1.50),
            ('Oregano', 0.50),
            ('Parmesão', 3.50)
        ]
        
        for i, (nome, preco) in enumerate(ingredientes, 1):
            ItemPersonalizacao.objects.create(
                opcao=opcao_adicionais,
                nome=nome,
                preco_adicional=preco,
                ordem=i
            )
    
    def criar_marmita_executiva(self, restaurante):
        """Cria produto de marmita executiva com opções de personalização"""
        
        # Buscar categoria ou criar uma
        from core.models import Categoria
        categoria, created = Categoria.objects.get_or_create(
            restaurante=restaurante,
            slug='marmitas',
            defaults={
                'nome': 'Marmitas',
                'descricao': 'Marmitas executivas e tradicionais',
                'ordem': 2
            }
        )
        
        # Criar produto de marmita
        marmita = Produto.objects.create(
            restaurante=restaurante,
            categoria=categoria,
            nome='Marmita Executiva',
            slug='marmita-executiva',
            descricao='Marmita completa com arroz, feijão, salada e sua escolha de mistura e acompanhamentos.',
            preco=18.50,
            destaque=True,
            tempo_preparo=20,
            ingredientes='Arroz, feijão, salada, mistura e acompanhamento',
            permite_observacoes=True
        )
        
        self.stdout.write(f'Produto criado: {marmita.nome}')
        
        # Opção 1: Mistura (obrigatório)
        opcao_mistura = OpcaoPersonalizacao.objects.create(
            produto=marmita,
            nome='Escolha a Mistura',
            tipo='radio',
            obrigatorio=True,
            ordem=1
        )
        
        misturas = [
            ('Bife Acebolado', 0.00),
            ('Frango Grelhado', 0.00),
            ('Peixe Grelhado', 2.00),
            ('Linguiça Calabresa', 0.00),
            ('Costela de Porco', 4.00),
            ('Filé de Frango à Parmegiana', 3.00)
        ]
        
        for i, (nome, preco) in enumerate(misturas, 1):
            ItemPersonalizacao.objects.create(
                opcao=opcao_mistura,
                nome=nome,
                preco_adicional=preco,
                ordem=i
            )
        
        # Opção 2: Acompanhamentos (múltipla escolha)
        opcao_acompanhamentos = OpcaoPersonalizacao.objects.create(
            produto=marmita,
            nome='Acompanhamentos',
            tipo='checkbox',
            obrigatorio=False,
            ordem=2
        )
        
        acompanhamentos = [
            ('Batata Frita', 2.50),
            ('Mandioca Frita', 2.00),
            ('Purê de Batata', 1.50),
            ('Farofa', 1.00),
            ('Vinagrete', 1.00),
            ('Ovo Frito', 1.50)
        ]
        
        for i, (nome, preco) in enumerate(acompanhamentos, 1):
            ItemPersonalizacao.objects.create(
                opcao=opcao_acompanhamentos,
                nome=nome,
                preco_adicional=preco,
                ordem=i
            )
        
        # Opção 3: Tamanho da porção (obrigatório)
        opcao_porcao = OpcaoPersonalizacao.objects.create(
            produto=marmita,
            nome='Tamanho da Porção',
            tipo='select',
            obrigatorio=True,
            ordem=3
        )
        
        ItemPersonalizacao.objects.create(
            opcao=opcao_porcao,
            nome='Porção Normal',
            preco_adicional=0.00,
            ordem=1
        )
        
        ItemPersonalizacao.objects.create(
            opcao=opcao_porcao,
            nome='Porção Grande',
            preco_adicional=4.00,
            ordem=2
        )
        
        ItemPersonalizacao.objects.create(
            opcao=opcao_porcao,
            nome='Porção Família (2 pessoas)',
            preco_adicional=12.00,
            ordem=3
        )
        
        # Criar mais alguns produtos exemplo
        self.criar_bebidas(restaurante)
    
    def criar_bebidas(self, restaurante):
        """Cria categoria e produtos de bebidas"""
        
        from core.models import Categoria
        categoria, created = Categoria.objects.get_or_create(
            restaurante=restaurante,
            slug='bebidas',
            defaults={
                'nome': 'Bebidas',
                'descricao': 'Refrigerantes, sucos e bebidas geladas',
                'ordem': 3
            }
        )
        
        # Refrigerante com opções de tamanho
        refrigerante = Produto.objects.create(
            restaurante=restaurante,
            categoria=categoria,
            nome='Refrigerante',
            slug='refrigerante',
            descricao='Refrigerante gelado em diversas opções de sabor.',
            preco=4.50,
            tempo_preparo=2
        )
        
        # Opção sabor
        opcao_sabor = OpcaoPersonalizacao.objects.create(
            produto=refrigerante,
            nome='Sabor',
            tipo='select',
            obrigatorio=True,
            ordem=1
        )
        
        sabores = ['Coca-Cola', 'Pepsi', 'Guaraná', 'Fanta Laranja', 'Fanta Uva', 'Sprite']
        for i, sabor in enumerate(sabores, 1):
            ItemPersonalizacao.objects.create(
                opcao=opcao_sabor,
                nome=sabor,
                preco_adicional=0.00,
                ordem=i
            )
        
        # Opção tamanho
        opcao_tamanho_bebida = OpcaoPersonalizacao.objects.create(
            produto=refrigerante,
            nome='Tamanho',
            tipo='radio',
            obrigatorio=True,
            ordem=2
        )
        
        ItemPersonalizacao.objects.create(
            opcao=opcao_tamanho_bebida,
            nome='Lata 350ml',
            preco_adicional=0.00,
            ordem=1
        )
        
        ItemPersonalizacao.objects.create(
            opcao=opcao_tamanho_bebida,
            nome='Garrafa 600ml',
            preco_adicional=1.50,
            ordem=2
        )
        
        ItemPersonalizacao.objects.create(
            opcao=opcao_tamanho_bebida,
            nome='Garrafa 2L',
            preco_adicional=4.00,
            ordem=3
        )
        
        self.stdout.write(f'Categoria e produtos de bebidas criados!')