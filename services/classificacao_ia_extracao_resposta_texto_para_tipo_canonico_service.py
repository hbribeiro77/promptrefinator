"""
Extrai o tipo de triagem (classificação) a partir do texto bruto retornado pela IA.

Fonte canônica da lista de tipos: Config.TIPOS_ACAO em config.py.
Para novo tipo: (1) adicione em TIPOS_ACAO; (2) se a IA devolver token diferente (ex. SNAKE_CASE),
    inclua o par em ALIASES_TRIAGEM_IA_PARA_CANONICO (chaves em UPPER).
"""
import json
import re
from typing import List, Sequence

# Variações comuns na saída da IA (UPPER) → rótulo exatamente como em Config.TIPOS_ACAO
ALIASES_TRIAGEM_IA_PARA_CANONICO: dict[str, str] = {
    "ELABORAR_PECA": "ELABORAR PEÇA",
    "ELABORAR PECA": "ELABORAR PEÇA",
    "CONTATO_PECA": "CONTATO PEÇA",
    "CONTATO PECA": "CONTATO PEÇA",
    "CONTATAR_ASSISTIDO": "CONTATAR ASSISTIDO",
    "ANALISAR_PROCESSO": "ANALISAR PROCESSO",
    "RENUNCIAR_PRAZO": "RENUNCIAR PRAZO",
    "ENCAMINHAR_INTIMACAO_PARA_OUTRO_DEFENSOR": "ENCAMINHAR INTIMAÇÃO PARA OUTRO DEFENSOR",
    "AGENDAR_RETORNO": "AGENDAR RETORNO",
    "URGENCIA": "URGÊNCIA",
    "INDETERMINADA": "INDETERMINADO",
}

ERRO_CLASSIFICACAO_NAO_RECONHECIDA_PREFIX = "ERRO: Classificação não reconhecida"


def extrair_classificacao_da_resposta_ia(resposta: str, tipos_acao: Sequence[str]) -> str:
    """
    Núcleo compartilhado (equivalente ao fluxo completo do antigo openai_service._extrair_classificacao).
    Usa apenas tipos_acao e ALIASES_TRIAGEM_IA_PARA_CANONICO — sem lista fixa de tipos.
    """
    if resposta is None or not str(resposta).strip():
        return "ERRO: Resposta vazia"

    tipos: List[str] = list(tipos_acao)
    resposta_limpa = resposta.strip().upper()
    aliases = ALIASES_TRIAGEM_IA_PARA_CANONICO

    try:
        dados_json = json.loads(resposta)
        if "triagem" in dados_json:
            triagem_ia = str(dados_json["triagem"]).upper().strip()
            if triagem_ia in aliases:
                return aliases[triagem_ia]
            for tipo_acao in tipos:
                if tipo_acao.upper() == triagem_ia:
                    return tipo_acao
    except (json.JSONDecodeError, TypeError, AttributeError):
        pass

    for tipo_acao in tipos:
        if tipo_acao.upper() in resposta_limpa:
            return tipo_acao

    for variacao, classificacao_padrao in aliases.items():
        if variacao in resposta_limpa:
            return classificacao_padrao

    for tipo_acao in tipos:
        palavras_chave = tipo_acao.upper().split()
        if palavras_chave and all(p in resposta_limpa for p in palavras_chave):
            return tipo_acao

    patterns = [
        r'"triagem":\s*"([^"]+)"',
        r"triagem[:\s]*([^\n\.]+)",
        r"classificação[:\s]*([^\n\.]+)",
        r"resposta[:\s]*([^\n\.]+)",
        r"ação[:\s]*([^\n\.]+)",
        r"^([^\n\.]+)$",
    ]

    for pattern in patterns:
        match = re.search(pattern, resposta_limpa, re.IGNORECASE)
        if match:
            possivel = match.group(1).strip()
            if possivel in aliases:
                return aliases[possivel]
            for tipo_acao in tipos:
                if tipo_acao.upper() == possivel:
                    return tipo_acao

    return f"{ERRO_CLASSIFICACAO_NAO_RECONHECIDA_PREFIX} - {resposta[:100]}"


def classificacao_extracao_indica_falha_nucleo(resultado: str) -> bool:
    """True se o núcleo não encontrou tipo conhecido (permite fallbacks específicos do Azure)."""
    return resultado.startswith(ERRO_CLASSIFICACAO_NAO_RECONHECIDA_PREFIX)
