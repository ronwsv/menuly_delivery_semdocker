"""
Campos customizados para otimização automática de imagens
"""

from django.db import models
from django.core.files.storage import default_storage
from .image_optimizer import ImageOptimizer
import os


class OptimizedImageField(models.ImageField):
    """
    Campo de imagem que otimiza automaticamente as imagens enviadas,
    criando versões em diferentes tamanhos e formatos (WebP + JPEG).
    """
    
    def __init__(self, image_type='produto', create_thumbnails=True, *args, **kwargs):
        """
        Args:
            image_type: Tipo da imagem para definir os tamanhos ('produto', 'categoria', etc.)
            create_thumbnails: Se deve criar miniaturas automaticamente
        """
        self.image_type = image_type
        self.create_thumbnails = create_thumbnails
        super().__init__(*args, **kwargs)
    
    def contribute_to_class(self, cls, name, **kwargs):
        """Adiciona métodos e propriedades extras à classe do modelo"""
        super().contribute_to_class(cls, name, **kwargs)
        
        # Adiciona método para obter URL otimizada
        def get_optimized_url(instance, size='medium', format='webp', request=None):
            field_value = getattr(instance, self.attname)
            if not field_value:
                return None
                
            return ImageOptimizer.get_optimized_url(field_value, size, format, request)
        
        # Adiciona método à classe do modelo
        setattr(cls, f'get_{name}_optimized_url', get_optimized_url)
        
        # Adiciona propriedades para diferentes tamanhos
        sizes = ImageOptimizer.SIZES.get(self.image_type, ImageOptimizer.SIZES['produto'])
        
        for size_name in sizes.keys():
            # Propriedade para WebP
            def make_webp_property(size_name):
                def webp_property(instance):
                    return getattr(instance, f'{self.attname}_{size_name}_webp', None)
                return property(webp_property)
            
            # Propriedade para JPEG
            def make_jpeg_property(size_name):
                def jpeg_property(instance):
                    return getattr(instance, f'{self.attname}_{size_name}_jpeg', None)
                return property(jpeg_property)
            
            setattr(cls, f'{name}_{size_name}_webp', make_webp_property(size_name))
            setattr(cls, f'{name}_{size_name}_jpeg', make_jpeg_property(size_name))


def add_image_versions_to_model(model_class, field_name, image_type):
    """
    Adiciona campos para as versões otimizadas da imagem ao modelo.
    Deve ser chamado após a definição da classe do modelo.
    """
    sizes = ImageOptimizer.SIZES.get(image_type, ImageOptimizer.SIZES['produto'])
    
    for size_name in sizes.keys():
        # Campo para versão WebP
        webp_field_name = f'{field_name}_{size_name}_webp'
        webp_field = models.ImageField(
            upload_to=lambda instance, filename: f'optimized/{image_type}/{size_name}/webp/{filename}',
            null=True,
            blank=True,
            editable=False
        )
        webp_field.contribute_to_class(model_class, webp_field_name)
        
        # Campo para versão JPEG
        jpeg_field_name = f'{field_name}_{size_name}_jpeg'
        jpeg_field = models.ImageField(
            upload_to=lambda instance, filename: f'optimized/{image_type}/{size_name}/jpeg/{filename}',
            null=True,
            blank=True,
            editable=False
        )
        jpeg_field.contribute_to_class(model_class, jpeg_field_name)


class SmartImageField(models.ImageField):
    """
    Campo inteligente que detecta automaticamente o melhor formato
    e tamanho de imagem para servir baseado no contexto.
    """
    
    def __init__(self, image_type='produto', auto_optimize=True, *args, **kwargs):
        self.image_type = image_type
        self.auto_optimize = auto_optimize
        super().__init__(*args, **kwargs)
    
    def get_smart_url(self, instance, request=None, size='medium'):
        """
        Retorna a URL mais apropriada baseada no contexto:
        - WebP se o navegador suporta
        - JPEG como fallback
        - Tamanho apropriado baseado no device (futuro: responsive images)
        """
        field_value = getattr(instance, self.attname)
        if not field_value:
            return None
            
        # Detecta suporte a WebP
        supports_webp = False
        if request and hasattr(request, 'META'):
            accept_header = request.META.get('HTTP_ACCEPT', '')
            supports_webp = 'image/webp' in accept_header
        
        # Escolhe o formato
        format_preference = 'webp' if supports_webp else 'jpeg'
        
        # Tenta encontrar a versão otimizada
        optimized_field_name = f'{self.attname}_{size}_{format_preference}'
        optimized_field = getattr(instance, optimized_field_name, None)
        
        if optimized_field:
            return optimized_field.url
        
        # Fallback para imagem original
        return field_value.url