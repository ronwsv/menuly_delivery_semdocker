from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core.models import Restaurante, Plano, Categoria, Produto, Pedido
from decimal import Decimal

User = get_user_model()

class Command(BaseCommand):
    help = 'Cria dados de teste para demonstrar o sistema de entrega'

    def handle(self, *args, **options):
        # Criar usuário lojista
        lojista_username = 'lojista_teste'
        lojista_password = 'senha123'
        
        if User.objects.filter(username=lojista_username).exists():
            self.stdout.write(
                self.style.WARNING(f'Usuário lojista {lojista_username} já existe')
            )
            lojista = User.objects.get(username=lojista_username)
        else:
            lojista = User.objects.create_user(
                username=lojista_username,
                password=lojista_password,
                first_name='Maria',
                last_name='Santos',
                email='maria.lojista@menuly.com',
                celular='11988776655',
                tipo_usuario='lojista'
            )
            self.stdout.write(
                self.style.SUCCESS(f'Usuário lojista {lojista_username} criado')
            )

        # Criar cliente
        cliente_username = 'cliente_teste'
        cliente_password = 'senha123'
        
        if User.objects.filter(username=cliente_username).exists():
            cliente = User.objects.get(username=cliente_username)
        else:
            cliente = User.objects.create_user(
                username=cliente_username,
                password=cliente_password,
                first_name='João',
                last_name='Cliente',
                email='joao.cliente@menuly.com',
                celular='11977665544',
                tipo_usuario='cliente'
            )
            self.stdout.write(
                self.style.SUCCESS(f'Usuário cliente {cliente_username} criado')
            )

        # Criar plano se não existe
        plano_pro, created = Plano.objects.get_or_create(
            nome='pro',
            defaults={
                'titulo': 'Plano Pro',
                'descricao': 'Plano completo para restaurantes',
                'preco_mensal': Decimal('99.90'),
                'permite_area_entregador': True,
                'ativo': True
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('Plano Pro criado'))

        # Criar restaurante
        restaurante_nome = 'Pizzaria Teste'
        try:
            restaurante = Restaurante.objects.get(nome=restaurante_nome)
            self.stdout.write(
                self.style.WARNING(f'Restaurante {restaurante_nome} já existe')
            )
        except Restaurante.DoesNotExist:
            restaurante = Restaurante.objects.create(
                nome=restaurante_nome,
                slug='pizzaria-teste',
                descricao='Restaurante de teste para demonstrar entregas',
                proprietario=lojista,
                plano=plano_pro,
                telefone='11999888777',
                email='contato@pizzariateste.com',
                cep='01310-100',
                logradouro='Av. Paulista',
                numero='1000',
                bairro='Bela Vista',
                cidade='São Paulo',
                estado='SP',
                tipo_servico='ambos',
                taxa_entrega=Decimal('5.00'),
                valor_minimo_pedido=Decimal('20.00'),
                status='ativo'
            )
            self.stdout.write(
                self.style.SUCCESS(f'Restaurante {restaurante_nome} criado')
            )

        # Criar categoria
        categoria, created = Categoria.objects.get_or_create(
            restaurante=restaurante,
            nome='Pizzas',
            defaults={
                'slug': 'pizzas',
                'descricao': 'Pizzas saborosas',
                'ordem': 1
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('Categoria Pizzas criada'))

        # Criar produto
        produto, created = Produto.objects.get_or_create(
            restaurante=restaurante,
            categoria=categoria,
            nome='Pizza Margherita',
            defaults={
                'slug': 'pizza-margherita',
                'descricao': 'Pizza com molho de tomate, mussarela e manjericão',
                'preco': Decimal('32.90'),
                'disponivel': True,
                'ordem': 1
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('Produto Pizza Margherita criado'))

        # Criar pedido de teste
        pedido_numero = 'TEST001'
        try:
            pedido = Pedido.objects.get(numero=pedido_numero)
            self.stdout.write(
                self.style.WARNING(f'Pedido {pedido_numero} já existe')
            )
        except Pedido.DoesNotExist:
            pedido = Pedido.objects.create(
                numero=pedido_numero,
                restaurante=restaurante,
                cliente=cliente,
                cliente_nome='João Cliente',
                cliente_celular='11977665544',
                cliente_email='joao.cliente@menuly.com',
                endereco_cep='04038-001',
                endereco_logradouro='Rua Vergueiro',
                endereco_numero='3185',
                endereco_bairro='Vila Mariana',
                endereco_cidade='São Paulo',
                endereco_estado='SP',
                tipo_entrega='delivery',
                forma_pagamento='dinheiro',
                subtotal=Decimal('32.90'),
                taxa_entrega=Decimal('5.00'),
                valor_entrega=Decimal('8.00'),  # Valor pago ao entregador
                total=Decimal('37.90'),
                status='aguardando_entregador',
                observacoes='Pedido de teste para demonstração'
            )
            
            # Criar item do pedido
            from core.models import ItemPedido
            ItemPedido.objects.create(
                pedido=pedido,
                produto=produto,
                produto_nome=produto.nome,
                produto_preco=produto.preco,
                quantidade=1,
                preco_unitario=produto.preco,
                subtotal=produto.preco
            )
            
            self.stdout.write(
                self.style.SUCCESS(f'Pedido {pedido_numero} criado com status "aguardando_entregador"')
            )

        self.stdout.write(
            self.style.SUCCESS(
                f'\n=== DADOS DE TESTE CRIADOS ===\n'
                f'🏪 Lojista: {lojista_username} / {lojista_password}\n'
                f'👤 Cliente: {cliente_username} / {cliente_password}\n'
                f'🏍️ Entregador: entregador_teste / senha123\n'
                f'🍕 Restaurante: {restaurante_nome}\n'
                f'📦 Pedido: {pedido_numero} (Status: aguardando_entregador)\n'
                f'\n🌐 URLs de teste:\n'
                f'- Login Entregador: http://localhost:8080/entregador/login/\n'
                f'- Login Lojista: http://localhost:8080/admin-loja/login/\n'
                f'- API Pedidos Disponíveis: http://localhost:8080/api/pedidos/disponiveis/\n'
                f'- Django Admin: http://localhost:8080/admin/\n'
            )
        )