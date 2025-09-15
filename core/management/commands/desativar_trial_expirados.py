from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from core.models import Usuario

class Command(BaseCommand):
    help = 'Desativa usuários com trial expirado (mais de 7 dias sem plano)'

    def handle(self, *args, **options):
        # Data limite: 7 dias atrás
        data_limite = timezone.now() - timedelta(days=7)
        
        # Buscar usuários lojistas ativos sem plano que foram criados há mais de 7 dias
        usuarios_trial_expirado = Usuario.objects.filter(
            tipo_usuario='lojista',
            is_active=True,
            restaurantes__plano__isnull=True,
            date_joined__lt=data_limite
        ).distinct()
        
        total_desativados = 0
        
        for usuario in usuarios_trial_expirado:
            usuario.is_active = False
            usuario.save()
            total_desativados += 1
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Usuário {usuario.username} desativado - Trial expirado'
                )
            )
        
        if total_desativados == 0:
            self.stdout.write(
                self.style.WARNING('Nenhum usuário com trial expirado encontrado')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Total de {total_desativados} usuários desativados por trial expirado'
                )
            )
