#!/usr/bin/env python3
"""Script para remover todos os emojis Unicode dos arquivos JavaScript"""

import os
import re

def fix_file(file_path):
    """Remove emojis Unicode de um arquivo"""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Remove emojis específicos que estão causando problemas
        emoji_map = {
            '🛒': '',
            '📦': '', 
            '✅': '',
            '💰': '',
            '🆕': '',
            '❌': '',
            '🔧': 'DEBUG',
            '🔍': '',
            '🔢': '',
            'ℹ️': '',
            '⚠️': 'WARN',
            '💥': '',
            '🎨': '',
            '📋': '',
            '🔓': '',
            '⏸️': '',
            '📡': '',
            '🏪': '',
            '📭': '',
            '🔄': '',
            '⏳': '',
            '📥': '',
            '🍕': ''
        }
        
        for emoji, replacement in emoji_map.items():
            content = content.replace(emoji, replacement)
        
        # Remove espaços duplos resultantes
        content = re.sub(r'  +', ' ', content)
        content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Fixed: {file_path}")
        
    except Exception as e:
        print(f"Error fixing {file_path}: {e}")

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Arquivos para corrigir
    files = [
        os.path.join(base_dir, 'static', 'js', 'carrinho-novo.js'),
        os.path.join(base_dir, 'templates', 'loja', 'produto_detalhe.html')
    ]
    
    for file_path in files:
        if os.path.exists(file_path):
            fix_file(file_path)
        else:
            print(f"File not found: {file_path}")

if __name__ == "__main__":
    main()