# Multiplayer Quiz

A real-time multiplayer quiz game where players compete by answering questions as fast as possible. Points are awarded proportionally — the quicker the correct answer, the higher the score (max 100 points per question).

## Architecture

```
┌─────────────┐     REST/WS      ┌──────────────────┐
│   Frontend  │ ──────────────── │   Backend (API)  │
│  React + TS │                  │   FastAPI + JWT   │
└─────────────┘                  └────────┬─────────┘
                                          │
              ┌───────────────────────────┤
              │                           │
     ┌────────▼────────┐        ┌─────────▼────────┐
     │   Game Server   │        │   PostgreSQL      │
     │  Socket.io (WS) │        │  users, questions │
     └────────┬────────┘        │  matches, scores  │
              │                 └──────────────────┘
     ┌────────▼────────┐
     │      Redis      │
     │  live game state│
     └─────────────────┘
```

| Service | Tech | Responsibility |
|---|---|---|
| `backend` | Python FastAPI | REST API: auth, questions, rooms, scores |
| `game-server` | Python / Go + Socket.io | WebSocket hub, real-time game state machine |
| `frontend` | React + TypeScript (Vite) | Player UI |
| `redis` | Redis 7 | Live room/score state during a game |
| `postgres` | PostgreSQL 16 | Persistent data: users, question bank, match history |

### Scoring

```
score = round(100 × (T − t) / T)   # T = time limit (s), t = elapsed time (s)
score = 0  for wrong or unanswered
```

The timer starts when the server emits `question:start`. Elapsed time is always measured server-side — client timestamps are not trusted.

---

## Local Development

### Prerequisites

- Docker Desktop
- Python 3.12+ (for running backend tests locally)

### Run all services

```bash
docker compose up
```

This starts PostgreSQL, Redis, and the backend. The backend runs `alembic upgrade head` on startup.

| Service | URL |
|---|---|
| Backend API | http://localhost:8000 |
| API docs | http://localhost:8000/docs |

### Backend (without Docker)

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux

pip install -r requirements-dev.txt
cp .env.example .env            # fill in values

alembic upgrade head
uvicorn app.main:app --reload
```

### Running tests

```bash
cd backend
pytest tests/ -v                # all tests
pytest tests/test_scoring.py    # single file
pytest -k test_login            # single test by name
```

---

## GitOps Workflow

This project follows GitOps: **`main` is always the desired cluster state**. No direct `kubectl apply` to production.

```
feature branch
      │
      │  git push + open PR
      ▼
  GitHub PR ──► CI: pytest must pass
      │
      │  merge to main
      ▼
  CD Pipeline
  ├─ builds Docker image
  ├─ pushes to GHCR (ghcr.io/davidrgodwin/multiplayer-quiz-backend:<sha>)
  └─ commits updated image tag → k8s/overlays/prod/kustomization.yaml
                                          │
                                          ▼
                                       ArgoCD
                                  detects Git change
                                  syncs cluster to new state
```

### Branch rules

| Rule | Detail |
|---|---|
| Direct push to `main` | Blocked |
| PR merge requires | `test-backend` CI check to pass |
| Secrets in Git | Never — applied to the cluster manually (see below) |

### Development flow

```bash
git checkout -b feature/my-feature
# make changes
git push origin feature/my-feature
# open PR on GitHub → CI runs → merge when green
```

---

## Kubernetes & ArgoCD

### Prerequisites

- A running Kubernetes cluster (local: [kind](https://kind.sigs.k8s.io/) or [minikube](https://minikube.sigs.k8s.io/))
- `kubectl` configured to target the cluster
- ArgoCD installed in the cluster

### 1. Install ArgoCD

```bash
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Wait for ArgoCD to be ready
kubectl wait --for=condition=available deployment/argocd-server -n argocd --timeout=120s
```

### 2. Access the ArgoCD UI

```bash
# Get the initial admin password
kubectl get secret argocd-initial-admin-secret -n argocd \
  -o jsonpath="{.data.password}" | base64 -d

# Forward the UI to localhost
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

Open https://localhost:8080 and log in with `admin` and the password above.

### 3. Create the backend secret (one-time, per cluster)

Secrets are never stored in Git. Apply them directly to the cluster:

```bash
kubectl create namespace quiz

kubectl create secret generic backend-secret -n quiz \
  --from-literal=DATABASE_URL=postgresql+asyncpg://<user>:<pass>@<host>:5432/quiz \
  --from-literal=REDIS_URL=redis://<host>:6379 \
  --from-literal=SECRET_KEY=<strong-random-value> \
  --from-literal=INTERNAL_SECRET=<strong-random-value>
```

### 4. Register the app with ArgoCD

```bash
kubectl apply -f k8s/argocd/application.yaml
```

ArgoCD will immediately begin syncing `k8s/overlays/prod` from the `main` branch. From this point, every merge to `main` that touches `backend/` triggers the CD pipeline, which commits a new image tag — ArgoCD detects the commit and rolls out the update automatically.

### Manual overlay commands (dev / debugging)

```bash
# Preview what would be applied
kubectl kustomize k8s/overlays/prod

# Apply dev overlay manually
kubectl apply -k k8s/overlays/dev

# Check rollout
kubectl rollout status deployment/backend -n quiz

# Port-forward for local debugging
kubectl port-forward svc/backend 8000:8000 -n quiz
```

### Manifest structure

```
k8s/
├── argocd/
│   └── application.yaml          ArgoCD Application (watches overlays/prod on main)
├── base/
│   ├── namespace.yaml
│   └── backend/
│       ├── deployment.yaml       image tag managed by CD pipeline
│       ├── service.yaml          ClusterIP on port 8000
│       └── configmap.yaml        non-sensitive env vars
└── overlays/
    ├── dev/                      1 replica, latest tag
    └── prod/                     2 replicas, pinned SHA tag (updated by CD)
```

> **Adding a new service (frontend, game-server, etc.):** add its manifests under `k8s/base/<service>/`, reference it in `k8s/base/kustomization.yaml`, and add a matching `images:` entry in both overlays.

---

## API Reference

Interactive docs available at `http://localhost:8000/docs` when the backend is running.

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/auth/register` | — | Create account |
| POST | `/auth/login` | — | Get JWT token |
| GET | `/rooms` | JWT | List open rooms |
| POST | `/rooms` | JWT | Create a room |
| GET | `/rooms/{code}` | JWT | Get room details |
| GET | `/matches/{id}/scores` | JWT | Per-player scores for a match |
| GET | `/scores/leaderboard` | — | All-time top scores |
| POST | `/questions` | Admin JWT | Add a question |
| POST | `/internal/rooms/{code}/match` | Internal token | Start a match (game-server only) |
| POST | `/internal/matches/{id}/scores` | Internal token | Submit final scores (game-server only) |
