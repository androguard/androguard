#!/usr/bin/env python3
"""Regenerate docs/mastg-coverage.md from the latest validate JSON.

Run after ``python scripts/mastg_validate.py`` (or ``--scan-only``).
This is the single human-readable MASTG coverage reference (checked into docs/).
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
REPORTS = REPO / "workspace" / "reports"
MASTG = REPO / "workspace" / "mastg-validation" / "mastg" / "demos" / "android"
EXPECTED = REPO / "scripts" / "mastg_expected.json"
OUT = REPO / "docs" / "mastg-coverage.md"

FRIDA_STATIC = {
    "MASTG-DEMO-0002": (
        "hit",
        "external_storage_write (+ logging/secrets) — Frida traces the same storage APIs.",
    ),
    "MASTG-DEMO-0027": (
        "hit",
        "device_lock_api_check — isDeviceSecure / canAuthenticate inventoried statically.",
    ),
    "MASTG-DEMO-0030": ("hit", "webview_file_access — insecure WebView content/file settings."),
    "MASTG-DEMO-0031": ("hit", "webview_file_access — local file access flags."),
    "MASTG-DEMO-0038": ("hit", "strict_mode_policy via DEMO-0037 sources."),
    "MASTG-DEMO-0058": ("hit", "weak_crypto (AES/ECB) — Frida only observes."),
    "MASTG-DEMO-0059": (
        "hit",
        "prefs_plaintext_secret — plaintext tokens in SharedPreferences.",
    ),
    "MASTG-DEMO-0060": (
        "n/a",
        "EncryptedSharedPreferences secure counterpart; prefs_plaintext_secret suppressed.",
    ),
    "MASTG-DEMO-0072": (
        "hit",
        "keystore_multipurpose via DEMO-0071 (sign+encrypt paddings).",
    ),
    "MASTG-DEMO-0081": (
        "partial",
        "tracker_fingerprint_api inventories analytics; not event PII payloads.",
    ),
    "MASTG-DEMO-0082": (
        "partial",
        "webview_javascript_interface related; not WebStorage cleanup.",
    ),
    "MASTG-DEMO-0088": (
        "partial",
        "rce_dynamic_loading from root-check exec surfaces in 0087.",
    ),
    "MASTG-DEMO-0106": (
        "hit",
        "hardcoded_crypto_secret — API key + Cipher.doFinal (hookable statically).",
    ),
    "MASTG-DEMO-0107": ("hit", "anti_frida_maps — /proc/self/maps + frida/gadget."),
    "MASTG-DEMO-0108": (
        "hit",
        "Same anti-Frida surface as 0107 (bypass itself is dynamic).",
    ),
    "MASTG-DEMO-0114": (
        "hit",
        "emulator_detection — Build.* + emulator package/string markers.",
    ),
    "MASTG-DEMO-0139": (
        "partial",
        "implicit_intent_* on provider flow; path_traversal still weak.",
    ),
    "MASTG-DEMO-0158": ("hit", "webview_url_override from DEMO-0157 sources."),
}


def latest_validate_json() -> Path:
    cands = sorted(REPORTS.glob("mastg-scan-validate-*.json"))
    if not cands:
        raise SystemExit(f"no mastg-scan-validate-*.json under {REPORTS}")
    return cands[-1]


def title_of(d: Path) -> str:
    md = next(d.glob("MASTG-DEMO-*.md"), None)
    if not md:
        return ""
    m = re.search(r"^title:\s*(.+)$", md.read_text(errors="replace"), re.M)
    return m.group(1).strip().strip("\"'") if m else ""


def is_frida(d: Path) -> bool:
    files = {p.name for p in d.iterdir() if p.is_file()}
    md = next(d.glob("MASTG-DEMO-*.md"), None)
    text = md.read_text(errors="replace") if md else ""
    t = title_of(d).lower()
    return (
        "frida" in t
        or any(f.endswith(".js") for f in files)
        or ("hooks.json" in files and "frida" in text.lower())
    )


def main() -> int:
    vjson = latest_validate_json()
    rows = json.loads(vjson.read_text())
    by_id = {r["demo_id"]: r for r in rows}
    expected = json.loads(EXPECTED.read_text()).get("demos", {})
    demos = sorted(p for p in MASTG.rglob("MASTG-DEMO-*") if p.is_dir())
    day = date.today().isoformat()
    status_c = Counter(r["status"] for r in rows)
    frida_ids = [d.name for d in demos if is_frida(d)]
    fv = Counter(FRIDA_STATIC[i][0] for i in frida_ids if i in FRIDA_STATIC)

    lines = [
        "# MASTG coverage reference (Androguard scan_vulns)",
        "",
        f"**Updated:** {day}  ",
        "**Scope:** all 94 Android demos under "
        "[OWASP MASTG `demos/android`](https://github.com/OWASP/mastg/tree/master/demos/android), "
        "built via [mas-app-android](https://github.com/cpholguera/mas-app-android).",
        "",
        "This is the **single** reference document for MASTG ↔ Androguard security-scanner coverage "
        "(checked into `docs/`).",
        f"Machine JSON: `{vjson.relative_to(REPO)}`. Expectations: `scripts/mastg_expected.json`.",
        "",
        "## Overall status",
        "",
        "| status | count | meaning |",
        "|--------|------:|---------|",
        f"| pass | {status_c.get('pass', 0)} | Curated expectation matched |",
        f"| gap | {status_c.get('gap', 0)} | Scanned; lesson not yet curated / uncovered |",
        f"| skip | {status_c.get('skip', 0)} | No injectable sources |",
        f"| fail | {status_c.get('fail', 0)} | Expectation missed |",
        "",
        f"**Total:** {len(rows)} demos · **Frida-oriented:** {len(frida_ids)}",
        "",
        "## Frida demos — static detection",
        "",
        "Frida demos are those whose title/docs/scripts use Frida. "
        "`scan_vulns` assessment is whether the **lesson** is visible statically.",
        "",
        "| static | count |",
        "|--------|------:|",
        f"| hit | {fv.get('hit', 0)} |",
        f"| partial | {fv.get('partial', 0)} |",
        f"| miss | {fv.get('miss', 0)} |",
        f"| n/a | {fv.get('n/a', 0)} |",
        "",
        "| Demo | Title | Validate | Static | Categories | Assessment |",
        "|------|-------|----------|--------|------------|------------|",
    ]
    for did in sorted(frida_ids):
        r = by_id.get(did) or {}
        d = next(x for x in demos if x.name == did)
        st, detail = FRIDA_STATIC.get(did, ("?", "—"))
        cats = ", ".join(r.get("found_categories") or []) or "—"
        status = r.get("status") or "?"
        lines.append(
            f"| {did} | {title_of(d)[:48]} | `{status}` | **{st}** | `{cats}` | {detail} |"
        )

    lines += [
        "",
        "### Detector categories for former Frida misses",
        "",
        "| Category | Covers |",
        "|----------|--------|",
        "| `device_lock_api_check` | KeyguardManager.isDeviceSecure / BiometricManager.canAuthenticate |",
        "| `strict_mode_policy` | StrictMode.setVmPolicy / setThreadPolicy |",
        "| `prefs_plaintext_secret` | SharedPreferences putString* + secret markers (skips EncryptedSharedPreferences) |",
        "| `keystore_multipurpose` | KeyGenParameterSpec with both signature + encryption paddings |",
        "| `anti_frida_maps` | `/proc/self/maps` + frida/gadget string checks |",
        "| `emulator_detection` | Build.* reads + emulator fingerprint/package markers |",
        "| `hardcoded_crypto_secret` | Secret-like consts co-located with Cipher.doFinal |",
        "",
        "## All demos",
        "",
        "| Demo | MASVS | Status | Frida | Static | Found | Notes |",
        "|------|-------|--------|:-----:|--------|-------|-------|",
    ]
    for d in sorted(demos, key=lambda p: (p.parent.name, p.name)):
        r = by_id.get(d.name) or {"status": "?", "found_categories": [], "message": "missing from validate JSON"}
        fr = "yes" if is_frida(d) else ""
        st = FRIDA_STATIC[d.name][0] if d.name in FRIDA_STATIC else ""
        exp = expected.get(d.name, {})
        note = (exp.get("notes") or r.get("message") or "")[:70].replace("|", "/")
        found = ", ".join(r.get("found_categories") or []) or "—"
        lines.append(
            f"| {d.name} | {d.parent.name} | `{r.get('status', '?')}` | {fr} | {st} | `{found}` | {note} |"
        )

    lines += ["", "## Per-demo detail", ""]
    for d in sorted(demos, key=lambda p: p.name):
        r = by_id.get(d.name) or {
            "status": "?",
            "found_categories": [],
            "message": "missing from validate JSON",
            "source_mode": "?",
            "source_from": [],
            "apk": None,
        }
        exp = expected.get(d.name, {})
        lines += [
            f"### {d.name} — `{r['status']}`",
            "",
            f"- **Title:** {title_of(d)}",
            f"- **MASVS:** `{d.parent.name}`",
            f"- **Frida:** {'yes' if is_frida(d) else 'no'}",
        ]
        if d.name in FRIDA_STATIC:
            st, detail = FRIDA_STATIC[d.name]
            lines.append(f"- **Static (Frida lesson):** `{st}` — {detail}")
        lines += [
            f"- **Sources:** `{r.get('source_mode')}`"
            + (
                f" ← {', '.join(r.get('source_from') or [])}"
                if r.get("source_from")
                else ""
            ),
            f"- **expect_any:** `{exp.get('expect_any', [])}`",
            f"- **forbid:** `{exp.get('forbid', [])}`",
            f"- **Found:** `{r.get('found_categories') or []}`",
            f"- **Message:** {r.get('message')}",
            f"- **Notes:** {exp.get('notes') or '—'}",
            f"- **APK:** `{r.get('apk') or '—'}`",
            "",
        ]

    lines += [
        "## Reproduce",
        "",
        "```bash",
        "python scripts/mastg_validate.py --setup",
        "python scripts/mastg_validate.py",
        "python scripts/mastg_validate.py --scan-only",
        "python scripts/mastg_coverage_doc.py",
        "```",
        "",
    ]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n")
    print(f"wrote {OUT} ({OUT.stat().st_size} bytes)")
    print(
        "summary",
        dict(status_c),
        "frida_static",
        dict(fv),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
