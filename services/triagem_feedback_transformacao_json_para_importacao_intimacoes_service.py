"""
Transforma JSON de feedback de triagem (content[]) para o formato de importação em lote
(origem, total_registros, registros) usado pelo Prompt Refinator.
"""
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Pattern, Tuple


SYSTEM_MARKER = "====== [INICIO: SYSTEM] ======"
USER_MARKER = "====== [INICIO: USER] ======"
AI_MARKER = "====== [INICIO: AI] ======"
# Espaços entre "FIM:" e o rótulo podem variar no prompt exportado
FIM_SYSTEM_MARKER_REGEX = re.compile(r"====== \[FIM:\s+SYSTEM\] ======")
FIM_USER_MARKER_REGEX = re.compile(r"====== \[FIM:\s+USER\] ======")
FIM_AI_MARKER_REGEX = re.compile(r"====== \[FIM:\s+AI\] ======")
CONTEXTO_INTIMACAO_FIM_SENTINEL = "Triagem IA executada com sucesso para intimação"
# Export novo: lixo após atribuição text='…' com a mesma frase de sucesso
_TRIAGEM_SUCESSO_TEXT_ASSIGN_RE = re.compile(
    r"text\s*=\s*['\"]Triagem IA executada com sucesso para intimação",
    re.IGNORECASE,
)

# Layout do export: texto em triagem.prompt vs campos estruturados em triagem (export novo)
LAYOUT_FEEDBACK_LEGACY = "legacy"
LAYOUT_FEEDBACK_POS_2026_03_25 = "pos_2026_03_25"
LAYOUT_FEEDBACK_VALID = frozenset({LAYOUT_FEEDBACK_LEGACY, LAYOUT_FEEDBACK_POS_2026_03_25})


def normalize_feedback_export_layout(raw: Any) -> str:
    """Normaliza o parâmetro enviado pela API; inválido levanta ValueError."""
    if raw is None or (isinstance(raw, str) and not str(raw).strip()):
        return LAYOUT_FEEDBACK_LEGACY
    s = str(raw).strip()
    if s in LAYOUT_FEEDBACK_VALID:
        return s
    raise ValueError(
        f'layout inválido: {s!r}. Valores aceitos: "{LAYOUT_FEEDBACK_LEGACY}" '
        f'(export até 24/03/2026) ou "{LAYOUT_FEEDBACK_POS_2026_03_25}" (25/03/2026 em diante).'
    )


@dataclass
class ValidationIssue:
    registro_index: int
    campo: str
    mensagem: str
    intimacao_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        out: Dict[str, Any] = {
            "registro_index": self.registro_index,
            "campo": self.campo,
            "mensagem": self.mensagem,
        }
        if self.intimacao_id is not None:
            out["intimacaoId"] = self.intimacao_id
        return out


def safe_get(dct: Dict[str, Any], *keys: str) -> Any:
    current: Any = dct
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def normalize_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _strip_blocks_between(text: str, start_marker: str, end_regex: Pattern[str]) -> str:
    """Remove todas as ocorrências de blocos delimitados por start_marker … fechamento end_regex."""
    while True:
        ini = text.find(start_marker)
        if ini == -1:
            break
        m = end_regex.search(text, ini + len(start_marker))
        if m is None:
            text = text[:ini]
            break
        text = text[:ini] + text[m.end() :]
    return text


def extract_after_ai(prompt: Optional[str]) -> Optional[str]:
    """
    Remove do prompt os blocos entre marcadores INICIO/FIM de SYSTEM, USER e AI
    (com um ou mais espaços após FIM: em cada fechamento).
    O texto restante é o contexto da intimação. Sem esses blocos, usa o que sobrar do prompt.
    Se algum [INICIO: …] existir sem fechamento [FIM: …] correspondente, descarta da abertura até o fim.
    Por fim, remove CONTEXTO_INTIMACAO_FIM_SENTINEL e tudo o que vier depois.
    """
    if not isinstance(prompt, str) or not prompt.strip():
        return None
    text = _strip_blocks_between(prompt, SYSTEM_MARKER, FIM_SYSTEM_MARKER_REGEX)
    text = _strip_blocks_between(text, USER_MARKER, FIM_USER_MARKER_REGEX)
    text = _strip_blocks_between(text, AI_MARKER, FIM_AI_MARKER_REGEX)
    result = text.strip()
    corte = result.find(CONTEXTO_INTIMACAO_FIM_SENTINEL)
    if corte != -1:
        result = result[:corte].strip()
    return result if result else None


def _cut_prompt_antes_sentinela_triagem_sucesso(text: str) -> str:
    """Remove tudo a partir da frase de sucesso da triagem ou de text='…' com essa frase."""
    if not text:
        return text
    cortes: List[int] = []
    m = _TRIAGEM_SUCESSO_TEXT_ASSIGN_RE.search(text)
    if m is not None:
        cortes.append(m.start())
    idx = text.find(CONTEXTO_INTIMACAO_FIM_SENTINEL)
    if idx != -1:
        cortes.append(idx)
    if not cortes:
        return text
    return text[: min(cortes)]


def prompt_window_pos_2026_03_25(prompt: Optional[str]) -> Optional[str]:
    """
    Janela do prompt para layout pos_2026_03_25 (export a partir de 25/03/2026):
    - texto a partir de ====== [INICIO: USER] ====== (se o marcador existir; senão usa o prompt inteiro);
    - remove blocos entre [INICIO: AI] e [FIM: AI];
    - corta antes de Triagem IA executada… e antes de text='Triagem IA executada…'.
    """
    if not isinstance(prompt, str) or not prompt.strip():
        return None
    p = prompt.strip()
    u = p.find(USER_MARKER)
    if u != -1:
        text = p[u + len(USER_MARKER) :].lstrip()
    else:
        text = p
    text = _strip_blocks_between(text, AI_MARKER, FIM_AI_MARKER_REGEX)
    text = _cut_prompt_antes_sentinela_triagem_sucesso(text)
    text = text.strip()
    return text if text else None


# Markdown no USER: bloco de regras → campo regras_usuario_prioridade_alta; contexto sem o miolo.
_REGRAS_USUARIO_MD_HEADER_RE = re.compile(
    r"^[ \t]*#\s*Regras\s+do\s+Usu[aá]rio\s*\(\s*PRIORIDADE\s+ALTA\s*\)\s*$",
    re.IGNORECASE | re.MULTILINE,
)
_INFO_INTIMACAO_MD_HEADER_RE = re.compile(
    r"^[ \t]*#\s*Informa[cç][oõ]es\s+da\s+Intima[cç][aã]o\s*$",
    re.IGNORECASE | re.MULTILINE,
)


def extrair_regras_usuario_markdown_e_sanitizar_contexto(
    texto: Optional[str],
) -> Tuple[Optional[str], Optional[str]]:
    """
    Entre '# Regras do Usuário (PRIORIDADE ALTA)' e '# Informações da Intimação':
    - devolve o corpo (trim) como regras extraídas;
    - devolve o texto com o miolo removido, mantendo a linha do cabeçalho de regras
      colada ao cabeçalho de informações da intimação.
    Se algum cabeçalho faltar, retorna (texto original, None).
    """
    if not isinstance(texto, str) or not texto.strip():
        return texto, None
    m_regras = _REGRAS_USUARIO_MD_HEADER_RE.search(texto)
    if not m_regras:
        return texto, None
    line_end = texto.find("\n", m_regras.end())
    if line_end == -1:
        after_regras_line = len(texto)
    else:
        after_regras_line = line_end + 1
    m_info = _INFO_INTIMACAO_MD_HEADER_RE.search(texto, after_regras_line)
    if not m_info:
        return texto, None
    corpo = texto[after_regras_line : m_info.start()]
    regras_extraidas = corpo.strip()
    regras_out: Optional[str] = regras_extraidas if regras_extraidas else None
    novo = texto[:after_regras_line] + texto[m_info.start() :]
    novo = novo.strip() if novo else novo
    return (novo if novo else texto), regras_out


def extrair_somente_regras_usuario_markdown(texto: Optional[str]) -> Optional[str]:
    """Só o texto das regras, sem alterar o documento (útil se o contexto veio de campo estruturado)."""
    _, r = extrair_regras_usuario_markdown_e_sanitizar_contexto(texto)
    return r


def extract_field(prompt: Optional[str], field_names: List[str]) -> Optional[str]:
    if not isinstance(prompt, str):
        return None

    for field_name in field_names:
        pattern = (
            rf"\*\*\s*{re.escape(field_name)}\s*\*\*\s*:\s*(.*?)"
            rf"(?=\s+-\s+\*\*|\s+##\s+|\s+###\s+|\Z)"
        )
        match = re.search(pattern, prompt, flags=re.IGNORECASE)
        if match:
            return normalize_spaces(match.group(1))
    return None


# Rótulos no prompt: **Intimados**, **Intimados da intimação**, opcionalmente com "- " antes do negrito
_INTIMADOS_LABEL_REGEX = (
    r"(?:-\s*)?"
    r"\*\*\s*Intimados(?:\s+da\s+intimação)?\s*\*\*"
    r"\s*:\s*"
)


def extract_intimados(prompt: Optional[str]) -> Optional[str]:
    if not isinstance(prompt, str):
        return None

    block_match = re.search(
        _INTIMADOS_LABEL_REGEX + r"(.*?)(?=\s+-\s+\*\*|\s+##\s+|\s+###\s+|\Z)",
        prompt,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if not block_match:
        return extract_field(prompt, ["Intimados da intimação", "Intimados"])

    block = block_match.group(1)
    nomes = [normalize_spaces(m.group(1)) for m in re.finditer(r"-\s*(.+)", block)]
    nomes_validos = [nome for nome in nomes if nome]
    if not nomes_validos:
        return extract_field(prompt, ["Intimados da intimação", "Intimados"])
    return "; ".join(nomes_validos)


def extract_defensor_name(prompt: Optional[str]) -> Optional[str]:
    """
    Extrai o nome (ou matrícula) do defensor do texto do prompt.
    Formatos suportados:
    - Legado: "Você está realizando a triagem para: **Fulano**"
    - Novo: "Você está realizando a triagem para o defensor (a): **Fulano**"
    - Novo sem negrito na mesma linha: "... defensor (a): Fulano"
    """
    if not isinstance(prompt, str):
        return None

    candidatos: List[Tuple[str, int]] = [
        (
            r"Você está realizando a triagem para o defensor\s*\(a\)\s*:\s*\*\*(.+?)\*\*",
            re.IGNORECASE | re.DOTALL,
        ),
        (
            r"Você está realizando a triagem para o defensor\s*\(a\)\s*:\s*([^\n]+?)\s*(?=\n|\Z)",
            re.IGNORECASE,
        ),
        (
            r"Você está realizando a triagem para:\s*\*\*(.+?)\*\*",
            re.IGNORECASE | re.DOTALL,
        ),
    ]
    for pattern, flags in candidatos:
        match = re.search(pattern, prompt, flags=flags)
        if match:
            val = normalize_spaces(match.group(1))
            if val:
                return val
    return None


def map_cor_etiqueta(sucesso: Any) -> Optional[str]:
    if sucesso is True:
        return "verde"
    if sucesso is False:
        return "amarelo"
    return None


def _sucesso_feedback_definido(sucesso: Any) -> bool:
    """Somente True ou False (bool) são aceitos; null, ausente ou outros valores não."""
    return sucesso is True or sucesso is False


def _item_intimacao_id_externo(item: Dict[str, Any]) -> Optional[str]:
    triagem = item.get("triagem") if isinstance(item.get("triagem"), dict) else {}
    raw = triagem.get("intimacaoId")
    if raw is None:
        return None
    s = str(raw).strip()
    return s if s else None


def _fmt_sucesso_para_aviso(sucesso: Any) -> str:
    if sucesso is None:
        return "ausente ou null"
    if isinstance(sucesso, bool):
        return str(sucesso).lower()
    try:
        return json.dumps(sucesso, ensure_ascii=False)
    except (TypeError, ValueError):
        return repr(sucesso)


def _decode_json_string_escapes(s: str) -> str:
    """Interpreta sequências \\n, \\", \\\\ etc. como em string JSON."""
    try:
        return json.loads(f'"{s}"')
    except json.JSONDecodeError:
        return s.replace("\\n", "\n").replace('\\"', '"').replace("\\\\", "\\")


def _extract_json_string_field_from_prompt(prompt: Optional[str], key: str) -> Optional[str]:
    """
    Localiza "key":"valor" ou \\"key\\":\\"valor\\" no texto do prompt
    (ex.: arguments de executaTriagem). Retorna None se não achar.
    """
    if not isinstance(prompt, str) or not str(key).strip():
        return None

    p1 = rf'"{re.escape(key)}"\s*:\s*"((?:[^"\\]|\\.)*)"'
    m1 = re.search(p1, prompt, flags=re.DOTALL)
    if m1:
        return _decode_json_string_escapes(m1.group(1))

    p2 = rf'\\"{re.escape(key)}\\"\s*:\s*\\"((?:[^\\]|\\.)*?)\\"(?=\s*[,}}])'
    m2 = re.search(p2, prompt, flags=re.DOTALL)
    if m2:
        return _decode_json_string_escapes(m2.group(1))

    return None


def _substituir_analisar_por_analisar_processo(val: Any) -> Any:
    """Sinônimo legado: classificação só 'ANALISAR' vira o tipo cadastrado ANALISAR PROCESSO."""
    if val is None:
        return None
    cand = " ".join(str(val).strip().replace("_", " ").split())
    if cand.casefold() == "analisar":
        return "ANALISAR PROCESSO"
    return val


def _triagem_primeiro_texto(triagem: Dict[str, Any], keys: List[str]) -> Optional[str]:
    """
    Primeiro valor não vazio entre chaves de triagem (string, número ou lista de strings/objetos com nome).
    Usado no layout pos_2026_03_25 quando o export passa campos estruturados além do markdown no prompt.
    """
    if not isinstance(triagem, dict):
        return None
    for k in keys:
        v = triagem.get(k)
        if v is None:
            continue
        if isinstance(v, str) and v.strip():
            return normalize_spaces(v)
        if isinstance(v, bool):
            return "true" if v else "false"
        if isinstance(v, (int, float)):
            s = str(v).strip()
            return s if s else None
        if isinstance(v, list):
            parts: List[str] = []
            for x in v:
                if x is None:
                    continue
                if isinstance(x, str) and x.strip():
                    parts.append(normalize_spaces(x))
                elif isinstance(x, dict):
                    n = x.get("nome") or x.get("name") or x.get("nomeCompleto")
                    if isinstance(n, str) and n.strip():
                        parts.append(normalize_spaces(n))
                else:
                    sx = str(x).strip()
                    if sx:
                        parts.append(sx)
            if parts:
                return "; ".join(parts)
    return None


def transform_item(
    item: Dict[str, Any],
    layout: str = LAYOUT_FEEDBACK_LEGACY,
) -> Dict[str, Any]:
    feedback = safe_get(item, "feedback") or {}
    triagem = safe_get(item, "triagem") or {}
    if not isinstance(triagem, dict):
        triagem = {}
    prompt = triagem.get("prompt")
    sucesso = feedback.get("sucesso")
    p_win: Optional[str] = None
    if layout == LAYOUT_FEEDBACK_POS_2026_03_25:
        p_win = prompt_window_pos_2026_03_25(prompt)

    if layout == LAYOUT_FEEDBACK_POS_2026_03_25:
        processo = _triagem_primeiro_texto(
            triagem,
            ["numeroProcesso", "numero_processo", "nrProcesso", "processo", "numProcesso"],
        )
        if not processo and triagem.get("numeroProcesso") is not None:
            s = str(triagem.get("numeroProcesso")).strip()
            processo = s if s else None
        if not processo:
            processo = extract_field(p_win, ["Processo"])

        orgao_julgador = _triagem_primeiro_texto(
            triagem,
            [
                "orgaoJulgador",
                "orgao_julgador",
                "nomeOrgaoJulgador",
                "orgaoJulgadorNome",
                "juizo",
                "nomeJuizo",
                "vara",
                "nomeVara",
            ],
        ) or extract_field(p_win, ["Órgão Julgador", "Orgao Julgador"])

        classe = _triagem_primeiro_texto(
            triagem,
            ["classe", "classeProcessual", "classe_processual", "tipoClasse", "classeNome"],
        ) or extract_field(p_win, ["Classe", "Classe Processual"])

        intimado = _triagem_primeiro_texto(
            triagem,
            ["intimado", "intimados", "nomeIntimado", "nomesIntimados", "partes", "assistidos"],
        ) or extract_intimados(p_win)

        prazo = _triagem_primeiro_texto(
            triagem,
            ["prazo", "dias", "diasPrazo", "dias_prazo", "prazoDias", "numeroDias"],
        ) or extract_field(p_win, ["Dias", "Prazo"])

        nome_defensor = _triagem_primeiro_texto(
            triagem,
            [
                "nomeDefensor",
                "defensor",
                "defensorNome",
                "nome_defensor",
                "matriculaDefensor",
                "matrículaDefensor",
            ],
        ) or extract_defensor_name(p_win)

        contexto = _triagem_primeiro_texto(
            triagem,
            [
                "contexto",
                "contextoIntimacao",
                "contexto_intimacao",
                "textoIntimacao",
                "corpoIntimacao",
            ],
        )
        if not contexto:
            contexto = p_win
    else:
        processo = triagem.get("numeroProcesso")
        if processo is not None and not isinstance(processo, str):
            processo = str(processo).strip() or None
        elif isinstance(processo, str):
            processo = processo.strip() or None
        processo = processo or extract_field(prompt, ["Processo"])
        orgao_julgador = extract_field(prompt, ["Órgão Julgador", "Orgao Julgador"])
        classe = extract_field(prompt, ["Classe", "Classe Processual"])
        intimado = extract_intimados(prompt)
        prazo = extract_field(prompt, ["Dias", "Prazo"])
        nome_defensor = extract_defensor_name(prompt)
        contexto = extract_after_ai(prompt)

    if sucesso is True:
        cm_triagem = ia_triagem = None
        if layout == LAYOUT_FEEDBACK_POS_2026_03_25:
            cm_triagem = _triagem_primeiro_texto(
                triagem,
                [
                    "triagemResultado",
                    "categoriaDaTriagem",
                    "categoria_da_triagem",
                    "resultadoTriagem",
                    "classificacao",
                    "categoria",
                ],
            )
            ia_triagem = _triagem_primeiro_texto(
                triagem,
                ["informacaoAdicional", "informacao_adicional", "observacaoTriagem"],
            )
        prompt_para_json_no_prompt = (
            p_win if layout == LAYOUT_FEEDBACK_POS_2026_03_25 else prompt
        )
        classificacao_manual = cm_triagem or _extract_json_string_field_from_prompt(
            prompt_para_json_no_prompt, "categoriaDaTriagem"
        )
        informacoes_adicionais = ia_triagem or _extract_json_string_field_from_prompt(
            prompt_para_json_no_prompt, "informacaoAdicional"
        )
        if classificacao_manual is None:
            classificacao_manual = triagem.get("triagemResultado")
            if classificacao_manual is not None and not isinstance(classificacao_manual, str):
                classificacao_manual = str(classificacao_manual).strip() or None
        if informacoes_adicionais is None:
            informacoes_adicionais = triagem.get("informacaoAdicional")
            if informacoes_adicionais is not None and not isinstance(informacoes_adicionais, str):
                informacoes_adicionais = str(informacoes_adicionais).strip() or None
    else:
        classificacao_manual = feedback.get("inferenciaCorreta")
        informacoes_adicionais = feedback.get("observacao")

    classificacao_manual = _substituir_analisar_por_analisar_processo(classificacao_manual)

    contexto, regras_md_ctx = extrair_regras_usuario_markdown_e_sanitizar_contexto(contexto)
    regras_usuario_prioridade_alta = _triagem_primeiro_texto(
        triagem,
        [
            "regrasUsuarioPrioridadeAlta",
            "regras_usuario_prioridade_alta",
            "regrasDoUsuarioPrioridadeAlta",
            "regras_do_usuario_prioridade_alta",
        ],
    ) or regras_md_ctx
    if regras_usuario_prioridade_alta is None:
        if layout == LAYOUT_FEEDBACK_POS_2026_03_25 and p_win:
            regras_usuario_prioridade_alta = extrair_somente_regras_usuario_markdown(p_win)
        elif isinstance(prompt, str) and prompt.strip():
            regras_usuario_prioridade_alta = extrair_somente_regras_usuario_markdown(
                extract_after_ai(prompt)
            )

    return {
        "intimacaoId": triagem.get("intimacaoId"),
        "contexto da intimação": contexto,
        "processo": processo,
        "órgão julgador": orgao_julgador,
        "Classe": classe,
        "intimado": intimado,
        "status": triagem.get("status"),
        "prazo": prazo,
        "nome do defensor": nome_defensor,
        "cor da etiqueta": map_cor_etiqueta(sucesso),
        "classificação manual": classificacao_manual,
        "Informações adicionais": informacoes_adicionais,
        "regras_usuario_prioridade_alta": regras_usuario_prioridade_alta,
    }


def _registro_intimacao_id_externo(registro: Dict[str, Any]) -> Optional[str]:
    raw = registro.get("intimacaoId")
    if raw is None:
        return None
    s = str(raw).strip()
    return s if s else None


def validate_record(registro: Dict[str, Any], registro_index: int) -> List[ValidationIssue]:
    obrigatorios = [
        "intimacaoId",
        "contexto da intimação",
        "processo",
        "órgão julgador",
        "Classe",
        "intimado",
        "status",
        "prazo",
        "nome do defensor",
        "cor da etiqueta",
        "classificação manual",
    ]

    iid = _registro_intimacao_id_externo(registro)
    issues: List[ValidationIssue] = []
    for campo in obrigatorios:
        valor = registro.get(campo)
        if valor is None or (isinstance(valor, str) and not valor.strip()):
            issues.append(
                ValidationIssue(
                    registro_index=registro_index,
                    campo=campo,
                    mensagem="Campo obrigatório não encontrado durante a extração.",
                    intimacao_id=iid,
                )
            )
    return issues


def repair_unescaped_quotes_in_prompt(raw_text: str) -> str:
    pattern = re.compile(
        r'"prompt"\s*:\s*"(.*?)"\s*,\s*\n\s*"output"\s*:',
        flags=re.DOTALL,
    )

    def _replacer(match) -> str:
        prompt_content = match.group(1)
        fixed = prompt_content.replace("\\", "\\\\").replace('"', '\\"')
        fixed = fixed.replace("\\\\\\\"", "\\\\\"")
        return f'"prompt": "{fixed}",\n    "output":'

    return pattern.sub(_replacer, raw_text)


def load_json_from_text(raw_text: str) -> Dict[str, Any]:
    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        repaired_text = repair_unescaped_quotes_in_prompt(raw_text)
        return json.loads(repaired_text)


def load_json_from_path(path: Path) -> Dict[str, Any]:
    raw_text = path.read_text(encoding="utf-8")
    return load_json_from_text(raw_text)


def transform_content_to_import_payload(
    data: Dict[str, Any],
    origem: str,
    layout: str = LAYOUT_FEEDBACK_LEGACY,
) -> Tuple[Dict[str, Any], List[ValidationIssue]]:
    content = data.get("content", [])
    if not isinstance(content, list):
        raise ValueError("O JSON precisa ter a chave 'content' com uma lista de registros.")

    registros_transformados: List[Dict[str, Any]] = []
    issues: List[ValidationIssue] = []

    for index, item in enumerate(content, start=1):
        if not isinstance(item, dict):
            issues.append(
                ValidationIssue(
                    registro_index=index,
                    campo="registro",
                    mensagem="Item em 'content' não é um objeto JSON.",
                )
            )
            continue

        feedback = item.get("feedback") if isinstance(item.get("feedback"), dict) else {}
        sucesso = feedback.get("sucesso")
        if not _sucesso_feedback_definido(sucesso):
            issues.append(
                ValidationIssue(
                    registro_index=index,
                    campo="feedback.sucesso",
                    mensagem=(
                        "feedback.sucesso deve ser exatamente true ou false "
                        f"(recebido: {_fmt_sucesso_para_aviso(sucesso)}). "
                        "Registro excluído do JSON de importação."
                    ),
                    intimacao_id=_item_intimacao_id_externo(item),
                )
            )
            continue

        registro = transform_item(item, layout=layout)
        registros_transformados.append(registro)
        issues.extend(validate_record(registro, index))

    output_payload = {
        "origem": origem,
        "total_registros": len(registros_transformados),
        "registros": registros_transformados,
    }
    return output_payload, issues


def transform_feedback_json_text(
    raw_text: str,
    origem: str = "colado.json",
    layout: str = LAYOUT_FEEDBACK_LEGACY,
) -> Tuple[Dict[str, Any], List[ValidationIssue]]:
    """Entrada: texto JSON bruto do export de feedback. Saída: payload de importação + issues."""
    data = load_json_from_text(raw_text.strip())
    return transform_content_to_import_payload(data, origem=origem, layout=layout)


def transform_file(
    input_path: Path,
    output_path: Path,
    layout: str = LAYOUT_FEEDBACK_LEGACY,
) -> Tuple[int, List[ValidationIssue]]:
    data = load_json_from_path(input_path)
    output_payload, issues = transform_content_to_import_payload(
        data, origem=input_path.name, layout=layout
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(output_payload, f, ensure_ascii=False, indent=2)
    return len(output_payload["registros"]), issues


def run_batch(
    input_dir: Path,
    output_dir: Path,
    layout: str = LAYOUT_FEEDBACK_LEGACY,
) -> int:
    input_files = sorted(input_dir.glob("*.json"))
    if not input_files:
        print(f"[ERRO] Nenhum arquivo .json encontrado em: {input_dir}")
        return 1

    output_dir.mkdir(parents=True, exist_ok=True)
    total_issues = 0

    print(f"[INFO] Arquivos de entrada: {len(input_files)}")
    for input_file in input_files:
        output_file = output_dir / input_file.name
        try:
            total_registros, issues = transform_file(
                input_file, output_file, layout=layout
            )
            total_issues += len(issues)
            print(f"[OK] {input_file.name} -> {output_file.name} | registros: {total_registros}")

            if issues:
                print(f"[WARN] {input_file.name} teve {len(issues)} inconsistência(s):")
                for issue in issues:
                    iid = issue.intimacao_id if issue.intimacao_id else "(ausente)"
                    print(
                        f"  - registro #{issue.registro_index} | intimacaoId={iid} | "
                        f"campo '{issue.campo}': {issue.mensagem}"
                    )
            else:
                print(f"[INFO] {input_file.name} sem inconsistências de campos obrigatórios.")
        except Exception as exc:
            total_issues += 1
            print(f"[ERRO] Falha ao processar {input_file.name}: {exc}")

    print("\n[RESUMO]")
    print(f"- Saída em: {output_dir}")
    print(f"- Total de inconsistências: {total_issues}")
    return 0
