from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core.models import Entregador

User = get_user_model()

class Command(BaseCommand):
    help = 'Cria um entregador de teste para demonstração do sistema'

    def handle(self, *args, **options):
        # Criar usuário
        username = 'entregador_teste'
        password = 'senha123'
        
        # Verificar se já existe
        if User.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.WARNING(f'Usuário {username} já existe')
            )
            user = User.objects.get(username=username)
        else:
            user = User.objects.create_user(
                username=username,
                password=password,
                first_name='João',
                last_name='Silva',
                email='joao.entregador@menuly.com',
                celular='11999887766',
                tipo_usuario='entregador'
            )
            self.stdout.write(
                self.style.SUCCESS(f'Usuário {username} criado com sucesso')
            )

        # Verificar se já existe perfil de entregador
        try:
            entregador = user.entregador
            self.stdout.write(
                self.style.WARNING(f'Entregador {entregador.nome} já existe')
            )
        except Entregador.DoesNotExist:
            # Criar perfil de entregador
            entregador = Entregador.objects.create(
                usuario=user,
                nome='João Silva',
                telefone='11999887766',
                cnh='12345678901',
                veiculo='Honda CG 160 Titan',
                dados_bancarios='Banco do Brasil - Ag: 1234 - CC: 56789-0',
                disponivel=True,
                em_pausa=False
            )
            self.stdout.write(
                self.style.SUCCESS(f'Entregador {entregador.nome} criado com sucesso')
            )

        self.stdout.write(
            self.style.SUCCESS(
                f'\nEntregador de teste criado:'
                f'\nUsuário: {username}'
                f'\nSenha: {password}'
                f'\nNome: {entregador.nome}'
                f'\nTelefone: {entregador.telefone}'
                f'\nStatus: {"Disponível" if entregador.disponivel else "Indisponível"}'
                f'\n\nPara acessar o painel:'
                f'\nURL: http://localhost:8000/entregador/login/'
            )
        )