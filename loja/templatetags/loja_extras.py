"""
Template tags personalizadas para a loja
"""
import logging
from django import template
from django.urls import reverse, NoReverseMatch
from django.utils.safestring import mark_safe

register = template.Library()
logger = logging.getLogger(__name__)

# Mapeamento de views que não precisam de argumentos adicionais
SIMPLE_VIEWS = {
    'home': 'loja:home',
    'cardapio': 'loja:cardapio', 
    'carrinho': 'loja:carrinho',
    'checkout': 'loja:checkout',
    'sobre': 'loja:sobre',
    'contato': 'loja:contato',
    'buscar': 'loja:buscar',
    'meus_pedidos': 'loja:meus_pedidos',
    'perfil': 'loja:perfil',
}

@register.simple_tag(takes_context=True)
def loja_url(context, view_name, **kwargs):
    """
    Template tag personalizada para gerar URLs da loja com suporte hierárquico
    
    Uso:
    {% loja_url 'home' %}
    {% loja_url 'categoria' categoria_slug='pizzas' %}
    {% loja_url 'produto_detalhe' produto_slug='margherita' %}
    """
    try:
        request = context.get('request')
        
        # Verificar se temos um restaurante_slug no contexto ou na URL
        restaurante_slug = None
        
        # Tentar pegar do contexto primeiro
        if 'restaurante_atual' in context and context['restaurante_atual']:
            restaurante_slug = context['restaurante_atual'].slug
        
        # Se não tiver no contexto, tentar pegar da URL atual
        if not restaurante_slug and request:
            url_parts = request.path.strip('/').split('/')
            if url_parts and url_parts[0] not in ['admin', 'admin-loja', 'superadmin', 'static', 'media']:
                # Primeiro segmento pode ser o slug do restaurante
                restaurante_slug = url_parts[0]
        
        # Preparar argumentos para a URL
        url_kwargs = kwargs.copy()
        
        # Mapear nomes de views simples
        if view_name in SIMPLE_VIEWS:
            view_name = SIMPLE_VIEWS[view_name]
        else:
            # Para views complexas, adicionar o prefixo loja:
            if not view_name.startswith('loja:'):
                view_name = f'loja:{view_name}'
        
        # Se temos um restaurante_slug, adicionar aos kwargs
        if restaurante_slug:
            url_kwargs['restaurante_slug'] = restaurante_slug
        
        # Tentar gerar a URL
        try:
            url = reverse(view_name, kwargs=url_kwargs)
            logger.debug(f"✅ URL gerada: {view_name} -> {url}")
            return url
        except NoReverseMatch:
            # Se falhar com restaurante_slug, tentar sem
            if 'restaurante_slug' in url_kwargs:
                url_kwargs.pop('restaurante_slug')
                try:
                    url = reverse(view_name, kwargs=url_kwargs)
                    logger.debug(f"✅ URL gerada (sem slug): {view_name} -> {url}")
                    return url
                except NoReverseMatch:
                    pass
            
            # Log do erro e retornar URL padrão
            logger.error(f"❌ Erro de NoReverseMatch na template tag 'loja_url': "
                        f"Reverse for '{view_name}' with keyword arguments '{url_kwargs}' not found. "
                        f"View: '{view_name}', Args: (), Kwargs: {url_kwargs}")
            
            # Retornar URL de fallback
            return '#'
            
    except Exception as e:
        logger.error(f"❌ Erro inesperado na template tag 'loja_url': {e}")
        return '#'


@register.filter
def currency(value):
    """
    Formatar valor como moeda brasileira
    
    Uso: {{ produto.preco|currency }}
    """
    try:
        if value is None:
            return "R$ 0,00"
        
        # Converter para float se necessário
        if isinstance(value, str):
            value = float(value.replace(',', '.'))
        
        return f"R$ {value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    except (ValueError, TypeError):
        return "R$ 0,00"


@register.filter
def multiply(value, arg):
    """
    Multiplicar dois valores
    
    Uso: {{ produto.preco|multiply:item.quantidade }}
    """
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0


@register.simple_tag
def define(val=None):
    """
    Definir uma variável no template
    
    Uso: {% define "valor" as minha_variavel %}
    """
    return val


@register.inclusion_tag('loja/components/breadcrumb.html', takes_context=True)
def breadcrumb(context, items):
    """
    Renderizar breadcrumb
    
    Uso: {% breadcrumb breadcrumb_items %}
    """
    return {
        'items': items,
        'request': context.get('request'),
    }


@register.filter
def get_item(dictionary, key):
    """
    Pegar item de um dicionário
    
    Uso: {{ meu_dict|get_item:chave }}
    """
    try:
        return dictionary.get(key)
    except (AttributeError, TypeError):
        return None


@register.simple_tag
def active_page(request, view_name):
    """
    Verificar se uma página está ativa
    
    Uso: {% active_page request 'home' %}
    """
    try:
        if request and hasattr(request, 'resolver_match'):
            current_view = request.resolver_match.view_name
            return 'active' if current_view == view_name else ''
    except (AttributeError, TypeError):
        pass
    return ''


# Registrar filtros adicionais para compatibilidade
register.filter('currency', currency)
register.filter('multiply', multiply)
register.filter('get_item', get_item)
