/**
 * Componente Popover de Acurácia
 * Componente reutilizável para exibir histórico de acurácia de prompts
 */

class PopoverAcuracia {
    constructor() {
        this.popovers = new Map();
        this.timeouts = new Map();
    }

    /**
     * Mostrar popover de acurácia
     * @param {string} promptId - ID do prompt
     * @param {HTMLElement} triggerElement - Elemento que dispara o popover
     */
    mostrar(promptId, triggerElement) {
        // Limpar timeout anterior se existir
        if (this.timeouts.has(promptId)) {
            clearTimeout(this.timeouts.get(promptId));
        }

        // Se já existe popover, apenas mostrar
        if (this.popovers.has(promptId)) {
            this._posicionarPopover(promptId, triggerElement);
            return;
        }

        // Criar novo popover
        this._criarPopover(promptId, triggerElement);
    }

    /**
     * Esconder popover de acurácia
     * @param {string} promptId - ID do prompt
     */
    esconder(promptId) {
        const timeout = setTimeout(() => {
            const popover = this.popovers.get(promptId);
            if (popover) {
                popover.style.display = 'none';
            }
        }, 300);

        this.timeouts.set(promptId, timeout);
    }

    /**
     * Criar popover HTML
     * @param {string} promptId - ID do prompt
     * @param {HTMLElement} triggerElement - Elemento que dispara o popover
     */
    _criarPopover(promptId, triggerElement) {
        // Criar elemento do popover
        const popover = document.createElement('div');
        popover.id = `popover-acuracia-${promptId}`;
        popover.className = 'popover-acuracia';
        popover.innerHTML = `
            <div class="popover-header">
                <i class="bi bi-graph-up"></i>
                Histórico de Acurácia
            </div>
            <div class="popover-body">
                <div class="text-center py-3">
                    <div class="spinner-border spinner-border-sm text-primary" role="status">
                        <span class="visually-hidden">Carregando...</span>
                    </div>
                    <p class="text-muted mt-2 mb-0">Carregando histórico...</p>
                </div>
            </div>
            <div class="popover-footer">
                <i class="bi bi-info-circle"></i>
                Passe o mouse para manter visível
            </div>
        `;

        // Adicionar ao DOM
        document.body.appendChild(popover);

        // Armazenar referência
        this.popovers.set(promptId, popover);

        // Posicionar e mostrar
        this._posicionarPopover(promptId, triggerElement);

        // Carregar dados
        this._carregarDados(promptId);

        // Adicionar eventos para manter visível
        this._adicionarEventosPopover(promptId);
    }

    /**
     * Posicionar popover
     * @param {string} promptId - ID do prompt
     * @param {HTMLElement} triggerElement - Elemento que dispara o popover
     */
    _posicionarPopover(promptId, triggerElement) {
        const popover = this.popovers.get(promptId);
        if (!popover) return;

        const rect = triggerElement.getBoundingClientRect();
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        const scrollLeft = window.pageXOffset || document.documentElement.scrollLeft;

        // Posicionar acima do elemento
        popover.style.position = 'absolute';
        popover.style.top = (rect.top + scrollTop - popover.offsetHeight - 10) + 'px';
        popover.style.left = (rect.left + scrollLeft + rect.width / 2 - popover.offsetWidth / 2) + 'px';
        popover.style.display = 'block';

        // Ajustar se sair da tela
        this._ajustarPosicao(popover);
    }

    /**
     * Ajustar posição se popover sair da tela
     * @param {HTMLElement} popover - Elemento do popover
     */
    _ajustarPosicao(popover) {
        const viewport = {
            width: window.innerWidth,
            height: window.innerHeight
        };

        const popoverRect = popover.getBoundingClientRect();

        // Ajustar horizontalmente
        if (popoverRect.left < 10) {
            popover.style.left = '10px';
        } else if (popoverRect.right > viewport.width - 10) {
            popover.style.left = (viewport.width - popover.offsetWidth - 10) + 'px';
        }

        // Ajustar verticalmente
        if (popoverRect.top < 10) {
            const rect = popover.parentElement.getBoundingClientRect();
            popover.style.top = (rect.bottom + 10) + 'px';
        }
    }

    /**
     * Carregar dados do histórico
     * @param {string} promptId - ID do prompt
     */
    _carregarDados(promptId) {
        fetch(`/api/prompts/${promptId}/historico-acuracia`)
            .then(response => response.json())
            .then(data => {
                if (data.success && data.historico && data.historico.length > 0) {
                    this._exibirDados(promptId, data.historico);
                } else {
                    this._exibirSemDados(promptId);
                }
            })
            .catch(error => {
                console.error(`Erro ao carregar histórico do prompt ${promptId}:`, error);
                this._exibirErro(promptId);
            });
    }

    /**
     * Exibir dados do histórico
     * @param {string} promptId - ID do prompt
     * @param {Array} historico - Array com dados do histórico
     */
    _exibirDados(promptId, historico) {
        const popover = this.popovers.get(promptId);
        if (!popover) return;

        let html = '';
        historico.forEach((item, index) => {
            const badgeClass = this._getBadgeClass(item.acuracia_media);
            const dataFormatada = this._formatarData(item.ultima_analise);
            
            html += `
                <div class="popover-item">
                    <div>
                        <span class="badge ${badgeClass}">${item.acuracia_media}%</span>
                        <span class="info ms-2">${item.numero_intimacoes} int. • Temp: ${item.temperatura}</span>
                    </div>
                    <div class="info">
                        ${dataFormatada}
                    </div>
                </div>
            `;
        });

        const popoverBody = popover.querySelector('.popover-body');
        popoverBody.innerHTML = html;
    }

    /**
     * Exibir quando não há dados
     * @param {string} promptId - ID do prompt
     */
    _exibirSemDados(promptId) {
        const popover = this.popovers.get(promptId);
        if (!popover) return;

        const popoverBody = popover.querySelector('.popover-body');
        popoverBody.innerHTML = `
            <div class="text-center py-3">
                <i class="bi bi-graph-down fa-2x text-muted mb-2"></i>
                <p class="text-muted mb-0">Nenhum histórico encontrado</p>
                <small class="text-muted">Este prompt ainda não possui análises</small>
            </div>
        `;
    }

    /**
     * Exibir erro
     * @param {string} promptId - ID do prompt
     */
    _exibirErro(promptId) {
        const popover = this.popovers.get(promptId);
        if (!popover) return;

        const popoverBody = popover.querySelector('.popover-body');
        popoverBody.innerHTML = `
            <div class="text-center py-3">
                <i class="bi bi-exclamation-triangle fa-2x text-danger mb-2"></i>
                <p class="text-danger mb-0">Erro ao carregar</p>
                <small class="text-muted">Não foi possível obter o histórico</small>
            </div>
        `;
    }

    /**
     * Obter classe do badge baseada na acurácia
     * @param {number} acuracia - Valor da acurácia
     * @returns {string} Classe CSS do badge
     */
    _getBadgeClass(acuracia) {
        if (acuracia >= 80) return 'bg-success';
        if (acuracia >= 60) return 'bg-warning';
        if (acuracia > 0) return 'bg-danger';
        return 'bg-secondary';
    }

    /**
     * Formatat data
     * @param {string} dateString - String da data
     * @returns {string} Data formatada
     */
    _formatarData(dateString) {
        if (!dateString) return 'N/A';
        
        try {
            const date = new Date(dateString);
            if (isNaN(date.getTime())) return 'Data inválida';
            
            const day = String(date.getDate()).padStart(2, '0');
            const month = String(date.getMonth() + 1).padStart(2, '0');
            const year = date.getFullYear();
            const hours = String(date.getHours()).padStart(2, '0');
            const minutes = String(date.getMinutes()).padStart(2, '0');
            
            return `${day}/${month}/${year} ${hours}:${minutes}`;
        } catch (e) {
            return 'Data inválida';
        }
    }

    /**
     * Adicionar eventos ao popover
     * @param {string} promptId - ID do prompt
     */
    _adicionarEventosPopover(promptId) {
        const popover = this.popovers.get(promptId);
        if (!popover) return;

        // Manter visível quando mouse estiver sobre o popover
        popover.addEventListener('mouseenter', () => {
            if (this.timeouts.has(promptId)) {
                clearTimeout(this.timeouts.get(promptId));
            }
        });

        popover.addEventListener('mouseleave', () => {
            this.esconder(promptId);
        });
    }

    /**
     * Destruir popover
     * @param {string} promptId - ID do prompt
     */
    destruir(promptId) {
        const popover = this.popovers.get(promptId);
        if (popover) {
            popover.remove();
            this.popovers.delete(promptId);
        }

        if (this.timeouts.has(promptId)) {
            clearTimeout(this.timeouts.get(promptId));
            this.timeouts.delete(promptId);
        }
    }

    /**
     * Destruir todos os popovers
     */
    destruirTodos() {
        for (const promptId of this.popovers.keys()) {
            this.destruir(promptId);
        }
    }
}

// Instância global do componente
window.popoverAcuracia = new PopoverAcuracia();

// Funções globais para compatibilidade
window.mostrarPopoverAcuracia = function(promptId) {
    const triggerElement = document.getElementById(`acuracia-${promptId}`);
    if (triggerElement) {
        window.popoverAcuracia.mostrar(promptId, triggerElement);
    }
};

window.esconderPopoverAcuracia = function(promptId) {
    window.popoverAcuracia.esconder(promptId);
};
