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
            # Usar utilitário para calcular custo do frete considerando configuração do lojista
            from core.utils_frete_cep import calcular_frete_cep
            if cep_origem and cep_destino:
                resultado = calcular_frete_cep(
                    cep_destino=cep_destino,
                    cep_referencia=cep_origem,
                    taxa_base=float(restaurante.valor_frete_padrao),
                    taxa_km=float(restaurante.valor_adicional_km) if restaurante.valor_adicional_km else 0
                )
                if resultado and 'custo_frete' in resultado:
                    return JsonResponse({'frete': resultado['custo_frete'], 'fixo': False, 'distancia_km': resultado.get('distancia_km')})
                elif resultado and 'erro' in resultado:
                    return JsonResponse({'erro': resultado['erro']}, status=400)
            # fallback: retorna valor padrão se não for possível calcular
            return JsonResponse({'frete': float(restaurante.valor_frete_padrao), 'fixo': False})
        return JsonResponse({'frete': 0, 'fixo': False})
    return JsonResponse({'erro': 'Método não permitido.'}, status=405)
