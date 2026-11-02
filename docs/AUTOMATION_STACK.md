# How the tools in your stack plug in

| Tool | Role | How it connects here |
|------|------|----------------------|
| ChatGPT / Claude (agent brain) | LLM for all agents | Set `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`. Microsoft Copilot has no public API for this, so use it manually with the prompts in `graphics.json`. |
| Perplexity (research) | Extra research source | Not built in yet. Easiest path: paste its findings into `data/manual_signals.csv`. |
| Google Trends | Trend signal | Built in (public RSS feed). |
| Canva AI | Thumbnails, carousels | Use `graphics.json` prompts + `text_overlay`; add text in Canva (AI image models garble text). |
| CapCut AI | Video editing | Use `video_<fmt>.json` scenes + `subtitles_<fmt>.srt` (import the .srt as captions). |
| Zapier / Make.com | Glue | Create a "Catch Hook" trigger, put its URL in `SOCIAL_WEBHOOK_URL`. Each queue item arrives as one JSON object. |
| Buffer / Metricool | Scheduling | Add a Buffer/Metricool action in your Zap/Scenario using `text`, `hashtags`, `scheduled_at`. |
| Notion / Airtable | Content calendar, KPIs | Add a "create record" step after the webhook; export KPI CSV into Airtable if you like. |

## Webhook payload (one POST per post)

```json
{
  "id": "2026-11-02-x-001",
  "platform": "x",
  "topic": "Use AI to summarize long PDFs",
  "scheduled_at": "2026-11-03T12:00:00+01:00",
  "title": "",
  "text": "…",
  "hashtags": ["#tips", "#aitools"],
  "needs_asset": "",
  "status": "approved"
}
```
`needs_asset` is `""` for text posts, `"video"` or `"image"` when you still have to produce media. Only asset-free items are sent by `publish --send`.
