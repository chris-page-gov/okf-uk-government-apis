#!/usr/bin/env python3
"""Build the source-linked Notify walkthrough from frozen bundle records."""

from __future__ import annotations

import hashlib
import html
import json
import re
import gzip
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "bundle"
SOURCE = ROOT / "walkthroughs" / "notification-catalogue.json"


def read_source(path: str) -> tuple[Path, str, str]:
    target = BUNDLE / path
    content = target.read_bytes()
    text = content.decode("utf-8")
    digest = hashlib.sha256(content).hexdigest()
    return target, text, digest


def find_assertion(source: str, target: str, predicate: str) -> dict[str, object]:
    """Return the exact frozen metadata assertion for the authored route path."""
    semantic_root = BUNDLE / "data" / "semantic"
    matches = []
    for path in sorted(semantic_root.glob("assertions-*.jsonld.gz")):
        graph = json.loads(gzip.decompress(path.read_bytes()))
        for row in graph.get("@graph", []):
            predicate_value = row.get("predicate")
            predicate_iri = predicate_value.get("@id") if isinstance(predicate_value, dict) else predicate_value
            if (
                row.get("source_route") == source
                and row.get("target_route") == target
                and predicate_iri == predicate
            ):
                matches.append(row)
    if len(matches) != 1:
        raise ValueError(
            f"expected one frozen metadata assertion for {source} -> {target} ({predicate}); found {len(matches)}"
        )
    row = matches[0]
    return {
        "id": row["@id"],
        "source_route": row["source_route"],
        "target_route": row["target_route"],
        "predicate": predicate,
        "label": row.get("label"),
        "assertion_status": row.get("assertion_status"),
        "assertion_scope": row.get("assertion_scope"),
    }


def _render_svg(*, mobile: bool) -> str:
    if mobile:
        width, height = 390, 950
        boxes = [(20, 150, 350, 210), (20, 400, 350, 210), (20, 650, 350, 210)]
        arrows = [(195, 365, 195, 390), (195, 615, 195, 640)]
    else:
        width, height = 1120, 510
        boxes = [(35, 125, 325, 210), (398, 125, 325, 210), (761, 125, 325, 210)]
        arrows = [(362, 230, 390, 230), (725, 230, 753, 230)]
    titles = ["GOV.UK Notify", "GOVUK Notify", "Government Notify"]
    subtitles = [
        ["Government Digital Service", "Endpoint recorded", "Access unknown · licence not specified"],
        ["Department for Work and Pensions", "No endpoint in this record", "ISC declared for this record only"],
        ["Wayfinder fictional catalogue", ".example endpoint · synthetic", "Rights not specified · excluded from live admission"],
    ]
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        '<title id="title">Three distinct Notify catalogue records</title>',
        '<desc id="desc">Compare two GOV.UK API Catalogue records and one Wayfinder synthetic record. A connecting line marks comparison only, not equivalence.</desc>',
        '<defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L0,6 L6,3 z" fill="#52667a"/></marker></defs>',
        '<rect width="100%" height="100%" rx="24" fill="#f4f7fb"/>',
    ]
    if mobile:
        out.extend([
            '<text x="22" y="39" font-family="system-ui,sans-serif" font-size="21" font-weight="700" fill="#172b4d">A name match is not an</text>',
            '<text x="22" y="64" font-family="system-ui,sans-serif" font-size="21" font-weight="700" fill="#172b4d">identity match</text>',
            '<text x="22" y="92" font-family="system-ui,sans-serif" font-size="13" fill="#334e68">Catalogue snapshot: 16 July 2026</text>',
            '<text x="22" y="111" font-family="system-ui,sans-serif" font-size="13" fill="#334e68">Synthetic capture: 24 September 2026</text>',
        ])
    else:
        out.extend([
            '<text x="28" y="48" font-family="system-ui,sans-serif" font-size="26" font-weight="700" fill="#172b4d">A name match is not an identity match</text>',
            '<text x="28" y="80" font-family="system-ui,sans-serif" font-size="15" fill="#334e68">Real-world catalogue snapshot: 16 July 2026 · synthetic overlay capture: 24 September 2026</text>',
        ])
    if mobile:
        mobile_subtitles = [
            ["Government Digital Service", "Endpoint recorded", "Access unknown · licence", "not specified"],
            ["Department for Work and", "Pensions", "No endpoint in this record", "Access unknown", "ISC declared for this record only"],
            ["Wayfinder fictional catalogue", ".example endpoint · synthetic", "Rights not specified", "Excluded from live admission"],
        ]
        for i, (x, y, w, h) in enumerate(boxes):
            fill, stroke = ("#ffffff", "#3264a8") if i < 2 else ("#fff8e6", "#a76b00")
            out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="16" fill="{fill}" stroke="{stroke}" stroke-width="3"/>')
            out.append(f'<text x="{x+18}" y="{y+34}" font-family="system-ui,sans-serif" font-size="18" font-weight="700" fill="#172b4d">{html.escape(titles[i])}</text>')
            for j, line in enumerate(mobile_subtitles[i]):
                out.append(f'<text x="{x+18}" y="{y+72+j*23}" font-family="system-ui,sans-serif" font-size="14" fill="#334e68">{html.escape(line)}</text>')
            label = "catalogue record" if i < 2 else "negative control"
            out.append(f'<text x="{x+18}" y="{y+h-15}" font-family="system-ui,sans-serif" font-size="12" font-weight="700" fill="{stroke}">{label.upper()}</text>')
    else:
        for i, (x, y, w, h) in enumerate(boxes):
            fill, stroke = ("#ffffff", "#3264a8") if i < 2 else ("#fff8e6", "#a76b00")
            out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="16" fill="{fill}" stroke="{stroke}" stroke-width="3"/>')
            out.append(f'<text x="{x+18}" y="{y+35}" font-family="system-ui,sans-serif" font-size="19" font-weight="700" fill="#172b4d">{html.escape(titles[i])}</text>')
            for j, line in enumerate(subtitles[i]):
                out.append(f'<text x="{x+18}" y="{y+75+j*34}" font-family="system-ui,sans-serif" font-size="14" fill="#334e68">{html.escape(line)}</text>')
            label = "catalogue record" if i < 2 else "negative control"
            out.append(f'<text x="{x+18}" y="{y+h-18}" font-family="system-ui,sans-serif" font-size="12" font-weight="700" fill="{stroke}">{label.upper()}</text>')
    for x1, y1, x2, y2 in arrows:
        out.append(f'<path d="M{x1},{y1} L{x2},{y2}" stroke="#52667a" stroke-width="3" marker-end="url(#arrow)"/>')
    if mobile:
        out.extend([
            '<text x="22" y="900" font-family="system-ui,sans-serif" font-size="14" font-weight="700" fill="#842029">Do not transfer licence, endpoint or</text>',
            '<text x="22" y="921" font-family="system-ui,sans-serif" font-size="14" font-weight="700" fill="#842029">live-service claims between records.</text>',
            '</svg>',
        ])
    else:
        out.extend([
            '<text x="28" y="' + str(height-45) + '" font-family="system-ui,sans-serif" font-size="14" font-weight="700" fill="#842029">Do not transfer licence, endpoint or live-service claims between records.</text>',
            '</svg>',
        ])
    return "\n".join(out) + "\n"


def build() -> dict[str, object]:
    spec = json.loads(SOURCE.read_text(encoding="utf-8"))
    descriptor = json.loads((BUNDLE / "okf-explorer.json").read_text(encoding="utf-8"))
    sources = []
    for source in spec["sources"]:
        target, text, digest = read_source(source["path"])
        sources.append({**source, "bytes": target.stat().st_size, "sha256": digest})
        if source["path"].endswith("government-digital-service-gov-uk-notify.md"):
            required = ["title: \"GOV.UK Notify\"", "Access model: unknown", "Licence: Not specified", "documentation-only"]
        elif source["path"].endswith("department-for-work-and-pensions-govuk-notify.md"):
            required = ["title: \"GOVUK Notify\"", "Access model: unknown", "Licence: isc (isc)", "undocumented-in-catalogue"]
        elif source["path"].endswith("wayfinder-demo-gov-notify.md"):
            required = ["synthetic_demo", "Rights not specified", ".example"]
        else:
            required = ["synthetic-fixture-opt-in", "not specified"]
        if any(term.casefold() not in text.casefold() for term in required):
            raise ValueError(f"walkthrough assertions do not match source: {source['path']}")
    metadata_id = descriptor["@id"]
    traversal_spec = spec["traversal"]
    graph_path = find_assertion(
        traversal_spec["source_route"],
        traversal_spec["target_route"],
        traversal_spec["predicate"],
    )
    if graph_path["id"] != traversal_spec["assertion_id"]:
        raise ValueError("walkthrough graph assertion identity differs from its frozen source specification")
    metadata_url = "https://chris-page-gov.github.io/okf-explorer/explore/?bundle=" + quote(metadata_id, safe="")
    metadata_url += "&q=" + quote(traversal_spec["search_query"], safe="")
    metadata_url += "&view=reader"
    metadata_url += "#" + traversal_spec["source_route"]
    reader_url = (
        metadata_url
    )
    guide = {
        "schema": "okf-api-walkthrough-evidence.v1",
        "id": spec["id"],
        "bundle_id": metadata_id,
        "version": descriptor["version"],
        "snapshot": descriptor["snapshot"],
        "question": spec["question"],
        "scope": spec["scope"],
        "answer": spec["answer"],
        "decision": spec["decision"],
        "reader_boundary": spec["reader_boundary"],
        "sources": sources,
        "metadata_graph_path": graph_path,
        "metadata_extension_descriptor": {
            "path": "okf-explorer.json",
            "bundle_id": metadata_id,
            "sha256": hashlib.sha256((BUNDLE / "okf-explorer.json").read_bytes()).hexdigest(),
            "version": descriptor["version"],
            "snapshot": descriptor["snapshot"],
        },
        "traversal": spec["traversal"],
        "negative_controls": spec["negative_controls"],
        "reader_url": reader_url,
        "claims": {
            "live_availability_checked": False,
            "live_api_called": False,
            "licence_applies_only_to_named_source_record": True,
            "wayfinder_admitted_as_real_service": False,
        },
    }
    card_html = []
    for source in sources:
        card_html.append(
            '<li><a href="' + html.escape(source["path"], quote=True) + '">'
            + html.escape(source["label"]) + '</a><span class="role">'
            + html.escape(source["role"]) + '</span><code>SHA-256 '
            + source["sha256"] + '</code></li>'
        )
    answer_html = "".join("<p>" + html.escape(line) + "</p>" for line in spec["answer"])
    negative_html = "".join("<li>" + html.escape(line) + "</li>" for line in spec["negative_controls"])
    svg_desktop = _render_svg(mobile=False)
    svg_mobile = _render_svg(mobile=True)
    html_document = f'''<!doctype html>
<html lang="en-GB"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(spec['title'])}</title><style>
:root{{color-scheme:light;--ink:#172b4d;--muted:#334e68;--line:#d8e1ed;--blue:#1d4f91;--amber:#805400;--red:#842029;--paper:#fff}}
*{{box-sizing:border-box}}body{{margin:0;background:#f4f7fb;color:var(--ink);font:17px/1.6 system-ui,-apple-system,sans-serif}}
main{{max-width:1040px;margin:auto;padding:2rem 1.2rem 4rem}}h1{{font-size:clamp(2rem,5vw,3.25rem);line-height:1.1;max-width:18ch}}h2{{font-size:1.45rem}}
.lead,.panel{{background:var(--paper);border:1px solid var(--line);border-radius:16px;padding:1.25rem;margin:1.2rem 0;box-shadow:0 4px 18px #102a430d}}
.decision{{border-left:6px solid var(--red);background:#fff7f7}}.facts{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:1rem}}
.facts article{{background:var(--paper);border:1px solid var(--line);border-top:5px solid var(--blue);border-radius:12px;padding:1rem;min-width:0}}
.facts article.synthetic{{border-top-color:var(--amber);background:#fffaf0}}.facts h3{{margin-top:.25rem}}a{{color:var(--blue);text-underline-offset:.18em}}a:focus-visible{{outline:3px solid #ffbf47;outline-offset:3px}}
.role{{display:block;color:var(--muted);font-size:.9rem}}code{{display:block;overflow-wrap:anywhere;font-size:.78rem;margin-top:.5rem}}
.diagrams{{display:grid;grid-template-columns:1fr 1fr;gap:1rem}}.diagrams img{{display:block;width:100%;height:auto;background:white;border-radius:12px;border:1px solid var(--line)}}
.caveat{{color:var(--muted)}}@media(max-width:760px){{main{{padding:1.1rem .8rem 3rem}}.facts,.diagrams{{grid-template-columns:1fr}}}}
</style></head><body><main>
<p class="eyebrow">UK Government APIs · source-linked walkthrough</p><h1>{html.escape(spec['title'])}</h1>
<section class="lead"><h2>Question</h2><p>{html.escape(spec['question'])}</p><p class="caveat">{html.escape(spec['scope'])}</p>
<p><a href="{html.escape(reader_url, quote=True)}">Open GOV.UK Notify in the metadata Explorer</a> · <a href="notification-reader-journeys.json">Replay the metadata Reader journeys</a></p></section>
<section class="facts" aria-label="Three records compared">
<article><h3>GOV.UK Notify</h3><p>Government Digital Service. The record reports an endpoint and a documentation URL; access is unknown, contract status is documentation-only and the licence is not specified.</p><p><a href="api-records/government-digital-service-gov-uk-notify.md">Read the source record</a></p></article>
<article><h3>GOVUK Notify</h3><p>Department for Work and Pensions. This record has no endpoint, says access is unknown and records an ISC licence for this entry only.</p><p><a href="api-records/department-for-work-and-pensions-govuk-notify.md">Read the source record</a></p></article>
<article class="synthetic"><h3>Government Notify</h3><p>Wayfinder comparison fixture. Its fictional endpoint and rights-not-specified state are not evidence about a live government service.</p><p><a href="api-records/wayfinder-demo-gov-notify.md">Read the synthetic record</a></p></article>
</section>
<section class="panel"><h2>Worked answer</h2>{answer_html}<p class="decision"><strong>Decision boundary:</strong> {html.escape(spec['decision'])}</p></section>
<section class="panel"><h2>Reader label note</h2><p>{html.escape(spec['reader_boundary'])}</p></section>
<section class="panel"><h2>Metadata graph path</h2><p>The frozen metadata graph links the GOV.UK Notify catalogue record to the Government Digital Service publisher using the source-backed “published by” assertion. This does not establish current availability or licence coverage.</p>
<p>Assertion <code>{html.escape(str(graph_path['id']))}</code> has status <code>{html.escape(str(graph_path['assertion_status']))}</code> and scope <code>{html.escape(str(graph_path['assertion_scope']))}</code>. Open the separate <a href="okf-core-explorer.json">3,464-concept OKF core projection</a> for authored Markdown sources; this walkthrough uses the <a href="okf-explorer.json">metadata extension descriptor</a>.</p></section>
<section class="panel"><h2>Visual comparison</h2><div class="diagrams"><img src="notification-walkthrough-desktop.svg" alt="Desktop diagram comparing the three Notify records and their differing evidence"><img src="notification-walkthrough-mobile.svg" alt="Mobile diagram comparing the three Notify records and their differing evidence"></div></section>
<section class="panel"><h2>Source trail</h2><ul>{''.join(card_html)}</ul></section>
<section class="panel"><h2>Negative controls</h2><ul>{negative_html}</ul><p class="caveat">No live API call, current availability check or legal assessment was performed.</p></section>
</main></body></html>\n'''
    (BUNDLE / "notification-catalogue-walkthrough.html").write_text(html_document, encoding="utf-8")
    (BUNDLE / "notification-walkthrough-desktop.svg").write_text(svg_desktop, encoding="utf-8")
    (BUNDLE / "notification-walkthrough-mobile.svg").write_text(svg_mobile, encoding="utf-8")
    (BUNDLE / "notification-walkthrough-evidence.json").write_text(
        json.dumps(guide, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return guide


if __name__ == "__main__":
    result = build()
    print(f"built source-linked walkthrough for {len(result['sources'])} exact inputs")
