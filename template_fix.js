console.log('🔧 Produto template inicializado');

// DADOS DO PRODUTO
const PRODUTO = {
    id: parseInt('{{ produto.id|default:"0" }}') || 0,
    nome: '{{ produto.nome|escapejs|default:"" }}',
    preco_base: parseFloat('{{ produto.preco_final|default:"0.00" }}') || 0,
    categoria: '{{ produto.categoria.nome|default:""|escapejs }}',
    imagem: '{% if produto.imagem_principal %}{{ produto.imagem_principal.url }}{% else %}{% endif %}'
};

console.log('📦 Produto carregado:', PRODUTO);

// FUNÇÃO: ATUALIZAR PREÇO
function atualizarPreco() {
    console.log('💰 Calculando preço...');
    
    try {
        const quantidadeInput = document.getElementById('quantidade');
        const quantidade = quantidadeInput ? parseInt(quantidadeInput.value) || 1 : 1;
        let precoAdicional = 0;
        
        const inputsSelecionados = document.querySelectorAll('#produto-form input:checked, #produto-form select');
        
        inputsSelecionados.forEach(input => {
            let preco = 0;
            
            if (input.type === 'checkbox' || input.type === 'radio') {
                preco = parseFloat(input.dataset.preco || 0);
            } else if (input.tagName === 'SELECT') {
                const option = input.options[input.selectedIndex];
                preco = option ? parseFloat(option.dataset.preco || 0) : 0;
            }
            
            if (preco > 0) {
                precoAdicional += preco;
            }
        });
        
        const precoTotal = (PRODUTO.preco_base + precoAdicional) * quantidade;
        const elementoPreco = document.getElementById('preco-total');
        
        if (elementoPreco) {
            elementoPreco.textContent = `R$ ${precoTotal.toFixed(2).replace('.', ',')}`;
            console.log('✅ Preço: R$', precoTotal.toFixed(2));
        }
        
    } catch (error) {
        console.error('❌ Erro no cálculo:', error);
    }
}

// FUNÇÃO: ALTERAR QUANTIDADE
function alterarQuantidadeProduto(delta) {
    const input = document.getElementById('quantidade');
    if (!input) return;
    
    const atual = parseInt(input.value) || 1;
    const nova = atual + delta;
    
    if (nova >= 1 && nova <= 99) {
        input.value = nova;
        atualizarPreco();
    }
}

// FUNÇÃO: VALIDAR OPÇÕES
function validarQuantidade(opcaoId) {
    const card = document.querySelector(`[data-opcao-id="${opcaoId}"]`);
    if (!card) return;
    
    const tipo = card.getAttribute('data-tipo');
    const max = parseInt(card.getAttribute('data-max')) || 0;
    
    if (tipo === 'checkbox' && max > 0) {
        const selecionados = document.querySelectorAll(`[name="opcao_${opcaoId}[]"]:checked`);
        const quantidade = selecionados.length;
        
        card.classList.remove('border-danger', 'border-warning', 'border-success', 'border-info');
        
        if (quantidade >= max) {
            document.querySelectorAll(`[name="opcao_${opcaoId}[]"]:not(:checked)`).forEach(cb => {
                cb.disabled = true;
                const label = cb.closest('.form-check');
                if (label) label.classList.add('text-muted', 'opacity-50');
            });
            card.classList.add('border-success');
        } else {
            document.querySelectorAll(`[name="opcao_${opcaoId}[]"]`).forEach(cb => {
                cb.disabled = false;
                const label = cb.closest('.form-check');
                if (label) label.classList.remove('text-muted', 'opacity-50');
            });
            
            if (quantidade > 0) card.classList.add('border-info');
        }
    }
    
    atualizarPreco();
}

// Tornar funções globais
window.atualizarPreco = atualizarPreco;
window.alterarQuantidadeProduto = alterarQuantidadeProduto;
window.validarQuantidade = validarQuantidade;

// INICIALIZAÇÃO
document.addEventListener('DOMContentLoaded', function() {
    console.log('🏁 DOM pronto');
    console.log('🧪 Funções:', typeof atualizarPreco, typeof alterarQuantidadeProduto, typeof validarQuantidade);
    atualizarPreco();
    console.log('✅ Sistema inicializado');
});
