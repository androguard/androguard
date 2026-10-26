# Androguard MCP Server

Expose Androguard analysis to LLM hosts ([Model Context Protocol](https://modelcontextprotocol.io/)): Claude Code, Cursor, and other MCP clients.

Design notes: [`mcp-server-plan.md`](mcp-server-plan.md).

## Install

```bash
# from this repo
export PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1   # Python 3.14+
pip install -e '.[mcp]'
# recommended for decompile / findrefs / vulns:
pip install -e '.[mcp,decompile]'
# optional disassembly:
pip install -e '.[mcp,disasm]'
# or everything:
pip install -e '.[full]'
```

Entrypoints:

```bash
androguard-mcp
python -m androguard.mcp
```

## Configure a client

### Claude Code / Cursor

Add an MCP server entry (paths adjusted to your checkout):

```json
{
  "mcpServers": {
    "androguard": {
      "command": "androguard-mcp",
      "args": [],
      "env": {
        "ANDROGUARD_MCP_ROOTS": "/absolute/path/to/androguard/workspace:/absolute/path/to/androguard/tests/data"
      }
    }
  }
}
```

On Windows, separate roots with `;` (e.g. `C:\\workspace;D:\\samples`), not `:`.

Or run via the venv Python:

```json
{
  "mcpServers": {
    "androguard": {
      "command": "/absolute/path/to/androguard/.venv/bin/python",
      "args": ["-m", "androguard.mcp"],
      "env": {
        "ANDROGUARD_MCP_ROOTS": "/absolute/path/to/androguard"
      }
    }
  }
}
```

## Typical agent flow

1. `open_apk` with a path under the allowlist → `session_id` + summary  
2. `list_classes` / `list_methods` / `search_strings`  
3. `find_refs` / `scan_vulns` / `inspect_code` / `method_cfg` / `dalvik_cfg`
4. `decompile_package` for larger trees (writes under `workspace/output/`)  
5. `close_apk` when done  

All tool results are **JSON strings** with `ok: true|false`. On failure:

```json
{
  "ok": false,
  "error": {
    "code": "extra_missing",
    "message": "…",
    "hint": "pip install 'androguard[decompile]'"
  }
}
```

## Tools

| Tool | Requires | Purpose |
|------|----------|---------|
| `open_apk` | — | Open APK/DEX → `session_id` |
| `close_apk` | — | Drop session |
| `list_sessions` | — | Open sessions |
| `apk_summary` | — | Package / DEX counts / signed |
| `get_manifest` | — | Decoded `AndroidManifest.xml` (paged) |
| `list_components` | — | Manifest components & attack surface (paged) |
| `get_signature_info` | — | Signature schemes (v1-v3) & cert details |
| `list_permissions` | — | Permissions (paged) |
| `list_classes` | — | Class names (regex + paging) |
| `list_methods` | — | Methods (regex + paging) |
| `list_strings` / `search_strings` | — | String pool |
| `inspect_code` | `[decompile]` Java / `[disasm]` Dalvik | Class/method Java or Dalvik, paged |
| `decompile_method` | `[decompile]` | `Class#method` → Java |
| `get_class` | `[decompile]` | One class → Java |
| `decompile_package` | `[decompile]` | Package tree → disk |
| `find_refs` | `[decompile]` | string/type/method/field refs |
| `scan_vulns` | `[decompile]` | Vulnerability detectors |
| `method_cfg` | `[decompile]` | Decompiler CFG (rows / nodes / edges) |
| `taint_solve` | `[decompile]` | Taint solver JSON (truncated) |
| `disassemble_method` | `[disasm]` | Legacy: regex-based Dalvik disassembly |
| `dalvik_cfg` | `[disasm]` | Dalvik CFG edges for matching methods |
| `decode_project` | `[patch]` + `ALLOW_WRITE` | List apk-patch project entry paths (one-shot) |
| `open_patch_project` | `[patch]` + `ALLOW_WRITE` | Decode editable workspace onto the session |
| `list_patch_classes` | `[patch]` | List `*.dex.txt` paths (optional regex) |
| `get_patch_class` / `put_patch_class` | `[patch]` (+ write for put) | Read/replace class dex-txt |
| `get_patch_method` / `put_patch_method` | `[patch]` (+ write for put) | Read/replace one method block |
| `rebuild_apk` | `[patch]` + `ALLOW_WRITE` | Assemble workspace → signed APK on disk |

### Patch workflow

```text
open_apk → open_patch_project(all_src=true)
  → get_patch_method(sid, "pkg.Class", "onCreate(Landroid/os/Bundle;)V")
  → put_patch_method(sid, "pkg.Class", "onCreate(Landroid/os/Bundle;)V", new_dex_txt)
  → rebuild_apk(sid, "workspace/output/app-patched.apk")
```

Class names accept Java (`com.example.Foo`) or Dalvik (`Lcom/example/Foo;`).
Method signatures must be exact dex-txt form: `name(params)return`.
`rebuild_apk` writes under `ANDROGUARD_MCP_ROOTS` only; it does not return APK bytes.

### Code inspection

`inspect_code` accepts a literal class name or `Class#method` selector:

```text
inspect_code(sid, "com.example.Auth")                         # Java class
inspect_code(sid, "com.example.Auth#login", format="dalvik")  # Dalvik method
inspect_code(sid, "com.example.Auth", offset=32000)          # Next page
```

Java is the default; DEX descriptors (`Lcom/example/Auth;`) are accepted.
Dalvik output is an instruction listing, not Smali. Same-name overloads are
included in Dalvik mode; Java mode retains the backend's name-only selection.
Large responses include `next_offset` for pagination. Existing tools remain
available; `disassemble_method` still supports regex selection.

## Environment

| Variable | Default | Meaning |
|----------|---------|---------|
| `ANDROGUARD_MCP_ROOTS` | cwd (+ `./workspace`) | Path allowlist (`:` on POSIX, `;` on Windows) |
| `ANDROGUARD_MCP_ALLOW_ANY` | unset | `1` disables path allowlist |
| `ANDROGUARD_MCP_ALLOW_ANY_EXT` | unset | `1` allows non-`.apk`/`.dex` |
| `ANDROGUARD_MCP_MAX_LIST_ITEMS` | `200` | List page size |
| `ANDROGUARD_MCP_MAX_TEXT_CHARS` | `32000` | Decompile/disasm cap |
| `ANDROGUARD_MCP_MAX_FINDREFS` | `100` | findrefs cap |
| `ANDROGUARD_MCP_MAX_VULNS` | `100` | scan_vulns cap |
| `ANDROGUARD_MCP_ALLOW_WRITE` | unset | `1` enables patch decode/edit/rebuild tools |
| `ANDROGUARD_MCP_MAX_SESSIONS` | `4` | Concurrent APKs |
| `ANDROGUARD_MCP_TTL_SECONDS` | `1800` | Idle session eviction |

## CLI flags

```bash
androguard-mcp --help
androguard-mcp --log-level DEBUG --log-tools
```

| Flag | Default | Meaning |
|------|---------|---------|
| `--log-level` | `INFO` | stderr level: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` |
| `--log-tools` | off | Log each tool invocation on stderr |

MCP client config example:

```json
{
  "mcpServers": {
    "androguard": {
      "command": "androguard-mcp",
      "args": ["--log-level", "DEBUG", "--log-tools"],
      "env": {
        "ANDROGUARD_MCP_ROOTS": "/path/to/androguard"
      }
    }
  }
}
```

## Logging

Startup and runtime logs go to **stderr** so stdout stays reserved for MCP JSON-RPC:

```text
2026-09-22T13:00:00 INFO [androguard-mcp] Androguard MCP server starting
2026-09-22T13:00:00 INFO [androguard-mcp]   androguard         5.0.0
2026-09-22T13:00:00 INFO [androguard-mcp]   tools (15)         open_apk, …
2026-09-22T13:00:00 INFO [androguard-mcp] Ready — waiting for MCP client on stdio
```

## Session thread affinity

MCP tool calls are serialized on a dedicated worker thread. The Rust-backed
APK/DEX parser objects are not safe to access or destroy on another thread;
routing synchronous tools through the SDK's ordinary worker pool can cause
PyO3 thread-affinity panics. Session eviction, closure, and server shutdown
also release objects on the same worker. This does not restrict clients from
submitting concurrent requests; they are queued for safe execution.

## Security

- Local analyst tool: inherits the host user’s privileges.  
- Keep `ANDROGUARD_MCP_ROOTS` tight in shared environments.  
- Do not expose the stdio server on a public network.  
- Authorized analysis only.

## Tests

```bash
pip install -e '.[mcp]'
python -m unittest tests.test_mcp -v
```

CI installs `androguard[mcp]` so session, tool, and server registration tests run on every push. Decompile/disasm cases skip when those extras are absent.
