import uuid
from datetime import datetime
from typing import Optional

class Prompt:
    """Modelo para representar um prompt de IA"""
    
    def __init__(self, 
                 nome: str,
                 conteudo: str,
                 descricao: Optional[str] = None,
                 regra_negocio: Optional[str] = None,
                 id: Optional[str] = None,
                 data_criacao: Optional[datetime] = None):
        """
        Inicializar um novo prompt
        
        Args:
            nome: Nome identificador do prompt
            conteudo: Texto do prompt
            descricao: Descrição opcional do prompt
            regra_negocio: Regra de negócio opcional do prompt
            id: ID único do prompt (gerado automaticamente se não fornecido)
            data_criacao: Data de criação (atual se não fornecida)
        """
        self.id = id or str(uuid.uuid4())
        self.nome = nome
        self.descricao = descricao or ""
        self.regra_negocio = regra_negocio or ""
        self.conteudo = conteudo
        self.data_criacao = data_criacao or datetime.now()
    
    def to_dict(self) -> dict:
        """Converter para dicionário para serialização JSON"""
        return {
            'id': self.id,
            'nome': self.nome,
            'descricao': self.descricao,
            'regra_negocio': self.regra_negocio,
            'conteudo': self.conteudo,
            'data_criacao': self.data_criacao.isoformat() if isinstance(self.data_criacao, datetime) else self.data_criacao
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Prompt':
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
            nome=data.get('nome', ''),
            descricao=data.get('descricao', ''),
            regra_negocio=data.get('regra_negocio', ''),
            conteudo=data.get('conteudo', ''),
            data_criacao=data_criacao
        )
    
    def validate(self) -> list:
        """Validar dados do prompt"""
        errors = []
        
        if not self.nome or not self.nome.strip():
            errors.append('Nome é obrigatório')
        
        if not self.conteudo or not self.conteudo.strip():
            errors.append('Conteúdo é obrigatório')
        
        if len(self.nome) > 200:
            errors.append('Nome deve ter no máximo 200 caracteres')
        
        if len(self.conteudo) > 10000:
            errors.append('Conteúdo deve ter no máximo 10.000 caracteres')
        
        return errors
    
    def get_preview(self, max_length: int = 100) -> str:
        """Obter preview do conteúdo do prompt"""
        if len(self.conteudo) <= max_length:
            return self.conteudo
        return self.conteudo[:max_length] + '...'
    
    def count_tokens_estimate(self) -> int:
        """Estimativa aproximada do número de tokens"""
        # Estimativa simples: ~4 caracteres por token
        return len(self.conteudo) // 4
    
    def __str__(self) -> str:
        """Representação string do prompt"""
        return f"Prompt({self.nome}): {self.get_preview(50)}"
    
    def __repr__(self) -> str:
        """Representação para debug"""
        return f"Prompt(id='{self.id}', nome='{self.nome}')"