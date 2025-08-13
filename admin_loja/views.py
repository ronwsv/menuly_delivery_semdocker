
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django import forms

# Avançar status do pedido
@login_required
def admin_loja_avancar_status_pedido(request, pedido_id):
    from core.models import Pedido
    pedido = Pedido.objects.get(id=pedido_id, restaurante__proprietario=request.user)
    # Definir o fluxo de status
    fluxo = ['novo', 'preparo', 'pronto', 'entrega', 'finalizado']
    try:
        idx = fluxo.index(pedido.status)
        if idx < len(fluxo) - 1:
            pedido.status = fluxo[idx + 1]
            pedido.save()
    except ValueError:
        pass
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/admin-loja/pedidos/'))

class AdminLojaLoginForm(forms.Form):
    username = forms.CharField(label='Usuário')
    password = forms.CharField(widget=forms.PasswordInput, label='Senha')

def admin_loja_login(request):
    error = None
    if request.method == 'POST':
        form = AdminLojaLoginForm(request.POST)
        if form.is_valid():
            user = authenticate(request, username=form.cleaned_data['username'], password=form.cleaned_data['password'])
            if user is not None and hasattr(user, 'tipo_usuario') and user.tipo_usuario == 'lojista':
                login(request, user)
                return redirect('admin_loja:dashboard')
            else:
                error = 'Usuário ou senha inválidos, ou você não é um lojista.'
    else:
        form = AdminLojaLoginForm()
    return render(request, 'admin_loja/login.html', {'form': form, 'error': error})

@login_required
def admin_loja_dashboard(request):
    # Aqui futuramente vamos filtrar para mostrar só dados da loja do lojista
    return render(request, 'admin_loja/dashboard.html')

class DashboardView(TemplateView):
    template_name = 'admin_loja/dashboard.html'


# Página de pedidos do lojista
from django.contrib.auth.decorators import login_required
@login_required

def admin_loja_pedidos(request):
    # Buscar restaurantes do lojista logado
    restaurantes = request.user.restaurantes.all()
    pedidos = []
    status_list = ['novo', 'preparo', 'pronto', 'entrega', 'finalizado']
    pedidos_por_status = {status: [] for status in status_list}
    if restaurantes.exists():
        from core.models import Pedido
        pedidos = Pedido.objects.filter(restaurante__in=restaurantes).order_by('created_at')
        for pedido in pedidos:
            if pedido.status in pedidos_por_status:
                pedidos_por_status[pedido.status].append(pedido)
    return render(request, 'admin_loja/pedidos.html', {'pedidos_por_status': pedidos_por_status})

# Visualização de cupom do pedido
from django.shortcuts import get_object_or_404
@login_required
def admin_loja_cupom_pedido(request, pedido_id):
    from core.models import Pedido, ItemPedido
    pedido = get_object_or_404(Pedido, id=pedido_id, restaurante__proprietario=request.user)
    itens = pedido.itens.all() if hasattr(pedido, 'itens') else []
    return render(request, 'admin_loja/cupom_pedido.html', {'pedido': pedido, 'itens': itens})
