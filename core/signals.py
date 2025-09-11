"""
Signals para otimização automática de imagens
Processa as imagens automaticamente quando os modelos são salvos.
"""

from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.core.files.storage import default_storage
from .models import Produto, Categoria, Restaurante, Usuario
from .image_optimizer import ImageOptimizer
import os


@receiver(post_save, sender=Produto)
def optimize_produto_image(sender, instance, created, **kwargs):
    """Otimiza imagens de produtos automaticamente após salvamento"""
    if instance.imagem_principal and (created or instance.imagem_principal):
        # Evita loop infinito verificando se já foi processado
        if not hasattr(instance, '_image_processing'):
            instance._image_processing = True
            
            try:
                # Otimiza a imagem
                optimized_versions = ImageOptimizer.optimize_image(
                    instance.imagem_principal,
                    image_type='produto'
                )
                
                if optimized_versions:
                    # Salva as versões otimizadas
                    for version_name, version_file in optimized_versions.items():
                        field_name = f'imagem_principal_{version_name}'
                        
                        # Salva o arquivo otimizado
                        if hasattr(instance, field_name):
                            setattr(instance, field_name, version_file)
                    
                    # Salva novamente apenas os campos das imagens otimizadas
                    update_fields = [
                        f'imagem_principal_{version_name}' 
                        for version_name in optimized_versions.keys()
                        if hasattr(instance, f'imagem_principal_{version_name}')
                    ]
                    
                    if update_fields:
                        # Salva sem trigger de signals para evitar loop
                        Produto.objects.filter(pk=instance.pk).update(**{
                            field: getattr(instance, field) 
                            for field in update_fields
                        })
                        
            except Exception as e:
                print(f"Erro ao otimizar imagem do produto {instance.id}: {e}")
            
            finally:
                # Remove flag para permitir futuras otimizações
                delattr(instance, '_image_processing')


@receiver(post_save, sender=Categoria)
def optimize_categoria_image(sender, instance, created, **kwargs):
    """Otimiza imagens de categorias automaticamente após salvamento"""
    if instance.imagem and (created or instance.imagem):
        if not hasattr(instance, '_image_processing'):
            instance._image_processing = True
            
            try:
                optimized_versions = ImageOptimizer.optimize_image(
                    instance.imagem,
                    image_type='categoria'
                )
                
                if optimized_versions:
                    for version_name, version_file in optimized_versions.items():
                        field_name = f'imagem_{version_name}'
                        if hasattr(instance, field_name):
                            setattr(instance, field_name, version_file)
                    
                    update_fields = [
                        f'imagem_{version_name}' 
                        for version_name in optimized_versions.keys()
                        if hasattr(instance, f'imagem_{version_name}')
                    ]
                    
                    if update_fields:
                        Categoria.objects.filter(pk=instance.pk).update(**{
                            field: getattr(instance, field) 
                            for field in update_fields
                        })
                        
            except Exception as e:
                print(f"Erro ao otimizar imagem da categoria {instance.id}: {e}")
            
            finally:
                delattr(instance, '_image_processing')


@receiver(post_save, sender=Restaurante)
def optimize_restaurante_images(sender, instance, created, **kwargs):
    """Otimiza imagens do restaurante (logo, banner, favicon)"""
    images_to_process = [
        ('logo', 'restaurante'),
        ('banner', 'restaurante'),
        ('favicon', 'restaurante'),
    ]
    
    for image_field, image_type in images_to_process:
        image_value = getattr(instance, image_field)
        if image_value and (created or image_value):
            if not hasattr(instance, f'_{image_field}_processing'):
                setattr(instance, f'_{image_field}_processing', True)
                
                try:
                    optimized_versions = ImageOptimizer.optimize_image(
                        image_value,
                        image_type=image_type
                    )
                    
                    if optimized_versions:
                        for version_name, version_file in optimized_versions.items():
                            field_name = f'{image_field}_{version_name}'
                            if hasattr(instance, field_name):
                                setattr(instance, field_name, version_file)
                        
                        update_fields = [
                            f'{image_field}_{version_name}' 
                            for version_name in optimized_versions.keys()
                            if hasattr(instance, f'{image_field}_{version_name}')
                        ]
                        
                        if update_fields:
                            Restaurante.objects.filter(pk=instance.pk).update(**{
                                field: getattr(instance, field) 
                                for field in update_fields
                            })
                            
                except Exception as e:
                    print(f"Erro ao otimizar {image_field} do restaurante {instance.id}: {e}")
                
                finally:
                    delattr(instance, f'_{image_field}_processing')


@receiver(post_save, sender=Usuario)
def optimize_usuario_avatar(sender, instance, created, **kwargs):
    """Otimiza avatar do usuário"""
    if instance.avatar and (created or instance.avatar):
        if not hasattr(instance, '_avatar_processing'):
            instance._avatar_processing = True
            
            try:
                optimized_versions = ImageOptimizer.optimize_image(
                    instance.avatar,
                    image_type='avatar'
                )
                
                if optimized_versions:
                    for version_name, version_file in optimized_versions.items():
                        field_name = f'avatar_{version_name}'
                        if hasattr(instance, field_name):
                            setattr(instance, field_name, version_file)
                    
                    update_fields = [
                        f'avatar_{version_name}' 
                        for version_name in optimized_versions.keys()
                        if hasattr(instance, f'avatar_{version_name}')
                    ]
                    
                    if update_fields:
                        Usuario.objects.filter(pk=instance.pk).update(**{
                            field: getattr(instance, field) 
                            for field in update_fields
                        })
                        
            except Exception as e:
                print(f"Erro ao otimizar avatar do usuário {instance.id}: {e}")
            
            finally:
                delattr(instance, '_avatar_processing')


@receiver(pre_delete, sender=Produto)
def cleanup_produto_optimized_images(sender, instance, **kwargs):
    """Remove imagens otimizadas quando um produto é deletado"""
    _cleanup_optimized_images(instance, 'imagem_principal', 'produto')


@receiver(pre_delete, sender=Categoria)
def cleanup_categoria_optimized_images(sender, instance, **kwargs):
    """Remove imagens otimizadas quando uma categoria é deletada"""
    _cleanup_optimized_images(instance, 'imagem', 'categoria')


@receiver(pre_delete, sender=Restaurante)
def cleanup_restaurante_optimized_images(sender, instance, **kwargs):
    """Remove imagens otimizadas quando um restaurante é deletado"""
    for image_field in ['logo', 'banner', 'favicon']:
        _cleanup_optimized_images(instance, image_field, 'restaurante')


@receiver(pre_delete, sender=Usuario)
def cleanup_usuario_optimized_images(sender, instance, **kwargs):
    """Remove imagens otimizadas quando um usuário é deletado"""
    _cleanup_optimized_images(instance, 'avatar', 'avatar')


def _cleanup_optimized_images(instance, base_field_name, image_type):
    """Remove arquivos de imagens otimizadas do storage"""
    sizes = ImageOptimizer.SIZES.get(image_type, ImageOptimizer.SIZES['produto'])
    
    for size_name in sizes.keys():
        for format_type in ['webp', 'jpeg']:
            field_name = f'{base_field_name}_{size_name}_{format_type}'
            if hasattr(instance, field_name):
                image_field = getattr(instance, field_name)
                if image_field:
                    try:
                        # Remove o arquivo do storage
                        if default_storage.exists(image_field.name):
                            default_storage.delete(image_field.name)
                    except Exception as e:
                        print(f"Erro ao remover imagem otimizada {field_name}: {e}")