from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, Date, Enum, UniqueConstraint, Boolean
from sqlalchemy.orm import relationship
import enum
from database import Base


class Categoria(Base):
    __tablename__ = "categorias"

    id = Column(Integer, primary_key = True, index = True)
    nome = Column(String, nullable= False, unique= True)
    cor = Column(String, nullable= True)


class Conta(Base):
    __tablename__ = "contas"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    saldo_inicial = Column(Numeric(10,2), nullable=False, default=0)


class TipoTransacao(str, enum.Enum):
    entrada = "entrada"
    saida = "saida"


class Transacao(Base):
    __tablename__ = "transacoes"

    id = Column(Integer, primary_key= True, index= True)
    descricao = Column(String, nullable= False)
    valor = Column(Numeric(10,2), nullable= False)
    tipo = Column(Enum(TipoTransacao), nullable=False)
    data = Column(Date, nullable=False)

    conta_id = Column(Integer, ForeignKey("contas.id"), nullable=False)
    categoria_id = Column(Integer, ForeignKey("categorias.id"), nullable=False)

    conta = relationship("Conta")
    categoria = relationship("Categoria")


class Orcamento(Base):
    __tablename__ = "orcamentos"
    __table_args__ = (
        UniqueConstraint("categoria_id", "mes", "ano", name="uma_categoria_por_mes"),
    )

    id = Column(Integer, primary_key=True, index=True)
    categoria_id = Column(Integer, ForeignKey("categorias.id"), nullable=False)
    mes = Column(Integer, nullable=False)
    ano= Column(Integer, nullable=False)
    valor_limite = Column(Numeric(10,2), nullable=False)

    categoria = relationship("Categoria")


class Meta(Base):
    __tablename__ = "metas"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    valor_alvo = Column(Numeric(10,2), nullable=False)
    valor_atual = Column(Numeric(10,2), nullable=False, default=0)

class ContaFixa(Base):
    __tablename__ = "contas_fixas"


    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    valor = Column(Numeric(10,2), nullable=False)
    dia_vencimento = Column(Integer, nullable=False)
    categoria_id = Column(Integer, ForeignKey("categorias.id"), nullable=False)
    conta_id = Column(Integer, ForeignKey("contas.id"), nullable=False)
    ativa = Column(Boolean, nullable=False, default=True)

    categoria = relationship("Categoria")
    conta = relationship("Conta")

    
