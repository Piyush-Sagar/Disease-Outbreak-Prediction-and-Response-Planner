# Setup & Running

## Prerequisites

- **Python 3.10+** (developed on 3.14). The code uses `X | None` type unions and
  built-in generics.
- **Node.js 20+** and npm.
- A working console on Windows / macOS / Linux. All commands below run from the
  **repository root**.

## 1. Install dependencies

```bash
# Python (ML + backend)
pip install -r backend/requirements.txt

# Node (root workspace tooling)
npm install

# Node (frontend)
cd frontend && npm install && cd ..
```

> The root `package.json` uses `concurrently` to launch both servers with one
> command.

## 2. Train the model (once)

```bash
npm run train            # python ml/train.py
```

Writes to `ml/artifacts/` (`*.joblib`, `metrics.json`, `feature_importance.csv`,
`metadata.json`) and `ml/figures/` (ROC, confusion matrices, feature
importance). These directories are git-ignored, so training is required after a
fresh clone. Takes ~10–30 s.

## 3. Seed the database (once)

```bash
npm run seed             # creates backend/demo.db + loads the demo CSVs
```

Seed is idempotent — re-running inserts 0 rows. The backend also seeds
automatically on first use if the file is missing.

## 4. Run everything

```bash
npm run dev
```

- API: **http://127.0.0.1:8000** (+ interactive docs at `/docs`)
- Dashboard: **http://localhost:3000**

On the first API request the backend lazily loads the trained models and
persists the latest-week predictions. Press `Ctrl+C` to stop both servers.

### Run servers individually

```bash
python backend/run.py         # FastAPI only, :8000
cd frontend && npm run dev    # Next.js only, :3000
```

## Verification

```bash
npm run test:backend     # pytest — expect "19 passed"
npm run test:frontend    # tsc --noEmit — expect no output
npm run build            # next build — expect all routes to compile
npx eslint .             # from frontend/ — expect no errors
```

## Project layout

```text
.
├── backend/            FastAPI service
│   ├── app/
│   │   ├── routers/    /api endpoints (regions, predictions, recommendations,
│   │   │               routes, model-info, dashboard)
│   │   ├── services/   model loading, severity, priority, response planning,
│   │   │               alerts, explainability, routing, pipeline
│   │   ├── main.py     app factory, CORS, static figures
│   │   ├── database.py SQLite schema + seed + upserts
│   │   ├── config.py   env vars + re-exported ml/config thresholds
│   │   └── schemas.py  Pydantic payloads
│   ├── tests/          19 pytest tests
│   ├── requirements.txt
│   └── run.py          dev launcher (ucicorn)
├── data/               synthetic demo dataset (CSV + roads.json)
├── docs/               this documentation set
├── frontend/           Next.js dashboard
│   └── src/app/        /dashboard /regions /predictions/[id] /response
│                       /routes /model /data  (+ layout, sidebar nav)
├── ml/                 training pipeline (config, preprocess, features, label,
│   │                   train, evaluate, predict) + artifacts/figures
├── scripts/            generate_data.py (dataset generator)
├── .env.example        documented environment variables
└── package.json        workspace scripts (dev, train, seed, test, build)
```

## Environment variables

See `.env.example`. Defaults are ready to run with no configuration:

| Variable | Default |
| --- | --- |
| `API_HOST` | `127.0.0.1` |
| `API_PORT` | `8000` |
| `DATABASE_PATH` | `backend/demo.db` |
| `ML_ARTIFACTS_DIR` | `ml/artifacts` |
| `ML_FIGURES_DIR` | `ml/figures` |
| `NEXT_PUBLIC_API_URL` | `http://127.0.0.1:8000` |
| `DEMO_MODE` | `true` |

`DEMO_MODE=true` keeps the demo-data watermark visible in the UI.

## Troubleshooting

- **`Model artifacts not found` on API start** → run `npm run train`.
- **API refuses connections / empty pages** → check `NEXT_PUBLIC_API_URL`
  matches the API address (`http://127.0.0.1:8000` by default) and that the
  backend started (`curl http://127.0.0.1:8000/health`).
- **Ports already in use** → change `API_PORT` or run the frontend with
  `npx next dev -p 3001`.
- **`demo node_modules` / multiple lockfiles warnings in `next build`** → benign;
  `next.config.ts` sets `turbopack.root` to keep the frontend build scoped
  correctly.
- **Seeded data looks stale** → delete `backend/demo.db` and restart; the
  database is re-seeded and re-predicted automatically.