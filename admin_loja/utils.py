from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import redirect
from django.contrib import messages

def painel_loja_required(view_func):
    def check_user(user):
        return (
            getattr(user, 'tipo_usuario', None) in ['lojista', 'gerente']
            or user.groups.filter(name='Atendente').exists()
        )
    return user_passes_test(check_user, login_url='login')(view_func)

def verificar_permissao_gerencial(request, recurso="esta funcionalidade"):
    """
    Verifica se o usuário tem permissão para funcionalidades gerenciais
    (apenas lojista e gerente)
    """
    tipo_usuario = getattr(request.user, 'tipo_usuario', None)
    if tipo_usuario not in ['lojista', 'gerente']:
        messages.error(request, f'Você não tem permissão para acessar {recurso}.')
        return redirect('admin_loja:dashboard')
    return None

def verificar_permissao_lojista(request, recurso="esta funcionalidade"):
    """
    Verifica se o usuário é lojista
    (apenas lojista)
    """
    tipo_usuario = getattr(request.user, 'tipo_usuario', None)
    if tipo_usuario != 'lojista':
        messages.error(request, f'Apenas o lojista pode acessar {recurso}.')
        return redirect('admin_loja:dashboard')
    return None

def obter_restaurante_usuario(user):
    """
    Obtém o restaurante do usuário baseado no seu tipo
    """
    tipo_usuario = getattr(user, 'tipo_usuario', None)
    
    if tipo_usuario == 'lojista':
        # Lojista: buscar restaurantes que possui
        return user.restaurantes.first()
    else:
        # Gerente/Atendente: buscar restaurante onde trabalha
        return user.trabalha_em.first()