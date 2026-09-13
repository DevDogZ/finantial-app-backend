from pydantic import BaseModel, field_validator
from typing import Optional
from decimal import Decimal
from datetime import date
from models import TipoTransacao


class CategoriaBase(BaseModel):
    nome: str
    cor: Optional[str] = None


class CategoriaCreate(CategoriaBase):
    pass


class CategoriaResponse(CategoriaBase):
    id: int

    class config:
        from_attributes = True


class ContaBase(BaseModel):
    nome: str
    saldo_inicial: Decimal = 0


class ContaCreate(ContaBase):
    pass


class ContaResponse(ContaBase):
    id: int

    class Config:
        from_attributes = True


class TransacaoBase(BaseModel):
    descricao: str
    valor: Decimal
    tipo: TipoTransacao
    data: date
    conta_id: int
    categoria_id: int


class TransacaoCreate(TransacaoBase):
    pass

class TransacaoResponse(TransacaoBase):
    id: int

    class Config:
        from_attributes = True


class OrcamentoBase(BaseModel):
    categoria_id: int
    mes: int
    ano: int
    valor_limite: Decimal


class OrcamentoCreate(OrcamentoBase):
    pass

class OrcamentoResponse(OrcamentoBase):
    id: int

    class Config:
        from_attributes = True


class MetaBase(BaseModel):
    nome: str
    valor_alvo: Decimal

class MetaCreate(MetaBase):
    pass 

class MetaResponse(MetaBase):
    id: int
    valor_atual: Decimal

    class Config:
        from_attributes = True

class MetaContribuicao(BaseModel):
    valor: Decimal

class ContaFixaBase(BaseModel):
    nome: str
    valor: Decimal
    dia_vencimento: int
    categoria_id: int
    conta_id: int

    @field_validator("dia_vencimento")
    @classmethod
    def validar_dia(cls, v):
        if v < 1 or v > 31:
            raise ValueError("dia_vencimento deve estar entre 1 e 31")
        return v

class ContaFixaCreate(ContaFixaBase):
    pass 

class ContaFixaResponse(ContaFixaBase):
    id: int
    ativa: bool

    class Config:
        from_attributes = True



