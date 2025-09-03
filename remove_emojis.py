#!/usr/bin/env python3
"""Script para remover emojis Unicode dos arquivos JavaScript"""

import re
import os

def remove_emojis_from_file(file_path):
    """Remove emojis Unicode de um arquivo"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Lista de emojis específicos para remover
        emoji_replacements = {
            '🛒': '',
            '📦': '',
            '✅': '',
            '💰': '',
            '🆕': '',
            '❌': '',
            '🔧': '',
            '🔍': '',
            '🔢': '',
            'ℹ️': '',
            '⚠️': '',
            '💥': '',
            '🎨': '',
            '📋': '',
            '🔓': '',
            '⏸️': '',
            '📡': '',
        }
        
        # Substituir cada emoji
        for emoji, replacement in emoji_replacements.items():
            content = content.replace(emoji, replacement)
        
        # Remover espaços duplos que podem ter sobrado
        content = re.sub(r'  +', ' ', content)
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✓ Emojis removidos de {file_path}")
            return True
        else:
            print(f"- Nenhum emoji encontrado em {file_path}")
            return False
            
    except Exception as e:
        print(f"✗ Erro ao processar {file_path}: {e}")
        return False

def main():
    """Função principal"""
    files_to_process = [
        'static/js/carrinho-novo.js',
        'templates/loja/produto_detalhe.html'
    ]
    
    base_path = os.path.dirname(os.path.abspath(__file__))
    
    for file_path in files_to_process:
        full_path = os.path.join(base_path, file_path)
        if os.path.exists(full_path):
            remove_emojis_from_file(full_path)
        else:
            print(f"✗ Arquivo não encontrado: {full_path}")

if __name__ == "__main__":
    main()