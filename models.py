from sqlalchemy import (
    Column,
    Integer,
    String,
    Numeric,
    ForeignKey,
    Date,
    Enum,
    UniqueConstraint,
    Boolean,
)
from sqlalchemy.orm import relationship
import enum

from database import Base


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True, index=True)
    senha_hash = Column(String, nullable=False)

    categorias = relationship("Categoria", back_populates="usuario", cascade="all, delete-orphan")
    contas = relationship("Conta", back_populates="usuario", cascade="all, delete-orphan")
    orcamentos = relationship("Orcamento", back_populates="usuario", cascade="all, delete-orphan")
    metas = relationship("Meta", back_populates="usuario", cascade="all, delete-orphan")
    contas_fixas = relationship("ContaFixa", back_populates="usuario", cascade="all, delete-orphan")
    dividas = relationship("Divida", back_populates="usuario", cascade="all, delete-orphan")
    cartoes = relationship("CartaoCredito", back_populates="usuario", cascade="all, delete-orphan")


class Categoria(Base):
    __tablename__ = "categorias"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    cor = Column(String, nullable=True)

    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)

    usuario = relationship("Usuario", back_populates="categorias")
    transacoes = relationship("Transacao", back_populates="categoria")
    orcamentos = relationship("Orcamento", back_populates="categoria")
    contas_fixas = relationship("ContaFixa", back_populates="categoria")
    dividas = relationship("Divida", back_populates="categoria")
    compras_cartao = relationship("CompraCartao", back_populates="categoria")

    __table_args__ = (
        UniqueConstraint("usuario_id", "nome", name="categoria_nome_por_usuario"),
    )


class Conta(Base):
    __tablename__ = "contas"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    saldo_inicial = Column(Numeric(10, 2), nullable=False, default=0)

    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)

    usuario = relationship("Usuario", back_populates="contas")
    transacoes = relationship("Transacao", back_populates="conta")
    contas_fixas = relationship("ContaFixa", back_populates="conta")
    dividas = relationship("Divida", back_populates="conta")


class TipoTransacao(str, enum.Enum):
    entrada = "entrada"
    saida = "saida"


class Transacao(Base):
    __tablename__ = "transacoes"

    id = Column(Integer, primary_key=True, index=True)
    descricao = Column(String, nullable=False)
    valor = Column(Numeric(10, 2), nullable=False)
    tipo = Column(Enum(TipoTransacao), nullable=False)
    data = Column(Date, nullable=False)

    conta_id = Column(Integer, ForeignKey("contas.id"), nullable=False)
    categoria_id = Column(Integer, ForeignKey("categorias.id"), nullable=False)

    conta = relationship("Conta", back_populates="transacoes")
    categoria = relationship("Categoria", back_populates="transacoes")


class Orcamento(Base):
    __tablename__ = "orcamentos"

    id = Column(Integer, primary_key=True, index=True)

    categoria_id = Column(Integer, ForeignKey("categorias.id"), nullable=False)
    mes = Column(Integer, nullable=False)
    ano = Column(Integer, nullable=False)
    valor_limite = Column(Numeric(10, 2), nullable=False)

    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)

    usuario = relationship("Usuario", back_populates="orcamentos")
    categoria = relationship("Categoria", back_populates="orcamentos")

    __table_args__ = (
        UniqueConstraint(
            "usuario_id",
            "categoria_id",
            "mes",
            "ano",
            name="uma_categoria_por_usuario_mes",
        ),
    )


class Meta(Base):
    __tablename__ = "metas"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    valor_alvo = Column(Numeric(10, 2), nullable=False)
    valor_atual = Column(Numeric(10, 2), nullable=False, default=0)

    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)

    usuario = relationship("Usuario", back_populates="metas")


class ContaFixa(Base):
    __tablename__ = "contas_fixas"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    valor = Column(Numeric(10, 2), nullable=False)
    dia_vencimento = Column(Integer, nullable=False)

    categoria_id = Column(Integer, ForeignKey("categorias.id"), nullable=False)
    conta_id = Column(Integer, ForeignKey("contas.id"), nullable=False)
    ativa = Column(Boolean, nullable=False, default=True)

    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)

    usuario = relationship("Usuario", back_populates="contas_fixas")
    categoria = relationship("Categoria", back_populates="contas_fixas")
    conta = relationship("Conta", back_populates="contas_fixas")


class Divida(Base):
    __tablename__ = "dividas"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    valor_parcela = Column(Numeric(10, 2), nullable=False)
    numero_parcelas = Column(Integer, nullable=False)
    parcelas_pagas = Column(Integer, nullable=False, default=0)
    quitada = Column(Boolean, nullable=False, default=False)

    categoria_id = Column(Integer, ForeignKey("categorias.id"), nullable=False)
    conta_id = Column(Integer, ForeignKey("contas.id"), nullable=False)

    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)

    usuario = relationship("Usuario", back_populates="dividas")
    categoria = relationship("Categoria", back_populates="dividas")
    conta = relationship("Conta", back_populates="dividas")


class CartaoCredito(Base):
    __tablename__ = "cartoes_credito"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    limite = Column(Numeric(10, 2), nullable=False)
    dia_fechamento = Column(Integer, nullable=False)

    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)

    usuario = relationship("Usuario", back_populates="cartoes")
    compras = relationship(
        "CompraCartao",
        back_populates="cartao",
        cascade="all, delete-orphan",
    )


class CompraCartao(Base):
    __tablename__ = "compras_cartao"

    id = Column(Integer, primary_key=True)
    descricao = Column(String, nullable=False)
    valor_total = Column(Numeric(10, 2), nullable=False)
    numero_parcelas = Column(Integer, nullable=False)
    data_compra = Column(Date, nullable=False)

    cartao_id = Column(Integer, ForeignKey("cartoes_credito.id"), nullable=False)
    categoria_id = Column(Integer, ForeignKey("categorias.id"), nullable=False)

    cartao = relationship("CartaoCredito", back_populates="compras")
    categoria = relationship("Categoria", back_populates="compras_cartao")
    parcelas = relationship(
        "ParcelaCartao",
        back_populates="compra",
        cascade="all, delete-orphan",
    )


class ParcelaCartao(Base):
    __tablename__ = "parcelas_cartao"

    id = Column(Integer, primary_key=True, index=True)
    compra_id = Column(Integer, ForeignKey("compras_cartao.id"), nullable=False)
    numero_parcela = Column(Integer, nullable=False)
    valor_parcela = Column(Numeric(10, 2), nullable=False)
    mes_fatura = Column(Integer, nullable=False)
    ano_fatura = Column(Integer, nullable=False)
    paga = Column(Boolean, nullable=False, default=False)

    compra = relationship("CompraCartao", back_populates="parcelas")