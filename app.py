import os
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
from werkzeug.utils import secure_filename
import json
import uuid
from config import config
from services.data_service import DataService
from services.openai_service import OpenAIService
from services.export_service import ExportService

# Carregar variáveis de ambiente do arquivo .env
from dotenv import load_dotenv
load_dotenv()

# Inicializar serviços
data_service = DataService()
openai_service = OpenAIService()
export_service = ExportService()

# Criar aplicação Flask
app = Flask(__name__)
app.secret_key = 'sua_chave_secreta_aqui_mude_em_producao'

# Configurações padrão
DEFAULT_CONFIG = {
    'openai_api_key': '',
    'modelo_padrao': 'gpt-3.5-turbo',
    'temperatura_padrao': 0.7,
    'max_tokens_padrao': 150,
    'timeout_padrao': 30,
    'max_retries': 3,
    'retry_delay': 1,
    'itens_por_pagina': 25,
    'formato_data': 'DD/MM/YYYY',
    'tema': 'light',
    'idioma': 'pt-BR',
    'mostrar_tooltips': True,
    'animacoes': True,
    'sons_notificacao': False,
    'auto_save': True,
    'backup_automatico': 'weekly',
    'max_backups': 10,
    'diretorio_backup': './backups',
    'compressao_backup': 'zip',
    'log_level': 'INFO',
    'cache_size': 100,
    'max_concurrent': 5,
    'session_timeout': 60,
    'debug_mode': False,
    'log_requests': False,
    'cache_enabled': True
}

# Importar tipos de ação do config
from config import Config

def gerar_dados_graficos(analises, performance_prompts):
    """Gera dados para os gráficos baseados nas análises reais"""
    try:
        dados = {
            'acuracia_periodo': {'labels': [], 'data': []},
            'classificacoes_manuais': {'labels': [], 'data': []},
            'resultados_ia': {'labels': [], 'data': []},
            'performance_prompts': {'labels': [], 'acuracia': [], 'usos': []}
        }
        
        if not analises:
            print("=== DEBUG: Nenhuma análise encontrada ===")
            return dados
        
        print(f"=== DEBUG: Gerando dados para {len(analises)} análises ===")
        
        # 1. Acurácia por período (últimos 6 meses)
        hoje = datetime.now()
        meses = []
        acuracias_mes = {}
        
        for i in range(6):
            data = hoje - timedelta(days=30*i)
            mes_ano = data.strftime('%b/%Y')
            meses.insert(0, mes_ano)
            acuracias_mes[mes_ano] = {'total': 0, 'acertos': 0}
        
        for analise in analises:
            if analise.get('data_analise'):
                try:
                    data_analise = datetime.fromisoformat(analise['data_analise'].replace('Z', '+00:00'))
                    mes_ano = data_analise.strftime('%b/%Y')
                    if mes_ano in acuracias_mes:
                        acuracias_mes[mes_ano]['total'] += 1
                        if analise.get('acertou'):
                            acuracias_mes[mes_ano]['acertos'] += 1
                except:
                    pass
        
        dados['acuracia_periodo']['labels'] = meses
        dados['acuracia_periodo']['data'] = [
            round((acuracias_mes[mes]['acertos'] / acuracias_mes[mes]['total'] * 100) if acuracias_mes[mes]['total'] > 0 else 0, 1)
            for mes in meses
        ]
        
        # 2. Distribuição de classificações manuais
        dist_manual = {}
        for analise in analises:
            class_manual = analise.get('classificacao_manual', 'Não classificado')
            dist_manual[class_manual] = dist_manual.get(class_manual, 0) + 1
        
        dados['classificacoes_manuais']['labels'] = list(dist_manual.keys())
        dados['classificacoes_manuais']['data'] = list(dist_manual.values())
        
        # 3. Distribuição de resultados da IA
        dist_ia = {}
        for analise in analises:
            class_ia = analise.get('resultado_ia', 'Não classificado')
            dist_ia[class_ia] = dist_ia.get(class_ia, 0) + 1
        
        dados['resultados_ia']['labels'] = list(dist_ia.keys())
        dados['resultados_ia']['data'] = list(dist_ia.values())
        
        # 4. Performance por prompt
        if performance_prompts:
            dados['performance_prompts']['labels'] = list(performance_prompts.keys())
            dados['performance_prompts']['acuracia'] = [p['acuracia'] for p in performance_prompts.values()]
            dados['performance_prompts']['usos'] = [p['total'] for p in performance_prompts.values()]
        
        print(f"=== DEBUG: Dados gerados com sucesso ===")
        return dados
        
    except Exception as e:
        print(f"=== ERRO ao gerar dados dos gráficos: {e} ===")
        return {
            'acuracia_periodo': {'labels': [], 'data': []},
            'classificacoes_manuais': {'labels': [], 'data': []},
            'resultados_ia': {'labels': [], 'data': []},
            'performance_prompts': {'labels': [], 'acuracia': [], 'usos': []}
        }

@app.route('/')
def dashboard():
    """Página principal - Dashboard"""
    try:
        stats = data_service.get_statistics()
        
        # Dados para gráficos
        classificacoes_manuais = {}
        status_analises = {'Pendente': 0, 'Concluída': 0, 'Erro': 0}
        
        intimacoes = data_service.get_all_intimacoes()
        for intimacao in intimacoes:
            # Contar classificações manuais
            classificacao = intimacao.get('classificacao_manual', 'Não classificada')
            classificacoes_manuais[classificacao] = classificacoes_manuais.get(classificacao, 0) + 1
            
            # Contar status das análises
            if intimacao.get('analises'):
                status_analises['Concluída'] += len(intimacao['analises'])
            else:
                status_analises['Pendente'] += 1
        
        return render_template('dashboard.html', 
                             stats=stats,
                             total_intimacoes=stats.get('total_intimacoes', 0),
                             total_analises=stats.get('total_analises', 0),
                             taxa_acuracia=stats.get('taxa_acuracia_geral', 0),
                             prompts_ativos=stats.get('total_prompts', 0),
                             classificacoes_manuais=classificacoes_manuais,
                             status_analises=status_analises,
                             tipos_acao=Config.TIPOS_ACAO)
    except Exception as e:
        flash(f'Erro ao carregar dashboard: {str(e)}', 'error')
        return render_template('dashboard.html', 
                             stats={'total_intimacoes': 0, 'total_analises': 0, 'taxa_acuracia': 0, 'prompts_ativos': 0},
                             total_intimacoes=0,
                             total_analises=0,
                             taxa_acuracia=0,
                             prompts_ativos=0,
                             classificacoes_manuais={},
                             status_analises={'Pendente': 0, 'Concluída': 0, 'Erro': 0},
                             tipos_acao=Config.TIPOS_ACAO)

@app.route('/intimacoes')
def listar_intimacoes():
    """Página de listagem de intimações"""
    try:
        print("=== DEBUG: BOTÃO VER LISTA CLICADO ===")
        print(f"URL: {request.url}")
        print(f"Args: {dict(request.args)}")
        
        # Parâmetros de filtro e paginação
        pagina = int(request.args.get('pagina', 1))
        busca = request.args.get('busca', '')
        classificacao = request.args.get('classificacao', '')
        ordenacao = request.args.get('ordenacao', 'data_desc')
        
        print(f"DEBUG: Parâmetros - Página: {pagina}, Busca: '{busca}', Classificação: '{classificacao}', Ordenação: '{ordenacao}'")
        
        config = data_service.get_config()
        itens_por_pagina = config.get('itens_por_pagina', 25)
        print(f"DEBUG: Itens por página: {itens_por_pagina}")
        
        print("DEBUG: Carregando todas as intimações...")
        intimacoes = data_service.get_all_intimacoes()
        print(f"DEBUG: Total de intimações carregadas: {len(intimacoes)}")
        for i, intimacao in enumerate(intimacoes):
            print(f"  {i+1}. ID: {intimacao.get('id')} | Contexto: {intimacao.get('contexto')[:50]}...")
        
        # Aplicar filtros
        if busca:
            intimacoes = [i for i in intimacoes if busca.lower() in i.get('contexto', '').lower()]
            print(f"DEBUG: Após filtro de busca: {len(intimacoes)}")
        
        if classificacao:
            intimacoes = [i for i in intimacoes if i.get('classificacao_manual') == classificacao]
            print(f"DEBUG: Após filtro de classificação: {len(intimacoes)}")
        
        # Aplicar ordenação
        if ordenacao == 'data_desc':
            intimacoes.sort(key=lambda x: x.get('data_criacao', ''), reverse=True)
        elif ordenacao == 'data_asc':
            intimacoes.sort(key=lambda x: x.get('data_criacao', ''))
        elif ordenacao == 'classificacao':
            intimacoes.sort(key=lambda x: x.get('classificacao_manual', ''))
        
        # Paginação
        total_itens = len(intimacoes)
        inicio = (pagina - 1) * itens_por_pagina
        fim = inicio + itens_por_pagina
        intimacoes_pagina = intimacoes[inicio:fim]
        
        print(f"DEBUG: Paginação - Total: {total_itens}, Página: {pagina}, Início: {inicio}, Fim: {fim}")
        print(f"DEBUG: Intimações na página atual: {len(intimacoes_pagina)}")
        for i, intimacao in enumerate(intimacoes_pagina):
            print(f"  Página {i+1}: ID: {intimacao.get('id')} | Contexto: {intimacao.get('contexto')[:30]}...")
        
        total_paginas = (total_itens + itens_por_pagina - 1) // itens_por_pagina
        
        # Estatísticas rápidas
        stats = {
            'total': total_itens,
            'com_classificacao': len([i for i in intimacoes if i.get('classificacao_manual')]),
            'analisadas': len([i for i in intimacoes if i.get('analises')]),
            'pendentes': len([i for i in intimacoes if not i.get('analises')])
        }
        
        return render_template('intimacoes.html',
                             intimacoes=intimacoes_pagina,
                             pagina_atual=pagina,
                             total_paginas=total_paginas,
                             total_itens=total_itens,
                             stats=stats,
                             classificacoes=Config.TIPOS_ACAO,
                             tipos_acao=Config.TIPOS_ACAO,
                             filtros={'busca': busca, 'classificacao': classificacao, 'ordenacao': ordenacao})
    except Exception as e:
        flash(f'Erro ao carregar intimações: {str(e)}', 'error')
        return render_template('intimacoes.html',
                             intimacoes=[],
                             pagina_atual=1,
                             total_paginas=1,
                             total_itens=0,
                             stats={'total': 0, 'com_classificacao': 0, 'analisadas': 0, 'pendentes': 0},
                             classificacoes=Config.TIPOS_ACAO,
                             tipos_acao=Config.TIPOS_ACAO,
                             filtros={'busca': '', 'classificacao': '', 'ordenacao': 'data_desc'})

@app.route('/intimacoes/nova', methods=['GET', 'POST'])
def nova_intimacao():
    """Página para criar nova intimação"""
    if request.method == 'POST':
        try:
            print("=== DEBUG: BOTÃO SALVAR CLICADO ===")
            print(f"Form data completo: {dict(request.form)}")
            
            contexto = request.form.get('contexto', '').strip()
            classificacao_manual = request.form.get('classificacao_manual', '').strip()
            informacoes_adicionais = request.form.get('informacoes_adicionais', '').strip()
            
            print(f"Contexto extraído: '{contexto}'")
            print(f"Classificação extraída: '{classificacao_manual}'")
            print(f"Informações extraídas: '{informacoes_adicionais}'")
            
            if not contexto:
                print("DEBUG: Contexto vazio, retornando erro")
                flash('O contexto da intimação é obrigatório.', 'error')
                return render_template('nova_intimacao.html', 
                                     classificacoes=Config.TIPOS_ACAO,
                                     tipos_acao=Config.TIPOS_ACAO,
                                     dados={'contexto': contexto, 
                                           'classificacao_manual': classificacao_manual,
                                           'informacoes_adicionais': informacoes_adicionais})
            
            # Criar a intimação
            intimacao_data = {
                'contexto': contexto,
                'classificacao_manual': classificacao_manual if classificacao_manual else None,
                'informacoes_adicionais': informacoes_adicionais if informacoes_adicionais else None,
                'data_criacao': datetime.now().isoformat(),
                'analises': []
            }
            
            print(f"DEBUG: Dados da intimação preparados: {intimacao_data}")
            
            print("DEBUG: Chamando data_service.criar_intimacao...")
            intimacao_id = data_service.criar_intimacao(intimacao_data)
            print(f"DEBUG: Intimação criada com ID: {intimacao_id}")
            
            print("DEBUG: Verificando se a intimação foi realmente criada...")
            intimacao_criada = data_service.get_intimacao_by_id(intimacao_id)
            print(f"DEBUG: Intimação recuperada: {intimacao_criada}")
            
            flash('Intimação criada com sucesso!', 'success')
            print(f"DEBUG: Redirecionando para visualizar_intimacao com ID: {intimacao_id}")
            return redirect(url_for('visualizar_intimacao', id=intimacao_id))
            
        except Exception as e:
            flash(f'Erro ao criar intimação: {str(e)}', 'error')
            return render_template('nova_intimacao.html', 
                                 classificacoes=Config.TIPOS_ACAO,
                                 tipos_acao=Config.TIPOS_ACAO,
                                 dados={'contexto': request.form.get('contexto', ''), 
                                       'classificacao_manual': request.form.get('classificacao_manual', ''),
                                       'informacoes_adicionais': request.form.get('informacoes_adicionais', '')})
    
    return render_template('nova_intimacao.html', 
                         classificacoes=Config.TIPOS_ACAO,
                         tipos_acao=Config.TIPOS_ACAO,
                         dados={})

@app.route('/intimacoes/<id>')
def visualizar_intimacao(id):
    """Página para visualizar detalhes de uma intimação"""
    try:
        intimacao = data_service.get_intimacao_by_id(id)
        
        if not intimacao:
            flash('Intimação não encontrada.', 'error')
            return redirect(url_for('listar_intimacoes'))
        
        # Obter análises da intimação
        analises = intimacao.get('analises', [])
        
        # Calcular estatísticas
        stats = {
            'total_analises': len(analises),
            'acertos': len([a for a in analises if a.get('acuracia', 0) == 1]),
            'erros': len([a for a in analises if a.get('acuracia', 0) == 0]),
            'taxa_acuracia': 0,
            'tempo_medio': 0,
            'distribuicao_resultados': {}
        }
        
        if analises:
            stats['taxa_acuracia'] = round(stats['acertos'] / len(analises) * 100, 1)
            tempos = [a.get('tempo_processamento', 0) for a in analises if a.get('tempo_processamento')]
            if tempos:
                stats['tempo_medio'] = round(sum(tempos) / len(tempos), 2)
            
            # Distribuição de resultados da IA
            for analise in analises:
                resultado = analise.get('resultado_ia', 'Não classificado')
                stats['distribuicao_resultados'][resultado] = stats['distribuicao_resultados'].get(resultado, 0) + 1
        
        return render_template('visualizar_intimacao.html',
                             intimacao=intimacao,
                             analises=analises,
                             stats=stats,
                             classificacoes=Config.TIPOS_ACAO,
                             tipos_acao=Config.TIPOS_ACAO)
                             
    except Exception as e:
        flash(f'Erro ao carregar intimação: {str(e)}', 'error')
        return redirect(url_for('listar_intimacoes'))

@app.route('/prompts')
def listar_prompts():
    """Página de listagem de prompts"""
    try:
        # Parâmetros de filtro e paginação
        pagina = int(request.args.get('pagina', 1))
        busca = request.args.get('busca', '')
        tamanho = request.args.get('tamanho', '')
        ordenacao = request.args.get('ordenacao', 'data_desc')
        
        config = data_service.get_config()
        itens_por_pagina = config.get('itens_por_pagina', 25)
        
        prompts = data_service.get_all_prompts()
        
        # Aplicar filtros
        if busca:
            prompts = [p for p in prompts if busca.lower() in p.get('nome', '').lower() or 
                      busca.lower() in p.get('descricao', '').lower()]
        
        if tamanho:
            prompts = [p for p in prompts if (
                (tamanho == 'pequeno' and len(p.get('conteudo', '')) <= 500) or
                (tamanho == 'medio' and 500 < len(p.get('conteudo', '')) <= 2000) or
                (tamanho == 'grande' and len(p.get('conteudo', '')) > 2000)
            )]
        
        # Aplicar ordenação
        if ordenacao == 'data_desc':
            prompts.sort(key=lambda x: x.get('data_criacao', ''), reverse=True)
        elif ordenacao == 'data_asc':
            prompts.sort(key=lambda x: x.get('data_criacao', ''))
        elif ordenacao == 'nome':
            prompts.sort(key=lambda x: x.get('nome', ''))
        elif ordenacao == 'uso':
            prompts.sort(key=lambda x: x.get('total_usos', 0), reverse=True)
        
        # Paginação
        total_itens = len(prompts)
        inicio = (pagina - 1) * itens_por_pagina
        fim = inicio + itens_por_pagina
        prompts_pagina = prompts[inicio:fim]
        
        total_paginas = (total_itens + itens_por_pagina - 1) // itens_por_pagina
        
        # Estatísticas rápidas
        stats = {
            'total': total_itens,
            'pequenos': len([p for p in prompts if len(p.get('conteudo', '')) <= 500]),
            'medios': len([p for p in prompts if 500 < len(p.get('conteudo', '')) <= 2000]),
            'grandes': len([p for p in prompts if len(p.get('conteudo', '')) > 2000])
        }
        
        return render_template('prompts.html',
                             prompts=prompts_pagina,
                             pagina_atual=pagina,
                             total_paginas=total_paginas,
                             total_itens=total_itens,
                             stats=stats,
                             classificacoes=Config.TIPOS_ACAO,
                             filtros={'busca': busca, 'tamanho': tamanho, 'ordenacao': ordenacao})
    except Exception as e:
        flash(f'Erro ao carregar prompts: {str(e)}', 'error')
        return render_template('prompts.html',
                             prompts=[],
                             pagina_atual=1,
                             total_paginas=1,
                             total_itens=0,
                             stats={'total': 0, 'pequenos': 0, 'medios': 0, 'grandes': 0},
                             classificacoes=Config.TIPOS_ACAO,
                             filtros={'busca': '', 'tamanho': '', 'ordenacao': 'data_desc'})

@app.route('/prompts/novo', methods=['GET', 'POST'])
def novo_prompt():
    """Página para criar novo prompt"""
    if request.method == 'POST':
        try:
            nome = request.form.get('nome', '').strip()
            descricao = request.form.get('descricao', '').strip()
            conteudo = request.form.get('conteudo', '').strip()
            
            if not nome or not conteudo:
                flash('Nome e conteúdo do prompt são obrigatórios.', 'error')
                return render_template('novo_prompt.html',
                                     classificacoes=Config.TIPOS_ACAO,
                                     dados={'nome': nome, 'descricao': descricao, 'conteudo': conteudo})
            
            # Validar se o prompt contém a variável {CONTEXTO}
            if '{CONTEXTO}' not in conteudo:
                flash('O prompt deve conter a variável {CONTEXTO} para funcionar corretamente.', 'warning')
            
            # Criar o prompt
            prompt_data = {
                'nome': nome,
                'descricao': descricao if descricao else None,
                'conteudo': conteudo,
                'data_criacao': datetime.now().isoformat(),
                'total_usos': 0,
                'acuracia_media': 0,
                'tempo_medio': 0,
                'custo_total': 0,
                'historico_uso': []
            }
            
            prompt_id = data_service.criar_prompt(prompt_data)
            
            flash('Prompt criado com sucesso!', 'success')
            return redirect(url_for('visualizar_prompt', id=prompt_id))
            
        except Exception as e:
            flash(f'Erro ao criar prompt: {str(e)}', 'error')
            return render_template('novo_prompt.html',
                                 classificacoes=Config.TIPOS_ACAO,
                                 dados={'nome': request.form.get('nome', ''), 
                                       'descricao': request.form.get('descricao', ''),
                                       'conteudo': request.form.get('conteudo', '')})
    
    return render_template('novo_prompt.html',
                         classificacoes=Config.TIPOS_ACAO,
                         dados={})

@app.route('/prompts/<id>')
def visualizar_prompt(id):
    """Página para visualizar detalhes de um prompt"""
    try:
        prompt = data_service.get_prompt_by_id(id)
        if not prompt:
            flash('Prompt não encontrado.', 'error')
            return redirect(url_for('listar_prompts'))
        
        # Obter histórico de uso
        historico = prompt.get('historico_uso', [])
        
        # Calcular estatísticas
        stats = {
            'total_usos': len(historico),
            'acuracia_media': prompt.get('acuracia_media', 0),
            'tempo_medio': prompt.get('tempo_medio', 0),
            'custo_total': prompt.get('custo_total', 0),
            'distribuicao_resultados': {},
            'ultimos_usos': historico[-10:] if historico else []  # Últimos 10 usos
        }
        
        # Distribuição de resultados
        for uso in historico:
            resultado = uso.get('resultado_ia', 'Não classificado')
            stats['distribuicao_resultados'][resultado] = stats['distribuicao_resultados'].get(resultado, 0) + 1
        
        return render_template('visualizar_prompt.html',
                             prompt=prompt,
                             analises=historico,
                             stats=stats,
                             classificacoes=Config.TIPOS_ACAO)
                             
    except Exception as e:
        flash(f'Erro ao carregar prompt: {str(e)}', 'error')
        return redirect(url_for('listar_prompts'))

@app.route('/analise')
def analise():
    """Página para testar prompts com intimações"""
    try:
        prompts = data_service.get_all_prompts()
        intimacoes = data_service.get_all_intimacoes()
        config = data_service.get_config()
        
        # Adicionar informações de tamanho aos prompts
        for prompt in prompts:
            conteudo_len = len(prompt.get('conteudo', ''))
            if conteudo_len <= 500:
                prompt['tamanho'] = 'Pequeno'
            elif conteudo_len <= 2000:
                prompt['tamanho'] = 'Médio'
            else:
                prompt['tamanho'] = 'Grande'
        
        return render_template('analise.html',
                             prompts=prompts,
                             intimacoes=intimacoes,
                             classificacoes=Config.TIPOS_ACAO,
                             modelos_disponiveis=Config.OPENAI_MODELS,
                             modelo_padrao=config.get('modelo_padrao', 'gpt-4'),
                             temperatura_padrao=config.get('temperatura_padrao', 0.7),
                             max_tokens_padrao=config.get('max_tokens_padrao', 500))
    except Exception as e:
        flash(f'Erro ao carregar página de análise: {str(e)}', 'error')
        return render_template('analise.html',
                             prompts=[],
                             intimacoes=[],
                             classificacoes=Config.TIPOS_ACAO,
                             modelos_disponiveis=Config.OPENAI_MODELS,
                             modelo_padrao='gpt-4',
                             temperatura_padrao=0.7,
                             max_tokens_padrao=500)

@app.route('/executar-analise', methods=['POST'])
def executar_analise():
    """Executar análise de intimações com prompts selecionados"""
    try:
        print("=== DEBUG: executar_analise iniciada ===")
        data = request.get_json()
        print(f"=== DEBUG: Dados recebidos: {data} ===")
        
        prompt_id = data.get('prompt_id')
        intimacao_ids = data.get('intimacao_ids', [])
        configuracoes = data.get('configuracoes', {})
        
        if not prompt_id or not intimacao_ids:
            return jsonify({'error': 'Prompt e intimações são obrigatórios'}), 400
        
        print(f"=== DEBUG: Prompt ID: {prompt_id} ===")
        print(f"=== DEBUG: Intimação IDs: {intimacao_ids} ===")
        
        # Carregar configurações padrão
        config = data_service.get_config()
        
        # Configurações da OpenAI (usar configurações da página se fornecidas, senão usar padrões)
        modelo = configuracoes.get('modelo', config.get('modelo_padrao', 'gpt-4'))
        temperatura = float(configuracoes.get('temperatura', config.get('temperatura_padrao', 0.7)))
        max_tokens = int(configuracoes.get('max_tokens', config.get('max_tokens_padrao', 500)))
        salvar_resultados = configuracoes.get('salvar_resultados', True)
        calcular_acuracia = configuracoes.get('calcular_acuracia', True)
        
        print(f"=== DEBUG: Configurações - Modelo: {modelo}, Temp: {temperatura}, Tokens: {max_tokens} ===")
        
        resultados = []
        
        # Executar análises
        prompt = data_service.get_prompt_by_id(prompt_id)
        if not prompt:
            return jsonify({'error': 'Prompt não encontrado'}), 404
            
        print(f"=== DEBUG: Prompt encontrado: {prompt['nome']} ===")
            
        for intimacao_id in intimacao_ids:
            intimacao = data_service.get_intimacao_by_id(intimacao_id)
            if not intimacao:
                print(f"=== DEBUG: Intimação {intimacao_id} não encontrada ===")
                continue
                
            print(f"=== DEBUG: Analisando intimação {intimacao_id} ===")
            print(f"=== DEBUG: Classificação manual: {intimacao.get('classificacao_manual')} ===")
                
            try:
                # Preparar o prompt final
                contexto = f"""
                Contexto da Intimação:
                {intimacao['contexto']}
                """
                
                prompt_final = prompt['conteudo'].replace('{CONTEXTO}', contexto)
                
                print(f"=== DEBUG: Prompt final preparado (primeiros 200 chars): {prompt_final[:200]}... ===")
                
                # Usar serviço OpenAI real
                from services.openai_service import OpenAIService
                import time
                
                inicio = time.time()
                
                # Inicializar serviço OpenAI
                openai_service = OpenAIService()
                
                # Preparar parâmetros para a OpenAI
                parametros = {
                    'model': modelo,
                    'temperature': temperatura,
                    'max_tokens': max_tokens,
                    'top_p': 1.0  # Adicionar top_p padrão
                }
                
                print(f"=== DEBUG: Chamando OpenAI com parâmetros: {parametros} ===")
                print(f"=== DEBUG: Prompt final (primeiros 500 chars): {prompt_final[:500]}... ===")
                print(f"=== DEBUG: Prompt final (últimos 500 chars): ...{prompt_final[-500:]} ===")
                
                # Fazer chamada direta para OpenAI (prompt já construído)
                resposta_completa = openai_service._fazer_chamada_com_retry(
                    prompt_final,  # Prompt já construído com contexto
                    parametros
                )
                
                # Extrair classificação da resposta
                resultado_ia = openai_service._extrair_classificacao(resposta_completa)
                
                print(f"=== DEBUG: Resposta completa da OpenAI: {resposta_completa} ===")
                print(f"=== DEBUG: Classificação extraída: {resultado_ia} ===")
                
                tempo_processamento = time.time() - inicio
                
                # Calcular acurácia se possível
                acertou = False
                if calcular_acuracia and intimacao.get('classificacao_manual'):
                    # Normalizar para comparação (remover underscores e espaços)
                    classificacao_manual = intimacao['classificacao_manual'].upper().strip().replace('_', ' ').replace('-', ' ')
                    resultado_ia_normalizado = resultado_ia.upper().strip().replace('_', ' ').replace('-', ' ')
                    acertou = resultado_ia_normalizado == classificacao_manual
                    print(f"=== DEBUG: Comparação - Manual: {classificacao_manual}, IA: {resultado_ia_normalizado}, Acertou: {acertou} ===")
                
                # Calcular tokens e custo reais
                tokens_usados = len(prompt_final.split()) + len(resposta_completa.split())  # Estimativa simples
                custo_estimado = openai_service.estimate_cost(
                    prompt_length=len(prompt_final),
                    response_length=len(resposta_completa),
                    model=modelo
                )
                
                # Debug para verificar campos da intimação
                print(f"=== DEBUG: Campos da intimação {intimacao_id} ===")
                print(f"Campos disponíveis: {list(intimacao.keys())}")
                print(f"Informações adicionais: {intimacao.get('informacoes_adicionais')}")
                print(f"Informações adicionais (alt): {intimacao.get('informacao_adicional')}")
                
                resultado = {
                    'prompt_id': prompt_id,
                    'prompt_nome': prompt['nome'],
                    'intimacao_id': intimacao_id,
                    'contexto': intimacao['contexto'][:100] + '...' if len(intimacao['contexto']) > 100 else intimacao['contexto'],
                    'classificacao_manual': intimacao.get('classificacao_manual'),
                    'informacao_adicional': intimacao.get('informacoes_adicionais') or intimacao.get('informacao_adicional'),
                    'resultado_ia': resultado_ia,
                    'acertou': acertou,
                    'tempo_processamento': round(tempo_processamento, 3),
                    'modelo': modelo,
                    'temperatura': temperatura,
                    'tokens_usados': tokens_usados,
                    'custo_estimado': round(custo_estimado, 4),
                    'prompt_completo': prompt_final,
                    'resposta_completa': resposta_completa
                }
                
                resultados.append(resultado)
                print(f"=== DEBUG: Resultado adicionado: {resultado} ===")
                
                # Salvar resultado se solicitado
                if salvar_resultados:
                    # Adicionar análise à intimação
                    analise_data = {
                        'data_analise': datetime.now().isoformat(),
                        'prompt_id': prompt_id,
                        'prompt_nome': prompt['nome'],
                        'resultado_ia': resultado_ia,
                        'acertou': acertou,
                        'tempo_processamento': tempo_processamento,
                        'modelo': modelo,
                        'temperatura': temperatura,
                        'tokens_usados': resultado['tokens_usados'],
                        'custo_estimado': resultado['custo_estimado'],
                        'prompt_completo': prompt_final,
                        'resposta_completa': resposta_completa
                    }
                    
                    data_service.adicionar_analise_intimacao(intimacao_id, analise_data)
                    data_service.adicionar_uso_prompt(prompt_id, analise_data)
                    print(f"=== DEBUG: Resultado salvo no banco ===")
                
            except Exception as e:
                print(f"=== ERRO ao analisar intimação {intimacao_id}: {e} ===")
                resultado = {
                    'prompt_id': prompt_id,
                    'prompt_nome': prompt['nome'],
                    'intimacao_id': intimacao_id,
                    'erro': str(e)
                }
                resultados.append(resultado)
        
        # Calcular estatísticas gerais
        total_analises = len([r for r in resultados if 'erro' not in r])
        acertos = len([r for r in resultados if r.get('acertou') == True])
        erros = len([r for r in resultados if r.get('acertou') == False])
        tempo_total = sum([r.get('tempo_processamento', 0) for r in resultados if 'erro' not in r])
        custo_total = sum([r.get('custo_estimado', 0) for r in resultados if 'erro' not in r])
        
        estatisticas = {
            'total_analises': total_analises,
            'acertos': acertos,
            'erros': erros,
            'taxa_acuracia': round(acertos / total_analises * 100, 1) if total_analises > 0 else 0,
            'tempo_total': round(tempo_total, 3),
            'tempo_medio': round(tempo_total / total_analises, 3) if total_analises > 0 else 0,
            'custo_total': round(custo_total, 4),
            'custo_medio': round(custo_total / total_analises, 4) if total_analises > 0 else 0
        }
        
        return jsonify({
            'success': True,
            'resultados': resultados,
            'estatisticas': estatisticas
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/relatorios')
def relatorios():
    """Página de relatórios e estatísticas"""
    try:
        # Parâmetros de filtro
        data_inicio = request.args.get('data_inicio', '')
        data_fim = request.args.get('data_fim', '')
        prompt_id = request.args.get('prompt_id', '')
        classificacao = request.args.get('classificacao', '')
        
        # Obter dados
        intimacoes = data_service.get_all_intimacoes()
        prompts = data_service.get_all_prompts()
        
        # Coletar todas as análises
        todas_analises = []
        for intimacao in intimacoes:
            for analise in intimacao.get('analises', []):
                analise['intimacao_id'] = intimacao['id']
                analise['contexto'] = intimacao['contexto']
                analise['classificacao_manual'] = intimacao.get('classificacao_manual')
                analise['informacao_adicional'] = intimacao.get('informacoes_adicionais')
                # Garantir que os campos de prompt e resposta completos estejam presentes
                analise['prompt_completo'] = analise.get('prompt_completo', 'N/A')
                analise['resposta_completa'] = analise.get('resposta_completa', 'N/A')
                todas_analises.append(analise)
        
        # Aplicar filtros
        analises_filtradas = todas_analises
        
        if data_inicio:
            analises_filtradas = [a for a in analises_filtradas if a.get('data_analise', '') >= data_inicio]
        
        if data_fim:
            analises_filtradas = [a for a in analises_filtradas if a.get('data_analise', '') <= data_fim]
        
        if prompt_id:
            analises_filtradas = [a for a in analises_filtradas if a.get('prompt_id') == prompt_id]
        
        if classificacao:
            analises_filtradas = [a for a in analises_filtradas if a.get('classificacao_manual') == classificacao]
        
        # Calcular métricas principais
        total_intimacoes = len(intimacoes)
        total_analises = len(analises_filtradas)
        total_prompts = len(prompts)
        
        acertos = len([a for a in analises_filtradas if a.get('acertou') == True])
        acuracia_geral = round(acertos / total_analises * 100, 1) if total_analises > 0 else 0
        
        # Distribuição de classificações
        dist_manual = {}
        dist_ia = {}
        
        for analise in analises_filtradas:
            # Classificação manual
            class_manual = analise.get('classificacao_manual', 'Não classificado')
            dist_manual[class_manual] = dist_manual.get(class_manual, 0) + 1
            
            # Classificação da IA
            class_ia = analise.get('resultado_ia', 'Não classificado')
            dist_ia[class_ia] = dist_ia.get(class_ia, 0) + 1
        
        # Performance por prompt
        performance_prompts = {}
        for analise in analises_filtradas:
            prompt_nome = analise.get('prompt_nome', 'Desconhecido')
            if prompt_nome not in performance_prompts:
                performance_prompts[prompt_nome] = {'total': 0, 'acertos': 0, 'tempo_total': 0}
            
            performance_prompts[prompt_nome]['total'] += 1
            if analise.get('acertou') == True:
                performance_prompts[prompt_nome]['acertos'] += 1
            performance_prompts[prompt_nome]['tempo_total'] += analise.get('tempo_processamento', 0)
        
        # Calcular acurácia por prompt
        for prompt_nome in performance_prompts:
            data = performance_prompts[prompt_nome]
            data['acuracia'] = round(data['acertos'] / data['total'] * 100, 1) if data['total'] > 0 else 0
            data['tempo_medio'] = round(data['tempo_total'] / data['total'], 3) if data['total'] > 0 else 0
        
        # Top 5 prompts por acurácia
        top_prompts = sorted(performance_prompts.items(), key=lambda x: x[1]['acuracia'], reverse=True)[:5]
        
        # Paginação das análises
        pagina = int(request.args.get('pagina', 1))
        itens_por_pagina = int(request.args.get('itens_por_pagina', 10))
        
        total_analises_filtradas = len(analises_filtradas)
        inicio = (pagina - 1) * itens_por_pagina
        fim = inicio + itens_por_pagina
        
        # Garantir que não ultrapasse os limites
        if inicio >= total_analises_filtradas and total_analises_filtradas > 0:
            # Se a página solicitada não existe, redirecionar para página 1
            return redirect(url_for('relatorios', **{k: v for k, v in request.args.items() if k != 'pagina'}))
        
        analises_paginadas = analises_filtradas[inicio:fim]
        
        # Calcular informações de paginação
        total_paginas = max(1, (total_analises_filtradas + itens_por_pagina - 1) // itens_por_pagina)
        paginacao = {
            'pagina_atual': pagina,
            'total_paginas': total_paginas,
            'itens_por_pagina': itens_por_pagina,
            'total_itens': total_analises_filtradas,
            'inicio': inicio + 1 if total_analises_filtradas > 0 else 0,
            'fim': min(fim, total_analises_filtradas)
        }
        
        # Gerar dados para gráficos
        dados_graficos = gerar_dados_graficos(analises_filtradas, performance_prompts)
        print(f"=== DEBUG: Dados dos gráficos gerados ===")
        print(f"Análises filtradas: {len(analises_filtradas)}")
        if analises_filtradas:
            print(f"=== DEBUG: Primeira análise - modelo: {analises_filtradas[0].get('modelo')}, temperatura: {analises_filtradas[0].get('temperatura')} ===")
            # Debug para verificar dados de prompt e resposta
            primeira_analise = analises_filtradas[0]
            print(f"=== DEBUG: Primeira análise - prompt_completo length: {len(str(primeira_analise.get('prompt_completo', '')))}")
            print(f"=== DEBUG: Primeira análise - resposta_completa length: {len(str(primeira_analise.get('resposta_completa', '')))}")
        print(f"Dados gráficos: {dados_graficos}")
        # Debug para verificar se há caracteres especiais
        import json
        try:
            json_str = json.dumps(dados_graficos, ensure_ascii=False)
            print(f"JSON válido gerado com sucesso, tamanho: {len(json_str)}")
        except Exception as e:
            print(f"ERRO ao gerar JSON: {e}")
        
        # Estatísticas rápidas
        tempo_total = sum([a.get('tempo_processamento', 0) for a in analises_filtradas])
        custo_total = sum([a.get('custo_estimado', 0) for a in analises_filtradas])
        
        stats = {
            'acertos': acertos,
            'erros': total_analises - acertos,
            'tempo_medio': round(tempo_total / total_analises, 3) if total_analises > 0 else 0,
            'custo_total': round(custo_total, 4),
            'analises_hoje': len([a for a in analises_filtradas if a.get('data_analise', '').startswith(datetime.now().strftime('%Y-%m-%d'))]),
            'prompt_mais_usado': max(performance_prompts.items(), key=lambda x: x[1]['total'])[0] if performance_prompts else 'Nenhum',
            'melhor_acuracia': max(performance_prompts.items(), key=lambda x: x[1]['acuracia'])[1]['acuracia'] if performance_prompts else 0
        }
        
        return render_template('relatorios.html',
                             total_intimacoes=total_intimacoes,
                             total_analises=total_analises,
                             total_prompts=total_prompts,
                             acuracia_geral=acuracia_geral,
                             distribuicao_manual=dist_manual,
                             distribuicao_ia=dist_ia,
                             performance_prompts=performance_prompts,
                             top_prompts=top_prompts,
                             stats=stats,
                             estatisticas=stats,
                             prompts=prompts,
                             classificacoes=Config.TIPOS_ACAO,
                             filtros={'data_inicio': data_inicio, 'data_fim': data_fim, 'prompt_id': prompt_id, 'classificacao': classificacao},
                             analises=analises_paginadas,
                             paginacao=paginacao,
                             dados_graficos=dados_graficos)
                             
    except Exception as e:
        flash(f'Erro ao carregar relatórios: {str(e)}', 'error')
        return render_template('relatorios.html',
                             total_intimacoes=0,
                             total_analises=0,
                             total_prompts=0,
                             acuracia_geral=0,
                             distribuicao_manual={},
                             distribuicao_ia={},
                             performance_prompts={},
                             top_prompts=[],
                             stats={},
                             estatisticas={},
                             prompts=[],
                             classificacoes=Config.TIPOS_ACAO,
                                                           filtros={'data_inicio': '', 'data_fim': '', 'prompt_id': '', 'classificacao': ''},
                              analises=[],
                              paginacao={'pagina_atual': 1, 'total_paginas': 1, 'itens_por_pagina': 10, 'total_itens': 0, 'inicio': 0, 'fim': 0},
                              dados_graficos={'acuracia_periodo': {'labels': [], 'data': []}, 'classificacoes_manuais': {'labels': [], 'data': []}, 'resultados_ia': {'labels': [], 'data': []}, 'performance_prompts': {'labels': [], 'acuracia': [], 'usos': []}})

@app.route('/api/relatorios/pagina/<int:pagina>')
def api_relatorios_pagina(pagina):
    """API para carregar dados de uma página específica via AJAX"""
    try:
        # Parâmetros de filtro
        data_inicio = request.args.get('data_inicio', '')
        data_fim = request.args.get('data_fim', '')
        prompt_id = request.args.get('prompt_id', '')
        classificacao = request.args.get('classificacao', '')
        itens_por_pagina = int(request.args.get('itens_por_pagina', 10))
        
        # Obter dados
        intimacoes = data_service.get_all_intimacoes()
        
        # Coletar todas as análises
        todas_analises = []
        for intimacao in intimacoes:
            for analise in intimacao.get('analises', []):
                analise['intimacao_id'] = intimacao['id']
                analise['contexto'] = intimacao['contexto']
                analise['classificacao_manual'] = intimacao.get('classificacao_manual')
                analise['informacao_adicional'] = intimacao.get('informacoes_adicionais')
                # Garantir que os campos de prompt e resposta completos estejam presentes
                analise['prompt_completo'] = analise.get('prompt_completo', 'N/A')
                analise['resposta_completa'] = analise.get('resposta_completa', 'N/A')
                todas_analises.append(analise)
        
        # Aplicar filtros
        analises_filtradas = todas_analises
        
        if data_inicio:
            analises_filtradas = [a for a in analises_filtradas if a.get('data_analise', '') >= data_inicio]
        
        if data_fim:
            analises_filtradas = [a for a in analises_filtradas if a.get('data_analise', '') <= data_fim]
        
        if prompt_id:
            analises_filtradas = [a for a in analises_filtradas if a.get('prompt_id') == prompt_id]
        
        if classificacao:
            analises_filtradas = [a for a in analises_filtradas if a.get('classificacao_manual') == classificacao]
        
        # Paginação
        total_analises_filtradas = len(analises_filtradas)
        inicio = (pagina - 1) * itens_por_pagina
        fim = inicio + itens_por_pagina
        
        # Garantir que não ultrapasse os limites
        if inicio >= total_analises_filtradas and total_analises_filtradas > 0:
            return jsonify({'error': 'Página não encontrada'}), 404
        
        analises_paginadas = analises_filtradas[inicio:fim]
        
        # Calcular informações de paginação
        total_paginas = max(1, (total_analises_filtradas + itens_por_pagina - 1) // itens_por_pagina)
        paginacao = {
            'pagina_atual': pagina,
            'total_paginas': total_paginas,
            'itens_por_pagina': itens_por_pagina,
            'total_itens': total_analises_filtradas,
            'inicio': inicio + 1 if total_analises_filtradas > 0 else 0,
            'fim': min(fim, total_analises_filtradas)
        }
        
        # Renderizar apenas a tabela e paginação
        html_tabela = render_template('partials/tabela_analises.html',
                                     analises=analises_paginadas,
                                     paginacao=paginacao)
        
        return jsonify({
            'success': True,
            'html': html_tabela,
            'paginacao': paginacao
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/exportar')
def exportar_dados():
    """Exportar dados em diferentes formatos"""
    try:
        formato = request.args.get('formato', 'csv')
        tipo = request.args.get('tipo', 'analises')
        
        # Parâmetros de filtro para análises
        data_inicio = request.args.get('data_inicio', '')
        data_fim = request.args.get('data_fim', '')
        prompt_id = request.args.get('prompt_id', '')
        classificacao = request.args.get('classificacao', '')
        
        if tipo == 'intimacoes':
            dados = data_service.get_all_intimacoes()
            filename = f'intimacoes_{datetime.now().strftime("%Y%m%d_%H%M%S")}.{formato}'
        elif tipo == 'prompts':
            dados = data_service.get_all_prompts()
            filename = f'prompts_{datetime.now().strftime("%Y%m%d_%H%M%S")}.{formato}'
        elif tipo == 'analises':
            # Coletar todas as análises
            intimacoes = data_service.get_all_intimacoes()
            todas_analises = []
            for intimacao in intimacoes:
                for analise in intimacao.get('analises', []):
                    analise['intimacao_id'] = intimacao['id']
                    analise['contexto'] = intimacao['contexto']
                    analise['classificacao_manual'] = intimacao.get('classificacao_manual')
                    analise['informacao_adicional'] = intimacao.get('informacoes_adicionais')
                    # Garantir que os campos de prompt e resposta completos estejam presentes
                    analise['prompt_completo'] = analise.get('prompt_completo', 'N/A')
                    analise['resposta_completa'] = analise.get('resposta_completa', 'N/A')
                    todas_analises.append(analise)
            
            # Aplicar filtros
            dados = todas_analises
            
            if data_inicio:
                dados = [a for a in dados if a.get('data_analise', '') >= data_inicio]
            
            if data_fim:
                dados = [a for a in dados if a.get('data_analise', '') <= data_fim]
            
            if prompt_id:
                dados = [a for a in dados if a.get('prompt_id') == prompt_id]
            
            if classificacao:
                dados = [a for a in dados if a.get('classificacao_manual') == classificacao]
            
            filename = f'analises_{datetime.now().strftime("%Y%m%d_%H%M%S")}.{formato}'
        else:
            return jsonify({'error': 'Tipo de dados inválido'}), 400
        
        # Gerar CSV diretamente se for formato CSV
        if formato == 'csv' and tipo == 'analises':
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Cabeçalho
            writer.writerow([
                'Data', 'Intimação ID', 'Contexto', 'Prompt', 'Classificação Manual',
                'Resultado IA', 'Acertou', 'Modelo', 'Temperatura', 'Tempo (s)', 'Custo ($)'
            ])
            
            # Dados
            for analise in dados:
                # Formatar data
                data_formatada = ''
                if analise.get('data_analise'):
                    try:
                        data = datetime.fromisoformat(analise['data_analise'].replace('Z', '+00:00'))
                        data_formatada = data.strftime('%d/%m/%Y %H:%M:%S')
                    except:
                        data_formatada = analise['data_analise']
                
                writer.writerow([
                    data_formatada,
                    analise.get('intimacao_id', '')[:8] + '...',
                    analise.get('contexto', '')[:100] + ('...' if len(analise.get('contexto', '')) > 100 else ''),
                    analise.get('prompt_nome', ''),
                    analise.get('classificacao_manual', ''),
                    analise.get('resultado_ia', ''),
                    'Sim' if analise.get('acertou') else 'Não',
                    analise.get('modelo', ''),
                    f"{analise.get('temperatura', 0):.1f}" if analise.get('temperatura') is not None else 'N/A',
                    f"{analise.get('tempo_processamento', 0):.3f}",
                    f"{analise.get('custo_estimado', 0):.4f}"
                ])
            
            output.seek(0)
            return send_file(
                io.BytesIO(output.getvalue().encode('utf-8')),
                mimetype='text/csv',
                as_attachment=True,
                download_name=filename
            )
        else:
            # Usar o export_service para outros formatos
            arquivo_path = export_service.exportar(dados, formato, filename)
            
            if arquivo_path:
                return send_file(arquivo_path, as_attachment=True, download_name=filename)
            else:
                return jsonify({'error': 'Erro ao gerar arquivo de exportação'}), 500
            
    except Exception as e:
        print(f"=== ERRO na exportação: {e} ===")
        return jsonify({'error': f'Erro ao exportar dados: {str(e)}'}), 500

@app.route('/configuracoes', methods=['GET', 'POST'])
def configuracoes():
    """Página de configurações do sistema"""
    if request.method == 'POST':
        try:
            # Processar dados do formulário
            config_data = {
                # Chave da API vem da variável de ambiente (.env)
                'modelo_padrao': request.form.get('modelo_padrao', 'gpt-4'),
                'temperatura_padrao': float(request.form.get('temperatura_padrao', 0.7)),
                'max_tokens_padrao': int(request.form.get('max_tokens_padrao', 500)),
                'timeout_padrao': int(request.form.get('timeout_padrao', 30)),
                'max_retries': int(request.form.get('max_retries', 3)),
                'retry_delay': int(request.form.get('retry_delay', 1)),
                'itens_por_pagina': int(request.form.get('itens_por_pagina', 25)),
                'formato_data': request.form.get('formato_data', 'DD/MM/YYYY'),
                'tema': request.form.get('tema', 'light'),
                'idioma': request.form.get('idioma', 'pt-BR'),
                'mostrar_tooltips': request.form.get('mostrar_tooltips') == 'on',
                'animacoes': request.form.get('animacoes') == 'on',
                'sons_notificacao': request.form.get('sons_notificacao') == 'on',
                'auto_save': request.form.get('auto_save') == 'on',
                'backup_automatico': request.form.get('backup_automatico', 'weekly'),
                'max_backups': int(request.form.get('max_backups', 10)),
                'diretorio_backup': request.form.get('diretorio_backup', './backups'),
                'compressao_backup': request.form.get('compressao_backup', 'zip'),
                'log_level': request.form.get('log_level', 'INFO'),
                'cache_size': int(request.form.get('cache_size', 100)),
                'max_concurrent': int(request.form.get('max_concurrent', 5)),
                'session_timeout': int(request.form.get('session_timeout', 60)),
                'debug_mode': request.form.get('debug_mode') == 'on',
                'log_requests': request.form.get('log_requests') == 'on',
                'cache_enabled': request.form.get('cache_enabled') == 'on'
            }
            
            data_service.save_config(config_data)
            flash('Configurações salvas com sucesso!', 'success')
            
        except Exception as e:
            flash(f'Erro ao salvar configurações: {str(e)}', 'error')
    
    try:
        # Carregar configurações
        config = data_service.get_config()
        
        # Garantir valores padrão se não existirem
        if not config:
            config = {}
        
        # Buscar chave da API da variável de ambiente
        config['openai_api_key'] = os.environ.get('OPENAI_API_KEY', '')
        
        # Debug: verificar se a chave está sendo passada
        print(f"=== DEBUG: Chave da API para interface: {config['openai_api_key'][:20]}... ===")
        
        # Valores padrão para configurações
        config.setdefault('modelo_padrao', 'gpt-4')
        config.setdefault('temperatura_padrao', 0.7)
        config.setdefault('max_tokens_padrao', 500)
        config.setdefault('timeout_padrao', 30)
        config.setdefault('max_retries', 3)
        config.setdefault('retry_delay', 1)
        config.setdefault('itens_por_pagina', 25)
        config.setdefault('formato_data', 'DD/MM/YYYY')
        config.setdefault('tema', 'light')
        config.setdefault('idioma', 'pt-BR')
        config.setdefault('mostrar_tooltips', True)
        config.setdefault('animacoes', True)
        config.setdefault('sons_notificacao', False)
        config.setdefault('auto_save', True)
        config.setdefault('backup_automatico', 'weekly')
        config.setdefault('max_backups', 10)
        config.setdefault('diretorio_backup', './backups')
        config.setdefault('compressao_backup', 'zip')
        config.setdefault('log_level', 'INFO')
        config.setdefault('cache_size', 100)
        config.setdefault('max_concurrent', 5)
        config.setdefault('session_timeout', 60)
        config.setdefault('debug_mode', False)
        config.setdefault('log_requests', False)
        config.setdefault('cache_enabled', True)
        
        # Status do sistema
        status_sistema = {
            'versao': '1.0.0',
            'uptime': '2 horas, 15 minutos',
            'memoria_usada': '45.2 MB',
            'espaco_disco': '2.1 GB disponível',
            'ultima_backup': '2024-01-15 10:30:00',
            'conexao_openai': 'Conectado'
        }
        
        # Uso da API
        uso_api = {
            'requisicoes_hoje': 127,
            'tokens_usados': 15420,
            'custo_estimado': 0.23,
            'limite_mensal': 10000,
            'percentual_usado': 15.4
        }
        
        # Logs recentes (simulados)
        logs_recentes = [
            {'timestamp': '2024-01-15 14:30:15', 'nivel': 'INFO', 'mensagem': 'Análise executada com sucesso'},
            {'timestamp': '2024-01-15 14:25:10', 'nivel': 'INFO', 'mensagem': 'Nova intimação criada'},
            {'timestamp': '2024-01-15 14:20:05', 'nivel': 'WARNING', 'mensagem': 'Cache próximo do limite'},
            {'timestamp': '2024-01-15 14:15:00', 'nivel': 'INFO', 'mensagem': 'Backup automático realizado'}
        ]
        
        return render_template('configuracoes.html',
                             config=config,
                             modelos_disponiveis=Config.OPENAI_MODELS,
                             status_sistema=status_sistema,
                             uso_api=uso_api,
                             logs_recentes=logs_recentes)
                             
    except Exception as e:
        flash(f'Erro ao carregar configurações: {str(e)}', 'error')
        return render_template('configuracoes.html',
                             config=DEFAULT_CONFIG,
                             modelos_disponiveis=Config.OPENAI_MODELS,
                             status_sistema={},
                             uso_api={},
                             logs_recentes=[])

# Rotas auxiliares e APIs

@app.route('/api/intimacoes/<id>/excluir', methods=['DELETE'])
def excluir_intimacao(id):
    """API para excluir uma intimação"""
    print(f"=== DEBUG: EXCLUINDO INTIMAÇÃO ===")
    print(f"ID da intimação: {id}")
    
    try:
        # Verificar se a intimação existe antes de excluir
        intimacao = data_service.get_intimacao_by_id(id)
        if not intimacao:
            print(f"DEBUG: Intimação {id} não encontrada")
            return jsonify({'success': False, 'message': 'Intimação não encontrada'}), 404
        
        print(f"DEBUG: Intimação encontrada: {intimacao.get('contexto', '')[:50]}...")
        
        # Excluir análises relacionadas primeiro
        analises = data_service.get_analises_by_intimacao_id(id)
        print(f"DEBUG: Excluindo {len(analises)} análises relacionadas")
        for analise in analises:
            data_service.delete_analise(analise['id'])
        
        # Excluir a intimação
        sucesso = data_service.delete_intimacao(id)
        if sucesso:
            print(f"DEBUG: Intimação {id} excluída com sucesso")
            return jsonify({'success': True, 'message': 'Intimação excluída com sucesso'})
        else:
            print(f"DEBUG: Erro ao excluir intimação {id}")
            return jsonify({'success': False, 'message': 'Erro ao excluir intimação'}), 500
    except Exception as e:
        print(f"DEBUG: Exceção ao excluir intimação: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/analises/excluir', methods=['DELETE'])
def excluir_analise():
    """Excluir análise específica"""
    try:
        data = request.get_json()
        intimacao_id = data.get('intimacao_id')
        analise_id = data.get('analise_id')
        
        if not intimacao_id or not analise_id:
            return jsonify({'error': 'ID da intimação e da análise são obrigatórios'}), 400
        
        print(f"=== DEBUG: Excluindo análise {analise_id} da intimação {intimacao_id} ===")
        
        # Buscar a intimação
        intimacoes = data_service.get_all_intimacoes()
        intimacao = next((i for i in intimacoes if i['id'] == intimacao_id), None)
        
        if not intimacao:
            return jsonify({'error': 'Intimação não encontrada'}), 404
        
        # Remover a análise específica
        analises = intimacao.get('analises', [])
        analise_encontrada = next((a for a in analises if a.get('id') == analise_id), None)
        
        if not analise_encontrada:
            return jsonify({'error': 'Análise não encontrada'}), 404
        
        # Remover a análise
        analises.remove(analise_encontrada)
        intimacao['analises'] = analises
        
        # Salvar a intimação atualizada
        data_service.save_intimacao(intimacao)
        
        print(f"=== DEBUG: Análise {analise_id} excluída com sucesso ===")
        
        return jsonify({'success': True, 'message': 'Análise excluída com sucesso'})
        
    except Exception as e:
        print(f"=== ERRO ao excluir análise: {e} ===")
        return jsonify({'error': str(e)}), 500

@app.route('/api/prompts/<id>/excluir', methods=['DELETE'])
def excluir_prompt(id):
    """API para excluir um prompt"""
    print(f"=== DEBUG: EXCLUINDO PROMPT ===")
    print(f"ID do prompt: {id}")
    
    try:
        # Verificar se o prompt existe antes de excluir
        prompt = data_service.get_prompt_by_id(id)
        if not prompt:
            print(f"DEBUG: Prompt {id} não encontrado")
            return jsonify({'success': False, 'message': 'Prompt não encontrado'}), 404
        
        print(f"DEBUG: Prompt encontrado: {prompt.get('nome', '')}")
        
        # Excluir análises relacionadas primeiro
        analises = data_service.get_analises_by_prompt_id(id)
        print(f"DEBUG: Excluindo {len(analises)} análises relacionadas")
        for analise in analises:
            data_service.delete_analise(analise['id'])
        
        # Excluir o prompt
        sucesso = data_service.delete_prompt(id)
        if sucesso:
            print(f"DEBUG: Prompt {id} excluído com sucesso")
            return jsonify({'success': True, 'message': 'Prompt excluído com sucesso'})
        else:
            print(f"DEBUG: Erro ao excluir prompt {id}")
            return jsonify({'success': False, 'message': 'Erro ao excluir prompt'}), 500
    except Exception as e:
        print(f"DEBUG: Exceção ao excluir prompt: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/prompts/<id>/duplicar', methods=['POST'])
def duplicar_prompt(id):
    """API para duplicar um prompt"""
    try:
        prompt_original = data_service.get_prompt_by_id(id)
        if not prompt_original:
            return jsonify({'success': False, 'message': 'Prompt não encontrado'}), 404
        
        # Criar cópia do prompt
        prompt_copia = prompt_original.copy()
        prompt_copia['nome'] = f"{prompt_original['nome']} (Cópia)"
        prompt_copia['data_criacao'] = datetime.now().isoformat()
        prompt_copia['total_usos'] = 0
        prompt_copia['acuracia_media'] = 0
        prompt_copia['tempo_medio'] = 0
        prompt_copia['custo_total'] = 0
        prompt_copia['historico_uso'] = []
        
        novo_id = data_service.criar_prompt(prompt_copia)
        
        return jsonify({
            'success': True, 
            'message': 'Prompt duplicado com sucesso',
            'novo_id': novo_id
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/configuracoes/testar-conexao', methods=['POST'])
def testar_conexao_openai():
    """API para testar conexão com OpenAI"""
    try:
        # Simular teste de conexão
        import time
        time.sleep(1)  # Simular delay de rede
        
        # Aqui seria implementado o teste real com a API da OpenAI
        return jsonify({
            'success': True,
            'message': 'Conexão com OpenAI estabelecida com sucesso',
            'latencia': '245ms',
            'modelo_disponivel': 'gpt-3.5-turbo'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro ao conectar com OpenAI: {str(e)}'
        }), 500

@app.route('/api/backup/criar', methods=['POST'])
def criar_backup():
    """API para criar backup manual"""
    try:
        # Simular criação de backup
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_nome = f'backup_manual_{timestamp}.zip'
        
        return jsonify({
            'success': True,
            'message': 'Backup criado com sucesso',
            'arquivo': backup_nome,
            'tamanho': '2.3 MB'
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/sistema/limpar-cache', methods=['POST'])
def limpar_cache():
    """API para limpar cache do sistema"""
    try:
        # Simular limpeza de cache
        return jsonify({
            'success': True,
            'message': 'Cache limpo com sucesso',
            'espaco_liberado': '15.2 MB'
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# Manipuladores de erro
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

if __name__ == '__main__':
    # Criar diretórios necessários
    os.makedirs('data', exist_ok=True)
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    
    app.run(debug=True, host='0.0.0.0', port=5000)