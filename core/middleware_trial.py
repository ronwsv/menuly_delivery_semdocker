from django.utils import timezone
from datetime import timedelta
from django.contrib import messages
from django.urls import reverse


class TrialNotificationMiddleware:
    """
    Middleware para notificar usuários sobre trials prestes a expirar
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Processar antes da view
        if request.user.is_authenticated and hasattr(request.user, 'restaurante'):
            self.check_trial_status(request)
        
        response = self.get_response(request)
        return response

    def check_trial_status(self, request):
        """Verifica o status do trial do usuário"""
        try:
            usuario = request.user
            
            # Só verifica lojistas
            if usuario.tipo_usuario != 'lojista':
                return
                
            restaurante = usuario.restaurantes.first() if hasattr(usuario, 'restaurantes') else None
            
            # Só verifica se o usuário tem restaurante e não tem plano
            if not restaurante or restaurante.plano:
                return
            
            # Calcular dias desde o cadastro
            dias_desde_cadastro = (timezone.now() - usuario.date_joined).days
            dias_restantes = 7 - dias_desde_cadastro
            
            # URL dos planos
            url_planos = reverse('admin_loja:planos_comparar')
            
            # Notificações baseadas nos dias restantes
            if dias_restantes <= 0:
                # Trial expirado
                messages.error(
                    request,
                    f'⚠️ Seu período trial expirou! '
                    f'<a href="{url_planos}" class="alert-link fw-bold">Escolha um plano agora</a> '
                    f'para continuar usando o sistema.',
                    extra_tags='safe'
                )
            elif dias_restantes == 1:
                # Último dia
                messages.warning(
                    request,
                    f'🔔 Último dia do seu trial! '
                    f'<a href="{url_planos}" class="alert-link fw-bold">Escolha um plano</a> '
                    f'para não perder o acesso.',
                    extra_tags='safe'
                )
            elif dias_restantes <= 3:
                # 2-3 dias restantes
                messages.info(
                    request,
                    f'⏰ Restam apenas {dias_restantes} dias do seu trial. '
                    f'<a href="{url_planos}" class="alert-link">Veja nossos planos</a>.',
                    extra_tags='safe'
                )
            elif dias_restantes == 5:
                # 5 dias restantes (notificação menos urgente)
                messages.info(
                    request,
                    f'💡 Você tem {dias_restantes} dias restantes no trial. '
                    f'<a href="{url_planos}" class="alert-link">Conheça nossos planos</a>.',
                    extra_tags='safe'
                )
                
        except Exception as e:
            # Falha silenciosa - não queremos quebrar a aplicação
            pass
