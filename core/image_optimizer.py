"""
Sistema de Otimização de Imagens para o Menuly
Inspirado no sistema do WordPress, otimiza automaticamente as imagens
convertendo para WebP e redimensionando conforme necessário.
"""

import os
import io
from PIL import Image, ImageOps
from django.core.files.base import ContentFile
from django.conf import settings
import uuid


class ImageOptimizer:
    """Classe responsável pela otimização automática de imagens"""
    
    # Configurações de qualidade e tamanhos
    WEBP_QUALITY = 85
    JPEG_QUALITY = 90
    
    # Tamanhos padrão para diferentes tipos de imagem
    SIZES = {
        'produto': {
            'thumb': (150, 150),
            'medium': (300, 300), 
            'large': (800, 800),
        },
        'categoria': {
            'thumb': (100, 100),
            'medium': (250, 250),
        },
        'restaurante': {
            'logo': (200, 200),
            'banner': (1200, 400),
            'favicon': (32, 32),
        },
        'avatar': {
            'thumb': (50, 50),
            'medium': (150, 150),
        }
    }
    
    @classmethod
    def optimize_image(cls, image_file, image_type='produto', maintain_aspect_ratio=True):
        """
        Otimiza uma imagem, criando versões em diferentes tamanhos e formatos.
        
        Args:
            image_file: Arquivo de imagem do Django
            image_type: Tipo da imagem ('produto', 'categoria', 'restaurante', 'avatar')
            maintain_aspect_ratio: Se deve manter a proporção original
            
        Returns:
            dict: Dicionário com as versões otimizadas da imagem
        """
        try:
            # Abre a imagem original
            original_image = Image.open(image_file)
            
            # Converte para RGB se necessário (para suportar PNG com transparência)
            if original_image.mode in ('RGBA', 'LA', 'P'):
                rgb_image = Image.new('RGB', original_image.size, (255, 255, 255))
                rgb_image.paste(original_image, mask=original_image.split()[-1] if 'A' in original_image.mode else None)
                original_image = rgb_image
            
            # Aplicar rotação automática baseada nos dados EXIF
            original_image = ImageOps.exif_transpose(original_image)
            
            results = {}
            sizes_config = cls.SIZES.get(image_type, cls.SIZES['produto'])
            
            for size_name, dimensions in sizes_config.items():
                # Redimensiona a imagem
                resized_image = cls._resize_image(original_image, dimensions, maintain_aspect_ratio)
                
                # Salva em formato WebP
                webp_file = cls._save_as_webp(resized_image, image_file.name, size_name)
                results[f'{size_name}_webp'] = webp_file
                
                # Salva também em JPEG como fallback
                jpeg_file = cls._save_as_jpeg(resized_image, image_file.name, size_name)
                results[f'{size_name}_jpeg'] = jpeg_file
            
            return results
            
        except Exception as e:
            print(f"Erro ao otimizar imagem: {e}")
            return None
    
    @classmethod
    def _resize_image(cls, image, target_size, maintain_aspect_ratio=True):
        """Redimensiona uma imagem mantendo ou não a proporção"""
        if maintain_aspect_ratio:
            # Redimensiona mantendo a proporção e centraliza
            image.thumbnail(target_size, Image.Resampling.LANCZOS)
            
            # Cria uma nova imagem com fundo branco no tamanho exato
            new_image = Image.new('RGB', target_size, (255, 255, 255))
            
            # Calcula a posição para centralizar
            paste_x = (target_size[0] - image.size[0]) // 2
            paste_y = (target_size[1] - image.size[1]) // 2
            
            new_image.paste(image, (paste_x, paste_y))
            return new_image
        else:
            # Redimensiona forçando o tamanho exato (pode distorcer)
            return image.resize(target_size, Image.Resampling.LANCZOS)
    
    @classmethod
    def _save_as_webp(cls, image, original_name, size_suffix):
        """Salva imagem em formato WebP"""
        output = io.BytesIO()
        image.save(output, format='WEBP', quality=cls.WEBP_QUALITY, optimize=True)
        output.seek(0)
        
        # Gera nome único para o arquivo
        base_name = os.path.splitext(os.path.basename(original_name))[0]
        filename = f"{base_name}_{size_suffix}_{uuid.uuid4().hex[:8]}.webp"
        
        return ContentFile(output.getvalue(), name=filename)
    
    @classmethod
    def _save_as_jpeg(cls, image, original_name, size_suffix):
        """Salva imagem em formato JPEG como fallback"""
        output = io.BytesIO()
        image.save(output, format='JPEG', quality=cls.JPEG_QUALITY, optimize=True)
        output.seek(0)
        
        # Gera nome único para o arquivo
        base_name = os.path.splitext(os.path.basename(original_name))[0]
        filename = f"{base_name}_{size_suffix}_{uuid.uuid4().hex[:8]}.jpg"
        
        return ContentFile(output.getvalue(), name=filename)
    
    @classmethod
    def get_optimized_url(cls, image_field, size='medium', format='webp', request=None):
        """
        Retorna a URL da versão otimizada da imagem
        
        Args:
            image_field: Campo ImageField do modelo
            size: Tamanho desejado ('thumb', 'medium', 'large')
            format: Formato desejado ('webp', 'jpeg')
            request: Request objeto para detectar suporte a WebP
            
        Returns:
            str: URL da imagem otimizada
        """
        if not image_field:
            return None
            
        # Verifica se o navegador suporta WebP através do request
        supports_webp = False
        if request and hasattr(request, 'META'):
            accept_header = request.META.get('HTTP_ACCEPT', '')
            supports_webp = 'image/webp' in accept_header
        
        # Escolhe o formato baseado no suporte do navegador
        chosen_format = 'webp' if (format == 'webp' and supports_webp) else 'jpeg'
        
        # Constrói o nome do arquivo otimizado
        if hasattr(image_field, f'url_{size}_{chosen_format}'):
            return getattr(image_field, f'url_{size}_{chosen_format}')
        
        # Fallback para a imagem original se não existir a versão otimizada
        return image_field.url if image_field else None


class OptimizedImageField:
    """Mixin para campos de imagem que devem ser otimizados automaticamente"""
    
    def __init__(self, image_type='produto', *args, **kwargs):
        self.image_type = image_type
        super().__init__(*args, **kwargs)
    
    def save_optimized_versions(self, instance, image_file):
        """Salva versões otimizadas da imagem"""
        if image_file:
            optimized_versions = ImageOptimizer.optimize_image(
                image_file, 
                self.image_type
            )
            
            if optimized_versions:
                # Salva as referências das versões otimizadas no modelo
                for version_name, version_file in optimized_versions.items():
                    setattr(instance, f'{self.attname}_{version_name}', version_file)
                
                return optimized_versions
        
        return None