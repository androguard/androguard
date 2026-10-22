"""APK session cache and path allowlist for the MCP server."""

from __future__ import annotations

import os
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path

from androguard.application import Application
from androguard.mcp.errors import McpToolError


def _parse_roots(raw: str | None) -> list[Path]:
    if not raw or not raw.strip():
        return []
    # Use os.pathsep so Windows drive letters (C:\…) are not split on ':'.
    return [
        Path(p.strip()).expanduser().resolve()
        for p in raw.split(os.pathsep)
        if p.strip()
    ]


def default_roots() -> list[Path]:
    """
    Allowed path roots.

    ``ANDROGUARD_MCP_ROOTS`` — ``os.pathsep``-separated absolute/relative paths
    (``:`` on POSIX, ``;`` on Windows).
    If unset: current working directory (and ``./workspace`` when present).
    ``ANDROGUARD_MCP_ALLOW_ANY=1`` disables the allowlist.
    """
    if os.environ.get("ANDROGUARD_MCP_ALLOW_ANY", "").strip() in (
        "1",
        "true",
        "True",
        "yes",
    ):
        return []
    env_roots = _parse_roots(os.environ.get("ANDROGUARD_MCP_ROOTS"))
    if env_roots:
        return env_roots
    cwd = Path.cwd().resolve()
    roots = [cwd]
    workspace = cwd / "workspace"
    if workspace.is_dir():
        roots.append(workspace.resolve())
    return roots


@dataclass
class Session:
    session_id: str
    path: Path
    app: Application
    opened_at: float = field(default_factory=time.time)
    last_used: float = field(default_factory=time.time)
    mtime: float = 0.0
    output_dir: Path | None = None
    # In-memory apk-patch project (path → bytes), when open_patch_project was used.
    patch_files: dict[str, bytes] | None = None
    patch_project_root: str | None = None
    patch_dirty: bool = False


class SessionStore:
    def __init__(
        self,
        *,
        roots: list[Path] | None = None,
        max_sessions: int = 4,
        ttl_seconds: float = 30 * 60,
        allow_any: bool | None = None,
    ) -> None:
        if allow_any is None:
            allow_any = os.environ.get("ANDROGUARD_MCP_ALLOW_ANY", "").strip() in (
                "1",
                "true",
                "True",
                "yes",
            )
        self.allow_any = allow_any
        self.roots = [] if allow_any else list(roots if roots is not None else default_roots())
        self.max_sessions = max(1, max_sessions)
        self.ttl_seconds = ttl_seconds
        self._sessions: dict[str, Session] = {}

    @classmethod
    def from_env(cls) -> SessionStore:
        max_sessions = int(os.environ.get("ANDROGUARD_MCP_MAX_SESSIONS", "4") or "4")
        ttl = float(os.environ.get("ANDROGUARD_MCP_TTL_SECONDS", str(30 * 60)) or 1800)
        return cls(max_sessions=max_sessions, ttl_seconds=ttl)

    def _is_allowed(self, path: Path) -> bool:
        if self.allow_any or not self.roots:
            return True
        for root in self.roots:
            try:
                path.relative_to(root)
                return True
            except ValueError:
                continue
        return False

    def resolve_path(self, path: str | Path) -> Path:
        resolved = Path(path).expanduser().resolve()
        if not resolved.is_file():
            raise McpToolError(
                "not_found",
                f"file not found: {resolved}",
            )
        suffix = resolved.suffix.lower()
        if suffix not in {".apk", ".dex"} and os.environ.get(
            "ANDROGUARD_MCP_ALLOW_ANY_EXT", ""
        ).strip() not in ("1", "true", "True", "yes"):
            raise McpToolError(
                "path_denied",
                f"unsupported extension {suffix!r} (use .apk or .dex)",
                hint="set ANDROGUARD_MCP_ALLOW_ANY_EXT=1 to override",
            )
        self._assert_under_roots(resolved)
        return resolved

    def resolve_output_dir(self, path: str | Path) -> Path:
        resolved = Path(path).expanduser().resolve()
        self._assert_under_roots(resolved)
        return resolved

    def resolve_output_file(self, path: str | Path) -> Path:
        """Resolve a writable output file path under allowed roots."""
        resolved = Path(path).expanduser().resolve()
        self._assert_under_roots(resolved)
        parent = resolved.parent
        if not parent.exists():
            parent.mkdir(parents=True, exist_ok=True)
        self._assert_under_roots(parent)
        return resolved

    def _assert_under_roots(self, path: Path) -> None:
        if not self._is_allowed(path):
            roots = ", ".join(str(r) for r in self.roots) or "(none)"
            raise McpToolError(
                "path_denied",
                f"path not under allowed roots: {path}",
                hint=(
                    f"allowed roots: {roots}; "
                    "set ANDROGUARD_MCP_ROOTS or ANDROGUARD_MCP_ALLOW_ANY=1"
                ),
            )

    @staticmethod
    def _release_app(app: Application) -> None:
        # apkparser.Permissions references its APK, creating a cycle that
        # could otherwise be finalized by GC on a different (unsafe) thread.
        app.apk.permissions = None
        app.apk.close()

    def _evict_expired(self) -> None:
        now = time.time()
        expired = [
            sid
            for sid, s in self._sessions.items()
            if now - s.last_used > self.ttl_seconds
        ]
        for sid in expired:
            session = self._sessions.pop(sid, None)
            if session is not None:
                self._release_app(session.app)

    def _evict_overflow(self) -> None:
        """Drop oldest sessions until there is room for one more open."""
        while len(self._sessions) >= self.max_sessions:
            oldest = min(self._sessions.values(), key=lambda s: s.last_used)
            self._sessions.pop(oldest.session_id, None)
            self._release_app(oldest.app)

    def open(self, path: str | Path) -> dict:
        resolved = self.resolve_path(path)
        self._evict_expired()
        self._evict_overflow()
        app = Application(resolved)
        session_id = str(uuid.uuid4())
        st = resolved.stat()
        session = Session(
            session_id=session_id,
            path=resolved,
            app=app,
            mtime=st.st_mtime,
        )
        self._sessions[session_id] = session
        summary = app.summary()
        return {
            "ok": True,
            "session_id": session_id,
            "path": str(resolved),
            "summary": summary,
        }

    def get(self, session_id: str) -> Session:
        self._evict_expired()
        session = self._sessions.get(session_id)
        if session is None:
            raise McpToolError(
                "session_expired",
                f"unknown or expired session_id: {session_id}",
                hint="call open_apk again",
            )
        try:
            mtime = session.path.stat().st_mtime
        except OSError as exc:
            self._sessions.pop(session_id, None)
            self._release_app(session.app)
            raise McpToolError(
                "not_found",
                f"APK disappeared: {session.path}",
            ) from exc
        if mtime != session.mtime:
            previous = session.app
            session.app = Application(session.path)
            session.mtime = mtime
            self._release_app(previous)
            # Source APK changed — drop any in-memory patch workspace.
            session.patch_files = None
            session.patch_project_root = None
            session.patch_dirty = False
        session.last_used = time.time()
        return session

    def close(self, session_id: str) -> dict:
        session = self._sessions.pop(session_id, None)
        if session is not None:
            self._release_app(session.app)
        return {
            "ok": True,
            "closed": session is not None,
            "session_id": session_id,
        }

    def close_all(self) -> int:
        """Release cached Rust-backed objects on the session owner thread."""
        count = len(self._sessions)
        for session in self._sessions.values():
            self._release_app(session.app)
        self._sessions.clear()
        return count

    def list_sessions(self) -> dict:
        self._evict_expired()
        items = [
            {
                "session_id": s.session_id,
                "path": str(s.path),
                "package": s.app.summary().get("package"),
                "last_used": s.last_used,
            }
            for s in self._sessions.values()
        ]
        return {"ok": True, "sessions": items}
