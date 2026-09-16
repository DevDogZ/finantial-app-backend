from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from utils import calcular_mes_ano_fatura, dividir_em_parcelas
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, case

from database import get_db
import models
import schemas

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)



@app.get("/")
def home():
    return {"Mensagem": "Finanças da casa no ar!"}

@app.post("/categorias", response_model=schemas.CategoriaResponse)
def criar_categoria(categoria: schemas.CategoriaCreate, db: Session = Depends(get_db)):
    nova_categoria = models.Categoria(**categoria.model_dump())
    db.add(nova_categoria)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Ja existe uma categoria com esse nome")
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


@app.post("/metas", response_model=schemas.MetaResponse)
def criar_meta(meta: schemas.MetaCreate, db: Session = Depends(get_db)):
    nova_meta = models.meta(**meta.model_dump())
    db.add(nova_meta)
    db.commit()
    db.refresh(nova_meta)
    return nova_meta

@app.get("/metas", response_model=list[schemas.MetaResponse])
def listar_metas(db: Session = Depends(get_db)):
    return db.query(models.meta).all()


@app.post("/metas/{meta_id}/contribuir", response_model=schemas.MetaResponse)
def contribuir_meta(meta_id: int, contribuicao: schemas.MetaContribuicao, db: Session = Depends(get_db)):
    meta = db.query(models.meta).filter(models.meta.id == meta_id).first()
    if meta is None:
        raise HTTPException(status_code=404, detail="Meta nao encontrada")

    if contribuicao.valor <= 0:
        raise HTTPException(status_code=400, detail="O valor do aporte deve ser positivo")

    meta.valor_atual += contribuicao.valor
    db.commit()
    db.refresh(meta)
    return meta


@app.post("/contas-fixas", response_model=schemas.ContaFixaResponse)
def criar_conta_fixa(conta_fixa: schemas.ContaFixaCreate, db: Session = Depends(get_db)):
    categoria = db.query(models.Categoria).filter(models.Categoria.id == conta_fixa.categoria_id).first()
    if categoria is None:
        raise HTTPException(status_code=404, detail="Categoria nao encontrada")

    conta = db.query(models.Conta).filter(models.Conta.id == conta_fixa.conta_id).first()
    if conta is None:
        raise HTTPException(status_code=404, detail="Conta nao encontrada")


    nova_conta_fixa = models.ContaFixa(**conta_fixa.model_dump())
    db.add(nova_conta_fixa)
    db.commit()
    db.refresh(nova_conta_fixa)
    return nova_conta_fixa


@app.get("/contas-fixas", response_model=list[schemas.ContaFixaResponse])
def listar_contas_fixas(db: Session = Depends(get_db)):
    return db.query(models.ContaFixa).filter(models.ContaFixa.ativa == True).all()

@app.post("/contas-fixas/{conta_fixa_id}/pagar", response_model=schemas.TransacaoResponse)
def pagar_conta_fixa(conta_fixa_id: int, db: Session = Depends(get_db)):
    from datetime import date

    conta_fixa = db.query(models.ContaFixa).filter(models.ContaFixa.id == conta_fixa_id).first()
    if conta_fixa is None:
        raise HTTPException(status_code=404, detail="Conta fixa nao encontrada")

    nova_transacao = models.Transacao(
        descricao = conta_fixa.nome,
        valor = conta_fixa.valor,
        tipo = models.TipoTransacao.saida,
        data = date.today(),
        conta_id = conta_fixa.conta_id,
        categoria_id = conta_fixa.categoria_id,
    )
    db.add(nova_transacao)
    db.commit()
    db.refresh(nova_transacao)
    return nova_transacao


@app.delete("/contas-fixas/{conta_fixa_id}")
def desativar_conta_fixa(conta_fixa_id: int, db: Session = Depends(get_db)):
    conta_fixa = db.query(models.ContaFixa).filter(models.ContaFixa.id == conta_fixa_id).first()
    if conta_fixa is None:
        raise HTTPException(status_code=404, detail="Conta fixa nao encontrada")

    conta_fixa.ativa = False
    db.commit()
    return {"detail": "Conta fixa desativada"}


@app.post("/dividas", response_model=schemas.DividaResponse)
def criar_divida(divida: schemas.DividaCreate, db: Session = Depends(get_db)):
    categoria = db.query(models.Categoria).filter(models.Categoria.id == divida.categoria_id).first()
    if categoria is None:
        raise HTTPException(status_code=404, detail="Categoria nao encontrada")

    conta = db.query(models.Conta).filter(models.Conta.id == divida.conta_id).first()
    if conta is None:
        raise HTTPException(status_code=404, detail="Conta nao encontrada")

    nova_divida = models.Divida(**divida.model_dump())
    db.add(nova_divida)
    db.commit()
    db.refresh(nova_divida)
    return nova_divida

@app.get("/dividas", response_model=list[schemas.DividaResponse])
def listar_dividas(db: Session = Depends(get_db)):
    return db.query(models.Divida).all()

@app.post("/dividas/{divida_id}/pagar-parcela", response_model=schemas.TransacaoResponse)
def pagar_parcela_divida(divida_id: int, db: Session = Depends(get_db)):
    from datetime import date

    divida = db.query(models.Divida).filter(models.Divida.id == divida_id).first()
    if divida is None:
        raise HTTPException(status_code=404, detail="Divida nao encontrada")

    if divida.quitada:
        raise HTTPException(status_code=400, detail="Essa divida ja foi quitada")

    nova_transacao = models.Transacao(
        descricao = f"{divida.nome} - parcela {divida.parcelas_pagas + 1}/{divida.numero_parcelas}",
        valor = divida.valor_parcela,
        tipo = models.TipoTransacao.saida,
        data = date.today(),
        conta_id = divida.conta_id,
        categoria_id = divida.categoria_id,
    )
    db.add(nova_transacao)

    divida.parcelas_pagas += 1
    if divida.parcelas_pagas >= divida.numero_parcelas:
        divida.quitada = True

    db.commit()
    db.refresh(nova_transacao)
    return nova_transacao

@app.post("/cartoes", response_model=schemas.CartaoCreditoResponse)
def criar_cartao(cartao: schemas.CartaoCreditoCreate, db: Session = Depends(get_db)):
    novo_cartao = models.CartaoCredito(**cartao.model_dump())
    db.add(novo_cartao)
    db.commit()
    db.refresh(novo_cartao)
    return novo_cartao

@app.get("/cartoes", response_model = list[schemas.CartaoCreditoResponse])
def listar_cartoes(db: Session = Depends(get_db)):
    return db.query(models.CartaoCredito).all()

@app.post("/compras-cartao", response_model=schemas.CompraCartaoResponse)
def criar_compra_cartao(compra: schemas.CompraCartaoCreate, db: Session = Depends(get_db)):

    cartao = db.query(models.CartaoCredito).filter(models.CartaoCredito.id == compra.cartao_id).first()
    if cartao is None:
        raise HTTPException(status_code=404, detail="Cartao nao encontrado")

    categoria = db.query(models.Categoria).filter(models.Categoria.id == compra.categoria_id).first()
    if categoria is None:
        raise HTTPException(status_code=404, detail="Categoria nao encontrada")

    nova_compra = models.CompraCartao(**compra.model_dump())
    db.add(nova_compra)
    db.flush()

    valores = dividir_em_parcelas(compra.valor_total, compra.numero_parcelas)

    for i, valor in enumerate(valores, start=1):
        mes_fatura, ano_fatura = calcular_mes_ano_fatura(compra.data_compra, cartao.dia_fechamento, i)
        parcela = models.ParcelaCartao(
            compra_id = nova_compra.id,
            numero_parcela = i,
            valor_parcela = valor,
            mes_fatura = mes_fatura,
            ano_fatura = ano_fatura,
        )
        db.add(parcela)

    db.commit()
    db.refresh(nova_compra)
    return nova_compra

@app.get("/cartoes/{cartao_id}/fatura")
def ver_fatura(cartao_id: int, mes: int, ano: int, db: Session = Depends(get_db)):
    parcelas = (
        db.query(models.ParcelaCartao)
        .join(models.CompraCartao)
        .filter(
            models.CompraCartao.cartao_id == cartao_id,
            models.ParcelaCartao.mes_fatura == mes,
            models.ParcelaCartao.ano_fatura == ano,
        )
        .all()
    )
    total = sum(p.valor_parcela for p in parcelas)
    return {
        "mes": mes,
        "ano": ano,
        "total": total,
        "parcelas": [schemas.ParcelaCartaoResponse.model_validate(p) for p in parcelas],
    }


@app.get("/contas/{conta_id}/saldo")
def calcular_saldo(conta_id: int, db: Session = Depends(get_db)):
    conta = db.query(models.Conta).filter(models.Conta.id == conta_id).first()
    if conta is None:
        raise HTTPException(status_code=404, detail="Conta nao encontrada")

    resultado = (
        db.query(
            func.sum(
                case(
                    (models.Transacao.tipo == models.TipoTransacao.entrada, models.Transacao.valor),
                    else_=-models.Transacao.valor,
                )
            )
        )
        .filter(models.Transacao.conta_id == conta_id).scalar()
    )

    total_transacoes = resultado or 0
    saldo = conta.saldo_inicial + total_transacoes

    return {"conta_id": conta_id, "saldo_inical": conta.saldo_inicial, "saldo_atual": saldo}