# kitoboy-mcp — Runbook

Operational guide: what this server is, what happens when it runs, how to launch
it against a local test stack, how to connect an agent, and how to wire it into a
real Kitoboy deployment.

---

## 1. What we built

A thin, **read-only** MCP server that wraps Kitoboy's READ API as 9 tools an LLM
agent can call. The agent analyses data (risk summaries, triage, trends, label
explanation, contact-leak audit) but **never mutates** anything — a volunteer
sets statuses manually in the Kitoboy UI.

```
 LLM agent (Claude Code / LangGraph / OpenAI Agents / ...)
        │  MCP over Streamable HTTP  (http://<host>:<port>/mcp)
        ▼
 kitoboy-mcp  ──HTTP──>  Kitoboy api:3052   (JWT, READ endpoints)
              ──HTTP──>  Kitoboy zoo:8000   (stateless ML classify)
```

The 9 tools (see README for the table): `kitoboy_search_person`,
`kitoboy_get_person`, `kitoboy_list_avatars`, `kitoboy_get_avatar`,
`kitoboy_list_attributes`, `kitoboy_list_statuses`, `zoo_classify_text`,
`zoo_classify_text_raw`, `zoo_list_services`.

## 2. What happens when the MCP server runs

1. It serves Streamable HTTP on `MCP_HOST:MCP_PORT` at path `/mcp`
   (default `0.0.0.0:9000`). In Docker the host port is `MCP_PUBLISH_PORT`.
2. On the **first** tool call it logs in to `KITOBOY_API_URL` with
   `KITOBOY_USER`/`KITOBOY_PASSWORD`, caches the JWT (12h TTL), and
   re-authenticates automatically on a 401.
3. `kitoboy_*` tools call `api:3052`; `zoo_*` tools call `zoo:8000`.
4. Responses are returned as structured JSON; the agent reasons over them.
5. If `MCP_AUTH_TOKEN` is set, the endpoint requires
   `Authorization: Bearer <token>`; otherwise it is open (local/in-network use).

Clients are process-lifetime singletons (not tied to a per-request lifespan).

---

## 3. Quick start A — local TEST stack (db + api, no ML models)

This is what was used to validate the server. It runs the real Kitoboy `api`
and Postgres, seeded with synthetic data. `zoo_*` tools are NOT functional here
(no Triton models) — only `kitoboy_*` tools are exercised.

Paths used below: MCP repo at `~/Downloads/kitoboy-mcp`, Kitoboy clone at
`~/Downloads/kitoboy`.

### 3.1 Docker engine (macOS, headless via colima)

```bash
brew install colima docker docker-compose
colima start --cpu 4 --memory 6 --disk 30
docker version            # client + daemon (context: colima)
```

> Compose: the standalone `docker-compose` binary is used below. `docker compose`
> (plugin) also works if registered in `~/.docker/config.json`.

### 3.2 Bring up Kitoboy db + api

```bash
git clone --depth 1 https://github.com/psytechlab/kitoboy.git ~/Downloads/kitoboy
```

Create `~/Downloads/kitoboy/.env` (development, no `COMPOSE_FILE` so the heavy
models compose is not selected):

```dotenv
NODE_ENV=development
VITE_APP_HOST=localhost
DB_NAME=api
DB_HOST=db
DB_USER=postgres
DB_PASSWORD=secret007
PG_USER=admin@example.com
PG_PASSWORD=admin
UI_USER=user
UI_PASSWORD=user
AUTH_KEY=secret_key
```

The dev image does not install deps (they are bind-mounted), so install them
once inside a Linux container:

```bash
docker run --rm -v ~/Downloads/kitoboy/api:/opt/api -w /opt/api \
  node:20.15.0-alpine npm install --ignore-scripts
```

Start only db + api:

```bash
docker-compose --project-directory ~/Downloads/kitoboy \
  -f ~/Downloads/kitoboy/docker-compose.development.yml up -d db api
```

The api creates tables and seeds 3 statuses + the `user` account ~10s after
start. Confirm:

```bash
docker logs kitoboy-api-1 | grep "Server is running"
```

This creates the docker network **`kitoboy_postgres`** (project name = clone
dir). `api` is reachable in-network as `api:3052`.

### 3.3 Seed synthetic test data

```bash
docker exec -i kitoboy-db-1 psql -U postgres -d api -v ON_ERROR_STOP=1 \
  < ~/Downloads/kitoboy-mcp/scripts/seed.sql
```

### 3.4 Build & run the MCP container

```bash
cd ~/Downloads/kitoboy-mcp
cp .env.example .env          # set MCP_PUBLISH_PORT=9100 if host 9000 is taken
docker-compose up -d --build  # joins network kitoboy_postgres, publishes :9100->9000
docker logs kitoboy-mcp       # uvicorn running on 0.0.0.0:9000
```

`docker-compose.yml` attaches to the external network `kitoboy_postgres`; if your
network name differs, check `docker network ls` and update `networks.kitoboy.name`.

The endpoint is now at **`http://localhost:9100/mcp`**.

---

## 4. Connect an agent

### 4.1 Claude Code

Add to the `mcpServers` config:

```json
{ "mcpServers": { "kitoboy": { "url": "http://localhost:9100/mcp" } } }
```

### 4.2 LangGraph / LangChain (`langchain-mcp-adapters`)

```python
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent

client = MultiServerMCPClient({
    "kitoboy": {"url": "http://localhost:9100/mcp", "transport": "streamable_http"},
    # with auth: add "headers": {"Authorization": "Bearer <MCP_AUTH_TOKEN>"}
})
tools = await client.get_tools()           # the 9 tools as LangChain tools
agent = create_react_agent(my_llm, tools)  # my_llm = any provider
```

### 4.3 Raw MCP client (smoke test, no LLM)

```python
import anyio
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

async def main():
    async with streamablehttp_client("http://localhost:9100/mcp") as (r, w, _):
        async with ClientSession(r, w) as s:
            await s.initialize()
            print([t.name for t in (await s.list_tools()).tools])
            print(await s.call_tool("kitoboy_search_person", {"query": "Пупкин"}))

anyio.run(main)
```

---

## 5. Quick start B — connect to a REAL Kitoboy deployment

The only differences from the test stack: real data already exists, the ML
models (`zoo` + Triton) are running, and you use real credentials. The MCP
container must sit on Kitoboy's docker network so it can reach `api:3052` and
`zoo:8000` (zoo is never exposed outside the network).

Two integration options:

**Option 1 — add the service to Kitoboy's own compose** (simplest; shares the
network automatically). Add a `kitoboy-mcp` service block (build or image) to
the Kitoboy compose file, on the same `postgres` network, then `up`.

**Option 2 — run our compose against the external network** (what we did):

```bash
cd kitoboy-mcp
# .env:
#   KITOBOY_API_URL=http://api:3052
#   ZOO_URL=http://zoo:8000
#   KITOBOY_USER / KITOBOY_PASSWORD = a real volunteer account (Kitoboy UI_USER/UI_PASSWORD)
#   MCP_AUTH_TOKEN=<set this if the endpoint is reachable beyond the host>
#   MCP_PUBLISH_PORT=<free host port, or drop publishing if only in-network agents connect>
# docker-compose.yml -> networks.kitoboy.name must match the real network
#   (docker network ls; typically <kitoboy-project-dir>_postgres)
docker-compose up -d --build
```

In a real deployment `zoo_*` tools work (models are up), and `kitoboy_*` tools
return real platform data. Everything else (tool set, auth flow, transport) is
identical to the test stack.

**Data flow in production:** a volunteer drives an external LLM agent (cloud now,
local model later via the agent's own `model_name`/`base_url`/`auth_key`); the
agent calls these READ tools to analyse the real platform and produce insights;
the volunteer applies any status change manually in the Kitoboy UI.

---

## 6. Operations

```bash
docker ps                                   # kitoboy-mcp / kitoboy-api-1 / kitoboy-db-1
docker logs -f kitoboy-mcp                  # follow MCP logs
docker-compose restart kitoboy-mcp          # restart MCP only (from kitoboy-mcp dir)

# Tear down
cd ~/Downloads/kitoboy-mcp && docker-compose down          # stop MCP
cd ~/Downloads/kitoboy && docker-compose \
  -f docker-compose.development.yml down                   # stop test stack
colima stop                                                # stop the VM
```

## 7. Test stack vs real deployment

| Aspect | Test stack (Quick start A) | Real deployment (Quick start B) |
| --- | --- | --- |
| Services | `db` + `api` only | full Kitoboy (api, db, zoo, Triton models, nginx) |
| Data | synthetic, from `scripts/seed.sql` | real platform data |
| `kitoboy_*` tools | work | work |
| `zoo_*` tools | not functional (no models) | work |
| Credentials | seeded `user` / `user` | real volunteer account |
| Endpoint auth | open | set `MCP_AUTH_TOKEN` |
