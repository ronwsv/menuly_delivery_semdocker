from django.core.management.base import BaseCommand
from core.models import Restaurante, Notificacao, Produto
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Cria notificações de teste para demonstrar o sistema'

    def add_arguments(self, parser):
        parser.add_argument('--usuario', type=str, help='Username do lojista')

    def handle(self, *args, **options):
        username = options.get('usuario')
        
        if not username:
            self.stdout.write(self.style.ERROR('Por favor, forneça um username com --usuario'))
            return
        
        try:
            user = User.objects.get(username=username)
            restaurante = Restaurante.objects.filter(proprietario=user).first()
            
            if not restaurante:
                self.stdout.write(self.style.ERROR(f'Usuário {username} não possui restaurante'))
                return
            
            # Criar notificação de novo pedido
            Notificacao.objects.create(
                restaurante=restaurante,
                tipo='pedido_novo',
                titulo='Novo pedido #001',
                mensagem='Um novo pedido foi recebido no valor de R$ 45,90',
                prioridade='alta',
                link_acao='/admin-loja/pedidos/'
            )
            
            # Criar notificação de sistema
            Notificacao.objects.create(
                restaurante=restaurante,
                tipo='sistema',
                titulo='Sistema de notificações ativo',
                mensagem='O sistema de notificações em tempo real foi ativado com sucesso!',
                prioridade='media'
            )
            
            # Criar produto com estoque baixo para demonstrar notificação
            produto = restaurante.produtos.first()
            if produto:
                produto.controlar_estoque = True
                produto.estoque_atual = 2
                produto.estoque_minimo = 5
                produto.save()
                
                Notificacao.objects.create(
                    restaurante=restaurante,
                    produto=produto,
                    tipo='estoque_baixo',
                    titulo=f'Estoque baixo: {produto.nome}',
                    mensagem=f'O produto "{produto.nome}" está com estoque baixo. Restam apenas {produto.estoque_atual} unidades.',
                    prioridade='alta',
                    link_acao=f'/admin-loja/produtos/{produto.id}/editar/'
                )
            
            self.stdout.write(
                self.style.SUCCESS(f'Notificações de teste criadas para {restaurante.nome}')
            )
            
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Usuário {username} não encontrado'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Erro: {str(e)}'))