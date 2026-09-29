from diagrams import Diagram, Cluster, Edge
from diagrams.programming.flowchart import (
    Action, Decision, StartEnd, Document, InputOutput, Preparation, Database
)

graph_attr = {
    "fontsize": "14",
    "bgcolor": "white",
    "pad": "0.5",
    "nodesep": "0.8",
    "ranksep": "1.0",
    "dpi": "200",
}

with Diagram(
    "Criacao e Edicao da Pagina - To-Be (Proposto)",
    filename="docs/02-fluxograma-processos/to-be-edicao-pagina",
    outformat="png",
    direction="TB",
    show=False,
    graph_attr=graph_attr,
):
    inicio = StartEnd("Admin acessa\narea administrativa")

    with Cluster("Autenticacao (MVP: credencial fixa)", graph_attr={"bgcolor": "#f0f0f0"}):
        login = Action("Informa credencial")
        valida = Decision("Credencial\nvalida?")

    with Cluster("Gestao da Comunidade (Community Link)", graph_attr={"bgcolor": "#eef5ff"}):
        existe = Decision("Comunidade\nja existe?")
        criar = Preparation("Cria comunidade\n(nome, slug, tema)")
        secoes = Action("Cria / edita secoes")
        addlink = Action("Adiciona link\n(tipo, emoji, foto)")
        embed = Action("Configura embed /\ndestaque")
        tema = Action("Escolhe tema\n(padroes disponiveis)")
        salvar = InputOutput("Salva alteracoes")

    with Cluster("Backend Serverless (AWS)", graph_attr={"bgcolor": "#eef5ff"}):
        api = Action("API FastAPI\n(Lambda)")
        db = Database("DynamoDB")
        s3 = Document("S3 (imagens)")

    publica = StartEnd("Pagina publica\natualizada")

    inicio >> login >> valida
    valida >> Edge(label="Nao", color="red") >> login
    valida >> Edge(label="Sim", color="darkgreen") >> existe
    existe >> Edge(label="Nao") >> criar >> secoes
    existe >> Edge(label="Sim") >> secoes
    secoes >> addlink >> embed >> tema >> salvar
    salvar >> api
    api >> db
    api >> s3
    api >> publica
