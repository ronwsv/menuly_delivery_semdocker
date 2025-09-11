"""
Comando para adicionar campos de imagens otimizadas aos modelos existentes.
Este comando cria uma migration personalizada para adicionar os campos necessários.
"""

from django.core.management.base import BaseCommand
from django.db import connection
from django.apps import apps


class Command(BaseCommand):
    help = 'Adiciona campos de imagens otimizadas aos modelos existentes'

    def handle(self, *args, **options):
        self.stdout.write('Criando campos para imagens otimizadas...')
        
        # SQL para adicionar campos de imagens otimizadas
        sql_commands = []
        
        # Campos para Produto
        produto_fields = [
            'imagem_principal_thumb_webp', 'imagem_principal_thumb_jpeg',
            'imagem_principal_medium_webp', 'imagem_principal_medium_jpeg',
            'imagem_principal_large_webp', 'imagem_principal_large_jpeg',
        ]
        
        for field in produto_fields:
            sql_commands.append(f"""
                ALTER TABLE produtos 
                ADD COLUMN {field} VARCHAR(100) NULL;
            """)
        
        # Campos para Categoria
        categoria_fields = [
            'imagem_thumb_webp', 'imagem_thumb_jpeg',
            'imagem_medium_webp', 'imagem_medium_jpeg',
        ]
        
        for field in categoria_fields:
            sql_commands.append(f"""
                ALTER TABLE categorias 
                ADD COLUMN {field} VARCHAR(100) NULL;
            """)
        
        # Campos para Restaurante
        restaurante_fields = [
            # Logo
            'logo_thumb_webp', 'logo_thumb_jpeg',
            'logo_medium_webp', 'logo_medium_jpeg',
            # Banner
            'banner_thumb_webp', 'banner_thumb_jpeg',
            'banner_medium_webp', 'banner_medium_jpeg',
            # Favicon
            'favicon_thumb_webp', 'favicon_thumb_jpeg',
            'favicon_medium_webp', 'favicon_medium_jpeg',
        ]
        
        for field in restaurante_fields:
            sql_commands.append(f"""
                ALTER TABLE restaurantes 
                ADD COLUMN {field} VARCHAR(100) NULL;
            """)
        
        # Campos para Usuario (avatar)
        usuario_fields = [
            'avatar_thumb_webp', 'avatar_thumb_jpeg',
            'avatar_medium_webp', 'avatar_medium_jpeg',
        ]
        
        for field in usuario_fields:
            sql_commands.append(f"""
                ALTER TABLE core_usuario 
                ADD COLUMN {field} VARCHAR(100) NULL;
            """)
        
        # Executa os comandos SQL
        with connection.cursor() as cursor:
            for sql in sql_commands:
                try:
                    cursor.execute(sql.strip())
                    self.stdout.write(f'✓ Campo adicionado: {sql.split("ADD COLUMN")[1].split(" ")[1]}')
                except Exception as e:
                    if 'Duplicate column name' in str(e) or 'already exists' in str(e):
                        self.stdout.write(f'ℹ Campo já existe: {sql.split("ADD COLUMN")[1].split(" ")[1]}')
                    else:
                        self.stderr.write(f'✗ Erro ao adicionar campo: {e}')
        
        self.stdout.write(
            self.style.SUCCESS('Campos de imagens otimizadas adicionados com sucesso!')
        )