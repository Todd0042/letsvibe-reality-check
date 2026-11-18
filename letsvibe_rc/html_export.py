"""Standalone HTML export for LetsVibe: Reality Check reports."""

from __future__ import annotations

import html
from typing import Any, Dict


def _esc(val: Any) -> str:
    return html.escape(str(val or ""), quote=True)


def render_rc_standalone_html(report: Dict[str, Any]) -> str:
    verdict = str(report.get("verdict") or "DO NOT BUILD")
    if verdict == "ACTUALLY VIABLE":
        accent = "#34d399"
    elif verdict == "NICHE ONLY":
        accent = "#22d3ee"
    else:
        accent = "#f87171"

    dims = report.get("dimensions") or {}
    dim_rows = "".join(
        f"<tr><td><strong>{_esc(d.get('label') or k)}</strong></td>"
        f"<td>{int(d.get('weight') or 0)}%</td>"
        f"<td style='color:#22d3ee;font-weight:700;white-space:nowrap'>{float(d.get('score') or 0):.1f}/10"
        f"<div class='lv-bar'><div class='lv-bar-fill' style='width:{min(100, max(0, float(d.get('score') or 0) * 10.0)):.1f}%'></div></div></td>"
        f"<td>{_esc(d.get('reasoning'))}</td></tr>"
        for k, d in dims.items()
        if isinstance(d, dict)
    )

    flaws = "".join(f"<li>⚠️ {_esc(x)}</li>" for x in (report.get("fatal_flaws") or [])) or "<li>None flagged.</li>"
    redeeming = "".join(f"<li>✅ {_esc(x)}</li>" for x in (report.get("redeeming_angles") or [])) or "<li>No major redeeming angles identified.</li>"
    comps = "".join(
        f"<div class='lv-card-item'><div class='lv-item-head'><strong>{_esc(c.get('name'))}</strong>"
        f"<span class='lv-pill'>{_esc(c.get('type'))}</span></div>"
        f"<p class='lv-muted' style='margin:0'>{_esc(c.get('why_it_wins'))}</p></div>"
        for c in (report.get("existing_competitors") or [])
        if isinstance(c, dict)
    ) or "<p class='lv-muted'>No direct competitors listed.</p>"

    pivots = "".join(
        f"<div class='lv-card-item'><div class='lv-item-head'><strong>{_esc(p.get('title'))}</strong>"
        f"<span class='lv-pill'>{_esc(p.get('impact', 'medium'))} Impact · {_esc(p.get('effort', 'medium'))} Effort</span></div>"
        f"<p>{_esc(p.get('why_it_matters'))}</p>"
        f"<p class='lv-muted'><strong>How:</strong> {_esc(p.get('how'))}</p></div>"
        for p in (report.get("pivots") or [])
        if isinstance(p, dict)
    ) or "<p class='lv-muted'>No viable pivots suggested.</p>"

    pr = report.get("pricing_recommendation") or {}
    pricing_html = (
        f"<div class='lv-card-item'><div class='lv-item-head'><strong>{_esc(pr.get('suggested_price') or 'N/A')}</strong>"
        f"<span class='lv-pill'>{_esc(pr.get('model') or 'Pricing')}</span></div>"
        f"<p class='lv-muted' style='margin:0'>{_esc(pr.get('reasoning') or '')}</p></div>"
        if pr
        else "<p class='lv-muted'>No pricing recommendation generated.</p>"
    )

    mp = report.get("marketing_playbook") or {}
    if mp:
        hangouts = "".join(f"<span class='lv-pill'>{_esc(h)}</span> " for h in (mp.get("where_buyers_hang_out") or []))
        channels = "".join(
            f"<div class='lv-card-item'><div class='lv-item-head'><strong>{_esc(ch.get('channel'))}</strong></div>"
            f"<p style='margin:0 0 6px'>{_esc(ch.get('why'))}</p>"
            f"<p class='lv-muted' style='margin:0'><strong>Day-1 Step:</strong> {_esc(ch.get('first_step'))}</p></div>"
            for ch in (mp.get("distribution_channels") or [])
            if isinstance(ch, dict)
        )
        trap = (
            f"<p class='lv-muted' style='margin:0 0 10px'><strong>⚠️ Biggest Trap:</strong> {_esc(mp.get('biggest_distribution_trap'))}</p>"
            if mp.get("biggest_distribution_trap")
            else ""
        )
        marketing_html = (
            f"<div class='meta' style='margin-bottom:10px'><span class='lv-pill'>Difficulty: {_esc(mp.get('difficulty') or 'Hard')}</span>{hangouts}</div>"
            f"{trap}{channels}"
        )
    else:
        marketing_html = "<p class='lv-muted'>No marketing playbook generated.</p>"

    le = report.get("liability_and_entity") or {}
    if le:
        prot = "".join(f"<li>🛡️ {_esc(p)}</li>" for p in (le.get("must_have_protections") or []))
        liability_html = (
            f"<div class='lv-card-item'><div class='lv-item-head'><strong>{_esc(le.get('recommendation') or 'Personal / Indie')}</strong>"
            f"<span class='lv-pill'>Risk: {_esc(le.get('risk_level') or 'Low')}</span></div>"
            f"<p style='margin:0 0 8px'>{_esc(le.get('reasoning') or '')}</p>"
            + (f"<ul>{prot}</ul>" if prot else "")
            + "<p class='lv-muted' style='margin:6px 0 0;font-size:.76rem'>Informational only — not legal or tax advice.</p></div>"
        )
    else:
        liability_html = "<p class='lv-muted'>No entity/liability assessment generated.</p>"

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>LetsVibe: Reality Check — {_esc(report.get('headline'))}</title>
<style>
  :root {{ --bg:#0b1120; --card:#111827; --border:#1f2937; --text:#e5e7eb; --muted:#94a3b8; --cyan:#22d3ee; }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; padding:24px; background:var(--bg); color:var(--text); font-family:Inter,system-ui,-apple-system,sans-serif; line-height:1.55; }}
  .wrap {{ max-width:1040px; margin:0 auto; display:grid; gap:18px; }}
  .card {{ background:var(--card); border:1px solid var(--border); border-radius:14px; padding:20px; }}
  .hero {{ display:flex; justify-content:space-between; align-items:center; gap:20px; flex-wrap:wrap; }}
  .grade {{ text-align:center; min-width:170px; padding:14px 18px; border-radius:14px; background:rgba(15,23,42,.9); border:2px solid {accent}; }}
  .grade .letter {{ font-size:1.25rem; font-weight:900; color:{accent}; line-height:1.2; }}
  .grade .pts {{ font-size:1.35rem; font-weight:800; color:var(--text); margin-top:4px; }}
  .grade .scale-tag {{ font-size:.74rem; color:var(--cyan); margin-top:4px; font-weight:600; }}
  h1 {{ margin:0 0 6px; font-size:1.55rem; }}
  h2 {{ margin:0 0 12px; font-size:1.12rem; color:#f8fafc; }}
  .meta {{ color:var(--muted); font-size:.86rem; display:flex; gap:10px; flex-wrap:wrap; align-items:center; }}
  .grid2 {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(320px,1fr)); gap:18px; }}
  table {{ width:100%; border-collapse:collapse; font-size:.88rem; }}
  th, td {{ text-align:left; padding:10px 8px; border-bottom:1px solid var(--border); vertical-align:top; }}
  th {{ color:var(--muted); font-weight:600; font-size:.78rem; text-transform:uppercase; }}
  .lv-bar {{ width:76px; height:5px; background:rgba(148,163,184,.18); border-radius:999px; margin-top:5px; overflow:hidden; }}
  .lv-bar-fill {{ height:100%; background:linear-gradient(90deg,#22d3ee,#34d399); border-radius:999px; }}
  .lv-pill {{ display:inline-block; font-size:.74rem; padding:2px 8px; border-radius:999px; background:rgba(34,211,238,.12); color:var(--cyan); border:1px solid rgba(34,211,238,.28); }}
  .lv-card-item {{ padding:12px; border:1px solid var(--border); border-radius:10px; background:rgba(15,23,42,.55); margin-bottom:10px; }}
  .lv-item-head {{ display:flex; justify-content:space-between; gap:8px; align-items:center; flex-wrap:wrap; margin-bottom:6px; }}
  .lv-muted {{ color:var(--muted); font-size:.86rem; }}
  .card-solid {{ border-left:4px solid #34d399; }}
  .card-warn {{ border-left:4px solid #f87171; }}
  ul {{ margin:0; padding-left:18px; }}
  li {{ margin-bottom:6px; }}
  .footer {{ text-align:center; color:var(--muted); font-size:.82rem; padding:8px 0 14px; }}
  .footer a {{ color:var(--cyan); text-decoration:none; }}
</style>
</head>
<body>
<div class="wrap">
  <div class="card hero">
    <div style="flex:1;min-width:260px">
      <div class="meta">
        <span><strong>LetsVibe: Reality Check</strong></span>
        <span>• Platform: {_esc(report.get('platform'))}</span>
        <span>• Saturation: {float(report.get('saturation_pct') or 0):.0f}%</span>
        <span>• Tier: {_esc(report.get('demand_tier'))}</span>
        <span>• Est. Waste: {_esc(report.get('wasted_hours_estimate'))} / {_esc(report.get('wasted_tokens_estimate'))}</span>
      </div>
      <h1>{_esc(report.get('headline'))}</h1>
      <p style="margin:10px 0 0;color:#cbd5e1;white-space:pre-line">{_esc(report.get('executive_summary'))}</p>
    </div>
    <div class="grade">
      <div class="letter">{_esc(verdict)}</div>
      <div class="pts">{float(report.get('viability_score') or 0):.1f} / 10</div>
      <div class="scale-tag">Viability Score</div>
    </div>
  </div>

  <div class="card">
    <h2>📊 6-Dimension Reality Breakdown</h2>
    <table>
      <thead><tr><th>Dimension</th><th>Weight</th><th>Score</th><th>Detailed Analysis</th></tr></thead>
      <tbody>{dim_rows}</tbody>
    </table>
  </div>

  <div class="grid2">
    <div class="card card-warn">
      <h2 style="color:#f87171">⚠️ Fatal Flaws &amp; Friction</h2>
      <ul>{flaws}</ul>
    </div>
    <div class="card card-solid">
      <h2 style="color:#34d399">💎 Redeeming Angles</h2>
      <ul>{redeeming}</ul>
    </div>
  </div>

  <div class="card">
    <h2>💵 Pricing &amp; Market Cost Reality</h2>
    {pricing_html}
  </div>

  <div class="card">
    <h2>📣 How to Market It — The Actual Hard Part</h2>
    {marketing_html}
  </div>

  <div class="card">
    <h2>⚖️ Personal Publish vs. LLC (Liability Check)</h2>
    {liability_html}
  </div>

  <div class="card">
    <h2>🏁 Existing Competitors &amp; Incumbents</h2>
    {comps}
  </div>

  <div class="card">
    <h2>🧭 Viable Pivots / Alternatives</h2>
    {pivots}
  </div>

  <div class="footer">
    <div>LetsVibe: Reality Check uses AI, AI can make mistakes.</div>
    Generated by <strong>LetsVibe: Reality Check</strong> (<a href="https://letsviberc.todd0042.dev">LetsVibeRC.todd0042.dev</a>) ·
    Companion to <a href="https://letsvibe.todd0042.dev">LetsVibe Code Auditor</a>
  </div>
</div>
</body>
</html>"""
