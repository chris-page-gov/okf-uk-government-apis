#!/usr/bin/env python3
"""Build the separate source-linked OKF core walkthrough."""

from __future__ import annotations

import hashlib
import html
import json
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "bundle"
SOURCE = ROOT / "walkthroughs" / "core-catalogue.json"
CORE_ID = "https://chris-page-gov.github.io/okf-uk-government-apis/okf-core-explorer.json"
EXPLORER = "https://chris-page-gov.github.io/okf-explorer/explore/?bundle="


def _diagram(*, mobile: bool, traversal: dict[str, object]) -> str:
    if mobile:
        width, height = 390, 790
        left, card_width = 24, 342
        cards = [(left, 140, card_width, 220), (left, 410, card_width, 220)]
        note_y = 685
        edge = '<path d="M195 366 L195 392" stroke="#52667a" stroke-width="3" marker-end="url(#arrow)"/>'
    else:
        width, height = 1120, 510
        cards = [(40, 142, 455, 205), (625, 142, 455, 205)]
        note_y = 422
        edge = '<path d="M500 244 L610 244" stroke="#52667a" stroke-width="3" marker-end="url(#arrow)"/>'
    source, target = (traversal["source_path"], traversal["target_path"])
    text = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        '<title id="title">Follow the authored Notify provider link</title>',
        '<desc id="desc">A typed GOV.UK Notify source concept points to a Government Digital Service concept through an authored Markdown link. The link does not prove present availability or rights.</desc>',
        '<defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L0,6 L6,3 z" fill="#52667a"/></marker></defs>',
        '<rect width="100%" height="100%" rx="24" fill="#f4f7fb"/>',
    ]
    if mobile:
        text.extend([
            '<text x="22" y="39" font-family="system-ui,sans-serif" font-size="20" font-weight="700" fill="#172b4d">A source link is not a</text>',
            '<text x="22" y="63" font-family="system-ui,sans-serif" font-size="20" font-weight="700" fill="#172b4d">live-service check</text>',
            '<text x="22" y="91" font-family="system-ui,sans-serif" font-size="13" fill="#334e68">OKF core 0.3 · snapshot: 16 July 2026</text>',
            '<text x="22" y="111" font-family="system-ui,sans-serif" font-size="13" fill="#334e68">Authored Markdown only</text>',
        ])
    else:
        text.extend([
            '<text x="28" y="48" font-family="system-ui,sans-serif" font-size="25" font-weight="700" fill="#172b4d">A source link is not a live-service check</text>',
            '<text x="28" y="82" font-family="system-ui,sans-serif" font-size="15" fill="#334e68">OKF core 0.3 · frozen catalogue snapshot: 16 July 2026 · authored Markdown only</text>',
        ])
    labels = [
        ("GOV.UK Notify", "API Product concept", source, "Access unknown · licence not specified"),
        ("Government Digital Service", "Organisation concept", target, "Authored Markdown link target"),
    ]
    if mobile:
        mobile_rows = [
            (["GOV.UK Notify"], ["API Product concept"], ["api-records/government-digital-", "service-gov-uk-notify.md"], ["Access unknown · licence", "not specified"]),
            (["Government Digital", "Service"], ["Organisation concept"], ["organisations/government-digital-", "service.md"], ["Authored Markdown link", "target"]),
        ]
        for (x, y, w, h), (title_lines, subtitle_lines, route_lines, caveat_lines) in zip(cards, mobile_rows, strict=True):
            text.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="16" fill="#ffffff" stroke="#3264a8" stroke-width="3"/>')
            for index, line in enumerate(title_lines):
                text.append(f'<text x="{x+18}" y="{y+34+index*22}" font-family="system-ui,sans-serif" font-size="18" font-weight="700" fill="#172b4d">{html.escape(line)}</text>')
            for index, line in enumerate(subtitle_lines):
                text.append(f'<text x="{x+18}" y="{y+81+index*20}" font-family="system-ui,sans-serif" font-size="14" fill="#334e68">{html.escape(line)}</text>')
            for index, line in enumerate(route_lines):
                text.append(f'<text x="{x+18}" y="{y+120+index*18}" font-family="system-ui,sans-serif" font-size="12" fill="#334e68">{html.escape(line)}</text>')
            for index, line in enumerate(caveat_lines):
                text.append(f'<text x="{x+18}" y="{y+174+index*18}" font-family="system-ui,sans-serif" font-size="13" font-weight="700" fill="#842029">{html.escape(line)}</text>')
        text.extend([
            edge,
            f'<text x="22" y="{note_y}" font-family="system-ui,sans-serif" font-size="14" font-weight="700" fill="#842029">No endpoint check · no access or licence upgrade</text>',
            f'<text x="22" y="{note_y+20}" font-family="system-ui,sans-serif" font-size="14" font-weight="700" fill="#842029">No equivalence claim</text>',
            f'<text x="22" y="{note_y+51}" font-family="system-ui,sans-serif" font-size="12" fill="#334e68">The arrow is the exact authored source link;</text>',
            f'<text x="22" y="{note_y+68}" font-family="system-ui,sans-serif" font-size="12" fill="#334e68">no metadata-extension relationship is used.</text>',
            '</svg>',
        ])
    else:
        for (x, y, w, h), (title, subtitle, route, caveat) in zip(cards, labels, strict=True):
            text.extend([
                f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="16" fill="#ffffff" stroke="#3264a8" stroke-width="3"/>',
                f'<text x="{x+20}" y="{y+42}" font-family="system-ui,sans-serif" font-size="20" font-weight="700" fill="#172b4d">{html.escape(title)}</text>',
                f'<text x="{x+20}" y="{y+76}" font-family="system-ui,sans-serif" font-size="15" fill="#334e68">{html.escape(subtitle)}</text>',
                f'<text x="{x+20}" y="{y+116}" font-family="system-ui,sans-serif" font-size="13" fill="#334e68">{html.escape(route)}</text>',
                f'<text x="{x+20}" y="{y+155}" font-family="system-ui,sans-serif" font-size="14" font-weight="700" fill="#842029">{html.escape(caveat)}</text>',
            ])
        text.extend([
            edge,
            f'<text x="28" y="{note_y}" font-family="system-ui,sans-serif" font-size="16" font-weight="700" fill="#842029">No endpoint health check · no access or licence upgrade · no equivalence claim</text>',
            '<text x="28" y="' + str(note_y + 34) + '" font-family="system-ui,sans-serif" font-size="14" fill="#334e68">The boxes are typed Markdown concepts; the arrow is the exact authored source link.</text>',
            '</svg>',
        ])
    return "\n".join(text) + "\n"


def build() -> dict[str, object]:
    spec = json.loads(SOURCE.read_text(encoding="utf-8"))
    core_path = BUNDLE / "okf-core-explorer.json"
    core_bytes = core_path.read_bytes()
    core = json.loads(core_bytes)
    if core.get("bundle_id") != CORE_ID:
        raise ValueError("core descriptor identity differs from the authored walkthrough")
    source_nodes = core.get("nodes", {})
    sources = []
    for source in spec["sources"]:
        path = str(source["path"])
        data = (BUNDLE / path).read_bytes()
        node = source_nodes.get(path)
        if not isinstance(node, dict):
            raise ValueError(f"walkthrough source is not in the typed core projection: {path}")
        digest = hashlib.sha256(data).hexdigest()
        if node.get("source_sha256") != digest or node.get("source_bytes") != len(data):
            raise ValueError(f"core projection source identity differs from source bytes: {path}")
        sources.append({
            "path": path,
            "label": source["label"],
            "role": source["role"],
            "bytes": len(data),
            "sha256": digest,
        })
    traversal_spec = spec["traversal"]
    source_node = source_nodes.get(traversal_spec["source_path"], {})
    expected_link = traversal_spec["source_link"]
    if source_node.get("markdown_links", {}).get(expected_link) != traversal_spec["target_path"]:
        raise ValueError("core walkthrough provider link is not authored in the frozen source Markdown")
    matches = [
        edge for edge in core.get("edges", [])
        if edge.get("source") == traversal_spec["source_path"]
        and edge.get("target") == traversal_spec["target_path"]
        and edge.get("kind") == traversal_spec["kind"]
        and edge.get("source_fields") == traversal_spec["source_fields"]
    ]
    if len(matches) != 1:
        raise ValueError(f"expected one authored core provider link; found {len(matches)}")
    traversal = {
        **traversal_spec,
        "edge": matches[0],
    }
    reader_url = (
        EXPLORER
        + quote(CORE_ID, safe="")
        + "&q=" + quote(spec["search_query"], safe="")
        + "&view=reader"
        + "#" + traversal_spec["source_path"]
    )
    evidence = {
        "schema": "okf-core-walkthrough-evidence.v1",
        "id": spec["id"],
        "bundle_id": CORE_ID,
        "version": core["version"],
        "snapshot": core["snapshot"],
        "question": spec["question"],
        "scope": spec["scope"],
        "answer": spec["answer"],
        "decision": spec["decision"],
        "core_projection": {
            "path": "okf-core-explorer.json",
            "sha256": hashlib.sha256(core_bytes).hexdigest(),
            "concept_count": len(source_nodes),
            "edge_count": len(core.get("edges", [])),
        },
        "sources": sources,
        "traversal": traversal,
        "negative_controls": spec["negative_controls"],
        "reader_url": reader_url,
        "claims": {
            "metadata_extension_graph_used": False,
            "live_availability_checked": False,
            "live_api_called": False,
            "licence_permission_inferred": False,
            "identity_equivalence_inferred": False,
        },
    }
    cards = "".join(
        '<li><a href="' + html.escape(source["path"], quote=True) + '">' + html.escape(source["label"])
        + '</a><span class="role">' + html.escape(source["role"]) + '</span><code>SHA-256 '
        + source["sha256"] + '</code></li>'
        for source in sources
    )
    answers = "".join("<p>" + html.escape(item) + "</p>" for item in spec["answer"])
    negatives = "".join("<li>" + html.escape(item) + "</li>" for item in spec["negative_controls"])
    desktop_svg = _diagram(mobile=False, traversal=traversal_spec)
    mobile_svg = _diagram(mobile=True, traversal=traversal_spec)
    html_page = f'''<!doctype html>
<html lang="en-GB"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="icon" href="data:,">
<title>{html.escape(spec['title'])}</title><style>
:root{{color-scheme:light;--ink:#172b4d;--muted:#334e68;--line:#d8e1ed;--blue:#1d4f91;--amber:#805400;--red:#842029;--paper:#fff}}
*{{box-sizing:border-box}}body{{margin:0;background:#f4f7fb;color:var(--ink);font:17px/1.6 system-ui,-apple-system,sans-serif}}
main{{max-width:1040px;margin:auto;padding:2rem 1.2rem 4rem}}h1{{font-size:clamp(2rem,5vw,3.15rem);line-height:1.1;max-width:22ch}}h2{{font-size:1.45rem}}
.panel{{background:var(--paper);border:1px solid var(--line);border-radius:16px;padding:1.25rem;margin:1.2rem 0;box-shadow:0 4px 18px #102a430d}}.answer{{border-left:6px solid #3264a8}}.decision{{border-left:6px solid var(--red);background:#fff7f7}}
a{{color:var(--blue);text-underline-offset:.18em}}a:focus-visible{{outline:3px solid #ffbf47;outline-offset:3px}}.role{{display:block;color:var(--muted);font-size:.9rem}}code{{overflow-wrap:anywhere}}
.diagram img{{display:block;width:100%;height:auto;background:#fff;border:1px solid var(--line);border-radius:12px}}ul.sources{{padding-left:1.4rem}}@media(max-width:760px){{main{{padding:1.1rem .8rem 3rem}}}}
</style></head><body><main>
<p class="eyebrow">UK Government APIs · OKF core 0.3 · frozen Markdown only</p>
<p><a href="index.html">Bundle homepage</a> · <a href="{html.escape(reader_url, quote=True)}">Open GOV.UK Notify in the core Reader</a> · <a href="core-reader-journeys.json">Replay the core Reader journeys</a></p>
<h1>{html.escape(spec['title'])}</h1>
<section class="panel"><h2>Question</h2><p>{html.escape(spec['question'])}</p><p>{html.escape(spec['scope'])}</p></section>
<section class="panel answer"><h2>Worked answer from the core sources</h2>{answers}<p class="decision"><strong>Decision boundary:</strong> {html.escape(spec['decision'])}</p></section>
<section class="panel diagram"><h2>Follow the authored core link</h2><picture><source media="(max-width: 760px)" srcset="core-walkthrough-mobile.svg"><img src="core-walkthrough-desktop.svg" alt="The GOV.UK Notify Markdown concept links to a Government Digital Service concept; current availability and rights remain unverified"></picture><p>The core projection has {len(source_nodes):,} typed Markdown concepts and {len(core.get('edges', [])):,} authored reference edges. This walkthrough uses one exact source-linked path; no metadata-extension relationship is read.</p></section>
<section class="panel"><h2>Exact sources</h2><ul class="sources">{cards}</ul><p>Core descriptor SHA-256: <code>{hashlib.sha256(core_bytes).hexdigest()}</code></p></section>
<section class="panel"><h2>Negative controls</h2><ul>{negatives}</ul><p>No live API call, availability check or paid language-model call was made.</p></section>
</main></body></html>
'''
    (BUNDLE / "core-walkthrough.html").write_text(html_page, encoding="utf-8")
    (BUNDLE / "core-walkthrough-desktop.svg").write_text(desktop_svg, encoding="utf-8")
    (BUNDLE / "core-walkthrough-mobile.svg").write_text(mobile_svg, encoding="utf-8")
    (BUNDLE / "core-walkthrough-evidence.json").write_text(
        json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return evidence


if __name__ == "__main__":
    result = build()
    print(f"built source-linked core walkthrough for {len(result['sources'])} exact inputs")
