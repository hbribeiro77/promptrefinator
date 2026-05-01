/**
 * Wizard de Análise Individual de Prompts
 * 
 * Este arquivo contém toda a lógica do wizard de análise de prompts individuais,
 * incluindo configuração, análise com IA, testes de triagem e testes combinados.
 * 
 * Arquivo original estava em: templates/visualizar_intimacao.html
 * Extraído para facilitar manutenção e organização do código.
 */

// ===== CONFIGURAÇÕES PADRÃO =====

function escapeHtmlWizard(text) {
    if (text === null || text === undefined) {
        return '';
    }
    const div = document.createElement('div');
    div.textContent = String(text);
    return div.innerHTML;
}

function escapeAttrWizard(text) {
    if (text === null || text === undefined) {
        return '';
    }
    return String(text)
        .replace(/&/g, '&amp;')
        .replace(/"/g, '&quot;');
}

/**
 * Modelo exibido no tooltip (select do cabeçalho ou padrão do resumo).
 */
function modeloDiagnosticoWizardSelecionadoOuPadrao() {
    const sel = document.getElementById('wizardModeloDiagnosticoSelect');
    if (sel && sel.value) {
        return sel.value;
    }
    const r = typeof window !== 'undefined' ? window.resumoIaDiagnosticoWizard : null;
    if (r && r.ok && r.modelo != null) {
        return String(r.modelo);
    }
    return '';
}

/**
 * Texto do tooltip com os detalhes da IA do diagnóstico (antes exibidos em alerta na etapa 1).
 */
function textoTooltipModeloDiagnosticoWizard() {
    const r = typeof window !== 'undefined' ? window.resumoIaDiagnosticoWizard : null;
    if (!r) {
        return 'Resumo do modelo não disponível. Recarregue a página.';
    }
    if (!r.ok) {
        return r.erro || 'Configuração incompleta em Configurações.';
    }
    const t = typeof r.temperatura === 'number' ? r.temperatura : parseFloat(String(r.temperatura), 10);
    const tempStr = Number.isFinite(t) ? String(t) : String(r.temperatura ?? '');
    const prov = r.provedor_label || r.provedor || '';
    const mod = modeloDiagnosticoWizardSelecionadoOuPadrao();
    const mtCfg = r.max_tokens_config;
    const mtEf = r.max_tokens_efetivo_diagnostico_wizard;
    return (
        `Provedor: ${prov}. `
        + `Modelo: ${mod}. `
        + `Temperatura: ${tempStr}. `
        + `Max. tokens (configuração): ${mtCfg}. `
        + `Na chamada com este assistente, o limite de saída é pelo menos ${mtEf} tokens (mesma regra do servidor).`
    );
}

/**
 * Fragmento HTML do cabeçalho: select de modelo (mesmo provedor) + ícone (i) para tooltip.
 * Depende de `window.resumoIaDiagnosticoWizard` (servidor / visualizar_intimacao).
 */
function htmlCabecalhoModeloDiagnosticoWizard() {
    const r = typeof window !== 'undefined' ? window.resumoIaDiagnosticoWizard : null;
    const iconAttrs =
        'id="wizardDiagnosticoModeloInfoBtn" class="bi bi-info-circle text-primary ms-1" '
        + 'role="button" tabindex="0" aria-label="Detalhes do modelo de IA usado no diagnóstico" '
        + 'style="cursor: help; font-size: 1rem;"';
    if (!r) {
        return `
                        <span class="d-inline-flex align-items-center gap-1 ms-2 flex-wrap">
                            <span class="badge bg-light text-dark border font-monospace text-truncate" style="max-width: 14rem;">—</span>
                            <i ${iconAttrs}></i>
                        </span>`;
    }
    if (!r.ok) {
        return `
                        <span class="d-inline-flex align-items-center gap-1 ms-2 flex-wrap">
                            <span class="badge bg-warning text-dark">IA indisponível</span>
                            <i ${iconAttrs}></i>
                        </span>`;
    }
    const lista = r.modelos_disponiveis_diagnostico;
    if (Array.isArray(lista) && lista.length > 0) {
        const padrao = String(r.modelo || '');
        const optHtml = lista.map((m) => {
            const ms = String(m);
            const sel = ms === padrao ? ' selected' : '';
            return `<option value="${escapeAttrWizard(ms)}"${sel}>${escapeHtmlWizard(ms)}</option>`;
        }).join('');
        return `
                        <span class="d-inline-flex align-items-center gap-1 ms-2 flex-wrap">
                            <select id="wizardModeloDiagnosticoSelect" class="form-select form-select-sm font-monospace py-0"
                                style="max-width: 16rem; font-size: 0.8rem;" aria-label="Modelo para o diagnóstico (mesmo provedor)">
                                ${optHtml}
                            </select>
                            <i ${iconAttrs}></i>
                        </span>`;
    }
    const mod = escapeHtmlWizard(r.modelo);
    return `
                        <span class="d-inline-flex align-items-center gap-1 ms-2 flex-wrap">
                            <span class="badge bg-secondary font-monospace text-truncate" style="max-width: 14rem;">${mod}</span>
                            <i ${iconAttrs}></i>
                        </span>`;
}

/**
 * Inicializa tooltip do ícone (i) no cabeçalho; use após o modal estar visível.
 */
function inicializarTooltipCabecalhoModeloDiagnosticoWizard() {
    const el = document.getElementById('wizardDiagnosticoModeloInfoBtn');
    if (!el || typeof bootstrap === 'undefined' || !bootstrap.Tooltip) {
        return;
    }
    const existing = bootstrap.Tooltip.getInstance(el);
    if (existing) {
        existing.dispose();
    }
    const title = textoTooltipModeloDiagnosticoWizard();
    bootstrap.Tooltip.getOrCreateInstance(el, {
        title,
        placement: 'bottom',
        container: 'body',
        trigger: 'hover focus',
    });
}

/**
 * Ao mudar o modelo no cabeçalho, atualiza o texto do tooltip.
 */
function wizardVincularSelectModeloDiagnosticoTooltip() {
    const sel = document.getElementById('wizardModeloDiagnosticoSelect');
    if (!sel || sel.dataset.wizardModeloTooltipBound === '1') {
        return;
    }
    sel.dataset.wizardModeloTooltipBound = '1';
    sel.addEventListener('change', () => {
        inicializarTooltipCabecalhoModeloDiagnosticoWizard();
    });
}

/**
 * Inclui `modeloDiagnosticoOverride` na config enviada à API quando há select no cabeçalho.
 */
function anexarModeloDiagnosticoOverrideSelecionado(configObj) {
    const c = { ...configObj };
    const sel = document.getElementById('wizardModeloDiagnosticoSelect');
    if (sel && sel.value) {
        c.modeloDiagnosticoOverride = sel.value;
    }
    return c;
}

const configPromptIndividualDefault = {
    persona: 'Você é um especialista na Defensoria Pública em análise de prompts de IA para classificação jurídica de intimações recebidas pelo poder judiciário.\n\nTAREFA: Analise a eficácia deste prompt específico para classificar a intimação fornecida.\n\nCRÍTICO: Use EXATAMENTE as informações fornecidas. NÃO invente, NÃO altere, NÃO ignore os dados fornecidos.',
    incluirContextoIntimacao: true,
    incluirInformacaoAdicional: true,
    incluirIdentificacaoPromptDesempenho: true,
    incluirConteudoPromptCadastrado: false,
    incluirTriagemFeitaPelaIa: true,
    instrucoesResposta: 'IMPORTANTE: Use APENAS as informações fornecidas no prompt. NUNCA invente ou altere o gabarito fornecido.\n\nResponda em formato JSON com as seguintes chaves:\n- "analise": análise geral (2-3 frases) sobre a eficácia do prompt\n- "pontos_fortes": array com 3-5 pontos fortes do prompt\n- "pontos_fracos": array com 3-5 pontos fracos do prompt\n- "recomendacoes": array com 3-5 recomendações para melhorar o prompt\n\nSeja objetivo, técnico e focado em eficácia para classificação jurídica.'
};

// Configuração do prompt de análise INDIVIDUAL (carregada do localStorage ou padrão)
let configPromptIndividual = { ...configPromptIndividualDefault };

// Variáveis para teste de triagem
let resultadoAnaliseAtual = null;
let promptIdAtual = null;
let regrasTestadasAtual = null;
let promptBaseAtual = null;

// ===== FUNÇÕES DE CONFIGURAÇÃO =====

/**
 * Carrega configurações do localStorage (ANÁLISE INDIVIDUAL)
 */
function carregarConfiguracoesAnalise() {
    try {
        const configSalva = localStorage.getItem('configPromptIndividual');
        if (configSalva) {
            const config = JSON.parse(configSalva);
            configPromptIndividual = { ...configPromptIndividualDefault, ...config };
            console.log('Configurações de análise INDIVIDUAL carregadas do localStorage:', configPromptIndividual);
        } else {
            console.log('Nenhuma configuração de análise INDIVIDUAL salva encontrada, usando padrão');
        }
    } catch (e) {
        console.error('Erro ao carregar configurações de análise INDIVIDUAL do localStorage:', e);
        configPromptIndividual = { ...configPromptIndividualDefault };
    }
}

/**
 * Salva configuração personalizada
 */
function salvarConfigAnaliseIndividual() {
    // Capturar valores atuais dos campos
    const configAtual = {
        persona: document.getElementById('personaIndividual').value.trim(),
        instrucoesResposta: document.getElementById('instrucoesRespostaIndividual').value.trim(),
        incluirContextoIntimacao: document.getElementById('incluirContextoIndividual').checked,
        incluirInformacaoAdicional: document.getElementById('incluirGabaritoIndividual').checked,
        incluirIdentificacaoPromptDesempenho: document.getElementById('incluirIdentificacaoPromptDesempenhoIndividual').checked,
        incluirConteudoPromptCadastrado: document.getElementById('incluirConteudoPromptCadastradoIndividual').checked,
        incluirTriagemFeitaPelaIa: document.getElementById('incluirTriagemFeitaPelaIaIndividual').checked
    };
    
    // Atualizar configuração atual
    configPromptIndividual = { ...configPromptIndividualDefault, ...configAtual };
    
    // Salvar no localStorage com CHAVE SEPARADA da comparação
    localStorage.setItem('configPromptIndividual', JSON.stringify(configPromptIndividual));
    
    if (typeof showToast !== 'undefined') {
        showToast('Configuração INDIVIDUAL salva com sucesso!', 'success');
    }
}

/**
 * Reseta configuração para padrão
 */
function resetarConfigAnaliseIndividual() {
    configPromptIndividual = { ...configPromptIndividualDefault };
    
    // Salvar no localStorage (CHAVE SEPARADA)
    localStorage.setItem('configPromptIndividual', JSON.stringify(configPromptIndividual));
    
    // Atualizar campos do formulário
    const personaField = document.getElementById('personaIndividual');
    const instrucoesField = document.getElementById('instrucoesRespostaIndividual');
    const incluirContextoField = document.getElementById('incluirContextoIndividual');
    const incluirGabaritoField = document.getElementById('incluirGabaritoIndividual');
    const incluirIdentificacaoField = document.getElementById('incluirIdentificacaoPromptDesempenhoIndividual');
    const incluirConteudoCadastroField = document.getElementById('incluirConteudoPromptCadastradoIndividual');
    const incluirTriagemField = document.getElementById('incluirTriagemFeitaPelaIaIndividual');
    
    if (personaField) personaField.value = configPromptIndividual.persona;
    if (instrucoesField) instrucoesField.value = configPromptIndividual.instrucoesResposta;
    if (incluirContextoField) incluirContextoField.checked = configPromptIndividual.incluirContextoIntimacao;
    if (incluirGabaritoField) incluirGabaritoField.checked = configPromptIndividual.incluirInformacaoAdicional;
    if (incluirIdentificacaoField) incluirIdentificacaoField.checked = configPromptIndividual.incluirIdentificacaoPromptDesempenho;
    if (incluirConteudoCadastroField) incluirConteudoCadastroField.checked = configPromptIndividual.incluirConteudoPromptCadastrado;
    if (incluirTriagemField) incluirTriagemField.checked = configPromptIndividual.incluirTriagemFeitaPelaIa;
    
    if (typeof showToast !== 'undefined') {
        showToast('Configuração INDIVIDUAL resetada para padrão!', 'info');
    }
}

// ===== FUNÇÃO PRINCIPAL: ANALISAR PROMPT INDIVIDUAL =====

/**
 * Função principal para iniciar análise de prompt individual
 * Cria e exibe o modal do wizard
 */
async function analisarPromptIndividual(promptId, promptNome, acertos, total) {
    console.log('Analisando prompt individual:', { promptId, promptNome, acertos, total });
    
    // Carregar configurações
    carregarConfiguracoesAnalise();
    
    // Calcular taxa de acerto usando os dados da linha
    let taxaAcerto = 'N/A';
    if (total > 0) {
        taxaAcerto = ((acertos / total) * 100).toFixed(1);
    }
    
    console.log('✅ Taxa de acerto calculada:', {
        taxaAcerto,
        acertos,
        total,
        promptId,
        promptNome
    });
    
    // Buscar dados da análise original para este prompt via API
    let dadosAnaliseOriginal = null;
    try {
        if (window.intimacaoData && window.intimacaoData.id) {
            const response = await fetch(`/api/intimacoes/${window.intimacaoData.id}/analise-dados/${promptId}`);
            const data = await response.json();
            
            if (data.success && data.dados_analise) {
                dadosAnaliseOriginal = {
                    resultado_ia: data.dados_analise.resultado_ia || 'N/A',
                    resposta_completa: data.dados_analise.resposta_completa || 'N/A',
                    informacao_adicional: data.dados_analise.informacao_adicional || 'N/A',
                    sugestao: data.dados_analise.sugestao || 'N/A'
                };
                console.log('📋 Dados da análise original encontrados via API:', dadosAnaliseOriginal);
            } else {
                console.log('⚠️ Dados da análise original não encontrados via API');
            }
        }
    } catch (error) {
        console.error('❌ Erro ao buscar dados da análise original:', error);
    }
    
    // Armazenar dados para o wizard
    window.wizardData = {
        promptId: promptId,
        promptNome: promptNome,
        acertos: acertos,
        total: total,
        taxaAcerto: taxaAcerto,
        dadosAnaliseOriginal: dadosAnaliseOriginal,
        etapaAtual: 1
    };
    
    // Criar wizard modal
    const modalHtml = criarModalWizard(promptNome, taxaAcerto, acertos, total);
    
    // Remover modal anterior se existir
    const existingModal = document.getElementById('modalWizardAnalise');
    if (existingModal) {
        existingModal.remove();
    }
    
    // Adicionar modal ao DOM
    document.body.insertAdjacentHTML('beforeend', modalHtml);

    const modalEl = document.getElementById('modalWizardAnalise');
    modalEl.addEventListener(
        'shown.bs.modal',
        function wizardCabecalhoDiagnosticoTooltipOnShown() {
            inicializarTooltipCabecalhoModeloDiagnosticoWizard();
            wizardVincularSelectModeloDiagnosticoTooltip();
        },
        { once: true },
    );

    // Mostrar modal
    const modal = new bootstrap.Modal(modalEl);
    modal.show();
}

/**
 * Cria o HTML do modal do wizard
 */
function criarModalWizard(promptNome, taxaAcerto, acertos, total) {
    return `
        <div class="modal fade" id="modalWizardAnalise" tabindex="-1" aria-labelledby="modalWizardAnaliseLabel" aria-hidden="true">
            <div class="modal-dialog modal-xl">
                <div class="modal-content">
                    <div class="modal-header flex-wrap align-items-center gap-2 py-2">
                        <div class="d-flex flex-wrap align-items-center gap-2 me-auto pe-2 min-w-0 flex-grow-1">
                            <h5 class="modal-title mb-0 text-truncate min-w-0" id="modalWizardAnaliseLabel" style="max-width: min(100%, 28rem);">
                                <i class="bi bi-magic"></i>
                                Wizard de Análise: ${escapeHtmlWizard(promptNome)}
                            </h5>
                            <span class="badge bg-info text-nowrap">Taxa: ${escapeHtmlWizard(String(taxaAcerto))}% (${escapeHtmlWizard(String(acertos))}/${escapeHtmlWizard(String(total))})</span>
                            ${htmlCabecalhoModeloDiagnosticoWizard()}
                        </div>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body wizard-body">
                        <!-- Indicador de Progresso -->
                        <div class="progress mb-4" style="height: 8px;">
                            <div class="progress-bar" id="wizardProgress" role="progressbar" style="width: 20%"></div>
                        </div>
                        
                        <!-- Navegação das Etapas -->
                        <div class="d-flex justify-content-between mb-4">
                            <div class="d-flex align-items-center" style="cursor: pointer;" onclick="navegarParaEtapa(1)">
                                <span class="badge bg-primary me-2" id="step1">1</span>
                                <span id="step1Text">Configuração</span>
                            </div>
                            <div class="d-flex align-items-center" style="cursor: pointer;" onclick="navegarParaEtapa(2)">
                                <span class="badge bg-secondary me-2" id="step2">2</span>
                                <span id="step2Text">Análise IA</span>
                            </div>
                            <div class="d-flex align-items-center" style="cursor: pointer;" onclick="navegarParaEtapa(3)">
                                <span class="badge bg-secondary me-2" id="step3">3</span>
                                <span id="step3Text">Teste Triagem</span>
                            </div>
                            <div class="d-flex align-items-center" style="cursor: pointer;" onclick="navegarParaEtapa(4)">
                                <span class="badge bg-secondary me-2" id="step4">4</span>
                                <span id="step4Text">Resultado</span>
                            </div>
                            <div class="d-flex align-items-center" style="cursor: pointer;" onclick="navegarParaEtapa(5)">
                                <span class="badge bg-secondary me-2" id="step5">5</span>
                                <span id="step5Text">Teste Combinado</span>
                            </div>
                        </div>
                        
                        <!-- Conteúdo das Etapas -->
                        <div id="wizardContent">
                            <!-- ETAPA 1: CONFIGURAÇÃO -->
                            <div id="etapa1" class="wizard-step">
                                <h6 class="mb-3"><i class="bi bi-gear"></i> Configuração da Análise</h6>
                                <form id="formAnaliseIndividual">
                                    <div class="mb-3">
                                        <label for="personaIndividual" class="form-label">
                                            <strong>Persona + Instruções de Análise:</strong>
                                        </label>
                                        <textarea class="form-control" id="personaIndividual" rows="6" 
                                            placeholder="Digite a persona e instruções para análise do prompt...">${configPromptIndividual.persona}</textarea>
                                    </div>
                                    
                                    <div class="row">
                                        <div class="col-md-6">
                                            <div class="form-check">
                                                <input class="form-check-input" type="checkbox" id="incluirContextoIndividual" 
                                                    ${configPromptIndividual.incluirContextoIntimacao ? 'checked' : ''}>
                                                <label class="form-check-label" for="incluirContextoIndividual">
                                                    Incluir contexto da intimação
                                                </label>
                                            </div>
                                        </div>
                                        <div class="col-md-6">
                                            <div class="form-check">
                                                <input class="form-check-input" type="checkbox" id="incluirGabaritoIndividual" 
                                                    ${configPromptIndividual.incluirInformacaoAdicional ? 'checked' : ''}>
                                                <label class="form-check-label" for="incluirGabaritoIndividual">
                                                    Incluir gabarito (classificação manual)
                                                </label>
                                            </div>
                                        </div>
                                    </div>
                                    <div class="row mt-1">
                                        <div class="col-md-6">
                                            <div class="form-check">
                                                <input class="form-check-input" type="checkbox" id="incluirIdentificacaoPromptDesempenhoIndividual" 
                                                    ${configPromptIndividual.incluirIdentificacaoPromptDesempenho ? 'checked' : ''}>
                                                <label class="form-check-label" for="incluirIdentificacaoPromptDesempenhoIndividual">
                                                    Incluir identificação do prompt e desempenho
                                                </label>
                                            </div>
                                        </div>
                                        <div class="col-md-6">
                                            <div class="form-check">
                                                <input class="form-check-input" type="checkbox" id="incluirTriagemFeitaPelaIaIndividual" 
                                                    ${configPromptIndividual.incluirTriagemFeitaPelaIa ? 'checked' : ''}>
                                                <label class="form-check-label" for="incluirTriagemFeitaPelaIaIndividual">
                                                    Incluir triagem feita pela IA
                                                </label>
                                            </div>
                                        </div>
                                    </div>
                                    <div class="row mt-1">
                                        <div class="col-12">
                                            <div class="form-check">
                                                <input class="form-check-input" type="checkbox" id="incluirConteudoPromptCadastradoIndividual"
                                                    ${configPromptIndividual.incluirConteudoPromptCadastrado ? 'checked' : ''}>
                                                <label class="form-check-label" for="incluirConteudoPromptCadastradoIndividual">
                                                    Incluir texto do campo &quot;Conteúdo do prompt&quot; do cadastro (o que vai para a triagem)
                                                </label>
                                            </div>
                                        </div>
                                    </div>
                                    
                                    <div class="mb-3 d-none" aria-hidden="true">
                                        <label for="instrucoesRespostaIndividual" class="form-label">
                                            <strong>Instruções de Resposta:</strong>
                                        </label>
                                        <textarea class="form-control" id="instrucoesRespostaIndividual" rows="4" 
                                            placeholder="Instruções específicas para a resposta da IA...">${configPromptIndividual.instrucoesResposta}</textarea>
                                    </div>
                                </form>
                            </div>
                            
                            <!-- ETAPA 2: ANÁLISE IA -->
                            <div id="etapa2" class="wizard-step d-none">
                                <div class="d-flex justify-content-between align-items-center mb-3">
                                    <h6 class="mb-0"><i class="bi bi-robot"></i> Análise da IA</h6>
                                    <button type="button" class="btn btn-sm btn-outline-info" onclick="mostrarDebugPrompt()" id="btnDebugPrompt" style="display: none;">
                                        <i class="bi bi-bug"></i>
                                        Debug Prompt
                                    </button>
                                </div>
                                <div id="analiseContent" class="wizard-step-content">
                                    <div class="text-center py-4">
                                        <div class="spinner-border text-primary" role="status">
                                            <span class="visually-hidden">Analisando...</span>
                                        </div>
                                        <p class="mt-3 text-muted">Executando análise com IA...</p>
                                    </div>
                                </div>
                            </div>
                            
                            <!-- ETAPA 3: TESTE TRIAGEM -->
                            <div id="etapa3" class="wizard-step d-none">
                                <h6 class="mb-3"><i class="bi bi-play-circle"></i> Teste de Triagem</h6>
                                <div id="testeContent" class="wizard-step-content">
                                    <div class="alert alert-info">
                                        <h6><i class="bi bi-lightbulb"></i> Sugestões da IA</h6>
                                        <p class="mb-2">Com base na análise, cole as regras de negócio sugeridas:</p>
                                        <textarea class="form-control" id="regrasNegocioManual" rows="6" 
                                            placeholder="Cole aqui as regras de negócio sugeridas pela IA..."></textarea>
                                        <div class="mt-2 d-flex flex-wrap gap-2 align-items-center">
                                            <button type="button" class="btn btn-sm btn-outline-secondary" onclick="preencherRegrasAutomaticamente()">
                                                <i class="bi bi-magic"></i>
                                                Tentar Extrair Automaticamente
                                            </button>
                                            <button type="button" class="btn btn-sm btn-outline-primary" onclick="mostrarPromptPreviewTesteTriagemWizard()">
                                                <i class="bi bi-eye"></i>
                                                Mostrar prompt do teste
                                            </button>
                                        </div>
                                    </div>
                                    
                                    <div class="row">
                                        <div class="col-md-6">
                                            <label for="quantidadeTestes" class="form-label">Quantidade de Testes:</label>
                                            <input type="number" class="form-control" id="quantidadeTestes" value="10" min="1" max="50">
                                        </div>
                                        <div class="col-md-6">
                                            <label class="form-label">Tempo Estimado:</label>
                                            <div class="form-control-plaintext" id="tempoEstimado">~30 segundos</div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            <!-- ETAPA 4: RESULTADO -->
                            <div id="etapa4" class="wizard-step d-none">
                                <h6 class="mb-3"><i class="bi bi-graph-up"></i> Resultado Consolidado</h6>
                                <div id="resultadoContent" class="wizard-step-content">
                                    <!-- Conteúdo será preenchido dinamicamente -->
                                </div>
                            </div>
                            
                            <!-- ETAPA 5: TESTE COMBINADO -->
                            <div id="etapa5" class="wizard-step d-none">
                                <h6 class="mb-3"><i class="bi bi-arrow-repeat"></i> Teste com Regras Combinadas</h6>
                                <div id="testeCombinadoContent" class="wizard-step-content">
                                    <!-- Conteúdo será preenchido dinamicamente -->
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="wizard-footer">
                        <div class="d-flex justify-content-between">
                            <button type="button" class="btn btn-outline-secondary" id="wizardAnterior" onclick="wizardAnterior()" style="display: none;">
                                <i class="bi bi-arrow-left"></i>
                                Anterior
                            </button>
                            <div>
                                <button type="button" class="btn btn-secondary me-2" onclick="resetarConfigAnaliseIndividual()">
                                    <i class="bi bi-arrow-clockwise"></i>
                                    Resetar
                                </button>
                                <button type="button" class="btn btn-outline-info me-2" onclick="mostrarPreviewPromptDiagnosticoWizard()">
                                    <i class="bi bi-eye"></i>
                                    Ver Prompt Completo
                                </button>
                                <button type="button" class="btn btn-primary" id="btnProximo" onclick="wizardProximo()">
                                    Fazer diagnóstico
                                    <i class="bi bi-arrow-right"></i>
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

// ===== FUNÇÕES DO WIZARD =====

/**
 * Navega para a próxima etapa do wizard
 */
function wizardProximo() {
    const etapaAtual = window.wizardData.etapaAtual;
    
    if (etapaAtual === 1) {
        // Salvar configuração e ir para análise
        salvarConfigAnaliseIndividual();
        irParaEtapa(2);
        executarAnaliseWizard();
    } else if (etapaAtual === 2) {
        // Ir para teste de triagem
        irParaEtapa(3);
    } else if (etapaAtual === 3) {
        // Executar teste de triagem
        executarTesteTriagemWizard();
    } else if (etapaAtual === 4) {
        // Verificar se teste combinado já foi executado
        if (window.wizardData.testeCombinado && window.wizardData.testeCombinado.executado) {
            // Ir para etapa 5 e carregar dados salvos
            irParaEtapa(5);
        } else {
            // Executar teste combinado pela primeira vez
            irParaEtapa(5);
            executarTesteCombinadoWizard();
        }
    }
}

/**
 * Navega para a etapa anterior do wizard
 */
function wizardAnterior() {
    const etapaAtual = window.wizardData.etapaAtual;
    
    if (etapaAtual > 1) {
        irParaEtapa(etapaAtual - 1);
    }
}

/**
 * Navega livremente entre etapas (navegação superior)
 */
function navegarParaEtapa(etapa) {
    const etapaAtual = window.wizardData.etapaAtual;
    
    // Verificar se pode navegar para a etapa
    if (etapa === 1) {
        // Sempre pode ir para etapa 1
        irParaEtapa(1);
    } else if (etapa === 2 && window.wizardData.resultadoAnalise) {
        // Pode ir para etapa 2 se já executou análise
        irParaEtapa(2);
    } else if (etapa === 3 && window.wizardData.resultadoAnalise) {
        // Pode ir para etapa 3 se já executou análise
        irParaEtapa(3);
    } else if (etapa === 4 && window.wizardData.resultadoAnalise) {
        // Pode ir para etapa 4 se já executou análise
        irParaEtapa(4);
    } else if (etapa === 5 && window.wizardData.testeCombinado && window.wizardData.testeCombinado.executado) {
        // Pode ir para etapa 5 se já executou teste combinado
        irParaEtapa(5);
    } else {
        // Etapa não disponível ainda
        if (typeof showToast !== 'undefined') {
            showToast(`Etapa ${etapa} não disponível ainda. Complete as etapas anteriores primeiro.`, 'warning');
        }
    }
}

/**
 * Navega para uma etapa específica e atualiza a interface
 */
function irParaEtapa(novaEtapa) {
    // Ocultar todas as etapas
    document.querySelectorAll('.wizard-step').forEach(etapa => {
        etapa.classList.add('d-none');
    });
    
    // Mostrar etapa atual
    const etapaElement = document.getElementById(`etapa${novaEtapa}`);
    if (etapaElement) {
        etapaElement.classList.remove('d-none');
    }
    
    // Atualizar indicadores
    atualizarIndicadoresEtapas(novaEtapa);
    
    // Atualizar botões
    atualizarBotoesWizard(novaEtapa);
    
    // Atualizar dados
    window.wizardData.etapaAtual = novaEtapa;
    
    // Carregar dados salvos se existirem
    if (novaEtapa === 2 && window.wizardData.resultadoAnalise) {
        // Carregar resultado da análise salva
        mostrarResultadoAnaliseWizard(window.wizardData.resultadoAnalise);
    } else if (novaEtapa === 4 && window.wizardData.resultadoAnalise) {
        // Carregar resultado consolidado se existir
        if (window.wizardData.resultadoConsolidado) {
            mostrarResultadoConsolidadoWizard(
                window.wizardData.resultadoConsolidado.resultados,
                window.wizardData.resultadoConsolidado.regrasSugeridas
            );
        }
    } else if (novaEtapa === 5 && window.wizardData.testeCombinado && window.wizardData.testeCombinado.executado) {
        // Carregar resultado do teste combinado salvo
        mostrarResultadoFinalWizard(
            window.wizardData.testeCombinado.resultados,
            window.wizardData.testeCombinado.regrasCombinadas
        );
    }
}

/**
 * Atualiza os indicadores visuais das etapas (badges)
 */
function atualizarIndicadoresEtapas(etapaAtual) {
    // Resetar todos os badges
    for (let i = 1; i <= 5; i++) {
        const badge = document.getElementById(`step${i}`);
        const text = document.getElementById(`step${i}Text`);
        
        if (!badge || !text) continue;
        
        // Verificar se etapa tem resultado
        let temResultado = false;
        if (i === 2 && window.wizardData.resultadoAnalise) temResultado = true;
        if (i === 4 && window.wizardData.resultadoConsolidado) temResultado = true;
        if (i === 5 && window.wizardData.testeCombinado && window.wizardData.testeCombinado.executado) temResultado = true;
        
        if (i < etapaAtual) {
            // Etapas concluídas
            badge.className = 'badge bg-success me-2';
            text.className = 'text-success';
        } else if (i === etapaAtual) {
            // Etapa atual
            badge.className = 'badge bg-primary me-2';
            text.className = 'text-primary fw-bold';
        } else if (temResultado) {
            // Etapas futuras com resultado disponível
            badge.className = 'badge bg-info me-2';
            text.className = 'text-info';
        } else {
            // Etapas futuras sem resultado
            badge.className = 'badge bg-secondary me-2';
            text.className = 'text-muted';
        }
    }
    
    // Atualizar barra de progresso
    const progresso = (etapaAtual / 5) * 100;
    const progressBar = document.getElementById('wizardProgress');
    if (progressBar) {
        progressBar.style.width = `${progresso}%`;
    }
}

/**
 * Atualiza os botões do wizard conforme a etapa atual
 */
function atualizarBotoesWizard(etapaAtual) {
    const btnAnterior = document.getElementById('wizardAnterior');
    const btnProximo = document.getElementById('btnProximo');
    
    // Botão Anterior
    if (btnAnterior) {
        if (etapaAtual === 1) {
            btnAnterior.style.display = 'none';
        } else {
            btnAnterior.style.display = 'inline-block';
        }
    }
    
    // Botão Próximo
    if (btnProximo) {
        if (etapaAtual === 5) {
            btnProximo.style.display = 'none';
        } else {
            btnProximo.style.display = 'inline-block';
            if (etapaAtual === 1) {
                btnProximo.innerHTML = 'Fazer diagnóstico <i class="bi bi-arrow-right"></i>';
            } else if (etapaAtual === 2) {
                btnProximo.innerHTML = 'Próximo <i class="bi bi-arrow-right"></i>';
            } else if (etapaAtual === 3) {
                btnProximo.innerHTML = '<i class="bi bi-play-circle"></i> Executar Teste';
            } else if (etapaAtual === 4) {
                btnProximo.innerHTML = '<i class="bi bi-arrow-repeat"></i> Teste Combinado';
            }
        }
    }
}

// ===== FUNÇÕES DE ANÁLISE =====

/**
 * Mostra preview do prompt completo do diagnóstico (sem chamar IA).
 */
async function mostrarPreviewPromptDiagnosticoWizard() {
    const { promptId, promptNome, acertos, total } = window.wizardData || {};
    if (!promptId) {
        if (typeof showToast !== 'undefined') {
            showToast('Prompt não identificado para gerar preview', 'error');
        }
        return;
    }

    try {
        const configAtual = {
            persona: (document.getElementById('personaIndividual')?.value || '').trim(),
            instrucoesResposta: (document.getElementById('instrucoesRespostaIndividual')?.value || '').trim(),
            incluirContextoIntimacao: !!document.getElementById('incluirContextoIndividual')?.checked,
            incluirInformacaoAdicional: !!document.getElementById('incluirGabaritoIndividual')?.checked,
            incluirIdentificacaoPromptDesempenho: !!document.getElementById('incluirIdentificacaoPromptDesempenhoIndividual')?.checked,
            incluirConteudoPromptCadastrado: !!document.getElementById('incluirConteudoPromptCadastradoIndividual')?.checked,
            incluirTriagemFeitaPelaIa: !!document.getElementById('incluirTriagemFeitaPelaIaIndividual')?.checked
        };

        const configComModelo = anexarModeloDiagnosticoOverrideSelecionado(configAtual);

        const response = await fetch('/api/analisar-prompt-individual', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                prompt_id: promptId,
                prompt_nome: promptNome,
                intimacao_id: window.intimacaoData ? window.intimacaoData.id : null,
                config_personalizada: configComModelo,
                taxa_acerto: window.wizardData.taxaAcerto,
                acertos: acertos,
                total_analises: total,
                dados_analise_original: window.wizardData.dadosAnaliseOriginal,
                preview_only: true
            })
        });

        const data = await response.json();
        if (!data.success) {
            throw new Error(data.message || 'Erro ao montar preview do prompt');
        }

        window.wizardData.promptCompleto = data.prompt_completo || 'Prompt não disponível';
        mostrarDebugPrompt();
    } catch (error) {
        console.error('Erro ao gerar preview do prompt do diagnóstico:', error);
        if (typeof showToast !== 'undefined') {
            showToast('Erro ao gerar preview do prompt do diagnóstico', 'error');
        }
    }
}

/**
 * Executa análise com IA (Etapa 2)
 */
async function executarAnaliseWizard() {
    const { promptId, promptNome, acertos, total } = window.wizardData;
    
    try {
        // Salvar configuração atual
        configPromptIndividual = {
            persona: document.getElementById('personaIndividual').value.trim(),
            instrucoesResposta: document.getElementById('instrucoesRespostaIndividual').value.trim(),
            incluirContextoIntimacao: document.getElementById('incluirContextoIndividual').checked,
            incluirInformacaoAdicional: document.getElementById('incluirGabaritoIndividual').checked,
            incluirIdentificacaoPromptDesempenho: document.getElementById('incluirIdentificacaoPromptDesempenhoIndividual').checked,
            incluirConteudoPromptCadastrado: document.getElementById('incluirConteudoPromptCadastradoIndividual').checked,
            incluirTriagemFeitaPelaIa: document.getElementById('incluirTriagemFeitaPelaIaIndividual').checked
        };
        
        // Salvar no localStorage
        localStorage.setItem('configPromptIndividual', JSON.stringify(configPromptIndividual));

        const configComModelo = anexarModeloDiagnosticoOverrideSelecionado(configPromptIndividual);
        
        // Fazer requisição para análise
        const response = await fetch('/api/analisar-prompt-individual', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                prompt_id: promptId,
                prompt_nome: promptNome,
                intimacao_id: window.intimacaoData ? window.intimacaoData.id : null,
                config_personalizada: configComModelo,
                taxa_acerto: window.wizardData.taxaAcerto,
                acertos: acertos,
                total_analises: total,
                dados_analise_original: window.wizardData.dadosAnaliseOriginal
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Armazenar resultado e prompt completo
            window.wizardData.resultadoAnalise = data.resultado;
            window.wizardData.promptCompleto = data.prompt_completo || 'Prompt não disponível';
            
            // Mostrar resultado na etapa 2
            mostrarResultadoAnaliseWizard(data.resultado);
            
            // Mostrar botão de debug
            const btnDebug = document.getElementById('btnDebugPrompt');
            if (btnDebug) btnDebug.style.display = 'inline-block';
        } else {
            throw new Error(data.message);
        }
    } catch (error) {
        console.error('Erro na análise:', error);
        const analiseContent = document.getElementById('analiseContent');
        if (analiseContent) {
            analiseContent.innerHTML = `
                <div class="alert alert-danger">
                    <h6><i class="bi bi-exclamation-triangle"></i> Erro na Análise</h6>
                    <p class="mb-0">Erro ao conectar com a IA. Tente novamente.</p>
                </div>
            `;
        }
    }
}

/**
 * Botão "copiar" no canto de cada bloco de código (```) do diagnóstico — estilo apps de chat.
 */
function wizardAnexarBotoesCopiarNosPresDoDiagnostico(analiseContentEl) {
    const root = analiseContentEl && analiseContentEl.querySelector('.markdown-content');
    if (!root) {
        return;
    }
    root.querySelectorAll('pre').forEach((pre) => {
        if (pre.parentElement && pre.parentElement.classList.contains('wizard-md-pre-wrap')) {
            return;
        }
        const wrap = document.createElement('div');
        wrap.className = 'wizard-md-pre-wrap position-relative mb-3';
        pre.parentNode.insertBefore(wrap, pre);
        wrap.appendChild(pre);
        const padExtra = '2.75rem';
        if (!pre.style.paddingRight) {
            pre.style.paddingRight = padExtra;
        }
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'btn btn-sm btn-light text-dark position-absolute border shadow-sm';
        btn.style.top = '0.4rem';
        btn.style.right = '0.4rem';
        btn.style.zIndex = '4';
        btn.style.lineHeight = '1';
        btn.setAttribute('aria-label', 'Copiar conteúdo deste bloco');
        btn.title = 'Copiar';
        btn.innerHTML = '<i class="bi bi-clipboard"></i>';
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            const t = pre.innerText != null ? pre.innerText : '';
            navigator.clipboard.writeText(t).then(() => {
                if (typeof showToast !== 'undefined') {
                    showToast('Bloco copiado para a área de transferência.', 'success');
                }
            }).catch((err) => {
                console.error('Erro ao copiar bloco do diagnóstico:', err);
                if (typeof showToast !== 'undefined') {
                    showToast('Não foi possível copiar este bloco.', 'error');
                }
            });
        });
        wrap.appendChild(btn);
    });
}

/**
 * Mostra resultado da análise na etapa 2
 */
function mostrarResultadoAnaliseWizard(resultado) {
    const analiseContent = document.getElementById('analiseContent');
    if (!analiseContent) return;

    const texto = resultado == null ? '' : String(resultado);
    if (!texto.trim()) {
        analiseContent.innerHTML = `
        <div class="alert alert-warning">
            <h6 class="mb-2"><i class="bi bi-chat-dots"></i> Resposta vazia da IA</h6>
            <p class="mb-0">O servidor respondeu com sucesso, mas o texto da análise veio vazio. Isso costuma ser limite de tokens, recusa do modelo ou formato da resposta no provedor (ex.: LiteLLM). Confira o terminal do Flask para logs <code>corpo assistant vazio</code> e <code>finish_reason</code>. Use <strong>Debug Prompt</strong> para ver o que foi enviado.</p>
        </div>
        <div class="d-flex gap-2 mb-4">
            <button type="button" class="btn btn-sm btn-outline-primary" onclick="copiarResultadoAnaliseIndividual()">
                <i class="bi bi-clipboard"></i>
                Copiar Resultado
            </button>
        </div>`;
        analiseContent.style.paddingBottom = '8rem';
        return;
    }

    let html = '';
    if (typeof marked !== 'undefined') {
        html = marked.parse(texto);
    } else {
        html = texto.replace(/\n/g, '<br>');
    }

    analiseContent.innerHTML = `
        <div class="alert alert-info">
            <div class="markdown-content">${html}</div>
        </div>
        <div class="d-flex gap-2 mb-4">
            <button type="button" class="btn btn-sm btn-outline-primary" onclick="copiarResultadoAnaliseIndividual()">
                <i class="bi bi-clipboard"></i>
                Copiar Resultado
            </button>
        </div>
    `;

    wizardAnexarBotoesCopiarNosPresDoDiagnostico(analiseContent);
    
    // Garantir que o padding seja aplicado após inserir o conteúdo
    analiseContent.style.paddingBottom = '8rem';
}

// ===== FUNÇÕES DE TESTE DE TRIAGEM =====

/**
 * Executa teste de triagem (Etapa 3 → 4)
 */
async function executarTesteTriagemWizard() {
    const { promptId, resultadoAnalise } = window.wizardData;
    
    if (!resultadoAnalise) {
        if (typeof showToast !== 'undefined') {
            showToast('Análise não disponível para teste', 'error');
        }
        return;
    }
    
    try {
        // Obter regras de negócio da textarea
        const regrasSugeridas = document.getElementById('regrasNegocioManual').value.trim();
        
        if (!regrasSugeridas) {
            if (typeof showToast !== 'undefined') {
                showToast('Por favor, cole as regras de negócio sugeridas', 'warning');
            }
            return;
        }
        
        // Obter quantidade de testes
        const quantidadeTestes = parseInt(document.getElementById('quantidadeTestes').value) || 10;
        
        // Armazenar dados para uso posterior
        promptIdAtual = promptId;
        resultadoAnaliseAtual = resultadoAnalise;
        
        // Armazenar regra testada
        window.wizardData.regraTestada = regrasSugeridas;
        
        // Ir para etapa 4
        irParaEtapa(4);
        
        // Mostrar loading
        const resultadoContent = document.getElementById('resultadoContent');
        if (resultadoContent) {
            resultadoContent.innerHTML = `
                <div class="text-center py-4">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">Executando testes...</span>
                    </div>
                    <p class="mt-3 text-muted">Executando ${quantidadeTestes} testes de triagem...</p>
                </div>
            `;
        }
        
        // Executar testes
        const resultados = [];
        
        for (let i = 0; i < quantidadeTestes; i++) {
            // Atualizar progresso
            if (resultadoContent) {
                resultadoContent.innerHTML = `
                    <div class="text-center py-4">
                        <div class="spinner-border text-primary" role="status">
                            <span class="visually-hidden">Executando teste ${i + 1}/${quantidadeTestes}...</span>
                        </div>
                        <p class="mt-3 text-muted">Executando teste ${i + 1} de ${quantidadeTestes}...</p>
                    </div>
                `;
            }
            
            try {
                const response = await fetch('/api/testar-triagem-customizada', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        intimacao_id: window.intimacaoData ? window.intimacaoData.id : null,
                        regras_negocio: regrasSugeridas,
                        prompt_base_id: promptId
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    resultados.push(data.resultado);
                } else {
                    resultados.push({
                        erro: true,
                        mensagem: data.message,
                        teste: i + 1
                    });
                }
            } catch (error) {
                resultados.push({
                    erro: true,
                    mensagem: 'Erro de conexão',
                    teste: i + 1
                });
            }
        }
        
        // Mostrar resultado consolidado
        mostrarResultadoConsolidadoWizard(resultados, regrasSugeridas);
        
    } catch (error) {
        console.error('Erro ao testar triagem:', error);
        const resultadoContent = document.getElementById('resultadoContent');
        if (resultadoContent) {
            resultadoContent.innerHTML = `
                <div class="alert alert-danger">
                    <h6><i class="bi bi-exclamation-triangle"></i> Erro no Teste</h6>
                    <p class="mb-0">Erro ao conectar com a API. Tente novamente.</p>
                </div>
            `;
        }
    }
}

/**
 * Mostra resultado consolidado dos testes (Etapa 4)
 */
function mostrarResultadoConsolidadoWizard(resultados, regrasSugeridas) {
    // Armazenar regras testadas
    regrasTestadasAtual = regrasSugeridas;
    
    // Armazenar resultado consolidado para navegação
    window.wizardData.resultadoConsolidado = {
        resultados: resultados,
        regrasSugeridas: regrasSugeridas
    };
    
    // Calcular estatísticas
    const testesComSucesso = resultados.filter(r => !r.erro);
    const acertos = testesComSucesso.filter(r => r.acertou === true).length;
    const taxaAcerto = testesComSucesso.length > 0 ? (acertos / testesComSucesso.length * 100).toFixed(1) : 0;
    
    // Construir HTML da tabela
    const tabelaHtml = construirTabelaResultados(resultados, regrasSugeridas, testesComSucesso, acertos, taxaAcerto);
    
    const resultadoContent = document.getElementById('resultadoContent');
    if (resultadoContent) {
        resultadoContent.innerHTML = tabelaHtml;
    }
    
    // Verificar se teste combinado já foi executado
    if (window.wizardData.testeCombinado && window.wizardData.testeCombinado.executado) {
        // Mostrar botão "Executar Novo Teste", esconder "Testar com Regras Combinadas"
        setTimeout(() => {
            const btnTesteCombinado = document.getElementById('btnTesteCombinado');
            const btnNovoTesteCombinado = document.getElementById('btnNovoTesteCombinado');
            
            if (btnTesteCombinado) btnTesteCombinado.style.display = 'none';
            if (btnNovoTesteCombinado) btnNovoTesteCombinado.style.display = 'inline-block';
        }, 100);
    }
    
    // Inicializar tooltips
    setTimeout(() => {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
        
        // Adicionar event listener para quantidade de testes combinado
        const quantidadeInput = document.getElementById('quantidadeTestesCombinado');
        if (quantidadeInput) {
            quantidadeInput.addEventListener('input', function() {
                calcularTempoEstimadoCombinado();
            });
        }
    }, 100);
}

/**
 * Constrói HTML da tabela de resultados
 */
function construirTabelaResultados(resultados, regrasSugeridas, testesComSucesso, acertos, taxaAcerto) {
    let tabelaHtml = `
        <!-- Seção Regra em Teste -->
        <div class="alert alert-info mb-4">
            <h6><i class="bi bi-lightbulb"></i> Regra em Teste</h6>
            <p class="mb-2"><strong>Sugestão da IA:</strong></p>
            <div class="bg-light p-3 rounded" style="max-height: 150px; overflow-y: auto;">
                <pre style="white-space: pre-wrap; margin: 0; font-size: 0.9em;">${window.wizardData.regraTestada || 'N/A'}</pre>
            </div>
            <small class="text-muted">
                <i class="bi bi-info-circle"></i>
                Esta regra foi sugerida pela IA na análise e está sendo testada com ${testesComSucesso.length} execuções.
            </small>
            <div class="mt-2">
                <button type="button" class="btn btn-sm btn-outline-secondary" onclick="copiarRegraTestada()">
                    <i class="bi bi-clipboard"></i>
                    Copiar Regra
                </button>
            </div>
        </div>
        
        <div class="row mb-4">
            <div class="col-md-3">
                <div class="card text-center">
                    <div class="card-body">
                        <h5 class="card-title text-primary">${testesComSucesso.length}</h5>
                        <p class="card-text">Testes Executados</p>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card text-center">
                    <div class="card-body">
                        <h5 class="card-title text-success">${acertos}</h5>
                        <p class="card-text">Acertos</p>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card text-center">
                    <div class="card-body">
                        <h5 class="card-title text-info">${taxaAcerto}%</h5>
                        <p class="card-text">Taxa de Acerto</p>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card text-center">
                    <div class="card-body">
                        <h5 class="card-title text-warning">${resultados.length - testesComSucesso.length}</h5>
                        <p class="card-text">Erros</p>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="table-responsive">
            <table class="table table-hover">
                <thead class="table-light">
                    <tr>
                        <th>Teste</th>
                        <th>Classificação IA</th>
                        <th>Classificação Manual</th>
                        <th>Acertou</th>
                        <th>Modelo</th>
                        <th>Resposta Completa</th>
                    </tr>
                </thead>
                <tbody>
    `;
    
    resultados.forEach((resultado, index) => {
        const acertou = resultado.acertou ? 'Sim' : 'Não';
        const badgeClass = resultado.acertou ? 'bg-success' : 'bg-danger';
        const respostaCompleta = resultado.resposta_completa || 'N/A';
        
        tabelaHtml += `
            <tr>
                <td>${index + 1}</td>
                <td>${resultado.classificacao_ia || 'N/A'}</td>
                <td>${resultado.classificacao_manual || 'N/A'}</td>
                <td><span class="badge ${badgeClass}">${acertou}</span></td>
                <td><small class="text-muted">${resultado.modelo_utilizado || 'N/A'}</small></td>
                <td>
                    <span class="badge bg-info" 
                          data-bs-toggle="tooltip" 
                          data-bs-placement="top" 
                          title="${escaparTextoParaTooltip(respostaCompleta)}">
                        Ver Resposta
                    </span>
                </td>
            </tr>
        `;
    });
    
    tabelaHtml += `
                </tbody>
            </table>
        </div>
        
        <!-- Configuração do Teste Combinado -->
        <div class="card mb-4" id="configTesteCombinado">
            <div class="card-header">
                <h6 class="mb-0"><i class="bi bi-gear"></i> Configuração do Teste Combinado</h6>
            </div>
            <div class="card-body">
                <div class="row">
                    <div class="col-md-6">
                        <label for="quantidadeTestesCombinado" class="form-label">Quantidade de Testes:</label>
                        <input type="number" class="form-control" id="quantidadeTestesCombinado" value="10" min="1" max="50">
                    </div>
                    <div class="col-md-6">
                        <label class="form-label">Tempo Estimado:</label>
                        <div class="form-control-plaintext" id="tempoEstimadoCombinado">~30 segundos</div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="d-flex gap-2 mt-3">
            <button type="button" class="btn btn-outline-secondary" onclick="copiarRegrasUtilizadas()">
                <i class="bi bi-clipboard"></i>
                Copiar Regras
            </button>
            <button type="button" class="btn btn-info" onclick="verPromptCombinado()">
                <i class="bi bi-eye"></i>
                Ver Prompt Combinado
            </button>
            <button type="button" class="btn btn-success" onclick="wizardProximo()" id="btnTesteCombinado">
                <i class="bi bi-arrow-repeat"></i>
                Testar com Regras Combinadas
            </button>
            <button type="button" class="btn btn-warning" onclick="executarNovoTesteCombinado()" id="btnNovoTesteCombinado" style="display: none;">
                <i class="bi bi-arrow-repeat"></i>
                Executar Novo Teste
            </button>
        </div>
    `;
    
    return tabelaHtml;
}

// ===== FUNÇÕES DE TESTE COMBINADO =====

/**
 * Executa teste combinado (Etapa 5)
 */
async function executarTesteCombinadoWizard() {
    const { promptId } = window.wizardData;
    
    if (!promptId || !regrasTestadasAtual) {
        if (typeof showToast !== 'undefined') {
            showToast('Dados não disponíveis para teste combinado', 'error');
        }
        return;
    }
    
    try {
        // Mostrar loading
        const testeCombinadoContent = document.getElementById('testeCombinadoContent');
        if (testeCombinadoContent) {
            testeCombinadoContent.innerHTML = `
                <div class="text-center py-4">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">Executando teste combinado...</span>
                    </div>
                    <p class="mt-3 text-muted">Executando teste com regras combinadas...</p>
                </div>
            `;
        }
        
        // Buscar prompt base
        let promptBase = null;
        if (!promptBaseAtual) {
            try {
                const response = await fetch(`/api/prompts/${promptId}`);
                const data = await response.json();
                if (data.success && data.prompt) {
                    promptBase = data.prompt;
                    promptBaseAtual = promptBase;
                }
            } catch (error) {
                console.error('Erro ao buscar prompt base:', error);
            }
        } else {
            promptBase = promptBaseAtual;
        }
        
        if (!promptBase) {
            throw new Error('Prompt base não encontrado');
        }
        
        // Combinar regras originais + testadas
        const regrasOriginais = promptBase.regra_negocio || '';
        const regrasCombinadas = `${regrasOriginais}\n\n=== REGRAS ADICIONAIS TESTADAS ===\n${regrasTestadasAtual}`;
        
        // Obter quantidade de testes (do campo da Etapa 4)
        const quantidadeTestes = parseInt(document.getElementById('quantidadeTestesCombinado').value) || 10;
        
        // Executar testes combinados
        const resultados = [];
        
        for (let i = 0; i < quantidadeTestes; i++) {
            // Atualizar progresso
            if (testeCombinadoContent) {
                testeCombinadoContent.innerHTML = `
                    <div class="text-center py-4">
                        <div class="spinner-border text-primary" role="status">
                            <span class="visually-hidden">Executando teste combinado ${i + 1}/${quantidadeTestes}...</span>
                        </div>
                        <p class="mt-3 text-muted">Executando teste combinado ${i + 1} de ${quantidadeTestes}...</p>
                    </div>
                `;
            }
            
            try {
                const response = await fetch('/api/testar-triagem-customizada', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        intimacao_id: window.intimacaoData ? window.intimacaoData.id : null,
                        regras_negocio: regrasCombinadas,
                        prompt_base_id: promptId
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    resultados.push(data.resultado);
                } else {
                    resultados.push({
                        erro: true,
                        mensagem: data.message,
                        teste: i + 1
                    });
                }
            } catch (error) {
                resultados.push({
                    erro: true,
                    mensagem: 'Erro de conexão',
                    teste: i + 1
                });
            }
        }
        
        // Armazenar dados do teste combinado
        window.wizardData.testeCombinado = {
            resultados: resultados,
            regrasCombinadas: regrasCombinadas,
            executado: true
        };
        
        // Mostrar resultado final
        mostrarResultadoFinalWizard(resultados, regrasCombinadas);
        
    } catch (error) {
        console.error('Erro ao executar teste combinado:', error);
        const testeCombinadoContent = document.getElementById('testeCombinadoContent');
        if (testeCombinadoContent) {
            testeCombinadoContent.innerHTML = `
                <div class="alert alert-danger">
                    <h6><i class="bi bi-exclamation-triangle"></i> Erro no Teste Combinado</h6>
                    <p class="mb-0">Erro ao conectar com a API. Tente novamente.</p>
                </div>
            `;
        }
    }
}

/**
 * Mostra resultado final do teste combinado (Etapa 5)
 */
function mostrarResultadoFinalWizard(resultados, regrasCombinadas) {
    // Calcular estatísticas
    const testesComSucesso = resultados.filter(r => !r.erro);
    const acertos = testesComSucesso.filter(r => r.acertou === true).length;
    const taxaAcerto = testesComSucesso.length > 0 ? (acertos / testesComSucesso.length * 100).toFixed(1) : 0;
    
    // Construir HTML do resultado final (similar ao consolidado, mas sem botão de teste combinado)
    const html = construirTabelaResultadosCombinados(resultados, regrasCombinadas, testesComSucesso, acertos, taxaAcerto);
    
    const testeCombinadoContent = document.getElementById('testeCombinadoContent');
    if (testeCombinadoContent) {
        testeCombinadoContent.innerHTML = html;
    }
    
    // Inicializar tooltips
    setTimeout(() => {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }, 100);
}

/**
 * Constrói HTML da tabela de resultados combinados
 */
function construirTabelaResultadosCombinados(resultados, regrasCombinadas, testesComSucesso, acertos, taxaAcerto) {
    let html = `
        <!-- Seção Regra Testada -->
        <div class="alert alert-info mb-4">
            <h6><i class="bi bi-lightbulb"></i> Regra Testada</h6>
            <p class="mb-2"><strong>Sugestão da IA (já testada):</strong></p>
            <div class="bg-light p-3 rounded" style="max-height: 150px; overflow-y: auto;">
                <pre style="white-space: pre-wrap; margin: 0; font-size: 0.9em;">${window.wizardData.regraTestada || 'N/A'}</pre>
            </div>
            <small class="text-muted">
                <i class="bi bi-info-circle"></i>
                Esta regra foi testada anteriormente e agora está sendo combinada com as regras originais do prompt.
            </small>
            <div class="mt-2">
                <button type="button" class="btn btn-sm btn-outline-secondary" onclick="copiarRegraTestada()">
                    <i class="bi bi-clipboard"></i>
                    Copiar Regra
                </button>
            </div>
        </div>
        
        <div class="alert alert-success">
            <h6><i class="bi bi-check-circle"></i> Teste Combinado Concluído!</h6>
            <p class="mb-0">Teste executado com regras originais + regras testadas.</p>
        </div>
        
        <div class="row mb-4">
            <div class="col-md-3">
                <div class="card text-center">
                    <div class="card-body">
                        <h5 class="card-title text-primary">${testesComSucesso.length}</h5>
                        <p class="card-text">Testes Executados</p>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card text-center">
                    <div class="card-body">
                        <h5 class="card-title text-success">${acertos}</h5>
                        <p class="card-text">Acertos</p>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card text-center">
                    <div class="card-body">
                        <h5 class="card-title text-info">${taxaAcerto}%</h5>
                        <p class="card-text">Taxa de Acerto</p>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card text-center">
                    <div class="card-body">
                        <h5 class="card-title text-warning">${resultados.length - testesComSucesso.length}</h5>
                        <p class="card-text">Erros</p>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="table-responsive">
            <table class="table table-hover">
                <thead class="table-light">
                    <tr>
                        <th>Teste</th>
                        <th>Classificação IA</th>
                        <th>Classificação Manual</th>
                        <th>Acertou</th>
                        <th>Modelo</th>
                        <th>Resposta Completa</th>
                    </tr>
                </thead>
                <tbody>
    `;
    
    resultados.forEach((resultado, index) => {
        const acertou = resultado.acertou ? 'Sim' : 'Não';
        const badgeClass = resultado.acertou ? 'bg-success' : 'bg-danger';
        const respostaCompleta = resultado.resposta_completa || 'N/A';
        
        html += `
            <tr>
                <td>${index + 1}</td>
                <td>${resultado.classificacao_ia || 'N/A'}</td>
                <td>${resultado.classificacao_manual || 'N/A'}</td>
                <td><span class="badge ${badgeClass}">${acertou}</span></td>
                <td><small class="text-muted">${resultado.modelo_utilizado || 'N/A'}</small></td>
                <td>
                    <span class="badge bg-info" 
                          data-bs-toggle="tooltip" 
                          data-bs-placement="top" 
                          title="${escaparTextoParaTooltip(respostaCompleta)}">
                        Ver Resposta
                    </span>
                </td>
            </tr>
        `;
    });
    
    html += `
                </tbody>
            </table>
        </div>
        
        <div class="d-flex gap-2 mt-3">
            <button type="button" class="btn btn-outline-secondary" onclick="navigator.clipboard.writeText('${regrasCombinadas.replace(/'/g, "\\'")}')">
                <i class="bi bi-clipboard"></i>
                Copiar Regras Combinadas
            </button>
            <button type="button" class="btn btn-info" onclick="verPromptCombinado()">
                <i class="bi bi-eye"></i>
                Ver Prompt Combinado
            </button>
            <button type="button" class="btn btn-primary" onclick="criarNovoPromptComRegrasConsolidadas()" id="btnCriarNovoPrompt">
                <i class="bi bi-plus-circle"></i>
                Criar Novo Prompt com Regras Consolidadas
            </button>
            <button type="button" class="btn btn-success" onclick="wizardAnterior()">
                <i class="bi bi-arrow-left"></i>
                Voltar ao Resultado
            </button>
        </div>
    `;
    
    return html;
}

// ===== FUNÇÕES AUXILIARES =====

/**
 * Copia resultado da análise individual
 */
function copiarResultadoAnaliseIndividual() {
    let texto = '';
    const wizardMd = document.querySelector('#analiseContent .markdown-content');
    if (wizardMd) {
        texto = wizardMd.textContent || wizardMd.innerText || '';
    } else {
        const resultadoElement = document.getElementById('resultado-analise-individual');
        if (resultadoElement) {
            texto = resultadoElement.textContent || resultadoElement.innerText || '';
        }
    }
    if (!String(texto).trim() && typeof window !== 'undefined' && window.wizardData && window.wizardData.resultadoAnalise) {
        texto = String(window.wizardData.resultadoAnalise);
    }
    if (!String(texto).trim()) {
        if (typeof showToast !== 'undefined') {
            showToast('Nenhum resultado encontrado para copiar.', 'warning');
        }
        return;
    }
    navigator.clipboard.writeText(String(texto)).then(function() {
        if (typeof showToast !== 'undefined') {
            showToast('Resultado copiado para a área de transferência!', 'success');
        }
    }).catch(function(err) {
        console.error('Erro ao copiar resultado: ', err);
        if (typeof showToast !== 'undefined') {
            showToast('Erro ao copiar resultado.', 'error');
        }
    });
}

/**
 * Preenche regras automaticamente (extrai da análise)
 */
function preencherRegrasAutomaticamente() {
    if (!resultadoAnaliseAtual) {
        if (typeof showToast !== 'undefined') {
            showToast('Dados da análise não disponíveis', 'error');
        }
        return;
    }
    
    try {
        const regrasExtraidas = extrairRegrasSugeridas(resultadoAnaliseAtual);
        
        if (regrasExtraidas) {
            const regrasField = document.getElementById('regrasNegocioManual');
            if (regrasField) {
                regrasField.value = regrasExtraidas;
                if (typeof showToast !== 'undefined') {
                    showToast('Regras extraídas automaticamente! Revise e ajuste se necessário.', 'success');
                }
            }
        } else {
            if (typeof showToast !== 'undefined') {
                showToast('Não foi possível extrair regras automaticamente. Cole manualmente.', 'warning');
            }
        }
    } catch (error) {
        console.error('Erro ao extrair regras:', error);
        if (typeof showToast !== 'undefined') {
            showToast('Erro ao extrair regras automaticamente. Cole manualmente.', 'error');
        }
    }
}

/**
 * Extrai regras sugeridas do texto da análise
 */
function extrairRegrasSugeridas(resultadoAnalise) {
    // Tentar extrair JSON primeiro
    try {
        const jsonMatch = resultadoAnalise.match(/\{[\s\S]*\}/);
        if (jsonMatch) {
            const json = JSON.parse(jsonMatch[0]);
            if (json.recomendacoes) {
                return Array.isArray(json.recomendacoes) 
                    ? json.recomendacoes.join('\n') 
                    : json.recomendacoes;
            }
        }
    } catch (e) {
        // Não é JSON válido, continuar
    }
    
    // Fallback: extrair seções que parecem ser regras de negócio
    const linhas = resultadoAnalise.split('\n');
    const regras = [];
    let coletando = false;
    
    for (let linha of linhas) {
        linha = linha.trim();
        
        // Identificar início de seção de regras
        if (linha.toLowerCase().includes('regra') || 
            linha.toLowerCase().includes('recomenda') ||
            linha.toLowerCase().includes('sugestão')) {
            coletando = true;
            continue;
        }
        
        // Coletar linhas que parecem regras
        if (coletando && (linha.startsWith('-') || linha.startsWith('*') || linha.match(/^\d+\./))) {
            regras.push(linha);
        }
    }
    
    return regras.length > 0 ? regras.join('\n') : null;
}

/**
 * Copia regras utilizadas
 */
function copiarRegrasUtilizadas() {
    if (!regrasTestadasAtual) {
        if (typeof showToast !== 'undefined') {
            showToast('Nenhuma regra disponível para copiar', 'warning');
        }
        return;
    }
    
    navigator.clipboard.writeText(regrasTestadasAtual).then(function() {
        if (typeof showToast !== 'undefined') {
            showToast('Regras copiadas para a área de transferência!', 'success');
        }
    }).catch(function(err) {
        console.error('Erro ao copiar regras:', err);
        if (typeof showToast !== 'undefined') {
            showToast('Erro ao copiar regras.', 'error');
        }
    });
}

/**
 * Copia regra testada
 */
function copiarRegraTestada() {
    if (!window.wizardData || !window.wizardData.regraTestada) {
        if (typeof showToast !== 'undefined') {
            showToast('Nenhuma regra disponível para copiar', 'warning');
        }
        return;
    }
    
    navigator.clipboard.writeText(window.wizardData.regraTestada).then(function() {
        if (typeof showToast !== 'undefined') {
            showToast('Regra copiada para a área de transferência!', 'success');
        }
    }).catch(function(err) {
        console.error('Erro ao copiar regra:', err);
        if (typeof showToast !== 'undefined') {
            showToast('Erro ao copiar regra.', 'error');
        }
    });
}

/**
 * Executa novo teste combinado
 */
function executarNovoTesteCombinado() {
    // Limpar dados do teste anterior
    window.wizardData.testeCombinado = null;
    
    // Ir para etapa 5 e executar novo teste
    irParaEtapa(5);
    executarTesteCombinadoWizard();
}

/**
 * Calcula tempo estimado do teste combinado
 */
function calcularTempoEstimadoCombinado() {
    const quantidadeInput = document.getElementById('quantidadeTestesCombinado');
    const tempoEstimadoElement = document.getElementById('tempoEstimadoCombinado');
    
    if (!quantidadeInput || !tempoEstimadoElement) return;
    
    const quantidade = parseInt(quantidadeInput.value) || 10;
    const tempoPorTeste = 3; // segundos por teste (estimativa)
    const tempoTotal = quantidade * tempoPorTeste;
    
    tempoEstimadoElement.textContent = `~${tempoTotal} segundos`;
}

/**
 * Mostra debug do prompt
 */
function mostrarDebugPrompt() {
    if (window.wizardData && window.wizardData.promptCompleto) {
        const modalContent = document.getElementById('modal-debug-prompt-content');
        const debugModalEl = document.getElementById('modalDebugPrompt');
        const wizardModalEl = document.getElementById('modalWizardAnalise');
        if (modalContent) {
            modalContent.textContent = window.wizardData.promptCompleto;
            if (wizardModalEl && wizardModalEl.classList.contains('show')) {
                wizardModalEl.style.visibility = 'hidden';
            }
            const modal = new bootstrap.Modal(debugModalEl);
            if (debugModalEl) {
                debugModalEl.addEventListener('hidden.bs.modal', () => {
                    if (wizardModalEl) {
                        wizardModalEl.style.visibility = '';
                    }
                }, { once: true });
            }
            modal.show();
        }
    } else {
        if (typeof showToast !== 'undefined') {
            showToast('Prompt completo não disponível', 'warning');
        }
    }
}

/**
 * Preview do user prompt que será enviado no teste de triagem (etapa 3).
 */
async function mostrarPromptPreviewTesteTriagemWizard() {
    const promptId = window.wizardData ? window.wizardData.promptId : null;
    const intimacaoId = window.intimacaoData ? window.intimacaoData.id : null;
    const ta = document.getElementById('regrasNegocioManual');
    const regras = ta ? ta.value : '';

    const alerta = document.getElementById('modal-preview-prompt-triagem-alerta');
    const pre = document.getElementById('modal-preview-prompt-triagem-content');
    const modalEl = document.getElementById('modalPreviewPromptTesteTriagem');

    if (!intimacaoId) {
        if (typeof showToast !== 'undefined') {
            showToast('Intimação não identificada', 'error');
        }
        return;
    }
    if (!modalEl || !pre) {
        if (typeof showToast !== 'undefined') {
            showToast('Modal de preview não encontrado (abra o wizard nesta página)', 'error');
        }
        return;
    }

    pre.textContent = 'Carregando...';
    if (alerta) {
        alerta.classList.add('d-none');
    }

    try {
        const response = await fetch('/api/preview-prompt-triagem-customizada', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                intimacao_id: intimacaoId,
                regras_negocio: regras,
                prompt_base_id: promptId || null
            })
        });
        const data = await response.json();
        if (!data.success) {
            if (typeof showToast !== 'undefined') {
                showToast(data.message || 'Erro ao gerar preview', 'error');
            }
            return;
        }
        pre.textContent = data.prompt_final || '';
        if (alerta) {
            if (data.aviso_regras_vazias) {
                alerta.classList.remove('d-none');
            } else {
                alerta.classList.add('d-none');
            }
        }
        const modal = new bootstrap.Modal(modalEl);
        modal.show();
    } catch (e) {
        console.error(e);
        if (typeof showToast !== 'undefined') {
            showToast('Erro ao buscar preview do prompt', 'error');
        }
    }
}

function copiarPromptPreviewTriagemWizard() {
    const el = document.getElementById('modal-preview-prompt-triagem-content');
    if (!el) return;
    navigator.clipboard.writeText(el.textContent || '').then(() => {
        if (typeof showToast !== 'undefined') {
            showToast('Prompt copiado para a área de transferência!', 'success');
        }
    }).catch(() => {
        if (typeof showToast !== 'undefined') {
            showToast('Erro ao copiar', 'error');
        }
    });
}

/**
 * Escapa texto para uso em tooltip
 */
function escaparTextoParaTooltip(texto) {
    if (!texto) return 'N/A';
    
    return texto
        .replace(/&/g, '&amp;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/\n/g, ' ')
        .replace(/\r/g, ' ')
        .replace(/\t/g, ' ')
        .replace(/\s+/g, ' ')
        .trim()
        .substring(0, 500) + (texto.length > 500 ? '...' : '');
}

/**
 * Visualiza prompt combinado (regras originais + regras testadas)
 * 
 * O prompt combinado é gerado combinando:
 * - As regras de negócio originais do prompt base
 * - As regras adicionais testadas na etapa 4
 * - O contexto da intimação (se disponível)
 */
async function verPromptCombinado() {
    const { promptId } = window.wizardData;
    
    if (!promptId || !regrasTestadasAtual) {
        if (typeof showToast !== 'undefined') {
            showToast('Dados não disponíveis para gerar prompt combinado', 'error');
        }
        return;
    }
    
    try {
        // Buscar prompt base se ainda não foi carregado
        let promptBase = null;
        if (!promptBaseAtual) {
            try {
                const response = await fetch(`/api/prompts/${promptId}`);
                const data = await response.json();
                if (data.success && data.prompt) {
                    promptBase = data.prompt;
                    promptBaseAtual = promptBase;
                }
            } catch (error) {
                console.log('Prompt base não encontrado, usando template padrão');
            }
        } else {
            promptBase = promptBaseAtual;
        }
        
        // Preparar contexto da intimação
        const contexto = window.intimacaoData && window.intimacaoData.contexto
            ? `Contexto da Intimação:\n${window.intimacaoData.contexto}`
            : 'Contexto da Intimação não disponível';
        
        // Construir regras combinadas
        let regrasCombinadas = '';
        if (promptBase && promptBase.regra_negocio) {
            regrasCombinadas = `${promptBase.regra_negocio}\n\n=== REGRAS ADICIONAIS TESTADAS ===\n${regrasTestadasAtual}`;
        } else {
            regrasCombinadas = regrasTestadasAtual;
        }
        
        // Construir prompt final
        let promptFinal;
        if (promptBase && promptBase.conteudo) {
            // Usar prompt base como template
            promptFinal = promptBase.conteudo;
            // Substituir {REGRADENEGOCIO} pelas regras combinadas
            if (promptFinal.includes('{REGRADENEGOCIO}')) {
                promptFinal = promptFinal.replace('{REGRADENEGOCIO}', regrasCombinadas);
            }
            // Substituir {CONTEXTO}
            if (promptFinal.includes('{CONTEXTO}')) {
                promptFinal = promptFinal.replace('{CONTEXTO}', contexto);
            }
        } else {
            // Usar prompt padrão simples
            promptFinal = `Você é um especialista em análise jurídica da Defensoria Pública.

${regrasCombinadas}

${contexto}

Com base nas regras de negócio fornecidas e no contexto da intimação, classifique a ação necessária.

Responda apenas com uma das seguintes opções:
- RENUNCIAR_PRAZO
- OCULTAR
- ELABORAR_PECA
- CONTATAR_ASSISTIDO
- ANALISAR_PROCESSO
- ENCAMINHAR_INTIMACAO_PARA_OUTRO_DEFENSOR
- URGENCIA`;
        }
        
        // Mostrar modal com o prompt combinado
        mostrarModalPromptCombinado(promptFinal, regrasCombinadas);
        
    } catch (error) {
        console.error('Erro ao preparar prompt combinado:', error);
        if (typeof showToast !== 'undefined') {
            showToast('Erro ao preparar prompt combinado', 'error');
        }
    }
}

/**
 * Mostra modal com o prompt combinado
 */
function mostrarModalPromptCombinado(promptFinal, regrasCombinadas) {
    // Escapar HTML para segurança
    const escapeHtml = (text) => {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    };
    
    const modalHtml = `
        <div class="modal fade" id="modalPromptCombinado" tabindex="-1" aria-labelledby="modalPromptCombinadoLabel" aria-hidden="true">
            <div class="modal-dialog modal-xl">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title" id="modalPromptCombinadoLabel">
                            <i class="bi bi-file-text"></i>
                            Prompt Combinado - Regras Originais + Testadas
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        <div class="alert alert-info">
                            <h6><i class="bi bi-lightbulb"></i> Este prompt combina as regras originais do prompt com as regras testadas:</h6>
                        </div>
                        
                        <div class="mb-3">
                            <h6><i class="bi bi-gear"></i> Regras Combinadas:</h6>
                            <div class="bg-light p-3 rounded" style="max-height: 200px; overflow-y: auto;">
                                <pre style="white-space: pre-wrap; font-size: 0.9em; margin: 0;">${escapeHtml(regrasCombinadas)}</pre>
                            </div>
                        </div>
                        
                        <div class="mb-3">
                            <h6><i class="bi bi-file-text"></i> Prompt Completo:</h6>
                            <div class="bg-light p-3 rounded" style="max-height: 400px; overflow-y: auto;">
                                <pre id="prompt-combinado-conteudo" style="white-space: pre-wrap; font-size: 0.9em; margin: 0;">${escapeHtml(promptFinal)}</pre>
                            </div>
                        </div>
                        
                        <div class="row">
                            <div class="col-md-6">
                                <div class="card">
                                    <div class="card-header">
                                        <h6 class="mb-0"><i class="bi bi-info-circle"></i> Informações</h6>
                                    </div>
                                    <div class="card-body">
                                        <ul class="list-unstyled mb-0">
                                            <li><strong>Intimação:</strong> ${window.intimacaoData ? window.intimacaoData.id : 'N/A'}</li>
                                            <li><strong>Prompt Base:</strong> ${window.wizardData ? window.wizardData.promptNome : 'N/A'}</li>
                                            <li><strong>Total de caracteres:</strong> ${promptFinal.length}</li>
                                            <li><strong>Total de palavras:</strong> ${promptFinal.split(' ').length}</li>
                                            <li><strong>Total de linhas:</strong> ${promptFinal.split('\n').length}</li>
                                        </ul>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="card">
                                    <div class="card-header">
                                        <h6 class="mb-0"><i class="bi bi-check-circle"></i> Composição</h6>
                                    </div>
                                    <div class="card-body">
                                        <ul class="list-unstyled mb-0">
                                            <li><i class="bi bi-check text-success"></i> Regras originais do prompt</li>
                                            <li><i class="bi bi-check text-success"></i> Regras adicionais testadas</li>
                                            <li><i class="bi bi-check text-success"></i> Contexto da intimação</li>
                                            <li><i class="bi bi-check text-success"></i> Instruções de classificação</li>
                                        </ul>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-outline-secondary" onclick="copiarPromptCombinado()">
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
    const existingModal = document.getElementById('modalPromptCombinado');
    if (existingModal) {
        existingModal.remove();
    }
    
    // Adicionar novo modal
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    // Mostrar modal
    const modal = new bootstrap.Modal(document.getElementById('modalPromptCombinado'));
    modal.show();
}

/**
 * Copia o prompt combinado para a área de transferência
 */
function copiarPromptCombinado() {
    const promptContent = document.getElementById('prompt-combinado-conteudo');
    if (promptContent) {
        const texto = promptContent.textContent || promptContent.innerText;
        navigator.clipboard.writeText(texto).then(() => {
            if (typeof showToast !== 'undefined') {
                showToast('Prompt combinado copiado para a área de transferência!', 'success');
            }
        }).catch(err => {
            console.error('Erro ao copiar:', err);
            if (typeof showToast !== 'undefined') {
                showToast('Erro ao copiar prompt', 'error');
            }
        });
    }
}

/**
 * Abre a tela de criação de prompt com dados pré-preenchidos
 * 
 * Esta função:
 * 1. Pega as regras combinadas do teste
 * 2. Gera nome e descrição sugeridos
 * 3. Abre a página de criação de prompt com os dados pré-preenchidos
 *    (nome, descrição, regra_negocio - mas NÃO o conteúdo)
 */
async function criarNovoPromptComRegrasConsolidadas() {
    const { promptId, promptNome } = window.wizardData;
    
    if (!promptId || !regrasTestadasAtual) {
        if (typeof showToast !== 'undefined') {
            showToast('Dados não disponíveis para criar prompt', 'error');
        }
        return;
    }
    
    // Verificar se o teste combinado foi executado
    if (!window.wizardData.testeCombinado || !window.wizardData.testeCombinado.regrasCombinadas) {
        if (typeof showToast !== 'undefined') {
            showToast('Execute o teste combinado primeiro para obter as regras consolidadas', 'warning');
        }
        return;
    }
    
    const regrasCombinadas = window.wizardData.testeCombinado.regrasCombinadas;
    
    // Gerar nome sugerido
    const nomeSugerido = `${promptNome || 'Prompt'} - Refinado`;
    const descricaoSugerida = `Prompt refinado baseado em "${promptNome}" com regras consolidadas (originais + testadas). Criado através do wizard de análise.`;
    
    // Construir URL com parâmetros
    const params = new URLSearchParams({
        nome: nomeSugerido,
        descricao: descricaoSugerida,
        regra_negocio: regrasCombinadas
    });
    
    // Abrir página de criação de prompt em nova aba com dados pré-preenchidos
    window.open(`/prompts/novo?${params.toString()}`, '_blank');
}

// ===== INICIALIZAÇÃO =====

// Carregar configurações quando o script é carregado
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', carregarConfiguracoesAnalise);
} else {
    carregarConfiguracoesAnalise();
}
