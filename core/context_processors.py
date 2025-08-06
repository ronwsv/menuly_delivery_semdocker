from django.conf import settings
from .models import Restaurante


def site_context(request):
    """
    Context processor para fornecer dados do restaurante/site atual
    baseado no domínio ou slug na URL
    """
    context = {}
    
    # Por enquanto, vamos usar o primeiro restaurante ativo
    # Futuramente isso será baseado no domínio ou slug da URL
    try:
        restaurante = Restaurante.objects.filter(status='ativo').first()
        if restaurante:
            context['restaurante_atual'] = restaurante
            context['cores_tema'] = {
                'primaria': restaurante.cor_primaria,
                'secundaria': restaurante.cor_secundaria,
                'destaque': restaurante.cor_destaque,
            }
    except Restaurante.DoesNotExist:
        context['restaurante_atual'] = None
        context['cores_tema'] = {
            'primaria': '#dc3545',
            'secundaria': '#6c757d',
            'destaque': '#ffc107',
        }
    
    return context
