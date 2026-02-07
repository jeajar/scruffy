

<p align="center">
  <img src="https://s3.ca-central-1.wasabisys.com/public-jmax/scruffy.png">
</p>

# Scruffy, the Janitor
![Coverage](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/jeajar/c4d296c768b6156a0315ceca529b6d68/raw/coverage.json)
![Python](https://img.shields.io/badge/python-3.13-blue.svg)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)



Scruffy, the janitor is responsible to delete media requested by users with Overseerr.
For when your friends and family members are out of control.

**Note** Current project status: Very experimental and in proof of concept.

## The Problem
Overseerr is an amazing request application but the project has decided, at least for the time being, that it is not responsible for deleting media even if it has API access to Plex, Radarr and Sonarr. We need a process to handle this externally.

## Proposed Features:
* Scruffy handles media requests like a library loan. Media on disk is deleted X days after they have been added (made available).
* Scruffy don't punish the user if stuff takes time to download. The loan period starts when all the requested media is available.
* A Request is either a Movie or a TV Request for any number of seasons. If a user asks for 97000 seasons of a show, they will have 30 days to watch all of it.
* Scruffy doesn't care about watch data. You request it, you don't watch it? Too bad, it's gone after 30 days.
* Scruffy notifies you by email a week before stuff gets deleted.
* The user can click a link to ask for an extension, at least once.
* Scruffy runs as a scheduled job (API + APScheduler or cron). A simple web UI lets admins manage settings and schedules.



## Development Setup

### Environment Variables

For local development, create a `.env` file in the project root. A `.env.example` template is provided for reference.

**Important:** The `.env` file is gitignored and should never be committed. Always use `.env.example` as a template.

#### Using `uv` with Environment Variables

The project uses `pydantic-settings` which automatically loads environment variables from a `.env` file. You can use `uv run` to execute commands:

```bash
# Run commands with environment variables loaded from .env
uv run scruffy validate
uv run scruffy check
uv run scruffy process

# Or run Python scripts directly
uv run python -m scruffy.frameworks_and_drivers.cli.cli_controller validate
```

#### Debugging with VS Code

VS Code debug configurations are provided in `.vscode/launch.json`. The debugger will automatically load environment variables from `.env`:

1. Set breakpoints in your code
2. Press `F5` or go to Run and Debug
3. Select one of the available configurations:
   - **Python: Scruffy CLI (validate)** - Debug the validate command
   - **Python: Scruffy CLI (check)** - Debug the check command
   - **Python: Scruffy CLI (process)** - Debug the process command
   - **Python: Current File** - Debug the currently open Python file

The `.env` file is automatically loaded by the debugger via the `envFile` setting in the launch configuration.

#### Manual Environment Variable Loading

If you need to manually set environment variables (e.g., in a shell script):

```bash
# Load .env file and export variables
export $(cat .env | xargs)

# Then run commands
uv run scruffy validate
```

Or use `uv run` with explicit environment variables:

```bash
uv run --env-file .env scruffy validate
```

### Running the application

**Backend (API)**

From the project root, with a `.env` file in place:

```bash
uv run scruffy-api
```

The API runs at **http://localhost:8080**. For hot-reload during development:

```bash
uv run uvicorn scruffy.frameworks_and_drivers.api.app:create_app --factory --host 0.0.0.0 --port 8080 --reload
```

**Frontend**

From the project root:

```bash
cd frontend
npm install   # first time only
npm run dev
```

The frontend runs at **http://localhost:5173** and proxies `/api`, `/auth`, and `/static` to the backend at port 8080. Start the backend first so the frontend can reach it.

**Admin & scheduled jobs**

When the API is running, scheduled jobs (check/process) are stored in the same SQLite DB and run in the background via APScheduler. Admin access is determined by **Overseerr**: any user with admin permission in Overseerr can open **Admin** in the header and manage **Scheduled Jobs** (add/edit/delete cron-style schedules and run jobs on demand). The **Jobs** page shows run history with an expandable summary of what was sent (reminders) or deleted per run. No env var is required.

If you upgraded from a version before job run summaries and use an existing SQLite DB, add the column so new runs can store summaries: `sqlite3 scruffy.db "ALTER TABLE jobrunmodel ADD COLUMN summary TEXT;"`

**Using Docker Compose**

To run both backend and frontend in containers:

```bash
docker compose up
```

- Frontend: **http://localhost:3000** (production build via nginx)
- Backend: **http://localhost:8080**

With `docker-compose.override.yml` (included in the repo), the same command uses dev images with hot-reload and frontend on **http://localhost:5173**.

**Published images (CI/CD)**

CI builds and pushes two images to GitHub Container Registry on push to `main` and on version tags (`v*`):

- **Backend:** `ghcr.io/<owner>/<repo>/backend` — run on your local infra; intended for private network access only (e.g. Tailscale). The frontend (on the VPS) calls the API at the backend URL you configure.
- **Frontend:** `ghcr.io/<owner>/<repo>/frontend` — run on a VPS; serves the web UI and proxies `/api`, `/auth`, and `/static` to the backend. Point the frontend container at your backend URL (e.g. over Tailscale).

Example (replace `<owner>/<repo>` with your GitHub org/repo, e.g. `jeajar/scruffy`):

```bash
docker pull ghcr.io/<owner>/<repo>/frontend:latest
docker pull ghcr.io/<owner>/<repo>/backend:latest
```

## Configuration

**Services and Notifications** (Overseerr, Radarr, Sonarr, email) are configured in **Admin Settings** (database). Environment variables below are used as fallbacks when the database has no value (e.g. first run, CLI, Docker). Prefer configuring via the Admin UI for normal operation.

| Environment Variable | Default Value | Description | Required |
|---------------------|---------------|-------------|-----------|
| `OVERSEERR_URL` | `http://localhost:5050` | Overseerr server URL (fallback) | No |
| `OVERSEERR_API_KEY` | `None` | API key for Overseerr (fallback) | Yes |
| `SONARR_URL` | `http://localhost:8989` | Sonarr server URL (fallback) | No |
| `SONARR_API_KEY` | `None` | API key for Sonarr (fallback) | Yes |
| `RADARR_URL` | `http://localhost:7878` | Radarr server URL (fallback) | No |
| `RADARR_API_KEY` | `None` | API key for Radarr (fallback) | Yes |
| `RETENTION_DAYS` | `30` | Number of days to keep media before deletion | No |
| `REMINDER_DAYS` | `7` | Days before deletion to send reminder | No |
| `EXTENSION_DAYS` | `7` | Extra days granted when user requests an extension | No |
| `APP_BASE_URL` | `http://localhost:5173` | Base URL for email links (e.g. extension link) | No |
| `DATA_DIR` | `None` | Optional data directory (e.g. for SQLite, logs in Docker) | No |
| `EMAIL_ENABLED` | `False` | Enable email notifications (fallback) | No |
| `SMTP_HOST` | `localhost` | SMTP server hostname (fallback) | If email enabled |
| `SMTP_PORT` | `25` | SMTP server port (fallback) | If email enabled |
| `SMTP_USERNAME` | `None` | SMTP authentication username (fallback) | Optional |
| `SMTP_PASSWORD` | `None` | SMTP authentication password (fallback) | Optional |
| `SMTP_FROM_EMAIL` | `scruffy@example.com` | Sender email address (fallback) | If email enabled |
| `SMTP_SSL_TLS` | `True` | Use SSL/TLS for SMTP connection (fallback) | No |
| `SMTP_STARTTLS` | `False` | Use STARTTLS for SMTP connection (fallback) | No |
| `API_SECRET_KEY` | `change-me-in-production` | Secret key for session signing (use a strong value in production) | No |
| `CORS_ORIGINS` | `["http://localhost:5173","http://localhost:3000"]` | Allowed origins for CORS (JSON array) | No |
| `LOG_LEVEL` | `INFO` | Application logging level (DEBUG, INFO, WARNING, ERROR) | No |
| `LOG_FILE` | `None` | Path to log file (enables file logging with rotation) | No |
| `LOKI_ENABLED` | `False` | Enable Loki log shipping | No |
| `LOKI_URL` | `None` | Loki push API URL (e.g., `http://loki:3100/loki/api/v1/push`) | If Loki enabled |
| `LOKI_LABELS` | `{"app": "scruffy"}` | JSON object of static labels for Loki streams | No |

### Docker image configuration
Those cron settings are only available if deploying using the docker image
| Environment Variable | Default Value | Description | Required |
|---------------------|---------------|-------------|-----------|
| `PROCESS_SCHEDULE` | `None` | Cron string schedule to run check and delete | Yes |
| `CHECK_SCHEDULE` | `None` | Cron string schedule to run check only (logs output) | Yes |

## Docker Compose
Example `docker-compose.yaml`:

```yaml
version: '3'
services:
  scruffy:
    build: .
    environment:
      - OVERSEERR_URL=${OVERSEERR_URL}
      - OVERSEERR_API_KEY=${OVERSEERR_API_KEY}
      - SONARR_URL=${SONARR_URL}
      - SONARR_API_KEY=${SONARR_API_KEY}
      - RADARR_URL=${RADARR_URL}
      - RADARR_API_KEY=${RADARR_API_KEY}
      - EMAIL_ENABLED=${EMAIL_ENABLED}
      - SMTP_HOST=${SMTP_HOST}
      - SMTP_PORT=${SMTP_PORT}
      - SMTP_USERNAME=${SMTP_USERNAME}
      - SMTP_PASSWORD=${SMTP_PASSWORD}
      - SMTP_FROM_EMAIL=${SMTP_FROM_EMAIL}
      - TZ=America/New_York
    restart: unless-stopped
```

## Loki Integration

Scruffy supports shipping logs directly to Grafana Loki for centralized logging and monitoring. Logs are sent as structured JSON with the following format:

```json
{
  "timestamp": "2026-01-18T10:30:00.123456+00:00",
  "level": "INFO",
  "logger": "scruffy.use_cases.process_media_use_case",
  "message": "Processing media request",
  "request_id": 123,
  "media_type": "movie"
}
```

### Enabling Loki

Set the following environment variables:

```bash
LOKI_ENABLED=true
LOKI_URL=http://loki:3100/loki/api/v1/push
LOKI_LABELS='{"app": "scruffy", "env": "production"}'
```

### Docker Compose with Loki

Example `docker-compose.yaml` with Loki and Grafana:

```yaml
version: '3'
services:
  scruffy:
    build: .
    environment:
      - OVERSEERR_URL=${OVERSEERR_URL}
      - OVERSEERR_API_KEY=${OVERSEERR_API_KEY}
      - SONARR_URL=${SONARR_URL}
      - SONARR_API_KEY=${SONARR_API_KEY}
      - RADARR_URL=${RADARR_URL}
      - RADARR_API_KEY=${RADARR_API_KEY}
      - LOG_LEVEL=INFO
      - LOKI_ENABLED=true
      - LOKI_URL=http://loki:3100/loki/api/v1/push
      - LOKI_LABELS={"app":"scruffy","env":"production"}
      - TZ=America/New_York
    restart: unless-stopped
    depends_on:
      - loki

  loki:
    image: grafana/loki:2.9.0
    ports:
      - "3100:3100"
    command: -config.file=/etc/loki/local-config.yaml
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    restart: unless-stopped
```

### Querying Logs in Grafana

Once configured, you can query Scruffy logs in Grafana using LogQL:

```logql
{app="scruffy"} |= "delete"
{app="scruffy", level="error"}
{app="scruffy"} | json | request_id > 0
```