from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from core.models import Restaurante, Produto, Pedido, Categoria, HorarioFuncionamento

class Command(BaseCommand):
    help = 'Cria os grupos de permissões padrão para Lojistas (Gerente e Atendente)'

    def handle(self, *args, **options):
        self.stdout.write('Criando grupos de permissões...')

        # --- Grupo Gerente ---
        gerente_group, created = Group.objects.get_or_create(name='Gerente')
        if created:
            self.stdout.write('Grupo "Gerente" criado.')
        
        # Permissões para o Gerente (acesso total aos modelos do restaurante)
        permissions = [
            'view_restaurante', 'change_restaurante',
            'add_produto', 'view_produto', 'change_produto', 'delete_produto',
            'add_pedido', 'view_pedido', 'change_pedido', 'delete_pedido',
            'add_cupom', 'view_cupom', 'change_cupom', 'delete_cupom',
            'add_categoria', 'view_categoria', 'change_categoria', 'delete_categoria',
            'add_horariofuncionamento', 'view_horariofuncionamento', 'change_horariofuncionamento', 'delete_horariofuncionamento',
        ]
        
        for perm_codename in permissions:
            try:
                app_label, model_name = self.get_app_model_from_codename(perm_codename)
                content_type = ContentType.objects.get(app_label=app_label, model=model_name)
                permission = Permission.objects.get(content_type=content_type, codename=perm_codename)
                gerente_group.permissions.add(permission)
            except (ContentType.DoesNotExist, Permission.DoesNotExist):
                self.stdout.write(self.style.WARNING(f'Permissão {perm_codename} não encontrada. Pulando.'))

        self.stdout.write(self.style.SUCCESS('Permissões para "Gerente" configuradas.'))

        # --- Grupo Atendente ---
        atendente_group, created = Group.objects.get_or_create(name='Atendente')
        if created:
            self.stdout.write('Grupo "Atendente" criado.')

        # Permissões para o Atendente (apenas visualizar e gerenciar pedidos)
        permissions_atendente = [
            'view_pedido', 'change_pedido',
        ]

        for perm_codename in permissions_atendente:
            try:
                app_label, model_name = self.get_app_model_from_codename(perm_codename)
                content_type = ContentType.objects.get(app_label=app_label, model=model_name)
                permission = Permission.objects.get(content_type=content_type, codename=perm_codename)
                atendente_group.permissions.add(permission)
            except (ContentType.DoesNotExist, Permission.DoesNotExist):
                self.stdout.write(self.style.WARNING(f'Permissão {perm_codename} não encontrada. Pulando.'))

        self.stdout.write(self.style.SUCCESS('Permissões para "Atendente" configuradas.'))
        self.stdout.write(self.style.SUCCESS('Comando finalizado com sucesso!'))

    def get_app_model_from_codename(self, codename):
        # Mapeamento de codename para (app_label, model_name)
        # Isso pode precisar de ajuste dependendo da sua estrutura de apps
        model_map = {
            'restaurante': ('core', 'restaurante'),
            'produto': ('core', 'produto'),
            'pedido': ('core', 'pedido'),
            'cupom': ('core', 'cupom'),
            'categoria': ('core', 'categoria'),
            'horariofuncionamento': ('core', 'horariofuncionamento'),
        }
        action, model_name = codename.split('_')
        return model_map.get(model_name, ('', ''))
