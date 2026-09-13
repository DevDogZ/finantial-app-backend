def test_criar_categoria(client):
    resposta = client.post("/categorias", json={"nome": "Alimentacao", "cor": "#ff0000"})

    assert resposta.status_code == 200
    dados = resposta.json()
    assert dados["nome"] == "Alimentacao"
    assert "id" in dados


def test_nao_permite_categoria_duplicada(client):
    client.post("/categorias", json={"nome": "Lazer"})
    resposta = client.post("/categorias", json={"nome": "Lazer"})

    assert resposta.status_code == 400


def test_listar_categorias_vazio(client):
    resposta = client.get("/categorias")

    assert resposta.status_code == 200
    assert resposta.json() == []