/**
 * Componente de Select Customizado com Badges
 * Permite exibir badges coloridos dentro das opções
 */
class CustomSelect {
    constructor(selectElement, options = {}) {
        this.originalSelect = selectElement;
        this.options = {
            placeholder: 'Selecione uma opção...',
            allowSearch: false,
            showBadges: true,
            ...options
        };
        
        this.isOpen = false;
        this.selectedValue = '';
        this.selectedText = '';
        this.selectedBadge = '';
        
        this.init();
    }
    
    init() {
        // Criar container do select customizado
        this.createCustomSelect();
        
        // Adicionar event listeners
        this.addEventListeners();
        
        // Carregar opções do select original
        this.loadOptions();
        
        // Definir valor inicial se já houver um selecionado
        this.setInitialValue();
        
        // Esconder select original
        this.originalSelect.style.display = 'none';
    }
    
    createCustomSelect() {
        // Container principal
        this.container = document.createElement('div');
        this.container.className = 'custom-select-container';
        
        // Select customizado
        this.customSelect = document.createElement('div');
        this.customSelect.className = 'custom-select';
        this.customSelect.innerHTML = `
            <span class="custom-select-text">${this.options.placeholder}</span>
            <span class="custom-select-arrow">▼</span>
        `;
        
        // Dropdown
        this.dropdown = document.createElement('div');
        this.dropdown.className = 'custom-select-dropdown';
        
        // Montar estrutura
        this.container.appendChild(this.customSelect);
        this.container.appendChild(this.dropdown);
        
        // Inserir após o select original
        this.originalSelect.parentNode.insertBefore(this.container, this.originalSelect.nextSibling);
    }
    
    loadOptions() {
        this.dropdown.innerHTML = '';
        
        const options = this.originalSelect.querySelectorAll('option');
        options.forEach((option, index) => {
            if (option.value === '') return; // Pular opção vazia
            
            const optionElement = document.createElement('div');
            optionElement.className = 'custom-select-option';
            optionElement.dataset.value = option.value;
            optionElement.dataset.index = index;
            
            const text = option.textContent;
            const badgeHtml = this.options.showBadges ? 
                `<span class="custom-select-option-badge badge-secondary" data-prompt-id="${option.dataset.promptId || ''}">Carregando...</span>` : '';
            
            optionElement.innerHTML = `
                <span class="custom-select-option-text">${text}</span>
                ${badgeHtml}
            `;
            
            this.dropdown.appendChild(optionElement);
        });
        
        // Carregar badges se habilitado
        if (this.options.showBadges) {
            this.loadBadges();
        }
    }
    
    async loadBadges() {
        if (!window.configCoresManager) {
            console.warn('ConfigCoresManager não encontrado');
            return;
        }
        
        // Aguardar configurações carregarem
        if (!window.configCoresManager.isLoaded()) {
            await window.configCoresManager.carregarConfiguracoes();
        }
        
        const badgeElements = this.dropdown.querySelectorAll('.custom-select-option-badge[data-prompt-id]');
        const promptIds = Array.from(badgeElements)
            .map(b => b.dataset.promptId)
            .filter(Boolean);
        if (!promptIds.length) {
            return;
        }

        const bindPopoverHover = (badge, promptId) => {
            if (badge.dataset.historicoPopoverBound === '1') return;
            badge.dataset.historicoPopoverBound = '1';
            badge.style.cursor = 'help';
            badge.title = 'Ver histórico de acurácia por condições';
            badge.addEventListener('mouseenter', (ev) => {
                ev.stopPropagation();
                if (typeof window.mostrarPopoverAcuracia === 'function') {
                    window.mostrarPopoverAcuracia(promptId, badge);
                }
            });
            badge.addEventListener('mouseleave', () => {
                if (typeof window.esconderPopoverAcuracia === 'function') {
                    window.esconderPopoverAcuracia(promptId);
                }
            });
        };

        const aplicarBadge = (badge, promptId, historico) => {
            if (historico && historico.length > 0) {
                const acuracia = historico[0].acuracia_media;
                if (window.configCoresManager) {
                    const badgeClass = window.configCoresManager.determinarClasseBadge(acuracia);
                    badge.className = `custom-select-option-badge ${badgeClass}`;
                    badge.textContent = `${acuracia}%`;
                } else {
                    badge.className = 'custom-select-option-badge badge bg-secondary';
                    badge.textContent = `${acuracia}%`;
                }
            } else {
                badge.className = 'custom-select-option-badge badge bg-secondary';
                badge.textContent = 'N/A';
            }
            bindPopoverHover(badge, promptId);
        };

        try {
            const response = await fetch('/api/prompts/historico-acuracia-batch', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ prompt_ids: promptIds }),
            });
            const data = await response.json();
            const porPrompt = (data.success && data.por_prompt) ? data.por_prompt : {};
            badgeElements.forEach(badge => {
                const promptId = badge.dataset.promptId;
                if (!promptId) return;
                aplicarBadge(badge, promptId, porPrompt[promptId] || []);
            });
        } catch (error) {
            console.error('Erro ao carregar acurácia dos prompts (batch):', error);
            badgeElements.forEach(badge => {
                const promptId = badge.dataset.promptId;
                if (!promptId) return;
                badge.className = 'custom-select-option-badge badge-secondary';
                badge.textContent = 'N/A';
                bindPopoverHover(badge, promptId);
            });
        }
    }
    
    addEventListeners() {
        // Click no select
        this.customSelect.addEventListener('click', (e) => {
            e.stopPropagation();
            this.toggle();
        });
        
        // Click nas opções
        this.dropdown.addEventListener('click', (e) => {
            const option = e.target.closest('.custom-select-option');
            if (option) {
                this.selectOption(option);
            }
        });
        
        // Click fora para fechar
        document.addEventListener('click', (e) => {
            if (!this.container.contains(e.target)) {
                this.close();
            }
        });
        
        // Keyboard navigation
        this.customSelect.addEventListener('keydown', (e) => {
            this.handleKeydown(e);
        });
    }
    
    toggle() {
        if (this.isOpen) {
            this.close();
        } else {
            this.open();
        }
    }
    
    open() {
        this.isOpen = true;
        this.customSelect.classList.add('open');
        this.dropdown.classList.add('show');
        
        // Focar no select
        this.customSelect.focus();
    }
    
    close() {
        this.isOpen = false;
        this.customSelect.classList.remove('open');
        this.dropdown.classList.remove('show');
    }
    
    selectOption(optionElement) {
        const value = optionElement.dataset.value;
        const text = optionElement.querySelector('.custom-select-option-text').textContent;
        const badge = optionElement.querySelector('.custom-select-option-badge');
        const badgeText = badge ? badge.textContent : '';
        const badgeClass = badge ? badge.className : '';
        
        // Atualizar seleção
        this.selectedValue = value;
        this.selectedText = text;
        this.selectedBadge = badgeText;
        
        // Atualizar display
        this.updateDisplay(text, badgeText, badgeClass);
        
        // Atualizar select original
        this.originalSelect.value = value;
        console.log(`🔧 Select customizado: valor definido como "${value}"`);
        console.log(`🔧 Select original value: "${this.originalSelect.value}"`);
        
        // Disparar evento change no select original
        const changeEvent = new Event('change', { bubbles: true });
        this.originalSelect.dispatchEvent(changeEvent);
        
        // Disparar evento input também (para formulários)
        const inputEvent = new Event('input', { bubbles: true });
        this.originalSelect.dispatchEvent(inputEvent);
        
        // Fechar dropdown
        this.close();
    }
    
    updateDisplay(text, badgeText, badgeClass) {
        const textElement = this.customSelect.querySelector('.custom-select-text');
        
        if (badgeText && this.options.showBadges) {
            textElement.innerHTML = `${text} <span class="custom-select-option-badge ${badgeClass}">${badgeText}</span>`;
        } else {
            textElement.textContent = text;
        }
    }
    
    handleKeydown(e) {
        if (!this.isOpen) {
            if (e.key === 'Enter' || e.key === ' ' || e.key === 'ArrowDown') {
                e.preventDefault();
                this.open();
            }
            return;
        }
        
        switch (e.key) {
            case 'Escape':
                e.preventDefault();
                this.close();
                break;
            case 'ArrowDown':
                e.preventDefault();
                this.navigateOptions(1);
                break;
            case 'ArrowUp':
                e.preventDefault();
                this.navigateOptions(-1);
                break;
            case 'Enter':
                e.preventDefault();
                this.selectHighlighted();
                break;
        }
    }
    
    navigateOptions(direction) {
        const options = this.dropdown.querySelectorAll('.custom-select-option');
        const current = this.dropdown.querySelector('.custom-select-option.highlighted');
        
        let nextIndex = 0;
        if (current) {
            const currentIndex = Array.from(options).indexOf(current);
            nextIndex = currentIndex + direction;
            if (nextIndex < 0) nextIndex = options.length - 1;
            if (nextIndex >= options.length) nextIndex = 0;
        }
        
        // Remover highlight anterior
        options.forEach(opt => opt.classList.remove('highlighted'));
        
        // Adicionar highlight
        if (options[nextIndex]) {
            options[nextIndex].classList.add('highlighted');
        }
    }
    
    selectHighlighted() {
        const highlighted = this.dropdown.querySelector('.custom-select-option.highlighted');
        if (highlighted) {
            this.selectOption(highlighted);
        }
    }
    
    setInitialValue() {
        const initialValue = this.originalSelect.value;
        console.log(`🔧 Valor inicial do select: "${initialValue}"`);
        
        if (initialValue && initialValue !== '') {
            const option = this.dropdown.querySelector(`[data-value="${initialValue}"]`);
            if (option) {
                const text = option.querySelector('.custom-select-option-text').textContent;
                const badge = option.querySelector('.custom-select-option-badge');
                const badgeText = badge ? badge.textContent : '';
                const badgeClass = badge ? badge.className : '';
                
                this.selectedValue = initialValue;
                this.selectedText = text;
                this.selectedBadge = badgeText;
                
                this.updateDisplay(text, badgeText, badgeClass);
                console.log(`🔧 Valor inicial definido: "${initialValue}"`);
            }
        }
    }
    
    // Métodos públicos
    getValue() {
        return this.selectedValue;
    }
    
    setValue(value) {
        const option = this.dropdown.querySelector(`[data-value="${value}"]`);
        if (option) {
            this.selectOption(option);
        }
    }
    
    // Sincronizar valor antes do envio do formulário
    syncValue() {
        if (this.selectedValue) {
            this.originalSelect.value = this.selectedValue;
            console.log(`🔧 Valor sincronizado: "${this.selectedValue}"`);
        }
    }
    
    destroy() {
        // Restaurar select original
        this.originalSelect.style.display = '';
        
        // Remover container customizado
        if (this.container && this.container.parentNode) {
            this.container.parentNode.removeChild(this.container);
        }
    }
}

// Função helper para inicializar
function initCustomSelect(selector, options = {}) {
    const selectElement = document.querySelector(selector);
    if (selectElement) {
        return new CustomSelect(selectElement, options);
    }
    return null;
}

// Exportar para uso global
window.CustomSelect = CustomSelect;
window.initCustomSelect = initCustomSelect;
