"""Deterministic offline responses so the whole pipeline can run (and be tested) with no API key.
This is SAMPLE output, not real research."""
from __future__ import annotations

SEEDS = {
    "Personal finance": ["Build a $1,000 emergency fund fast", "A simple monthly budget that sticks", "How to read your credit report"],
    "Productivity": ["The 2-minute rule to stop procrastinating", "Plan your week in 15 minutes", "Fix a messy inbox in one evening"],
    "AI tools": ["Use AI to summarize long PDFs", "Write better prompts in 3 steps", "Automate repetitive tasks with free AI tools"],
    "Home improvement": ["Fix a leaky faucet without a plumber", "Patch small wall holes like a pro", "Cut your energy bill with cheap upgrades"],
    "Health habits": ["Build a 10-minute morning routine", "Sleep better without supplements", "Walk more with a desk job"],
    "Career growth": ["Ask for a raise with evidence", "Update your resume for ATS filters", "Learn a new skill in 30 days"],
    "Mobile technology": ["Free up phone storage in 5 minutes", "Make your phone battery last longer", "Lock down phone privacy settings"],
    "Education": ["Study smarter with active recall", "Learn a language 15 minutes a day", "Take better notes with a simple method"],
}
CATS = list(SEEDS)


def _trend(p: dict) -> dict:
    n = int(p.get("top_n", 20))
    topics = []
    for i in range(n):
        cat = CATS[i % len(CATS)]
        seeds = SEEDS[cat]
        title = seeds[(i // len(CATS)) % len(seeds)]
        topics.append({
            "title": title,
            "category": cat,
            "audience": f"Busy adults looking for practical help with {cat.lower()}",
            "problem": f"People feel stuck or overwhelmed when they try to: {title.lower()}",
            "search_intent": "How-to / problem-solving",
            "content_opportunities": ["Step-by-step short video", "Checklist carousel", "Beginner blog guide"],
            "monetization_opportunities": ["Lead magnet checklist", "Relevant affiliate tool (disclosed)", "Ad revenue"],
            "competition_score": 3 + (i * 3) % 6,
            "viral_potential": 4 + (i * 5) % 6,
            "evergreen_value": 5 + (i * 7) % 5,
            "sources": ["mock"],
        })
    return {"topics": topics}


def _ideas(t: str, n: int) -> list[dict]:
    return [{"title": f"{t}: tip {i + 1}", "hook": f"Most people get '{t.lower()}' wrong - here's tip {i + 1}.",
             "outline": "Problem -> quick fix -> result", "caption": f"Tip {i + 1} for: {t}. Save this for later."}
            for i in range(n)]


def _posts(t: str, n: int) -> list[dict]:
    return [{"text": f"{t} - practical tip #{i + 1}: start small, track one number, and repeat daily."} for i in range(n)]


def _strategy(p: dict) -> dict:
    t = p["topic"]["title"]
    return {
        "content_pillar": p["topic"].get("category", "General"),
        "audience_pain_point": p["topic"].get("problem") or f"People struggle with: {t}",
        "problem_statement": f"Without a clear method, '{t}' feels confusing and gets postponed.",
        "solution_framework": ["Define the goal", "Do the smallest useful step", "Track it", "Review weekly"],
        "hook": f"Struggling with {t.lower()}? Try this 3-step fix.",
        "cta": "Save this and follow for one practical fix every day.",
        "monetization_method": "Free checklist (lead magnet), then a relevant disclosed affiliate tool.",
        "youtube_shorts": _ideas(t, 5),
        "instagram_reels": _ideas(t, 5),
        "facebook_posts": _posts(t, 5),
        "x_posts": _posts(t, 5),
        "linkedin_posts": _posts(t, 3),
        "blog_outline": {"title": f"{t}: a beginner's guide",
                         "sections": [{"heading": h, "points": ["Key idea", "Example"]}
                                      for h in ("Why it matters", "The 3-step method", "Common mistakes", "Next steps")]},
    }


def _script(t: str, words: int) -> dict:
    body = (f"Here is a simple way to handle {t.lower()}. " * (words // 10 + 1)).split()[:words]
    return {"hook": f"Stop scrolling - this fixes {t.lower()}.", "main_problem": f"Most people struggle with {t.lower()}.",
            "solution": "Use the three-step method.", "demonstration": "Show the steps on screen.",
            "cta": "Follow for more practical tips.", "full_script": " ".join(body)}


def _scripts(p: dict) -> dict:
    t = p["topic"]["title"]
    return {"scripts": {"30s": _script(t, 75), "60s": _script(t, 150), "2min": _script(t, 300)},
            "blog_article_markdown": f"# {t}\n\n## Why it matters\nA short intro.\n\n## The method\n1. Step one\n2. Step two\n3. Step three\n"}


def _prompts(t: str, ar: str) -> dict:
    base = f"clean modern layout, high contrast, bold readable focal subject about '{t}', mobile friendly, uncluttered background"
    return {"midjourney": f"{base} --ar {ar} --style raw --v 6", "dalle": base, "copilot": base,
            "canva_ai": f"{base}, flat vector style", "stable_diffusion": f"{base}, sharp, 8k, studio lighting"}


def _graphics(p: dict) -> dict:
    t = p["topic"]["title"]
    neg = "blurry, low contrast, cluttered, distorted text, watermark"
    return {"designs": {
        "thumbnail": {"size": "1280x720", "text_overlay": t[:30], "prompts": _prompts(t, "16:9"), "negative_prompt": neg},
        "carousel": {"size": "1080x1350", "slide_copy": ["Hook", "Problem", "Step 1", "Step 2", "Step 3", "CTA"],
                     "prompts": _prompts(t, "4:5"), "negative_prompt": neg},
        "story": {"size": "1080x1920", "text_overlay": "Quick tip", "prompts": _prompts(t, "9:16"), "negative_prompt": neg},
        "reel_cover": {"size": "1080x1920", "text_overlay": t[:30], "prompts": _prompts(t, "9:16"), "negative_prompt": neg},
    }}


def _video(p: dict) -> dict:
    t = p["topic"]["title"]
    target = int(p.get("target_seconds", 60))
    each = max(3, target // 5)
    voice = ["Stop scrolling. This fixes a common problem.", "Most people get this wrong.",
             "Here is the simple method.", "Watch how it works in practice.", "Follow for more practical tips."]
    scenes = [{"scene": i + 1, "visual": f"Screen recording / talking head - part {i + 1}", "broll": ["hands typing", "phone close-up"],
               "voiceover": v, "duration_seconds": each} for i, v in enumerate(voice)]
    return {"scenes": scenes, "voiceover_prompt": "Warm, friendly, clear narrator, medium pace, neutral accent.",
            "youtube_title": f"{t} (simple method)",
            "youtube_description": f"A practical walkthrough of: {t}.\n\nDisclosure: some links may be affiliate links."}


def _seo(p: dict) -> dict:
    t = p["topic"]["title"]
    return {"main_keyword": t.lower(), "secondary_keywords": [f"{t.lower()} tips", f"{t.lower()} guide"],
            "long_tail_keywords": [f"how to {t.lower()} for beginners", f"easy way to {t.lower()}"],
            "seo_title": f"{t}: Simple Step-by-Step Guide", "meta_description": f"Learn {t.lower()} with a simple, practical method.",
            "internal_linking_ideas": ["Link to a beginner checklist", "Link to a related tool review"],
            "youtube": {"title": f"{t} (Simple Method)", "tags": [t.lower(), "how to", "tips"]},
            "pinterest": {"title": f"{t} - Step by Step", "description": f"Save this practical guide: {t.lower()}."}}


def _monetization(p: dict) -> dict:
    return {"affiliate_programs": [{"name": "Relevant tool affiliate", "fit": "Solves the same problem", "note": "Disclose clearly"}],
            "digital_products": ["Printable checklist pack"], "courses": ["Mini-course for beginners"],
            "ad_revenue": ["YouTube Partner Program once eligible", "Display ads on blog"],
            "sponsorships": ["Tools in the same niche"], "lead_magnets": ["Free 1-page checklist"],
            "earning_potential": "Medium", "ethics_note": "Only recommend products you have used; disclose all affiliate links."}


def _publisher(p: dict) -> dict:
    plats = p.get("platforms", [])
    times = {"YouTube": ["15:00", "18:00"], "Facebook": ["09:00", "13:00"], "Instagram": ["11:00", "19:00"],
             "LinkedIn": ["08:00", "12:00"], "Pinterest": ["20:00", "21:00"], "TikTok": ["18:00", "21:00"], "X": ["08:00", "12:00", "17:00"]}
    return {"optimal_times": {k: v for k, v in times.items() if not plats or k in plats},
            "hashtag_sets": {t["id"]: ["#tips", "#howto", f"#{t.get('category', 'life').replace(' ', '').lower()}"] for t in p.get("topics", [])},
            "repurposing_strategy": [{"source_format": "60s video", "repurpose_to": ["YouTube Shorts", "Reels", "TikTok"],
                                      "how": "Same cut, native captions, platform-specific hook text"}],
            "posting_cadence": {"X": "3/day", "YouTube": "1/day", "Instagram": "1/day"},
            "notes": "Times are starting points - check each platform's own analytics after 2 weeks."}


def _brief(p: dict) -> dict:
    return {"summary": "Sample daily brief (mock mode).", "top_priorities": ["Review and approve the queue"],
            "risks": ["Scores are estimates"], "improvements": ["Connect real API keys"], "kpi_focus": ["watch time", "CTR"]}


def _optimize(p: dict) -> dict:
    return {"summary": "Sample optimization (mock mode).", "what_worked": ["n/a"], "what_to_fix": ["n/a"],
            "next_actions": ["Post consistently for 2 weeks, then compare"], "kpi_targets_next_week": {"reach": "+10%"},
            "monetization_adjustments": ["Add one lead magnet"]}


_MOCKS = {
    "trend_research": _trend, "content_strategist": _strategy, "script_writer": _scripts,
    "graphic_designer": _graphics, "video_producer": _video, "seo": _seo, "monetization": _monetization,
    "publisher": _publisher, "ceo_brief": _brief, "ceo_optimize": _optimize,
}


def mock_response(agent: str, payload: dict) -> dict:
    return _MOCKS[agent](payload)
