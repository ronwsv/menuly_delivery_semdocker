"""
Comando para criar pedidos de teste para validar o fluxo de pedidos
e o sistema de arquivamento após 24 horas.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from core.models import Pedido, Restaurante, Categoria, Produto
import uuid
import random


class Command(BaseCommand):
    help = 'Cria pedidos de teste para validar o fluxo e arquivamento'

    def add_arguments(self, parser):
        parser.add_argument(
            '--quantidade',
            type=int,
            default=10,
            help='Quantidade de pedidos para criar (padrão: 10)',
        )
        parser.add_argument(
            '--antigos',
            action='store_true',
            help='Criar pedidos antigos (mais de 24h) para testar arquivamento',
        )

    def handle(self, *args, **options):
        quantidade = options['quantidade']
        criar_antigos = options['antigos']
        
        # Buscar um restaurante existente
        restaurante = Restaurante.objects.first()
        if not restaurante:
            self.stdout.write(
                self.style.ERROR('Nenhum restaurante encontrado. Execute o comando popular_dados primeiro.')
            )
            return
        
        # Status possíveis
        status_choices = ['pendente', 'novo', 'confirmado', 'preparo', 'preparando', 'pronto', 'entrega', 'em_entrega', 'finalizado']
        
        # Nomes de clientes fictícios
        nomes_clientes = [
            'João Silva', 'Maria Santos', 'Pedro Oliveira', 'Ana Costa', 'Carlos Souza',
            'Lucia Ferreira', 'Roberto Lima', 'Patricia Alves', 'Fernando Rocha', 'Sandra Mendes'
        ]
        
        # Telefones fictícios
        telefones = [
            '(11) 99999-0001', '(11) 99999-0002', '(11) 99999-0003', '(11) 99999-0004',
            '(11) 99999-0005', '(11) 99999-0006', '(11) 99999-0007', '(11) 99999-0008',
            '(11) 99999-0009', '(11) 99999-0010'
        ]
        
        pedidos_criados = 0
        
        for i in range(quantidade):
            # Definir data de criação
            if criar_antigos:
                # Criar pedidos entre 25-72 horas atrás (arquivados)
                horas_atras = random.randint(25, 72)
                data_criacao = timezone.now() - timedelta(hours=horas_atras)
            else:
                # Criar pedidos nas últimas 23 horas (ativos)
                horas_atras = random.randint(1, 23)
                data_criacao = timezone.now() - timedelta(hours=horas_atras)
            
            # Dados do pedido
            numero_pedido = f"PD{random.randint(10000, 99999)}"
            cliente_nome = random.choice(nomes_clientes)
            cliente_telefone = random.choice(telefones)
            status = random.choice(status_choices)
            total = round(random.uniform(25.00, 150.00), 2)
            
            # Tipo de entrega e endereço
            tipo_entrega = random.choice(['delivery', 'balcao'])
            
            # Criar pedido
            pedido_data = {
                'id': uuid.uuid4(),
                'restaurante': restaurante,
                'numero': numero_pedido,
                'cliente_nome': cliente_nome,
                'cliente_celular': cliente_telefone,
                'cliente_email': f"{cliente_nome.lower().replace(' ', '.')}@email.com",
                'status': status,
                'tipo_entrega': tipo_entrega,
                'forma_pagamento': random.choice(['dinheiro', 'cartao', 'pix']),
                'total': total,
                'subtotal': total * 0.9,  # Simulando desconto
                'taxa_entrega': 5.00 if tipo_entrega == 'delivery' else 0.00,
                'observacoes': f"Pedido de teste #{i+1}",
                'created_at': data_criacao,
                'updated_at': data_criacao,
            }
            
            # Adicionar campos de endereço se for delivery
            if tipo_entrega == 'delivery':
                pedido_data.update({
                    'endereco_cep': f"{random.randint(10000, 99999):05d}-{random.randint(100, 999):03d}",
                    'endereco_logradouro': f"Rua Teste {random.randint(100, 999)}",
                    'endereco_numero': str(random.randint(10, 999)),
                    'endereco_bairro': random.choice(['Centro', 'Vila Nova', 'Jardim Flores', 'Santa Maria']),
                    'endereco_cidade': 'São Paulo',
                    'endereco_estado': 'SP',
                })
            
            pedido = Pedido.objects.create(**pedido_data)
            
            pedidos_criados += 1
            
            # Feedback de progresso
            if pedidos_criados % 5 == 0:
                self.stdout.write(f'Criados {pedidos_criados}/{quantidade} pedidos...')
        
        # Relatório final
        tipo_pedidos = "arquivados (>24h)" if criar_antigos else "ativos (<24h)"
        self.stdout.write(
            self.style.SUCCESS(
                f'[OK] {pedidos_criados} pedidos {tipo_pedidos} criados com sucesso!'
            )
        )
        
        # Estatísticas por status
        self.stdout.write('\nDistribuicao por status:')
        for status in status_choices:
            if criar_antigos:
                limite_24h = timezone.now() - timedelta(hours=24)
                count = Pedido.objects.filter(
                    restaurante=restaurante,
                    status=status,
                    created_at__lt=limite_24h
                ).count()
            else:
                limite_24h = timezone.now() - timedelta(hours=24)
                count = Pedido.objects.filter(
                    restaurante=restaurante,
                    status=status,
                    created_at__gte=limite_24h
                ).count()
            
            if count > 0:
                self.stdout.write(f'  {status}: {count} pedidos')
        
        self.stdout.write('\nComandos uteis:')
        self.stdout.write('  Ver pedidos ativos: http://127.0.0.1:8600/admin-loja/pedidos/')
        self.stdout.write('  Ver pedidos arquivados: http://127.0.0.1:8600/admin-loja/pedidos-arquivados/')
        
        if not criar_antigos:
            self.stdout.write('\nPara criar pedidos arquivados, execute:')
            self.stdout.write('  python manage.py criar_pedidos_teste --antigos --quantidade 15')