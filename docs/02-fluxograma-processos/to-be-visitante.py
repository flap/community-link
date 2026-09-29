from diagrams import Diagram, Cluster, Edge
from diagrams.programming.flowchart import (
    Action, Decision, StartEnd, InputOutput, Database, Document
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
    "Jornada do Visitante na Pagina Publica - To-Be",
    filename="docs/02-fluxograma-processos/to-be-visitante",
    outformat="png",
    direction="TB",
    show=False,
    graph_attr=graph_attr,
):
    inicio = StartEnd("Visitante acessa\nawscommunity.com.br/slug")

    with Cluster("Entrega de Conteudo (AWS)", graph_attr={"bgcolor": "#eef5ff"}):
        cf = Action("CloudFront (CDN)")
        apigw = Action("API Gateway")
        lambda_fn = Action("Lambda / FastAPI")
        db = Database("DynamoDB\n(comunidade + links)")

    with Cluster("Experiencia na Pagina", graph_attr={"bgcolor": "#eef5ff"}):
        render = InputOutput("Renderiza pagina\ncom tema e secoes")
        navega = Action("Navega pelas secoes")
        tipo = Decision("Tipo de link?")
        embed = Document("Ve embed\n(video, evento)")
        externo = Action("Abre link externo\n(rede social, site)")

    fim = StartEnd("Engajamento /\nacesso ao conteudo")

    inicio >> cf >> apigw >> lambda_fn >> db
    db >> render >> navega >> tipo
    tipo >> Edge(label="embeddavel") >> embed >> fim
    tipo >> Edge(label="externo") >> externo >> fim
