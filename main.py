from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

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


@app.post("/contas", response_model = schemas.ContaResponse)
def criar_conta(conta: schemas.ContaCreate, db: Session = Depends(get_db)):
    nova_conta = models.Conta(**conta.model_dump())
    db.add(nova_conta)
    db.commit()
    db.refresh(nova_conta)
    return nova_conta


@app.get("/contas", response_model=list[schemas.ContaResponse])
def listar_contas(db: Session = Depends(get_db)):
    return db.query(models.Conta).all()


@app.post("/transacoes", response_model=schemas.TransacaoResponse)
def criar_transacao(transacao: schemas.TransacaoCreate, db: Session = Depends(get_db)):
    conta = db.query(models.Conta).filter(models.Conta.id == transacao.conta_id).first()
    if conta is None:
        raise HTTPException(status_code=404, detail = "Conta nao encontrada")

    categoria = db.query(models.Categoria).filter(models.Categoria.id == transacao.categoria_id).first()
    if categoria is None:
        raise HTTPException(status_code=404, detail="Categoria nao encontrada")

    nova_transacao = models.Transacao(**transacao.model_dump())
    db.add(nova_transacao)
    db.commit()
    db.refresh(nova_transacao)
    return nova_transacao


@app.get("/transacoes", response_model=list[schemas.TransacaoResponse])
def listar_transacoes(db: Session = Depends(get_db)):
    return db.query(models.Transacao).all()


@app.post("/orcamentos", response_model=schemas.OrcamentoResponse)
def criar_orcamento(orcamento: schemas.OrcamentoCreate, db: Session = Depends(get_db)):
    categoria = db.query(models.Categoria).filter(models.Categoria.id == orcamento.categoria_id).first()
    if categoria is None:
        raise HTTPException(status_code=404, detail="Categoria nao encontrada")

    novo_orcamento = models.Orcamento(**orcamento.model_dump())
    db.add(novo_orcamento)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Ja existe um orcamento para essa categoria neste mes/ano")
    db.refresh(novo_orcamento)
    return novo_orcamento

@app.get("/orcamentos", response_model=list[schemas.OrcamentoResponse])
def listar_orcamentos(mes: int | None = None, ano: int | None = None, db: Session = Depends(get_db)):
    query = db.query(models.Orcamento)
    if mes is not None:
        query = query.filter(models.Orcamento.mes == mes)
    if ano is not None:
        query = query.filter(models.Orcamento.ano == ano)
    return query.all()


