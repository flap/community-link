from diagrams import Diagram, Cluster, Edge
from diagrams.programming.flowchart import (
    Action, Decision, StartEnd, Document, InputOutput
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
    "Divulgacao de Comunidade - As-Is (Atual)",
    filename="docs/02-fluxograma-processos/as-is-divulgacao",
    outformat="png",
    direction="TB",
    show=False,
    graph_attr=graph_attr,
):
    inicio = StartEnd("Comunidade quer\ndivulgar conteudo")

    with Cluster("Processo Manual e Fragmentado", graph_attr={"bgcolor": "#fff0f0"}):
        decide = Decision("Onde publicar?")
        insta = Action("Post no Instagram")
        linkedin = Action("Post no LinkedIn")
        site = Document("Atualiza site\nproprio (manual)")
        linktree = Action("Edita agregador\ngenerico (1 pessoa)")

    with Cluster("Experiencia do Publico", graph_attr={"bgcolor": "#fff0f0"}):
        publico = InputOutput("Publico procura\ncanais dispersos")
        perda = Action("Nao encontra tudo /\nlinks desatualizados")

    fim = StartEnd("Baixo engajamento\ne perda de audiencia")

    inicio >> decide
    decide >> Edge(label="rede social") >> insta
    decide >> Edge(label="rede social") >> linkedin
    decide >> Edge(label="site") >> site
    decide >> Edge(label="bio/link") >> linktree

    insta >> publico
    linkedin >> publico
    site >> publico
    linktree >> publico

    publico >> perda >> fim
