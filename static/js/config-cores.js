/**
 * Gerenciador de Configurações de Cores para Acurácia
 * Carrega e aplica configurações dinâmicas de cores
 */

class ConfigCoresManager {
    constructor() {
        this.config = {
            cor_verde_min: 80,
            cor_amarelo_min: 60,
            cor_vermelho_min: 1,
            cor_cinza_max: 0,
            cores_ativadas: true
        };
        this.loaded = false;
    }

    /**
     * Carrega as configurações de cores do servidor
     */
    async carregarConfiguracoes() {
        try {
            const response = await fetch('/api/config/cores');
            const data = await response.json();
            
            if (data.success) {
                this.config = data.cores;
                this.loaded = true;
                console.log('🎨 Configurações de cores carregadas:', this.config);
            } else {
                console.warn('⚠️ Erro ao carregar configurações de cores:', data.message);
            }
        } catch (error) {
            console.error('❌ Erro ao carregar configurações de cores:', error);
        }
    }

    /**
     * Determina a classe CSS baseada na acurácia
     * @param {number} acuracia - Valor da acurácia (0-100)
     * @returns {string} - Classe CSS correspondente
     */
    determinarClasseAcuracia(acuracia) {
        if (!this.config.cores_ativadas) {
            return 'accuracy-muted';
        }

        if (acuracia >= this.config.cor_verde_min) {
            return 'accuracy-success';
        } else if (acuracia >= this.config.cor_amarelo_min) {
            return 'accuracy-warning';
        } else if (acuracia > this.config.cor_vermelho_min) {
            return 'accuracy-danger';
        } else {
            return 'accuracy-muted';
        }
    }

    /**
     * Determina o emoji baseado na acurácia
     * @param {number} acuracia - Valor da acurácia (0-100)
     * @returns {string} - Emoji correspondente
     */
    determinarEmojiAcuracia(acuracia) {
        if (!this.config.cores_ativadas) {
            return '⚪';
        }

        if (acuracia >= this.config.cor_verde_min) {
            return '🟢';
        } else if (acuracia >= this.config.cor_amarelo_min) {
            return '🟡';
        } else if (acuracia > this.config.cor_vermelho_min) {
            return '🔴';
        } else {
            return '⚪';
        }
    }

    /**
     * Determina a classe do badge baseada na acurácia
     * @param {number} acuracia - Valor da acurácia (0-100)
     * @returns {string} - Classe CSS do badge
     */
    determinarClasseBadge(acuracia) {
        if (!this.config.cores_ativadas) {
            return 'badge bg-secondary';
        }

        if (acuracia >= this.config.cor_verde_min) {
            return 'badge bg-success';
        } else if (acuracia >= this.config.cor_amarelo_min) {
            return 'badge bg-warning';
        } else if (acuracia > this.config.cor_vermelho_min) {
            return 'badge bg-danger';
        } else {
            return 'badge bg-secondary';
        }
    }

    /**
     * Formata a acurácia com badge
     * @param {number} acuracia - Valor da acurácia (0-100)
     * @returns {string} - HTML formatado
     */
    formatarAcuracia(acuracia) {
        if (acuracia === null || acuracia === undefined) {
            return `<span class="badge bg-secondary">N/A</span>`;
        }
        
        const badgeClass = this.determinarClasseBadge(acuracia);
        return `<span class="${badgeClass}">${acuracia}%</span>`;
    }

    /**
     * Aplica as configurações de cores a um elemento
     * @param {HTMLElement} element - Elemento a ser atualizado
     * @param {number} acuracia - Valor da acurácia
     */
    aplicarCores(element, acuracia) {
        if (element) {
            element.innerHTML = this.formatarAcuracia(acuracia);
        }
    }

    /**
     * Verifica se as configurações foram carregadas
     * @returns {boolean}
     */
    isLoaded() {
        return this.loaded;
    }

    /**
     * Força o recarregamento das configurações
     */
    async recarregar() {
        this.loaded = false;
        await this.carregarConfiguracoes();
    }
}

// Instância global do gerenciador
window.configCoresManager = new ConfigCoresManager();

// Carregar configurações automaticamente quando o DOM estiver pronto
document.addEventListener('DOMContentLoaded', function() {
    window.configCoresManager.carregarConfiguracoes();
});

// Função de conveniência para usar em outros scripts
window.formatarAcuraciaComConfig = function(acuracia) {
    return window.configCoresManager.formatarAcuracia(acuracia);
};

window.aplicarCoresAcuracia = function(element, acuracia) {
    return window.configCoresManager.aplicarCores(element, acuracia);
};
