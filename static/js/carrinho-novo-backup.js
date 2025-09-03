/**
 * Sistema de Carrinho Menuly - Versão Limpa
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
    
    // Enviar para o backend
    fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify(item)
    })
    .then(function(response) {
        console.log('📡 Resposta recebida:', response.status, response.statusText);
        if (!response.ok) {
            throw new Error('HTTP error! status: ' + response.status);
        }
        return response.json();
    })
    .then(function(data) {
        console.log('📦 Dados da resposta:', data);
        if (data.success) {
            // Atualizar contador do carrinho
            atualizarContadorCarrinho();
            
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
    // Implementação básica - pode ser expandida conforme necessário
    console.log('🔧 Sidebar do carrinho inicializado');
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
