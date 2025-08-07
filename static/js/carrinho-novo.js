/**
 * Sistema de Carrinho Menuly - Integrado com Django
 * Versão: 3.0 - Com Sidebar
 */

// Estado global do carrinho
window.carrinhoSidebar = {
    items: [],
    total: 0,
    restaurante: null,
    isOpen: false
};

// Inicializar sistema quando DOM carregar
document.addEventListener('DOMContentLoaded', function() {
    console.log('🛒 Sistema de carrinho carregado');
    
    // Carregar contador inicial
    atualizarContadorCarrinho();
    
    // Inicializar sidebar
    inicializarSidebarCarrinho();
});

// Inicializar eventos do sidebar
function inicializarSidebarCarrinho() {
    // Botão para abrir carrinho
    var btnAbrirCarrinho = document.getElementById('btn-abrir-carrinho');
    if (btnAbrirCarrinho) {
        btnAbrirCarrinho.addEventListener('click', abrirCarrinhoSidebar);
    }
    
    // Botão finalizar pedido
    var btnFinalizarPedido = document.getElementById('btn-finalizar-pedido');
    if (btnFinalizarPedido) {
        btnFinalizarPedido.addEventListener('click', finalizarPedido);
    }
    
    // Botão limpar carrinho
    var btnLimparCarrinho = document.getElementById('btn-limpar-carrinho');
    if (btnLimparCarrinho) {
        btnLimparCarrinho.addEventListener('click', limparCarrinho);
    }
    
    // Overlay para fechar
    var overlay = document.getElementById('carrinho-overlay');
    if (overlay) {
        overlay.addEventListener('click', fecharCarrinhoSidebar);
    }
}

// Abrir sidebar do carrinho
function abrirCarrinhoSidebar() {
    console.log('🔓 Abrindo sidebar do carrinho');
    
    var sidebar = document.getElementById('carrinho-sidebar');
    if (sidebar) {
        // Carregar dados do carrinho
        carregarDadosCarrinho();
        
        // Mostrar sidebar usando Bootstrap Offcanvas
        var offcanvas = new bootstrap.Offcanvas(sidebar);
        offcanvas.show();
        
        window.carrinhoSidebar.isOpen = true;
    }
}

// Fechar sidebar do carrinho
function fecharCarrinhoSidebar() {
    var sidebar = document.getElementById('carrinho-sidebar');
    if (sidebar) {
        var offcanvas = bootstrap.Offcanvas.getInstance(sidebar);
        if (offcanvas) {
            offcanvas.hide();
        }
        window.carrinhoSidebar.isOpen = false;
    }
}

// Carregar dados do carrinho via AJAX
function carregarDadosCarrinho() {
    var currentPath = window.location.pathname;
    var slugMatch = currentPath.match(/^\/([^\/]+)\//);
    
    if (!slugMatch) {
        console.log('🔍 Não está em página de restaurante');
        return;
    }
    
    var restauranteSlug = slugMatch[1];
    
    fetch('/' + restauranteSlug + '/carrinho/', {
        method: 'GET',
        headers: {
            'Accept': 'application/json'
        }
    })
    .then(function(response) {
        if (response.ok) {
            return response.json();
        } else {
            throw new Error('Erro na resposta: ' + response.status);
        }
    })
    .then(function(data) {
        window.carrinhoSidebar.items = data.items || [];
        window.carrinhoSidebar.total = data.total || 0;
        window.carrinhoSidebar.restaurante = data.restaurante || null;
        
        renderizarCarrinhoSidebar();
        console.log('📋 Dados do carrinho carregados:', data);
    })
    .catch(function(error) {
        console.error('⚠️ Erro ao carregar carrinho:', error);
        mostrarToast('Erro ao carregar carrinho', 'error');
    });
}

// Renderizar conteúdo do sidebar
function renderizarCarrinhoSidebar() {
    var items = window.carrinhoSidebar.items;
    var total = window.carrinhoSidebar.total;
    var restaurante = window.carrinhoSidebar.restaurante;
    
    // Elementos do DOM
    var carrinhoVazio = document.getElementById('carrinho-vazio');
    var carrinhoItems = document.getElementById('carrinho-items');
    var carrinhoHeader = document.getElementById('carrinho-header');
    var carrinhoFooter = document.getElementById('carrinho-footer');
    var carrinhoTotal = document.getElementById('carrinho-total');
    
    if (items.length === 0) {
        // Carrinho vazio
        carrinhoVazio.style.display = 'block';
        carrinhoHeader.style.display = 'none';
        carrinhoFooter.style.display = 'none';
    } else {
        // Carrinho com itens
        carrinhoVazio.style.display = 'none';
        
        // Header do restaurante
        if (restaurante && carrinhoHeader) {
            carrinhoHeader.style.display = 'block';
            var nomeEl = document.getElementById('carrinho-restaurante-nome');
            var enderecoEl = document.getElementById('carrinho-restaurante-endereco');
            if (nomeEl) nomeEl.textContent = restaurante.nome;
            if (enderecoEl) enderecoEl.textContent = restaurante.endereco;
        }
        
        // Lista de itens
        renderizarItensCarrinho(items);
        
        // Footer com total
        if (carrinhoFooter) {
            carrinhoFooter.style.display = 'block';
            if (carrinhoTotal) {
                carrinhoTotal.textContent = 'R$ ' + formatarPreco(total);
            }
        }
    }
}

// Renderizar lista de itens
function renderizarItensCarrinho(items) {
    var container = document.getElementById('carrinho-items');
    if (!container) return;
    
    var html = '';
    
    for (var i = 0; i < items.length; i++) {
        var item = items[i];
        html += `
            <div class="border-bottom p-3" data-produto-id="${item.produto_id}">
                <div class="d-flex align-items-start">
                    <div class="flex-grow-1">
                        <h6 class="mb-1">${item.nome}</h6>
                        <p class="text-muted small mb-2">${item.categoria || ''}</p>
                        <div class="d-flex align-items-center">
                            <button class="btn btn-outline-secondary btn-sm" onclick="alterarQuantidade('${item.produto_id}', -1)">
                                <i class="bi bi-dash"></i>
                            </button>
                            <span class="mx-3 fw-bold">${item.quantidade}</span>
                            <button class="btn btn-outline-secondary btn-sm" onclick="alterarQuantidade('${item.produto_id}', 1)">
                                <i class="bi bi-plus"></i>
                            </button>
                        </div>
                    </div>
                    <div class="text-end">
                        <div class="fw-bold text-primary mb-2">R$ ${formatarPreco(item.preco_total)}</div>
                        <button class="btn btn-outline-danger btn-sm" onclick="removerItemCarrinho('${item.produto_id}')">
                            <i class="bi bi-trash"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;
    }
    
    container.innerHTML = html;
}

// Formatar preço
function formatarPreco(valor) {
    return parseFloat(valor).toFixed(2).replace('.', ',');
}

// Remover item do carrinho
window.removerItemCarrinho = function(produtoId) {
    var currentPath = window.location.pathname;
    var slugMatch = currentPath.match(/^\/([^\/]+)\//);
    
    if (!slugMatch) return;
    
    var restauranteSlug = slugMatch[1];
    
    fetch('/' + restauranteSlug + '/carrinho/remover/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            produto_id: produtoId
        })
    })
    .then(function(response) {
        return response.json();
    })
    .then(function(data) {
        if (data.success) {
            carregarDadosCarrinho();
            atualizarContadorCarrinho();
            mostrarToast('Item removido do carrinho', 'success');
        } else {
            mostrarToast('Erro ao remover item', 'error');
        }
    })
    .catch(function(error) {
        console.error('Erro:', error);
        mostrarToast('Erro ao remover item', 'error');
    });
};

// Alterar quantidade
window.alterarQuantidade = function(produtoId, delta) {
    var currentPath = window.location.pathname;
    var slugMatch = currentPath.match(/^\/([^\/]+)\//);
    
    if (!slugMatch) return;
    
    var restauranteSlug = slugMatch[1];
    
    fetch('/' + restauranteSlug + '/carrinho/alterar-quantidade/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            produto_id: produtoId,
            delta: delta
        })
    })
    .then(function(response) {
        return response.json();
    })
    .then(function(data) {
        if (data.success) {
            carregarDadosCarrinho();
            atualizarContadorCarrinho();
        } else {
            mostrarToast('Erro ao alterar quantidade', 'error');
        }
    })
    .catch(function(error) {
        console.error('Erro:', error);
        mostrarToast('Erro ao alterar quantidade', 'error');
    });
};

// Finalizar pedido
function finalizarPedido() {
    var currentPath = window.location.pathname;
    var slugMatch = currentPath.match(/^\/([^\/]+)\//);
    
    if (!slugMatch) return;
    
    var restauranteSlug = slugMatch[1];
    window.location.href = '/' + restauranteSlug + '/checkout/';
}

// Limpar carrinho
function limparCarrinho() {
    if (!confirm('Tem certeza que deseja limpar todo o carrinho?')) {
        return;
    }
    
    var currentPath = window.location.pathname;
    var slugMatch = currentPath.match(/^\/([^\/]+)\//);
    
    if (!slugMatch) return;
    
    var restauranteSlug = slugMatch[1];
    
    fetch('/' + restauranteSlug + '/carrinho/limpar/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(function(response) {
        return response.json();
    })
    .then(function(data) {
        if (data.success) {
            carregarDadosCarrinho();
            atualizarContadorCarrinho();
            mostrarToast('Carrinho limpo com sucesso', 'success');
        } else {
            mostrarToast('Erro ao limpar carrinho', 'error');
        }
    })
    .catch(function(error) {
        console.error('Erro:', error);
        mostrarToast('Erro ao limpar carrinho', 'error');
    });
}

// Função global para atualizar contador
window.atualizarContadorCarrinho = function() {
    // Verificar se estamos em uma página de loja
    var currentPath = window.location.pathname;
    
    // Extrair slug do restaurante da URL
    var slugMatch = currentPath.match(/^\/([^\/]+)\//);
    
    if (!slugMatch) {
        console.log('🔍 Não está em página de restaurante, ocultando carrinho');
        ocultarContadorCarrinho();
        return;
    }
    
    var restauranteSlug = slugMatch[1];
    
    // Fazer requisição para carrinho do restaurante
    fetch('/' + restauranteSlug + '/carrinho/', {
        method: 'GET',
        headers: {
            'Accept': 'application/json'
        }
    })
    .then(function(response) {
        if (response.ok) {
            return response.json();
        } else {
            throw new Error('Erro na resposta: ' + response.status);
        }
    })
    .then(function(data) {
        var total = data.carrinho_count || 0;
        atualizarBadgeCarrinho(total);
        console.log('🔢 Contador atualizado:', total);
        
        // Atualizar sidebar se estiver aberto
        if (window.carrinhoSidebar.isOpen) {
            window.carrinhoSidebar.items = data.items || [];
            window.carrinhoSidebar.total = data.total || 0;
            renderizarCarrinhoSidebar();
        }
    })
    .catch(function(error) {
        console.warn('⚠️ Erro ao atualizar contador:', error);
        ocultarContadorCarrinho();
    });
};

// Atualizar visual do badge
function atualizarBadgeCarrinho(count) {
    var badges = document.querySelectorAll('#carrinho-badge, .carrinho-count, .cart-count');
    
    for (var i = 0; i < badges.length; i++) {
        var badge = badges[i];
        if (badge) {
            badge.textContent = count;
            badge.style.display = count > 0 ? 'inline' : 'none';
        }
    }
}

// Ocultar contador
function ocultarContadorCarrinho() {
    var badges = document.querySelectorAll('#carrinho-badge, .carrinho-count, .cart-count');
    for (var i = 0; i < badges.length; i++) {
        var badge = badges[i];
        if (badge) {
            badge.style.display = 'none';
        }
    }
}

// Função para obter cookie CSRF
function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Função global para mostrar toast
window.mostrarToast = function(message, type = 'info') {
    // Remover toasts existentes
    document.querySelectorAll('.toast-menuly').forEach(toast => toast.remove());
    
    // Criar novo toast
    const toast = document.createElement('div');
    toast.className = `toast-menuly alert alert-${type === 'success' ? 'success' : type === 'error' ? 'danger' : 'info'} position-fixed`;
    toast.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px; animation: slideInRight 0.3s ease;';
    
    const icon = type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle';
    
    toast.innerHTML = `
        <div class="d-flex align-items-center">
            <i class="bi bi-${icon} me-2"></i>
            <span>${message}</span>
            <button type="button" class="btn-close ms-auto" aria-label="Close"></button>
        </div>
    `;
    
    // Adicionar evento de fechar
    toast.querySelector('.btn-close').addEventListener('click', () => {
        toast.remove();
    });
    
    document.body.appendChild(toast);
    
    // Auto remover após 4 segundos
    setTimeout(() => {
        if (toast.parentNode) {
            toast.remove();
        }
    }, 4000);
};

// CSS para animações
const style = document.createElement('style');
style.textContent = `
    @keyframes slideInRight {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    .toast-menuly {
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        border: none;
        border-radius: 8px;
    }
`;
document.head.appendChild(style);

console.log('✅ Carrinho Menuly inicializado');
