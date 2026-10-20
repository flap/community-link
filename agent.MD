# agent-tofu — Agente de Infra as Code (Terraform / OpenTofu)

Agente Kiro especializado em **Infraestrutura como Código**. Olha para um projeto,
desenha o **diagrama de arquitetura do deploy** em Python (pacote `diagrams`) e gera a
**infra em Terraform/OpenTofu** seguindo a skill
[`antonbabenko/terraform-skill`](https://github.com/antonbabenko/terraform-skill) —
módulos, composição por ambiente, state remoto, testes, segurança e CI/CD.

Este arquivo permite **replicar o agente** em outros projetos ou para outros
desenvolvedores. Copie-o para o repositório e siga a instalação abaixo.

---

## O que o agente faz

Dado um projeto para implantar:

1. **Analisa** o projeto (README, configs de build, Dockerfiles, compose, manifests,
   `.env.example` — nunca segredos reais) e infere a topologia de deploy: compute,
   storage, banco, rede, borda/CDN, identidade, filas/eventos, observabilidade.
   Captura o contexto de execução: runtime (`terraform`|`tofu`) + versão, provider(s)
   de nuvem, backend de state, caminho de execução (local/CI), criticidade do ambiente.
2. **Desenha o diagrama** do deploy em Python com o pacote `diagrams`
   (mingrammer/diagrams), com ícones oficiais do provider, `Cluster()` para
   VPC/subnets/AZs/regiões, `Edge(label=...)` para fluxo de dados, `dpi>=200`,
   executa o script e gera o **PNG**.
3. **Gera Terraform/OpenTofu** seguindo a skill: `environments/` separado de
   `modules/`, hierarquia resource → módulo → composição, arquivos padrão
   (`main.tf`, `variables.tf`, `outputs.tf`, `versions.tf`, `tests/*.tftest.hcl`),
   contratos de variável/output, state remoto com encrypt+versioning+locking,
   segredos fora do state (secret manager ou `write_only`/`*_wo` em 1.11+),
   version pinning e `.terraform.lock.hcl` commitado.
4. **Valida**: `terraform fmt`/`validate`/`tflint`, testes nativos (1.6+) ou Terratest,
   `trivy config .` e `checkov -d .`; e emite o **Response Contract** da skill.

### Regras de segurança (não-negociáveis)

- Nunca roda `terraform destroy` sem antes `terraform plan -destroy` + mostrar todos os
  recursos (incl. dependentes implícitos via locals/`for_each`) e confirmação explícita.
  Nunca usa `-auto-approve` em destroy.
- Nunca recomenda `apply` direto em produção sem artefato de plan revisado e aprovação.
- Nunca escreve segredos reais em arquivos — usa placeholders.

---

## Padrões permanentes (onde o agente guarda sua configuração)

| Item | Caminho | Papel |
|------|---------|------|
| **Agente** | `~/.kiro/agents/agent-tofu.json` | Definição do agente (prompt, tools, permissões, MCP) |
| **Steering** | `~/.kiro/steering/agent-tofu-iac.md` | Fluxo de trabalho e padrões de IaC (inclusão `manual`, ativável com `#agent-tofu-iac`) |
| **Skill** | `~/.kiro/skills/terraform-skill/` | Fonte de verdade de Terraform/OpenTofu (SKILL.md + `references/*.md`) |

A skill é clonada do repositório oficial e **atualizável com `git pull`** — a
orientação técnica não é duplicada, fica na skill.

---

## Instalação (replicar em outra máquina/projeto)

Pré-requisitos no PATH: `git`, `python3`, Graphviz (`dot`), e `terraform` **ou**
`tofu`. Opcionais: `tflint`, `trivy`, `checkov`, `terraform-docs`, `docker` (para o
MCP read-only da HashiCorp).

```bash
# 1) Instalar a skill oficial (Kiro auto-descobre em ~/.kiro/skills/)
git clone https://github.com/antonbabenko/terraform-skill.git \
  ~/.kiro/skills/terraform-skill
# atualizar depois: cd ~/.kiro/skills/terraform-skill && git pull

# 2) Instalar o pacote de diagramas
pip install diagrams     # requer Graphviz 'dot' no sistema

# 3) Copiar os dois arquivos de configuração permanente deste repositório:
#    - agent-tofu.json  -> ~/.kiro/agents/agent-tofu.json
#    - agent-tofu-iac.md -> ~/.kiro/steering/agent-tofu-iac.md
# (constam abaixo em "Arquivos de configuração", ou peça ao agente para recriá-los)
```

Reinicie a sessão Kiro para que o agente e a steering sejam descobertos.

### MCP opcional (HashiCorp terraform-mcp-server, read-only)

Já declarado em `agent-tofu.json`. Roda via Docker; valida schemas de
providers/recursos antes de escrever asserts de teste. O agente funciona sem ele.

```json
{
  "mcpServers": {
    "terraform-mcp-server": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "hashicorp/terraform-mcp-server:latest"],
      "disabled": false
    }
  }
}
```

---

## Como usar

Com o agente selecionado (`agent-tofu`):

- "Analise este projeto e gere o diagrama de deploy + a infra Terraform na AWS, região us-east-1."
- "Gere a infra em OpenTofu com state remoto S3 e locking nativo (use_lockfile)."
- "Dê o equivalente em Azure/GCP deste padrão de deploy."
- "Revise esta configuração Terraform seguindo as boas práticas."

O agente ativa a skill `terraform-skill` automaticamente em tarefas de Terraform/OpenTofu.

---

## Saídas no projeto

```
<projeto>/
├── generated-diagrams/        # .py (diagrams) + PNG do diagrama de deploy
├── infra/
│   ├── environments/{prod,staging,dev}/
│   ├── modules/{networking,compute,data}/
│   └── examples/{minimal,complete}/
└── agent.MD                   # este cartão de replicação
```

---

## Notas de ambiente

- A skill recomenda `use_lockfile` (Terraform 1.10+) e `write_only` (1.11+). Se o
  runtime local for inferior, o agente **degrada** e declara a alternativa
  (ex.: `dynamodb_table` para locking) no Response Contract.
- AWS, Azure e GCP são first-class; AWS é o default nos exemplos.

---

## Arquivos de configuração

As definições canônicas vivem em:
`~/.kiro/agents/agent-tofu.json` e `~/.kiro/steering/agent-tofu-iac.md`.
Para recriar em um novo ambiente, peça ao agente ("recrie suas configs permanentes")
ou copie esses dois arquivos de uma instalação existente.

---

## Teste end-to-end neste projeto (pastel)

Execução de referência do agente apontado para o próprio repositório `pastel`.

### Saídas geradas

```
generated-diagrams/
├── deploy-architecture.py     # script diagrams (AWS, us-east-1, dpi=220)
└── deploy-architecture.png    # PNG renderizado (5135x3920)
infra/
├── environments/{prod,staging}/   # composições (main/variables/outputs/versions/backend/tfvars/README)
├── modules/
│   ├── data/      # DynamoDB single-table (PK/SK, PAY_PER_REQUEST, sem GSI)
│   ├── storage/   # bucket S3 privado (OAC) — SPA e mídia
│   ├── compute/   # Lambda (FastAPI/Mangum, python3.12) + API Gateway HTTP API + IAM least-privilege
│   └── edge/      # CloudFront (3 origens, OAC, 2 CloudFront Functions)
├── examples/{minimal,complete}/
├── README.md
└── .gitignore
```

### Validação executada (sem deploy real)

- `terraform init -backend=false` — OK (prod, staging, examples/minimal, examples/complete)
- `terraform fmt -recursive -check` — OK (sem reformatação necessária)
- `terraform validate` — **Success** nas 4 raízes
- `.terraform.lock.hcl` commitado nas 4 raízes; `.terraform/` em `.gitignore`

### Notas de ambiente observadas neste teste

| Item | Estado | Ação do agente |
|------|--------|----------------|
| `terraform` | v1.5.7 (**< 1.10**) | Degradou state locking para `dynamodb_table` (sem `use_lockfile`/`write_only`); declarado no Response Contract e nos `backend.tf`. |
| `tofu` | ausente | Usou `terraform`. |
| Graphviz `dot` | presente (14.1.5) | PNG renderizado com sucesso. |
| `diagrams` (pip) | ausente; PEP 668 bloqueou install global | Instalou em venv temporário (`.venv-diagrams`, removido ao final). |
| `tflint` / `trivy` / `checkov` | ausentes | Validação limitada a `fmt`/`validate`; pendências registradas no Validation plan. |

### Ciclo de dependência resolvido

`storage` ↔ `edge` teria ciclo (edge precisa do domínio do bucket; policy do bucket
precisa do ARN da distribuição). Resolvido movendo a **policy OAC para a composição**
(`environments/*`), mantendo os módulos desacoplados.
