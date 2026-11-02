# Publish this repo to GitHub

1. Create an empty repo on github.com (no README, no .gitignore, no license), e.g. `socialpilot-ai`.
2. In this folder:

```bash
git init -b main
git add .
git commit -m "Initial commit: SocialPilot AI multi-agent workflow"
git remote add origin https://github.com/<your-username>/socialpilot-ai.git
git push -u origin main
```

3. Repo → Settings → Secrets and variables → Actions: add `ANTHROPIC_API_KEY` (or `OPENAI_API_KEY`), and optionally
   `YOUTUBE_API_KEY`, `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`, `REDDIT_USER_AGENT`.
4. Actions tab → "Daily run" → Run workflow to test.

Never commit `.env` (already in `.gitignore`).
