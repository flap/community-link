#!/usr/bin/env python3
"""Diagrama de arquitetura de DEPLOY do projeto *pastel* (Community Link).

Gera `deploy-architecture.png` com o pacote `diagrams` (mingrammer/diagrams),
usando ícones oficiais AWS. Requer Graphviz (`dot`) no PATH.

Topologia (AWS, us-east-1), inferida do código do projeto:

  Cliente (navegador)
    -> CloudFront (1 distribuição, OAC para os buckets S3, 2 CloudFront Functions:
         F1 = SPA fallback para /index.html; F2 = strip do prefixo /media)
         com 3 origens:
           1) S3 SPA      (frontend/dist, privado via OAC)   -> default behavior
           2) S3 Media    (uploads em links/*, privado OAC)  -> /media/*
           3) API Gateway HTTP API ($default)                -> /api/*
    -> Lambda (FastAPI via Mangum, handler app.lambda_handler.handler, python3.12)
         - lê config de SSM Parameter Store /community-link/beta/backend/* no cold start
         - persiste em DynamoDB single-table `community-link` (PK/SK, PAY_PER_REQUEST)
         - grava mídia no bucket S3 Media (prefixo links/*)

  Auth: Supabase (externo) valida JWT do SPA; segredos em SSM/Secrets Manager.

Execução:
    python deploy-architecture.py        # gera ./deploy-architecture.png
"""

from diagrams import Cluster, Diagram, Edge
from diagrams.aws.compute import Lambda
from diagrams.aws.database import Dynamodb
from diagrams.aws.management import SystemsManagerParameterStore
from diagrams.aws.network import CloudFront
from diagrams.aws.network import APIGateway
from diagrams.aws.security import SecretsManager
from diagrams.aws.storage import S3
from diagrams.onprem.client import Users
from diagrams.saas.identity import Auth0  # proxy visual para "Supabase (IdP externo)"

GRAPH_ATTR = {
    "fontsize": "16",
    "bgcolor": "white",
    "pad": "0.6",
    "nodesep": "0.8",
    "ranksep": "1.1",
    "dpi": "220",  # >= 200 para qualidade de impressão
    "labelloc": "t",
}

with Diagram(
    "Pastel / Community Link — Deploy AWS (us-east-1)",
    filename="deploy-architecture",
    outformat="png",
    direction="LR",
    show=False,
    graph_attr=GRAPH_ATTR,
):
    visitor = Users("Visitante / Admin\n(navegador)")

    with Cluster("Auth externa (SaaS)"):
        supabase = Auth0("Supabase Auth\n(JWT / JWKS)")

    with Cluster("AWS — conta beta · us-east-1"):
        with Cluster("Borda (CDN)"):
            cdn = CloudFront(
                "CloudFront\n1 distribuição · OAC\n2 CloudFront Functions\n(SPA fallback · strip /media)"
            )

        with Cluster("Storage privado (S3 + OAC)"):
            spa_bucket = S3("S3 SPA\n(frontend/dist)")
            media_bucket = S3("S3 Media\n(links/*)")

        with Cluster("API serverless"):
            api = APIGateway("API Gateway\nHTTP API ($default)")
            fn = Lambda("Lambda\nFastAPI + Mangum\npython3.12")

        with Cluster("Dados"):
            table = Dynamodb("DynamoDB\n`community-link`\nPK/SK · PAY_PER_REQUEST")

        with Cluster("Configuração & Segredos"):
            ssm = SystemsManagerParameterStore(
                "SSM Parameter Store\n/community-link/beta/*"
            )
            secrets = SecretsManager("Segredos\n(Supabase keys)")

    # --- Fluxo do cliente -> borda ---
    visitor >> Edge(label="HTTPS") >> cdn
    visitor >> Edge(label="login (JWT)", style="dashed", color="darkgreen") >> supabase

    # --- CloudFront -> 3 origens ---
    cdn >> Edge(label="default → SPA") >> spa_bucket
    cdn >> Edge(label="/media/* (OAC)") >> media_bucket
    cdn >> Edge(label="/api/* → HTTP API") >> api

    # --- API -> compute -> dados/mídia/config ---
    api >> Edge(label="$default → handler") >> fn
    fn >> Edge(label="get/put items") >> table
    fn >> Edge(label="put_object links/*") >> media_bucket
    fn >> Edge(label="cold start: get_parameters_by_path", style="dashed") >> ssm
    fn >> Edge(label="valida JWT (JWKS)", style="dashed", color="darkgreen") >> supabase

    # --- Segredos consumidos via config ---
    ssm >> Edge(label="refs", style="dotted", color="gray") >> secrets
