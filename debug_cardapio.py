#!/usr/bin/env python
import os
import sys
import django

# Setup do Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'menuly.settings')
django.setup()

from core.models import Restaurante, Categoria, Produto
from django.db.models import Prefetch

print("🔍 DEBUGANDO CARDÁPIO")
print("=" * 50)

# 1. Verificar se existe restaurante
restaurante = Restaurante.objects.filter(status='ativo').first()
print(f"1. Restaurante encontrado: {restaurante}")
if restaurante:
    print(f"   - Nome: {restaurante.nome}")
    print(f"   - Slug: {restaurante.slug}")
    print(f"   - Status: {restaurante.status}")

# 2. Verificar categorias
print("\n2. Categorias do restaurante:")
if restaurante:
    categorias_all = restaurante.categorias.all()
    categorias_ativas = restaurante.categorias.filter(ativo=True)
    print(f"   - Total de categorias: {categorias_all.count()}")
    print(f"   - Categorias ativas: {categorias_ativas.count()}")
    
    for categoria in categorias_ativas:
        print(f"   - {categoria.nome} (ativo: {categoria.ativo}, ordem: {categoria.ordem})")

# 3. Verificar produtos
print("\n3. Produtos do restaurante:")
if restaurante:
    produtos_all = restaurante.produtos.all()
    produtos_disponiveis = restaurante.produtos.filter(disponivel=True)
    print(f"   - Total de produtos: {produtos_all.count()}")
    print(f"   - Produtos disponíveis: {produtos_disponiveis.count()}")

# 4. Simular a query da CardapioView
print("\n4. Simulando query da CardapioView:")
if restaurante:
    categorias = restaurante.categorias.filter(
        ativo=True
    ).prefetch_related(
        Prefetch('produtos', queryset=Produto.objects.filter(disponivel=True).order_by('ordem', 'nome'))
    ).order_by('ordem', 'nome')
    
    print(f"   - Categorias retornadas: {categorias.count()}")
    
    for categoria in categorias:
        produtos_categoria = categoria.produtos.all()
        print(f"   - {categoria.nome}: {produtos_categoria.count()} produtos")
        
        for produto in produtos_categoria[:3]:  # Mostrar apenas 3 primeiros
            print(f"     * {produto.nome} (R$ {produto.preco}) - Disponível: {produto.disponivel}")

# 5. Verificar estrutura do template context
print("\n5. Dados para o template (categorias_cardapio):")
if restaurante:
    context_data = []
    for categoria in categorias:
        produtos_lista = list(categoria.produtos.all())
        context_data.append({
            'categoria': categoria.nome,
            'slug': categoria.slug,
            'produtos_count': len(produtos_lista),
            'produtos': [p.nome for p in produtos_lista[:5]]  # Primeiros 5
        })
    
    print(f"   - Total de categorias no context: {len(context_data)}")
    for item in context_data:
        print(f"   - {item['categoria']}: {item['produtos_count']} produtos")
        if item['produtos']:
            print(f"     Exemplos: {', '.join(item['produtos'])}")

print("\n" + "=" * 50)
print("🔍 DEBUG CONCLUÍDO")
