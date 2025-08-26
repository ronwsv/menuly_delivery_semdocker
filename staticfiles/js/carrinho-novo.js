/**
 * Sistema de Carrinho Menuly - Integrado com Django
 * Versão: 3.0 - Com Sidebar
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

// Variável para controlar debounce
var ultimaChamadaCarrinho = 0;

// Abrir sidebar do carrinho
function abrirCarrinhoSidebar() {
    console.log('🔓 Abrindo sidebar do carrinho');
    
    // Debounce: evitar múltiplas chamadas em sequência
    var agora = Date.now();
    if (agora - ultimaChamadaCarrinho < 500) {
        console.log('⏸️ Chamada muito recente, ignorando...');
        return;
    }
    ultimaChamadaCarrinho = agora;
    
    var sidebar = document.getElementById('carrinho-sidebar');
    if (!sidebar) {
        console.error('❌ Elemento sidebar não encontrado!');
        return;
    }
    
    // Carregar dados do carrinho
    carregarDadosCarrinho();
    
    // Mostrar sidebar usando Bootstrap Offcanvas
    var offcanvas = new bootstrap.Offcanvas(sidebar);
    offcanvas.show();
    
    window.carrinhoSidebar.isOpen = true;
    console.log('✅ Sidebar aberto com sucesso');
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

// Aguardar elementos do sidebar estarem disponíveis
function aguardarElementosSidebar(callback, maxTentativas = 50) {
    var tentativas = 0;
    
    function verificarElementos() {
        tentativas++;
        console.log('🔍 Verificando elementos do sidebar (tentativa ' + tentativas + ')');
        
        // Primeiro verifica se o sidebar principal existe
        var sidebarContainer = document.getElementById('carrinho-sidebar');
        console.log('📋 Sidebar container existe:', !!sidebarContainer);
        
        // Se o sidebar não existe, tenta encontrar elementos na página
        if (!sidebarContainer) {
            console.log('⚠️ Sidebar container não encontrado, listando todos os elementos com ID carrinho*');
            var allElements = document.querySelectorAll('[id*="carrinho"]');
            for (var i = 0; i < allElements.length; i++) {
                console.log('  - Encontrado elemento:', allElements[i].id);
            }
        }
        
        var carrinhoVazio = document.getElementById('carrinho-vazio');
        var carrinhoItems = document.getElementById('carrinho-items');
        var carrinhoHeader = document.getElementById('carrinho-header');
        var carrinhoFooter = document.getElementById('carrinho-footer');
        var carrinhoTotal = document.getElementById('carrinho-total');
        
        // Debug detalhado dos elementos
        console.log('🔍 Estado dos elementos:');
        console.log('  - carrinho-vazio:', !!carrinhoVazio);
        console.log('  - carrinho-items:', !!carrinhoItems);
        console.log('  - carrinho-header:', !!carrinhoHeader);
        console.log('  - carrinho-footer:', !!carrinhoFooter);
        console.log('  - carrinho-total:', !!carrinhoTotal);
        
        // Mudança: verificar apenas elementos essenciais para evitar loop
        if (carrinhoItems && carrinhoFooter && carrinhoTotal) {
            console.log('✅ Elementos essenciais do sidebar foram encontrados');
            callback();
        } else if (tentativas < maxTentativas) {
            console.log('⏳ Elementos ainda não disponíveis, tentando novamente em 100ms');
            setTimeout(verificarElementos, 100);
        } else {
            console.error('❌ Timeout: elementos do sidebar não foram encontrados após ' + maxTentativas + ' tentativas');
            // Tentar renderizar mesmo assim
            console.log('🔄 Tentando renderizar mesmo sem todos os elementos...');
            callback();
        }
    }
    
    verificarElementos();
}

// Variável para controlar se já está carregando carrinho
var carregandoCarrinho = false;

// Carregar dados do carrinho via AJAX
function carregarDadosCarrinho() {
    if (carregandoCarrinho) {
        console.log('⏸️ Carregamento já em andamento, ignorando nova chamada');
        return;
    }
    
    carregandoCarrinho = true;
    console.log('📥 Iniciando carregamento dos dados do carrinho');
    
    var currentPath = window.location.pathname;
    var slugMatch = currentPath.match(/^\/([^\/]+)\//);
    
    if (!slugMatch) {
        console.log('🔍 Não está em página de restaurante');
        carregandoCarrinho = false;
        return;
    }
    
    var restauranteSlug = slugMatch[1];
    console.log('🍕 Carregando carrinho para:', restauranteSlug);
    
    fetch('/' + restauranteSlug + '/carrinho/', {
        method: 'GET',
        headers: {
            'Accept': 'application/json'
        }
    })
    .then(function(response) {
        console.log('📡 Resposta recebida:', response.status);
        if (response.ok) {
            return response.json();
        } else {
            throw new Error('Erro na resposta: ' + response.status);
        }
    })
    .then(function(data) {
        console.log('📋 Dados do carrinho carregados:', data);
        
        window.carrinhoSidebar.items = data.items || [];
        window.carrinhoSidebar.total = data.total || 0;
        window.carrinhoSidebar.restaurante = data.restaurante || null;
        
        console.log('🔄 Aguardando elementos do sidebar...');
        aguardarElementosSidebar(function() {
            console.log('🎨 Chamando renderizarCarrinhoSidebar...');
            renderizarCarrinhoSidebar();
            console.log('✅ Renderização concluída');
            carregandoCarrinho = false; // Reset da variável
        });
    })
    .catch(function(error) {
        console.error('⚠️ Erro ao carregar carrinho:', error);
        mostrarToast('Erro ao carregar carrinho', 'error');
        carregandoCarrinho = false; // Reset da variável
    });
}

// Renderizar conteúdo do sidebar
function renderizarCarrinhoSidebar() {
    console.log('🎨 Iniciando renderização do sidebar');
    
    var items = window.carrinhoSidebar.items;
    var total = window.carrinhoSidebar.total;
    var restaurante = window.carrinhoSidebar.restaurante;
    
    console.log('📦 Dados para renderizar:', {
        items: items,
        total: total,
        restaurante: restaurante
    });
    
    // Elementos do DOM
    var carrinhoVazio = document.getElementById('carrinho-vazio');
    var carrinhoItems = document.getElementById('carrinho-items');
    var carrinhoHeader = document.getElementById('carrinho-header');
    var carrinhoFooter = document.getElementById('carrinho-footer');
    var carrinhoTotal = document.getElementById('carrinho-total');
    
    console.log('🔍 Elementos encontrados:', {
        carrinhoVazio: !!carrinhoVazio,
        carrinhoItems: !!carrinhoItems,
        carrinhoHeader: !!carrinhoHeader,
        carrinhoFooter: !!carrinhoFooter,
        carrinhoTotal: !!carrinhoTotal
    });
    
    // Verificar se elementos essenciais existem
    if (!carrinhoItems) {
        console.warn('⚠️ Elemento carrinho-items não encontrado, tentando criar estrutura');
        // Procurar o container do offcanvas
        var offcanvasBody = document.querySelector('#carrinho-sidebar .offcanvas-body');
        if (offcanvasBody) {
            console.log('🔧 Offcanvas body encontrado, recriando estrutura');
            offcanvasBody.innerHTML = `
                <div class="p-3 bg-light border-bottom" id="carrinho-header" style="display: none;">
                    <div class="d-flex align-items-center">
                        <i class="bi bi-shop text-primary me-2"></i>
                        <div>
                            <h6 class="mb-0" id="carrinho-restaurante-nome"></h6>
                            <small class="text-muted" id="carrinho-restaurante-endereco"></small>
                        </div>
                    </div>
                </div>
                <div class="flex-grow-1" id="carrinho-items">
                    <div class="p-4 text-center text-muted" id="carrinho-vazio">
                        <i class="bi bi-cart-x fs-1 mb-3 d-block"></i>
                        <h6>Seu carrinho está vazio</h6>
                        <p class="small mb-0">Adicione produtos para continuar</p>
                    </div>
                </div>
                <div class="border-top bg-white p-3" id="carrinho-footer" style="display: none;">
                    <div class="row align-items-center mb-3">
                        <div class="col">
                            <span class="fw-bold">Total:</span>
                        </div>
                        <div class="col-auto">
                            <span class="h5 mb-0 text-primary fw-bold" id="carrinho-total">R$ 0,00</span>
                        </div>
                    </div>
                    <div class="d-grid gap-2">
                        <button class="btn btn-primary" id="btn-finalizar-pedido">
                            <i class="bi bi-credit-card me-2"></i>Finalizar Pedido
                        </button>
                        <button class="btn btn-outline-danger btn-sm" id="btn-limpar-carrinho">
                            <i class="bi bi-trash me-2"></i>Limpar Carrinho
                        </button>
                    </div>
                </div>
            `;
            
            // Reobter os elementos
            carrinhoVazio = document.getElementById('carrinho-vazio');
            carrinhoItems = document.getElementById('carrinho-items');
            carrinhoHeader = document.getElementById('carrinho-header');
            carrinhoFooter = document.getElementById('carrinho-footer');
            carrinhoTotal = document.getElementById('carrinho-total');
            
            console.log('✅ Estrutura recriada com sucesso');
        } else {
            console.error('❌ Não foi possível encontrar ou criar estrutura do carrinho');
            return;
        }
    }
    
    if (items.length === 0) {
        console.log('📭 Carrinho vazio - mostrando estado vazio');
        // Carrinho vazio - mostrar mensagem mas manter botões
        if (carrinhoVazio) carrinhoVazio.style.display = 'block';
        if (carrinhoHeader) carrinhoHeader.style.display = 'none';
        
        // Limpar conteúdo de itens mas manter estrutura
        if (carrinhoItems) {
            carrinhoItems.innerHTML = '<div class="p-4 text-center text-muted" id="carrinho-vazio"><i class="bi bi-cart-x fs-1 mb-3 d-block"></i><h6>Seu carrinho está vazio</h6><p class="small mb-0">Adicione produtos para continuar</p></div>';
        }
        
        // Manter footer mas atualizar total para zero
        if (carrinhoFooter) {
            carrinhoFooter.style.display = 'block';
            if (carrinhoTotal) {
                carrinhoTotal.textContent = 'R$ 0,00';
            }
        }
        
        // Configurar eventos dos botões
        configurarEventosCarrinho();
    } else {
        console.log('📦 Carrinho com', items.length, 'itens - renderizando lista');
        // Carrinho com itens
        if (carrinhoVazio) carrinhoVazio.style.display = 'none';
        
        // Header do restaurante
        if (restaurante && carrinhoHeader) {
            console.log('🏪 Configurando header do restaurante');
            carrinhoHeader.style.display = 'block';
            var nomeEl = document.getElementById('carrinho-restaurante-nome');
            var enderecoEl = document.getElementById('carrinho-restaurante-endereco');
            if (nomeEl) nomeEl.textContent = restaurante.nome;
            if (enderecoEl) enderecoEl.textContent = restaurante.endereco;
        }
        
        // Lista de itens
        console.log('📋 Renderizando lista de itens');
        renderizarItensCarrinho(items);
        
        // Footer com total
        if (carrinhoFooter) {
            console.log('💰 Configurando footer com total:', total);
            carrinhoFooter.style.display = 'block';
            if (carrinhoTotal) {
                carrinhoTotal.textContent = 'R$ ' + formatarPreco(total);
            }
        }
        
        // Configurar eventos dos botões após renderização
        configurarEventosCarrinho();
    }
    
    console.log('✅ Renderização do sidebar concluída');
}

// Configurar eventos dos botões do carrinho
function configurarEventosCarrinho() {
    console.log('🔧 Configurando eventos do carrinho');
    
    // Botão finalizar pedido
    var btnFinalizar = document.getElementById('btn-finalizar-pedido');
    if (btnFinalizar) {
        btnFinalizar.onclick = function() {
            var currentPath = window.location.pathname;
            var slugMatch = currentPath.match(/^\/([^\/]+)\//);
            if (slugMatch) {
                window.location.href = '/' + slugMatch[1] + '/checkout/';
            }
        };
        console.log('✅ Evento do botão finalizar configurado');
    }
    
    // Botão limpar carrinho
    var btnLimpar = document.getElementById('btn-limpar-carrinho');
    if (btnLimpar) {
        btnLimpar.onclick = function() {
            if (confirm('Tem certeza que deseja limpar todo o carrinho?')) {
                limparCarrinho();
            }
        };
        console.log('✅ Evento do botão limpar configurado');
    }
}

// Renderizar lista de itens
function renderizarItensCarrinho(items) {
    var container = document.getElementById('carrinho-items');
    if (!container) return;
    
    console.log('🎨 Renderizando', items.length, 'itens do carrinho');
    
    var html = '';
    
    for (var i = 0; i < items.length; i++) {
        var item = items[i];
        console.log('📦 Renderizando item:', item.nome, 'Qtd:', item.quantidade);
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
    console.log('✅ Renderização de itens concluída');
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
        
        // Atualizar sidebar se estiver aberto E se elementos existem
        var sidebar = document.getElementById('carrinho-sidebar');
        if (window.carrinhoSidebar.isOpen && sidebar && sidebar.classList.contains('show')) {
            window.carrinhoSidebar.items = data.items || [];
            window.carrinhoSidebar.total = data.total || 0;
            window.carrinhoSidebar.restaurante = data.restaurante || null;
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
