from pydantic import BaseModel
from typing import Optional


class CategoriaBase(BaseModel):
    nome: str
    cor: Optional[str] = None


class CategoriaCreate(CategoriaBase):
    pass


class CategoriaResponse(CategoriaBase):
    id: int

    class config:
        from_attributes = True
        