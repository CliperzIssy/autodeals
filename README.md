# AutoDeals

Car sourcing tool for Dutch dealers. It runs listings from German car marketplaces through an AI pipeline that scores each deal.

**Status:** project from March 2026, not a commercial product.

## What it does

Each car goes through a four-step Gemini 2.5 Flash pipeline, where each step fails independently:

1. **Normalise** the listing data.
2. **Flag** possible problems with the car.
3. **Score** the deal against comparable cars.
4. **Translate** the result into Dutch.

## Where to look

| Path | What it holds |
|---|---|
| `backend/app/ai/pipeline.py` | The pipeline and its failure handling |
| `backend/app/ai/prompts/` | Prompts for each step |
| `backend/app/tasks/` | Celery jobs and scheduling |
| `backend/app/api/` | FastAPI routes |
| `frontend/src/` | Next.js dashboard |

**Stack:** Python, FastAPI, Celery, Redis, PostgreSQL, Gemini, Next.js

The scraper code is not in this public copy, so the backend will not run from this repo alone. This is a clean snapshot without the original files or logs. Shared as a portfolio project; all rights reserved.
