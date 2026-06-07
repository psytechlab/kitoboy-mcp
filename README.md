# kitoboy-mcp

A read-only [MCP](https://modelcontextprotocol.io) server that exposes the
[Kitoboy](https://github.com/psytechlab/kitoboy) suicide-prevention platform to
an LLM agent, so volunteers can be helped with triage, risk summaries, signal
dynamics, label explanation and contact-leak audits.

The agent **never changes platform data** — a volunteer sets statuses manually
in the Kitoboy UI. The server only wraps Kitoboy's READ endpoints.

## Docs

- [Architecture & deployment scenarios](docs/ARCHITECTURE.md) — diagrams, local vs cloud access.
- [Runbook](docs/RUNBOOK.md) — local test stack, agent wiring, real integration.

## Tools


| Tool                               | Kitoboy endpoint                   | Purpose                                                   |
| ---------------------------------- | ---------------------------------- | --------------------------------------------------------- |
| `kitoboy_search_person(query)`     | `GET /search-person`               | Find people by name substring (max 20).                   |
| `kitoboy_get_person(person_id)`    | `GET /get-person-with-avatars/:id` | Full person card: profile, status, all avatars + posts.   |
| `kitoboy_list_avatars(page, size)` | `POST /get-avatars`                | Page through avatars (newest first) for triage / review.  |
| `kitoboy_get_avatar(avatar_id)`    | `GET /get-avatar/:id`              | Full avatar card: person, status, posts with labels.      |
| `kitoboy_list_attributes()`        | `GET /get-attributes`              | Dictionary of ML annotation classes (max 100).            |
| `kitoboy_list_statuses()`          | `GET /get-statuses`                | Dictionary of suicide-risk statuses.                      |
| `zoo_classify_text(texts)`         | `POST /predict_on_text`            | Classify text (mapped names, no "irrelevant"); stateless. |
| `zoo_classify_text_raw(texts)`     | `POST /predict`                    | Raw class strings; stateless.                             |
| `zoo_list_services()`              | `GET /show_services`               | Connected Triton model services.                          |


Higher-level analysis (summaries, triage ranking, trend, similarity) is the
agent's job on top of these tools — it is not a separate endpoint.

## Important facts about the real Kitoboy API

These shape how the tools behave (verified against the Kitoboy source):

- **No confidence score exists.** Post attributes carry only `{id, name, color}`
— there is no `weight`/probability anywhere. Reason by class **presence and
frequency**, not by confidence.
- **Attribute ids are UUIDs.** Identify a class by its human-readable Russian
`name` (e.g. `номер телефона`, `эл. почта`), not by id.
- **Statuses are data-driven.** Read names/ids from `kitoboy_list_statuses` at
runtime; do not assume a fixed set.
- `**kitoboy_list_avatars` has no person filter.** For one person's avatars use
`kitoboy_get_person`.
- **Zoo returns labels only** (no weights, no sub-threshold predictions), so a
per-label "why / how confident" explanation is not available from the API.

## Configuration

All settings come from environment variables (or a local `.env`, see
`.env.example`):


| Variable                                  | Default            | Meaning                                                              |
| ----------------------------------------- | ------------------ | -------------------------------------------------------------------- |
| `KITOBOY_API_URL`                         | `http://api:3052`  | Kitoboy api base URL (in-network).                                   |
| `ZOO_URL`                                 | `http://zoo:8000`  | Zoo inference base URL (in-network).                                 |
| `KITOBOY_USER` / `KITOBOY_PASSWORD`       | `user` / `user`    | Volunteer login used to obtain a JWT.                                |
| `MCP_HOST` / `MCP_PORT`                   | `0.0.0.0` / `9000` | Streamable HTTP bind (inside the container).                         |
| `MCP_PUBLISH_PORT`                        | `9000`             | Host port docker-compose publishes (override if 9000 is taken).      |
| `MCP_AUTH_TOKEN`                          | *unset*            | If set, require `Authorization: Bearer <token>` on the MCP endpoint. |
| `REQUEST_TIMEOUT`                         | `30.0`             | Upstream HTTP timeout (s).                                           |
| `LOGIN_MAX_RETRIES` / `LOGIN_RETRY_DELAY` | `30` / `2.0`       | Startup login retry/backoff.                                         |


The server logs in to Kitoboy with the volunteer credentials, caches the JWT
(12h TTL) and transparently re-logs-in once on a 401.

## Run locally (development)

```bash
uv sync
uv run kitoboy-mcp           # serves Streamable HTTP at http://0.0.0.0:9000/mcp
```

## Run with Docker alongside Kitoboy

The MCP container must join Kitoboy's docker network (`zoo` is only reachable
inside it). Confirm the network name with `docker network ls` (Docker prefixes
the `postgres` network with the compose project, e.g. `kitoboy_postgres`) and
set it in `docker-compose.yml` under `networks.kitoboy.name`.

```bash
cp .env.example .env          # adjust credentials / MCP_PUBLISH_PORT if needed
docker compose up --build     # exposes http://localhost:${MCP_PUBLISH_PORT}/mcp
```

(If the Compose plugin is not registered, use the standalone `docker-compose` binary.)

Alternatively, add the `kitoboy-mcp` service block straight into Kitoboy's own
compose file (then it shares the `postgres` network directly).

## Testing

Unit tests mock the upstream HTTP with `respx`:

```bash
uv run pytest --cov=kitoboy_mcp --cov-report=term-missing
```

End-to-end (lite stack, no GPU models):

1. Bring up Kitoboy `db` + `api` (+ `nginx`). The api seeds statuses and the UI user.
2. Seed test data: `docker compose exec -T db psql -U postgres -d api < scripts/seed.sql`.
3. Start this server (Docker section above).
4. Inspect with the MCP Inspector: `npx @modelcontextprotocol/inspector`, connect to `http://localhost:9000/mcp`.
5. Connect a real agent (e.g. Claude Code) by adding to `mcpServers`:
  `{"kitoboy": {"url": "http://localhost:9000/mcp"}}`, then ask an analysis question.

`zoo_*` tools require the Triton model services and are only functional on the
full stack; with the lite stack they are present but not exercised.

---

*Developed by **Denis Kazhekin** ([deniskazhekinn@gmail.com](mailto:deniskazhekinn@gmail.com)), `Mar–Jun 2026`, during `Project Activity` at ITMO University.*