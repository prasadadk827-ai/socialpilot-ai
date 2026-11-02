# SocialPilot AI

A multi-agent system that runs the daily workflow of a small digital media business:
**research trends → pick topics → plan → write → design prompts → video plans → SEO → monetization → schedule → track KPIs → optimize.**

Nine specialist agents are coordinated by a Master CEO agent. Every agent's behaviour lives in a plain Markdown file in
[`src/socialpilot/prompts/`](src/socialpilot/prompts), so you can edit the "personality" without touching code.

```
                         ┌──────────────── Master CEO (orchestrator) ────────────────┐
 Google Trends ─┐        │                                                           │
 YouTube ───────┤        │  1 Trend Research ─► 2 Select top 5 (scoring formula)     │
 Reddit ────────┼─signals┤        │                                                  │
 News RSS ──────┤        │        ▼   per topic                                      │
 manual CSV ────┘        │  3 Content Strategist ─► 4 Graphic Designer               │
 (Pinterest/TikTok/      │  5 Script Writer ─► Video Producer (+ .srt) ─► SEO ─►     │
  X/Quora exports)       │    Monetization                                           │
                         │  6 Publisher (calendar, times, hashtags) ─► queue.json    │
                         │  7 KPIs (CSV) ─► 8 CEO brief & optimization               │
                         └───────────────────────────────────────────────────────────┘
                                   │ human review: approve ─► publish --send
                                   ▼
                      Zapier / Make webhook ─► Buffer, Metricool, Notion, Airtable ...
```

## Quick start

```bash
git clone https://github.com/<you>/socialpilot-ai.git
cd socialpilot-ai
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
cp .env.example .env                                   # add ANTHROPIC_API_KEY or OPENAI_API_KEY
socialpilot run                                        # no key? it runs in offline MOCK mode with sample output
```

Output lands in `reports/YYYY-MM-DD/`:

| File | What |
|------|------|
| `trend_report.md/.json` | Top 20 opportunities with all 9 fields + opportunity score |
| `topics/<topic>/strategy.json` | pillar, pain point, framework, hook, CTA, 5+5+5+5+3 post ideas, blog outline |
| `topics/<topic>/scripts.json`, `blog_article.md` | 30s / 60s / 2min scripts and a blog article |
| `topics/<topic>/graphics.json` | Prompts for Midjourney, DALL-E, Copilot, Canva AI, Stable Diffusion (thumbnail, carousel, story, reel cover) |
| `topics/<topic>/video_<fmt>.json`, `subtitles_<fmt>.srt` | Scene breakdown, B-roll, voiceover prompt, YouTube title/description, subtitles |
| `topics/<topic>/seo.json` | Keywords, titles, meta description, internal links (Google / YouTube / Pinterest) |
| `topics/<topic>/monetization.json` | Affiliate / products / courses / ads / sponsors / lead magnets + earning potential |
| `publishing_plan.json`, `queue.json` | Posting times, hashtag sets, repurposing strategy, scheduled posts |
| `daily_brief.md`, `run_summary.md` | CEO priorities, risks, improvements |

## Commands

```bash
socialpilot research --top 20          # STEP 1-2 only
socialpilot run --topics 5             # full daily workflow
socialpilot approve --all              # human review gate (or --ids ID ...)
socialpilot publish                    # dry run: shows what would be sent
socialpilot publish --send             # POSTs approved, asset-ready items to your webhook
socialpilot kpi add --platform youtube --reach 1200 --followers 340 --watch-time-minutes 95 --ctr 4.1 --engagement 5.2 --leads 12 --revenue 8
socialpilot kpi summary
socialpilot optimize                   # STEP 7-8: recommendations from your KPIs
```
Global flags go before the command: `socialpilot --provider mock --date 2026-11-02 run`.

## Configuration

Edit [`config/settings.yaml`](config/settings.yaml): LLM provider/model, geo, subreddits, news feeds, priority
categories, platforms, timezone, video formats (remove formats to cut API cost). Secrets live in `.env` (never committed).

## What is real, and what you must do yourself

Please read this: it avoids surprises.

- **Trend sources.** Google Trends (public RSS), YouTube (official API, needs key), Reddit (OAuth recommended) and news RSS are
  collected automatically. **Quora, Pinterest Trends, X and TikTok have no free official trend APIs**, so drop what you see
  there into `data/manual_signals.csv` (see `data/manual_signals.example.csv`). Scores are model *estimates*, not measured search volume.
- **Publishing.** The app builds a scheduled queue and sends it to a **Zapier/Make webhook**; connect that to Buffer, Metricool,
  etc. It does not log in to social accounts or scrape. Text posts (X, LinkedIn, Facebook) are ready to publish. Video and image
  posts are flagged `needs_asset` until you produce the asset (CapCut, Canva, an AI voice tool) from the generated plans.
- **Human approval is built in.** Nothing is sent until you run `approve` and `publish --send`. Fully unattended posting of
  AI-written content is the fastest way to get accounts limited, and it risks health/finance misinformation. Skim before you ship.
- **Platform rules.** Check each platform's policy on automation and AI-generated content (several require an AI-content label),
  Reddit's API terms for commercial use, and disclose affiliate links (e.g. FTC rules in the US).
- **Cost.** One daily run is roughly 40-45 LLM calls (1 research + 8 per topic × 5 + plan + brief). Reduce `topics_per_day` or `video_formats` to lower it.
- **Scheduled runs.** `.github/workflows/daily.yml` runs the workflow every day and uploads `reports/` as an artifact (add your API keys as repo secrets). It never publishes.

## Development

```bash
pytest -q          # fully offline; uses the mock provider
```

## Roadmap ideas

Perplexity as an extra research source · Notion/Airtable direct sync · Canva Connect API · CapCut/ElevenLabs automation ·
per-platform analytics importers · web dashboard.

## License

MIT
