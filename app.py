import requests
from bs4 import BeautifulSoup
import pandas as pd
from flask import Flask, request
from flask import render_template

app = Flask(__name__)


@app.route("/")
def home():
    dadosAtualizadoAte = consultarDiaAtualizado()
    return render_template("home.html", dia=dadosAtualizadoAte)


@app.route("/empenho", methods=['POST'])
def empenho():
    empenho_consultar = request.form['empenhoConsultar']
    empenhoUg = request.form['ug']
    empenhoOrgao = request.form['orgao']
    dadosEmpenho = consultarEmpenho(empenhoUg, empenhoOrgao, empenho_consultar)
    return f"""
    <tr>
        <td>{dadosEmpenho["empenho"]}</td>
        <td>{dadosEmpenho["favorecido"]}</td>
        <td>{dadosEmpenho["cnpj"]}</td>
        <td>{dadosEmpenho["valor"]}</td>
    </tr><ARRAY>
    {dadosEmpenho["listaItens"]}<ARRAY>
    {dadosEmpenho["pagamentos"]}
    """


def consultarDiaAtualizado():
    url = "https://www.portaltransparencia.gov.br/despesas/consulta"
    r = requests.get(url)
    if r.status_code == 200:
        try:
            soup = BeautifulSoup(r.text, "html.parser")
            dia = soup.select_one("#datas > a").text.strip()
            return {"dia": dia}
        except Exception as erro:
            return {"erro": erro}
    else:
        return {"erro": r.status_code}


def consultarEmpenho(ug, orgao, empenho):
    url = f'https://www.portaldatransparencia.gov.br/despesas/empenho/{ug}{orgao}{empenho}'
    url_pagamentos = f'https://www.portaltransparencia.gov.br/despesas/documento/documentos-relacionados/resultado?paginacaoSimples=true&tamanhoPagina=15&offset=0&direcaoOrdenacao=asc&colunaOrdenacao=fase&colunasSelecionadas=data%2Cfase%2CdocumentoResumido%2Cespecie&fase=Empenho&codigo={ug}{orgao}{empenho}&_=1656178891541'

    r = requests.get(url)
    if r.status_code == 200:
        try:
            soup = BeautifulSoup(r.text, "html.parser")
            empenhoRetornado = soup.select_one("body > main > div:nth-child(3) > section.dados-tabelados > div:nth-child(1) > div:nth-child(1) > span").text.strip()
            valorEmpenho = soup.select_one("body > main > div:nth-child(3) > section.dados-tabelados > div:nth-child(3) > div.col-xs-12.col-sm-6 > span").text.strip()
            favorecidoEmpenho = soup.select_one("#collapse-1 > div > div > div.col-xs-12.col-sm-9 > span").text.strip()
            cnpjEmpenho = soup.select_one("#collapse-1 > div > div > div.col-xs-12.col-sm-3 > span > a").text.strip()
            listaItensEmpenho = pd.read_csv(f"https://www.portaltransparencia.gov.br/despesas/documento/empenho/detalhamento/baixar?direcaoOrdenacao=asc&codigo={ug}{orgao}{empenho}&totalDeRegistrosDaTabela=15",sep=";")
            documentosRelacionados = get_pagamentos(url_pagamentos)
            cnpjEmpenho = soup.select_one("#collapse-1 > div > div > div.col-xs-12.col-sm-3 > span > a").text.strip()
            return {
                "empenho": empenhoRetornado,
                "valor": valorEmpenho,
                "favorecido": favorecidoEmpenho,
                "cnpj": cnpjEmpenho,
                "listaItens": listaItensEmpenho.to_html(columns=['Item', 'Código subelemento', 'Subelemento', 'Valor atual'],justify='left', index=False),
                "pagamentos": documentosRelacionados
            }
        except Exception as erro:
            return {"erro": erro}
    else:
        return {"erro": r.status_code}

def consultarNotaSistema(ug, orgao, notaSistema):
    url = f'https://www.portaltransparencia.gov.br/despesas/liquidacao/{ug}{orgao}{notaSistema}'
    r = requests.get(url)
    if r.status_code == 200:
        try:
            soup = BeautifulSoup(r.text, "html.parser")
            valorNotaSistema = 0
        except Exception as erro:
            return {"erro": erro}
    else:
        return {"erro": r.status_code}

def get_pagamentos(url):
    import json

    pagamentos = []
    r = requests.get(url)
    if r.status_code == 200:
        try:
            documentosRelacionados = json.loads(r.text)
            if len(documentosRelacionados["data"]) > 0:
                documentos = documentosRelacionados["data"]
                for documento in documentos:
                    if documento["fase"] == "Pagamento":
                        pagamentos.append(
                            {
                                "documento": documento["documentoResumido"],
                                "data": documento["data"],
                                "favorecido": documento["favorecido"],
                                "valor": documento["valor"]
                            }
                        )
        except Exception as erro:
            return {"erro": erro}
    else:
        return {"erro": r.status_code}

    return pagamentos
