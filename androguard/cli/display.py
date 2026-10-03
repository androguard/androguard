"""Colored, structured CLI printers (Rich)."""

from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path

from rich import box
from rich.console import Console
from rich.rule import Rule
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text

from androguard import __version__ as ANDROGUARD_VERSION

_SEVERITY_STYLE = {
    "critical": "bold white on dark_red",
    "high": "bold white on red",
    "medium": "bold black on yellow",
    "low": "bold white on blue",
    "info": "bold white on cyan",
}

_OPCODE_STYLES = (
    ("invoke-", "bold cyan"),
    ("filled-new-array", "blue"),
    ("packed-switch", "yellow"),
    ("sparse-switch", "yellow"),
    ("instance-of", "blue"),
    ("check-cast", "blue"),
    ("array-length", "blue"),
    ("monitor-", "red"),
    ("return", "bold green"),
    ("throw", "bold red"),
    ("goto", "yellow"),
    ("if-", "yellow"),
    ("const", "magenta"),
    ("new-", "blue"),
    ("iget", "bright_blue"),
    ("iput", "bright_blue"),
    ("sget", "bright_blue"),
    ("sput", "bright_blue"),
    ("move", "green"),
    ("nop", "dim"),
)

_DISASM_LINE = re.compile(
    r"^(?P<lead>\s*)"
    r"(?P<off>(?:0x)?[0-9a-fA-F]+)(?P<colon>:?)"
    r"(?P<mid>\s+)"
    r"(?:(?P<byte>[0-9a-fA-F]{2})\s+)?"
    r"(?P<op>\S+)"
    r"(?P<rest>.*)$"
)


def console(*, stderr: bool = False) -> Console:
    return Console(
        file=sys.stderr if stderr else sys.stdout,
        highlight=False,
        soft_wrap=True,
        emoji=False,
    )


def print_error(message: str) -> None:
    console(stderr=True).print(
        Text.assemble((" error ", "bold white on red"), (" ", ""), (message, "red"))
    )


def print_warning(message: str) -> None:
    console(stderr=True).print(
        Text.assemble(
            (" warn ", "bold black on yellow"),
            (" ", ""),
            (message, "yellow"),
        )
    )


def print_info(message: str) -> None:
    console(stderr=True).print(
        Text.assemble((" info ", "bold white on blue"), (" ", ""), (message, "cyan"))
    )


def print_version(c: Console | None = None) -> None:
    out = c or console()
    out.print(
        Text.assemble(
            ("androguard", "bold cyan"),
            (" ", ""),
            (ANDROGUARD_VERSION, "bold"),
        )
    )


def print_summary(summary: dict, apk_path: str, c: Console | None = None) -> None:
    out = c or console()
    app_name = str(summary.get("app_name") or "") or Path(apk_path).name
    table = Table(
        title=app_name,
        box=box.ROUNDED,
        show_header=False,
        pad_edge=True,
        expand=True,
    )
    table.add_column("key", style="dim", no_wrap=True)
    table.add_column("value", overflow="fold")

    for key, value in summary.items():
        table.add_row(f"{key}:", _format_summary_value(key, value))
    out.print(table)
    out.print()


def print_class_names(names, c: Console | None = None) -> None:
    out = c or console()
    seq = names if isinstance(names, (list, tuple)) else list(names)
    out.print(Rule(f"{len(seq)} class(es)", style="cyan"))
    for name in seq:
        out.print(_style_type_name(str(name)))


def print_methods(methods, c: Console | None = None) -> None:
    out = c or console()
    seq = methods if isinstance(methods, (list, tuple)) else list(methods)
    out.print(Rule(f"{len(seq)} method(s)", style="cyan"))
    for method in seq:
        line = Text()
        line.append_text(_style_type_name(str(method.class_name)))
        line.append(" -> ", style="dim")
        line.append(str(method.name), style="bold magenta")
        out.print(line)


def print_java(java: str, heading: str | None = None, c: Console | None = None) -> None:
    out = c or console()
    if heading:
        out.print(Rule(heading, style="cyan"))
    out.print(
        Syntax(
            java,
            "java",
            theme="ansi_dark",
            line_numbers=True,
            word_wrap=True,
            padding=0,
        )
    )


def print_disasm_header(class_name: str, method_name: str, c: Console | None = None) -> None:
    out = c or console()
    title = Text()
    title.append("# ", style="dim")
    title.append_text(_style_type_name(class_name))
    title.append(".", style="dim")
    title.append(method_name, style="bold magenta")
    out.print()
    out.print(Rule(title, style="cyan"))


def print_cfg_edges(edges, block_count: int, c: Console | None = None) -> None:
    out = c or console()
    for edge in edges:
        line = Text("  ")
        line.append(f"{edge['from']:08x}", style="cyan")
        line.append(" -> ", style="dim")
        line.append(f"{edge['to']:08x}", style="cyan")
        out.print(line)
    out.print(
        Text.assemble(
            ("  # ", "dim"),
            (str(block_count), "bold cyan"),
            (" basic block(s)", "dim"),
        )
    )


def print_disasm_line(line: str, c: Console | None = None) -> None:
    (c or console()).print(_style_disasm_line(line))


def print_findrefs(
    kind: str,
    value: str,
    sites,
    pool: list[str] | None = None,
    c: Console | None = None,
) -> None:
    out = c or console()
    sites = list(sites)
    out.print(
        Text.assemble(
            ("findrefs: ", "bold"),
            (str(len(sites)), "bold cyan"),
            (" code site(s) for ", "dim"),
            (kind, "yellow"),
            (" ", ""),
            (repr(value), "magenta"),
        )
    )
    if sites:
        table = Table(box=box.SIMPLE, show_header=True, pad_edge=False, expand=True)
        table.add_column("location", overflow="fold")
        table.add_column("offset", style="cyan", no_wrap=True)
        for s in sites:
            loc = f"{s.get('class_name')}#{s.get('method_name')}"
            off = s.get("file_offset")
            table.add_row(loc, "" if off is None else str(off))
        out.print(table)
    if pool is not None:
        out.print(
            Text.assemble(
                ("string pool: ", "bold"),
                (str(len(pool)), "bold cyan"),
                (" match(es) with no code reference", "dim"),
            )
        )
        for s in pool[:30]:
            out.print(Text.assemble(("  ", ""), (repr(s), "green")))
        extra = len(pool) - 30
        if extra > 0:
            out.print(Text(f"  ... ({extra} more)", style="dim"))


def print_emulate(result: dict, c: Console | None = None) -> None:
    out = c or console()
    finished = bool(result.get("finished"))
    out.print(
        Text.assemble(
            ("steps=", "dim"),
            (str(result.get("steps")), "bold cyan"),
            ("  ", ""),
            ("finished=", "dim"),
            (str(result.get("finished")), "bold green" if finished else "bold yellow"),
        )
    )
    regs = result.get("registers") or {}
    for k in sorted(regs, key=lambda x: int(x) if str(x).isdigit() else 0):
        out.print(
            Text.assemble(
                ("  v", "dim"),
                (str(k), "cyan"),
                (" = ", "dim"),
                (str(regs[k]), "white"),
            )
        )


def print_decode_project(project: dict, c: Console | None = None) -> None:
    out = c or console()
    out.print(
        Text.assemble(
            ("project_root=", "dim"),
            (str(project["project_root"]), "cyan"),
            ("  entries=", "dim"),
            (str(project["entry_count"]), "bold cyan"),
            ("  dex_classes=", "dim"),
            (str(project["dex_class_count"]), "bold cyan"),
        )
    )
    files = sorted(project["files"])
    for path in files[:50]:
        out.print(Text(str(path), style="white"))
    extra = len(files) - 50
    if extra > 0:
        out.print(Text(f"... ({extra} more)", style="dim"))


def print_scan_vulns(findings: list, c: Console | None = None) -> None:
    out = c or console()
    counts = Counter(str(f.get("severity") or "?").lower() for f in findings)
    head = Text.assemble(
        ("scan-vulns: ", "bold"),
        (f"{len(findings)} finding(s)", "bold cyan"),
    )
    out.print(head)
    if counts:
        bar = Text("  ")
        order = ("critical", "high", "medium", "low", "info")
        first = True
        for sev in order:
            n = counts.get(sev, 0)
            if not n:
                continue
            if not first:
                bar.append("  ", style="")
            first = False
            bar.append(f" {sev.upper()} {n} ", style=_SEVERITY_STYLE.get(sev, "bold"))
        extra = [k for k in counts if k not in order]
        for sev in extra:
            bar.append("  ")
            bar.append(
                f" {sev.upper()} {counts[sev]} ",
                style=_SEVERITY_STYLE.get(sev, "bold white on grey37"),
            )
        if bar.plain.strip():
            out.print(bar)
    if not findings:
        return
    out.print()
    for i, f in enumerate(findings, 1):
        _print_vuln_finding(out, i, f if isinstance(f, dict) else dict(f))


def _print_vuln_finding(c: Console, index: int, f: dict) -> None:
    severity = str(f.get("severity") or "?").lower()
    style = _SEVERITY_STYLE.get(severity, "bold white on grey37")
    category = str(f.get("category") or "")
    title = str(f.get("title") or "")
    cls = str(f.get("class_name") or "")
    meth = str(f.get("method_name") or "")
    loc = f"{cls}#{meth}" if meth else cls

    head = Text()
    head.append(f"{index}. ", style="bold dim")
    head.append(f" {severity.upper()} ", style=style)
    head.append(" ")
    head.append(category, style="bold cyan")
    if title:
        head.append(" — ", style="dim")
        head.append(title, style="bold")
    c.print(head)

    if loc:
        c.print(Text.assemble(("   at     ", "dim"), (loc, "white")))
    if f.get("cwe"):
        c.print(Text.assemble(("   CWE    ", "dim"), (str(f["cwe"]), "magenta")))

    msg = str(f.get("message") or "").strip()
    if msg and msg != title:
        short = msg.split(". Sink:")[0].split(". Source:")[0].strip()
        if short and not short.endswith("."):
            short += "."
        c.print(Text.assemble(("   note   ", "dim"), (short, "white")))

    mas_rows = (
        ("MASWE  ", "maswe", "red"),
        ("MASVS  ", "masvs", "yellow"),
        ("MASTG  ", "mastg_know", "green"),
        ("BEST   ", "mastg_best", "green"),
    )
    for label, key, color in mas_rows:
        ids = _mas_ids(f.get(key))
        if not ids:
            continue
        shown = "KNOW   " if key == "mastg_know" else label
        c.print(Text.assemble((f"   {shown}", "dim"), (", ".join(ids), color)))

    rec = str(f.get("recommendation") or "").strip()
    if rec:
        c.print(Text.assemble(("   fix    ", "dim"), (rec, "italic bright_white")))
    c.print()


def _mas_ids(links) -> list[str]:
    ids: list[str] = []
    for link in links or []:
        if isinstance(link, dict):
            lid = (link.get("id") or "").strip()
            if lid:
                ids.append(lid)
        elif link:
            ids.append(str(link))
    seen: set[str] = set()
    out: list[str] = []
    for i in ids:
        if i not in seen:
            seen.add(i)
            out.append(i)
    return out


def _format_summary_value(key: str, value: object) -> Text:
    if key == "signed":
        ok = bool(value)
        return Text("yes" if ok else "no", style="bold green" if ok else "bold red")
    if key in {"classes", "strings", "methods"}:
        return Text(str(value), style="bold cyan")
    if key == "dex_files":
        if isinstance(value, (list, tuple)):
            if not value:
                return Text("(none)", style="dim")
            t = Text()
            for i, name in enumerate(value):
                if i:
                    t.append(", ", style="dim")
                t.append(str(name), style="cyan")
            return t
    if key == "package":
        return Text(str(value), style="bold yellow")
    if key in {"app_name", "main_activity"}:
        return Text(str(value) if value else "—", style="white" if value else "dim")
    return Text(str(value))


def _style_type_name(name: str) -> Text:
    t = Text()
    if name.startswith("L") and name.endswith(";"):
        parts = name[1:-1].split("/")
        t.append("L", style="dim")
        for i, part in enumerate(parts):
            if i:
                t.append("/", style="dim")
            last = i == len(parts) - 1
            t.append(part, style="bold cyan" if last else "cyan")
        t.append(";", style="dim")
        return t
    if "." in name:
        pkg, _, cls = name.rpartition(".")
        t.append(pkg, style="cyan")
        t.append(".", style="dim")
        t.append(cls, style="bold cyan")
        return t
    t.append(name, style="cyan")
    return t


def _style_disasm_line(line: str) -> Text:
    m = _DISASM_LINE.match(line)
    if not m:
        return Text(line)
    t = Text()
    t.append(m.group("lead") or "")
    t.append(m.group("off"), style="dim cyan")
    t.append(m.group("colon") or "")
    t.append(m.group("mid") or "")
    if m.group("byte"):
        t.append(m.group("byte"), style="dim")
        t.append("  ")
    op = m.group("op")
    t.append(op, style=_opcode_style(op))
    rest = m.group("rest") or ""
    t.append(_style_disasm_operands(rest))
    return t


def _opcode_style(op: str) -> str:
    low = op.lower()
    for prefix, style in _OPCODE_STYLES:
        if low.startswith(prefix):
            return style
    return "bold"


def _style_disasm_operands(rest: str) -> Text:
    t = Text()
    if not rest:
        return t
    parts = re.split(
        r"(L[^;]+;|[\"'].*?[\"']|(?:method|string|type|field|call_site)@\d+|v\d+)",
        rest,
    )
    for part in parts:
        if part.startswith("L") and part.endswith(";"):
            t.append_text(_style_type_name(part))
        elif len(part) >= 2 and part[0] in "\"'" and part[-1] == part[0]:
            t.append(part, style="green")
        elif part.startswith("v") and part[1:].isdigit():
            t.append(part, style="cyan")
        elif "@" in part and part.split("@", 1)[0] in {
            "method",
            "string",
            "type",
            "field",
            "call_site",
        }:
            t.append(part, style="magenta")
        else:
            t.append(part, style="white")
    return t
