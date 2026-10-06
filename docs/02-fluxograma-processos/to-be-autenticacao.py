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
    "Autenticacao e Autorizacao (Supabase Auth) - To-Be (Fase 2)",
    filename="docs/02-fluxograma-processos/to-be-autenticacao",
    outformat="png",
    direction="TB",
    show=False,
    graph_attr=graph_attr,
):
    inicio = StartEnd("Admin acessa\n/admin")

    with Cluster("Tela de login propria (Vue)", graph_attr={"bgcolor": "#eef5ff"}):
        tela = InputOutput("Tela de login\n(tema AWS)")
        metodo = Decision("Metodo?")
        email = Action("E-mail + senha")
        social = Action("Google / GitHub /\noutros (OAuth PKCE)")

    with Cluster("Supabase Auth (gerenciado)", graph_attr={"bgcolor": "#f0f0f0"}):
        valida = Action("Valida credenciais /\nprovedor social")
        jwt = Document("Emite JWT\n(sub, email, exp)")

    with Cluster("Backend FastAPI (Lambda)", graph_attr={"bgcolor": "#eef5ff"}):
        verifica = Action("Valida JWT\n(JWKS em cache)")
        tokenok = Decision("Token\nvalido?")
        admin = Decision("E admin da\ncomunidade?")
        convite = Action("Efetiva convite\npendente (por e-mail)")
        db = Database("DynamoDB\nCOMMUNITY#slug / ADMIN#sub")

    ok = StartEnd("Operacao\nautorizada")
    e401 = StartEnd("401 Nao autenticado")
    e403 = StartEnd("403 Sem permissao")

    inicio >> tela >> metodo
    metodo >> Edge(label="e-mail") >> email >> valida
    metodo >> Edge(label="social") >> social >> valida
    valida >> jwt
    jwt >> Edge(label="Authorization: Bearer") >> verifica >> tokenok
    tokenok >> Edge(label="Nao", color="red") >> e401
    tokenok >> Edge(label="Sim", color="darkgreen") >> admin
    admin >> Edge(label="consulta") >> db
    admin >> Edge(label="Nao, mas ha convite") >> convite >> db
    admin >> Edge(label="Sim", color="darkgreen") >> ok
    admin >> Edge(label="Nao", color="red") >> e403
