# Sistema de Otimização de Imagens - Menuly

Este documento descreve o sistema de otimização automática de imagens implementado no projeto Menuly, inspirado no sistema do WordPress.

## 🎯 Objetivo

Otimizar automaticamente as imagens enviadas para:
- **Melhorar performance**: Carregamento mais rápido das páginas
- **Economizar espaço**: Redução do tamanho dos arquivos
- **Melhorar experiência**: Imagens responsivas e adaptáveis
- **SEO**: Imagens otimizadas impactam positivamente no ranking

## 🚀 Funcionalidades

### Otimização Automática
- **Conversão para WebP**: Formato moderno com até 30% menos tamanho
- **Fallback JPEG**: Compatibilidade com navegadores antigos
- **Múltiplos tamanhos**: thumb, medium, large
- **Compressão inteligente**: Qualidade otimizada por tipo de imagem
- **Rotação automática**: Corrige orientação baseada em EXIF

### Tipos de Imagem Suportados
- **Produtos**: Imagem principal + galeria
- **Categorias**: Imagem de categoria
- **Restaurantes**: Logo, banner, favicon
- **Usuários**: Avatar

### Tamanhos Gerados

| Tipo | Thumb | Medium | Large |
|------|-------|--------|-------|
| Produto | 150x150 | 300x300 | 800x800 |
| Categoria | 100x100 | 250x250 | - |
| Restaurante | 200x200 | 1200x400 | - |
| Avatar | 50x50 | 150x150 | - |

## 📦 Instalação

### 1. Instalar dependências
```bash
pip install Pillow
```

### 2. Adicionar campos ao banco
```bash
python manage.py add_optimized_image_fields
```

### 3. Executar migrações (se necessário)
```bash
python manage.py makemigrations
python manage.py migrate
```

## 🔧 Uso nos Templates

### 1. Carregar as tags
```html
{% load image_tags %}
```

### 2. Imagem simples otimizada
```html
{% optimized_image produto.imagem_principal size="medium" alt="Produto" css_class="img-fluid" %}
```

### 3. Apenas a URL da imagem
```html
{% optimized_image_url produto.imagem_principal size="large" format="webp" %}
```

### 4. Imagem responsiva com srcset
```html
{% responsive_image produto.imagem_principal alt="Produto" css_class="img-fluid" %}
```

### 5. Galeria de imagens
```html
{% image_gallery produto.imagens.all size="large" show_thumbs=True %}
```

## 🎨 Exemplos Práticos

### Template de Produto
```html
{% load image_tags %}

<div class="produto-card">
    <!-- Imagem responsiva -->
    {% responsive_image produto.imagem_principal alt="{{ produto.nome }}" css_class="img-fluid" %}
    
    <div class="produto-info">
        <h3>{{ produto.nome }}</h3>
        <p>{{ produto.preco }}</p>
    </div>
</div>
```

### Lista de Produtos
```html
{% for produto in produtos %}
    <div class="col-md-4">
        {% optimized_image produto.imagem_principal size="medium" alt="{{ produto.nome }}" css_class="produto-thumb" %}
        <h5>{{ produto.nome }}</h5>
    </div>
{% endfor %}
```

### Galeria do Produto
```html
<div class="produto-galeria">
    {% image_gallery produto.imagens.all size="large" show_thumbs=True %}
</div>
```

## ⚙️ Configuração Avançada

### Personalizar qualidade
```python
# Em core/image_optimizer.py
WEBP_QUALITY = 85  # 0-100
JPEG_QUALITY = 90  # 0-100
```

### Personalizar tamanhos
```python
SIZES = {
    'produto': {
        'thumb': (200, 200),    # Personalizado
        'medium': (400, 400),   # Personalizado
        'large': (1000, 1000),  # Personalizado
    }
}
```

## 🔍 Como Funciona

### 1. Upload da Imagem
Quando uma imagem é enviada:
1. **Django Signal** detecta o upload
2. **ImageOptimizer** processa a imagem
3. **Múltiplas versões** são criadas automaticamente
4. **Arquivos** são salvos no storage

### 2. Exibição no Template
1. **Template tag** é usada
2. **Detecção de suporte** a WebP no navegador
3. **URL apropriada** é retornada
4. **Fallback** para JPEG se necessário

### 3. Estrutura de Arquivos
```
media/
├── produtos/
│   ├── produto_original.jpg
│   └── optimized/
│       ├── produtos/
│       │   ├── thumb/
│       │   │   ├── webp/
│       │   │   └── jpeg/
│       │   ├── medium/
│       │   └── large/
```

## 📊 Benefícios

### Performance
- **30-50% menor** tamanho de arquivo com WebP
- **Carregamento mais rápido** das páginas
- **Menos bandwidth** utilizada
- **Melhor experiência** no mobile

### SEO
- **Imagens otimizadas** impactam no ranking
- **Tempo de carregamento** é fator de ranking
- **Core Web Vitals** melhorados

### Desenvolvimento
- **Automático**: Não precisa otimizar manualmente
- **Flexível**: Template tags simples
- **Responsivo**: Suporte nativo a srcset
- **Compatível**: Fallback para navegadores antigos

## 🛠️ Comandos Úteis

### Reprocessar imagens existentes
```bash
python manage.py shell
>>> from core.models import Produto
>>> for produto in Produto.objects.all():
...     produto.save()  # Triggers optimization
```

### Verificar tamanhos de arquivo
```python
import os
from core.models import Produto

produto = Produto.objects.first()
original_size = os.path.getsize(produto.imagem_principal.path)
webp_size = os.path.getsize(produto.imagem_principal_medium_webp.path)
print(f"Redução: {((original_size - webp_size) / original_size) * 100:.1f}%")
```

## 🚨 Considerações

### Compatibilidade
- **WebP**: Suportado por 95% dos navegadores modernos
- **Fallback**: JPEG para compatibilidade total
- **Progressive Enhancement**: Funciona mesmo sem WebP

### Storage
- **Mais arquivos**: Cada imagem gera múltiplas versões
- **Mais espaço**: Trade-off entre espaço e performance
- **Cleanup**: Remoção automática ao deletar registros

### Performance
- **Processamento**: Demora extra no upload inicial
- **CPU**: Uso de CPU para redimensionamento
- **Async**: Considere processamento assíncrono para muitas imagens

## 📝 Próximos Passos

1. **Processamento assíncrono** com Celery
2. **CDN integration** para distribuição global
3. **Lazy loading** nativo
4. **Art direction** com diferentes crops
5. **Analytics** de performance de imagens