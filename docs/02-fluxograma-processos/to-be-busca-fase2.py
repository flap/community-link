from diagrams import Diagram, Cluster, Edge
from diagrams.programming.flowchart import (
    Action, Decision, StartEnd, InputOutput, Database
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
    "Busca e Filtros - To-Be (Fase 2)",
    filename="docs/02-fluxograma-processos/to-be-busca-fase2",
    outformat="png",
    direction="LR",
    show=False,
    graph_attr=graph_attr,
):
    inicio = StartEnd("Visitante quer\nencontrar conteudo")

    with Cluster("Interface de Descoberta", graph_attr={"bgcolor": "#eef5ff"}):
        entrada = InputOutput("Digita termo /\naplica filtros")
        filtros = Decision("Filtro por?")
        f_data = Action("Data")
        f_tipo = Action("Tipo de conteudo")
        f_autor = Action("Autor / comunidade")

    with Cluster("Backend de Busca (AWS)", graph_attr={"bgcolor": "#eef5ff"}):
        api = Action("API de busca\n(Lambda / FastAPI)")
        idx = Database("Indice de busca\n(DynamoDB GSI)")

    resultado = InputOutput("Lista de links\nfiltrada e ordenada")
    fim = StartEnd("Visitante acessa\nconteudo relevante")

    inicio >> entrada >> filtros
    filtros >> Edge(label="data") >> f_data >> api
    filtros >> Edge(label="tipo") >> f_tipo >> api
    filtros >> Edge(label="autor") >> f_autor >> api
    api >> idx >> resultado >> fim
