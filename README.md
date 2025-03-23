

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
* A Request is either a Movie or a TV Request for any number of seasons. If a users asks for 97000 seasons of a 
show, they will have 30 days to watch all of it. 
* Scruffy doesn't care about watch data. You request it, you don't watch it? Too bad, it's gone after 30 days.
* Scruffy is at least going to notify you by email a week before stuff gets deleted.
* The user should be able to click a link to ask for an extension, at least once.
* Scuffy should remain simple and run as a cron or sceduled job, no fancy UI.



## Configuration

| Environment Variable | Default Value | Description | Required |
|---------------------|---------------|-------------|-----------|
| `OVERSEERR_URL` | `http://localhost:5050` | Overseerr server URL | No |
| `OVERSEERR_API_KEY` | `None` | API key for Overseerr authentication | Yes |
| `SONARR_URL` | `http://localhost:8989` | Sonarr server URL | No |
| `SONARR_API_KEY` | `None` | API key for Sonarr authentication | Yes |
| `RADARR_URL` | `http://localhost:7878` | Radarr server URL | No |
| `RADARR_API_KEY` | `None` | API key for Radarr authentication | Yes |
| `RETENTION_DAYS` | `60` | Number of days to keep media before deletion | No |
| `REMINDER_DAYS` | `7` | Days before deletion to send reminder | No |
| `EMAIL_ENABLED` | `False` | Enable email notifications | No |
| `SMTP_HOST` | `localhost` | SMTP server hostname | If email enabled |
| `SMTP_PORT` | `25` | SMTP server port | If email enabled |
| `SMTP_USERNAME` | `None` | SMTP authentication username | Optional |
| `SMTP_PASSWORD` | `None` | SMTP authentication password | Optional |
| `SMTP_FROM_EMAIL` | `scruffy@example.com` | Sender email address | If email enabled |
| `SMTP_SSL_TLS` | `True` | Use SSL/TLS for SMTP connection | No |
| `SMTP_STARTTLS` | `False` | Use STARTTLS for SMTP connection | No |
| `LOG_LEVEL` | `INFO` | Application logging level | No |

### Docker image configuration
Those cron settings are only available if deploying using the docker image
| Environment Variable | Default Value | Description | Required |
|---------------------|---------------|-------------|-----------|
| `PROCESS_SCHEDULE` | `None` | Cron string scedule to run check and delete | Yes |
| `CHECK_SCHEDULE` | `None` | Cron string scedule to run check only (logs output) | Yes |

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