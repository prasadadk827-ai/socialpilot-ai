import csv
import datetime as dt
import json

import pytest

from socialpilot.config import load_settings
from socialpilot.export import scenes_to_srt, srt_time
from socialpilot.kpi import KPIStore
from socialpilot.llm import LLMError, extract_json
from socialpilot.models import Topic
from socialpilot.orchestrator import CEO


@pytest.fixture
def settings(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    s = load_settings()
    s["llm"]["provider"] = "mock"
    s["pipeline"]["output_dir"] = str(tmp_path / "reports")
    s["pipeline"]["data_dir"] = str(tmp_path / "data")
    for src in s["research"]["sources"].values():
        src["enabled"] = False
    csv_path = tmp_path / "manual.csv"
    csv_path.write_text("source,title,url,score,notes\npinterest,Storage hacks,,80,rising\n", encoding="utf-8")
    s["research"]["sources"]["manual_csv"] = {"enabled": True, "path": str(csv_path)}
    return s


def test_extract_json_variants():
    assert extract_json('{"a": 1}') == {"a": 1}
    assert extract_json('```json\n{"a": 2}\n```') == {"a": 2}
    assert extract_json('Sure! Here you go: {"a": 3} hope it helps') == {"a": 3}
    with pytest.raises(LLMError):
        extract_json("no json here")


def test_topic_coercion_and_score():
    t = Topic(title="X", content_opportunities="one", competition_score="15", viral_potential=0, evergreen_value="abc",
              category="AI tools")
    assert t.content_opportunities == ["one"]
    assert (t.competition_score, t.viral_potential, t.evergreen_value) == (10, 1, 5)
    easy = Topic(title="Easy", competition_score=1, viral_potential=9, evergreen_value=9, category="AI tools")
    hard = Topic(title="Hard", competition_score=10, viral_potential=9, evergreen_value=9, category="AI tools")
    assert easy.opportunity_score() > hard.opportunity_score()


def test_srt():
    assert srt_time(3661.5) == "01:01:01,500"
    srt = scenes_to_srt([{"voiceover": "Hello there. This is a test.", "duration_seconds": 6}])
    assert "00:00:00,000 -->" in srt and srt.count("-->") == 2


def test_kpi_summary(tmp_path):
    store = KPIStore(tmp_path)
    today = dt.date.today()
    store.add(date=today.isoformat(), platform="youtube", reach=1000, followers=50, ctr=4, revenue=2)
    store.add(date=(today - dt.timedelta(days=8)).isoformat(), platform="youtube", reach=400, followers=40)
    s = store.summary()
    assert s["current"]["reach"] == 1000 and s["previous"]["reach"] == 400
    assert s["followers_latest_total"] == 50


def test_full_daily_run(settings):
    ceo = CEO(settings, run_date="2026-11-02")
    out = ceo.run_daily()
    report = json.loads((out / "trend_report.json").read_text())
    assert len(report["topics"]) == 20
    assert (out / "trend_report.md").exists() and (out / "daily_brief.md").exists()
    topic_dirs = list((out / "topics").iterdir())
    assert len(topic_dirs) == 5
    for d in topic_dirs:
        for name in ("strategy.json", "scripts.json", "graphics.json", "seo.json", "monetization.json",
                     "video_60s.json", "subtitles_60s.srt", "blog_article.md"):
            assert (d / name).exists(), f"{name} missing in {d.name}"
    queue = json.loads((out / "queue.json").read_text())
    assert queue and all(i["status"] == "pending" for i in queue)
    platforms = {i["platform"] for i in queue}
    assert {"x", "linkedin", "facebook", "instagram", "youtube", "tiktok", "pinterest"} <= platforms


def test_approve_and_publish_gate(settings):
    ceo = CEO(settings, run_date="2026-11-02")
    ceo.run_daily(n_topics=1)
    assert ceo.publish()["approved"] == 0            # nothing approved yet
    assert ceo.approve(all_items=True) > 0
    result = ceo.publish()                           # dry run
    assert result["dry_run"] and result["would_send"] > 0 and result["waiting_for_asset"] > 0
    assert all(not i["needs_asset"] for i in result["items"])
    with pytest.raises(RuntimeError):
        ceo.publish(send=True)                       # no webhook configured


def test_optimize_needs_data(settings):
    ceo = CEO(settings, run_date="2026-11-02")
    assert ceo.optimize() is None
    ceo.kpis.add(platform="x", reach=10)
    assert ceo.optimize().exists()
