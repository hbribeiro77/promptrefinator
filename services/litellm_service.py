"""Cliente LiteLLM via API compatível com OpenAI (SDK openai + base_url)."""
import ssl
import time
from typing import Tuple, Dict, Any, List, Optional, Union
from urllib.parse import urlparse

import httpx
import openai

from config import Config
from services.sqlite_service import SQLiteService
from services.ai_service_interface import AIServiceInterface
from services.classificacao_ia_extracao_resposta_texto_para_tipo_canonico_service import (
    extrair_classificacao_da_resposta_ia,
)
from services.extracao_texto_resposta_chat_completions_openai_compat import (
    texto_mensagem_assistente,
)


def _normalize_litellm_base_url(url: str) -> str:
    u = (url or "").strip().rstrip("/")
    if not u:
        return u
    if u.endswith("/v1"):
        return u
    return f"{u}/v1"


def _litellm_proxy_url(config: Config) -> Optional[str]:
    """Uma URL de proxy explícita (HTTPS > HTTP > LITELLM_PROXY)."""
    return (
        config.LITELLM_HTTPS_PROXY
        or config.LITELLM_HTTP_PROXY
        or config.LITELLM_PROXY
    )


def _mask_proxy_for_log(proxy_url: str) -> str:
    try:
        p = urlparse(proxy_url)
        if p.username:
            host = p.hostname or ""
            port = f":{p.port}" if p.port else ""
            return f"{p.scheme}://***:***@{host}{port}"
        return proxy_url
    except Exception:
        return "(proxy)"


def build_litellm_http_client(config: Config) -> httpx.Client:
    """Cliente HTTP para o SDK OpenAI: proxy corporativo, trust_env, SSL."""
    proxy = _litellm_proxy_url(config)
    trust_env = config.LITELLM_PROXY_TRUST_ENV

    verify: Union[bool, str] = True
    if config.LITELLM_CA_BUNDLE_PATH:
        verify = config.LITELLM_CA_BUNDLE_PATH
    elif not config.LITELLM_SSL_VERIFY:
        verify = False

    timeout = httpx.Timeout(120.0, connect=60.0)
    kwargs: Dict[str, Any] = {
        "trust_env": trust_env,
        "timeout": timeout,
        "verify": verify,
    }
    if proxy:
        kwargs["proxy"] = proxy

    return httpx.Client(**kwargs)


def _ssl_tls_hint_from_exception(exc: BaseException) -> Optional[str]:
    """Se a cadeia de exceções indica TLS/certificado, sugere ajuste no .env."""
    seen: List[BaseException] = []
    cur: Optional[BaseException] = exc
    while cur is not None and len(seen) < 12:
        if cur in seen:
            break
        seen.append(cur)
        if isinstance(cur, ssl.SSLError):
            return (
                " Falha de SSL/TLS (ex.: certificado interno não confiável pelo Python). "
                "Como Test-NetConnection na 443 costuma passar, tente no .env: LITELLM_SSL_VERIFY=false "
                "ou o caminho da CA corporativa em LITELLM_CA_BUNDLE_PATH."
            )
        msg = str(cur).lower()
        if any(
            x in msg
            for x in (
                "certificate",
                "cert verify",
                "ssl",
                "tls",
                "handshake",
                "self signed",
            )
        ):
            return (
                " Indícios de problema de certificado/TLS. Tente LITELLM_SSL_VERIFY=false "
                "(teste) ou LITELLM_CA_BUNDLE_PATH com o .pem da CA da instituição."
            )
        cur = cur.__cause__ or cur.__context__
    return None


class LiteLLMService(AIServiceInterface):
    """Proxy LiteLLM exposto como OpenAI-compatible chat completions."""

    def __init__(self):
        self.data_service = SQLiteService()
        self.config = Config()
        self.client = None
        self._http_client: Optional[httpx.Client] = None
        self._initialize_client()

    def initialize_client(self) -> bool:
        return self._initialize_client()

    def _initialize_client(self) -> bool:
        try:
            api_key = self.config.LITELLM_API_KEY or ""
            endpoint = self.config.LITELLM_ENDPOINT or ""
            db = self.data_service.get_config() or {}
            if not api_key:
                api_key = (db.get("litellm_api_key") or "").strip()
            if not endpoint:
                endpoint = (db.get("litellm_endpoint") or "").strip()

            if api_key and endpoint:
                base_url = _normalize_litellm_base_url(endpoint)
                if self._http_client is not None:
                    try:
                        self._http_client.close()
                    except Exception:
                        pass
                self._http_client = build_litellm_http_client(self.config)
                self.client = openai.OpenAI(
                    api_key=api_key,
                    base_url=base_url,
                    http_client=self._http_client,
                )
                proxy = _litellm_proxy_url(self.config)
                extra = ""
                if proxy:
                    extra = f", proxy={_mask_proxy_for_log(proxy)}"
                if self.config.LITELLM_PROXY_TRUST_ENV:
                    extra += ", trust_env=HTTP(S)_PROXY do ambiente"
                print(f"SUCESSO: Cliente LiteLLM inicializado (base_url={base_url}{extra})")
                return True

            print("AVISO: LiteLLM sem LITELLM_API_KEY ou LITELLM_ENDPOINT no .env.")
            self.client = None
            return True
        except Exception as e:
            print(f"ERRO: Falha ao inicializar LiteLLM: {e}")
            self.client = None
            return True

    def _resolved_default_model(self) -> str:
        db = self.data_service.get_config() or {}
        raw = (db.get("litellm_default_model") or "").strip() or self.config.LITELLM_DEFAULT_MODEL
        return Config.normalize_litellm_model(raw)

    def _test_model(self) -> str:
        if self.config.LITELLM_TEST_MODEL:
            tm = self.config.LITELLM_TEST_MODEL
            s = tm.strip() if isinstance(tm, str) else str(tm).strip()
            return Config.normalize_litellm_model(s)
        return self._resolved_default_model()

    def test_connection(self) -> Tuple[bool, str]:
        if not self.client:
            return False, (
                "Cliente LiteLLM não inicializado. Defina LITELLM_API_KEY e LITELLM_ENDPOINT no .env "
                "(endpoint será normalizado com /v1 se necessário)."
            )
        modelo = self._test_model()
        try:
            self.client.chat.completions.create(
                model=modelo,
                messages=[{"role": "user", "content": "Responda apenas OK."}],
                max_tokens=5,
                temperature=0,
            )
            return True, f"Conexão com LiteLLM estabelecida (modelo de teste: {modelo})."
        except openai.AuthenticationError:
            return False, "Erro de autenticação LiteLLM. Verifique LITELLM_API_KEY."
        except openai.RateLimitError:
            return False, "Limite de taxa no LiteLLM. Tente novamente mais tarde."
        except openai.APIConnectionError as e:
            tls_hint = _ssl_tls_hint_from_exception(e)
            if tls_hint:
                return False, f"Falha ao contatar LiteLLM: {e}.{tls_hint}"
            return False, (
                f"Falha de rede ao contatar LiteLLM: {e}. "
                "Se Test-NetConnection na porta 443 já deu OK, o próximo suspeito é TLS: "
                "LITELLM_SSL_VERIFY=false (teste) ou LITELLM_CA_BUNDLE_PATH. "
                "Caso use proxy HTTP explícito: LITELLM_HTTPS_PROXY ou HTTP_PROXY/HTTPS_PROXY "
                "com LITELLM_PROXY_TRUST_ENV=true."
            )
        except openai.APIError as e:
            return False, f"Erro da API LiteLLM: {str(e)}"
        except Exception as e:
            return False, f"Erro inesperado: {str(e)}"

    def analisar_intimacao(
        self,
        contexto: str,
        prompt_template: str,
        parametros: Dict[str, Any],
    ) -> Tuple[str, str, Dict[str, int]]:
        if not self.client:
            raise Exception("Cliente LiteLLM não inicializado. Configure .env.")

        p = dict(parametros)
        raw_user_only = bool(p.pop("raw_user_prompt_only", False))
        prompt_completo = (
            prompt_template
            if raw_user_only
            else self._construir_prompt(prompt_template, contexto)
        )
        parametros_validados = self._validar_parametros(p)
        parametros_validados["_raw_user_only"] = raw_user_only
        resposta_completa, tokens_info = self._fazer_chamada_com_retry(
            prompt_completo, parametros_validados
        )
        classificacao = self._extrair_classificacao(resposta_completa)
        return classificacao, resposta_completa, tokens_info

    def _construir_prompt(self, template: str, contexto: str) -> str:
        tipos_acao = self.config.TIPOS_ACAO
        tipos_acao_str = "\n".join([f"- {acao}" for acao in tipos_acao])
        prompt = template.replace("{contexto}", contexto)
        prompt = prompt.replace("{tipos_acao}", tipos_acao_str)
        if "tipos de ação" not in prompt.lower() and "classificação" not in prompt.lower():
            prompt += (
                f"\n\nTipos de ação disponíveis:\n{tipos_acao_str}\n\n"
                "Responda APENAS com um dos tipos de ação listados acima."
            )
        return prompt

    def _validar_parametros(self, parametros: Dict[str, Any]) -> Dict[str, Any]:
        modelo = parametros.get("model") or parametros.get("modelo") or self._resolved_default_model()
        modelo = Config.normalize_litellm_model(modelo)
        temp = float(parametros.get("temperature", parametros.get("temperatura", 0.7)))
        max_tok = int(parametros.get("max_tokens", 500))
        temp = max(0.0, min(2.0, temp))
        max_tok = max(1, max_tok)
        return {"model": modelo, "temperature": temp, "max_tokens": max_tok}

    def _fazer_chamada_com_retry(
        self, prompt: str, parametros: Dict[str, Any], max_retries: int = 3
    ) -> Tuple[str, Dict[str, int]]:
        for tentativa in range(max_retries):
            try:
                raw_only = bool(parametros.get("_raw_user_only"))
                if raw_only:
                    messages: List[Dict[str, str]] = [{"role": "user", "content": prompt}]
                else:
                    messages = [
                        {
                            "role": "system",
                            "content": (
                                "Você é um assistente especializado em análise de intimações jurídicas. "
                                "Responda sempre com uma das classificações solicitadas."
                            ),
                        },
                        {"role": "user", "content": prompt},
                    ]
                response = self.client.chat.completions.create(
                    model=parametros["model"],
                    messages=messages,
                    temperature=parametros["temperature"],
                    max_tokens=parametros["max_tokens"],
                )
                tokens_info = {
                    "input": response.usage.prompt_tokens if response.usage else 0,
                    "output": response.usage.completion_tokens if response.usage else 0,
                    "total": response.usage.total_tokens if response.usage else 0,
                }
                choice0 = response.choices[0]
                texto = texto_mensagem_assistente(choice0.message)
                if not texto:
                    fr = getattr(choice0, "finish_reason", None)
                    print(
                        "LiteLLM: corpo assistant vazio após extração. "
                        f"finish_reason={fr!r}, model={parametros.get('model')!r}, "
                        f"completion_tokens={tokens_info.get('output')}"
                    )
                return texto, tokens_info
            except openai.RateLimitError:
                if tentativa < max_retries - 1:
                    time.sleep(2**tentativa)
                else:
                    raise Exception("Limite de taxa LiteLLM após várias tentativas")
            except openai.APIError as e:
                if tentativa < max_retries - 1:
                    time.sleep(2**tentativa)
                else:
                    raise Exception(f"Erro da API LiteLLM após várias tentativas: {str(e)}")
            except Exception as e:
                raise Exception(f"Erro na chamada LiteLLM: {str(e)}")
        raise Exception("Falha ao completar chamada LiteLLM")

    def _extrair_classificacao(self, resposta: str) -> str:
        return extrair_classificacao_da_resposta_ia(resposta, self.config.TIPOS_ACAO)

    def get_available_models(self) -> List[str]:
        return Config.get_litellm_ui_models()

    def analyze_text(
        self,
        prompt: str,
        modelo: str = "gpt-4",
        temperatura: float = 0.1,
        max_tokens: int = 500,
    ) -> str:
        if not self.client:
            raise Exception("Cliente LiteLLM não inicializado.")
        parametros = self._validar_parametros(
            {
                "model": modelo,
                "temperature": temperatura,
                "max_tokens": max_tokens,
            }
        )
        texto, _ = self._fazer_chamada_com_retry(prompt, parametros)
        return texto

    def get_provider_name(self) -> str:
        return "LiteLLM"

    def get_default_parameters(self) -> Dict[str, Any]:
        return {
            "model": self._resolved_default_model(),
            "temperature": self.config.OPENAI_DEFAULT_TEMPERATURE,
            "max_tokens": self.config.OPENAI_DEFAULT_MAX_TOKENS,
        }

    def validate_parameters(self, parametros: Dict[str, Any]) -> Dict[str, Any]:
        return self._validar_parametros(parametros)
