from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
import models
import schemas

app = FastAPI()

@app.get("/")
def home():
    return {"Mensagem": "Finanças da casa no ar!"}

@app.post("/categorias", response_model=schemas.CategoriaResponse)
def criar_categoria(Categoria: schemas.CategoriaCreate, db: Session = Depends(get_db)):
    nova_categoria = models.Categoria(**Categoria.model_dump())
    db.add(nova_categoria)
    db.commit()
    db.refresh(nova_categoria)
    return nova_categoria

@app.get("/categorias", response_model=list[schemas.CategoriaResponse])
def listar_categorias(db: Session = Depends(get_db)):
    return db.query(models.Categoria).all()

@app.get("/categorias/{categoria_id}", response_model=schemas.CategoriaResponse)
def buscar_categoria(categoria_id: int, db: Session = Depends(get_db)):
    categoria = db.query(models.Categoria).filter(models.Categoria.id == categoria_id).first()
    if categoria is None:
        raise HTTPException(status_code=404, detail="Categoria nao encontrada")
    return categoria


@app.put("/categorias/{categoria_id}", response_model=schemas.CategoriaResponse)
def atualizar_categoria(categoria_id: int, dados: schemas.CategoriaCreate, db: Session = Depends(get_db)):
    categoria = db.query(models.Categoria).filter(models.Categoria.id == categoria_id).first()
    if categoria is None:
        raise HTTPException(status_code=404, detail="Categoria nao encontrada")
    categoria.nome = dados.nome
    categoria.cor = dados.cor
    db.commit()
    db.refresh(categoria)
    return categoria

@app.delete("/categorias/{categoria_id}")
def deletar_categoria(categoria_id: int, db: Session = Depends(get_db)):
    categoria = db.query(models.Categoria).filter(models.Categoria.id == categoria_id).first()
    if categoria is None:
        raise HTTPException(status_code=404, detail="Categoria nao encontrada")
    db.delete(categoria)
    db.commit()
    return {"detail": "Categoria deletada"}

