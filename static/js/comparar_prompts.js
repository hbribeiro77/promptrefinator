// Configuração padrão do prompt de análise
const configPromptAnaliseDefault = {
    persona: 'Você é um especialista em análise de prompts de IA para classificação jurídica.\n\nAnalise as diferenças entre estas duas regras de negócio e forneça:\n\n1. Uma análise geral das principais diferenças\n2. Uma lista de 3-5 diferenças específicas\n3. Recomendações sobre qual abordagem pode ser mais eficaz',
    incluirContextoIntimacao: true,
    incluirInformacaoAdicional: true
};

// Configuração do prompt de análise (carregada do localStorage ou padrão)
let configPromptAnalise = { ...configPromptAnaliseDefault };

// Função para carregar configurações do localStorage
function carregarConfiguracoes() {
    try {
        const configSalva = localStorage.getItem('configPromptAnalise');
        if (configSalva) {
            const config = JSON.parse(configSalva);
            configPromptAnalise = { ...configPromptAnaliseDefault, ...config };
            console.log('Configurações carregadas do localStorage:', configPromptAnalise);
        } else {
            console.log('Nenhuma configuração salva encontrada, usando padrão');
        }
    } catch (e) {
        console.error('Erro ao carregar configurações do localStorage:', e);
        configPromptAnalise = { ...configPromptAnaliseDefault };
    }
}

// Função para salvar configurações no localStorage
function salvarConfiguracoes() {
    try {
        localStorage.setItem('configPromptAnalise', JSON.stringify(configPromptAnalise));
        console.log('Configurações salvas no localStorage:', configPromptAnalise);
    } catch (e) {
        console.error('Erro ao salvar configurações no localStorage:', e);
    }
}

// Carregar configurações ao inicializar
carregarConfiguracoes();

// Função para carregar dados da intimação
async function carregarDadosIntimacao() {
    console.log('Carregando dados da intimação...');
    
    // Primeiro, tentar pegar do elemento JSON
    const intimacaoDataElement = document.getElementById('intimacao-data');
    if (intimacaoDataElement) {
        try {
            window.intimacaoData = JSON.parse(intimacaoDataElement.textContent);
            console.log('Dados da intimação carregados do JSON:', window.intimacaoData);
            return true;
        } catch (e) {
            console.error(' Erro ao fazer parse do JSON:', e);
        }
    }
    
    // Se não conseguir do JSON, buscar no banco via API
    const intimacaoRow = document.querySelector('.intimacao-row');
    if (intimacaoRow) {
        const intimacaoId = intimacaoRow.getAttribute('data-intimacao-id');
        if (intimacaoId) {
            try {
                console.log(' Buscando intimação no banco via API:', intimacaoId);
                const response = await fetch(`/api/intimacao/${intimacaoId}`);
                const data = await response.json();
                
                if (data.success) {
                    window.intimacaoData = data.intimacao;
                    console.log(' Dados da intimação carregados do banco:', window.intimacaoData);
                    return true;
                } else {
                    console.error(' Erro na API:', data.error);
                }
            } catch (e) {
                console.error(' Erro ao buscar intimação:', e);
            }
        }
    }
    
    console.log(' Nenhum dado de intimação encontrado');
    return false;
}

// Função para configurar o prompt de análise
function configurarPromptAnalise() {
    const modalHtml = `
        <div class="modal fade" id="modalConfigPrompt" tabindex="-1" aria-labelledby="modalConfigPromptLabel" aria-hidden="true">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title" id="modalConfigPromptLabel">
                            <i class="bi bi-gear"></i>
                            Configurar Prompt de Análise
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        <form id="formConfigPrompt">
                            <div class="mb-3">
                                <label for="persona" class="form-label">
                                    <strong>Persona + Instruções de Análise:</strong>
                                    <small class="text-muted">Como a IA deve se comportar e o que deve fazer</small>
                                </label>
                                <textarea class="form-control" id="persona" rows="6" placeholder="Ex: Você é um especialista em análise de prompts de IA para classificação jurídica.&#10;&#10;Analise as diferenças entre estas duas regras de negócio e forneça:&#10;&#10;1. Uma análise geral das principais diferenças&#10;2. Uma lista de 3-5 diferenças específicas&#10;3. Recomendações sobre qual abordagem pode ser mais eficaz">${configPromptAnalise.persona}</textarea>
                            </div>
                            
                            <div class="mb-3">
                                <div class="form-check">
                                    <input class="form-check-input" type="checkbox" id="incluirContexto" ${configPromptAnalise.incluirContextoIntimacao ? 'checked' : ''}>
                                    <label class="form-check-label" for="incluirContexto">
                                        <strong>Incluir Contexto da Intimação</strong>
                                        <small class="text-muted d-block">Dados completos da intimação (processo, classe, órgão, etc.)</small>
                                    </label>
                                </div>
                            </div>
                            
                            <div class="mb-3">
                                <div class="form-check">
                                    <input class="form-check-input" type="checkbox" id="incluirGabarito" ${configPromptAnalise.incluirInformacaoAdicional ? 'checked' : ''}>
                                    <label class="form-check-label" for="incluirGabarito">
                                        <strong>Incluir Gabarito (Classificação Manual)</strong>
                                        <small class="text-muted d-block">A classificação correta para análise de performance</small>
                                    </label>
                                </div>
                            </div>
                            
                            <div class="alert alert-info">
                                <h6><i class="bi bi-info-circle"></i> Estrutura do Prompt:</h6>
                                <ol class="mb-0">
                                    <li><strong>Persona:</strong> Como a IA deve se comportar</li>
                                    <li><strong>Contexto da Intimação:</strong> Dados completos (se habilitado)</li>
                                    <li><strong>Gabarito:</strong> Classificação correta (se habilitado)</li>
                                    <li><strong>Instruções:</strong> O que fazer com as informações</li>
                                    <li><strong>Prompts a Comparar:</strong> As regras de negócio</li>
                                </ol>
                            </div>
                        </form>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-outline-secondary" onclick="resetarConfigPrompt()">
                            <i class="bi bi-arrow-clockwise"></i>
                            Resetar
                        </button>
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancelar</button>
                        <button type="button" class="btn btn-primary" onclick="salvarConfigPrompt()">
                            <i class="bi bi-check"></i>
                            Salvar Configuração
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Remover modal anterior se existir
    const existingModal = document.getElementById('modalConfigPrompt');
    if (existingModal) {
        existingModal.remove();
    }
    
    // Adicionar novo modal
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    // Mostrar modal
    const modal = new bootstrap.Modal(document.getElementById('modalConfigPrompt'));
    modal.show();
}

// Função para salvar configuração do prompt
function salvarConfigPrompt() {
    configPromptAnalise = {
        persona: document.getElementById('persona').value.trim(),
        incluirContextoIntimacao: document.getElementById('incluirContexto').checked,
        incluirInformacaoAdicional: document.getElementById('incluirGabarito').checked
    };
    
    // Salvar no localStorage
    salvarConfiguracoes();
    
    // Fechar modal
    const modal = bootstrap.Modal.getInstance(document.getElementById('modalConfigPrompt'));
    modal.hide();
    
    showToast('Configuração salva com sucesso!', 'success');
}

// Função para resetar configuração
function resetarConfigPrompt() {
    configPromptAnalise = { ...configPromptAnaliseDefault };
    
    // Salvar no localStorage
    salvarConfiguracoes();
    
    // Atualizar campos do formulário
    document.getElementById('persona').value = configPromptAnalise.persona;
    document.getElementById('incluirContexto').checked = configPromptAnalise.incluirContextoIntimacao;
    document.getElementById('incluirGabarito').checked = configPromptAnalise.incluirInformacaoAdicional;
    
    showToast('Configuração resetada para padrão!', 'info');
}

// Função para visualizar o prompt usado na análise
async function visualizarPromptAnalise() {
    const elements = document.querySelectorAll('[id^="regra-comparacao-"]');
    if (elements.length < 2) {
        showToast('É necessário ter pelo menos 2 prompts para comparar', 'warning');
        return;
    }

    // Obter nomes dos prompts
    const promptNames = document.querySelectorAll('.card-title a');
    const nome1 = promptNames[0] ? promptNames[0].textContent.trim() : 'Prompt 1';
    const nome2 = promptNames[1] ? promptNames[1].textContent.trim() : 'Prompt 2';
    
    const regra1 = elements[0].textContent;
    const regra2 = elements[1].textContent;
    
    // Construir prompt baseado na configuração
    let promptAnalise = configPromptAnalise.persona + '\n\n';
    console.log(' Configuração atual:', configPromptAnalise);
    
    // Adicionar contexto da intimação se habilitado
    if (configPromptAnalise.incluirContextoIntimacao) {
        // SEMPRE carregar dados da intimação
        await carregarDadosIntimacao();
        
        // Usar dados carregados
        const intimacaoData = window.intimacaoData;
        console.log(' Dados da intimação no Ver Prompt:', intimacaoData);
        
        if (intimacaoData && intimacaoData.id) {
            promptAnalise += `CONTEXTO DA INTIMAÇÃO:
- ID: ${intimacaoData.id}
- Processo: ${intimacaoData.processo || 'N/A'}
- Classe: ${intimacaoData.classe || 'N/A'}
- Órgão Julgador: ${intimacaoData.orgao_julgador || 'N/A'}
- Intimado: ${intimacaoData.intimado || 'N/A'}
- Defensor: ${intimacaoData.defensor || 'N/A'}
- Data: ${intimacaoData.data_criacao || 'N/A'}

CONTEÚDO DA INTIMAÇÃO:
${intimacaoData.contexto || 'N/A'}

`;
        } else {
            promptAnalise += `CONTEXTO DA INTIMAÇÃO:
- ID: N/A
- Processo: N/A
- Classe: N/A
- Órgão Julgador: N/A
- Intimado: N/A
- Defensor: N/A
- Data: N/A

CONTEÚDO DA INTIMAÇÃO:
N/A

`;
        }
    }
    
    // Adicionar informação adicional (gabarito) se habilitado
    if (configPromptAnalise.incluirInformacaoAdicional) {
        // Usar dados já carregados no window.intimacaoData
        const intimacaoData = window.intimacaoData;
        console.log(' Dados da intimação no Ver Prompt (Gabarito):', intimacaoData);
        
        if (intimacaoData && intimacaoData.id) {
            promptAnalise += `CLASSIFICAÇÃO MANUAL (GABARITO):
${intimacaoData.classificacao_manual || 'N/A'}

INFORMAÇÕES ADICIONAIS:
${intimacaoData.informacao_adicional || 'N/A'}

A classificação correta para esta intimação é: "${intimacaoData.classificacao_manual || 'N/A'}".

Analise por que um prompt teve melhor performance que o outro considerando:
1. A precisão na classificação da intimação
2. A adequação das regras de negócio ao contexto específico
3. A capacidade de capturar nuances importantes do caso

`;
        } else {
            promptAnalise += `CLASSIFICAÇÃO MANUAL (GABARITO):
N/A

INFORMAÇÕES ADICIONAIS:
N/A

A classificação correta para esta intimação é: "N/A".

Analise por que um prompt teve melhor performance que o outro considerando:
1. A precisão na classificação da intimação
2. A adequação das regras de negócio ao contexto específico
3. A capacidade de capturar nuances importantes do caso

`;
        }
    }
    
    // As instruções já estão incluídas no persona
    
    // Adicionar prompts a comparar
    promptAnalise += `${nome1.toUpperCase()}:
${regra1}

${nome2.toUpperCase()}:
${regra2}

Responda em formato JSON com as seguintes chaves:
- "analise": análise geral (2-3 frases)
- "diferencas": array com 3-5 diferenças específicas
- "recomendacoes": array com 3-5 recomendações

Seja objetivo, técnico e focado em eficácia para classificação jurídica.`;
    
    // Criar modal para mostrar o prompt
    const modalHtml = `
        <div class="modal fade" id="modalPromptAnalise" tabindex="-1" aria-labelledby="modalPromptAnaliseLabel" aria-hidden="true">
            <div class="modal-dialog modal-xl">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title" id="modalPromptAnaliseLabel">
                            <i class="bi bi-eye"></i>
                            Prompt Usado na Análise de Diferenças
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        <div class="mb-3">
                            <label class="form-label"><strong>Prompt Enviado para a IA:</strong></label>
                            <div class="bg-light p-3 rounded" style="max-height: 500px; overflow-y: auto;">
                                <pre style="white-space: pre-wrap; font-size: 0.9em; margin: 0;">${promptAnalise}</pre>
                            </div>
                        </div>
                        <div class="row">
                            <div class="col-md-6">
                                <label class="form-label"><strong>Estatísticas:</strong></label>
                                <ul class="list-group list-group-flush">
                                    <li class="list-group-item d-flex justify-content-between">
                                        <span>Total de caracteres:</span>
                                        <span class="badge bg-primary">${promptAnalise.length}</span>
                                    </li>
                                    <li class="list-group-item d-flex justify-content-between">
                                        <span>Total de palavras:</span>
                                        <span class="badge bg-primary">${promptAnalise.split(' ').length}</span>
                                    </li>
                                    <li class="list-group-item d-flex justify-content-between">
                                        <span>Total de linhas:</span>
                                        <span class="badge bg-primary">${promptAnalise.split('\n').length}</span>
                                    </li>
                                </ul>
                            </div>
                            <div class="col-md-6">
                                <label class="form-label"><strong>Regras de Negócio:</strong></label>
                                <ul class="list-group list-group-flush">
                                    <li class="list-group-item d-flex justify-content-between">
                                        <span>${nome1} (caracteres):</span>
                                        <span class="badge bg-info">${regra1.length}</span>
                                    </li>
                                    <li class="list-group-item d-flex justify-content-between">
                                        <span>${nome2} (caracteres):</span>
                                        <span class="badge bg-info">${regra2.length}</span>
                                    </li>
                                    <li class="list-group-item d-flex justify-content-between">
                                        <span>Diferença de tamanho:</span>
                                        <span class="badge ${Math.abs(regra1.length - regra2.length) > 100 ? 'bg-warning' : 'bg-success'}">${Math.abs(regra1.length - regra2.length)}</span>
                                    </li>
                                </ul>
                            </div>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-outline-secondary" onclick="copiarPromptAnalise()">
                            <i class="bi bi-clipboard"></i>
                            Copiar Prompt
                        </button>
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Fechar</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Remover modal anterior se existir
    const existingModal = document.getElementById('modalPromptAnalise');
    if (existingModal) {
        existingModal.remove();
    }
    
    // Adicionar novo modal
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    // Mostrar modal
    const modal = new bootstrap.Modal(document.getElementById('modalPromptAnalise'));
    modal.show();
}

// Função para copiar o prompt de análise
async function copiarPromptAnalise() {
    const elements = document.querySelectorAll('[id^="regra-comparacao-"]');
    if (elements.length < 2) return;
    
    // Obter nomes dos prompts
    const promptNames = document.querySelectorAll('.card-title a');
    const nome1 = promptNames[0] ? promptNames[0].textContent.trim() : 'Prompt 1';
    const nome2 = promptNames[1] ? promptNames[1].textContent.trim() : 'Prompt 2';
    
    const regra1 = elements[0].textContent;
    const regra2 = elements[1].textContent;
    
    // Construir prompt baseado na configuração (mesmo código da função visualizar)
    let promptAnalise = configPromptAnalise.persona + '\n\n';
    
    // Adicionar contexto da intimação se habilitado
    if (configPromptAnalise.incluirContextoIntimacao) {
        // SEMPRE carregar dados da intimação
        await carregarDadosIntimacao();
        
        const intimacaoData = window.intimacaoData || {};
        promptAnalise += `CONTEXTO DA INTIMAÇÃO:
- ID: ${intimacaoData.id || 'N/A'}
- Processo: ${intimacaoData.processo || 'N/A'}
- Classe: ${intimacaoData.classe || 'N/A'}
- Órgão Julgador: ${intimacaoData.orgao_julgador || 'N/A'}
- Intimado: ${intimacaoData.intimado || 'N/A'}
- Defensor: ${intimacaoData.defensor || 'N/A'}
- Data: ${intimacaoData.data_criacao || 'N/A'}

CONTEÚDO DA INTIMAÇÃO:
${intimacaoData.contexto || 'N/A'}

`;
    }
    
    // Adicionar informação adicional (gabarito) se habilitado
    if (configPromptAnalise.incluirInformacaoAdicional) {
        // Usar dados já carregados no window.intimacaoData
        const intimacaoData = window.intimacaoData;
        console.log(' Dados da intimação no Ver Prompt (Gabarito):', intimacaoData);
        
        if (intimacaoData && intimacaoData.id) {
            promptAnalise += `CLASSIFICAÇÃO MANUAL (GABARITO):
${intimacaoData.classificacao_manual || 'N/A'}

INFORMAÇÕES ADICIONAIS:
${intimacaoData.informacao_adicional || 'N/A'}

A classificação correta para esta intimação é: "${intimacaoData.classificacao_manual || 'N/A'}".

Analise por que um prompt teve melhor performance que o outro considerando:
1. A precisão na classificação da intimação
2. A adequação das regras de negócio ao contexto específico
3. A capacidade de capturar nuances importantes do caso

`;
        } else {
            promptAnalise += `CLASSIFICAÇÃO MANUAL (GABARITO):
N/A

INFORMAÇÕES ADICIONAIS:
N/A

A classificação correta para esta intimação é: "N/A".

Analise por que um prompt teve melhor performance que o outro considerando:
1. A precisão na classificação da intimação
2. A adequação das regras de negócio ao contexto específico
3. A capacidade de capturar nuances importantes do caso

`;
        }
    }
    
    // As instruções já estão incluídas no persona
    
    // Adicionar prompts a comparar
    promptAnalise += `${nome1.toUpperCase()}:
${regra1}

${nome2.toUpperCase()}:
${regra2}

Responda em formato JSON com as seguintes chaves:
- "analise": análise geral (2-3 frases)
- "diferencas": array com 3-5 diferenças específicas
- "recomendacoes": array com 3-5 recomendações

Seja objetivo, técnico e focado em eficácia para classificação jurídica.`;
    
    navigator.clipboard.writeText(promptAnalise).then(() => {
        showToast('Prompt copiado para a área de transferência!', 'success');
    }).catch(() => {
        showToast('Erro ao copiar prompt', 'error');
    });
}

// Função para analisar diferenças com IA
function analisarDiferencasComIA() {
    const elements = document.querySelectorAll('[id^="regra-comparacao-"]');
    if (elements.length < 2) {
        showToast('É necessário ter pelo menos 2 prompts para comparar', 'warning');
        return;
    }
    
    // Obter nomes dos prompts
    const promptNames = document.querySelectorAll('.card-title a');
    const nome1 = promptNames[0] ? promptNames[0].textContent.trim() : 'Prompt 1';
    const nome2 = promptNames[1] ? promptNames[1].textContent.trim() : 'Prompt 2';
    
    const regra1 = elements[0].textContent;
    const regra2 = elements[1].textContent;
    
    // Mostrar seção de análise
    const analiseSection = document.getElementById('analise-ia-section');
    analiseSection.style.display = 'block';
    
    // Scroll para a seção
    analiseSection.scrollIntoView({ behavior: 'smooth' });
    
    // Fazer requisição para análise com IA
    fetch('/api/analisar-diferencas-prompts', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            regra_negocio_1: regra1,
            regra_negocio_2: regra2,
            nome_prompt_1: nome1,
            nome_prompt_2: nome2,
            config_personalizada: configPromptAnalise,
            intimacao_id: window.intimacaoData ? window.intimacaoData.id : null
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            document.getElementById('analise-ia-content').innerHTML = `
                <div class="alert alert-info">
                    <h6><i class="bi bi-lightbulb"></i> Análise da IA:</h6>
                    <p class="mb-0">${data.analise}</p>
                </div>
                <div class="row mt-3">
                    <div class="col-md-6">
                        <h6 class="text-primary">Principais Diferenças:</h6>
                        <ul class="list-group list-group-flush">
                            ${data.diferencas.map(diff => `<li class="list-group-item">${diff}</li>`).join('')}
                        </ul>
                    </div>
                    <div class="col-md-6">
                        <h6 class="text-success">Recomendações:</h6>
                        <ul class="list-group list-group-flush">
                            ${data.recomendacoes.map(rec => `<li class="list-group-item">${rec}</li>`).join('')}
                        </ul>
                    </div>
                </div>
            `;
        } else {
            document.getElementById('analise-ia-content').innerHTML = `
                <div class="alert alert-danger">
                    <h6><i class="bi bi-exclamation-triangle"></i> Erro na análise:</h6>
                    <p class="mb-0">${data.message}</p>
                </div>
            `;
        }
    })
    .catch(error => {
        console.error('Erro na análise:', error);
        document.getElementById('analise-ia-content').innerHTML = `
            <div class="alert alert-danger">
                <h6><i class="bi bi-exclamation-triangle"></i> Erro na análise:</h6>
                <p class="mb-0">Erro ao conectar com a IA. Tente novamente.</p>
            </div>
        `;
    });
}
