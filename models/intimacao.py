import uuid
from datetime import datetime
from typing import Optional

class Intimacao:
    """Modelo para representar uma intimação jurídica"""
    
    def __init__(self, 
                 contexto: str,
                 classificacao_manual: str,
                 informacao_adicional: Optional[str] = None,
                 processo: Optional[str] = None,
                 orgao_julgador: Optional[str] = None,
                 classe: Optional[str] = None,
                 disponibilizacao: Optional[str] = None,
                 intimado: Optional[str] = None,
                 status: Optional[str] = None,
                 prazo: Optional[str] = None,
                 id: Optional[str] = None,
                 data_criacao: Optional[datetime] = None):
        """
        Inicializar uma nova intimação
        
        Args:
            contexto: Texto completo da intimação
            classificacao_manual: Classificação manual da intimação
            informacao_adicional: Observações opcionais do usuário
            processo: Número do processo
            orgao_julgador: Órgão julgador
            classe: Classe processual
            disponibilizacao: Data de disponibilização
            intimado: Nome do intimado
            status: Status da intimação
            prazo: Prazo da intimação
            id: ID único da intimação (gerado automaticamente se não fornecido)
            data_criacao: Data de criação (atual se não fornecida)
        """
        self.id = id or str(uuid.uuid4())
        self.contexto = contexto
        self.classificacao_manual = classificacao_manual
        self.informacao_adicional = informacao_adicional or ""
        self.processo = processo or ""
        self.orgao_julgador = orgao_julgador or ""
        self.classe = classe or ""
        self.disponibilizacao = disponibilizacao or ""
        self.intimado = intimado or ""
        self.status = status or ""
        self.prazo = prazo or ""
        self.data_criacao = data_criacao or datetime.now()
    
    def to_dict(self) -> dict:
        """Converter para dicionário para serialização JSON"""
        return {
            'id': self.id,
            'contexto': self.contexto,
            'classificacao_manual': self.classificacao_manual,
            'informacao_adicional': self.informacao_adicional,
            'processo': self.processo,
            'orgao_julgador': self.orgao_julgador,
            'classe': self.classe,
            'disponibilizacao': self.disponibilizacao,
            'intimado': self.intimado,
            'status': self.status,
            'prazo': self.prazo,
            'data_criacao': self.data_criacao.isoformat() if isinstance(self.data_criacao, datetime) else self.data_criacao
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Intimacao':
        """Criar instância a partir de dicionário"""
        data_criacao = data.get('data_criacao')
        if isinstance(data_criacao, str):
            try:
                data_criacao = datetime.fromisoformat(data_criacao.replace('Z', '+00:00'))
            except ValueError:
                data_criacao = datetime.now()
        elif data_criacao is None:
            data_criacao = datetime.now()
        
        return cls(
            id=data.get('id'),
            contexto=data.get('contexto', ''),
            classificacao_manual=data.get('classificacao_manual', ''),
            informacao_adicional=data.get('informacao_adicional', ''),
            processo=data.get('processo', ''),
            orgao_julgador=data.get('orgao_julgador', ''),
            classe=data.get('classe', ''),
            disponibilizacao=data.get('disponibilizacao', ''),
            intimado=data.get('intimado', ''),
            status=data.get('status', ''),
            prazo=data.get('prazo', ''),
            data_criacao=data_criacao
        )
    
    def validate(self) -> list:
        """Validar dados da intimação"""
        errors = []
        
        if not self.contexto or not self.contexto.strip():
            errors.append('Contexto é obrigatório')
        
        if not self.classificacao_manual or not self.classificacao_manual.strip():
            errors.append('Classificação manual é obrigatória')
        
        # Validar se a classificação está na lista de tipos válidos
        from config import Config
        if self.classificacao_manual not in Config.TIPOS_ACAO:
            errors.append(f'Classificação manual deve ser uma das opções: {", ".join(Config.TIPOS_ACAO)}')
        
        return errors
    
    def __str__(self) -> str:
        """Representação string da intimação"""
        contexto_resumido = self.contexto[:100] + '...' if len(self.contexto) > 100 else self.contexto
        return f"Intimação({self.id}): {contexto_resumido} - {self.classificacao_manual}"
    
    def __repr__(self) -> str:
        """Representação para debug"""
        return f"Intimacao(id='{self.id}', classificacao_manual='{self.classificacao_manual}')"