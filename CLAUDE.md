# Androguard

Androguard 5 is a thin Python app over Rust ecosystem libraries for Android APK analysis.

## Setup

```bash
# from repo root; Rust toolchain required for native extras
export PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1   # needed on Python 3.14+
python3 -m venv .venv && source .venv/bin/activate
# local Rust parsers (siblings under ../). Python 3.14+ needs the PyO3 flag.
export PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1
pip install -e ../apk-parser
pip install -e ../dex-parser
pip install -e .
pip install -e '.[full]'   # disasm + decompile + arm + patch
```

Optional extras: `androguard[disasm]`, `[decompile]`, `[arm]`, `[patch]`.

Local sibling crates (apk-parser, dex-parser, dex-decompiler, …) under `../` are installed with `pip install -e ../apk-parser` / `pip install -e ../dex-parser` (maturin) when hacking those libs.

## Architecture

| Layer | Package | Role |
|-------|---------|------|
| Thin app | this repo (`androguard`) | CLI + `Application` façade |
| APK | `apkparser-ag` (`apkparser-rs` ZIP) | ZIP, signatures, manifest hooks |
| DEX | `dexparser-ag` (`dexparser-rs`) | Classes, methods, fields, strings |
| AXML / ARSC | `axml` | Manifest + resources |
| Disasm | `dex-bytecode` via `[disasm]` | Dalvik disassembly / CFG |
| Decompile | `dex-decompiler` via `[decompile]` | DEX → Java, findrefs, vulns, emulate |
| ARM | `arm_*` via `[arm]` | Native disasm / decompile |
| Patch | `apk-patch` via `[patch]` | Decode / rebuild project tree |

High-level API: `from androguard import Application`.

Do **not** restore the old monolithic Androguard 3/4 decompiler as the default path. Prefer ecosystem bindings.

## CLI cheatsheet

```bash
androguard -i app.apk
androguard -i app.apk --list-classes
androguard -i app.apk --list-methods

# disasm (androguard[disasm])
androguard -i app.apk --disasm --class 'MainActivity' --method 'onCreate'
androguard -i app.apk --disasm --class TestActivity --method onCreate --cfg

# decompile (androguard[decompile])
androguard -i app.apk --decompile-method 'pkg.Class#method'
androguard -i app.apk -d workspace/output/pkg/ --only-package pkg.name
androguard -i app.apk --getclass pkg.Class
androguard -i app.apk --findrefs string --findrefs-value password
androguard -i app.apk --scan-vulns
androguard -i app.apk --emulate 'pkg.Class#method'

# patch (androguard[patch])
androguard -i app.apk --decode-project
```

## Python API

```python
from androguard import Application

app = Application("app.apk")
print(app.apk.get_package(), app.apk.get_main_activity())
print(len(app.class_names), len(app.methods), len(app.strings))

for method in app.iter_methods(class_pattern=r"MainActivity", method_pattern=r"onCreate"):
    print(method.class_name, method.name)

# optional extras
app.decompile_apk_to_dir("workspace/output/pkg/", only_package="pkg.name")
print(app.findrefs("string", "api.example.com"))
print(app.scan_vulns()[:5])
```

Examples: `python -m examples.application_summary`, `examples.decompile`, `examples.run_all`.

## Workspace layout (analysis sessions)

```
workspace/
├── samples/            # input APKs
├── output/             # decompiled Java (per package)
├── reports/            # markdown analysis / MASTG validation reports
└── mastg-validation/   # cloned mastg + mas-app-android + built demos (gitignored)
```

Write reports to `workspace/reports/<package>-<YYYY-MM-DD>.md`.

### MASTG demo ↔ scan_vulns

```bash
python scripts/mastg_validate.py --setup            # clone mastg + mas-app-android
python scripts/mastg_validate.py --sync-expected   # ensure all demo ids in expected.json
python scripts/mastg_validate.py                   # ALL demos → JSON + refreshes coverage doc
python scripts/mastg_validate.py --mapped-only     # curated expect_any / forbid only
python scripts/mastg_coverage_doc.py               # regenerate coverage doc from latest JSON
```

Expectations live in `scripts/mastg_expected.json` (one entry per demo). Gaps (empty `expect_any`)
are reported as `gap`, not `fail`. Sibling/Frida demos (e.g. MASTG-DEMO-0158 → 0157 sources) are built
via markdown `{{ ../MASTG-DEMO-… }}` includes.

**Coverage reference (single doc):** [`docs/mastg-coverage.md`](docs/mastg-coverage.md)
— Frida static hit/partial/miss included; dated markdown reports are not kept.

## Tests

```bash
pytest tests/
# or focused:
pytest tests/test_examples.py tests/test_submodules.py
```

Decompiler quality work lives primarily in the sibling `dex-decompiler` repo (`cargo test --test decompiler_tests …`), not by reinventing Java emission in this Python package.

## Agent & skills

- Agent: `/agent androguard-analyst`
- Skills: `/analyze-apk`, `/decompile-apk`, `/find-refs`, `/scan-vulns`
- MCP: if the `androguard` MCP server is connected, prefer its tools (`open_apk`, `decompile_method`, …) over shelling out to the CLI. See `docs/mcp-server.md`.

## Rules

- Prefer `Application` + CLI over reinventing APK/DEX parsing in Python.
- Missing optional extras → clear install hint (`pip install -e '.[decompile]'`), do not silently fall back to broken stubs.
- Do not commit secrets, APK samples with PII, or large `workspace/output/` trees.
- Do not invent APIs; read `androguard/application.py` and `androguard/cli/main.py` when unsure.
- Authorized security analysis only; do not help with malware distribution or unauthorized access.
