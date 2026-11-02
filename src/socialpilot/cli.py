from __future__ import annotations

import argparse
import json
import logging
import sys

from .config import load_settings
from .orchestrator import CEO


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="socialpilot", description="AI social media agency in a box")
    p.add_argument("--config", help="path to settings.yaml (default config/settings.yaml)")
    p.add_argument("--provider", help="anthropic | openai | mock | auto")
    p.add_argument("--date", help="run date YYYY-MM-DD (default today)")
    sub = p.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("research", help="STEP 1-2: daily trend report only")
    r.add_argument("--top", type=int, help="number of topics (default 20)")

    run = sub.add_parser("run", help="full daily workflow (research -> content -> plan -> brief)")
    run.add_argument("--topics", type=int, help="how many top topics to produce (default 5)")
    run.add_argument("--goal", help="override the business goal for this run")

    ap = sub.add_parser("approve", help="approve queued posts (human review gate)")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--ids", nargs="*")

    pub = sub.add_parser("publish", help="send approved posts to your Zapier/Make webhook (dry run by default)")
    pub.add_argument("--send", action="store_true", help="actually send")

    k = sub.add_parser("kpi", help="track KPIs")
    ks = k.add_subparsers(dest="kpi_cmd", required=True)
    ka = ks.add_parser("add")
    ka.add_argument("--platform", required=True)
    for f in ("reach", "followers", "watch_time_minutes", "ctr", "engagement", "leads", "revenue"):
        ka.add_argument(f"--{f.replace('_', '-')}", dest=f, type=float, default=0)
    ks.add_parser("summary")

    sub.add_parser("optimize", help="STEP 7-8: analyse KPIs and recommend improvements")
    return p


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S")
    args = build_parser().parse_args(argv)
    settings = load_settings(args.config)
    if args.provider:
        settings["llm"]["provider"] = args.provider
    ceo = CEO(settings, run_date=args.date)

    if args.cmd == "research":
        topics, _ = ceo.research(args.top)
        print(f"{len(topics)} topics -> {ceo.out / 'trend_report.md'}")
    elif args.cmd == "run":
        print(f"Done -> {ceo.run_daily(goal=args.goal, n_topics=args.topics)}")
    elif args.cmd == "approve":
        if not (args.all or args.ids):
            print("Use --all or --ids ID [ID ...]", file=sys.stderr)
            return 2
        print(f"Approved {ceo.approve(args.ids, args.all)} item(s)")
    elif args.cmd == "publish":
        print(json.dumps(ceo.publish(send=args.send), indent=2, ensure_ascii=False))
    elif args.cmd == "kpi":
        if args.kpi_cmd == "add":
            row = {f: getattr(args, f) for f in ("reach", "followers", "watch_time_minutes", "ctr", "engagement", "leads", "revenue")}
            ceo.kpis.add(platform=args.platform, **row)
            print("KPI row saved")
        else:
            print(json.dumps(ceo.kpis.summary() or "no KPI data yet", indent=2))
    elif args.cmd == "optimize":
        path = ceo.optimize()
        print(f"-> {path}" if path else "No KPI data yet - add some with `socialpilot kpi add`.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
