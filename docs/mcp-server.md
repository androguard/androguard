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
3. `find_refs` / `scan_vulns` / `decompile_method` / `get_class`  
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
| `list_permissions` | — | Permissions (paged) |
| `list_classes` | — | Class names (regex + paging) |
| `list_methods` | — | Methods (regex + paging) |
| `list_strings` / `search_strings` | — | String pool |
| `decompile_method` | `[decompile]` | `Class#method` → Java |
| `get_class` | `[decompile]` | One class → Java |
| `decompile_package` | `[decompile]` | Package tree → disk |
| `find_refs` | `[decompile]` | string/type/method/field refs |
| `scan_vulns` | `[decompile]` | Vulnerability detectors |
| `disassemble_method` | `[disasm]` | Dalvik disassembly |

## Environment

| Variable | Default | Meaning |
|----------|---------|---------|
| `ANDROGUARD_MCP_ROOTS` | cwd (+ `./workspace`) | Colon-separated path allowlist |
| `ANDROGUARD_MCP_ALLOW_ANY` | unset | `1` disables path allowlist |
| `ANDROGUARD_MCP_ALLOW_ANY_EXT` | unset | `1` allows non-`.apk`/`.dex` |
| `ANDROGUARD_MCP_MAX_LIST_ITEMS` | `200` | List page size |
| `ANDROGUARD_MCP_MAX_TEXT_CHARS` | `32000` | Decompile/disasm cap |
| `ANDROGUARD_MCP_MAX_FINDREFS` | `100` | findrefs cap |
| `ANDROGUARD_MCP_MAX_VULNS` | `100` | scan_vulns cap |
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
