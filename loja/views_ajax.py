from django.http import JsonResponse
from core.models import Restaurante, calcular_distancia_entre_ceps

def calcular_frete_ajax(request, restaurante_slug=None):
    """Endpoint AJAX para calcular o frete em tempo real no checkout."""
    if request.method == 'POST':
        cep_origem = request.POST.get('cep_origem')
        cep_destino = request.POST.get('cep_destino')
        restaurante_id = request.POST.get('restaurante_id')
        try:
            restaurante = Restaurante.objects.get(id=restaurante_id)
        except Restaurante.DoesNotExist:
            return JsonResponse({'erro': 'Restaurante não encontrado.'}, status=404)
        if restaurante.frete_fixo and restaurante.valor_frete_fixo is not None:
            return JsonResponse({'frete': float(restaurante.valor_frete_fixo), 'fixo': True})
        if restaurante.valor_frete_padrao is not None:
            valor = float(restaurante.valor_frete_padrao)
            if cep_origem and cep_destino and restaurante.valor_adicional_km:
                distancia_km = calcular_distancia_entre_ceps(cep_origem, cep_destino)
                if distancia_km is not None:
                    valor += float(restaurante.valor_adicional_km) * distancia_km
            return JsonResponse({'frete': valor, 'fixo': False})
        return JsonResponse({'frete': 0, 'fixo': False})
    return JsonResponse({'erro': 'Método não permitido.'}, status=405)
