# VeilPass Docker

This directory contains Docker Compose configuration for running the full VeilPass stack locally.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) 24+
- [Docker Compose](https://docs.docker.com/compose/install/) v2.20+

## Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/veillabs/private-pass.git
cd private-pass

# 2. Set up environment variables
cp docker/.env.example docker/.env
# Edit docker/.env and fill in your signing keys

# 3. Start all services
docker compose -f docker/docker-compose.yml up -d

# 4. Verify services are running
docker compose -f docker/docker-compose.yml ps
```

## Services

| Service  | URL                     | Description                |
|----------|-------------------------|----------------------------|
| **API**  | http://localhost:8000    | FastAPI backend            |
| **Web**  | http://localhost:3000    | Next.js frontend           |
| **Docs** | http://localhost:3001    | Documentation site         |
| **DB**   | localhost:5432           | PostgreSQL 16              |
| **Redis**| localhost:6379           | Redis 7                    |

## API Documentation

Once running, the API documentation is available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/openapi.json

## Environment Variables

| Variable                   | Description                          | Default                                      |
|----------------------------|--------------------------------------|----------------------------------------------|
| `VEILPASS_SIGNING_KEY`     | Ed25519 signing key (hex)            | *required*                                   |
| `VEILPASS_VERIFICATION_KEY`| Ed25519 verification key (hex)       | Derived from signing key                     |
| `VEILPASS_DATABASE_URL`    | PostgreSQL connection string         | `postgresql+asyncpg://veilpass:veilpass@db:5432/veilpass` |
| `VEILPASS_REDIS_URL`       | Redis connection string              | `redis://redis:6379/0`                       |
| `VEILPASS_RATE_LIMIT`      | API rate limit (requests/min)        | `100`                                        |
| `NEXT_PUBLIC_API_URL`      | Frontend API URL                     | `http://localhost:8000`                      |

## Commands

```bash
# Start all services (detached)
docker compose -f docker/docker-compose.yml up -d

# View logs
docker compose -f docker/docker-compose.yml logs -f

# View logs for a specific service
docker compose -f docker/docker-compose.yml logs -f api

# Rebuild a specific service
docker compose -f docker/docker-compose.yml build api

# Restart a service
docker compose -f docker/docker-compose.yml restart web

# Stop all services
docker compose -f docker/docker-compose.yml down

# Stop and remove volumes (⚠️ destroys database data)
docker compose -f docker/docker-compose.yml down -v
```

## Generating Signing Keys

```bash
# Generate a random 32-byte seed for Ed25519
openssl rand -hex 32

# Or use the VeilPass CLI
docker compose -f docker/docker-compose.yml run --rm api \
    python -c "from app.crypto import generate_key; print(generate_key().hex())"
```

## Production Deployment

For production deployments:

1. Use strong, unique secrets for `VEILPASS_SIGNING_KEY`
2. Change the default database password
3. Use a reverse proxy (nginx/traefik) with TLS termination
4. Enable Redis authentication
5. Configure resource limits in docker-compose.yml
6. Use Docker Swarm or Kubernetes for orchestration

## Troubleshooting

**Database connection refused:**
```bash
# Wait for PostgreSQL to initialize (first start takes ~30s)
docker compose -f docker/docker-compose.yml logs db
```

**Port already in use:**
```bash
# Change host ports in docker-compose.yml or stop conflicting services
netstat -ano | findstr :3000
```

**Permission denied for volume:**
```bash
# On Linux, ensure the pgdata volume is owned by the postgres user
docker compose -f docker/docker-compose.yml down -v
# Then restart
docker compose -f docker/docker-compose.yml up -d
```
