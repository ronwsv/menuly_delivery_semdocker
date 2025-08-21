# ==================== VIEWS DE PERFIL DO USUÁRIO ====================

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from .utils import painel_loja_required
from .forms import PerfilForm, AlterarSenhaForm

@painel_loja_required
def perfil_visualizar(request):
    """View para visualizar dados do perfil do usuário"""
    usuario = request.user
    tipo_usuario_display = {
        'lojista': 'Lojista',
        'gerente': 'Gerente',
        'funcionario': 'Funcionário/Atendente'
    }.get(usuario.tipo_usuario, 'Usuário')
    
    # Verificar grupos do usuário para atendentes
    grupos = usuario.groups.all()
    
    context = {
        'usuario': usuario,
        'tipo_usuario_display': tipo_usuario_display,
        'grupos': grupos,
    }
    
    return render(request, 'admin_loja/perfil_visualizar.html', context)

@painel_loja_required
def perfil_editar(request):
    """View para editar dados do perfil do usuário"""
    usuario = request.user
    
    if request.method == 'POST':
        form = PerfilForm(request.POST, instance=usuario)
        if form.is_valid():
            form.save()
            # Atualizar username com o email se foi alterado
            if form.cleaned_data.get('email'):
                usuario.username = form.cleaned_data['email']
                usuario.save()
            
            messages.success(request, 'Perfil atualizado com sucesso!')
            return redirect('admin_loja:perfil_visualizar')
    else:
        form = PerfilForm(instance=usuario)
    
    return render(request, 'admin_loja/perfil_editar.html', {
        'form': form,
        'usuario': usuario
    })

@painel_loja_required
def perfil_alterar_senha(request):
    """View para alterar senha do usuário"""
    if request.method == 'POST':
        form = AlterarSenhaForm(request.user, request.POST)
        if form.is_valid():
            form.save()
            
            # Manter o usuário logado após alterar a senha
            update_session_auth_hash(request, form.user)
            messages.success(request, 'Senha alterada com sucesso!')
            return redirect('admin_loja:perfil_visualizar')
    else:
        form = AlterarSenhaForm(request.user)
    
    return render(request, 'admin_loja/perfil_alterar_senha.html', {
        'form': form
    })