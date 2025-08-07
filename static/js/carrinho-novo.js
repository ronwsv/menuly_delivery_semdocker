/**
 * Sistema de Carrinho Menuly - Integrado com Django
 * Versão: 2.0
 */

// Inicializar sistema quando DOM carregar
document.addEventListener('DOMContentLoaded', function() {
    console.log('🛒 Sistema de carrinho carregado');
    
    // Carregar contador inicial
    atualizarContadorCarrinho();
});

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
