from sqlalchemy import Column, Integer, String
from database import Base

class Categoria(Base):
    __tablename__ = "categorias"

    id = Column(Integer, primary_key = True, index = True)
    nome = Column(String, nullable= False, unique= True)
    cor = Column(String, nullable= True)

    
