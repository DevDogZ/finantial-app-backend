# relatorios.py
"""
Geração do "Relatório Geral" em PDF, com o mesmo padrão visual (neon/dark)
do app FinanDog.

Dependências novas (adicionar no requirements.txt):
    weasyprint
    jinja2
    matplotlib

Observação sobre nomes de campos:
    Este módulo assume os nomes de campo abaixo, com base no que já é usado
    em main.py. Se algum nome for diferente no seu models.py/schemas.py,
    ajuste só a função `montar_dados_relatorio` — o resto (template e PDF)
    não muda.
        Orcamento.limite        -> valor limite do orçamento
        Meta.valor_alvo         -> valor alvo da meta
        ContaFixa.dia_vencimento-> dia de vencimento
        Conta.nome              -> nome da conta
"""

import base64
import calendar
import io
from datetime import date

import matplotlib
matplotlib.use("Agg")  # backend sem interface gráfica, necessário no servidor
import matplotlib.patheffects as patheffects
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
from dateutil.relativedelta import relativedelta
from jinja2 import Environment
from sqlalchemy import func
from sqlalchemy.orm import Session
from weasyprint import HTML

import models

# ============================================================
# PALETA NEON — ajuste aqui para bater 100% com o app
# ============================================================
CORES = {
    "bg": "#0b0e17",
    "bg_card": "#121729",
    "bg_card_alt": "#161c33",
    "borda": "#232a45",
    "texto": "#e7e9f5",
    "texto_fraco": "#8d93b0",
    "neon_verde": "#39ff9d",     # entradas / positivo
    "neon_rosa": "#ff2e6d",      # gastos / negativo
    "neon_azul": "#00e5ff",      # destaque / saldo / marca
    "neon_roxo": "#b26bff",      # destaque secundário
    "neon_amarelo": "#ffd23f",   # alertas / metas
}

CORES_CATEGORIAS = [
    CORES["neon_azul"],
    CORES["neon_roxo"],
    CORES["neon_verde"],
    CORES["neon_rosa"],
    CORES["neon_amarelo"],
    "#4dd0e1",
    "#c792ea",
]

NOME_APP = "FinanDog"  # <- troque se o nome do app no frontend for outro


# ============================================================
# 1) AGREGAÇÃO DOS DADOS
# ============================================================
def montar_dados_relatorio(db: Session, usuario: models.Usuario, mes: int, ano: int) -> dict:
    primeiro_dia = date(ano, mes, 1)
    ultimo_dia = date(ano, mes, calendar.monthrange(ano, mes)[1])

    transacoes = (
        db.query(models.Transacao)
        .join(models.Conta, models.Transacao.conta_id == models.Conta.id)
        .filter(
            models.Conta.usuario_id == usuario.id,
            models.Transacao.data >= primeiro_dia,
            models.Transacao.data <= ultimo_dia,
        )
        .order_by(models.Transacao.data)
        .all()
    )

    entradas = sum(t.valor for t in transacoes if t.tipo == models.TipoTransacao.entrada)
    gastos = sum(t.valor for t in transacoes if t.tipo == models.TipoTransacao.saida)
    saldo = entradas - gastos

    # gastos por categoria
    gastos_por_categoria = {}
    for t in transacoes:
        if t.tipo == models.TipoTransacao.saida:
            nome_cat = t.categoria.nome
            gastos_por_categoria[nome_cat] = gastos_por_categoria.get(nome_cat, 0) + t.valor

    categorias = []
    for i, (nome_cat, valor) in enumerate(
        sorted(gastos_por_categoria.items(), key=lambda x: x[1], reverse=True)
    ):
        pct = (valor / gastos * 100) if gastos else 0
        categorias.append(
            {
                "nome": nome_cat,
                "valor": valor,
                "pct": pct,
                "cor": CORES_CATEGORIAS[i % len(CORES_CATEGORIAS)],
            }
        )

    # evolução dos últimos 6 meses (entradas x gastos)
    evolucao = []
    for i in range(5, -1, -1):
        ref = (primeiro_dia - relativedelta(months=i))
        ini = ref.replace(day=1)
        fim = ref.replace(day=calendar.monthrange(ref.year, ref.month)[1])
        linha = (
            db.query(
                func.sum(
                    func.case((models.Transacao.tipo == models.TipoTransacao.entrada, models.Transacao.valor), else_=0)
                ),
                func.sum(
                    func.case((models.Transacao.tipo == models.TipoTransacao.saida, models.Transacao.valor), else_=0)
                ),
            )
            .join(models.Conta, models.Transacao.conta_id == models.Conta.id)
            .filter(
                models.Conta.usuario_id == usuario.id,
                models.Transacao.data >= ini,
                models.Transacao.data <= fim,
            )
            .first()
        )
        evolucao.append(
            {
                "label": f"{ref.strftime('%b/%y').capitalize()}",
                "entradas": float(linha[0] or 0),
                "gastos": float(linha[1] or 0),
            }
        )

    contas_fixas = (
        db.query(models.ContaFixa)
        .filter(models.ContaFixa.usuario_id == usuario.id, models.ContaFixa.ativa == True)
        .all()
    )

    orcamentos = (
        db.query(models.Orcamento)
        .filter(models.Orcamento.usuario_id == usuario.id, models.Orcamento.mes == mes, models.Orcamento.ano == ano)
        .all()
    )

    dividas = (
        db.query(models.Divida)
        .filter(models.Divida.usuario_id == usuario.id, models.Divida.quitada == False)
        .all()
    )

    metas = db.query(models.Meta).filter(models.Meta.usuario_id == usuario.id).all()

    return {
        "usuario_nome": usuario.nome,
        "mes": mes,
        "ano": ano,
        "mes_nome": primeiro_dia.strftime("%B de %Y").capitalize(),
        "gerado_em": date.today().strftime("%d/%m/%Y"),
        "entradas": entradas,
        "gastos": gastos,
        "saldo": saldo,
        "categorias": categorias,
        "evolucao": evolucao,
        "transacoes": transacoes,
        "contas_fixas": contas_fixas,
        "orcamentos": orcamentos,
        "dividas": dividas,
        "metas": metas,
    }


# ============================================================
# 2) GRÁFICOS (matplotlib, com o glow neon)
# ============================================================
def _fig_para_base64(fig) -> str:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=200, bbox_inches="tight", transparent=True)
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")


def gerar_grafico_categorias(categorias: list) -> str:
    if not categorias:
        return ""

    valores = [c["valor"] for c in categorias]
    cores = [c["cor"] for c in categorias]
    labels = [f'{c["nome"]} ({c["pct"]:.0f}%)' for c in categorias]

    fig, ax = plt.subplots(figsize=(4.2, 4.2), facecolor="none")
    wedges, _ = ax.pie(
        valores,
        colors=cores,
        startangle=90,
        wedgeprops={"width": 0.42, "edgecolor": CORES["bg_card"], "linewidth": 3},
    )
    # leve "glow" duplicando o anel com alpha baixo por fora
    for w, cor in zip(wedges, cores):
        glow = mpatches.Wedge(
            w.center, w.r + 0.03, w.theta1, w.theta2,
            width=0.02, facecolor=cor, alpha=0.35, edgecolor="none",
        )
        ax.add_patch(glow)

    legenda = ax.legend(
        wedges,
        labels,
        loc="center left",
        bbox_to_anchor=(1.02, 0.5),
        frameon=False,
        fontsize=10,
    )
    for texto in legenda.get_texts():
        texto.set_color(CORES["texto"])
    ax.set_aspect("equal")
    return _fig_para_base64(fig)


def gerar_grafico_evolucao(evolucao: list) -> str:
    labels = [e["label"] for e in evolucao]
    entradas = [e["entradas"] for e in evolucao]
    gastos = [e["gastos"] for e in evolucao]

    x = range(len(labels))
    largura = 0.36

    fig, ax = plt.subplots(figsize=(9, 3.4), facecolor="none")
    ax.set_facecolor("none")

    b1 = ax.bar(
        [i - largura / 2 for i in x], entradas, largura,
        label="Entradas", color=CORES["neon_verde"],
    )
    b2 = ax.bar(
        [i + largura / 2 for i in x], gastos, largura,
        label="Gastos", color=CORES["neon_rosa"],
    )
    for bars, cor in ((b1, CORES["neon_verde"]), (b2, CORES["neon_rosa"])):
        for bar in bars:
            bar.set_path_effects(
                [patheffects.withStroke(linewidth=4, foreground=cor, alpha=0.25)]
            )

    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, color=CORES["texto_fraco"], fontsize=9)
    ax.tick_params(axis="y", colors=CORES["texto_fraco"], labelsize=9)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.grid(axis="y", color=CORES["borda"], linewidth=0.6, alpha=0.5)
    legenda = ax.legend(
        frameon=False, loc="upper left",
        bbox_to_anchor=(0, 1.15), ncol=2, fontsize=9,
    )
    for texto in legenda.get_texts():
        texto.set_color(CORES["texto"])
    fig.tight_layout()
    return _fig_para_base64(fig)


# ============================================================
# 3) TEMPLATE HTML (neon) + RENDERIZAÇÃO DO PDF
# ============================================================
TEMPLATE_HTML = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
<meta charset="utf-8">
<style>
    @page {
        size: A4;
        margin: 20mm 14mm 18mm 14mm;
        background-color: {{ cores.bg }};
        @bottom-center {
            content: "{{ nome_app }} · Relatório gerado em {{ dados.gerado_em }} · página " counter(page) " de " counter(pages);
            font-size: 8px;
            color: {{ cores.texto_fraco }};
        }
    }
    * { box-sizing: border-box; }
    html {
        background: {{ cores.bg }};
        min-height: 100%;
    }
    body {
        margin: 0;
        background: {{ cores.bg }};
        color: {{ cores.texto }};
        font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
        font-size: 11px;
        min-height: 100%;
    }

    .topo {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        border-bottom: 1px solid {{ cores.borda }};
        padding-bottom: 12px;
        margin-bottom: 18px;
    }
    .marca {
        font-size: 15px;
        font-weight: 800;
        letter-spacing: 1px;
        color: {{ cores.neon_azul }};
        text-shadow: 0 0 6px {{ cores.neon_azul }}, 0 0 14px {{ cores.neon_azul }}55;
    }
    .marca span { color: {{ cores.neon_rosa }}; text-shadow: 0 0 6px {{ cores.neon_rosa }}; }
    .titulo-bloco h1 {
        margin: 2px 0 2px 0;
        font-size: 24px;
        background: linear-gradient(90deg, {{ cores.neon_azul }}, {{ cores.neon_roxo }});
        -webkit-background-clip: text;
        color: transparent;
    }
    .titulo-bloco .subtitulo {
        color: {{ cores.texto_fraco }};
        font-size: 12px;
    }
    .gerado-em {
        text-align: right;
        font-size: 9px;
        color: {{ cores.texto_fraco }};
        font-style: italic;
    }

    .cards {
        display: flex;
        gap: 10px;
        margin-bottom: 22px;
    }
    .card {
        flex: 1;
        background: {{ cores.bg_card }};
        border: 1px solid {{ cores.borda }};
        border-radius: 10px;
        padding: 12px 14px;
        break-inside: avoid;
    }
    .card .rotulo { color: {{ cores.texto_fraco }}; font-size: 9px; text-transform: uppercase; letter-spacing: .5px; }
    .card .valor { font-size: 17px; font-weight: 700; margin-top: 4px; }
    .card.entradas .valor { color: {{ cores.neon_verde }}; text-shadow: 0 0 8px {{ cores.neon_verde }}66; }
    .card.gastos .valor { color: {{ cores.neon_rosa }}; text-shadow: 0 0 8px {{ cores.neon_rosa }}66; }
    .card.saldo .valor { color: {{ cores.neon_azul }}; text-shadow: 0 0 8px {{ cores.neon_azul }}66; }

    h2.secao {
        font-size: 13px;
        color: {{ cores.neon_azul }};
        border-left: 3px solid {{ cores.neon_azul }};
        padding-left: 8px;
        margin: 22px 0 10px 0;
        text-shadow: 0 0 6px {{ cores.neon_azul }}55;
        break-after: avoid;
    }

    table {
        width: 100%;
        border-collapse: collapse;
        background: {{ cores.bg_card }};
        border-radius: 8px;
        overflow: hidden;
        margin-bottom: 4px;
    }
    thead { display: table-header-group; }
    tr { break-inside: avoid; }
    thead tr { background: {{ cores.bg_card_alt }}; }
    th {
        text-align: left;
        padding: 7px 10px;
        font-size: 9px;
        text-transform: uppercase;
        letter-spacing: .4px;
        color: {{ cores.neon_azul }};
        border-bottom: 1px solid {{ cores.borda }};
    }
    td {
        padding: 7px 10px;
        border-bottom: 1px solid {{ cores.borda }};
        color: {{ cores.texto }};
    }
    tr:nth-child(even) td { background: {{ cores.bg_card_alt }}33; }
    .valor-pos { color: {{ cores.neon_verde }}; font-weight: 600; }
    .valor-neg { color: {{ cores.neon_rosa }}; font-weight: 600; }
    .status-paga { color: {{ cores.neon_verde }}; font-weight: 600; }
    .status-pendente { color: {{ cores.neon_amarelo }}; font-weight: 600; }

    .grafico-categorias { display: flex; align-items: center; gap: 8px; margin-bottom: 14px; }
    .grafico-categorias img { width: 230px; }

    .barra-progresso {
        width: 100%;
        height: 8px;
        border-radius: 4px;
        background: {{ cores.bg_card_alt }};
        overflow: hidden;
    }
    .barra-progresso .fill {
        height: 100%;
        background: linear-gradient(90deg, {{ cores.neon_azul }}, {{ cores.neon_roxo }});
    }

    .vazio { color: {{ cores.texto_fraco }}; font-style: italic; font-size: 10px; padding: 6px 0 16px 0; }
</style>
</head>
<body>

    <div class="topo">
        <div class="titulo-bloco">
            <h1>Relatório Geral</h1>
            <div class="subtitulo">{{ dados.mes_nome }} · {{ dados.usuario_nome }}</div>
        </div>
        <div>
            <div class="marca">Finan<span>Dog</span></div>
            <div class="gerado-em">Gerado em {{ dados.gerado_em }}</div>
        </div>
    </div>

    <div class="cards">
        <div class="card entradas">
            <div class="rotulo">Entradas do mês</div>
            <div class="valor">R$ {{ dados.entradas|moeda }}</div>
        </div>
        <div class="card gastos">
            <div class="rotulo">Gastos do mês</div>
            <div class="valor">R$ {{ dados.gastos|moeda }}</div>
        </div>
        <div class="card saldo">
            <div class="rotulo">Saldo do mês</div>
            <div class="valor">R$ {{ dados.saldo|moeda }}</div>
        </div>
    </div>

    <h2 class="secao">Gastos por categoria</h2>
    {% if dados.categorias %}
    <div class="grafico-categorias">
        <img src="data:image/png;base64,{{ grafico_categorias }}">
    </div>
    <table>
        <thead><tr><th>Categoria</th><th>Valor</th><th>% do total</th></tr></thead>
        <tbody>
        {% for c in dados.categorias %}
            <tr><td>{{ c.nome }}</td><td>R$ {{ c.valor|moeda }}</td><td>{{ "%.1f"|format(c.pct) }}%</td></tr>
        {% endfor %}
        </tbody>
    </table>
    {% else %}
        <div class="vazio">Nenhum gasto registrado no período.</div>
    {% endif %}

    <h2 class="secao">Evolução — entradas x gastos (6 meses)</h2>
    <img src="data:image/png;base64,{{ grafico_evolucao }}" style="width: 100%;">

    <h2 class="secao">Transações do mês</h2>
    {% if dados.transacoes %}
    <table>
        <thead><tr><th>Data</th><th>Descrição</th><th>Categoria</th><th>Conta</th><th>Valor</th></tr></thead>
        <tbody>
        {% for t in dados.transacoes %}
            <tr>
                <td>{{ t.data.strftime("%d/%m/%Y") }}</td>
                <td>{{ t.descricao }}</td>
                <td>{{ t.categoria.nome }}</td>
                <td>{{ t.conta.nome }}</td>
                <td class="{{ 'valor-pos' if t.tipo.value == 'entrada' else 'valor-neg' }}">
                    {{ '+' if t.tipo.value == 'entrada' else '-' }} R$ {{ t.valor|moeda }}
                </td>
            </tr>
        {% endfor %}
        </tbody>
    </table>
    {% else %}
        <div class="vazio">Nenhuma transação no período.</div>
    {% endif %}

    <h2 class="secao">Contas fixas</h2>
    {% if dados.contas_fixas %}
    <table>
        <thead><tr><th>Conta</th><th>Vencimento (dia)</th><th>Valor</th></tr></thead>
        <tbody>
        {% for cf in dados.contas_fixas %}
            <tr><td>{{ cf.nome }}</td><td>{{ cf.dia_vencimento }}</td><td>R$ {{ cf.valor|moeda }}</td></tr>
        {% endfor %}
        </tbody>
    </table>
    {% else %}
        <div class="vazio">Nenhuma conta fixa cadastrada.</div>
    {% endif %}

    <h2 class="secao">Orçamentos por categoria</h2>
    {% if dados.orcamentos %}
    <table>
        <thead><tr><th>Categoria</th><th>Limite</th><th>Gasto</th><th>% usado</th></tr></thead>
        <tbody>
        {% for o in dados.orcamentos %}
            <tr>
                <td>{{ o.categoria.nome }}</td>
                <td>R$ {{ o.limite|moeda }}</td>
                <td>R$ {{ o.gasto_atual|moeda if o.gasto_atual is defined else "-" }}</td>
                <td>{{ "%.0f"|format((o.gasto_atual / o.limite * 100) if o.limite else 0) }}%</td>
            </tr>
        {% endfor %}
        </tbody>
    </table>
    {% else %}
        <div class="vazio">Nenhum orçamento definido para este mês.</div>
    {% endif %}

    <h2 class="secao">Dívidas em aberto</h2>
    {% if dados.dividas %}
    <table>
        <thead><tr><th>Credor</th><th>Parcela mensal</th><th>Restante</th><th>Parcelas</th></tr></thead>
        <tbody>
        {% for d in dados.dividas %}
            <tr>
                <td>{{ d.nome }}</td>
                <td>R$ {{ d.valor_parcela|moeda }}</td>
                <td>R$ {{ (d.valor_parcela * (d.numero_parcelas - d.parcelas_pagas))|moeda }}</td>
                <td>{{ d.parcelas_pagas }}/{{ d.numero_parcelas }}</td>
            </tr>
        {% endfor %}
        </tbody>
    </table>
    {% else %}
        <div class="vazio">Nenhuma dívida em aberto.</div>
    {% endif %}

    <h2 class="secao">Metas de economia</h2>
    {% if dados.metas %}
    <table>
        <thead><tr><th>Meta</th><th>Atual</th><th>Alvo</th><th>Progresso</th></tr></thead>
        <tbody>
        {% for m in dados.metas %}
            {% set pct = (m.valor_atual / m.valor_alvo * 100) if m.valor_alvo else 0 %}
            <tr>
                <td>{{ m.nome }}</td>
                <td>R$ {{ m.valor_atual|moeda }}</td>
                <td>R$ {{ m.valor_alvo|moeda }}</td>
                <td style="width: 160px;">
                    <div class="barra-progresso"><div class="fill" style="width: {{ pct if pct <= 100 else 100 }}%;"></div></div>
                    <div style="font-size:8px; color:{{ cores.texto_fraco }}; margin-top:2px;">{{ "%.0f"|format(pct) }}%</div>
                </td>
            </tr>
        {% endfor %}
        </tbody>
    </table>
    {% else %}
        <div class="vazio">Nenhuma meta cadastrada.</div>
    {% endif %}

</body>
</html>
"""


def formatar_moeda(valor) -> str:
    """1234.5 -> '1.234,50' (padrão brasileiro, com separador de milhar)."""
    valor = float(valor or 0)
    texto = f"{valor:,.2f}"  # ex: '1,234.50'
    texto = texto.replace(",", "X").replace(".", ",").replace("X", ".")
    return texto


_env = Environment()
_env.filters["moeda"] = formatar_moeda
_TEMPLATE = _env.from_string(TEMPLATE_HTML)


def gerar_pdf_relatorio(dados: dict) -> bytes:
    grafico_categorias = gerar_grafico_categorias(dados["categorias"])
    grafico_evolucao = gerar_grafico_evolucao(dados["evolucao"])

    html_renderizado = _TEMPLATE.render(
        dados=dados,
        cores=CORES,
        nome_app=NOME_APP,
        grafico_categorias=grafico_categorias,
        grafico_evolucao=grafico_evolucao,
    )

    return HTML(string=html_renderizado).write_pdf()
