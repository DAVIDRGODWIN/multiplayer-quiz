# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A real-time multiplayer quiz application deployed on Kubernetes. Players join game rooms, answer timed questions simultaneously, and see live leaderboards. The backend is Python (FastAPI + Socket.io) or Go where performance demands it; the frontend is React with TypeScript.

## Planned Architecture

```
multiplayer-quiz/
├── frontend/          # React + TypeScript (Vite)
├── backend/           # Python FastAPI — REST API, auth, question management
├── game-server/       # Python (python-socketio) or Go — real-time game logic
├── k8s/               # Kubernetes manifests
│   ├── base/          # Kustomize base configs
│   └── overlays/      # dev / staging / prod overlays
└── docker/            # Dockerfiles per service
```

### Service responsibilities

| Service | Technology | Role |
|---|---|---|
| `frontend` | React + TypeScript (Vite) | Player UI, Socket.io client |
| `backend` | Python FastAPI | REST: users, questions, lobby, scores |
| `game-server` | Python python-socketio / Go | WebSocket hub, game state machine |
| `redis` | Redis | Live game state: rooms, current question, scores |
| `postgres` | PostgreSQL | Persistent: question bank, user accounts, match history |

### Real-time game flow

1. Player creates/joins a room via REST (`backend`).
2. `game-server` manages room lifecycle over WebSockets (Socket.io).
3. Game state (room players, current question index, scores) lives in **Redis** keyed by room ID.
4. On game end, `game-server` persists final scores to **PostgreSQL** via an internal call to `backend`.

## Development Commands

```bash
# Run all services locally (postgres + redis + backend)
docker compose up

# Backend — first-time setup
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS/Linux
pip install -r requirements-dev.txt
cp .env.example .env

# Backend — run dev server (requires postgres running)
uvicorn app.main:app --reload

# Backend — database migrations
alembic revision --autogenerate -m "describe change"
alembic upgrade head

# Backend — tests
pytest                          # all tests
pytest tests/test_auth.py       # single file
pytest -k test_login            # single test by name

# Frontend (to be added)
# Game server (to be added)
```

## Kubernetes Deployment

Manifests live in `k8s/`. Use Kustomize overlays for environment differences.

```bash
# Apply to a cluster
kubectl apply -k k8s/overlays/dev

# Check rollout
kubectl rollout status deployment/game-server -n quiz

# Port-forward for local debugging
kubectl port-forward svc/backend 8000:8000 -n quiz
```

Each service needs a `Deployment`, `Service`, and (for frontend/backend) an `Ingress`. The `game-server` WebSocket service requires `nginx.ingress.kubernetes.io/proxy-read-timeout` and sticky sessions (`nginx.ingress.kubernetes.io/affinity: cookie`) so Socket.io connections are not disrupted by load balancing.

Redis and PostgreSQL run as `StatefulSet` resources with `PersistentVolumeClaim` storage.

## Scoring System

Each question has a fixed time limit `T` (seconds, configured per quiz). Points for a correct answer are awarded based on answer speed:

```
score = round(100 * (T - t) / T)   # t = seconds elapsed when answer submitted
score = max(0, score)               # floor at 0 (late but correct still scores 0)
```

- Maximum: **100 points** (answered instantly at `t ≈ 0`)
- Wrong answer: **0 points**, regardless of speed
- Unanswered (timeout): **0 points**

The question timer starts the moment the `game-server` emits the `question:start` event. The server records `answer_time` as `now - question_start_time` when it receives the player's answer event — **never trust a timestamp sent by the client**.

Score updates are written to Redis immediately on answer receipt so the live leaderboard reflects them without waiting for the question to end.

## Key Design Constraints

- **Socket.io sticky sessions**: WebSocket connections must always route to the same `game-server` pod. Configure Ingress affinity or use Socket.io's Redis adapter to share state across pods.
- **Redis as source of truth for live state**: Do not read live game state from PostgreSQL during a game round; always use Redis.
- **Question atomicity**: When the game-server advances a question, it should use a Redis transaction (MULTI/EXEC) to update the question index and reset per-player answer flags atomically.
- **Graceful pod shutdown**: `game-server` must handle SIGTERM by notifying connected players before the pod terminates (preStop hook + terminationGracePeriodSeconds).
