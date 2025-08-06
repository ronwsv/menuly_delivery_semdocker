from django.views.generic import TemplateView
from .models import Restaurante

class LandingView(TemplateView):
    """
    View para a página inicial (landing page) do Menuly.
    Lista os restaurantes disponíveis.
    """
    template_name = 'landing.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['restaurantes'] = Restaurante.objects.filter(status='ativo').order_by('nome')
        context['admin_url'] = '/admin/' # Futuramente pode ser uma URL mais específica
        return context

class SobreView(TemplateView):
    """Página Sobre genérica do Menuly."""
    template_name = 'sobre.html'

class ContatoView(TemplateView):
    """Página de Contato genérica do Menuly."""
    template_name = 'contato.html'

