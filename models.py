from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, Date, Enum
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