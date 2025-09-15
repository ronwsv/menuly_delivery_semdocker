/**
 * Sistema de Busca Avançada - Menuly
 * Funcionalidades: autocomplete, histórico, sugestões
 */

class BuscaAvancada {
    constructor() {
        this.init();
    }

    init() {
        this.setupAutocomplete();
        this.setupHistorico();
        this.setupSugestoes();
    }

    // Autocomplete simples
    setupAutocomplete() {
        const inputs = document.querySelectorAll('input[name="q"]');
        
        inputs.forEach(input => {
            let timeout;
            
            input.addEventListener('input', (e) => {
                clearTimeout(timeout);
                const query = e.target.value.trim();
                
                if (query.length >= 2) {
                    timeout = setTimeout(() => {
                        this.buscarSugestoes(query, input);
                    }, 300);
                } else {
                    this.esconderSugestoes(input);
                }
            });

            // Esconder sugestões ao perder foco
            input.addEventListener('blur', (e) => {
                setTimeout(() => {
                    this.esconderSugestoes(input);
                }, 150);
            });
        });
    }

    // Buscar sugestões do servidor
    async buscarSugestoes(query, input) {
        try {
            const response = await fetch(`/api/buscar-sugestoes/?q=${encodeURIComponent(query)}`);
            
            if (response.ok) {
                const data = await response.json();
                this.mostrarSugestoes(data.sugestoes, input);
            }
        } catch (error) {
            console.log('Erro ao buscar sugestões:', error);
        }
    }

    // Mostrar sugestões
    mostrarSugestoes(sugestoes, input) {
        // Remover sugestões existentes
        this.esconderSugestoes(input);

        if (sugestoes.length === 0) return;

        const container = document.createElement('div');
        container.className = 'busca-sugestoes position-absolute bg-white border rounded shadow-sm';
        container.style.cssText = `
            top: 100%;
            left: 0;
            right: 0;
            z-index: 1000;
            max-height: 300px;
            overflow-y: auto;
        `;

        sugestoes.forEach(sugestao => {
            const item = document.createElement('button');
            item.className = 'btn btn-sm btn-link text-start d-block w-100 py-2 px-3 border-0';
            item.style.color = '#333';
            item.innerHTML = `
                <i class="bi bi-search me-2"></i>
                ${this.highlightQuery(sugestao, input.value)}
            `;

            item.addEventListener('click', (e) => {
                e.preventDefault();
                input.value = sugestao;
                input.form.submit();
            });

            container.appendChild(item);
        });

        // Posicionar relativo ao input
        const inputGroup = input.closest('.input-group') || input.parentElement;
        inputGroup.style.position = 'relative';
        inputGroup.appendChild(container);
    }

    // Esconder sugestões
    esconderSugestoes(input) {
        const container = input.parentElement.querySelector('.busca-sugestoes');
        if (container) {
            container.remove();
        }
    }

    // Destacar termo da busca nas sugestões
    highlightQuery(text, query) {
        if (!query) return text;
        
        const regex = new RegExp(`(${query})`, 'gi');
        return text.replace(regex, '<strong>$1</strong>');
    }

    // Sistema de histórico de busca
    setupHistorico() {
        const forms = document.querySelectorAll('form[action*="buscar"]');
        
        forms.forEach(form => {
            form.addEventListener('submit', (e) => {
                const query = form.querySelector('input[name="q"]').value.trim();
                if (query) {
                    this.salvarNoHistorico(query);
                }
            });
        });

        this.carregarHistorico();
    }

    // Salvar busca no histórico
    salvarNoHistorico(query) {
        let historico = JSON.parse(localStorage.getItem('busca_historico') || '[]');
        
        // Remover se já existe
        historico = historico.filter(item => item !== query);
        
        // Adicionar no início
        historico.unshift(query);
        
        // Manter apenas 10 itens
        historico = historico.slice(0, 10);
        
        localStorage.setItem('busca_historico', JSON.stringify(historico));
    }

    // Carregar histórico de busca
    carregarHistorico() {
        const historico = JSON.parse(localStorage.getItem('busca_historico') || '[]');
        
        if (historico.length > 0) {
            // Adicionar histórico em inputs quando focados
            const inputs = document.querySelectorAll('input[name="q"]');
            
            inputs.forEach(input => {
                input.addEventListener('focus', () => {
                    if (!input.value) {
                        this.mostrarHistorico(historico, input);
                    }
                });
            });
        }
    }

    // Mostrar histórico
    mostrarHistorico(historico, input) {
        this.esconderSugestoes(input);

        const container = document.createElement('div');
        container.className = 'busca-sugestoes position-absolute bg-white border rounded shadow-sm';
        container.style.cssText = `
            top: 100%;
            left: 0;
            right: 0;
            z-index: 1000;
            max-height: 300px;
            overflow-y: auto;
        `;

        // Título do histórico
        const titulo = document.createElement('div');
        titulo.className = 'px-3 py-2 border-bottom bg-light';
        titulo.innerHTML = '<small class="text-muted"><i class="bi bi-clock-history me-1"></i>Buscas recentes</small>';
        container.appendChild(titulo);

        historico.forEach(item => {
            const botao = document.createElement('button');
            botao.className = 'btn btn-sm btn-link text-start d-block w-100 py-2 px-3 border-0';
            botao.style.color = '#333';
            botao.innerHTML = `<i class="bi bi-clock-history me-2"></i>${item}`;

            botao.addEventListener('click', (e) => {
                e.preventDefault();
                input.value = item;
                input.form.submit();
            });

            container.appendChild(botao);
        });

        // Opção para limpar histórico
        const limpar = document.createElement('button');
        limpar.className = 'btn btn-sm btn-link text-danger d-block w-100 py-2 px-3 border-0 border-top';
        limpar.innerHTML = '<i class="bi bi-trash me-2"></i>Limpar histórico';
        limpar.addEventListener('click', (e) => {
            e.preventDefault();
            localStorage.removeItem('busca_historico');
            this.esconderSugestoes(input);
        });
        container.appendChild(limpar);

        const inputGroup = input.closest('.input-group') || input.parentElement;
        inputGroup.style.position = 'relative';
        inputGroup.appendChild(container);
    }

    // Configurar sugestões rápidas
    setupSugestoes() {
        // Adicionar atalhos de teclado
        document.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + K para focar na busca
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                const input = document.querySelector('input[name="q"]');
                if (input) {
                    input.focus();
                    input.select();
                }
            }
        });
    }
}

// Inicializar quando o DOM estiver pronto
document.addEventListener('DOMContentLoaded', () => {
    new BuscaAvancada();
});

// Adicionar indicador de atalho de teclado
document.addEventListener('DOMContentLoaded', () => {
    const inputs = document.querySelectorAll('input[name="q"]');
    inputs.forEach(input => {
        if (!input.placeholder.includes('Ctrl+K')) {
            input.placeholder += ' (Ctrl+K)';
        }
    });
});
