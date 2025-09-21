import os
import time
import asyncio
import concurrent.futures
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file, Response
from werkzeug.utils import secure_filename
import json
import uuid
from config import config
from services.sqlite_service import SQLiteService
from services.ai_manager_service import AIManagerService
from services.export_service import ExportService
from services.cost_calculation_service import cost_service

# Carregar variáveis de ambiente do arquivo .env
from dotenv import load_dotenv
load_dotenv()

# Fallback: definir variável diretamente se não foi carregada do .env
if not os.environ.get('OPENAI_API_KEY'):
    try:
        with open('.env', 'r', encoding='utf-8') as f:
            content = f.read()
            for line in content.split('\n'):
                # Remover BOM se presente
                line = line.replace('\ufeff', '')
                if line.startswith('OPENAI_API_KEY='):
                    os.environ['OPENAI_API_KEY'] = line.strip().split('=', 1)[1]
                    break
    except Exception as e:
        pass

# Inicializar serviços
from services.sqlite_service import SQLiteService
data_service = SQLiteService()  # Mudança para SQLite
ai_manager_service = AIManagerService()
export_service = ExportService()

# Sistema de controle de cancelamento de análises
analises_em_andamento = {}  # {session_id: {'cancelado': bool, 'total': int, 'atual': int}}

def criar_session_id():
    """Cria um ID único para a sessão de análise"""
    return str(uuid.uuid4())

def registrar_analise(session_id, total_intimacoes):
    """Registra uma nova análise em andamento"""
    analises_em_andamento[session_id] = {
        'cancelado': False,
        'total': total_intimacoes,
        'atual': 0,
        'inicio': time.time()
    }
    print(f"=== DEBUG: Análise registrada - Session ID: {session_id}, Total: {total_intimacoes} ===")

def cancelar_analise(session_id):
    """Marca uma análise para cancelamento"""
    if session_id in analises_em_andamento:
        analises_em_andamento[session_id]['cancelado'] = True
        print(f"=== DEBUG: Análise cancelada - Session ID: {session_id} ===")
        return True
    return False

def verificar_cancelamento(session_id):
    """Verifica se uma análise foi cancelada"""
    if session_id in analises_em_andamento:
        return analises_em_andamento[session_id]['cancelado']
    return False

def atualizar_progresso_analise(session_id, atual):
    """Atualiza o progresso de uma análise"""
    if session_id in analises_em_andamento:
        analises_em_andamento[session_id]['atual'] = atual

def finalizar_analise(session_id):
    """Remove uma análise do controle"""
    if session_id in analises_em_andamento:
        del analises_em_andamento[session_id]
        print(f"=== DEBUG: Análise finalizada - Session ID: {session_id} ===")

# Criar aplicação Flask
app = Flask(__name__)
app.secret_key = 'sua_chave_secreta_aqui_mude_em_producao'

# Configurar limite de upload para 100MB
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB

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
        defensor = request.args.get('defensor', '')
        ordenacao = request.args.get('ordenacao', 'data_desc')
        itens_por_pagina_usuario = request.args.get('itens_por_pagina', '')
        
        print(f"DEBUG: Parâmetros - Página: {pagina}, Busca: '{busca}', Classificação: '{classificacao}', Ordenação: '{ordenacao}', Itens por página: '{itens_por_pagina_usuario}'")
        
        config = data_service.get_config()
        # Usar o valor selecionado pelo usuário ou o padrão da configuração
        if itens_por_pagina_usuario and itens_por_pagina_usuario.isdigit():
            itens_por_pagina = int(itens_por_pagina_usuario)
        else:
            itens_por_pagina = config.get('itens_por_pagina', 25)
        print(f"DEBUG: Itens por página: {itens_por_pagina}")
        
        print("DEBUG: Carregando todas as intimações...")
        intimacoes = data_service.get_all_intimacoes()
        
        # Validação defensiva
        if intimacoes is None:
            intimacoes = []
        
        print(f"DEBUG: Total de intimações carregadas: {len(intimacoes)}")
        for i, intimacao in enumerate(intimacoes):
            if intimacao is None:
                print(f"  {i+1}. ❌ Intimação None encontrada")
                continue
            contexto = intimacao.get('contexto', '')
            if contexto is None:
                contexto = ''
            print(f"  {i+1}. ID: {intimacao.get('id')} | Contexto: {contexto[:50]}...")
        
        # Filtrar intimações None
        intimacoes = [i for i in intimacoes if i is not None]
        
        # Aplicar filtros
        if busca:
            intimacoes = [i for i in intimacoes if busca.lower() in (i.get('contexto', '') or '').lower()]
            print(f"DEBUG: Após filtro de busca: {len(intimacoes)}")
        
        if classificacao:
            intimacoes = [i for i in intimacoes if i.get('classificacao_manual') == classificacao]
            print(f"DEBUG: Após filtro de classificação: {len(intimacoes)}")
        
        if defensor:
            intimacoes = [i for i in intimacoes if i.get('defensor') == defensor]
            print(f"DEBUG: Após filtro de defensor: {len(intimacoes)}")
        
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
                             config=config,
                             classificacoes=Config.TIPOS_ACAO,
                             tipos_acao=Config.TIPOS_ACAO,
                             defensores=Config.DEFENSORES,
                             filtros={'busca': busca, 'classificacao': classificacao, 'defensor': request.args.get('defensor', ''), 'ordenacao': ordenacao})
    except Exception as e:
        flash(f'Erro ao carregar intimações: {str(e)}', 'error')
        return render_template('intimacoes.html',
                             intimacoes=[],
                             pagina_atual=1,
                             total_paginas=1,
                             total_itens=0,
                             stats={'total': 0, 'com_classificacao': 0, 'analisadas': 0, 'pendentes': 0},
                             config={},
                             classificacoes=Config.TIPOS_ACAO,
                             tipos_acao=Config.TIPOS_ACAO,
                             defensores=Config.DEFENSORES,
                             filtros={'busca': '', 'classificacao': '', 'defensor': '', 'ordenacao': 'data_desc'})

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
            processo = request.form.get('processo', '').strip()
            orgao_julgador = request.form.get('orgao_julgador', '').strip()
            classe = request.form.get('classe', '').strip()
            disponibilizacao = request.form.get('disponibilizacao', '').strip()
            intimado = request.form.get('intimado', '').strip()
            status = request.form.get('status', '').strip()
            prazo = request.form.get('prazo', '').strip()
            defensor = request.form.get('defensor', '').strip()
            id_tarefa = request.form.get('id_tarefa', '').strip()
            cor_etiqueta = request.form.get('cor_etiqueta', '').strip()
            
            print(f"Contexto extraído: '{contexto}'")
            print(f"Classificação extraída: '{classificacao_manual}'")
            print(f"Informações extraídas: '{informacoes_adicionais}'")
            print(f"Processo: '{processo}'")
            print(f"Órgão Julgador: '{orgao_julgador}'")
            print(f"Classe: '{classe}'")
            print(f"Disponibilização: '{disponibilizacao}'")
            print(f"Intimado: '{intimado}'")
            print(f"Status: '{status}'")
            print(f"Prazo: '{prazo}'")
            print(f"Defensor: '{defensor}'")
            print(f"ID Tarefa: '{id_tarefa}'")
            print(f"Cor Etiqueta: '{cor_etiqueta}'")
            
            if not contexto:
                print("DEBUG: Contexto vazio, retornando erro")
                flash('O contexto da intimação é obrigatório.', 'error')
                return render_template('nova_intimacao.html', 
                                     classificacoes=Config.TIPOS_ACAO,
                                     tipos_acao=Config.TIPOS_ACAO,
                                     defensores=Config.DEFENSORES,
                                     dados={'contexto': contexto, 
                                           'classificacao_manual': classificacao_manual,
                                           'informacoes_adicionais': informacoes_adicionais,
                                           'processo': processo,
                                           'orgao_julgador': orgao_julgador,
                                           'classe': classe,
                                           'disponibilizacao': disponibilizacao,
                                           'intimado': intimado,
                                           'status': status,
                                           'prazo': prazo,
                                           'defensor': defensor,
                                           'id_tarefa': id_tarefa,
                                           'cor_etiqueta': cor_etiqueta})
            
            # Criar a intimação
            intimacao_data = {
                'contexto': contexto,
                'classificacao_manual': classificacao_manual if classificacao_manual else None,
                'informacoes_adicionais': informacoes_adicionais if informacoes_adicionais else None,
                'processo': processo if processo else None,
                'orgao_julgador': orgao_julgador if orgao_julgador else None,
                'classe': classe if classe else None,
                'disponibilizacao': disponibilizacao if disponibilizacao else None,
                'intimado': intimado if intimado else None,
                'status': status if status else None,
                'prazo': prazo if prazo else None,
                'defensor': defensor if defensor else None,
                'id_tarefa': id_tarefa if id_tarefa else None,
                'cor_etiqueta': cor_etiqueta if cor_etiqueta else None,
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
                                 defensores=Config.DEFENSORES,
                                 dados={'contexto': request.form.get('contexto', ''), 
                                       'classificacao_manual': request.form.get('classificacao_manual', ''),
                                       'informacoes_adicionais': request.form.get('informacoes_adicionais', ''),
                                       'processo': request.form.get('processo', ''),
                                       'orgao_julgador': request.form.get('orgao_julgador', ''),
                                       'classe': request.form.get('classe', ''),
                                       'disponibilizacao': request.form.get('disponibilizacao', ''),
                                       'intimado': request.form.get('intimado', ''),
                                       'status': request.form.get('status', ''),
                                       'prazo': request.form.get('prazo', ''),
                                       'defensor': request.form.get('defensor', ''),
                                       'id_tarefa': request.form.get('id_tarefa', ''),
                                       'cor_etiqueta': request.form.get('cor_etiqueta', '')})
    
    return render_template('nova_intimacao.html', 
                         classificacoes=Config.TIPOS_ACAO,
                         tipos_acao=Config.TIPOS_ACAO,
                         defensores=Config.DEFENSORES,
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
        
        # Carregar configurações para o link do portal
        config = data_service.get_config()
        
        return render_template('visualizar_intimacao.html',
                             intimacao=intimacao,
                             analises=analises,
                             stats=stats,
                             config=config,
                             classificacoes=Config.TIPOS_ACAO,
                             tipos_acao=Config.TIPOS_ACAO,
                             defensores=Config.DEFENSORES)
                             
    except Exception as e:
        flash(f'Erro ao carregar intimação: {str(e)}', 'error')
        return redirect(url_for('listar_intimacoes'))

@app.route('/analises/<analise_id>')
def visualizar_analise(analise_id):
    """Página para visualizar detalhes de uma análise específica"""
    try:
        # Buscar a análise em todas as intimações
        intimacoes = data_service.get_all_intimacoes()
        analise_encontrada = None
        intimacao_relacionada = None
        
        for intimacao in intimacoes:
            for analise in intimacao.get('analises', []):
                if analise.get('id') == analise_id:
                    analise_encontrada = analise
                    intimacao_relacionada = intimacao
                    break
            if analise_encontrada:
                break
        
        if not analise_encontrada:
            flash('Análise não encontrada.', 'error')
            return redirect(url_for('analise'))
        
        # Buscar informações do prompt usado
        prompt_usado = None
        if analise_encontrada.get('prompt_id'):
            prompt_usado = data_service.get_prompt_by_id(analise_encontrada['prompt_id'])
        
        return render_template('visualizar_analise.html',
                               analise=analise_encontrada,
                               intimacao=intimacao_relacionada,
                               prompt=prompt_usado)
    except Exception as e:
        print(f"Erro ao visualizar análise: {e}")
        flash('Erro ao carregar análise.', 'error')
        return redirect(url_for('analise'))

@app.route('/prompts')
def listar_prompts():
    """Página de listagem de prompts"""
    try:
        # Parâmetros de filtro e paginação
        pagina = int(request.args.get('pagina', 1))
        busca = request.args.get('busca', '')
        status = request.args.get('status', '')
        tamanho = request.args.get('tamanho', '')
        ordenacao = request.args.get('ordenacao', 'data_desc')
        
        config = data_service.get_config()
        itens_por_pagina = config.get('itens_por_pagina', 25)
        
        prompts = data_service.get_all_prompts()
        
        # Filtrar apenas prompts ativos se não for admin
        # Por enquanto, mostrar todos para permitir gerenciamento
        # prompts = data_service.get_prompts_ativos()
        
        # Aplicar filtros
        if busca:
            prompts = [p for p in prompts if busca.lower() in p.get('nome', '').lower() or 
                      busca.lower() in p.get('descricao', '').lower()]
        
        if status:
            if status == 'ativo':
                prompts = [p for p in prompts if p.get('ativo', True)]
            elif status == 'inativo':
                prompts = [p for p in prompts if not p.get('ativo', True)]
        
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
            'ativos': len([p for p in prompts if p.get('ativo', True)]),
            'inativos': len([p for p in prompts if not p.get('ativo', True)]),
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
                             filtros={'busca': busca, 'status': status, 'tamanho': tamanho, 'ordenacao': ordenacao})
    except Exception as e:
        flash(f'Erro ao carregar prompts: {str(e)}', 'error')
        return render_template('prompts.html',
                             prompts=[],
                             pagina_atual=1,
                             total_paginas=1,
                             total_itens=0,
                             stats={'total': 0, 'ativos': 0, 'inativos': 0, 'pequenos': 0, 'medios': 0, 'grandes': 0},
                             classificacoes=Config.TIPOS_ACAO,
                             filtros={'busca': '', 'status': '', 'tamanho': '', 'ordenacao': 'data_desc'})

@app.route('/prompts/novo', methods=['GET', 'POST'])
def novo_prompt():
    """Página para criar novo prompt"""
    if request.method == 'POST':
        try:
            nome = request.form.get('nome', '').strip()
            descricao = request.form.get('descricao', '').strip()
            regra_negocio = request.form.get('regra_negocio', '').strip()
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
                'regra_negocio': regra_negocio if regra_negocio else None,
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
        
        # Obter sessões de análise relacionadas ao prompt
        sessoes = data_service.get_sessoes_analise(limit=50, prompt_id=id)
        
        # Obter intimações que foram analisadas com este prompt
        intimacoes_historico = data_service.get_intimacoes_por_prompt(id)
        
        # Calcular estatísticas das sessões
        stats = {
            'total_sessoes': len(sessoes),
            'total_intimacoes_processadas': sum(s.get('intimações_processadas', 0) for s in sessoes),
            'total_acertos': sum(s.get('acertos', 0) for s in sessoes),
            'tempo_total': sum(s.get('tempo_total', 0) for s in sessoes),
            'custo_total': sum(s.get('custo_total', 0) for s in sessoes),
            'tokens_total': sum(s.get('tokens_total', 0) for s in sessoes),
            'acuracia_media': 0,
            'ultimas_sessoes': sessoes[:10]  # Últimas 10 sessões
        }
        
        # Calcular acurácia média
        if stats['total_intimacoes_processadas'] > 0:
            stats['acuracia_media'] = (stats['total_acertos'] * 100.0) / stats['total_intimacoes_processadas']
        
        return render_template('visualizar_prompt.html',
                             prompt=prompt,
                             sessoes=sessoes,
                             intimacoes_historico=intimacoes_historico,
                             stats=stats,
                             classificacoes=Config.TIPOS_ACAO)
                             
    except Exception as e:
        flash(f'Erro ao carregar prompt: {str(e)}', 'error')
        return redirect(url_for('listar_prompts'))

@app.route('/analise')
def analise():
    """Página para testar prompts com intimações"""
    try:
        prompts = data_service.get_prompts_ativos()
        intimacoes = data_service.get_all_intimacoes()
        config = data_service.get_config()
        
        # Validar dados antes de processar
        if prompts is None:
            prompts = []
        if intimacoes is None:
            intimacoes = []
        if config is None:
            config = {}
        
        # Adicionar informações de tamanho aos prompts
        for prompt in prompts:
            conteudo = prompt.get('conteudo', '')
            if conteudo is None:
                conteudo = ''
            conteudo_len = len(conteudo)
            if conteudo_len <= 500:
                prompt['tamanho'] = 'Pequeno'
            elif conteudo_len <= 2000:
                prompt['tamanho'] = 'Médio'
            else:
                prompt['tamanho'] = 'Grande'
        
        # Usar o ai_manager_service global
        provedor_atual = ai_manager_service.get_current_provider()
        
        # Debug das configurações
        modelo_padrao = config.get('azure_deployment', 'gpt-4')
        temperatura_padrao = config.get('azure_temperatura', 0.7)
        max_tokens_padrao = config.get('azure_max_tokens', 500)
        
        print(f"=== DEBUG: Configurações carregadas - Modelo: {modelo_padrao}, Temp: {temperatura_padrao}, Tokens: {max_tokens_padrao} ===")
        
        return render_template('analise.html',
                             prompts=prompts,
                             intimacoes=intimacoes,
                             classificacoes=Config.TIPOS_ACAO,
                             modelos_disponiveis=Config.OPENAI_MODELS,
                             modelo_padrao=modelo_padrao,
                             temperatura_padrao=temperatura_padrao,
                             max_tokens_padrao=max_tokens_padrao,
                             provedor_atual=provedor_atual)
    except Exception as e:
        flash(f'Erro ao carregar página de análise: {str(e)}', 'error')
        return render_template('analise.html',
                             prompts=[],
                             intimacoes=[],
                             classificacoes=Config.TIPOS_ACAO,
                             modelos_disponiveis=Config.OPENAI_MODELS,
                             provedor_atual='openai',
                             modelo_padrao='gpt-4',
                             temperatura_padrao=0.7,
                             max_tokens_padrao=500)

@app.route('/historico')
def historico_analises():
    """Página para visualizar histórico de análises"""
    try:
        # Obter lista de sessões de análise (primeira página)
        sessoes = data_service.get_sessoes_analise(limit=20, offset=0)
        
        # Calcular total de sessões para paginação
        total_sessoes = data_service.get_total_sessoes_analise()
        
        return render_template('historico.html', 
                             sessoes=sessoes, 
                             total_sessoes=total_sessoes,
                             pagina_atual=1,
                             itens_por_pagina=20)
    except Exception as e:
        flash(f'Erro ao carregar histórico: {str(e)}', 'error')
        return render_template('historico.html', sessoes=[], total_sessoes=0, pagina_atual=1, itens_por_pagina=20)

@app.route('/historico/<session_id>')
def visualizar_sessao_analise(session_id):
    """Visualizar detalhes de uma sessão específica"""
    try:
        # Obter detalhes da sessão
        sessao = data_service.get_sessao_analise(session_id)
        if not sessao:
            flash('Sessão não encontrada', 'error')
            return redirect(url_for('historico_analises'))
        
        # Obter análises da sessão
        analises = data_service.get_analises_por_sessao(session_id)
        
        return render_template('visualizar_sessao.html', sessao=sessao, analises=analises)
    except Exception as e:
        flash(f'Erro ao carregar sessão: {str(e)}', 'error')
        return redirect(url_for('historico_analises'))

@app.route('/api/historico/pagina/<int:pagina>')
def api_historico_pagina(pagina):
    """API para carregar dados de uma página específica do histórico via AJAX"""
    try:
        # Parâmetros de filtro
        data_inicio = request.args.get('data_inicio', '')
        data_fim = request.args.get('data_fim', '')
        prompt_id = request.args.get('prompt_id', '')
        status = request.args.get('status', '')
        acuracia_min = request.args.get('acuracia_min', '')
        itens_por_pagina = int(request.args.get('itens_por_pagina', 20))
        
        # Calcular offset
        offset = (pagina - 1) * itens_por_pagina
        
        # Obter sessões com filtros
        sessoes = data_service.get_sessoes_analise(
            limit=itens_por_pagina, 
            offset=offset,
            data_inicio=data_inicio,
            data_fim=data_fim,
            prompt_id=prompt_id,
            status=status,
            acuracia_min=acuracia_min
        )
        
        # Calcular total de sessões para paginação
        total_sessoes = data_service.get_total_sessoes_analise(
            data_inicio=data_inicio,
            data_fim=data_fim,
            prompt_id=prompt_id,
            status=status,
            acuracia_min=acuracia_min
        )
        
        # Calcular informações de paginação
        total_paginas = (total_sessoes + itens_por_pagina - 1) // itens_por_pagina
        
        return jsonify({
            'success': True,
            'sessoes': sessoes,
            'pagina_atual': pagina,
            'total_paginas': total_paginas,
            'total_sessoes': total_sessoes,
            'itens_por_pagina': itens_por_pagina
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro ao carregar página: {str(e)}'
        }), 500

@app.route('/api/historico/excluir-sessao', methods=['POST'])
def excluir_sessao_analise():
    """Excluir uma sessão de análise e suas análises associadas"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        
        if not session_id:
            return jsonify({'error': 'Session ID é obrigatório'}), 400
        
        # Verificar se a sessão existe
        sessao = data_service.get_sessao_analise(session_id)
        if not sessao:
            return jsonify({'error': 'Sessão não encontrada'}), 404
        
        # Excluir a sessão e suas análises
        sucesso = data_service.excluir_sessao_analise(session_id)
        
        if sucesso:
            return jsonify({
                'success': True,
                'message': 'Sessão excluída com sucesso',
                'session_id': session_id
            })
        else:
            return jsonify({'error': 'Erro ao excluir sessão'}), 500
            
    except Exception as e:
        print(f"Erro ao excluir sessão: {e}")
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

@app.route('/api/database/upload', methods=['POST'])
def upload_database():
    """Upload de banco de dados via interface web"""
    try:
        if 'database_file' not in request.files:
            return jsonify({'success': False, 'message': 'Nenhum arquivo foi enviado'}), 400
        
        file = request.files['database_file']
        if file.filename == '':
            return jsonify({'success': False, 'message': 'Nenhum arquivo foi selecionado'}), 400
        
        if not file.filename.endswith('.db'):
            return jsonify({'success': False, 'message': 'Arquivo deve ter extensão .db'}), 400
        
        # Fazer backup do banco atual
        backup_path = f"data/database_backup_antes_upload_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        import shutil
        shutil.copy2('data/database.db', backup_path)
        
        # Salvar novo banco
        file.save('data/database.db')
        
        # Testar se o banco é válido
        try:
            test_conn = sqlite3.connect('data/database.db')
            test_conn.execute('SELECT COUNT(*) FROM intimacoes LIMIT 1')
            test_conn.close()
        except Exception as e:
            # Restaurar backup se o banco for inválido
            shutil.copy2(backup_path, 'data/database.db')
            return jsonify({'success': False, 'message': f'Banco de dados inválido: {str(e)}'}), 400
        
        return jsonify({
            'success': True, 
            'message': f'Banco de dados atualizado com sucesso! Backup salvo em: {backup_path}'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro ao fazer upload: {str(e)}'}), 500

@app.route('/api/database/download', methods=['GET'])
def download_database():
    """Download do banco de dados atual"""
    try:
        return send_file('data/database.db', as_attachment=True, download_name='database.db')
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro ao fazer download: {str(e)}'}), 500

@app.route('/api/historico/exportar-sessao', methods=['POST'])
def exportar_sessao_analise():
    """Exportar uma sessão de análise para CSV/Excel"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        formato = data.get('formato', 'csv')  # csv ou excel
        
        if not session_id:
            return jsonify({'error': 'Session ID é obrigatório'}), 400
        
        # Verificar se a sessão existe
        sessao = data_service.get_sessao_analise(session_id)
        if not sessao:
            return jsonify({'error': 'Sessão não encontrada'}), 404
        
        # Obter análises da sessão
        analises = data_service.get_analises_por_sessao(session_id)
        
        if not analises:
            return jsonify({'error': 'Nenhuma análise encontrada para esta sessão'}), 404
        
        # Preparar dados para exportação
        dados_exportacao = []
        for analise in analises:
            dados_exportacao.append({
                'ID da Análise': analise['id'],
                'ID da Intimação': analise['intimacao_id'],
                'Processo': analise.get('processo', 'N/A'),
                'Órgão Julgador': analise.get('orgao_julgador', 'N/A'),
                'Classificação Manual': analise.get('classificacao_manual', 'N/A'),
                'Resultado IA': analise.get('resultado_ia', 'N/A'),
                'Acertou': 'Sim' if analise.get('acertou') else 'Não',
                'Tempo Processamento (s)': round(analise.get('tempo_processamento', 0), 2),
                'Custo Real ($)': round(analise.get('custo_real', 0), 6),
                'Tokens Input': analise.get('tokens_input', 0),
                'Tokens Output': analise.get('tokens_output', 0),
                'Modelo': analise.get('modelo', 'N/A'),
                'Temperatura': analise.get('temperatura', 'N/A'),
                'Data da Análise': analise.get('data_analise_formatada', 'N/A'),
                'Informação Adicional': analise.get('informacao_adicional', 'N/A')
            })
        
        # Gerar arquivo
        if formato == 'excel':
            # Usar o serviço de exportação para Excel
            from services.export_service import ExportService
            export_service = ExportService()
            
            # Criar nome do arquivo
            nome_arquivo = f"historico_sessao_{session_id[:8]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            
            # Gerar Excel
            caminho_arquivo = export_service.export_to_excel(
                dados_exportacao, 
                nome_arquivo,
                sheet_name='Análises da Sessão'
            )
            
            # Retornar arquivo para download
            return send_file(
                caminho_arquivo,
                as_attachment=True,
                download_name=nome_arquivo,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
        else:
            # Exportar como CSV
            from services.export_service import ExportService
            export_service = ExportService()
            
            # Criar nome do arquivo
            nome_arquivo = f"historico_sessao_{session_id[:8]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            
            # Gerar CSV
            caminho_arquivo = export_service.export_to_csv(
                dados_exportacao, 
                nome_arquivo
            )
            
            # Retornar arquivo para download
            return send_file(
                caminho_arquivo,
                as_attachment=True,
                download_name=nome_arquivo,
                mimetype='text/csv'
            )
            
    except Exception as e:
        print(f"Erro ao exportar sessão: {e}")
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

def executar_analise_paralela(intimacao_ids, prompt, modelo, temperatura, max_tokens, 
                              salvar_resultados, calcular_acuracia, session_id, 
                              analise_paralela, delay_entre_lotes):
    """Executar análise de intimações em paralelo"""
    resultados = []
    
    # Dividir intimações em lotes
    lotes = [intimacao_ids[i:i + analise_paralela] for i in range(0, len(intimacao_ids), analise_paralela)]
    
    print(f"=== DEBUG: Executando {len(lotes)} lotes de até {analise_paralela} análises ===")
    
    for lote_idx, lote in enumerate(lotes, 1):
        # Verificar cancelamento antes de cada lote
        if verificar_cancelamento(session_id):
            print(f"=== DEBUG: Análise cancelada no lote {lote_idx} ===")
            break
            
        print(f"=== DEBUG: Processando lote {lote_idx}/{len(lotes)} com {len(lote)} intimações ===")
        
        # Executar análises do lote em paralelo
        with concurrent.futures.ThreadPoolExecutor(max_workers=analise_paralela) as executor:
            # Criar tasks para cada intimação do lote
            futures = []
            for intimacao_id in lote:
                future = executor.submit(
                    analisar_intimacao_individual,
                    intimacao_id, prompt, modelo, temperatura, max_tokens,
                    salvar_resultados, calcular_acuracia, session_id
                )
                futures.append(future)
            
            # Coletar resultados do lote
            for future in concurrent.futures.as_completed(futures):
                try:
                    resultado = future.result()
                    if resultado:
                        resultados.append(resultado)
                        # Atualizar progresso
                        atualizar_progresso_analise(session_id, len(resultados))
                except Exception as e:
                    print(f"=== DEBUG: Erro na análise paralela: {str(e)} ===")
        
        # Delay entre lotes (exceto no último lote)
        if lote_idx < len(lotes) and delay_entre_lotes > 0:
            print(f"=== DEBUG: Aguardando {delay_entre_lotes}s antes do próximo lote ===")
            time.sleep(delay_entre_lotes)
    
    return resultados

def analisar_intimacao_individual(intimacao_id, prompt, modelo, temperatura, max_tokens,
                                 salvar_resultados, calcular_acuracia, session_id):
    """Analisar uma intimação individual (para uso em paralelo)"""
    try:
        intimacao = data_service.get_intimacao_by_id(intimacao_id)
        if not intimacao:
            print(f"=== DEBUG: Intimação {intimacao_id} não encontrada ===")
            return None
            
        print(f"=== DEBUG: Analisando intimação {intimacao_id} ===")
        
        # Preparar o prompt final
        contexto = f"""
Contexto da Intimação:
{intimacao.get('contexto', '')}
"""
        
        # Substituir variáveis no prompt (mesma lógica da análise sequencial)
        prompt_final = prompt['conteudo']
        
        # Substituir {REGRADENEGOCIO} se existir
        if prompt.get('regra_negocio') and '{REGRADENEGOCIO}' in prompt_final:
            prompt_final = prompt_final.replace('{REGRADENEGOCIO}', prompt['regra_negocio'])
        
        # Substituir {CONTEXTO}
        prompt_final = prompt_final.replace('{CONTEXTO}', contexto)
        
        print(f"=== DEBUG: Prompt final preparado (primeiros 200 chars): {prompt_final[:200]}... ===")
        
        # Preparar parâmetros para a IA
        parametros = {
            'model': modelo,
            'temperature': temperatura,
            'max_tokens': max_tokens,
            'top_p': 1.0
        }
        
        # Chamar IA
        inicio_analise = time.time()
        resultado_ia, resposta_ia, tokens_info = ai_manager_service.analisar_intimacao(
            contexto, prompt_final, parametros
        )
        fim_analise = time.time()
        tempo_processamento = fim_analise - inicio_analise
        
        # Calcular acurácia se solicitado
        acertou = None
        if calcular_acuracia and intimacao.get('classificacao_manual'):
            acertou = resultado_ia.strip().upper() == intimacao['classificacao_manual'].strip().upper()
            print(f"=== DEBUG: Comparação - Manual: {intimacao['classificacao_manual']}, IA: {resultado_ia}, Acertou: {acertou} ===")
        
        # Usar tokens reais da API
        tokens_input = tokens_info.get('input', 0)
        tokens_output = tokens_info.get('output', 0)
        tokens_usados = tokens_info.get('total', tokens_input + tokens_output)
        
        # Calcular custo real baseado nos tokens
        provider = ai_manager_service.get_current_provider()
        custo_real = cost_service.calculate_real_cost(tokens_input, tokens_output, modelo, provider)
        
        # Preparar resultado
        resultado = {
            'prompt_id': prompt['id'],
            'prompt_nome': prompt['nome'],
            'regra_negocio': prompt.get('regra_negocio', ''),
            'intimacao_id': intimacao_id,
            'resultado_ia': resultado_ia,
            'classificacao_manual': intimacao.get('classificacao_manual'),
            'informacao_adicional': intimacao.get('informacao_adicional'),
            'tempo_processamento': round(tempo_processamento, 2),
            'acertou': acertou,
            'prompt_completo': prompt_final,
            'resposta_completa': resposta_ia,
            'modelo': modelo,
            'temperatura': temperatura,
            'tokens_input': tokens_input,
            'tokens_output': tokens_output,
            'tokens_usados': tokens_usados,
            'custo_real': custo_real,
            'provider': provider,
            'intimacao': intimacao
        }
        
        # Salvar no banco se solicitado
        if salvar_resultados:
            analise_data = {
                'session_id': session_id,
                'intimacao_id': intimacao_id,
                'prompt_id': prompt['id'],
                'prompt_nome': prompt['nome'],
                'resultado_ia': resultado_ia,
                'acertou': acertou,
                'tempo_processamento': tempo_processamento,
                'modelo': modelo,
                'temperatura': temperatura,
                'tokens_input': tokens_input,
                'tokens_output': tokens_output,
                'custo_real': custo_real,
                'prompt_completo': prompt_final,
                'resposta_completa': resposta_ia
            }
            data_service.save_analise(analise_data)
        
        return resultado
        
    except Exception as e:
        print(f"=== DEBUG: Erro ao analisar intimação {intimacao_id}: {str(e)} ===")
        return None

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
        session_id = data.get('session_id')  # ID da sessão para cancelamento
        
        if not prompt_id or not intimacao_ids:
            return jsonify({'error': 'Prompt e intimações são obrigatórios'}), 400
        
        if not session_id:
            return jsonify({'error': 'Session ID é obrigatório para cancelamento'}), 400
        
        print(f"=== DEBUG: Prompt ID: {prompt_id} ===")
        print(f"=== DEBUG: Intimação IDs: {intimacao_ids} ===")
        print(f"=== DEBUG: Session ID: {session_id} ===")
        
        # Registrar análise para controle de cancelamento
        registrar_analise(session_id, len(intimacao_ids))
        
        # Carregar configurações padrão
        config = data_service.get_config()
        
        # Criar sessão de análise no banco
        prompt = data_service.get_prompt_by_id(prompt_id)
        if not prompt:
            finalizar_analise(session_id)
            return jsonify({'error': 'Prompt não encontrado'}), 404
        
        # Preparar configurações para a sessão
        config_sessao = {
            'modelo': configuracoes.get('modelo', config.get('modelo_padrao', 'gpt-4')),
            'temperatura': float(configuracoes.get('temperatura', config.get('temperatura_padrao', 0.7))),
            'max_tokens': int(configuracoes.get('max_tokens', config.get('max_tokens_padrao', 500))),
            'timeout': int(configuracoes.get('timeout', config.get('timeout_padrao', 30))),
            'salvar_resultados': configuracoes.get('salvar_resultados', True),
            'calcular_acuracia': configuracoes.get('calcular_acuracia', True),
            'modo_paralelo': configuracoes.get('modo_paralelo', False),
            'regra_negocio': prompt.get('regra_negocio', '')
        }
        
        # Criar sessão no banco
        data_service.criar_sessao_analise(
            session_id=session_id,
            prompt_id=prompt_id,
            prompt_nome=prompt['nome'],
            modelo=configuracoes.get('modelo', config.get('modelo_padrao', 'gpt-4')),
            temperatura=float(configuracoes.get('temperatura', config.get('temperatura_padrao', 0.7))),
            max_tokens=int(configuracoes.get('max_tokens', config.get('max_tokens_padrao', 500))),
            timeout=int(configuracoes.get('timeout', config.get('timeout_padrao', 30))),
            total_intimacoes=len(intimacao_ids),
            configuracoes=config_sessao
        )
        
        # Configurações da OpenAI (usar configurações da página se fornecidas, senão usar padrões)
        modelo = configuracoes.get('modelo', config.get('modelo_padrao', 'gpt-4'))
        temperatura = float(configuracoes.get('temperatura', config.get('temperatura_padrao', 0.7)))
        max_tokens = int(configuracoes.get('max_tokens', config.get('max_tokens_padrao', 500)))
        salvar_resultados = configuracoes.get('salvar_resultados', True)
        calcular_acuracia = configuracoes.get('calcular_acuracia', True)
        
        # Configurações de análise paralela (específicas por provider)
        provider_atual = ai_manager_service.get_current_provider()
        if provider_atual == 'azure':
            analise_paralela = int(config.get('azure_analise_paralela', 1))
            delay_entre_lotes = float(config.get('azure_delay_entre_lotes', 0.5))
        else:
            analise_paralela = int(config.get('analise_paralela', 1))
            delay_entre_lotes = float(config.get('delay_entre_lotes', 0.5))
        
        print(f"=== DEBUG: Provider: {provider_atual}, Modelo: {modelo}, Temp: {temperatura}, Tokens: {max_tokens} ===")
        print(f"=== DEBUG: Análise Paralela: {analise_paralela}, Delay: {delay_entre_lotes}s ===")
        
        resultados = []
        
        print(f"=== DEBUG: Prompt encontrado: {prompt['nome']} ===")
        
        # Executar análise paralela ou sequencial
        if analise_paralela > 1:
            resultados = executar_analise_paralela(
                intimacao_ids, prompt, modelo, temperatura, max_tokens, 
                salvar_resultados, calcular_acuracia, session_id, 
                analise_paralela, delay_entre_lotes
            )
        else:
            # Análise sequencial (comportamento original)
            for i, intimacao_id in enumerate(intimacao_ids, 1):
                # Verificar se a análise foi cancelada
                if verificar_cancelamento(session_id):
                    print(f"=== DEBUG: Análise cancelada pelo usuário - Session ID: {session_id} ===")
                    finalizar_analise(session_id)
                    return jsonify({
                        'success': False,
                        'cancelado': True,
                        'message': 'Análise cancelada pelo usuário'
                    })
                
                # Atualizar progresso
                atualizar_progresso_analise(session_id, i)
                
                intimacao = data_service.get_intimacao_by_id(intimacao_id)
                if not intimacao:
                    print(f"=== DEBUG: Intimação {intimacao_id} não encontrada ===")
                    continue
                    
                print(f"=== DEBUG: Analisando intimação {intimacao_id} ({i}/{len(intimacao_ids)}) ===")
                print(f"=== DEBUG: Classificação manual: {intimacao.get('classificacao_manual')} ===")
                    
                try:
                    # Preparar o prompt final
                    contexto = f"""
Contexto da Intimação:
{intimacao.get('contexto', '')}
"""
                    
                    # Substituir variáveis no prompt
                    prompt_final = prompt['conteudo']
                    
                    # Substituir {REGRADENEGOCIO} se existir
                    if prompt.get('regra_negocio') and '{REGRADENEGOCIO}' in prompt_final:
                        prompt_final = prompt_final.replace('{REGRADENEGOCIO}', prompt['regra_negocio'])
                    
                    # Substituir {CONTEXTO}
                    prompt_final = prompt_final.replace('{CONTEXTO}', contexto)
                    
                    print(f"=== DEBUG: Prompt final preparado (primeiros 200 chars): {prompt_final[:200]}... ===")
                    
                    inicio = time.time()
                    
                    # Preparar parâmetros para a IA
                    parametros = {
                        'model': modelo,
                        'temperature': temperatura,
                        'max_tokens': max_tokens,
                        'top_p': 1.0
                    }
                    
                    # Fazer chamada para IA usando o gerenciador
                    resultado_ia, resposta_ia, tokens_info = ai_manager_service.analisar_intimacao(
                        contexto, prompt_final, parametros
                    )
                    
                    tempo_processamento = time.time() - inicio
                    
                    # Usar tokens reais da API
                    tokens_input = tokens_info.get('input', 0)
                    tokens_output = tokens_info.get('output', 0)
                    tokens_usados = tokens_info.get('total', tokens_input + tokens_output)
                    
                    # Calcular acurácia se possível
                    acertou = None
                    if calcular_acuracia and intimacao.get('classificacao_manual'):
                        acertou = resultado_ia.strip().upper() == intimacao['classificacao_manual'].strip().upper()
                        print(f"=== DEBUG: Comparação - Manual: {intimacao['classificacao_manual']}, IA: {resultado_ia}, Acertou: {acertou} ===")
                    
                    # Calcular custo real baseado nos tokens
                    provider = ai_manager_service.get_current_provider()
                    custo_real = cost_service.calculate_real_cost(tokens_input, tokens_output, modelo, provider)
                    
                    resultado = {
                        'prompt_id': prompt['id'],
                        'prompt_nome': prompt['nome'],
                        'regra_negocio': prompt.get('regra_negocio', ''),
                        'intimacao_id': intimacao_id,
                        'resultado_ia': resultado_ia,
                        'classificacao_manual': intimacao.get('classificacao_manual'),
                        'informacao_adicional': intimacao.get('informacao_adicional'),
                        'tempo_processamento': round(tempo_processamento, 2),
                        'acertou': acertou,
                        'prompt_completo': prompt_final,
                        'resposta_completa': resposta_ia,
                        'modelo': modelo,
                        'temperatura': temperatura,
                        'tokens_input': tokens_input,
                        'tokens_output': tokens_output,
                        'tokens_usados': tokens_usados,
                        'custo_real': custo_real,
                        'provider': provider,
                        'intimacao': intimacao
                    }
                    
                    # Salvar resultado se solicitado
                    if salvar_resultados:
                        analise_data = {
                            'session_id': session_id,
                            'intimacao_id': intimacao_id,
                            'prompt_id': prompt['id'],
                            'prompt_nome': prompt['nome'],
                            'resultado_ia': resultado_ia,
                            'acertou': acertou,
                            'tempo_processamento': tempo_processamento,
                            'modelo': modelo,
                            'temperatura': temperatura,
                            'tokens_input': tokens_input,
                            'tokens_output': tokens_output,
                            'custo_real': custo_real,
                            'prompt_completo': prompt_final,
                            'resposta_completa': resposta_ia
                        }
                        data_service.save_analise(analise_data)
                        print(f"=== DEBUG: Resultado salvo no banco ===")
                    
                    resultados.append(resultado)
                    
                except Exception as e:
                    print(f"=== ERRO ao analisar intimação {intimacao_id}: {e} ===")
                    resultado = {
                        'prompt_id': prompt['id'],
                        'prompt_nome': prompt['nome'],
                        'intimacao_id': intimacao_id,
                        'erro': str(e)
                    }
                    resultados.append(resultado)
        
        # Finalizar análise
        finalizar_analise(session_id)
        
        # Calcular estatísticas gerais
        total_analises = len([r for r in resultados if 'erro' not in r])
        acertos = len([r for r in resultados if r.get('acertou') == True])
        erros = len([r for r in resultados if r.get('acertou') == False])
        tempo_total = sum([r.get('tempo_processamento', 0) for r in resultados if 'erro' not in r])
        custo_total = sum([r.get('custo_real', 0) for r in resultados if 'erro' not in r])
        tokens_total = sum([r.get('tokens_input', 0) + r.get('tokens_output', 0) for r in resultados if 'erro' not in r])
        
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
        
        # Finalizar sessão no banco
        estatisticas_sessao = {
            'total_processadas': total_analises,
            'acertos': acertos,
            'erros': erros,
            'tempo_total': tempo_total,
            'custo_total': custo_total,
            'tokens_total': tokens_total
        }
        data_service.finalizar_sessao_analise(session_id, estatisticas_sessao)
        
        return jsonify({
            'success': True,
            'resultados': resultados,
            'estatisticas': estatisticas
        })
        
    except Exception as e:
        # Garantir que a análise seja finalizada mesmo em caso de erro
        session_id = data.get('session_id') if 'data' in locals() else None
        if session_id:
            finalizar_analise(session_id)
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
        
        # Coletar todas as análises diretamente da tabela (evita duplicação)
        todas_analises_raw = data_service.get_all_analises()
        todas_analises = []
        
        # Criar mapa de intimações para lookup rápido
        intimacoes_map = {intimacao['id']: intimacao for intimacao in intimacoes}
        
        for analise in todas_analises_raw:
            # Buscar intimação correspondente
            intimacao = intimacoes_map.get(analise.get('intimacao_id'))
            if intimacao:
                analise['contexto'] = intimacao['contexto']
                analise['classificacao_manual'] = intimacao.get('classificacao_manual')
                analise['informacao_adicional'] = intimacao.get('informacao_adicional')
                # Incluir o objeto intimação completo para o card
                analise['intimacao'] = intimacao
            else:
                # Análise sem intimação (histórico antigo)
                analise['contexto'] = analise.get('contexto', 'N/A')
                analise['classificacao_manual'] = analise.get('classificacao_manual', 'N/A')
                analise['informacao_adicional'] = 'N/A'
                analise['intimacao'] = None
            
            # Garantir que os campos de prompt e resposta completos estejam presentes
            analise['prompt_completo'] = analise.get('prompt_completo', 'N/A')
            analise['resposta_completa'] = analise.get('resposta_completa', 'N/A')
            
            # Calcular custo real baseado nos tokens
            tokens_input = analise.get('tokens_input', 0)
            tokens_output = analise.get('tokens_output', 0)
            modelo = analise.get('modelo', 'gpt-3.5-turbo')
            
            # Obter provider atual ou usar o salvo na análise
            provider = analise.get('provider', ai_manager_service.get_current_provider())
            analise['provider'] = provider
            
            if tokens_input > 0 or tokens_output > 0:
                custo_real = cost_service.calculate_real_cost(tokens_input, tokens_output, modelo, provider)
                analise['custo_real'] = custo_real
            else:
                analise['custo_real'] = 0.0
            
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
        custo_total = sum([a.get('custo_real', 0.0) for a in analises_filtradas])
        
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
        
        # Coletar todas as análises diretamente da tabela (evita duplicação)
        todas_analises_raw = data_service.get_all_analises()
        todas_analises = []
        
        # Criar mapa de intimações para lookup rápido
        intimacoes_map = {intimacao['id']: intimacao for intimacao in intimacoes}
        
        for analise in todas_analises_raw:
            # Buscar intimação correspondente
            intimacao = intimacoes_map.get(analise.get('intimacao_id'))
            if intimacao:
                analise['contexto'] = intimacao['contexto']
                analise['classificacao_manual'] = intimacao.get('classificacao_manual')
                analise['informacao_adicional'] = intimacao.get('informacao_adicional')
                # Incluir o objeto intimação completo para o card
                analise['intimacao'] = intimacao
            else:
                # Análise sem intimação (histórico antigo)
                analise['contexto'] = analise.get('contexto', 'N/A')
                analise['classificacao_manual'] = analise.get('classificacao_manual', 'N/A')
                analise['informacao_adicional'] = 'N/A'
                analise['intimacao'] = None
            
            # Garantir que os campos de prompt e resposta completos estejam presentes
            analise['prompt_completo'] = analise.get('prompt_completo', 'N/A')
            analise['resposta_completa'] = analise.get('resposta_completa', 'N/A')
            
            # Calcular custo real baseado nos tokens
            tokens_input = analise.get('tokens_input', 0)
            tokens_output = analise.get('tokens_output', 0)
            modelo = analise.get('modelo', 'gpt-3.5-turbo')
            
            # Obter provider atual ou usar o salvo na análise
            provider = analise.get('provider', ai_manager_service.get_current_provider())
            analise['provider'] = provider
            
            if tokens_input > 0 or tokens_output > 0:
                custo_real = cost_service.calculate_real_cost(tokens_input, tokens_output, modelo, provider)
                analise['custo_real'] = custo_real
            else:
                analise['custo_real'] = 0.0
            
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
        html_tabela = render_template('partials/tabela_analises_com_card.html',
                                     analises=analises_paginadas,
                                     paginacao=paginacao)
        
        return jsonify({
            'success': True,
            'html': html_tabela,
            'paginacao': paginacao
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/componentes-demo')
def componentes_demo():
    """Página de demonstração dos componentes"""
    # Dados mockados para demonstração
    analises_demo = [
        {
            'id': 'analise-001',
            'intimacao_id': 'f71ac7be-a6d8-4c00-bd62-e5a4d94fad8c',
            'data_analise': '2025-08-11T18:01:31',
            'contexto': '# Dados do Processo\n## Informações Básicas do Processo\n- **Classe Processual**: Cumprimento de sentença\n- **Comarca**: Carazinho\n- **Competência**: Cível - Geral\n- **Data Ajuizamento**: 2025-07-18T14:18:56\n- **Assuntos**: Sucumbência\n- **Valor da Causa**: R$ 406,61\n- **Órgão Julgador**: Juízo da 2ª Vara Cível da Comarca de Carazinho',
            'prompt_nome': 'prompt inicial',
            'prompt_completo': 'Analise o contexto da intimação e classifique adequadamente.',
            'classificacao_manual': 'RENUNCIAR PRAZO',
            'informacao_adicional': 'decisão que recebe a fase de cumprimento de sentença',
            'resultado_ia': 'ELABORAR PEÇA',
            'acertou': False,
            'modelo': 'gpt-4',
            'temperatura': 0.0,
            'tempo_processamento': 2.5,

            'resposta_completa': 'Resposta completa da IA para demonstração.'
        },
        {
            'id': 'analise-002',
            'intimacao_id': '7240e914-6832-4a83-b159-4dbcb8f43854',
            'data_analise': '2025-08-11T18:02:15',
            'contexto': '# Dados do Processo\n## Informações Básicas do Processo\n- **Classe Processual**: Execução de Título Extrajudicial\n- **Comarca**: Passo Fundo\n- **Competência**: Cível - Geral\n- **Data Ajuizamento**: 2025-07-20T10:30:00\n- **Assuntos**: Cobrança\n- **Valor da Causa**: R$ 1.250,00\n- **Órgão Julgador**: Juízo da 1ª Vara Cível da Comarca de Passo Fundo',
            'prompt_nome': 'prompt inicial',
            'prompt_completo': 'Analise o contexto da intimação e classifique adequadamente.',
            'classificacao_manual': 'RENUNCIAR PRAZO',
            'informacao_adicional': 'intimação para apresentação de defesa',
            'resultado_ia': 'ELABORAR PEÇA',
            'acertou': False,
            'modelo': 'gpt-4',
            'temperatura': 0.0,
            'tempo_processamento': 3.1,

            'resposta_completa': 'Outra resposta completa da IA.'
        },
        {
            'id': 'analise-003',
            'intimacao_id': 'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
            'data_analise': '2025-08-11T18:03:42',
            'contexto': '# Dados do Processo\n## Informações Básicas do Processo\n- **Classe Processual**: Procedimento Comum\n- **Comarca**: Erechim\n- **Competência**: Cível - Geral\n- **Data Ajuizamento**: 2025-07-22T16:45:00\n- **Assuntos**: Indenização\n- **Valor da Causa**: R$ 5.000,00\n- **Órgão Julgador**: Juízo da 3ª Vara Cível da Comarca de Erechim',
            'prompt_nome': 'prompt inicial',
            'prompt_completo': 'Analise o contexto da intimação e classifique adequadamente.',
            'classificacao_manual': 'RENUNCIAR PRAZO',
            'informacao_adicional': 'decisão interlocutória sobre pedido de liminar',
            'resultado_ia': 'ELABORAR PEÇA',
            'acertou': False,
            'modelo': 'gpt-4',
            'temperatura': 0.0,
            'tempo_processamento': 1.8,

            'resposta_completa': 'Terceira resposta completa da IA.'
        },
        {
            'id': 'analise-004',
            'intimacao_id': 'b2c3d4e5-f6g7-8901-bcde-f23456789012',
            'data_analise': '2025-08-11T18:04:18',
            'contexto': '# Dados do Processo\n## Informações Básicas do Processo\n- **Classe Processual**: Ação de Cobrança\n- **Comarca**: Caxias do Sul\n- **Competência**: Cível - Geral\n- **Data Ajuizamento**: 2025-07-25T09:20:00\n- **Assuntos**: Cobrança\n- **Valor da Causa**: R$ 2.800,00\n- **Órgão Julgador**: Juízo da 2ª Vara Cível da Comarca de Caxias do Sul',
            'prompt_nome': 'prompt inicial',
            'prompt_completo': 'Analise o contexto da intimação e classifique adequadamente.',
            'classificacao_manual': 'RENUNCIAR PRAZO',
            'informacao_adicional': 'decisão que recebe a fase de cumprimento de sentença',
            'resultado_ia': 'ELABORAR PEÇA',
            'acertou': False,
            'modelo': 'gpt-4',
            'temperatura': 0.0,
            'tempo_processamento': 2.8,

            'resposta_completa': 'Quarta resposta completa da IA.'
        },
        {
            'id': 'analise-005',
            'intimacao_id': 'c3d4e5f6-g7h8-9012-cdef-345678901234',
            'data_analise': '2025-08-11T18:05:33',
            'contexto': '# Dados do Processo\n## Informações Básicas do Processo\n- **Classe Processual**: Execução de Sentença\n- **Comarca**: Bento Gonçalves\n- **Competência**: Cível - Geral\n- **Data Ajuizamento**: 2025-07-28T14:10:00\n- **Assuntos**: Execução\n- **Valor da Causa**: R$ 3.500,00\n- **Órgão Julgador**: Juízo da 1ª Vara Cível da Comarca de Bento Gonçalves',
            'prompt_nome': 'prompt inicial',
            'prompt_completo': 'Analise o contexto da intimação e classifique adequadamente.',
            'classificacao_manual': 'RENUNCIAR PRAZO',
            'informacao_adicional': 'intimação para apresentação de defesa',
            'resultado_ia': 'ELABORAR PEÇA',
            'acertou': False,
            'modelo': 'gpt-4',
            'temperatura': 0.0,
            'tempo_processamento': 2.2,

            'resposta_completa': 'Quinta resposta completa da IA.'
        },
        {
            'id': 'analise-006',
            'intimacao_id': 'd4e5f6g7-h8i9-0123-defg-456789012345',
            'data_analise': '2025-08-11T18:06:47',
            'contexto': '# Dados do Processo\n## Informações Básicas do Processo\n- **Classe Processual**: Procedimento Comum\n- **Comarca**: Farroupilha\n- **Competência**: Cível - Geral\n- **Data Ajuizamento**: 2025-07-30T11:35:00\n- **Assuntos**: Indenização\n- **Valor da Causa**: R$ 4.200,00\n- **Órgão Julgador**: Juízo da 3ª Vara Cível da Comarca de Farroupilha',
            'prompt_nome': 'prompt inicial',
            'prompt_completo': 'Analise o contexto da intimação e classifique adequadamente.',
            'classificacao_manual': 'RENUNCIAR PRAZO',
            'informacao_adicional': 'decisão interlocutória sobre pedido de liminar',
            'resultado_ia': 'ELABORAR PEÇA',
            'acertou': False,
            'modelo': 'gpt-4',
            'temperatura': 0.0,
            'tempo_processamento': 3.0,

            'resposta_completa': 'Sexta resposta completa da IA.'
        }
    ]
    
    prompts_demo = [
        {'id': 'prompt-001', 'nome': 'Classificar Intimação'},
        {'id': 'prompt-002', 'nome': 'Analisar Processo'},
        {'id': 'prompt-003', 'nome': 'Extrair Informações'}
    ]
    
    # Dados de paginação para demonstração
    paginacao_demo = {
        'pagina_atual': 1,
        'total_paginas': 1,
        'itens_por_pagina': 10,
        'total_itens': len(analises_demo),
        'inicio': 1,
        'fim': len(analises_demo)
    }
    
    # Dados de análises com informações completas de intimação para demonstração dos cards
    analises_demo_com_cards = [
        {
            'id': 'analise-001',
            'intimacao_id': 'f71ac7be-a6d8-4c00-bd62-e5a4d94fad8c',
            'data_analise': '2025-08-11T18:01:31',
            'contexto': 'Intimação para cumprimento de sentença - Sucumbência',
            'prompt_nome': 'prompt inicial',
            'prompt_completo': 'Analise o contexto da intimação e classifique adequadamente.',
            'classificacao_manual': 'ELABORAR PEÇA',
            'informacao_adicional': 'decisão que recebe a fase de cumprimento de sentença',
            'resultado_ia': 'ELABORAR PEÇA',
            'acertou': True,
            'modelo': 'gpt-4',
            'temperatura': 0.0,
            'tempo_processamento': 2.5,

            'resposta_completa': 'Resposta completa da IA para demonstração.',
            'intimacao': {
                'id': 'f71ac7be-a6d8-4c00-bd62-e5a4d94fad8c',
                'processo': '5000002-31.2025.8.21.0103',
                'orgao_julgador': 'Juízo da 2ª Vara Cível da Comarca de Carazinho',
                'classe': 'Cumprimento de sentença',
                'disponibilizacao': '11/08/2025 às 18:01',
                'intimado': 'DEFENSORIA PÚBLICA DO ESTADO DO RIO GRANDE DO SUL',
                'status': 'Pendente',
                'prazo': '15 dias'
            }
        },
        {
            'id': 'analise-002',
            'intimacao_id': '7240e914-6832-4a83-b159-4dbcb8f43854',
            'data_analise': '2025-08-11T18:02:15',
            'contexto': 'Intimação para apresentação de defesa em execução',
            'prompt_nome': 'prompt inicial',
            'prompt_completo': 'Analise o contexto da intimação e classifique adequadamente.',
            'classificacao_manual': 'URGÊNCIA',
            'informacao_adicional': 'intimação para apresentação de defesa',
            'resultado_ia': 'ELABORAR PEÇA',
            'acertou': False,
            'modelo': 'gpt-4',
            'temperatura': 0.0,
            'tempo_processamento': 3.1,

            'resposta_completa': 'Outra resposta completa da IA.',
            'intimacao': {
                'id': '7240e914-6832-4a83-b159-4dbcb8f43854',
                'processo': '5000123-45.2025.8.21.0104',
                'orgao_julgador': 'Juízo da 1ª Vara Cível da Comarca de Passo Fundo',
                'classe': 'Execução de Título Extrajudicial',
                'disponibilizacao': '11/08/2025 às 18:02',
                'intimado': 'DEFENSORIA PÚBLICA DO ESTADO DO RIO GRANDE DO SUL',
                'status': 'Urgente',
                'prazo': '5 dias'
            }
        },
        {
            'id': 'analise-003',
            'intimacao_id': 'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
            'data_analise': '2025-08-11T18:03:42',
            'contexto': 'Decisão interlocutória sobre pedido de liminar',
            'prompt_nome': 'prompt inicial',
            'prompt_completo': 'Analise o contexto da intimação e classifique adequadamente.',
            'classificacao_manual': 'ANALISAR PROCESSO',
            'informacao_adicional': 'decisão interlocutória sobre pedido de liminar',
            'resultado_ia': 'ANALISAR PROCESSO',
            'acertou': True,
            'modelo': 'gpt-4',
            'temperatura': 0.0,
            'tempo_processamento': 1.8,

            'resposta_completa': 'Terceira resposta completa da IA.',
            'intimacao': {
                'id': 'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
                'processo': '5000456-78.2025.8.21.0105',
                'orgao_julgador': 'Juízo da 3ª Vara Cível da Comarca de Erechim',
                'classe': 'Procedimento Comum',
                'disponibilizacao': '11/08/2025 às 18:03',
                'intimado': 'DEFENSORIA PÚBLICA DO ESTADO DO RIO GRANDE DO SUL',
                'status': 'Concluído',
                'prazo': '10 dias'
            }
        }
    ]
    
    return render_template('componentes_demo.html', 
                         analises=analises_demo, 
                         prompts_demo=prompts_demo,
                         paginacao=paginacao_demo,
                         analises_demo_com_cards=analises_demo_com_cards)

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
                    analise['informacao_adicional'] = intimacao.get('informacao_adicional')
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
                    "N/A"  # Custo removido - simulação desabilitada
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
                'portal_defensoria_link': request.form.get('portal_defensoria_link', ''),
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
        
        # Buscar chave da API da variável de ambiente (não expor no frontend)
        api_key = os.environ.get('OPENAI_API_KEY', '')
        if api_key:
            config['openai_api_key'] = '***CONFIGURADO VIA .ENV***'
        else:
            config['openai_api_key'] = 'NÃO CONFIGURADA'
        
        # Debug: verificar se a chave está sendo passada
        print("=== DEBUG: Chave da API configurada via variável de ambiente ===")
        
        # Usar o ai_manager_service global
        provedor_atual = ai_manager_service.get_current_provider()
        
        # Valores padrão para configurações
        config.setdefault('ai_provider', provedor_atual)
        config.setdefault('modelo_padrao', 'gpt-4')
        # Não definir valor padrão para azure_temperatura se já existe
        if 'azure_temperatura' not in config:
            config['azure_temperatura'] = 0.7
        if 'azure_max_tokens' not in config:
            config['azure_max_tokens'] = 500
        config.setdefault('timeout_padrao', 30)
        config.setdefault('max_retries', 3)
        config.setdefault('retry_delay', 1)
        config.setdefault('itens_por_pagina', 25)
        config.setdefault('formato_data', 'DD/MM/YYYY')
        config.setdefault('tema', 'light')
        config.setdefault('idioma', 'pt-BR')
        config.setdefault('portal_defensoria_link', '')
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
        
        # Obter informações do provedor atual
        provedor_atual = ai_manager_service.get_current_provider()
        
        # Usar todos os modelos disponíveis (OpenAI + Azure) para a página de configurações
        modelos_disponiveis = list(set(Config.OPENAI_MODELS + Config.AZURE_OPENAI_MODELS))
        modelos_disponiveis.sort()  # Ordenar alfabeticamente
        
        # Carregar preços da API
        precos_openai = config.get('precos_openai', Config.PRECOS_OPENAI_PADRAO)
        precos_azure = config.get('precos_azure', Config.PRECOS_AZURE_PADRAO)
        
        return render_template('configuracoes.html',
                             config=config,
                             provedor_atual=provedor_atual,
                             modelos_disponiveis=modelos_disponiveis,
                             status_sistema=status_sistema,
                             uso_api=uso_api,
                             logs_recentes=logs_recentes,
                             precos_openai=precos_openai,
                             precos_azure=precos_azure)
                             
    except Exception as e:
        flash(f'Erro ao carregar configurações: {str(e)}', 'error')
        return render_template('configuracoes.html',
                             config=DEFAULT_CONFIG,
                             provedor_atual='openai',
                             modelos_disponiveis=Config.OPENAI_MODELS,
                             precos_openai=Config.PRECOS_OPENAI_PADRAO,
                             precos_azure=Config.PRECOS_AZURE_PADRAO,
                             status_sistema={},
                             uso_api={},
                             logs_recentes=[])

# Rotas auxiliares e APIs

@app.route('/api/intimacoes/<id>/editar', methods=['POST'])
def editar_intimacao_api(id):
    """API para editar campo de intimação"""
    print(f"=== DEBUG: EDITANDO INTIMAÇÃO ===")
    print(f"ID da intimação: {id}")
    
    try:
        data = request.get_json()
        campo = data.get('campo')
        valor = data.get('valor')
        
        print(f"DEBUG: Campo: {campo}, Valor: {valor}")
        
        if not campo:
            return jsonify({'success': False, 'error': 'Campo não especificado'}), 400
        
        # Buscar intimação atual
        intimacao = data_service.get_intimacao_by_id(id)
        if not intimacao:
            return jsonify({'success': False, 'error': 'Intimação não encontrada'}), 404
        
        # Atualizar o campo
        intimacao[campo] = valor
        
        # Salvar intimação atualizada
        data_service.save_intimacao(intimacao)
        
        print(f"DEBUG: Campo {campo} atualizado com sucesso")
        return jsonify({'success': True, 'message': 'Campo atualizado com sucesso'})
        
    except Exception as e:
        print(f"DEBUG: Erro ao editar intimação: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

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
        analise_ids = data.get('analise_ids', [])
        
        # Suporte para exclusão única (compatibilidade)
        if 'analise_id' in data:
            analise_ids = [data['analise_id']]
        
        if not analise_ids:
            return jsonify({'error': 'IDs das análises são obrigatórios'}), 400
        
        print(f"=== DEBUG: Excluindo {len(analise_ids)} análises: {analise_ids} ===")
        
        excluidas = 0
        erros = []
        
        for analise_id in analise_ids:
            try:
                # Excluir diretamente da tabela de análises
                sucesso = data_service.delete_analise(analise_id)
                if sucesso:
                    excluidas += 1
                    print(f"✅ Análise {analise_id} excluída")
                else:
                    erros.append(f"Análise {analise_id} não encontrada")
                    print(f"❌ Análise {analise_id} não encontrada")
            except Exception as e:
                erros.append(f"Erro ao excluir {analise_id}: {str(e)}")
                print(f"❌ Erro ao excluir análise {analise_id}: {e}")
        
        if excluidas > 0:
            print(f"✅ {excluidas} análises excluídas com sucesso")
        
        return jsonify({
            'success': True,
            'message': f'{excluidas} análises excluídas com sucesso',
            'excluidas': excluidas,
            'erros': erros
        })
        
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

@app.route('/api/prompts/<id>/toggle-ativo', methods=['POST'])
def toggle_prompt_ativo(id):
    """Alternar status ativo/inativo de um prompt"""
    try:
        success = data_service.toggle_prompt_ativo(id)
        if success:
            return jsonify({'success': True, 'message': 'Status do prompt alterado com sucesso'})
        else:
            return jsonify({'success': False, 'error': 'Prompt não encontrado'}), 404
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/configuracoes/testar-conexao', methods=['POST'])
def testar_conexao_ai():
    """API para testar conexão com o provedor de IA atual"""
    try:
        # Testar conexão usando o gerenciador de IA
        sucesso, mensagem = ai_manager_service.test_connection()
        
        if sucesso:
            provider_name = ai_manager_service.get_provider_display_name()
            return jsonify({
                'success': True,
                'message': f'Conexão com {provider_name} estabelecida com sucesso',
                'provider': provider_name,
                'models': ai_manager_service.get_available_models()[:3]  # Primeiros 3 modelos
            })
        else:
            return jsonify({
                'success': False,
                'message': mensagem
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro ao testar conexão: {str(e)}'
        }), 500

@app.route('/api/configuracoes/provedor', methods=['POST'])
def alterar_provedor_ia():
    """API para alterar o provedor de IA"""
    try:
        data = request.get_json()
        provider = data.get('provider', 'openai')
        
        # Validar provedor
        if provider not in ai_manager_service.get_available_providers():
            return jsonify({
                'success': False,
                'message': f'Provedor "{provider}" não disponível'
            }), 400
        
        # Alterar provedor
        if ai_manager_service.set_provider(provider):
            return jsonify({
                'success': True,
                'message': f'Provedor alterado para {provider} com sucesso',
                'current_provider': ai_manager_service.get_current_provider(),
                'provider_name': ai_manager_service.get_provider_display_name()
            })
        else:
            return jsonify({
                'success': False,
                'message': f'Falha ao alterar para o provedor {provider}'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro ao alterar provedor: {str(e)}'
        }), 500

@app.route('/api/configuracoes/testar-azure', methods=['POST'])
def testar_conexao_azure():
    """API para testar conexão com Azure OpenAI"""
    try:
        data = request.get_json()
        
        # Verificar se deve usar credenciais do .env
        if data.get('use_env_credentials'):
            # Usar credenciais das variáveis de ambiente
            from services.azure_service import AzureService
            azure_service = AzureService()
            
            # Testar conexão com credenciais do .env
            sucesso, mensagem = azure_service.test_connection()
            
            if sucesso:
                return jsonify({
                    'success': True,
                    'message': 'Conexão com Azure OpenAI estabelecida com sucesso!',
                    'models': azure_service.get_available_models()[:3]
                })
            else:
                return jsonify({
                    'success': False,
                    'message': mensagem
                }), 500
        else:
            # Usar credenciais fornecidas no formulário (modo legado)
            api_key = data.get('api_key')
            endpoint = data.get('endpoint')
            api_version = data.get('api_version', '2024-02-15-preview')
            
            if not api_key or not endpoint:
                return jsonify({
                    'success': False,
                    'message': 'Chave da API e endpoint são obrigatórios'
                }), 400
            
            # Importar e testar Azure OpenAI temporariamente
            from services.azure_service import AzureService
            azure_service = AzureService()
            
            # Atualizar credenciais temporariamente para teste
            azure_service.update_credentials(api_key, endpoint, api_version)
            
            # Testar conexão
            sucesso, mensagem = azure_service.test_connection()
            
            if sucesso:
                return jsonify({
                    'success': True,
                    'message': 'Conexão com Azure OpenAI estabelecida com sucesso!',
                    'models': azure_service.get_available_models()[:3]
                })
            else:
                return jsonify({
                    'success': False,
                    'message': mensagem
                }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro ao testar conexão Azure: {str(e)}'
        }), 500

@app.route('/api/configuracoes/azure', methods=['POST'])
def salvar_configuracao_azure():
    """API para salvar configurações do Azure OpenAI"""
    try:
        data = request.get_json()
        
        # Carregar configuração atual
        config = data_service.get_config() or {}
        
        # Atualizar configurações do Azure
        config.update({
            'azure_api_key': data.get('azure_api_key', ''),
            'azure_endpoint': data.get('azure_endpoint', ''),
            'azure_api_version': data.get('azure_api_version', '2024-02-15-preview'),
            'azure_deployment': data.get('azure_deployment', 'gpt-4'),
            'azure_temperatura': float(data.get('azure_temperatura', 0.7)),
            'azure_max_tokens': int(data.get('azure_max_tokens', 500)),
            'azure_timeout': int(data.get('azure_timeout', 30)),
            'azure_analise_paralela': int(data.get('azure_analise_paralela', 1)),
            'azure_delay_entre_lotes': float(data.get('azure_delay_entre_lotes', 0.5))
        })
        
        # Salvar configuração
        data_service.save_config(config)
        
        return jsonify({
            'success': True,
            'message': 'Configurações do Azure OpenAI salvas com sucesso!'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro ao salvar configurações: {str(e)}'
        }), 500

@app.route('/api/configuracoes/precos-openai', methods=['POST'])
def salvar_precos_openai():
    """API para salvar preços da OpenAI"""
    try:
        data = request.get_json()
        
        # Carregar configuração atual
        config = data_service.get_config() or {}
        
        # Atualizar preços OpenAI (formato aninhado para compatibilidade com template)
        precos_openai = {
            'gpt-4o': {
                'input': float(data.get('openai_gpt4o_input', 2.50)),
                'output': float(data.get('openai_gpt4o_output', 10.00))
            },
            'gpt-4o-mini': {
                'input': float(data.get('openai_gpt4o_mini_input', 0.15)),
                'output': float(data.get('openai_gpt4o_mini_output', 0.60))
            },
            'gpt-4-turbo': {
                'input': float(data.get('openai_gpt4_turbo_input', 10.00)),
                'output': float(data.get('openai_gpt4_turbo_output', 30.00))
            },
            'gpt-3.5-turbo': {
                'input': float(data.get('openai_gpt35_turbo_input', 0.50)),
                'output': float(data.get('openai_gpt35_turbo_output', 1.50))
            },
            'data_atualizacao': data.get('data_atualizacao_openai', datetime.now().strftime('%Y-%m-%d'))
        }
        
        config['precos_openai'] = precos_openai
        
        # Salvar configuração
        data_service.save_config(config)
        
        return jsonify({
            'success': True,
            'message': 'Preços da OpenAI salvos com sucesso!'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro ao salvar preços: {str(e)}'
        }), 500



@app.route('/api/configuracoes/precos-azure', methods=['POST'])
def salvar_precos_azure():
    """API para salvar preços do Azure OpenAI"""
    try:
        data = request.get_json()
        
        # Carregar configuração atual
        config = data_service.get_config() or {}
        
        # Atualizar preços Azure (formato aninhado para compatibilidade com template)
        precos_azure = {
            'gpt-4o': {
                'input': float(data.get('azure_gpt4o_input', 5.00)),
                'output': float(data.get('azure_gpt4o_output', 15.00))
            },
            'gpt-4o-mini': {
                'input': float(data.get('azure_gpt4o_mini_input', 0.165)),
                'output': float(data.get('azure_gpt4o_mini_output', 0.66))
            },
            'gpt-4-turbo': {
                'input': float(data.get('azure_gpt4_turbo_input', 10.00)),
                'output': float(data.get('azure_gpt4_turbo_output', 30.00))
            },
            'gpt-3.5-turbo': {
                'input': float(data.get('azure_gpt35_turbo_input', 0.50)),
                'output': float(data.get('azure_gpt35_turbo_output', 1.50))
            },
            'data_atualizacao': data.get('data_atualizacao_azure', datetime.now().strftime('%Y-%m-%d'))
        }
        
        config['precos_azure'] = precos_azure
        
        # Salvar configuração
        data_service.save_config(config)
        
        return jsonify({
            'success': True,
            'message': 'Preços do Azure OpenAI salvos com sucesso!'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro ao salvar preços: {str(e)}'
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

@app.route('/api/extrair-informacoes', methods=['POST'])
def extrair_informacoes():
    """Extrair informações do contexto da intimação usando IA"""
    try:
        data = request.get_json()
        contexto = data.get('contexto', '').strip()
        
        if not contexto:
            return jsonify({'success': False, 'error': 'Contexto não fornecido'})
        
        print(f"=== DEBUG: Extraindo informações do contexto ===")
        print(f"Contexto length: {len(contexto)}")
        
        # Prompt para extrair informações
        prompt_extrair = f"""
Analise o seguinte contexto de intimação e extraia as informações solicitadas. Retorne APENAS um JSON válido com as seguintes chaves:

- processo: número do processo (se encontrado)
- orgao_julgador: órgão julgador (se encontrado)
- classe: classe processual (se encontrada)
- disponibilizacao: data de disponibilização (se encontrada)
- intimado: nome do intimado (se encontrado)
- status: status da intimação (se encontrado)
- prazo: prazo da intimação (se encontrado)
- defensor: nome do defensor responsável (se encontrado)
- id_tarefa: identificador da tarefa (se encontrado)

Se alguma informação não for encontrada, retorne null para essa chave.
Não tente extrair cor_etiqueta - esse campo será preenchido manualmente pelo usuário.

Contexto da intimação:
{contexto}

Retorne APENAS o JSON, sem texto adicional.
"""
        
        # Usar o mesmo padrão da análise de intimações que funciona
        # Preparar parâmetros igual à análise
        parametros = {
            'temperatura': 0.1,
            'max_tokens': 500,
            'top_p': 1.0
        }
        
        # Fazer chamada para IA usando o gerenciador igual à análise
        resultado_ia, resposta, tokens_info = ai_manager_service.analisar_intimacao(
            contexto=contexto,
            prompt_template=prompt_extrair,
            parametros=parametros
        )
        
        print(f"=== DEBUG: Resposta da IA: {resposta}")
        print(f"=== DEBUG: Tokens info: {tokens_info}")
        
        # Tentar extrair JSON da resposta
        try:
            # Limpar a resposta para extrair apenas o JSON
            json_str = resposta.strip()
            if json_str.startswith('```json'):
                json_str = json_str[7:]
            if json_str.endswith('```'):
                json_str = json_str[:-3]
            
            import json
            informacoes = json.loads(json_str)
            
            print(f"=== DEBUG: Informações extraídas: {informacoes}")
            
            return jsonify({
                'success': True,
                'informacoes': informacoes
            })
            
        except json.JSONDecodeError as e:
            print(f"=== ERRO: JSON inválido: {e}")
            print(f"Resposta da IA: {resposta}")
            return jsonify({
                'success': False,
                'error': 'Erro ao processar resposta da IA'
            })
            
    except Exception as e:
        print(f"=== ERRO na extração: {e}")
        return jsonify({'success': False, 'error': str(e)})

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

@app.route('/api/restaurar-dados-demo', methods=['POST'])
def restaurar_dados_demo():
    """API para restaurar dados mockados de demonstração"""
    try:
        # Dados mockados para demonstração
        dados_demo = {
            "analises": [
                {
                    "id": "demo-1",
                    "data": "2024-01-15",
                    "intimacao": "Intimação Demo 1",
                    "prompt": "Prompt de demonstração 1",
                    "classificacao_manual": "Urgente",
                    "informacao_ia": "Análise de demonstração 1",
                    "resultado_ia": "Resultado positivo",
                    "status": "Concluída",
                    "configuracoes": "Config padrão",
                    "tempo": "2.5s",
                    "custo": "R$ 0,15",
                    "prompt_completo": "Prompt completo de demonstração 1",
                    "resposta_ia": "Resposta detalhada da IA para demonstração"
                },
                {
                    "id": "demo-2",
                    "data": "2024-01-16",
                    "intimacao": "Intimação Demo 2",
                    "prompt": "Prompt de demonstração 2",
                    "classificacao_manual": "Normal",
                    "informacao_ia": "Análise de demonstração 2",
                    "resultado_ia": "Resultado neutro",
                    "status": "Em andamento",
                    "configuracoes": "Config personalizada",
                    "tempo": "1.8s",
                    "custo": "R$ 0,12",
                    "prompt_completo": "Prompt completo de demonstração 2",
                    "resposta_ia": "Resposta detalhada da IA para demonstração 2"
                },
                {
                    "id": "demo-3",
                    "data": "2024-01-17",
                    "intimacao": "Intimação Demo 3",
                    "prompt": "Prompt de demonstração 3",
                    "classificacao_manual": "Baixa",
                    "informacao_ia": "Análise de demonstração 3",
                    "resultado_ia": "Resultado negativo",
                    "status": "Erro",
                    "configuracoes": "Config avançada",
                    "tempo": "3.2s",
                    "custo": "R$ 0,18",
                    "prompt_completo": "Prompt completo de demonstração 3",
                    "resposta_ia": "Resposta detalhada da IA para demonstração 3"
                }
            ]
        }
        
        # Os dados agora são salvos no banco SQLite, não mais em JSON
        # Esta função foi mantida apenas para compatibilidade
        print("ℹ️  Dados de demonstração - salvamento em JSON descontinuado (usando SQLite)")
        
        return jsonify({
            'success': True,
            'message': 'Dados de demonstração restaurados com sucesso!',
            'total_analises': len(dados_demo['analises'])
        })
    except Exception as e:
        return jsonify({
            'success': False, 
            'message': f'Erro ao restaurar dados: {str(e)}'
        }), 500

@app.route('/api/precos-modelos')
def obter_precos_modelos():
    """Retorna os preços atuais dos modelos de IA configurados"""
    try:
        # Obter configurações atuais
        config_data = data_service.get_config()
        
        # Preços OpenAI (usar padrão se não configurado)
        precos_openai = config_data.get('precos_openai')
        if not precos_openai:
            precos_openai = Config.PRECOS_OPENAI_PADRAO.copy()
            # Remover data_atualizacao se existir
            precos_openai.pop('data_atualizacao', None)
        
        # Preços Azure (usar padrão se não configurado)
        precos_azure = config_data.get('precos_azure')
        if not precos_azure:
            precos_azure = Config.PRECOS_AZURE_PADRAO.copy()
            # Remover data_atualizacao se existir
            precos_azure.pop('data_atualizacao', None)
        
        return jsonify({
            'success': True,
            'precos': {
                'openai': precos_openai,
                'azure': precos_azure
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro ao obter preços dos modelos: {str(e)}'
        }), 500

@app.route('/api/cancelar-analise', methods=['POST'])
def cancelar_analise_api():
    """Cancela uma análise em andamento"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        
        if not session_id:
            return jsonify({
                'success': False,
                'message': 'Session ID é obrigatório'
            }), 400
        
        if cancelar_analise(session_id):
            return jsonify({
                'success': True,
                'message': 'Análise cancelada com sucesso'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Análise não encontrada ou já finalizada'
            }), 404
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro ao cancelar análise: {str(e)}'
        }), 500

@app.route('/api/tooltip-custo')
def gerar_tooltip_custo():
    """Gera tooltip de custo usando o serviço de custo"""
    try:
        modelo = request.args.get('modelo', 'gpt-4o-mini')
        tokens_input = int(request.args.get('tokens_input', 0))
        tokens_output = int(request.args.get('tokens_output', 0))
        provider = request.args.get('provider', 'azure')
        custo_real = float(request.args.get('custo_real', 0))
        
        tooltip_html = cost_service.generate_cost_tooltip(
            tokens_input, tokens_output, modelo, provider, custo_real
        )
        
        return jsonify({
            'success': True,
            'tooltip_html': tooltip_html
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro ao gerar tooltip: {str(e)}'
        }), 500

@app.route('/api/analise-progresso')
def analise_progresso():
    """Endpoint para Server-Sent Events do progresso da análise"""
    # Capturar argumentos ANTES de criar a função generate
    total_intimacoes = request.args.get('total', type=int, default=10)
    
    def generate():
        try:
            print(f"=== DEBUG: Iniciando progresso para {total_intimacoes} intimações ===")
            
            # Enviar início
            yield f"data: {json.dumps({'tipo': 'inicio', 'total': total_intimacoes, 'atual': 0})}\n\n"
            
            # Simular progresso real (sem cache)
            for i in range(1, total_intimacoes + 1):
                # Simular tempo de processamento real
                time.sleep(1)  # 1 segundo por intimação
                
                # Descrições realistas
                descricoes = [
                    f"Processando intimação {i} de {total_intimacoes}",
                    f"Analisando contexto da intimação {i}",
                    f"Classificando intimação {i} com IA",
                    f"Salvando resultado da intimação {i}",
                    f"Finalizando análise da intimação {i}"
                ]
                descricao = descricoes[i % len(descricoes)]
                
                yield f"data: {json.dumps({'tipo': 'progresso', 'total': total_intimacoes, 'atual': i, 'descricao': descricao})}\n\n"
            
            # Enviar conclusão
            yield f"data: {json.dumps({'tipo': 'conclusao', 'total': total_intimacoes, 'atual': total_intimacoes, 'descricao': 'Análise concluída com sucesso!'})}\n\n"
            
        except Exception as e:
            print(f"=== ERRO no progresso: {e} ===")
            yield f"data: {json.dumps({'tipo': 'erro', 'mensagem': str(e)})}\n\n"
    
    return Response(generate(), mimetype='text/event-stream')

# Rotas de Backup do Banco
@app.route('/api/backup/banco')
def download_backup_banco():
    """Endpoint para download do banco de dados"""
    try:
        db_path = 'data/database.db'
        
        if not os.path.exists(db_path):
            return jsonify({
                'success': False,
                'message': 'Banco de dados não encontrado'
            }), 404
        
        # Gerar nome do arquivo com timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'database_backup_{timestamp}.db'
        
        return send_file(
            db_path,
            as_attachment=True,
            download_name=filename,
            mimetype='application/octet-stream'
        )
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro ao fazer backup: {str(e)}'
        }), 500

@app.route('/api/backup/stats')
def stats_banco():
    """Endpoint para estatísticas do banco de dados"""
    try:
        db_path = 'data/database.db'
        
        if not os.path.exists(db_path):
            return jsonify({
                'success': False,
                'message': 'Banco de dados não encontrado'
            })
        
        # Conectar ao banco
        import sqlite3
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Contar registros em cada tabela
        stats = {}
        
        # Prompts
        cursor.execute("SELECT COUNT(*) FROM prompts")
        stats['prompts'] = cursor.fetchone()[0]
        
        # Intimações
        cursor.execute("SELECT COUNT(*) FROM intimacoes")
        stats['intimacoes'] = cursor.fetchone()[0]
        
        # Análises
        cursor.execute("SELECT COUNT(*) FROM analises")
        stats['analises'] = cursor.fetchone()[0]
        
        # Tamanho do arquivo
        size_bytes = os.path.getsize(db_path)
        stats['tamanho_mb'] = round(size_bytes / (1024 * 1024), 2)
        
        conn.close()
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro ao obter estatísticas: {str(e)}'
        }), 500

@app.route('/api/intimacoes/informacoes-adicionais', methods=['POST'])
def obter_informacoes_adicionais_intimacoes():
    """Obter informações adicionais de múltiplas intimações"""
    try:
        data = request.get_json()
        intimacoes_ids = data.get('intimacoes_ids', [])
        
        if not intimacoes_ids:
            return jsonify({
                'success': False,
                'message': 'Nenhuma intimação selecionada'
            }), 400
        
        # Buscar intimações no banco
        intimacoes = []
        for intimacao_id in intimacoes_ids:
            intimacao = data_service.get_intimacao_by_id(intimacao_id)
            if intimacao:
                intimacoes.append({
                    'id': intimacao_id,
                    'contexto': intimacao.get('contexto', ''),
                    'informacao_adicional': intimacao.get('informacao_adicional', '')
                })
        
        return jsonify({
            'success': True,
            'intimacoes': intimacoes
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro ao buscar informações: {str(e)}'
        }), 500

@app.route('/api/analises/informacoes-adicionais', methods=['POST'])
def obter_informacoes_adicionais_analises():
    """Obter informações adicionais de múltiplas análises"""
    try:
        data = request.get_json()
        analises_ids = data.get('analises_ids', [])
        
        if not analises_ids:
            return jsonify({
                'success': False,
                'message': 'Nenhuma análise selecionada'
            }), 400
        
        # Buscar análises no banco
        analises = []
        for analise_id in analises_ids:
            analise = data_service.get_analise_by_id(analise_id)
            if analise:
                # Buscar intimação associada para obter informações adicionais e contexto
                intimacao = data_service.get_intimacao_by_id(analise.get('intimacao_id'))
                analises.append({
                    'id': analise_id,
                    'intimacao_id': analise.get('intimacao_id'),
                    'contexto': intimacao.get('contexto', '') if intimacao else '',
                    'informacao_adicional': intimacao.get('informacao_adicional', '') if intimacao else ''
                })
        
        return jsonify({
            'success': True,
            'analises': analises
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro ao obter informações: {str(e)}'
        }), 500

@app.route('/api/intimacoes/<intimacao_id>/prompts-acerto')
def obter_prompts_acerto_intimacao(intimacao_id):
    """API para obter prompts e taxas de acerto de uma intimação específica"""
    try:
        # Buscar prompts e taxas de acerto da intimação
        prompts_acerto = data_service.get_prompts_acerto_por_intimacao(intimacao_id)
        
        return jsonify({
            'success': True,
            'prompts_acerto': prompts_acerto
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro ao obter prompts e acertos: {str(e)}'
        }), 500

@app.route('/api/intimacoes/taxa-acerto')
def obter_taxa_acerto_intimacoes():
    """API para obter taxa de acerto de todas as intimações"""
    try:
        # Buscar taxa de acerto de cada intimação
        taxas_acerto = data_service.get_taxa_acerto_por_intimacao()
        
        return jsonify({
            'success': True,
            'taxas_acerto': taxas_acerto
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro ao obter taxas de acerto: {str(e)}'
        }), 500

@app.route('/api/filtros/analise')
def obter_filtros_analise():
    """API para obter dados de filtros para a página de análise"""
    try:
        # Buscar classificações únicas do banco
        classificacoes = data_service.get_classificacoes_unicas()
        
        # Buscar defensores únicos do banco
        defensores = data_service.get_defensores_unicos()
        
        # Buscar classes únicas do banco
        classes = data_service.get_classes_unicas()
        
        return jsonify({
            'success': True,
            'classificacoes': classificacoes,
            'defensores': defensores,
            'classes': classes
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro ao obter filtros: {str(e)}'
        }), 500

@app.route('/api/backup/restaurar', methods=['POST'])
def restaurar_backup_banco():
    """Endpoint para restaurar backup do banco de dados"""
    try:
        # Verificar se foi enviado um arquivo
        if 'backup_file' not in request.files:
            return jsonify({
                'success': False,
                'message': 'Nenhum arquivo foi enviado'
            }), 400
        
        file = request.files['backup_file']
        
        # Verificar se o arquivo foi selecionado
        if file.filename == '':
            return jsonify({
                'success': False,
                'message': 'Nenhum arquivo foi selecionado'
            }), 400
        
        # Verificar extensão do arquivo
        if not file.filename.lower().endswith('.db'):
            return jsonify({
                'success': False,
                'message': 'Arquivo deve ter extensão .db'
            }), 400
        
        # Verificar tamanho do arquivo (máximo 100MB)
        max_size = 100 * 1024 * 1024  # 100MB
        file.seek(0, 2)  # Ir para o final do arquivo
        file_size = file.tell()
        file.seek(0)  # Voltar para o início
        
        if file_size > max_size:
            return jsonify({
                'success': False,
                'message': 'Arquivo muito grande. Máximo 100MB.'
            }), 400
        
        # Caminhos dos arquivos
        db_path = 'data/database.db'
        backup_dir = 'data/backups'
        
        # Criar diretório de backup se não existir
        os.makedirs(backup_dir, exist_ok=True)
        
        # Fazer backup do banco atual antes de restaurar
        if os.path.exists(db_path):
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = os.path.join(backup_dir, f'backup_antes_restauracao_{timestamp}.db')
            
            import shutil
            shutil.copy2(db_path, backup_path)
            print(f"Backup do banco atual salvo em: {backup_path}")
        
        # Salvar o arquivo de backup enviado
        filename = secure_filename(file.filename)
        temp_path = os.path.join(backup_dir, f'restore_{timestamp}_{filename}')
        file.save(temp_path)
        
        # Validar se o arquivo é um banco SQLite válido
        try:
            import sqlite3
            conn = sqlite3.connect(temp_path)
            cursor = conn.cursor()
            
            # Verificar se as tabelas necessárias existem
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            required_tables = ['prompts', 'intimacoes', 'analises']
            missing_tables = [table for table in required_tables if table not in tables]
            
            if missing_tables:
                conn.close()
                os.remove(temp_path)
                return jsonify({
                    'success': False,
                    'message': f'Banco inválido. Tabelas ausentes: {", ".join(missing_tables)}'
                }), 400
            
            conn.close()
            
        except Exception as e:
            # Limpar arquivo temporário
            if os.path.exists(temp_path):
                os.remove(temp_path)
            
            return jsonify({
                'success': False,
                'message': f'Arquivo não é um banco SQLite válido: {str(e)}'
            }), 400
        
        # Restaurar o banco
        import shutil
        shutil.copy2(temp_path, db_path)
        
        # Limpar arquivo temporário
        os.remove(temp_path)
        
        return jsonify({
            'success': True,
            'message': 'Backup restaurado com sucesso'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro ao restaurar backup: {str(e)}'
        }), 500

# Manipuladores de erro
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

@app.route('/prompts/<id>/editar', methods=['GET', 'POST'])
def editar_prompt(id):
    """Página para editar um prompt"""
    try:
        prompt = data_service.get_prompt_by_id(id)
        if not prompt:
            flash('Prompt não encontrado.', 'error')
            return redirect(url_for('listar_prompts'))
        
        if request.method == 'POST':
            # Processar formulário de edição
            nome = request.form.get('nome', '').strip()
            descricao = request.form.get('descricao', '').strip()
            regra_negocio = request.form.get('regra_negocio', '').strip()
            conteudo = request.form.get('conteudo', '').strip()
            
            if not nome or not conteudo:
                flash('Nome e conteúdo do prompt são obrigatórios.', 'error')
                return render_template('editar_prompt.html',
                                     prompt=prompt,
                                     dados={'nome': nome, 'descricao': descricao, 
                                           'regra_negocio': regra_negocio, 'conteudo': conteudo})
            
            # Validar se o prompt contém a variável {CONTEXTO}
            if '{CONTEXTO}' not in conteudo:
                flash('O prompt deve conter a variável {CONTEXTO} para funcionar corretamente.', 'warning')
            
            # Atualizar o prompt
            prompt_atualizado = {
                'id': prompt['id'],
                'nome': nome,
                'descricao': descricao,
                'regra_negocio': regra_negocio,
                'conteudo': conteudo,
                'categoria': prompt.get('categoria', ''),
                'tags': prompt.get('tags', []),
                'data_criacao': prompt.get('data_criacao', ''),
                'total_usos': prompt.get('total_usos', 0),
                'acuracia_media': prompt.get('acuracia_media', 0.0),
                'tempo_medio': prompt.get('tempo_medio', 0.0),
                'custo_total': prompt.get('custo_total', 0.0)
            }
            
            data_service.save_prompt(prompt_atualizado)
            flash('Prompt atualizado com sucesso!', 'success')
            return redirect(url_for('visualizar_prompt', id=id))
        
        # GET - mostrar formulário de edição
        return render_template('editar_prompt.html', prompt=prompt)
        
    except Exception as e:
        flash(f'Erro ao editar prompt: {str(e)}', 'error')
        return redirect(url_for('listar_prompts'))

@app.route('/prompts/<id>/copiar')
def copiar_prompt(id):
    """Copiar um prompt - redireciona para criação com dados preenchidos"""
    try:
        prompt = data_service.get_prompt_by_id(id)
        if not prompt:
            flash('Prompt não encontrado.', 'error')
            return redirect(url_for('listar_prompts'))
        
        # Preparar dados para a página de criação
        dados_copia = {
            'nome': f"{prompt['nome']} (Cópia)",
            'descricao': prompt.get('descricao', ''),
            'regra_negocio': prompt.get('regra_negocio', ''),
            'conteudo': prompt.get('conteudo', ''),
            'categoria': prompt.get('categoria', ''),
            'tags': prompt.get('tags', [])
        }
        
        # Redirecionar para página de criação com dados preenchidos
        return render_template('novo_prompt.html', dados=dados_copia)
        
    except Exception as e:
        flash(f'Erro ao copiar prompt: {str(e)}', 'error')
        return redirect(url_for('listar_prompts'))

@app.route('/comparar-prompts')
def comparar_prompts():
    """Página de comparação de prompts"""
    try:
        # Obter IDs dos prompts da query string
        prompt_ids = request.args.getlist('prompt_ids')
        
        if not prompt_ids:
            flash('Nenhum prompt selecionado para comparação', 'warning')
            return redirect(url_for('listar_prompts'))
        
        # Buscar dados dos prompts
        prompts = []
        for prompt_id in prompt_ids:
            prompt = data_service.get_prompt_by_id(prompt_id)
            if prompt:
                # Garantir que data_criacao seja uma string se não for datetime
                if prompt.get('data_criacao') and hasattr(prompt['data_criacao'], 'strftime'):
                    prompt['data_criacao'] = prompt['data_criacao'].strftime('%d/%m/%Y %H:%M')
                prompts.append(prompt)
        
        if len(prompts) < 2:
            flash('É necessário selecionar pelo menos 2 prompts para comparação', 'warning')
            return redirect(url_for('listar_prompts'))
        
        return render_template('comparar_prompts.html', 
                             prompts=prompts,
                             total_prompts=len(prompts))
        
    except Exception as e:
        flash(f'Erro ao carregar comparação: {str(e)}', 'error')
        return redirect(url_for('listar_prompts'))

if __name__ == '__main__':
    # Criar diretórios necessários
    os.makedirs('data', exist_ok=True)
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    
    app.run(debug=True, host='0.0.0.0', port=5000)