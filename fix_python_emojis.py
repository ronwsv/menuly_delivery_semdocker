#!/usr/bin/env python3
"""Script para remover emojis dos arquivos Python que podem afetar JavaScript"""

import os
import re

def fix_python_file(file_path):
    """Remove emojis Unicode de um arquivo Python"""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Mapa de emojis específicos que estão causando problemas no JavaScript
        emoji_map = {
            '🍕': 'PIZZA',
            '🛒': 'CART', 
            '📦': 'PACKAGE',
            '✅': 'OK',
            '💰': 'MONEY',
            '🆕': 'NEW',
            '❌': 'ERROR',
            '🔧': 'DEBUG',
            '🔍': 'SEARCH',
            '🔢': 'COUNT',
            'ℹ️': 'INFO',
            '⚠️': 'WARN',
            '💥': 'CRASH',
            '🎨': 'STYLE',
            '📋': 'LIST',
            '🔓': 'UNLOCK',
            '⏸️': 'PAUSE',
            '📡': 'SIGNAL',
            '🏪': 'STORE',
            '📭': 'MAIL',
            '🔄': 'RELOAD',
            '⏳': 'WAIT',
            '📥': 'INBOX',
            '🛍️': 'SHOPPING',
            '🏍️': 'DELIVERY'
        }
        
        original_content = content
        
        # Substituir emojis em prints e logs
        for emoji, replacement in emoji_map.items():
            content = content.replace(emoji, replacement)
        
        # Remove espaços duplos resultantes
        content = re.sub(r'  +', ' ', content)
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Fixed: {file_path}")
            return True
        else:
            print(f"No emojis found: {file_path}")
            return False
            
    except Exception as e:
        print(f"Error fixing {file_path}: {e}")
        return False

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Arquivos Python que podem afetar o JavaScript via templates
    files = [
        os.path.join(base_dir, 'loja', 'views.py'),
        os.path.join(base_dir, 'templates', 'base.html'),
        os.path.join(base_dir, 'templates', 'loja', 'cardapio.html')
    ]
    
    for file_path in files:
        if os.path.exists(file_path):
            fix_python_file(file_path)
        else:
            print(f"File not found: {file_path}")

if __name__ == "__main__":
    main()