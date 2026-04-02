/**
 * Módulo de Taxa de Acerto - Sistema Prompt Refinator
 * Funções reutilizáveis para exibição de taxa de acerto com popover interativo
 */

// Carregar taxas de acerto das intimações
function carregarTaxasAcerto() {
    console.log('🔄 Carregando taxas de acerto...');
    
    // Verificar se há um prompt específico selecionado
    const promptEspecifico = document.getElementById('prompt-especifico');
    const temperaturaEspecifica = document.getElementById('temperatura-especifica');
    const promptId = promptEspecifico ? promptEspecifico.value : null;
    const temperatura = temperaturaEspecifica ? temperaturaEspecifica.value : null;
    
    if (promptId && promptId !== '' && temperatura && temperatura !== '') {
        console.log('🎯 Carregando taxa de acerto do prompt específico com temperatura:', promptId, temperatura);
        carregarTaxasAcertoPromptTemperatura(promptId, temperatura);
    } else if (promptId && promptId !== '') {
        console.log('🎯 Carregando taxa de acerto do prompt específico:', promptId);
        carregarTaxasAcertoPromptEspecifico(promptId);
    } else {
        console.log('📊 Carregando taxa de acerto geral...');
        carregarTaxasAcertoGeral();
    }
}

// Função para carregar taxa de acerto geral
function carregarTaxasAcertoGeral() {
    fetch('/api/intimacoes/taxa-acerto')
        .then(response => {
            console.log('📡 Resposta da API geral:', response.status);
            return response.json();
        })
        .then(data => {
            console.log('📊 Dados gerais recebidos:', data);
            if (data.success) {
                console.log('✅ Taxas de acerto gerais carregadas:', data.taxas_acerto);
                atualizarTaxasAcerto(data.taxas_acerto);
            } else {
                console.error('❌ Erro ao carregar taxas de acerto gerais:', data.message);
            }
        })
        .catch(error => {
            console.error('❌ Erro na requisição de taxas de acerto gerais:', error);
        });
}

// Função para carregar taxa de acerto de prompt específico
function carregarTaxasAcertoPromptEspecifico(promptId) {
    fetch(`/api/intimacoes/taxa-acerto-prompt/${promptId}`)
        .then(response => {
            console.log('📡 Resposta da API prompt específico:', response.status);
            return response.json();
        })
        .then(data => {
            console.log('📊 Dados prompt específico recebidos:', data);
            if (data.success) {
                console.log('✅ Taxas de acerto do prompt específico carregadas:', data.taxas_acerto);
                atualizarTaxasAcertoArray(data.taxas_acerto);
            } else {
                console.error('❌ Erro ao carregar taxas de acerto do prompt específico:', data.message);
            }
        })
        .catch(error => {
            console.error('❌ Erro na requisição de taxas de acerto do prompt específico:', error);
        });
}

// Função para carregar taxa de acerto do prompt específico com temperatura específica
function carregarTaxasAcertoPromptTemperatura(promptId, temperatura) {
    fetch(`/api/intimacoes/taxa-acerto-prompt-temperatura/${promptId}/${temperatura}`)
        .then(response => {
            console.log('📡 Resposta da API prompt + temperatura:', response.status);
            return response.json();
        })
        .then(data => {
            console.log('📊 Dados prompt + temperatura recebidos:', data);
            if (data.success) {
                console.log('✅ Taxas de acerto do prompt + temperatura carregadas:', data.taxas_acerto);
                atualizarTaxasAcertoArray(data.taxas_acerto);
            } else {
                console.error('❌ Erro ao carregar taxas de acerto do prompt + temperatura:', data.message);
            }
        })
        .catch(error => {
            console.error('❌ Erro na requisição de taxas de acerto do prompt + temperatura:', error);
        });
}

/** Célula sem nenhuma análise (API não retorna a intimação ou total_analises === 0). */
function aplicarCelulaTaxaSemAnalises(elemento) {
    if (!elemento) return;
    elemento.classList.remove('taxa-acerto-placeholder');
    elemento.innerHTML = `
        <div class="d-flex flex-column align-items-center text-muted taxa-acerto-sem-testes py-1"
             title="Nenhuma análise foi registrada ainda para esta intimação.">
            <i class="bi bi-minus-circle" aria-hidden="true"></i>
            <small class="text-center lh-sm" style="max-width: 5rem;">Sem testes</small>
        </div>
    `;
}

// Atualizar taxas de acerto na interface (para objeto com chaves)
function atualizarTaxasAcerto(taxasAcerto) {
    console.log('🎯 Atualizando taxas de acerto na interface:', taxasAcerto);
    Object.keys(taxasAcerto).forEach(intimacaoId => {
        const elemento = document.getElementById(`taxa-acerto-${intimacaoId}`);
        console.log(`🔍 Procurando elemento para intimação ${intimacaoId}:`, elemento);
        if (elemento) {
            const dados = taxasAcerto[intimacaoId];
            const total = dados.total_analises != null ? Number(dados.total_analises) : 0;
            const taxa = dados.taxa_acerto;
            const acertos = dados.acertos;
            if (!total || total === 0) {
                aplicarCelulaTaxaSemAnalises(elemento);
                return;
            }
            elemento.classList.remove('taxa-acerto-placeholder');
            
            // Determinar cor do badge baseado na taxa
            let badgeClass = 'bg-secondary';
            if (taxa >= 80) {
                badgeClass = 'bg-success';
            } else if (taxa >= 60) {
                badgeClass = 'bg-warning';
            } else if (taxa >= 40) {
                badgeClass = 'bg-danger';
            }
            
            elemento.innerHTML = `
                <div class="d-flex flex-column align-items-center position-relative" 
                     data-intimacao-id="${intimacaoId}"
                     style="cursor: pointer;">
                    <span class="badge ${badgeClass} mb-1">${taxa}%</span>
                    <small class="text-muted">${acertos}/${total}</small>
                    
                    <!-- Popover customizado -->
                    <div class="custom-popover" id="popover-${intimacaoId}" style="display: none;">
                        <div class="popover-content">
                            <div class="popover-body">
                                <div class="text-center">
                                    <i class="bi bi-hourglass-split"></i>
                                    Carregando detalhes...
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            
            // Adicionar eventos para popover customizado
            const triggerElement = elemento.querySelector('[data-intimacao-id]');
            const popoverElement = elemento.querySelector('.custom-popover');
            
            // Variáveis para controle do popover
            elemento.popoverTimeout = null;
            elemento.showTimeout = null;
            elemento.isPopoverVisible = false;
            
            // Mostrar popover quando entrar no elemento (com delay)
            triggerElement.addEventListener('mouseenter', function() {
                clearTimeout(elemento.popoverTimeout);
                clearTimeout(elemento.showTimeout);
                
                // Armazenar ID da intimação atual globalmente
                window.currentIntimacaoId = intimacaoId;
                console.log('🔍 Intimação atual definida:', window.currentIntimacaoId);
                
                if (!elemento.isPopoverVisible) {
                    // Delay de 500ms para mostrar o popover
                    elemento.showTimeout = setTimeout(() => {
                        carregarDetalhesPrompts(intimacaoId, popoverElement);
                        posicionarPopoverInteligentemente(popoverElement, triggerElement);
                        popoverElement.style.display = 'block';
                        popoverElement.style.visibility = 'visible';
                        popoverElement.style.opacity = '1';
                        elemento.isPopoverVisible = true;
                        
                        console.log('🔍 Popover criado e exibido:', {
                            display: popoverElement.style.display,
                            visibility: popoverElement.style.visibility,
                            opacity: popoverElement.style.opacity,
                            intimacaoId: intimacaoId
                        });
                    }, 500);
                }
            });
            
            // Esconder popover quando sair do elemento
            triggerElement.addEventListener('mouseleave', function() {
                clearTimeout(elemento.showTimeout);
                elemento.popoverTimeout = setTimeout(() => {
                    if (elemento.isPopoverVisible) {
                        popoverElement.style.display = 'none';
                        popoverElement.style.visibility = 'hidden';
                        popoverElement.style.opacity = '0';
                        elemento.isPopoverVisible = false;
                        
                        // Limpar checkboxes quando popover fechar
                        limparCheckboxesPopover(popoverElement);
                        
                        console.log('🔍 Popover escondido:', {
                            intimacaoId: intimacaoId,
                            display: popoverElement.style.display
                        });
                    }
                }, 100);
            });
            
            // Manter popover visível quando mouse estiver sobre ele
            popoverElement.addEventListener('mouseenter', function() {
                clearTimeout(elemento.popoverTimeout);
            });
            
            // Esconder popover quando sair dele
            popoverElement.addEventListener('mouseleave', function() {
                elemento.popoverTimeout = setTimeout(() => {
                    if (elemento.isPopoverVisible) {
                        popoverElement.style.display = 'none';
                        popoverElement.style.visibility = 'hidden';
                        popoverElement.style.opacity = '0';
                        elemento.isPopoverVisible = false;
                        
                        // Limpar checkboxes quando popover fechar
                        limparCheckboxesPopover(popoverElement);
                    }
                }, 100);
            });
            
            console.log(`✅ Taxa de acerto atualizada para intimação ${intimacaoId}: ${taxa}% (${acertos}/${total})`);
        } else {
            console.warn(`⚠️ Elemento não encontrado para intimação ${intimacaoId}`);
        }
    });
    document.querySelectorAll('.taxa-acerto-placeholder').forEach(aplicarCelulaTaxaSemAnalises);
    if (typeof sincronizarVisibilidadeLinhasIntimacoes === 'function') {
        sincronizarVisibilidadeLinhasIntimacoes({ resetPagina: false });
    }
}

// Atualizar taxas de acerto na interface (para array de objetos)
function atualizarTaxasAcertoArray(taxasAcertoArray) {
    console.log('🎯 Atualizando taxas de acerto na interface (array):', taxasAcertoArray);
    taxasAcertoArray.forEach(dados => {
        const intimacaoId = dados.intimacao_id;
        const elemento = document.getElementById(`taxa-acerto-${intimacaoId}`);
        console.log(`🔍 Procurando elemento para intimação ${intimacaoId}:`, elemento);
        if (elemento) {
            const total = dados.total_analises != null ? Number(dados.total_analises) : 0;
            const taxa = dados.taxa_acerto;
            const acertos = dados.acertos;
            if (!total || total === 0) {
                aplicarCelulaTaxaSemAnalises(elemento);
                return;
            }
            elemento.classList.remove('taxa-acerto-placeholder');
            
            // Determinar cor do badge baseado na taxa
            let badgeClass = 'bg-secondary';
            if (taxa >= 80) {
                badgeClass = 'bg-success';
            } else if (taxa >= 60) {
                badgeClass = 'bg-warning';
            } else if (taxa >= 40) {
                badgeClass = 'bg-danger';
            }
            
            // Verificar se há um prompt específico selecionado
            const promptEspecifico = document.getElementById('prompt-especifico');
            const promptId = promptEspecifico ? promptEspecifico.value : null;
            const isPromptEspecifico = promptId && promptId !== '';
            
            elemento.innerHTML = `
                <div class="d-flex flex-column align-items-center position-relative" 
                     data-intimacao-id="${intimacaoId}"
                     data-prompt-especifico="${isPromptEspecifico ? promptId : ''}"
                     style="cursor: pointer;">
                    <span class="badge ${badgeClass} mb-1" style="font-size: 0.8em;">
                        ${taxa}%
                    </span>
                    <small class="text-muted" style="font-size: 0.7em;">
                        ${acertos}/${total}
                    </small>
                    
                    <!-- Popover customizado (EXATAMENTE igual à página de análise) -->
                    <div class="custom-popover" id="popover-${intimacaoId}" style="display: none;">
                        <div class="popover-content">
                            <div class="popover-body">
                                <div class="text-center">
                                    <i class="bi bi-hourglass-split"></i>
                                    Carregando detalhes...
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            
            // USAR COMPONENTE REUTILIZÁVEL (SEM DUPLICAÇÃO)
            setTimeout(() => {
                const triggerElement = elemento.querySelector('[data-intimacao-id]');
                if (triggerElement) {
                    criarPopoverReutilizavel(intimacaoId, triggerElement);
                }
            }, 100);
            
            console.log(`✅ Taxa de acerto atualizada para intimação ${intimacaoId}: ${taxa}% (${acertos}/${total})`);
        } else {
            console.warn(`⚠️ Elemento não encontrado para intimação ${intimacaoId}`);
        }
    });
    document.querySelectorAll('.taxa-acerto-placeholder').forEach(aplicarCelulaTaxaSemAnalises);
    if (typeof sincronizarVisibilidadeLinhasIntimacoes === 'function') {
        sincronizarVisibilidadeLinhasIntimacoes({ resetPagina: false });
    }
}

// Carregar detalhes dos prompts para o popover customizado
function carregarDetalhesPrompts(intimacaoId, popoverElement) {
    // Verificar se já foi carregado para evitar requisições desnecessárias
    if (popoverElement.dataset.loaded === 'true') {
        return; // Já foi carregado
    }
    
    // Mostrar loading no popover
    popoverElement.querySelector('.popover-body').innerHTML = `
        <div class="text-center">
            <i class="bi bi-hourglass-split"></i>
            Carregando detalhes...
        </div>
    `;
    
    // Verificar se há um prompt específico selecionado
    const promptEspecifico = document.getElementById('prompt-especifico');
    const promptId = promptEspecifico ? promptEspecifico.value : null;
    const isPromptEspecifico = promptId && promptId !== '';
    
    // Usar API diferente baseado no contexto
    const apiUrl = isPromptEspecifico 
        ? `/api/intimacoes/performance-prompt-temperatura/${promptId}`
        : `/api/intimacoes/${intimacaoId}/prompts-acerto`;
    
    fetch(apiUrl)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                let prompts = [];
                
                if (isPromptEspecifico) {
                    // Para prompt específico, filtrar dados da intimação
                    const performance = data.performance;
                    const intimacaoData = performance[intimacaoId];
                    
                    if (!intimacaoData) {
                        const content = '<div class="text-center"><em>Nenhuma análise encontrada para esta intimação</em></div>';
                        popoverElement.querySelector('.popover-body').innerHTML = content;
                        popoverElement.dataset.loaded = 'true';
                        return;
                    }
                    
                    // Buscar nome do prompt específico
                    buscarNomePrompt(promptId).then(promptNome => {
                        // Criar estrutura para cada temperatura com nome correto
                        prompts = intimacaoData.temperaturas.map(temp => ({
                            prompt_id: promptId,
                            prompt_nome: promptNome || 'Prompt Selecionado',
                            modelo: 'Modelo',
                            temperatura: temp.temperatura,
                            acertos: temp.acertos,
                            total_analises: temp.total_analises,
                            taxa_acerto: temp.taxa_acerto
                        }));
                        
                        // Usar a mesma lógica de construção do popover
                        construirConteudoPopover(popoverElement, prompts, true);
                    });
                    
                    // Criar estrutura temporária para cada temperatura
                    prompts = intimacaoData.temperaturas.map(temp => ({
                        prompt_id: promptId,
                        prompt_nome: 'Prompt Selecionado', // Temporário
                        modelo: 'Modelo',
                        temperatura: temp.temperatura,
                        acertos: temp.acertos,
                        total_analises: temp.total_analises,
                        taxa_acerto: temp.taxa_acerto
                    }));
                } else {
                    // Para caso geral, usar dados normais
                    prompts = data.prompts_acerto || [];
                }
                if (prompts.length === 0) {
                    const content = '<div class="text-center"><em>Nenhuma análise encontrada</em></div>';
                    popoverElement.querySelector('.popover-body').innerHTML = content;
                    popoverElement.dataset.loaded = 'true';
                    return;
                }
                
                // Construir conteúdo do popover
                let content = '<div class="text-start">';
                if (isPromptEspecifico) {
                    const promptNome = prompts.length > 0 ? prompts[0].prompt_nome : 'Prompt Selecionado';
                    content += `<div class="fw-bold mb-2">Performance do ${promptNome}:</div>`;
                } else {
                    content += '<div class="fw-bold mb-2">Prompts Testados:</div>';
                }
                
                prompts.forEach((prompt, index) => {
                    const taxa = prompt.taxa_acerto;
                    let badgeClass = 'bg-secondary';
                    if (taxa >= 80) {
                        badgeClass = 'bg-success';
                    } else if (taxa >= 60) {
                        badgeClass = 'bg-warning';
                    } else if (taxa >= 40) {
                        badgeClass = 'bg-danger';
                    }
                    
                    content += `
                        <div class="mb-2 p-2 border rounded prompt-card" 
                             style="transition: all 0.2s ease;">
                            <div class="d-flex align-items-start">
                                ${!isPromptEspecifico ? `
                                <div class="me-2 mt-1">
                                    <input type="checkbox" 
                                           class="form-check-input prompt-checkbox" 
                                           data-prompt-id="${prompt.prompt_id}"
                                           data-prompt-nome="${prompt.prompt_nome}"
                                           onchange="updateCompareButton()">
                                </div>
                                ` : ''}
                                <div class="flex-grow-1" 
                                     ${!isPromptEspecifico ? `onclick="window.open('/prompts/${prompt.prompt_id}', '_blank')" style="cursor: pointer;"` : ''}>
                                    <div class="d-flex justify-content-between align-items-start">
                                        <div class="flex-grow-1">
                                            <div class="fw-bold text-primary prompt-name" 
                                                 style="font-size: 0.9em;">
                                                ${prompt.prompt_nome}
                                            </div>
                                            <div class="text-muted small">
                                                ${prompt.modelo} • Temp: ${prompt.temperatura}
                                            </div>
                                            <div class="mt-1">
                                                <small class="text-muted">${prompt.acertos}/${prompt.total_analises} acertos</small>
                                            </div>
                                        </div>
                                        <span class="badge ${badgeClass} ms-2">${taxa}%</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    `;
                });
                
                // Adicionar footer apenas se não for prompt específico
                if (!isPromptEspecifico) {
                    content += `
                        <div class="popover-footer">
                            <button type="button" 
                                    class="btn btn-primary btn-sm w-100" 
                                    id="btn-compare-prompts"
                                    onclick="compareSelectedPrompts()">
                                <i class="bi bi-arrow-left-right"></i>
                                Comparar Prompts Selecionados
                            </button>
                        </div>
                    `;
                }
                
                // Atualizar conteúdo do popover
                popoverElement.querySelector('.popover-body').innerHTML = content;
                popoverElement.dataset.loaded = 'true';
                
                // Adicionar event listeners apenas se não for prompt específico
                if (!isPromptEspecifico) {
                    setTimeout(() => {
                        // Adicionar event listeners para checkboxes
                        adicionarEventListenersCheckboxes();
                        updateCompareButton();
                    }, 100);
                }
                
                console.log(`✅ Detalhes carregados para intimação ${intimacaoId}: ${prompts.length} prompts`);
            } else {
                console.error('❌ Erro ao carregar detalhes:', data.message);
                popoverElement.querySelector('.popover-body').innerHTML = 
                    '<div class="text-center text-danger"><em>Erro ao carregar detalhes</em></div>';
            }
        })
        .catch(error => {
            console.error('❌ Erro na requisição de detalhes:', error);
            popoverElement.querySelector('.popover-body').innerHTML = 
                '<div class="text-center text-danger"><em>Erro ao carregar detalhes</em></div>';
        });
}

// Posicionar popover de forma inteligente
function posicionarPopoverInteligentemente(popoverElement, triggerElement) {
    const viewportWidth = window.innerWidth;
    const viewportHeight = window.innerHeight;
    
    // Obter posição do elemento trigger (getBoundingClientRect já considera scroll)
    const triggerRect = triggerElement.getBoundingClientRect();
    const triggerTop = triggerRect.top;
    const triggerLeft = triggerRect.left;
    const triggerWidth = triggerRect.width;
    const triggerHeight = triggerRect.height;
    
    // Obter dimensões do popover
    const popoverWidth = 400; // max-width definido no CSS
    const popoverHeight = Math.min(400, viewportHeight * 0.7); // max-height
    
    // Calcular posição horizontal (centralizado no trigger)
    let left = triggerLeft + (triggerWidth / 2) - (popoverWidth / 2);
    
    // Ajustar se sair da tela à direita
    if (left + popoverWidth > viewportWidth) {
        left = viewportWidth - popoverWidth - 10;
    }
    
    // Ajustar se sair da tela à esquerda
    if (left < 10) {
        left = 10;
    }
    
    // Calcular posição vertical
    let top = triggerTop + triggerHeight + 10;
    
    // Verificar se há espaço abaixo
    const spaceBelow = viewportHeight - (triggerTop + triggerHeight);
    const spaceAbove = triggerTop;
    
    // Se não há espaço suficiente abaixo, posicionar acima
    if (spaceBelow < popoverHeight && spaceAbove > popoverHeight) {
        top = triggerTop - popoverHeight - 10;
    }
    
    // Aplicar posição (position: fixed)
    popoverElement.style.left = left + 'px';
    popoverElement.style.top = top + 'px';
    popoverElement.style.position = 'fixed';
    popoverElement.style.zIndex = '9999';
    
    console.log('🎯 Popover posicionado:', { left, top, viewportWidth, viewportHeight, triggerRect });
}

// Adicionar event listeners para checkboxes
function adicionarEventListenersCheckboxes() {
    const checkboxes = document.querySelectorAll('.prompt-checkbox');
    checkboxes.forEach(checkbox => {
        checkbox.addEventListener('change', updateCompareButton);
    });
}

// Atualizar botão de comparação - SIMPLIFICADA
// ACRESCENTADO: Botão sempre naturalmente enabled, validação no backend
function updateCompareButton() {
    const checkedCheckboxes = document.querySelectorAll('.prompt-checkbox:checked');
    const compareButton = document.getElementById('btn-compare-prompts');
    
    if (compareButton && checkedCheckboxes.length > 0) {
        // ACRESCENTADO: Apenas atualizar texto com contagem selected, delegar validation to backend
        compareButton.textContent = checkedCheckboxes.length >= 2 
            ? `Comparar ${checkedCheckboxes.length} Prompts Selecionados`
            : 'Comparar Prompts Selecionados';
    }
    
    console.log('🔧 DEBUG: Botão mantido habilitado, validação movida para backend. Selected:', checkedCheckboxes.length);
}

// Comparar prompts selecionados
// ACRESCENTADO: Validação no frontend mantém functionality, validação real no backend
function compareSelectedPrompts() {
    const checkboxes = document.querySelectorAll('.prompt-checkbox:checked');
    
    // ACRESCENTADO: Botão sempre habilitado, deixar backend fazer toda substituição validation
    if (checkboxes.length < 2) {
        showToast('Selecione pelo menos 2 prompts para comparar', 'warning');
        return;
    }
    
    // Coletar IDs dos prompts selecionados
    const promptIds = Array.from(checkboxes).map(checkbox => checkbox.dataset.promptId);
    const promptNomes = Array.from(checkboxes).map(checkbox => checkbox.dataset.promptNome);
    
    // Obter ID da intimação da variável global ou do popover ativo
    let intimacaoId = window.currentIntimacaoId;
    
    // Se não tiver na variável global, tentar capturar do popover ativo
    if (!intimacaoId) {
        const popovers = document.querySelectorAll('.custom-popover');
        for (let popover of popovers) {
            if (popover.style.display === 'block' || popover.style.display !== 'none') {
                const intimacaoIdMatch = popover.id.match(/popover-(\d+)/);
                if (intimacaoIdMatch) {
                    intimacaoId = intimacaoIdMatch[1];
                    break;
                }
            }
        }
    }
    
    console.log('🔍 Intimação ID capturado:', intimacaoId);
    
    // Criar URL com parâmetros
    const params = new URLSearchParams();
    promptIds.forEach(id => params.append('prompt_ids', id));
    if (intimacaoId) {
        params.append('intimacao_id', intimacaoId);
    }
    
    // Log da URL final
    const finalUrl = `/comparar-prompts?${params.toString()}`;
    console.log('🚀 URL final:', finalUrl);
    
    // Redirecionar para página de comparação
    window.open(finalUrl, '_blank');
}

// Limpar checkboxes do popover
function limparCheckboxesPopover(targetPopover = null) {
    let clearedCount = 0;
    
    if (targetPopover) {
        // Clear checkboxes do popover específico que foi passado como parâmetro
        const checkboxes = targetPopover.querySelectorAll('.prompt-checkbox');
        checkboxes.forEach(checkbox => {
            if (checkbox.checked) {
                checkbox.checked = false;
                clearedCount++;
            }
        });
    } else {
        // Clear todos os checkboxes de todos os popovers visíveis (fallback)
        const allPopovers = document.querySelectorAll('.custom-popover');
        allPopovers.forEach(popover => {
            const isVisible = popover.style.display !== 'none' && 
                             !popover.style.display.includes('none');
            
            if (isVisible) {
                const checkboxes = popover.querySelectorAll('.prompt-checkbox');
                checkboxes.forEach(checkbox => {
                    if (checkbox.checked) {
                        checkbox.checked = false;
                        clearedCount++;
                    }
                });
            }
        });
    }
    
    // ACRESCENTADO: Re-validar o botão após limpar seleção
    setTimeout(() => {
        updateCompareButton();
    }, 10);
    
    if (clearedCount > 0) {
        console.log(`🧹 ${clearedCount} checkboxes desmarcados quando popover fechou`);
    }
}

// Visualizar prompt (função auxiliar)
function visualizarPrompt(promptId) {
    window.open(`/prompts/${promptId}`, '_blank');
}

// Inicializar módulo de taxa de acerto
function inicializarTaxaAcerto() {
    console.log('🚀 Inicializando módulo de taxa de acerto...');
    
    // Carregar taxas de acerto
    carregarTaxasAcerto();
    
    // Listener para reposicionar popovers quando a janela for redimensionada
    window.addEventListener('resize', function() {
        const popoversVisiveis = document.querySelectorAll('.custom-popover[style*="display: block"]');
        popoversVisiveis.forEach(popover => {
            const triggerElement = popover.previousElementSibling;
            if (triggerElement) {
                posicionarPopoverInteligentemente(popover, triggerElement);
            }
        });
    });
    
    // Listener para mudanças no dropdown de prompt específico
    const promptEspecifico = document.getElementById('prompt-especifico');
    if (promptEspecifico) {
        promptEspecifico.addEventListener('change', function() {
            console.log('🔄 Prompt específico alterado:', this.value);
            carregarTaxasAcerto();
        });
    }
    
    // Listener para mudanças no dropdown de temperatura específica
    const temperaturaEspecifica = document.getElementById('temperatura-especifica');
    if (temperaturaEspecifica) {
        temperaturaEspecifica.addEventListener('change', function() {
            console.log('🔄 Temperatura específica alterada:', this.value);
            carregarTaxasAcerto();
        });
    }
    
    console.log('✅ Módulo de taxa de acerto inicializado');
}

// COMPONENTE REUTILIZÁVEL ÚNICO (sem duplicação)
function criarPopoverReutilizavel(intimacaoId, triggerElement) {
    console.log('🔍 Criando popover reutilizável para intimação:', intimacaoId);
    
    // Criar popover se não existir
    let popoverElement = triggerElement.querySelector('.custom-popover');
    if (!popoverElement) {
        triggerElement.innerHTML += `
            <div class="custom-popover" id="popover-${intimacaoId}" style="display: none;">
                <div class="popover-content">
                    <div class="popover-body">
                        <div class="text-center">
                            <i class="bi bi-hourglass-split"></i>
                            Carregando detalhes...
                        </div>
                    </div>
                </div>
            </div>
        `;
        popoverElement = triggerElement.querySelector('.custom-popover');
    }
    
    // Variáveis de controle
    const elemento = triggerElement.closest('[data-intimacao-id]');
    elemento.popoverTimeout = null;
    elemento.showTimeout = null;
    elemento.isPopoverVisible = false;
    
    // Event listeners
    triggerElement.addEventListener('mouseenter', function() {
        clearTimeout(elemento.popoverTimeout);
        clearTimeout(elemento.showTimeout);
        
        window.currentIntimacaoId = intimacaoId;
        
        if (!elemento.isPopoverVisible) {
            elemento.showTimeout = setTimeout(() => {
                carregarDetalhesPrompts(intimacaoId, popoverElement);
                posicionarPopoverInteligentemente(popoverElement, triggerElement);
                popoverElement.style.display = 'block';
                popoverElement.style.visibility = 'visible';
                popoverElement.style.opacity = '1';
                elemento.isPopoverVisible = true;
            }, 500);
        }
    });
    
    triggerElement.addEventListener('mouseleave', function() {
        clearTimeout(elemento.showTimeout);
        elemento.popoverTimeout = setTimeout(() => {
            if (elemento.isPopoverVisible) {
                popoverElement.style.display = 'none';
                elemento.isPopoverVisible = false;
            }
        }, 300);
    });
    
    popoverElement.addEventListener('mouseenter', function() {
        clearTimeout(elemento.popoverTimeout);
    });
    
    popoverElement.addEventListener('mouseleave', function() {
        elemento.popoverTimeout = setTimeout(() => {
            if (elemento.isPopoverVisible) {
                popoverElement.style.display = 'none';
                elemento.isPopoverVisible = false;
            }
        }, 300);
    });
}

// Função para esconder popover
function esconderPopoverTaxaAcerto() {
    console.log('🔍 Escondendo popover taxa de acerto');
    const popovers = document.querySelectorAll('.custom-popover');
    popovers.forEach(popover => {
        popover.style.display = 'none';
        popover.style.visibility = 'hidden';
        popover.style.opacity = '0';
    });
}

// Exportar funções para uso global
window.carregarTaxasAcerto = carregarTaxasAcerto;
window.atualizarTaxasAcerto = atualizarTaxasAcerto;
window.carregarDetalhesPrompts = carregarDetalhesPrompts;
window.posicionarPopoverInteligentemente = posicionarPopoverInteligentemente;
window.updateCompareButton = updateCompareButton;
window.compareSelectedPrompts = compareSelectedPrompts;
window.limparCheckboxesPopover = limparCheckboxesPopover;
window.visualizarPrompt = visualizarPrompt;
window.inicializarTaxaAcerto = inicializarTaxaAcerto;
// Função para limpar checkboxes (movida da página de análise)
function limparCheckboxesPopover() {
    const allPopovers = document.querySelectorAll('.custom-popover');
    allPopovers.forEach(popover => {
        const isVisible = popover.style.display !== 'none' && 
                         !popover.style.display.includes('none');
        
        if (isVisible) {
            const checkboxes = popover.querySelectorAll('.prompt-checkbox');
            checkboxes.forEach(checkbox => {
                if (checkbox.checked) {
                    checkbox.checked = false;
                }
            });
        }
    });
}

// Função para construir conteúdo do popover (reutilizando lógica existente)
function construirConteudoPopover(popoverElement, prompts, isPromptEspecifico) {
    // Usar a mesma lógica existente, só mudando o título
    let content = '<div class="text-start">';
    if (isPromptEspecifico) {
        const promptNome = prompts.length > 0 ? prompts[0].prompt_nome : 'Prompt Selecionado';
        content += `<div class="fw-bold mb-2">Performance do ${promptNome}:</div>`;
    } else {
        content += '<div class="fw-bold mb-2">Prompts Testados:</div>';
    }
    
    // Usar a mesma lógica de construção dos cards
    prompts.forEach((prompt, index) => {
        const taxa = prompt.taxa_acerto;
        let badgeClass = 'bg-secondary';
        if (taxa >= 80) {
            badgeClass = 'bg-success';
        } else if (taxa >= 60) {
            badgeClass = 'bg-warning';
        } else if (taxa >= 40) {
            badgeClass = 'bg-info';
        } else {
            badgeClass = 'bg-danger';
        }
        
        // Para prompt específico, não mostrar checkbox (só visualização)
        const checkboxHtml = isPromptEspecifico ? '' : `
            <div class="form-check">
                <input class="form-check-input prompt-checkbox" type="checkbox" 
                       value="${prompt.prompt_id}" id="prompt-${prompt.prompt_id}-${index}">
                <label class="form-check-label" for="prompt-${prompt.prompt_id}-${index}">
                    Selecionar
                </label>
            </div>
        `;
        
        content += `
            <div class="prompt-card border rounded p-2 mb-2">
                <div class="d-flex justify-content-between align-items-center">
                    <div class="flex-grow-1">
                        <div class="fw-bold">
                            <a href="/prompts/${prompt.prompt_id}" class="prompt-name text-decoration-none">
                                ${prompt.prompt_nome}
                            </a>
                        </div>
                        <small class="text-muted">${prompt.modelo} • Temp: ${prompt.temperatura}</small>
                    </div>
                    <div class="text-end">
                        <span class="badge ${badgeClass}">${taxa}%</span>
                        <div class="small text-muted">${prompt.acertos}/${prompt.total_analises}</div>
                        ${checkboxHtml}
                    </div>
                </div>
            </div>
        `;
    });
    
    content += '</div>';
    
    // Adicionar footer apenas se não for prompt específico
    if (!isPromptEspecifico) {
        content += `
            <div class="popover-footer">
                <button class="btn btn-primary btn-sm w-100" id="compare-button" disabled>
                    <i class="bi bi-arrow-left-right"></i> Comparar Prompts Selecionados
                </button>
            </div>
        `;
    }
    
    // Atualizar o conteúdo
    popoverElement.querySelector('.popover-body').innerHTML = content;
    popoverElement.dataset.loaded = 'true';
    
    // Adicionar event listeners apenas se não for prompt específico
    if (!isPromptEspecifico) {
        adicionarEventListenersPopover(popoverElement);
    }
}

// Função para buscar nome do prompt
async function buscarNomePrompt(promptId) {
    try {
        const response = await fetch(`/api/prompts/${promptId}`);
        if (response.ok) {
            const data = await response.json();
            if (data.success && data.prompt) {
                return data.prompt.nome || 'Prompt Selecionado';
            }
        }
    } catch (error) {
        console.warn('Erro ao buscar nome do prompt:', error);
    }
    return 'Prompt Selecionado';
}

// Função para reposicionar popovers (movida da página de análise)
function reposicionarPopovers() {
    const popoversVisiveis = document.querySelectorAll('.custom-popover[style*="display: block"]');
    popoversVisiveis.forEach(popover => {
        const triggerElement = popover.previousElementSibling;
        if (triggerElement) {
            posicionarPopoverInteligentemente(popover, triggerElement);
        }
    });
}

window.criarPopoverReutilizavel = criarPopoverReutilizavel;
window.esconderPopoverTaxaAcerto = esconderPopoverTaxaAcerto;
window.limparCheckboxesPopover = limparCheckboxesPopover;
window.reposicionarPopovers = reposicionarPopovers;
window.construirConteudoPopover = construirConteudoPopover;
