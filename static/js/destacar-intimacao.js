/**
 * Sistema de destaque de intimações
 * Componente reutilizável para destacar/remover destaque de intimações
 */

console.log('DEBUG: Script destacar-intimacao.js carregado!');

// Função principal para alternar destaque
function toggleDestacarIntimacao(button) {
    const intimacaoId = button.dataset.intimacaoId;
    const destacada = button.dataset.destacada === 'true' || button.dataset.destacada === '1';
    const novaDestacada = !destacada;
    
    // Mostrar loading
    const originalContent = button.innerHTML;
    button.innerHTML = '<i class="bi bi-hourglass-split"></i> Processando...';
    button.disabled = true;
    
    // Fazer requisição para API
    fetch(`/api/intimacoes/${intimacaoId}/destacar`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            destacada: novaDestacada
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Atualizar botão
            updateDestacarButton(button, novaDestacada);
            
            // Atualizar linha da tabela se existir
            updateTableRow(intimacaoId, novaDestacada);
            
            // Mostrar notificação
            showNotification(
                novaDestacada ? 'Intimação destacada!' : 'Destaque removido!',
                novaDestacada ? 'success' : 'info'
            );
        } else {
            throw new Error(data.message || 'Erro ao atualizar destaque');
        }
    })
    .catch(error => {
        console.error('Erro ao destacar intimação:', error);
        showNotification('Erro ao atualizar destaque: ' + error.message, 'error');
        
        // Restaurar botão original
        button.innerHTML = originalContent;
        button.disabled = false;
    })
    .finally(() => {
        button.disabled = false;
    });
}

// Atualizar aparência do botão
function updateDestacarButton(button, destacada) {
    button.dataset.destacada = destacada.toString();
    
    if (destacada) {
        button.className = button.className.replace('btn-outline-warning', 'btn-warning');
        button.innerHTML = '<i class="bi bi-star-fill"></i>';
        button.title = 'Remover destaque';
    } else {
        button.className = button.className.replace('btn-warning', 'btn-outline-warning');
        button.innerHTML = '<i class="bi bi-star"></i>';
        button.title = 'Destacar intimação';
    }
}

// Atualizar linha da tabela e card
function updateTableRow(intimacaoId, destacada) {
    const row = document.querySelector(`tr[data-intimacao-id="${intimacaoId}"]`);
    if (row) {
        if (destacada) {
            row.classList.add('intimacao-destacada');
        } else {
            row.classList.remove('intimacao-destacada');
        }
        
        // Aplicar classe no card para mudança imediata
        const card = row.querySelector('.intimacao-card-compact, .card-intimacao');
        if (card) {
            if (destacada) {
                card.classList.add('intimacao-destacada');
            } else {
                card.classList.remove('intimacao-destacada');
            }
        }
        
        // GAMBIARRA: Atualizar campo invisível para o filtro
        const campoDestacada = row.querySelector('.intimacao-destacada-value');
        if (campoDestacada) {
            campoDestacada.value = destacada ? '1' : '0';
            console.log('DEBUG GAMBIARRA: Campo atualizado para', campoDestacada.value);
        }
    }
}

// Mostrar notificação
function showNotification(message, type = 'info') {
    // Usar toast do Bootstrap se disponível
    if (typeof bootstrap !== 'undefined' && bootstrap.Toast) {
        const toastContainer = document.getElementById('toast-container') || createToastContainer();
        const toastId = 'toast-' + Date.now();
        
        const toastHtml = `
            <div id="${toastId}" class="toast align-items-center text-white bg-${type === 'error' ? 'danger' : type} border-0" role="alert">
                <div class="d-flex">
                    <div class="toast-body">
                        ${message}
                    </div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
                </div>
            </div>
        `;
        
        toastContainer.insertAdjacentHTML('beforeend', toastHtml);
        
        const toastElement = document.getElementById(toastId);
        const toast = new bootstrap.Toast(toastElement);
        toast.show();
        
        // Remover elemento após ser escondido
        toastElement.addEventListener('hidden.bs.toast', () => {
            toastElement.remove();
        });
    } else {
        // Fallback para alert simples
        alert(message);
    }
}

// Criar container de toasts se não existir
function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container position-fixed top-0 end-0 p-3';
    container.style.zIndex = '9999';
    document.body.appendChild(container);
    return container;
}

// Função para filtrar intimações destacadas
function toggleFiltroDestacadas(checkbox) {
    const destacadas = checkbox.checked;
    const rows = document.querySelectorAll('tr.intimacao-row');
    
    rows.forEach(row => {
        const intimacaoId = row.dataset.intimacaoId;
        const isDestacada = row.classList.contains('intimacao-destacada');
        
        if (destacadas && !isDestacada) {
            row.style.display = 'none';
        } else {
            row.style.display = '';
        }
    });
    
    // Atualizar contador se existir
    updateContadorIntimacoes();
}

// Atualizar contador de intimações visíveis
function updateContadorIntimacoes() {
    const contador = document.getElementById('contador-intimacoes');
    if (contador) {
        const visibleRows = document.querySelectorAll('tr.intimacao-row:not([style*="display: none"])');
        contador.textContent = visibleRows.length;
    }
}

// Verificar se já foi inicializado
if (!window.destacarIntimacaoInicializado) {
    window.destacarIntimacaoInicializado = true;
    
    // Inicializar sistema de destaque
    document.addEventListener('DOMContentLoaded', function() {
        // Carregar CSS centralizado se não estiver carregado
        if (!document.getElementById('destacar-intimacao-css')) {
            const link = document.createElement('link');
            link.id = 'destacar-intimacao-css';
            link.rel = 'stylesheet';
            link.href = '/static/css/destacar-intimacao.css';
            document.head.appendChild(link);
        }
        
        // Aplicar destaque baseado no estado do banco
        aplicarDestacarBaseadoNoBanco();
    });
}

// Função para aplicar destaque baseado no estado do banco
function aplicarDestacarBaseadoNoBanco() {
    console.log('DEBUG: Aplicando destaque baseado no banco...');
    
    const linhasIntimacao = document.querySelectorAll('tr[data-intimacao-id]');
    console.log('DEBUG: Linhas encontradas:', linhasIntimacao.length);
    
    linhasIntimacao.forEach(linha => {
        const intimacaoId = linha.dataset.intimacaoId;
        
        // Buscar o botão de destacar dentro desta linha
        const botaoDestacar = linha.querySelector('button[data-intimacao-id]');
        
        if (botaoDestacar) {
            const destacada = botaoDestacar.dataset.destacada === 'true' || botaoDestacar.dataset.destacada === '1';
            console.log('DEBUG: Intimação', intimacaoId, 'destacada:', destacada, 'data:', botaoDestacar.dataset.destacada);
            
            // Aplicar classe na linha para consistência visual
            if (destacada) {
                linha.classList.add('intimacao-destacada');
                console.log('DEBUG: Classe intimacao-destacada aplicada para', intimacaoId);
            } else {
                linha.classList.remove('intimacao-destacada');
            }
        } else {
            console.log('DEBUG: Botão não encontrado para intimação', intimacaoId);
        }
    });
}
