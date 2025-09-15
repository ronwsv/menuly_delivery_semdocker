from django.utils import timezone
from datetime import timedelta


def get_trial_info(user):
    """
    Retorna informações sobre o trial do usuário
    """
    if not user.is_authenticated or user.tipo_usuario != 'lojista':
        return None
    
    try:
        restaurante = user.restaurantes.first() if hasattr(user, 'restaurantes') else None
        
        # Se não tem restaurante ou já tem plano, não está em trial
        if not restaurante or restaurante.plano:
            return None
        
        # Calcular informações do trial
        data_cadastro = user.date_joined
        data_expiracao = data_cadastro + timedelta(days=7)
        dias_desde_cadastro = (timezone.now() - data_cadastro).days
        dias_restantes = 7 - dias_desde_cadastro
        
        # Determinar status
        if dias_restantes <= 0:
            status = 'expirado'
            status_class = 'danger'
            status_texto = 'Trial Expirado'
        elif dias_restantes <= 1:
            status = 'ultimo_dia'
            status_class = 'warning'
            status_texto = 'Último Dia'
        elif dias_restantes <= 3:
            status = 'expirando'
            status_class = 'warning'
            status_texto = 'Expirando em Breve'
        else:
            status = 'ativo'
            status_class = 'success'
            status_texto = 'Trial Ativo'
        
        return {
            'em_trial': True,
            'data_cadastro': data_cadastro,
            'data_expiracao': data_expiracao,
            'dias_restantes': max(0, dias_restantes),
            'dias_decorridos': dias_desde_cadastro,
            'total_dias': 7,
            'status': status,
            'status_class': status_class,
            'status_texto': status_texto,
            'porcentagem_usado': min(100, (dias_desde_cadastro / 7) * 100),
            'urgente': dias_restantes <= 3,
        }
        
    except Exception:
        return None


def trial_context_processor(request):
    """
    Context processor para adicionar informações de trial em todos os templates
    """
    trial_info = get_trial_info(request.user) if hasattr(request, 'user') else None
    
    return {
        'trial_info': trial_info
    }
