# admin_loja/context_processors.py

def painel_permissoes(request):
    user = request.user
    if not user.is_authenticated:
        return {
            'is_lojista': False,
            'is_gerente': False,
            'is_atendente': False,
        }
    
    is_lojista = getattr(user, 'tipo_usuario', None) == 'lojista'
    is_gerente = getattr(user, 'tipo_usuario', None) == 'gerente'
    is_atendente = user.groups.filter(name='Atendente').exists()
    return {
        'is_lojista': is_lojista,
        'is_gerente': is_gerente,
        'is_atendente': is_atendente,
    }