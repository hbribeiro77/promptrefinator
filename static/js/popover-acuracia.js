/**
 * Componente Popover de Acurácia
 * Componente reutilizável para exibir histórico de acurácia de prompts
 */

function _escapeHtmlPopoverAcuracia(s) {
    if (s == null || s === undefined) return '';
    const d = document.createElement('div');
    d.textContent = String(s);
    return d.innerHTML;
}

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
                Histórico de acurácia por condições
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

        let rows = '';
        historico.forEach((item) => {
            const badgeClass = this._getBadgeClass(item.acuracia_media);
            const dataUltima = this._formatarData(item.ultima_analise);
            const modelo = item.modelo != null && String(item.modelo).trim() !== ''
                ? String(item.modelo).trim()
                : 'N/D';
            const nAnalises = item.total_analises != null ? item.total_analises : 0;
            rows += `
                <tr>
                    <td class="text-center"><span class="badge bg-info">${item.numero_intimacoes}</span></td>
                    <td><small class="text-muted">${_escapeHtmlPopoverAcuracia(modelo)}</small></td>
                    <td class="text-center"><span class="badge bg-secondary">${item.temperatura}</span></td>
                    <td class="text-center"><small class="text-muted">${nAnalises}</small></td>
                    <td class="text-center"><span class="badge ${badgeClass}">${item.acuracia_media}%</span></td>
                    <td class="text-center"><small class="text-muted">${item.acuracia_minima}% – ${item.acuracia_maxima}%</small></td>
                    <td class="text-center"><small class="text-muted">${_escapeHtmlPopoverAcuracia(dataUltima)}</small></td>
                </tr>
            `;
        });

        const html = `
            <div class="table-responsive popover-acuracia-table-wrap">
                <table class="table table-sm table-bordered align-middle mb-0 popover-acuracia-table">
                    <thead class="table-light">
                        <tr>
                            <th class="text-center small">Int.</th>
                            <th class="small">Modelo</th>
                            <th class="text-center small">Temp.</th>
                            <th class="text-center small">Qtd.</th>
                            <th class="text-center small">Acurácia</th>
                            <th class="text-center small">Mín/Máx</th>
                            <th class="text-center small">Última</th>
                        </tr>
                    </thead>
                    <tbody>${rows}</tbody>
                </table>
            </div>
            <div class="mt-2 small text-muted px-1">
                <i class="bi bi-info-circle"></i>
                Mesmas condições da página do prompt: intimações, modelo, temperatura e agregados por recorte.
            </div>
        `;

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
window.mostrarPopoverAcuracia = function(promptId, triggerElement) {
    const el = triggerElement || document.getElementById(`acuracia-${promptId}`);
    if (el) {
        window.popoverAcuracia.mostrar(promptId, el);
    }
};

window.esconderPopoverAcuracia = function(promptId) {
    window.popoverAcuracia.esconder(promptId);
};
