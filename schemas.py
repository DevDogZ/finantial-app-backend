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

    class Config:
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


class DividaBase(BaseModel):
    nome: str
    valor_parcela: Decimal
    numero_parcelas: int
    categoria_id: int
    conta_id: int

    @field_validator("numero_parcelas")
    @classmethod
    def validar_parcelas(cls, v):
        if v < 1:
            raise ValueError("Numero de parcelas deve ser pelo menos 1")
        return v


class DividaCreate(DividaBase):
    pass

class DividaResponse(DividaBase):
    id: int
    parcelas_pagas: int
    quitada: bool

    class Config:
        from_attributes = True


class CartaoCreditoBase(BaseModel):
    nome: str
    limite: Decimal
    dia_fechamento: int

    @field_validator("dia_fechamento")
    @classmethod
    def validar_dia(cls, v):
        if v < 1 or v > 31:
            raise ValueError("dia_fechamento deve estar entre 1 e 31")
        return v

class CartaoCreditoCreate(CartaoCreditoBase):
    pass 

class CartaoCreditoResponse(CartaoCreditoBase):
    id: int

    class Config:
        from_attributes = True

class CompraCartaoCreate(BaseModel):
    descricao: str
    valor_total: Decimal
    numero_parcelas: int
    data_compra: date
    cartao_id: int
    categoria_id: int

    @field_validator("numero_parcelas")
    @classmethod
    def validar_parcelas(cls, v):
        if v < 1:
            raise ValueError("numero_parcelas deve ser pelo menos 1")
        return v

class ParcelaCartaoResponse(BaseModel):
    id: int
    numero_parcela: int
    valor_parcela: Decimal
    mes_fatura: int
    ano_fatura: int
    paga: bool

    class Config:
        from_attributes = True

class CompraCartaoResponse(BaseModel):
    id: int
    descricao: str
    valor_total: Decimal
    numero_parcelas: int
    data_compra: date
    cartao_id: int
    categoria_id: int
    parcelas: list[ParcelaCartaoResponse]

    class Config:
        from_attributes = True


class UsuarioCreate(BaseModel):
    nome: str
    email: str
    senha: str


class UsuarioResponse(BaseModel):
    id: int
    nome: str
    email: str

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    user_id: Optional[int] = None

class LoginRequest(BaseModel):
    email: str
    senha: str

