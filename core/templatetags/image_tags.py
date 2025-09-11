"""
Template tags para otimização de imagens
Facilita o uso de imagens otimizadas nos templates.
"""

from django import template
from django.utils.safestring import mark_safe
from ..image_optimizer import ImageOptimizer

register = template.Library()


@register.simple_tag(takes_context=True)
def optimized_image(context, image_field, size='medium', format='auto', alt='', css_class='', **kwargs):
    """
    Renderiza uma tag img com a versão otimizada da imagem.
    
    Uso:
    {% optimized_image produto.imagem_principal size="medium" format="auto" alt="Produto" css_class="img-fluid" %}
    
    Args:
        image_field: Campo de imagem do modelo
        size: Tamanho desejado ('thumb', 'medium', 'large')
        format: Formato ('auto', 'webp', 'jpeg')
        alt: Texto alternativo
        css_class: Classes CSS
        **kwargs: Atributos HTML adicionais
    """
    if not image_field:
        return ''
    
    request = context.get('request')
    
    # Determina o formato
    if format == 'auto':
        # Detecta suporte a WebP
        supports_webp = False
        if request and hasattr(request, 'META'):
            accept_header = request.META.get('HTTP_ACCEPT', '')
            supports_webp = 'image/webp' in accept_header
        format = 'webp' if supports_webp else 'jpeg'
    
    # Obtém a URL otimizada
    image_url = ImageOptimizer.get_optimized_url(image_field, size, format, request)
    
    if not image_url:
        return ''
    
    # Constrói os atributos HTML
    attributes = []
    attributes.append(f'src="{image_url}"')
    
    if alt:
        attributes.append(f'alt="{alt}"')
    
    if css_class:
        attributes.append(f'class="{css_class}"')
    
    # Adiciona atributos extras
    for key, value in kwargs.items():
        if key.startswith('data_'):
            # Converte data_ para data-
            key = key.replace('_', '-')
        attributes.append(f'{key}="{value}"')
    
    return mark_safe(f'<img {" ".join(attributes)} />')


@register.simple_tag(takes_context=True)
def optimized_image_url(context, image_field, size='medium', format='auto'):
    """
    Retorna apenas a URL da imagem otimizada.
    
    Uso:
    {% optimized_image_url produto.imagem_principal size="large" format="webp" %}
    """
    if not image_field:
        return ''
    
    request = context.get('request')
    
    # Determina o formato
    if format == 'auto':
        supports_webp = False
        if request and hasattr(request, 'META'):
            accept_header = request.META.get('HTTP_ACCEPT', '')
            supports_webp = 'image/webp' in accept_header
        format = 'webp' if supports_webp else 'jpeg'
    
    return ImageOptimizer.get_optimized_url(image_field, size, format, request) or ''


@register.simple_tag(takes_context=True)
def responsive_image(context, image_field, alt='', css_class='img-fluid', **kwargs):
    """
    Renderiza uma imagem responsiva com srcset para diferentes tamanhos.
    
    Uso:
    {% responsive_image produto.imagem_principal alt="Produto" css_class="img-fluid" %}
    """
    if not image_field:
        return ''
    
    request = context.get('request')
    
    # Detecta suporte a WebP
    supports_webp = False
    if request and hasattr(request, 'META'):
        accept_header = request.META.get('HTTP_ACCEPT', '')
        supports_webp = 'image/webp' in accept_header
    
    format = 'webp' if supports_webp else 'jpeg'
    
    # Constrói o srcset
    srcset_parts = []
    sizes = ['thumb', 'medium', 'large']
    widths = [150, 300, 800]  # Larguras aproximadas
    
    for size, width in zip(sizes, widths):
        url = ImageOptimizer.get_optimized_url(image_field, size, format, request)
        if url:
            srcset_parts.append(f'{url} {width}w')
    
    if not srcset_parts:
        return ''
    
    # URL padrão (medium)
    default_url = ImageOptimizer.get_optimized_url(image_field, 'medium', format, request)
    
    # Constrói os atributos HTML
    attributes = []
    attributes.append(f'src="{default_url}"')
    attributes.append(f'srcset="{", ".join(srcset_parts)}"')
    attributes.append('sizes="(max-width: 576px) 150px, (max-width: 768px) 300px, 800px"')
    
    if alt:
        attributes.append(f'alt="{alt}"')
    
    if css_class:
        attributes.append(f'class="{css_class}"')
    
    # Adiciona atributos extras
    for key, value in kwargs.items():
        if key.startswith('data_'):
            key = key.replace('_', '-')
        attributes.append(f'{key}="{value}"')
    
    return mark_safe(f'<img {" ".join(attributes)} />')


@register.simple_tag
def image_size_info(image_field, size='medium'):
    """
    Retorna informações sobre o tamanho da imagem otimizada.
    Útil para desenvolvimento e debugging.
    """
    if not image_field:
        return ''
    
    sizes_config = ImageOptimizer.SIZES.get('produto', ImageOptimizer.SIZES['produto'])
    target_size = sizes_config.get(size, (300, 300))
    
    return f'{target_size[0]}x{target_size[1]}'


@register.filter
def has_optimized_version(image_field, size_format):
    """
    Verifica se existe uma versão otimizada específica da imagem.
    
    Uso:
    {% if produto.imagem_principal|has_optimized_version:"medium_webp" %}
        <!-- Existe versão medium em WebP -->
    {% endif %}
    """
    if not image_field or not hasattr(image_field, 'instance'):
        return False
    
    instance = image_field.instance
    field_name = image_field.field.name
    optimized_field_name = f'{field_name}_{size_format}'
    
    return hasattr(instance, optimized_field_name) and getattr(instance, optimized_field_name)


@register.inclusion_tag('core/image_gallery.html', takes_context=True)
def image_gallery(context, images, size='medium', show_thumbs=True):
    """
    Renderiza uma galeria de imagens otimizada.
    
    Uso:
    {% image_gallery produto.imagens.all size="large" show_thumbs=True %}
    """
    request = context.get('request')
    
    # Prepara as imagens com URLs otimizadas
    processed_images = []
    for image in images:
        if hasattr(image, 'imagem'):
            image_field = image.imagem
        else:
            image_field = image
        
        if image_field:
            # Detecta suporte a WebP
            supports_webp = False
            if request and hasattr(request, 'META'):
                accept_header = request.META.get('HTTP_ACCEPT', '')
                supports_webp = 'image/webp' in accept_header
            
            format = 'webp' if supports_webp else 'jpeg'
            
            processed_images.append({
                'original': image,
                'main_url': ImageOptimizer.get_optimized_url(image_field, size, format, request),
                'thumb_url': ImageOptimizer.get_optimized_url(image_field, 'thumb', format, request) if show_thumbs else None,
            })
    
    return {
        'images': processed_images,
        'show_thumbs': show_thumbs,
        'request': request,
    }