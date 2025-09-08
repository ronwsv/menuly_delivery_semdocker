/**
 * JavaScript para a Loja - Sistema Menuly
 * Funcionalidades modernas e responsivas para a experiência do cliente
 */

// ====================== CONFIGURAÇÕES GLOBAIS ======================
const MENULY = {
    config: {
        carrinho: {
            key: 'menuly_carrinho',
            maxItens: 99
        },
        api: {
            timeout: 10000,
            retries: 3
        },
        animations: {
            duration: 300
        }
    },
    
    // URLs para APIs (serão definidas dinamicamente)
    urls: {
        adicionarCarrinho: '/api/carrinho/adicionar/',
        produto: '/api/produto/',
        buscarCEP: '/api/buscar-cep/',
        calcularEntrega: '/api/calcular-entrega/'
    }
};

// ====================== UTILITÁRIOS ======================
const Utils = {
    // Formatar moeda brasileira
    formatMoney(value) {
        return new Intl.NumberFormat('pt-BR', {
            style: 'currency',
            currency: 'BRL'
        }).format(value);
    },
    
    // Debounce para otimizar performance
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },
    
    // Mostrar toast/notificação
    showToast(message, type = 'success') {
        const toastContainer = document.getElementById('toast-container') || this.createToastContainer();
        
        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-white bg-${type} border-0`;
        toast.setAttribute('role', 'alert');
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    <i class="bi bi-${type === 'success' ? 'check-circle' : 'exclamation-triangle'}"></i>
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;
        
        toastContainer.appendChild(toast);
        
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();
        
        // Remover após 5 segundos
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 5000);
    },
    
    // Criar container de toasts se não existir
    createToastContainer() {
        const container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container position-fixed top-0 end-0 p-3';
        container.style.zIndex = '1060';
        document.body.appendChild(container);
        return container;
    },
    
    // Validar CPF
    validateCPF(cpf) {
        cpf = cpf.replace(/[^\d]+/g, '');
        if (cpf.length !== 11 || /^(\d)\1{10}$/.test(cpf)) return false;
        
        let sum = 0;
        for (let i = 0; i < 9; i++) {
            sum += parseInt(cpf.charAt(i)) * (10 - i);
        }
        let remainder = 11 - (sum % 11);
        if (remainder === 10 || remainder === 11) remainder = 0;
        if (remainder !== parseInt(cpf.charAt(9))) return false;
        
        sum = 0;
        for (let i = 0; i < 10; i++) {
            sum += parseInt(cpf.charAt(i)) * (11 - i);
        }
        remainder = 11 - (sum % 11);
        if (remainder === 10 || remainder === 11) remainder = 0;
        return remainder === parseInt(cpf.charAt(10));
    },
    
    // Validar email
    validateEmail(email) {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(email);
    },
    
    // Validar telefone brasileiro
    validatePhone(phone) {
        const re = /^(?:\+55\s?)?(?:\(?0?[1-9]{2}\)?\s?)?(?:9\s?)?[0-9]{4}-?[0-9]{4}$/;
        return re.test(phone);
    }
};

// ====================== GERENCIAMENTO DO CARRINHO ======================
const Carrinho = {
    itens: new Map(),
    eventsBound: false, // Flag para evitar múltiplos event listeners
    
    init() {
        this.loadFromStorage();
        this.updateUI();
        if (!this.eventsBound) {
            this.bindEvents();
            this.eventsBound = true;
        }
    },
    
    // Carregar carrinho do localStorage
    loadFromStorage() {
        try {
            const saved = localStorage.getItem(MENULY.config.carrinho.key);
            if (saved) {
                const data = JSON.parse(saved);
                this.itens = new Map(Object.entries(data));
            }
        } catch (error) {
            console.error('Erro ao carregar carrinho:', error);
            this.itens = new Map();
        }
    },
    
    // Salvar carrinho no localStorage
    saveToStorage() {
        try {
            const data = Object.fromEntries(this.itens);
            localStorage.setItem(MENULY.config.carrinho.key, JSON.stringify(data));
        } catch (error) {
            console.error('Erro ao salvar carrinho:', error);
        }
    },
    
    // Adicionar item ao carrinho
    async adicionar(produtoId, quantidade = 1, personalizacoes = [], observacoes = '') {
        try {
            const response = await fetch(MENULY.urls.adicionarCarrinho, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    produto_id: produtoId,
                    quantidade: quantidade,
                    personalizacoes: personalizacoes,
                    observacoes: observacoes
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.loadFromStorage(); // Recarregar do servidor
                this.updateUI();
                Utils.showToast(data.message || 'Produto adicionado ao carrinho!', 'success');
                return true;
            } else {
                throw new Error(data.message || 'Erro ao adicionar produto');
            }
        } catch (error) {
            console.error('Erro ao adicionar ao carrinho:', error);
            Utils.showToast('Erro ao adicionar produto ao carrinho', 'danger');
            return false;
        }
    },
    
    // Remover item do carrinho
    remover(itemId) {
        if (this.itens.has(itemId)) {
            this.itens.delete(itemId);
            this.saveToStorage();
            this.updateUI();
            Utils.showToast('Item removido do carrinho', 'success');
        }
    },
    
    // Atualizar quantidade de um item
    atualizarQuantidade(itemId, novaQuantidade) {
        if (this.itens.has(itemId)) {
            if (novaQuantidade <= 0) {
                this.remover(itemId);
            } else if (novaQuantidade <= MENULY.config.carrinho.maxItens) {
                const item = this.itens.get(itemId);
                item.quantidade = novaQuantidade;
                this.itens.set(itemId, item);
                this.saveToStorage();
                this.updateUI();
            }
        }
    },
    
    // Limpar carrinho
    limpar() {
        this.itens.clear();
        this.saveToStorage();
        this.updateUI();
        Utils.showToast('Carrinho limpo', 'success');
    },
    
    // Calcular total do carrinho
    calcularTotal() {
        let total = 0;
        this.itens.forEach(item => {
            total += item.preco * item.quantidade;
        });
        return total;
    },
    
    // Obter quantidade total de itens
    getTotalItens() {
        let total = 0;
        this.itens.forEach(item => {
            total += item.quantidade;
        });
        return total;
    },
    
    // Atualizar interface do usuário
    updateUI() {
        const totalItens = this.getTotalItens();
        const badgeCarrinho = document.getElementById('carrinho-badge');
        
        if (badgeCarrinho) {
            badgeCarrinho.textContent = totalItens;
            badgeCarrinho.style.display = totalItens > 0 ? 'inline' : 'none';
        }
        
        // Atualizar contador no menu mobile se existir
        const contadorMobile = document.getElementById('carrinho-mobile-count');
        if (contadorMobile) {
            contadorMobile.textContent = totalItens;
        }
        
        // Atualizar página do carrinho se estivermos nela
        if (window.location.pathname.includes('/carrinho/')) {
            this.updateCarrinhoPage();
        }
    },
    
    // Atualizar página específica do carrinho
    updateCarrinhoPage() {
        const carrinhoContainer = document.getElementById('carrinho-itens');
        const carrinhoTotal = document.getElementById('carrinho-total');
        
        if (!carrinhoContainer) return;
        
        if (this.itens.size === 0) {
            carrinhoContainer.innerHTML = `
                <div class="text-center py-5">
                    <i class="bi bi-cart-x fs-1 text-muted mb-3"></i>
                    <h5>Seu carrinho está vazio</h5>
                    <p class="text-muted">Adicione alguns produtos deliciosos!</p>
                    <a href="/cardapio/" class="btn btn-primary">
                        <i class="bi bi-menu-button-wide"></i> Ver Cardápio
                    </a>
                </div>
            `;
            if (carrinhoTotal) carrinhoTotal.textContent = Utils.formatMoney(0);
            return;
        }
        
        let html = '';
        this.itens.forEach((item, itemId) => {
            html += this.renderCarrinhoItem(itemId, item);
        });
        
        carrinhoContainer.innerHTML = html;
        
        if (carrinhoTotal) {
            carrinhoTotal.textContent = Utils.formatMoney(this.calcularTotal());
        }
    },
    
    // Renderizar item do carrinho
    renderCarrinhoItem(itemId, item) {
        return `
            <div class="carrinho-item" data-item-id="${itemId}">
                <div class="row align-items-center">
                    <div class="col-md-6">
                        <h6>${item.nome}</h6>
                        ${item.personalizacoes ? `<small class="text-muted">${item.personalizacoes}</small>` : ''}
                        ${item.observacoes ? `<small class="text-muted d-block">Obs: ${item.observacoes}</small>` : ''}
                    </div>
                    <div class="col-md-2">
                        <span class="fw-bold">${Utils.formatMoney(item.preco)}</span>
                    </div>
                    <div class="col-md-2">
                        <div class="input-group input-group-sm">
                            <button class="btn btn-outline-secondary btn-diminuir" type="button">
                                <i class="bi bi-dash"></i>
                            </button>
                            <input type="number" class="form-control text-center quantidade-input" 
                                   value="${item.quantidade}" min="1" max="${MENULY.config.carrinho.maxItens}">
                            <button class="btn btn-outline-secondary btn-aumentar" type="button">
                                <i class="bi bi-plus"></i>
                            </button>
                        </div>
                    </div>
                    <div class="col-md-1">
                        <span class="fw-bold">${Utils.formatMoney(item.preco * item.quantidade)}</span>
                    </div>
                    <div class="col-md-1">
                        <button class="btn btn-outline-danger btn-sm btn-remover" type="button">
                            <i class="bi bi-trash"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;
    },
    
    // Vincular eventos
    bindEvents() {
        // Botões "Adicionar ao Carrinho"
        document.addEventListener('click', (e) => {
            if (e.target.matches('.btn-adicionar-carrinho') || e.target.closest('.btn-adicionar-carrinho')) {
                e.preventDefault();
                const btn = e.target.closest('.btn-adicionar-carrinho');
                const produtoId = btn.dataset.produtoId;
                
                if (produtoId) {
                    this.handleAdicionarClick(btn, produtoId);
                }
            }
        });
        
        // Eventos da página do carrinho
        document.addEventListener('click', (e) => {
            const carrinhoItem = e.target.closest('.carrinho-item');
            if (!carrinhoItem) return;
            
            const itemId = carrinhoItem.dataset.itemId;
            
            if (e.target.matches('.btn-remover') || e.target.closest('.btn-remover')) {
                this.remover(itemId);
            } else if (e.target.matches('.btn-aumentar') || e.target.closest('.btn-aumentar')) {
                const input = carrinhoItem.querySelector('.quantidade-input');
                const novaQuantidade = parseInt(input.value) + 1;
                if (novaQuantidade <= MENULY.config.carrinho.maxItens) {
                    this.atualizarQuantidade(itemId, novaQuantidade);
                }
            } else if (e.target.matches('.btn-diminuir') || e.target.closest('.btn-diminuir')) {
                const input = carrinhoItem.querySelector('.quantidade-input');
                const novaQuantidade = parseInt(input.value) - 1;
                this.atualizarQuantidade(itemId, novaQuantidade);
            }
        });
        
        // Input de quantidade
        document.addEventListener('change', (e) => {
            if (e.target.matches('.quantidade-input')) {
                const carrinhoItem = e.target.closest('.carrinho-item');
                const itemId = carrinhoItem.dataset.itemId;
                const novaQuantidade = parseInt(e.target.value);
                
                this.atualizarQuantidade(itemId, novaQuantidade);
            }
        });
    },
    
    // Manipular clique no botão adicionar
    async handleAdicionarClick(btn, produtoId) {
        // Verificar se o botão já está processando
        if (btn.disabled || btn.classList.contains('processing')) {
            console.log('🚫 Produto já está sendo processado:', produtoId);
            return;
        }
        
        // Verificar se o produto tem opções de personalização
        const temOpcoes = btn.dataset.temOpcoes === 'true';
        const produtoSlug = btn.dataset.produtoSlug;
        
        if (temOpcoes) {
            // Produto complexo: redirecionar para página de detalhes
            console.log('🔧 Produto com opções, redirecionando para detalhes:', produtoId);
            
            // Construir URL correta com base na URL atual
            const currentPath = window.location.pathname;
            const slugMatch = currentPath.match(/^\/([^\/]+)\//);
            const restauranteSlug = slugMatch ? slugMatch[1] : '';
            const detailUrl = `/${restauranteSlug}/produto/${produtoSlug}/`;
            
            console.log('🔗 Redirecionando para:', detailUrl);
            window.location.href = detailUrl;
            return;
        }
        
        // Produto simples: adicionar direto ao carrinho
        console.log('🛒 Produto simples, adicionando direto ao carrinho:', produtoId);
        
        const originalText = btn.innerHTML;
        
        // Marcar como processando e desabilitar botão
        btn.disabled = true;
        btn.classList.add('processing');
        btn.innerHTML = '<i class="bi bi-arrow-repeat"></i> Adicionando...';
        
        try {
            const sucesso = await this.adicionar(produtoId);
            
            if (sucesso) {
                btn.innerHTML = '<i class="bi bi-check"></i> Adicionado!';
                btn.classList.remove('btn-primary');
                btn.classList.add('btn-success');
                
                setTimeout(() => {
                    btn.innerHTML = originalText;
                    btn.classList.remove('btn-success', 'processing');
                    btn.classList.add('btn-primary');
                    btn.disabled = false;
                }, 2000);
            } else {
                throw new Error('Falha ao adicionar');
            }
        } catch (error) {
            btn.innerHTML = '<i class="bi bi-exclamation-triangle"></i> Erro';
            btn.classList.remove('btn-primary');
            btn.classList.add('btn-danger');
            
            setTimeout(() => {
                btn.innerHTML = originalText;
                btn.classList.remove('btn-danger', 'processing');
                btn.classList.add('btn-primary');
                btn.disabled = false;
            }, 2000);
        }
    },
    
    // Obter CSRF Token
    getCSRFToken() {
        const csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
        return csrfInput ? csrfInput.value : '';
    }
};

// ====================== BUSCA DE CEP ======================
const BuscarCEP = {
    init() {
        this.bindEvents();
    },
    
    bindEvents() {
        const cepInputs = document.querySelectorAll('input[name="cep"], #id_cep');
        
        cepInputs.forEach(input => {
            input.addEventListener('blur', (e) => {
                this.buscar(e.target);
            });
            
            input.addEventListener('input', (e) => {
                this.formatCEP(e.target);
            });
        });
    },
    
    formatCEP(input) {
        let value = input.value.replace(/\D/g, '');
        if (value.length >= 5) {
            value = value.replace(/^(\d{5})(\d)/, '$1-$2');
        }
        input.value = value;
    },
    
    async buscar(input) {
        const cep = input.value.replace(/\D/g, '');
        
        if (cep.length !== 8) return;
        
        const loadingIndicator = this.showLoading(input);
        
        try {
            const response = await fetch(`${MENULY.urls.buscarCEP}?cep=${cep}`);
            const data = await response.json();
            
            if (response.ok && !data.error) {
                this.preencherEndereco(data);
                Utils.showToast('CEP encontrado!', 'success');
            } else {
                throw new Error(data.error || 'CEP não encontrado');
            }
        } catch (error) {
            console.error('Erro ao buscar CEP:', error);
            Utils.showToast('Erro ao buscar CEP. Verifique o número informado.', 'warning');
        } finally {
            this.hideLoading(loadingIndicator);
        }
    },
    
    preencherEndereco(dados) {
        const campos = {
            logradouro: ['logradouro', 'endereco', 'rua'],
            bairro: ['bairro'],
            cidade: ['cidade', 'localidade'],
            estado: ['estado', 'uf']
        };
        
        Object.keys(campos).forEach(campo => {
            const valor = dados[campo];
            if (valor) {
                campos[campo].forEach(nome => {
                    const input = document.querySelector(`input[name="${nome}"], #id_${nome}`);
                    if (input) {
                        input.value = valor;
                        input.dispatchEvent(new Event('change'));
                    }
                });
            }
        });
        
        // Focar no número se o logradouro foi preenchido
        const numeroInput = document.querySelector('input[name="numero"], #id_numero');
        if (numeroInput && dados.logradouro) {
            numeroInput.focus();
        }
    },
    
    showLoading(input) {
        const indicator = document.createElement('div');
        indicator.className = 'position-absolute';
        indicator.style.cssText = 'right: 10px; top: 50%; transform: translateY(-50%); z-index: 10;';
        indicator.innerHTML = '<i class="bi bi-arrow-repeat"></i>';
        
        input.parentNode.style.position = 'relative';
        input.parentNode.appendChild(indicator);
        
        return indicator;
    },
    
    hideLoading(indicator) {
        if (indicator && indicator.parentNode) {
            indicator.parentNode.removeChild(indicator);
        }
    }
};

// ====================== BUSCA DE PRODUTOS ======================
const BuscaProdutos = {
    init() {
        this.bindEvents();
    },
    
    bindEvents() {
        const searchInput = document.querySelector('input[name="q"]');
        if (!searchInput) return;
        
        const debouncedSearch = Utils.debounce((query) => {
            if (query.length >= 2) {
                this.buscar(query);
            }
        }, 500);
        
        searchInput.addEventListener('input', (e) => {
            debouncedSearch(e.target.value);
        });
    },
    
    async buscar(query) {
        // Implementar busca em tempo real se necessário
        console.log('Buscando:', query);
    }
};

// ====================== CHECKOUT ======================
const Checkout = {
    init() {
        this.bindEvents();
        this.loadSavedData();
    },
    
    bindEvents() {
        // Selecionar tipo de entrega
        const tipoEntregaInputs = document.querySelectorAll('input[name="tipo_entrega"]');
        tipoEntregaInputs.forEach(input => {
            input.addEventListener('change', () => {
                this.handleTipoEntregaChange();
            });
        });
        
        // Selecionar forma de pagamento
        const formaPagamentoInputs = document.querySelectorAll('input[name="forma_pagamento"]');
        formaPagamentoInputs.forEach(input => {
            input.addEventListener('change', () => {
                this.handleFormaPagamentoChange();
            });
        });
        
        // Validação em tempo real
        const form = document.getElementById('checkout-form');
        if (form) {
            form.addEventListener('submit', (e) => {
                if (!this.validateForm(form)) {
                    e.preventDefault();
                }
            });
        }
    },
    
    handleTipoEntregaChange() {
        const tipoSelecionado = document.querySelector('input[name="tipo_entrega"]:checked');
        const enderecoSection = document.getElementById('endereco-section');
        
        if (tipoSelecionado && enderecoSection) {
            if (tipoSelecionado.value === 'delivery') {
                enderecoSection.style.display = 'block';
                this.calcularTaxaEntrega();
            } else {
                enderecoSection.style.display = 'none';
                this.updateTaxaEntrega(0);
            }
        }
    },
    
    handleFormaPagamentoChange() {
        const formaSelecionada = document.querySelector('input[name="forma_pagamento"]:checked');
        const trocoSection = document.getElementById('troco-section');
        
        if (formaSelecionada && trocoSection) {
            if (formaSelecionada.value === 'dinheiro') {
                trocoSection.style.display = 'block';
            } else {
                trocoSection.style.display = 'none';
            }
        }
    },
    
    async calcularTaxaEntrega() {
        const cepInput = document.querySelector('input[name="cep"]');
        if (!cepInput || !cepInput.value) return;
        
        try {
            const response = await fetch(MENULY.urls.calcularEntrega, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': Carrinho.getCSRFToken()
                },
                body: JSON.stringify({
                    cep: cepInput.value.replace(/\D/g, '')
                })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                this.updateTaxaEntrega(data.taxa_entrega);
                this.updateTempoEntrega(data.tempo_estimado);
            }
        } catch (error) {
            console.error('Erro ao calcular entrega:', error);
        }
    },
    
    updateTaxaEntrega(taxa) {
        const taxaDisplay = document.getElementById('taxa-entrega-valor');
        const taxaInput = document.getElementById('taxa-entrega-input');
        
        if (taxaDisplay) {
            taxaDisplay.textContent = Utils.formatMoney(taxa);
        }
        
        if (taxaInput) {
            taxaInput.value = taxa;
        }
        
        this.updateTotal();
    },
    
    updateTempoEntrega(tempo) {
        const tempoDisplay = document.getElementById('tempo-entrega');
        if (tempoDisplay) {
            tempoDisplay.textContent = tempo;
        }
    },
    
    updateTotal() {
        const subtotal = parseFloat(document.getElementById('subtotal')?.textContent?.replace(/[^\d,]/g, '').replace(',', '.') || 0);
        const taxa = parseFloat(document.getElementById('taxa-entrega-input')?.value || 0);
        const desconto = parseFloat(document.getElementById('desconto-input')?.value || 0);
        
        const total = subtotal + taxa - desconto;
        
        const totalDisplay = document.getElementById('total-pedido');
        if (totalDisplay) {
            totalDisplay.textContent = Utils.formatMoney(total);
        }
    },
    
    validateForm(form) {
        let isValid = true;
        const errors = [];
        
        // Validar campos obrigatórios
        const requiredFields = form.querySelectorAll('input[required], select[required], textarea[required]');
        requiredFields.forEach(field => {
            if (!field.value.trim()) {
                isValid = false;
                errors.push(`${field.labels[0]?.textContent || field.name} é obrigatório`);
                field.classList.add('is-invalid');
            } else {
                field.classList.remove('is-invalid');
            }
        });
        
        // Validar email
        const emailField = form.querySelector('input[type="email"]');
        if (emailField && emailField.value && !Utils.validateEmail(emailField.value)) {
            isValid = false;
            errors.push('Email inválido');
            emailField.classList.add('is-invalid');
        }
        
        // Validar telefone
        const phoneField = form.querySelector('input[name="celular"]');
        if (phoneField && phoneField.value && !Utils.validatePhone(phoneField.value)) {
            isValid = false;
            errors.push('Telefone inválido');
            phoneField.classList.add('is-invalid');
        }
        
        if (!isValid) {
            Utils.showToast(errors[0], 'danger');
        }
        
        return isValid;
    },
    
    loadSavedData() {
        // Carregar dados salvos do localStorage se existirem
        try {
            const savedData = localStorage.getItem('menuly_checkout_data');
            if (savedData) {
                const data = JSON.parse(savedData);
                Object.keys(data).forEach(key => {
                    const input = document.querySelector(`[name="${key}"]`);
                    if (input && input.type !== 'password') {
                        input.value = data[key];
                    }
                });
            }
        } catch (error) {
            console.error('Erro ao carregar dados salvos:', error);
        }
    }
};

// ====================== PRODUTO DETALHES ======================
const ProdutoDetalhes = {
    personalizacoes: new Map(),
    precoBase: 0,
    
    init() {
        this.bindEvents();
        this.calcularPreco();
    },
    
    bindEvents() {
        // Opções de personalização
        document.addEventListener('change', (e) => {
            if (e.target.matches('input[name^="opcao_"], select[name^="opcao_"]')) {
                this.handlePersonalizacaoChange(e.target);
            }
        });
        
        // Quantidade
        const quantidadeInput = document.getElementById('quantidade');
        if (quantidadeInput) {
            quantidadeInput.addEventListener('change', () => {
                this.calcularPreco();
            });
        }
        
        // Botões de quantidade
        document.addEventListener('click', (e) => {
            if (e.target.matches('.btn-quantidade-menos')) {
                this.alterarQuantidade(-1);
            } else if (e.target.matches('.btn-quantidade-mais')) {
                this.alterarQuantidade(1);
            }
        });
        
        // Galeria de imagens
        this.initGaleria();
    },
    
    handlePersonalizacaoChange(input) {
        const opcaoId = input.dataset.opcaoId;
        const itemId = input.value;
        const preco = parseFloat(input.dataset.preco || 0);
        
        if (input.type === 'radio') {
            this.personalizacoes.set(opcaoId, {
                itemId: itemId,
                nome: input.dataset.nome,
                preco: preco
            });
        } else if (input.type === 'checkbox') {
            const opcaoMap = this.personalizacoes.get(opcaoId) || new Map();
            
            if (input.checked) {
                opcaoMap.set(itemId, {
                    nome: input.dataset.nome,
                    preco: preco
                });
            } else {
                opcaoMap.delete(itemId);
            }
            
            this.personalizacoes.set(opcaoId, opcaoMap);
        }
        
        this.calcularPreco();
    },
    
    calcularPreco() {
        let precoTotal = this.precoBase;
        
        // Somar personalizações
        this.personalizacoes.forEach(opcao => {
            if (opcao instanceof Map) {
                opcao.forEach(item => {
                    precoTotal += item.preco;
                });
            } else {
                precoTotal += opcao.preco;
            }
        });
        
        // Multiplicar pela quantidade
        const quantidade = parseInt(document.getElementById('quantidade')?.value || 1);
        const precoFinal = precoTotal * quantidade;
        
        // Atualizar display
        const precoDisplay = document.getElementById('preco-final');
        if (precoDisplay) {
            precoDisplay.textContent = Utils.formatMoney(precoFinal);
        }
    },
    
    alterarQuantidade(delta) {
        const input = document.getElementById('quantidade');
        if (!input) return;
        
        const atual = parseInt(input.value);
        const novo = Math.max(1, Math.min(atual + delta, MENULY.config.carrinho.maxItens));
        
        input.value = novo;
        this.calcularPreco();
    },
    
    initGaleria() {
        // Implementar galeria de imagens se necessário
        const thumbs = document.querySelectorAll('.produto-thumb');
        const mainImage = document.getElementById('produto-main-image');
        
        thumbs.forEach(thumb => {
            thumb.addEventListener('click', (e) => {
                e.preventDefault();
                if (mainImage) {
                    mainImage.src = thumb.href;
                    
                    // Atualizar classe ativa
                    thumbs.forEach(t => t.classList.remove('active'));
                    thumb.classList.add('active');
                }
            });
        });
    }
};

// ====================== INICIALIZAÇÃO ======================
document.addEventListener('DOMContentLoaded', function() {
    // Inicializar módulos
    Carrinho.init();
    BuscarCEP.init();
    BuscaProdutos.init();
    
    // Inicializar módulos específicos da página
    if (document.getElementById('checkout-form')) {
        Checkout.init();
    }
    
    if (document.querySelector('.produto-detalhes')) {
        ProdutoDetalhes.init();
    }
    
    // Smooth scroll para links internos
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
    
    // Lazy loading para imagens
    if ('IntersectionObserver' in window) {
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src;
                    img.classList.remove('lazy');
                    imageObserver.unobserve(img);
                }
            });
        });
        
        document.querySelectorAll('img[data-src]').forEach(img => {
            imageObserver.observe(img);
        });
    }
    
    // Tooltip Bootstrap
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Popover Bootstrap
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
});

// ====================== EXPOSIÇÃO GLOBAL ======================
window.MENULY = MENULY;
window.Utils = Utils;
window.Carrinho = Carrinho;
