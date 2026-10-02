#!/usr/bin/env python3
"""
Build ALL OWASP MASTG Android demos via mas-app-android and validate Androguard scan_vulns.

Covers every folder under demos/android (including Frida/docs demos that only
reference sibling sources via ``{{ ../MASTG-DEMO-XXXX/... }}``, e.g. MASTG-DEMO-0158).

Mirrors https://github.com/OWASP/mastg/.github/workflows/build-android-demos.yml:
inject demo sources into https://github.com/cpholguera/mas-app-android, assembleDebug,
then run Application.scan_vulns() and compare against scripts/mastg_expected.json.

Examples::

    python scripts/mastg_validate.py --setup
    python scripts/mastg_validate.py                 # ALL demos (default)
    python scripts/mastg_validate.py --mapped-only   # only curated expect_any entries
    python scripts/mastg_validate.py --only MASTG-DEMO-0158,MASTG-DEMO-0157
    python scripts/mastg_validate.py --sync-expected # fill expected.json for every demo id
    python scripts/mastg_validate.py --scan-only
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_WORK = REPO_ROOT / "workspace" / "mastg-validation"
EXPECTED_PATH = REPO_ROOT / "scripts" / "mastg_expected.json"
MASTG_DEMOS = "demos/android"
MAS_APP_REPO = "https://github.com/cpholguera/mas-app-android.git"
MASTG_REPO = "https://github.com/OWASP/mastg.git"

DEMO_ID_RE = re.compile(r"MASTG-DEMO-\d+")
INCLUDE_RE = re.compile(r"\{\{\s*([^}]+)\}\}")

# Files we can inject into mas-app-android (same set as MASTG CI + WebView helpers).
INJECT_FILES = (
    "MastgTest.kt",
    "MastgTestWebView.kt",
    "MainActivity.kt",
    "MainActivityWebView.kt",
    "AndroidManifest.xml",
    "filepaths.xml",
    "network_security_config.xml",
    "backup_rules.xml",
    "data_extraction_rules.xml",
    "proguard-rules.pro",
    "CMakeLists.txt",
)
INJECT_GLOBS = ("*.proto", "*.cpp", "build.gradle.kts.*")

FOCUS_CLASS_PREFIXES = (
    "org.owasp.mastestapp.MastgTest",
    "org.owasp.mastestapp.MastgTestWebView",
    "org.owasp.mastestapp.MainActivity",
)


@dataclass
class DemoResult:
    demo_id: str
    category: str
    title: str = ""
    status: str = "skip"  # pass | fail | gap | skip | build_error | scan_error
    build_ok: bool = False
    apk: str | None = None
    source_mode: str = ""  # local | sibling | reused_apk | none
    source_from: list[str] = field(default_factory=list)
    expected: list[str] = field(default_factory=list)
    forbid: list[str] = field(default_factory=list)
    found_categories: list[str] = field(default_factory=list)
    focused_findings: list[dict[str, Any]] = field(default_factory=list)
    message: str = ""
    elapsed_s: float = 0.0


def _run(
    cmd: list[str] | str,
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    check: bool = True,
    timeout: int | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        env=env,
        check=check,
        text=True,
        capture_output=True,
        timeout=timeout,
        shell=isinstance(cmd, str),
    )


def ensure_java_android_env(env: dict[str, str]) -> dict[str, str]:
    out = dict(env)
    if not out.get("JAVA_HOME") or not Path(out["JAVA_HOME"], "bin", "java").exists():
        for c in (
            Path("/opt/homebrew/opt/openjdk@17"),
            Path("/usr/local/opt/openjdk@17"),
            Path("/opt/homebrew/opt/openjdk@21"),
            Path("/opt/homebrew/opt/openjdk"),
        ):
            if (c / "bin" / "java").exists():
                out["JAVA_HOME"] = str(c)
                break
    java_home = out.get("JAVA_HOME")
    if java_home:
        out["PATH"] = f"{java_home}/bin:" + out.get("PATH", "")
    sdk = out.get("ANDROID_HOME") or out.get("ANDROID_SDK_ROOT")
    if not sdk or not Path(sdk).exists():
        default_sdk = Path.home() / "Library" / "Android" / "sdk"
        if default_sdk.exists():
            out["ANDROID_HOME"] = str(default_sdk)
            out["ANDROID_SDK_ROOT"] = str(default_sdk)
    elif not out.get("ANDROID_SDK_ROOT"):
        out["ANDROID_SDK_ROOT"] = sdk
    return out


def setup_repos(work: Path, *, force: bool = False) -> tuple[Path, Path]:
    work.mkdir(parents=True, exist_ok=True)
    mas = work / "mas-app-android"
    mastg = work / "mastg"
    if force and mas.exists():
        shutil.rmtree(mas)
    if force and mastg.exists():
        shutil.rmtree(mastg)
    if not mas.exists():
        print(f"[setup] cloning {MAS_APP_REPO}")
        _run(["git", "clone", "--depth", "1", MAS_APP_REPO, str(mas)])
    if not mastg.exists():
        print(f"[setup] sparse-cloning {MASTG_REPO} ({MASTG_DEMOS})")
        _run(
            [
                "git",
                "clone",
                "--depth",
                "1",
                "--filter=blob:none",
                "--sparse",
                MASTG_REPO,
                str(mastg),
            ]
        )
        _run(["git", "sparse-checkout", "set", MASTG_DEMOS], cwd=mastg)
    return mas, mastg


def load_expected(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text())
    return data.get("demos", {})


def discover_demos(mastg: Path) -> list[Path]:
    root = mastg / MASTG_DEMOS
    return sorted(
        p for p in root.rglob("MASTG-DEMO-*") if p.is_dir() and DEMO_ID_RE.fullmatch(p.name)
    )


def demo_title(demo_dir: Path) -> str:
    md = next(demo_dir.glob("MASTG-DEMO-*.md"), None)
    if not md:
        return ""
    text = md.read_text(errors="replace")
    m = re.search(r"^title:\s*(.+)$", text, re.M)
    if m:
        return m.group(1).strip().strip("\"'")
    m = re.search(r"^#\s+(.+)$", text, re.M)
    return m.group(1).strip() if m else ""


def demo_kind(demo_dir: Path) -> str:
    """Heuristic classification for reporting."""
    files = {p.name for p in demo_dir.iterdir() if p.is_file()}
    if any(n.endswith(".js") or n in {"bypass.js", "script.js"} for n in files):
        return "frida"
    if files <= {"MASTG-DEMO-" + demo_dir.name.split("-")[-1] + ".md"} or files == {
        f"{demo_dir.name}.md"
    }:
        return "docs"
    if (demo_dir / "MastgTest.kt").exists() or (demo_dir / "MastgTestWebView.kt").exists():
        return "static"
    if sibling_source_paths(demo_dir):
        return "sibling"
    return "other"


def sibling_source_paths(demo_dir: Path) -> list[Path]:
    """Resolve ``{{ ../MASTG-DEMO-XXXX/file.kt # ... }}`` includes from the demo markdown."""
    md = next(demo_dir.glob("MASTG-DEMO-*.md"), None)
    if not md:
        return []
    text = md.read_text(errors="replace")
    out: list[Path] = []
    seen: set[Path] = set()
    for block in INCLUDE_RE.findall(text):
        for part in block.split("#"):
            part = part.strip()
            if not part or part.startswith("run.sh") or part.endswith(".md"):
                continue
            # Relative to demo dir (MASTG uses ../MASTG-DEMO-XXXX/File)
            cand = (demo_dir / part).resolve()
            if not cand.is_file():
                continue
            name = cand.name
            useful = (
                name in INJECT_FILES
                or name.startswith("build.gradle.kts.")
                or cand.suffix in {".kt", ".xml", ".proto", ".cpp", ".pro"}
            )
            if useful and cand not in seen:
                seen.add(cand)
                out.append(cand)
    return out


def local_inject_paths(demo_dir: Path) -> list[Path]:
    paths: list[Path] = []
    for name in INJECT_FILES:
        p = demo_dir / name
        if p.is_file():
            paths.append(p)
    for pattern in INJECT_GLOBS:
        paths.extend(sorted(demo_dir.glob(pattern)))
    # de-dupe
    seen: set[Path] = set()
    uniq: list[Path] = []
    for p in paths:
        if p not in seen:
            seen.add(p)
            uniq.append(p)
    return uniq


def collect_sources(demo_dir: Path) -> tuple[list[Path], str, list[str]]:
    """Return (files to inject, mode, source demo ids). Local wins over sibling."""
    local = local_inject_paths(demo_dir)
    siblings = sibling_source_paths(demo_dir)
    by_name: dict[str, Path] = {}
    source_ids: list[str] = []
    for p in siblings + local:  # local overwrites sibling
        by_name[p.name] = p
        m = DEMO_ID_RE.search(str(p))
        if m and m.group(0) != demo_dir.name and m.group(0) not in source_ids:
            source_ids.append(m.group(0))
    files = list(by_name.values())
    if local and not siblings:
        mode = "local"
    elif local and siblings:
        mode = "local+sibling"
    elif siblings:
        mode = "sibling"
    else:
        mode = "none"
    return files, mode, source_ids


def is_buildable(demo_dir: Path) -> bool:
    files, mode, _ = collect_sources(demo_dir)
    return mode != "none" and bool(files)


def primary_source_demo(demo_dir: Path) -> str | None:
    """If this demo only reuses another demo's sources, return that demo id."""
    local = local_inject_paths(demo_dir)
    # Ignore reversed/docs-only locals
    meaningful_local = [
        p
        for p in local
        if p.name in INJECT_FILES or p.name.startswith("build.gradle.kts.") or p.suffix in {".proto", ".cpp"}
    ]
    if meaningful_local:
        return None
    _, _, ids = collect_sources(demo_dir)
    return ids[0] if len(ids) == 1 else (ids[0] if ids else None)


def reset_mas_app(mas: Path) -> None:
    _run(["git", "checkout", "--", "."], cwd=mas, check=False)
    _run(["git", "clean", "-fd", "app/"], cwd=mas, check=False)
    for rel in ("app/src/main/proto", "app/src/main/cpp"):
        p = mas / rel
        if p.exists():
            shutil.rmtree(p)


def _copy_into_mas(src: Path, mas: Path) -> None:
    java_pkg = mas / "app/src/main/java/org/owasp/mastestapp"
    res_xml = mas / "app/src/main/res/xml"
    name = src.name
    if name.endswith(".kt"):
        dst = java_pkg / name
    elif name == "AndroidManifest.xml":
        dst = mas / "app/src/main/AndroidManifest.xml"
    elif name in {
        "filepaths.xml",
        "network_security_config.xml",
        "backup_rules.xml",
        "data_extraction_rules.xml",
    }:
        res_xml.mkdir(parents=True, exist_ok=True)
        dst = res_xml / name
    elif name == "proguard-rules.pro":
        dst = mas / "app/proguard-rules.pro"
    elif name == "CMakeLists.txt" or name.endswith(".cpp"):
        cpp = mas / "app/src/main/cpp"
        cpp.mkdir(parents=True, exist_ok=True)
        dst = cpp / name
    elif name.endswith(".proto"):
        proto = mas / "app/src/main/proto"
        proto.mkdir(parents=True, exist_ok=True)
        dst = proto / name
    elif name.startswith("build.gradle.kts."):
        kind = name.split("build.gradle.kts.", 1)[1]
        _insert_gradle_block_from_file(src, mas, kind)
        print(f"  + {name}")
        return
    else:
        print(f"  ! skip unknown inject {name}")
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    print(f"  + {name}")


def _insert_gradle_block_from_file(src: Path, mas: Path, kind: str) -> None:
    target = mas / "app" / "build.gradle.kts"
    marker = f"// ADD_{kind.upper()}_HERE"
    text = target.read_text()
    if marker not in text:
        print(f"  ! missing marker {marker}")
        return
    block = src.read_text()
    text = text.replace(marker, block.rstrip() + "\n    " + marker, 1)
    target.write_text(text)


def inject_sources(files: list[Path], mas: Path) -> None:
    # Apply gradle overlays after other files so markers exist in a clean tree.
    normal = [p for p in files if not p.name.startswith("build.gradle.kts.")]
    overlays = [p for p in files if p.name.startswith("build.gradle.kts.")]
    for p in normal + overlays:
        _copy_into_mas(p, mas)


def build_apk(mas: Path, env: dict[str, str], *, timeout: int = 600) -> Path:
    props = mas / "gradle.properties"
    text = props.read_text() if props.exists() else ""
    if "org.gradle.caching=true" not in text:
        props.write_text(text + "\norg.gradle.caching=true\n")
    gradlew = mas / "gradlew"
    gradlew.chmod(gradlew.stat().st_mode | 0o111)
    proc = _run(
        ["./gradlew", "assembleDebug", "--stacktrace", "-q"],
        cwd=mas,
        env=env,
        check=False,
        timeout=timeout,
    )
    apk = mas / "app/build/outputs/apk/debug/app-debug.apk"
    if proc.returncode != 0 or not apk.is_file():
        tail = (proc.stdout or "")[-2000:] + "\n" + (proc.stderr or "")[-4000:]
        raise RuntimeError(f"gradle failed ({proc.returncode}):\n{tail}")
    return apk


def focus_findings(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    focused = []
    for f in findings:
        cls = str(f.get("class_name") or "")
        if cls == "AndroidManifest.xml" or cls.endswith("AndroidManifest.xml"):
            focused.append(f)
            continue
        if cls.endswith(".so") or "/lib" in cls.replace("\\", "/"):
            focused.append(f)
            continue
        if any(cls.startswith(p) or p in cls for p in FOCUS_CLASS_PREFIXES):
            focused.append(f)
            continue
        blob = json.dumps(f, default=str)
        if "MastgTest" in blob or "mastestapp" in blob.lower():
            focused.append(f)
    return focused


def scan_apk(apk: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    sys.path.insert(0, str(REPO_ROOT))
    from androguard import Application

    app = Application(str(apk))
    findings = app.scan_vulns()
    return findings, focus_findings(findings)


def evaluate(
    demo_id: str,
    spec: dict[str, Any] | None,
    focused: list[dict[str, Any]],
) -> tuple[str, str]:
    cats = sorted({str(f.get("category")) for f in focused if f.get("category")})
    if not spec:
        if cats:
            return "gap", f"no expected mapping; found {cats}"
        return "gap", "no expected mapping; no MastgTest findings"
    expect_any = list(spec.get("expect_any") or [])
    forbid = list(spec.get("forbid") or [])
    if forbid and not expect_any:
        hit = [c for c in forbid if c in cats]
        if hit:
            return "fail", f"forbidden categories present: {hit}"
        return "pass", "negative demo clean"
    if forbid:
        hit = [c for c in forbid if c in cats]
        if hit:
            return "fail", f"forbidden categories present: {hit}"
    if not expect_any:
        if cats:
            return "gap", f"documented uncovered (found {cats})"
        return "gap", "documented uncovered (no MastgTest findings)"
    if any(c in cats for c in expect_any):
        matched = [c for c in expect_any if c in cats]
        return "pass", f"matched {matched}"
    return "fail", f"expected one of {expect_any}, got {cats or '[]'}"


def sync_expected(mastg: Path, path: Path) -> None:
    """Ensure every demo id exists in expected.json (preserve curated entries)."""
    existing_full = json.loads(path.read_text()) if path.exists() else {"demos": {}}
    demos_map: dict[str, Any] = dict(existing_full.get("demos") or {})
    for d in discover_demos(mastg):
        if d.name in demos_map:
            continue
        files, mode, src_ids = collect_sources(d)
        kind = demo_kind(d)
        title = demo_title(d)
        if mode == "none":
            notes = f"GAP: {kind} demo with no injectable sources ({title})"
        elif mode == "sibling":
            notes = f"GAP: sources from {', '.join(src_ids)}; static scan of shared APK ({title})"
        else:
            notes = f"GAP: no curated expect_any yet ({title})"
        demos_map[d.name] = {"expect_any": [], "notes": notes}
        if src_ids:
            demos_map[d.name]["source_from"] = src_ids
    # stable key order by demo number
    ordered = dict(sorted(demos_map.items(), key=lambda kv: kv[0]))
    out = {
        "_comment": existing_full.get(
            "_comment",
            "Expected Androguard scan_vulns categories for OWASP MASTG Android demos.",
        ),
        "demos": ordered,
    }
    path.write_text(json.dumps(out, indent=2) + "\n")
    print(f"[sync-expected] {len(ordered)} demos → {path}")


def write_report(results: list[DemoResult], out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    day = date.today().isoformat()
    path = out_dir / f"mastg-scan-validate-{day}.json"
    # Human-readable reference is docs/mastg-coverage.md (see mastg_coverage_doc.py).
    path.write_text(json.dumps([asdict(r) for r in results], indent=2) + "\n")
    print(f"[report] {path}")
    coverage_script = REPO_ROOT / "scripts" / "mastg_coverage_doc.py"
    if coverage_script.is_file():
        proc = _run([sys.executable, str(coverage_script)], check=False)
        if proc.returncode != 0:
            print(f"[report] coverage doc refresh failed:\n{proc.stderr[-1000:]}")
        else:
            print("[report] docs/mastg-coverage.md")
    return path


def process_demo(
    demo_dir: Path,
    *,
    mas: Path,
    apk_dir: Path,
    env: dict[str, str],
    expected_map: dict[str, Any],
    build: bool,
    scan: bool,
    existing_apk: Path | None = None,
    built_apks: dict[str, Path] | None = None,
) -> DemoResult:
    demo_id = demo_dir.name
    masvs = demo_dir.parent.name
    title = demo_title(demo_dir)
    spec = expected_map.get(demo_id)
    files, mode, src_ids = collect_sources(demo_dir)
    result = DemoResult(
        demo_id=demo_id,
        category=masvs,
        title=title,
        expected=list((spec or {}).get("expect_any") or []),
        forbid=list((spec or {}).get("forbid") or []),
        source_mode=mode,
        source_from=src_ids,
    )
    t0 = time.time()
    built_apks = built_apks if built_apks is not None else {}

    apk_path = existing_apk

    # Reuse sibling APK when this demo has no local sources (e.g. 0158 → 0157).
    if apk_path is None and mode == "sibling":
        primary = primary_source_demo(demo_dir)
        if primary:
            cand = built_apks.get(primary) or (apk_dir / f"{primary}.apk")
            if Path(cand).is_file():
                dest = apk_dir / f"{demo_id}.apk"
                if Path(cand).resolve() != dest.resolve():
                    shutil.copy2(cand, dest)
                apk_path = dest
                result.source_mode = "reused_apk"
                result.build_ok = True
                result.apk = str(dest.relative_to(REPO_ROOT))
                print(f"[reuse] {demo_id} ← {primary}.apk")

    if build and apk_path is None:
        if mode == "none" or not files:
            result.status = "skip"
            result.message = (
                f"no injectables ({demo_kind(demo_dir)} / docs-only / tooling-only demo)"
            )
            result.elapsed_s = time.time() - t0
            return result
        print(f"[build] {masvs}/{demo_id} ({mode})")
        try:
            reset_mas_app(mas)
            inject_sources(files, mas)
            built = build_apk(mas, env)
            apk_dir.mkdir(parents=True, exist_ok=True)
            dest = apk_dir / f"{demo_id}.apk"
            shutil.copy2(built, dest)
            apk_path = dest
            built_apks[demo_id] = dest
            result.build_ok = True
            result.apk = str(dest.relative_to(REPO_ROOT))
        except Exception as exc:  # noqa: BLE001
            result.status = "build_error"
            result.message = str(exc)[:1500]
            result.elapsed_s = time.time() - t0
            return result
    elif existing_apk is not None and result.apk is None:
        result.build_ok = True
        result.apk = str(existing_apk)
        built_apks[demo_id] = Path(existing_apk)

    if apk_path is not None:
        built_apks[demo_id] = Path(apk_path)

    if not scan:
        result.status = "skip"
        result.message = "build-only"
        result.elapsed_s = time.time() - t0
        return result

    if apk_path is None or not Path(apk_path).is_file():
        result.status = "skip"
        result.message = result.message or "no APK to scan"
        result.elapsed_s = time.time() - t0
        return result

    print(f"[scan] {demo_id}")
    try:
        _all, focused = scan_apk(Path(apk_path))
    except Exception as exc:  # noqa: BLE001
        result.status = "scan_error"
        result.message = str(exc)[:1500]
        result.elapsed_s = time.time() - t0
        return result

    result.focused_findings = [
        {
            "category": f.get("category"),
            "severity": f.get("severity"),
            "title": f.get("title"),
            "class_name": f.get("class_name"),
            "method_name": f.get("method_name"),
        }
        for f in focused
    ]
    result.found_categories = sorted(
        {str(f.get("category")) for f in focused if f.get("category")}
    )
    status, msg = evaluate(demo_id, spec, focused)
    result.status = status
    result.message = msg
    result.elapsed_s = time.time() - t0
    print(f"  -> {status}: {msg}")
    return result


def parse_only(raw: str | None) -> set[str] | None:
    if not raw:
        return None
    parts = {p.strip() for p in raw.replace(" ", "").split(",") if p.strip()}
    return parts or None


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--work-dir", type=Path, default=DEFAULT_WORK)
    ap.add_argument("--setup", action="store_true", help="Clone/update mastg + mas-app-android")
    ap.add_argument("--force-clone", action="store_true")
    ap.add_argument(
        "--all",
        action="store_true",
        default=True,
        help="Build+scan every discoverable demo (default)",
    )
    ap.add_argument(
        "--mapped-only",
        action="store_true",
        help="Only demos with curated non-empty expect_any / forbid in expected.json",
    )
    ap.add_argument("--only", type=str, help="Comma-separated MASTG-DEMO-XXXX ids")
    ap.add_argument("--build-only", action="store_true")
    ap.add_argument("--scan-only", action="store_true")
    ap.add_argument("--apk-dir", type=Path, default=None)
    ap.add_argument("--expected", type=Path, default=EXPECTED_PATH)
    ap.add_argument("--sync-expected", action="store_true", help="Add missing demo ids to expected.json")
    ap.add_argument("--report-dir", type=Path, default=REPO_ROOT / "workspace" / "reports")
    ap.add_argument("--list", action="store_true", help="List demos and exit")
    args = ap.parse_args(argv)

    env = ensure_java_android_env(os.environ.copy())
    work = args.work_dir
    apk_dir = args.apk_dir or (work / "apks")

    if args.setup or args.force_clone or not (work / "mastg").exists():
        setup_repos(work, force=args.force_clone)

    mas = work / "mas-app-android"
    mastg = work / "mastg"
    if not mastg.exists():
        print("mastg missing; re-run with --setup", file=sys.stderr)
        return 2

    if args.sync_expected:
        sync_expected(mastg, args.expected)

    # Pure --sync-expected (no list/build/scan selection flags beyond defaults).
    action_flags = any(
        [
            args.list,
            args.only,
            args.mapped_only,
            args.scan_only,
            args.build_only,
            "--all" in (argv or sys.argv),
        ]
    )
    if args.sync_expected and not action_flags:
        return 0

    demos = discover_demos(mastg)
    only = parse_only(args.only)
    expected_map = load_expected(args.expected)

    if only:
        demos = [d for d in demos if d.name in only]
    elif args.mapped_only:
        demos = [
            d
            for d in demos
            if d.name in expected_map
            and (
                expected_map[d.name].get("expect_any")
                or expected_map[d.name].get("forbid")
            )
        ]
    # else: ALL demos (default)

    if args.list:
        for d in demos:
            files, mode, src = collect_sources(d)
            flag = "KT" if (d / "MastgTest.kt").exists() or (d / "MastgTestWebView.kt").exists() else "--"
            exp = "mapped" if d.name in expected_map else "unmapped"
            extra = f" ←{','.join(src)}" if src else ""
            print(
                f"{flag} {exp:8} {mode:14} {d.parent.name}/{d.name}{extra}  {demo_title(d)[:60]}"
            )
        print(f"total={len(demos)} buildable={sum(1 for d in demos if is_buildable(d))}")
        return 0

    if not args.scan_only and not mas.exists():
        print("mas-app-android missing; re-run with --setup", file=sys.stderr)
        return 2

    if not args.scan_only:
        java = Path(env.get("JAVA_HOME", "")) / "bin" / "java"
        if not java.exists():
            print("JAVA_HOME/bin/java not found (need JDK 17+)", file=sys.stderr)
            return 2
        if not env.get("ANDROID_HOME"):
            print("ANDROID_HOME not set / SDK missing", file=sys.stderr)
            return 2
        print(f"[env] JAVA_HOME={env.get('JAVA_HOME')}")
        print(f"[env] ANDROID_HOME={env.get('ANDROID_HOME')}")

    print(f"[plan] {len(demos)} demos (buildable={sum(1 for d in demos if is_buildable(d))})")

    results: list[DemoResult] = []
    do_build = not args.scan_only
    do_scan = not args.build_only
    built_apks: dict[str, Path] = {}

    # Prefer building source demos before dependents that reuse their APK.
    def sort_key(d: Path) -> tuple[int, str]:
        primary = primary_source_demo(d)
        return (1 if primary else 0, d.name)

    for demo_dir in sorted(demos, key=sort_key):
        existing = None
        if args.scan_only:
            candidate = apk_dir / f"{demo_dir.name}.apk"
            existing = candidate if candidate.is_file() else None
        results.append(
            process_demo(
                demo_dir,
                mas=mas,
                apk_dir=apk_dir,
                env=env,
                expected_map=expected_map,
                build=do_build,
                scan=do_scan,
                existing_apk=existing,
                built_apks=built_apks,
            )
        )

    # Keep report order by demo id
    results.sort(key=lambda r: r.demo_id)
    write_report(results, args.report_dir)
    fails = sum(1 for r in results if r.status in {"fail", "build_error", "scan_error"})
    print(
        "[summary]",
        ", ".join(
            f"{k}={sum(1 for r in results if r.status == k)}"
            for k in ("pass", "fail", "gap", "skip", "build_error", "scan_error")
            if any(r.status == k for r in results)
        ),
    )
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
