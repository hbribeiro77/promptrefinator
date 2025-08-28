import pandas as pd
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from flask import Response, make_response
from io import StringIO
from config import Config
from services.sqlite_service import SQLiteService

class ExportService:
    """Serviço para exportação de dados"""
    
    def __init__(self):
        """Inicializar o serviço de exportação"""
        self.data_service = SQLiteService()
        self.config = Config()
    
    def exportar_csv(self, 
                    filtro_periodo: Optional[Dict[str, str]] = None,
                    filtro_prompt: Optional[str] = None,
                    filtro_classificacao: Optional[str] = None) -> Response:
        """Exportar análises para CSV"""
        try:
            # Obter dados
            analises = self.data_service.get_all_analises()
            intimacoes = self.data_service.get_all_intimacoes()
            prompts = self.data_service.get_all_prompts()
            
            # Criar dicionários para lookup rápido
            intimacoes_dict = {i['id']: i for i in intimacoes}
            prompts_dict = {p['id']: p for p in prompts}
            
            # Aplicar filtros
            analises_filtradas = self._aplicar_filtros(
                analises, filtro_periodo, filtro_prompt, filtro_classificacao
            )
            
            # Preparar dados para CSV
            dados_csv = []
            for analise in analises_filtradas:
                intimacao = intimacoes_dict.get(analise.get('intimacao_id'), {})
                prompt = prompts_dict.get(analise.get('prompt_id'), {})
                
                # Truncar contexto para CSV
                contexto_truncado = self._truncar_texto(intimacao.get('contexto', ''), 200)
                resposta_truncada = self._truncar_texto(analise.get('resposta_completa_ia', ''), 300)
                
                dados_csv.append({
                    'ID_Analise': analise.get('id', ''),
                    'ID_Intimacao': analise.get('intimacao_id', ''),
                    'Contexto_Intimacao': contexto_truncado,
                    'Classificacao_Manual': analise.get('classificacao_manual', ''),
                    'Nome_Prompt': prompt.get('nome', 'Prompt não encontrado'),
                    'Classificacao_IA': analise.get('resultado_ia', ''),
                    'Acertou': 'Sim' if analise.get('acertou', False) else 'Não',
                    'Tempo_Processamento_s': analise.get('tempo_processamento', 0),
                    'Modelo_IA': analise.get('parametros_openai', {}).get('model', ''),
                    'Temperature': analise.get('parametros_openai', {}).get('temperature', ''),
                    'Max_Tokens': analise.get('parametros_openai', {}).get('max_tokens', ''),
                    'Data_Analise': self._formatar_data(analise.get('data_analise', '')),
                    'Resposta_Completa_IA': resposta_truncada,
                    'Informacao_Adicional': intimacao.get('informacao_adicional', '')
                })
            
            # Criar DataFrame
            df = pd.DataFrame(dados_csv)
            
            if df.empty:
                # Retornar CSV vazio com cabeçalhos
                df = pd.DataFrame(columns=[
                    'ID_Analise', 'ID_Intimacao', 'Contexto_Intimacao', 
                    'Classificacao_Manual', 'Nome_Prompt', 'Classificacao_IA',
                    'Acertou', 'Tempo_Processamento_s', 'Modelo_IA', 
                    'Temperature', 'Max_Tokens', 'Data_Analise',
                    'Resposta_Completa_IA', 'Informacao_Adicional'
                ])
            
            # Gerar CSV
            output = StringIO()
            df.to_csv(output, index=False, encoding='utf-8-sig')
            csv_content = output.getvalue()
            output.close()
            
            # Criar resposta HTTP
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'analises_intimacoes_{timestamp}.csv'
            
            response = make_response(csv_content)
            response.headers['Content-Type'] = 'text/csv; charset=utf-8-sig'
            response.headers['Content-Disposition'] = f'attachment; filename={filename}'
            
            return response
            
        except Exception as e:
            raise Exception(f"Erro ao exportar CSV: {str(e)}")
    
    def exportar_relatorio_resumo_csv(self) -> Response:
        """Exportar relatório resumo em CSV"""
        try:
            stats = self.data_service.get_statistics()
            
            # Dados gerais
            dados_gerais = [{
                'Metrica': 'Total de Intimações',
                'Valor': stats['total_intimacoes']
            }, {
                'Metrica': 'Total de Análises',
                'Valor': stats['total_analises']
            }, {
                'Metrica': 'Total de Prompts',
                'Valor': stats['total_prompts']
            }, {
                'Metrica': 'Taxa de Acurácia Geral (%)',
                'Valor': stats['taxa_acuracia_geral']
            }]
            
            # Estatísticas por prompt
            prompts = self.data_service.get_all_prompts()
            prompts_dict = {p['id']: p for p in prompts}
            
            dados_prompts = []
            for prompt_id, stats_prompt in stats['stats_por_prompt'].items():
                prompt = prompts_dict.get(prompt_id, {})
                dados_prompts.append({
                    'ID_Prompt': prompt_id,
                    'Nome_Prompt': prompt.get('nome', 'Prompt não encontrado'),
                    'Total_Analises': stats_prompt['total'],
                    'Acertos': stats_prompt['acertos'],
                    'Taxa_Acuracia_Percent': round(stats_prompt['taxa_acuracia'], 2)
                })
            
            # Distribuição por classificação
            dados_classificacao = []
            for classificacao, count in stats['distribuicao_classificacao'].items():
                dados_classificacao.append({
                    'Classificacao': classificacao,
                    'Quantidade': count,
                    'Percentual': round((count / stats['total_intimacoes'] * 100), 2) if stats['total_intimacoes'] > 0 else 0
                })
            
            # Criar arquivo Excel com múltiplas abas (usando CSV concatenado)
            output = StringIO()
            
            # Escrever seção de dados gerais
            output.write("=== ESTATISTICAS GERAIS ===\n")
            df_gerais = pd.DataFrame(dados_gerais)
            df_gerais.to_csv(output, index=False)
            output.write("\n")
            
            # Escrever seção de prompts
            output.write("=== ESTATISTICAS POR PROMPT ===\n")
            df_prompts = pd.DataFrame(dados_prompts)
            df_prompts.to_csv(output, index=False)
            output.write("\n")
            
            # Escrever seção de classificações
            output.write("=== DISTRIBUICAO POR CLASSIFICACAO ===\n")
            df_classificacao = pd.DataFrame(dados_classificacao)
            df_classificacao.to_csv(output, index=False)
            
            csv_content = output.getvalue()
            output.close()
            
            # Criar resposta HTTP
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'relatorio_resumo_{timestamp}.csv'
            
            response = make_response(csv_content)
            response.headers['Content-Type'] = 'text/csv; charset=utf-8-sig'
            response.headers['Content-Disposition'] = f'attachment; filename={filename}'
            
            return response
            
        except Exception as e:
            raise Exception(f"Erro ao exportar relatório resumo: {str(e)}")
    
    def exportar_matriz_confusao_csv(self) -> Response:
        """Exportar matriz de confusão em CSV"""
        try:
            analises = self.data_service.get_all_analises()
            
            # Criar matriz de confusão
            tipos_acao = self.config.TIPOS_ACAO
            matriz = {}
            
            # Inicializar matriz
            for manual in tipos_acao:
                matriz[manual] = {}
                for ia in tipos_acao:
                    matriz[manual][ia] = 0
            
            # Preencher matriz
            for analise in analises:
                manual = analise.get('classificacao_manual', '')
                ia = analise.get('resultado_ia', '')
                
                # Limpar classificação da IA se contém erro
                if ia.startswith('ERRO:'):
                    ia = 'ERRO_CLASSIFICACAO'
                
                if manual in matriz:
                    if ia in matriz[manual]:
                        matriz[manual][ia] += 1
                    else:
                        # Adicionar categoria para erros
                        if 'ERRO_CLASSIFICACAO' not in matriz[manual]:
                            matriz[manual]['ERRO_CLASSIFICACAO'] = 0
                        matriz[manual]['ERRO_CLASSIFICACAO'] += 1
            
            # Converter para DataFrame
            df_matriz = pd.DataFrame(matriz).fillna(0)
            df_matriz = df_matriz.astype(int)
            
            # Adicionar totais
            df_matriz['Total_Manual'] = df_matriz.sum(axis=1)
            df_matriz.loc['Total_IA'] = df_matriz.sum(axis=0)
            
            # Gerar CSV
            output = StringIO()
            output.write("=== MATRIZ DE CONFUSAO ===\n")
            output.write("Linhas: Classificacao Manual | Colunas: Classificacao IA\n\n")
            df_matriz.to_csv(output)
            
            csv_content = output.getvalue()
            output.close()
            
            # Criar resposta HTTP
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'matriz_confusao_{timestamp}.csv'
            
            response = make_response(csv_content)
            response.headers['Content-Type'] = 'text/csv; charset=utf-8-sig'
            response.headers['Content-Disposition'] = f'attachment; filename={filename}'
            
            return response
            
        except Exception as e:
            raise Exception(f"Erro ao exportar matriz de confusão: {str(e)}")
    
    def _aplicar_filtros(self, 
                        analises: List[Dict[str, Any]],
                        filtro_periodo: Optional[Dict[str, str]] = None,
                        filtro_prompt: Optional[str] = None,
                        filtro_classificacao: Optional[str] = None) -> List[Dict[str, Any]]:
        """Aplicar filtros às análises"""
        analises_filtradas = analises.copy()
        
        # Filtro por período
        if filtro_periodo and filtro_periodo.get('data_inicio') and filtro_periodo.get('data_fim'):
            try:
                data_inicio = datetime.fromisoformat(filtro_periodo['data_inicio'])
                data_fim = datetime.fromisoformat(filtro_periodo['data_fim'])
                
                analises_filtradas = [
                    a for a in analises_filtradas
                    if self._data_esta_no_periodo(
                        a.get('data_analise', ''), data_inicio, data_fim
                    )
                ]
            except ValueError:
                pass  # Ignorar filtro se datas inválidas
        
        # Filtro por prompt
        if filtro_prompt:
            analises_filtradas = [
                a for a in analises_filtradas
                if a.get('prompt_id') == filtro_prompt
            ]
        
        # Filtro por classificação
        if filtro_classificacao:
            analises_filtradas = [
                a for a in analises_filtradas
                if a.get('classificacao_manual') == filtro_classificacao
            ]
        
        return analises_filtradas
    
    def _data_esta_no_periodo(self, data_str: str, data_inicio: datetime, data_fim: datetime) -> bool:
        """Verificar se data está no período especificado"""
        try:
            if isinstance(data_str, str):
                data = datetime.fromisoformat(data_str.replace('Z', '+00:00'))
            else:
                return False
            
            return data_inicio <= data <= data_fim
        except (ValueError, TypeError):
            return False
    
    def _truncar_texto(self, texto: str, max_length: int) -> str:
        """Truncar texto para CSV"""
        if not texto:
            return ''
        
        if len(texto) <= max_length:
            return texto
        
        return texto[:max_length] + '...'
    
    def _formatar_data(self, data_str: str) -> str:
        """Formatar data para exibição"""
        try:
            if isinstance(data_str, str):
                data = datetime.fromisoformat(data_str.replace('Z', '+00:00'))
                return data.strftime('%d/%m/%Y %H:%M:%S')
            return str(data_str)
        except (ValueError, TypeError):
            return str(data_str)
    
    def salvar_arquivo_local(self, 
                           dados: str, 
                           nome_arquivo: str, 
                           formato: str = 'csv') -> str:
        """Salvar arquivo localmente na pasta de exports"""
        try:
            # Garantir que o diretório existe
            os.makedirs(self.config.EXPORT_DIR, exist_ok=True)
            
            # Criar nome do arquivo com timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            nome_completo = f"{timestamp}_{nome_arquivo}.{formato}"
            caminho_arquivo = os.path.join(self.config.EXPORT_DIR, nome_completo)
            
            # Salvar arquivo
            with open(caminho_arquivo, 'w', encoding='utf-8-sig') as f:
                f.write(dados)
            
            return caminho_arquivo
            
        except Exception as e:
            raise Exception(f"Erro ao salvar arquivo local: {str(e)}")
    
    def export_to_csv(self, dados: List[Dict[str, Any]], nome_arquivo: str) -> str:
        """Exportar dados para CSV"""
        try:
            # Criar DataFrame
            df = pd.DataFrame(dados)
            
            # Garantir que o diretório existe
            os.makedirs(self.config.EXPORT_DIR, exist_ok=True)
            
            # Criar caminho do arquivo
            caminho_arquivo = os.path.join(self.config.EXPORT_DIR, nome_arquivo)
            
            # Salvar CSV
            df.to_csv(caminho_arquivo, index=False, encoding='utf-8-sig')
            
            return caminho_arquivo
            
        except Exception as e:
            raise Exception(f"Erro ao exportar CSV: {str(e)}")
    
    def export_to_excel(self, dados: List[Dict[str, Any]], nome_arquivo: str, sheet_name: str = 'Dados') -> str:
        """Exportar dados para Excel"""
        try:
            # Criar DataFrame
            df = pd.DataFrame(dados)
            
            # Garantir que o diretório existe
            os.makedirs(self.config.EXPORT_DIR, exist_ok=True)
            
            # Criar caminho do arquivo
            caminho_arquivo = os.path.join(self.config.EXPORT_DIR, nome_arquivo)
            
            # Salvar Excel
            with pd.ExcelWriter(caminho_arquivo, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            return caminho_arquivo
            
        except Exception as e:
            raise Exception(f"Erro ao exportar Excel: {str(e)}")