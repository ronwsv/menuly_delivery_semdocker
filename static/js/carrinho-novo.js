/**
 * Sistema de Carrinho Menuly - Versão Corrigida v2.1
 * Última atualização: 2024-09-04 22:30 - Verificação completa de variáveis 'total' v2
 */

// Variáveis de controle global
var carregandoCarrinho = false;
var ultimaChamadaCarrinho = 0;
var processandoProduto = null;

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

// Função global para adicionar ao carrinho
window.adicionarAoCarrinho = function(item) {
    console.log('🛒 adicionarAoCarrinho chamada:', item);
    
    // Obter slug do restaurante da URL atual
    var currentPath = window.location.pathname;
    var slugMatch = currentPath.match(/^\/([^\/]+)\//);
    
    if (!slugMatch) {
        console.error('❌ Slug do restaurante não encontrado na URL');
        mostrarToast('Erro: não foi possível identificar o restaurante', 'error');
        return;
    }
    
    var restauranteSlug = slugMatch[1];
    var url = '/' + restauranteSlug + '/carrinho/adicionar/';
    
    // Obter CSRF token
    var csrfToken = document.querySelector('[name=csrfmiddlewaretoken]') || 
                    document.querySelector('meta[name=csrf-token]') || 
                    { value: getCookie('csrftoken') };
    
    // Enviar para o backend
    fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken.value || csrfToken.content || getCookie('csrftoken')
        },
        body: JSON.stringify(item)
    })
    .then(function(response) {
        console.log('📡 Resposta recebida:', response.status, response.statusText);
        console.log('🔧 Usando nova versão do código de erro!');
        if (!response.ok) {
            // Tentar ler o corpo da resposta para ver detalhes do erro
            return response.text().then(function(errorText) {
                console.error('❌ Erro do servidor (texto completo):', errorText);
                try {
                    var errorData = JSON.parse(errorText);
                    console.error('❌ Erro JSON parseado:', errorData);
                    throw new Error('Erro ' + response.status + ': ' + (errorData.error || errorData.message || errorText));
                } catch (e) {
                    console.error('❌ Erro ao parsear JSON:', e);
                    throw new Error('Erro ' + response.status + ': ' + errorText);
                }
            });
        }
        return response.json();
    })
    .then(function(data) {
        console.log('📦 Dados da resposta:', data);
        if (data.success) {
            // Atualizar contador do carrinho
            atualizarContadorCarrinho();
            
            // Se sidebar está aberto, atualizar dados
            const sidebar = document.getElementById('carrinho-sidebar');
            if (sidebar && sidebar.classList.contains('show')) {
                carregarDadosCarrinhoSidebar();
            }
            
            // Mostrar toast de sucesso
            mostrarToast('Produto adicionado ao carrinho!', 'success');
            
            // Se há um toast do Bootstrap na página, mostrar também
            if (typeof bootstrap !== 'undefined') {
                var toastEl = document.getElementById('toast-sucesso');
                if (toastEl) {
                    var toast = new bootstrap.Toast(toastEl);
                    toast.show();
                }
            }
            
        } else {
            console.error('❌ Erro no servidor:', data.error);
            mostrarToast('Erro: ' + (data.error || 'Falha ao adicionar produto.'), 'error');
        }
    })
    .catch(function(error) {
        console.error('❌ Erro na requisição:', error);
        mostrarToast('Erro ao adicionar produto ao carrinho', 'error');
    });
};

// Função global para atualizar contador
window.atualizarContadorCarrinho = function() {
    // Verificar se estamos em uma página de loja
    var currentPath = window.location.pathname;
    
    // Extrair slug do restaurante da URL
    var slugMatch = currentPath.match(/^\/([^\/]+)\//);
    
    if (!slugMatch) {
        console.log('ℹ️ Não está em página de restaurante, ocultando carrinho');
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
    })
    .catch(function(error) {
        console.error('⚠️ Erro ao carregar contador do carrinho:', error);
    });
};

// Função para atualizar badge visual
function atualizarBadgeCarrinho(total) {
    var badges = document.querySelectorAll('.carrinho-count, .badge-carrinho');
    badges.forEach(function(badge) {
        if (total > 0) {
            badge.textContent = total;
            badge.style.display = 'inline';
        } else {
            badge.textContent = '0';
            badge.style.display = 'none';
        }
    });
}

// Função para ocultar contador
function ocultarContadorCarrinho() {
    var badges = document.querySelectorAll('.carrinho-count, .badge-carrinho');
    badges.forEach(function(badge) {
        badge.style.display = 'none';
    });
}

// Inicializar eventos do sidebar
function inicializarSidebarCarrinho() {
    console.log('🔧 Inicializando sidebar do carrinho...');
    
    // Botão para abrir carrinho
    const btnAbrirCarrinho = document.getElementById('btn-abrir-carrinho');
    if (btnAbrirCarrinho) {
        btnAbrirCarrinho.addEventListener('click', function() {
            console.log('🛒 Abrindo sidebar do carrinho');
            abrirCarrinhoSidebar();
        });
    }
    
    // Botão para finalizar pedido
    const btnFinalizarPedido = document.getElementById('btn-finalizar-pedido');
    if (btnFinalizarPedido) {
        btnFinalizarPedido.addEventListener('click', function() {
            // Extrair slug do restaurante da URL
            var currentPath = window.location.pathname;
            var slugMatch = currentPath.match(/^\/([^\/]+)\//);
            
            if (slugMatch) {
                var restauranteSlug = slugMatch[1];
                window.location.href = '/' + restauranteSlug + '/checkout/';
            }
        });
    }
    
    // Botão para limpar carrinho
    const btnLimparCarrinho = document.getElementById('btn-limpar-carrinho');
    if (btnLimparCarrinho) {
        btnLimparCarrinho.addEventListener('click', function() {
            if (confirm('Tem certeza que deseja limpar o carrinho?')) {
                limparCarrinho();
            }
        });
    }
    
    console.log('✅ Sidebar do carrinho inicializado');
}

// Função para abrir sidebar do carrinho
function abrirCarrinhoSidebar() {
    const sidebar = document.getElementById('carrinho-sidebar');
    if (sidebar) {
        // Carregar dados do carrinho antes de abrir
        carregarDadosCarrinhoSidebar();
        
        // Usar Bootstrap Offcanvas API
        const offcanvas = new bootstrap.Offcanvas(sidebar);
        offcanvas.show();
    } else {
        console.error('❌ Sidebar do carrinho não encontrado');
    }
}

// Função para carregar dados do carrinho no sidebar
function carregarDadosCarrinhoSidebar() {
    console.log('📦 Carregando dados do carrinho no sidebar...');
    
    // Extrair slug do restaurante da URL
    var currentPath = window.location.pathname;
    var slugMatch = currentPath.match(/^\/([^\/]+)\//);
    
    if (!slugMatch) {
        console.warn('⚠️ Não foi possível identificar o restaurante');
        mostrarCarrinhoVazio();
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
        console.log('📦 Carrinho carregado:', data.items ? data.items.length : 0, 'itens');
        renderizarCarrinhoSidebar(data);
    })
    .catch(function(error) {
        console.error('❌ Erro ao carregar dados do carrinho:', error);
        mostrarCarrinhoVazio();
    });
}

// Função para renderizar carrinho no sidebar
function renderizarCarrinhoSidebar(data) {
    const carrinhoHeader = document.getElementById('carrinho-header');
    const carrinhoItems = document.getElementById('carrinho-items');
    const carrinhoFooter = document.getElementById('carrinho-footer');
    const carrinhoVazio = document.getElementById('carrinho-vazio');
    const carrinhoTotal = document.getElementById('carrinho-total');
    const restauranteNome = document.getElementById('carrinho-restaurante-nome');
    const restauranteEndereco = document.getElementById('carrinho-restaurante-endereco');
    
    if (!data.items || data.items.length === 0) {
        mostrarCarrinhoVazio();
        return;
    }
    
    // Mostrar header com info do restaurante
    if (data.restaurante && carrinhoHeader && restauranteNome && restauranteEndereco) {
        restauranteNome.textContent = data.restaurante.nome;
        restauranteEndereco.textContent = data.restaurante.endereco || '';
        carrinhoHeader.style.display = 'block';
    }
    
    // Renderizar itens
    if (carrinhoItems) {
        let html = '';
        let total = 0;
        
        data.items.forEach(function(item) {
            const subtotal = item.preco_total || (item.preco_unitario * item.quantidade);
            total += subtotal;
            
            // Personalizações
            let personalizacoesHtml = '';
            if (item.personalizacoes && item.personalizacoes.length > 0) {
                const personalizacoesList = item.personalizacoes.map(p => {
                    let texto = p.nome;
                    if (p.preco_adicional && p.preco_adicional > 0) {
                        texto += ` (+R$ ${p.preco_adicional.toFixed(2).replace('.', ',')})`;
                    }
                    return texto;
                }).join(', ');
                personalizacoesHtml = `<small class="text-primary d-block">${personalizacoesList}</small>`;
            }
            
            // Observações
            let observacoesHtml = '';
            if (item.observacoes && item.observacoes.trim()) {
                observacoesHtml = `<small class="text-muted d-block"><i class="bi bi-chat-dots me-1"></i>${item.observacoes}</small>`;
            }
            
            html += `
                <div class="border-bottom p-3" data-item-id="${item.produto_id || item.id || i}">
                    <div class="d-flex justify-content-between align-items-start">
                        <div class="flex-grow-1 me-2">
                            <h6 class="mb-1">${item.nome}</h6>
                            <small class="text-muted">${item.quantidade}x R$ ${(item.preco_unitario || item.preco || 0).toFixed(2).replace('.', ',')}</small>
                            ${personalizacoesHtml}
                            ${observacoesHtml}
                        </div>
                        <div class="text-end">
                            <div class="fw-bold mb-1">R$ ${subtotal.toFixed(2).replace('.', ',')}</div>
                            <button type="button" 
                                    class="btn btn-sm btn-outline-danger" 
                                    onclick="removerItemCarrinho('${item.produto_id || item.id || i}')"
                                    title="Remover item">
                                <i class="bi bi-trash"></i>
                            </button>
                        </div>
                    </div>
                </div>
            `;
        });
        
        carrinhoItems.innerHTML = html;
        
        // Ocultar mensagem de carrinho vazio
        if (carrinhoVazio) {
            carrinhoVazio.style.display = 'none';
        }
    }
    
    // Mostrar total e footer
    if (carrinhoTotal) {
        const totalValue = data.total || 0;
        carrinhoTotal.textContent = `R$ ${totalValue.toFixed(2).replace('.', ',')}`;
    }
    
    if (carrinhoFooter) {
        carrinhoFooter.style.display = 'block';
    }
}

// Função para mostrar carrinho vazio
function mostrarCarrinhoVazio() {
    const carrinhoHeader = document.getElementById('carrinho-header');
    const carrinhoItems = document.getElementById('carrinho-items');
    const carrinhoFooter = document.getElementById('carrinho-footer');
    const carrinhoVazio = document.getElementById('carrinho-vazio');
    
    if (carrinhoHeader) carrinhoHeader.style.display = 'none';
    if (carrinhoFooter) carrinhoFooter.style.display = 'none';
    
    if (carrinhoVazio) {
        carrinhoVazio.style.display = 'block';
    }
    
    if (carrinhoItems) {
        carrinhoItems.innerHTML = `
            <div class="p-4 text-center text-muted" id="carrinho-vazio">
                <i class="bi bi-cart-x fs-1 mb-3 d-block"></i>
                <h6>Seu carrinho está vazio</h6>
                <p class="small mb-0">Adicione produtos para continuar</p>
            </div>
        `;
    }
}

// Função para limpar carrinho
function limparCarrinho() {
    // Extrair slug do restaurante da URL
    var currentPath = window.location.pathname;
    var slugMatch = currentPath.match(/^\/([^\/]+)\//);
    
    if (!slugMatch) {
        mostrarToast('Erro: não foi possível identificar o restaurante', 'error');
        return;
    }
    
    var restauranteSlug = slugMatch[1];
    var url = '/' + restauranteSlug + '/carrinho/limpar/';
    
    fetch(url, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
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
        if (data.success) {
            mostrarCarrinhoVazio();
            atualizarContadorCarrinho();
            mostrarToast('Carrinho limpo com sucesso!', 'success');
        } else {
            mostrarToast('Erro ao limpar carrinho', 'error');
        }
    })
    .catch(function(error) {
        console.error('❌ Erro ao limpar carrinho:', error);
        mostrarToast('Erro ao limpar carrinho', 'error');
    });
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
if (!document.getElementById('menuly-toast-styles')) {
    const toastStyles = document.createElement('style');
    toastStyles.id = 'menuly-toast-styles';
    toastStyles.textContent = `
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
    document.head.appendChild(toastStyles);
}

// Função para remover item do carrinho
window.removerItemCarrinho = function(itemId) {
    console.log('🗑️ Removendo item do carrinho:', itemId);
    
    // Obter slug do restaurante da URL atual
    var currentPath = window.location.pathname;
    var slugMatch = currentPath.match(/^\/([^\/]+)\//);
    
    if (!slugMatch) {
        console.error('❌ Slug do restaurante não encontrado na URL');
        mostrarToast('Erro: não foi possível identificar o restaurante', 'error');
        return;
    }
    
    var restauranteSlug = slugMatch[1];
    var url = '/' + restauranteSlug + '/carrinho/remover/';
    
    // Obter CSRF token
    var csrfToken = document.querySelector('[name=csrfmiddlewaretoken]') || 
                    document.querySelector('meta[name=csrf-token]') || 
                    { value: getCookie('csrftoken') };
    
    if (!csrfToken || !csrfToken.value) {
        console.error('❌ Token CSRF não encontrado');
        mostrarToast('Erro de segurança. Recarregue a página.', 'error');
        return;
    }
    
    // Fazer requisição para remover
    fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken.value
        },
        body: JSON.stringify({
            'produto_id': itemId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            mostrarToast('Item removido do carrinho', 'success');
            
            // Atualizar contador
            atualizarContadorCarrinho();
            
            // Recarregar carrinho
            carregarCarrinho();
        } else {
            console.error('❌ Erro ao remover item:', data.error);
            mostrarToast(data.error || 'Erro ao remover item', 'error');
        }
    })
    .catch(error => {
        console.error('❌ Erro na requisição:', error);
        mostrarToast('Erro de conexão', 'error');
    });
};

console.log('✅ Carrinho Menuly inicializado - v2.1 CORRIGIDO ' + new Date().toISOString());
