#!/usr/bin/env python3
import os
import re

# Mapeamento de emojis para texto
emoji_map = {
    '🛒': 'CART',
    '📦': 'PACKAGE', 
    '✅': 'OK',
    '💰': 'MONEY',
    '🆕': 'NEW',
    '❌': 'ERROR',
    '🔧': 'DEBUG',
    '🔍': 'SEARCH',
    '🔢': 'COUNT',
    '📊': 'STATS',
    '⚠️': 'WARN',
    '🚫': 'BLOCKED',
    '💡': 'IDEA',
    '📝': 'NOTE',
    '🎯': 'TARGET',
    '⭐': 'STAR',
    '🌟': 'SHINE',
    '💯': 'PERFECT',
    '🎨': 'DESIGN',
    '🎉': 'PARTY',
    '🎊': 'CELEBRATION',
    '🔥': 'FIRE',
    '💥': 'BOOM',
    '⚡': 'LIGHTNING',
    '🌈': 'RAINBOW',
    '✨': 'SPARKLE',
    '🎭': 'THEATER',
    '🎪': 'CIRCUS',
    '🎸': 'GUITAR',
    '🎤': 'MIC',
    '🎧': 'HEADPHONE',
    '🎬': 'MOVIE',
    '🎮': 'GAME',
    '🎲': 'DICE',
    '🎰': 'SLOT',
    '🎳': 'BOWLING',
    '🏆': 'TROPHY',
    '🏅': 'MEDAL',
    '🏃‍♂️': 'RUNNING',
    '🚀': 'ROCKET',
    '🛸': 'UFO',
    '🌍': 'EARTH',
    '🌎': 'WORLD',
    '🌏': 'GLOBE',
    '🔑': 'KEY',
    '📡': 'SIGNAL',
    '📋': 'LIST',
    '📄': 'DOC',
    '📂': 'FOLDER',
    '💻': 'COMPUTER',
    '📱': 'PHONE',
    '⌚': 'WATCH',
    '📷': 'CAMERA',
    '🌐': 'NETWORK',
    '🔴': 'RED'
}

def fix_emojis_in_file(file_path):
    """Remove emojis from a single file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Substituir emojis
        for emoji, replacement in emoji_map.items():
            content = content.replace(emoji, replacement)
        
        # Check if any changes were made
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Fixed: {file_path}")
            return True
        else:
            print(f"No emojis found: {file_path}")
            return False
            
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def fix_all_remaining_emojis():
    """Fix emojis in all remaining template files"""
    template_files = [
        'templates/loja/checkout_novo.html',
        'templates/loja/home.html', 
        'templates/loja/confirmacao_pedido_novo.html',
        'templates/loja/checkout_completo.html',
        'templates/loja/produto_detalhe.html'
    ]
    
    for file_path in template_files:
        if os.path.exists(file_path):
            fix_emojis_in_file(file_path)
        else:
            print(f"File not found: {file_path}")

if __name__ == '__main__':
    fix_all_remaining_emojis()