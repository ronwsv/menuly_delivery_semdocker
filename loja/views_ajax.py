from django.http import JsonResponse
from core.models import Restaurante, calcular_distancia_entre_ceps

def calcular_frete_ajax(request, restaurante_slug=None):
    """Endpoint AJAX para calcular o frete em tempo real no checkout."""
    if request.method == 'POST':
        cep_origem = request.POST.get('cep_origem')
        cep_destino = request.POST.get('cep_destino')
        print(f"[DEBUG] calcular_frete_ajax: slug={restaurante_slug} cep_origem={cep_origem} cep_destino={cep_destino}")
        # Buscar restaurante pelo slug da URL
        try:
            restaurante = Restaurante.objects.get(slug=restaurante_slug)
        except Restaurante.DoesNotExist:
            print(f"[DEBUG] Restaurante não encontrado para slug={restaurante_slug}")
            return JsonResponse({'erro': 'Restaurante não encontrado.'}, status=404)
        print(f"[DEBUG] Restaurante: frete_fixo={restaurante.frete_fixo} valor_frete_fixo={restaurante.valor_frete_fixo} valor_frete_padrao={restaurante.valor_frete_padrao} valor_adicional_km={restaurante.valor_adicional_km} raio_limite_km={restaurante.raio_limite_km}")
        if restaurante.frete_fixo and restaurante.valor_frete_fixo is not None:
            print(f"[DEBUG] Frete fixo aplicado: {restaurante.valor_frete_fixo}")
            return JsonResponse({'frete': float(restaurante.valor_frete_fixo), 'fixo': True})
        if restaurante.valor_frete_padrao is not None:
            from core.utils_frete_cep import calcular_frete_cep
            if cep_origem and cep_destino:
                print(f"[DEBUG] Chamando calcular_frete_cep com base={restaurante.valor_frete_padrao}, km={restaurante.valor_adicional_km}, raio_limite={restaurante.raio_limite_km}")
                resultado = calcular_frete_cep(
                    cep_destino=cep_destino,
                    cep_referencia=cep_origem,
                    taxa_base=float(restaurante.valor_frete_padrao),
                    taxa_km=float(restaurante.valor_adicional_km) if restaurante.valor_adicional_km else 0,
                    raio_limite_km=float(restaurante.raio_limite_km) if restaurante.raio_limite_km else None
                )
                print(f"[DEBUG] Resultado calcular_frete_cep: {resultado}")
                if resultado and 'custo_frete' in resultado:
                    return JsonResponse({'frete': resultado['custo_frete'], 'fixo': False, 'distancia_km': resultado.get('distancia_km')})
                elif resultado and 'erro' in resultado:
                    mensagem_cliente = (
                        'Ocorreu um erro ao calcular o frete. Por favor, revise o endereço ou, se o problema persistir, '
                        'entre em contato pelo WhatsApp da loja para finalizar seu pedido.'
                    )
                    return JsonResponse({'erro': mensagem_cliente, 'erro_tecnico': resultado['erro']}, status=400)
            print(f"[DEBUG] Frete padrão aplicado: {restaurante.valor_frete_padrao}")
            return JsonResponse({'frete': float(restaurante.valor_frete_padrao), 'fixo': False})
        print(f"[DEBUG] Nenhuma configuração de frete encontrada para restaurante.")
        return JsonResponse({'frete': 0, 'fixo': False})
    return JsonResponse({'erro': 'Método não permitido.'}, status=405)
