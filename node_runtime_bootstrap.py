#!/usr/bin/env python3
"""Ensure Node.js 22 is available for yt-dlp's YouTube EJS runtime.

Uses a host-provided Node 22+ when available. Otherwise downloads the latest
stable Node 22 Linux binary from nodejs.org and verifies its SHA-256 checksum.
No npm packages or project JavaScript dependencies are required.
"""
from __future__ import annotations

import hashlib
import io
import json
import os
import platform
import re
import shutil
import stat
import sys
import tarfile
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RUNTIME_DIR = Path(os.getenv("NODE_RUNTIME_DIR", str(ROOT / ".runtime" / "node22"))).expanduser()
MINIMUM = (22, 0, 0)
TIMEOUT = 35
USER_AGENT = "TalkinChat-Node22-bootstrap/1.0"


def version_of(binary: str | Path) -> tuple[int, int, int] | None:
    import subprocess
    try:
        result = subprocess.run(
            [str(binary), "--version"], capture_output=True, text=True,
            timeout=5, check=False,
        )
        text = (result.stdout or result.stderr or "").strip()
        match = re.search(r"v?(\d+)\.(\d+)\.(\d+)", text)
        if result.returncode == 0 and match:
            return tuple(int(x) for x in match.groups())
    except Exception:
        pass
    return None


def supported(binary: str | Path) -> bool:
    version = version_of(binary)
    return bool(version and version >= MINIMUM)


def fetch(url: str, timeout: int = TIMEOUT) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def linux_arch() -> str:
    machine = platform.machine().lower()
    mapping = {
        "x86_64": "x64", "amd64": "x64",
        "aarch64": "arm64", "arm64": "arm64",
    }
    if machine not in mapping:
        raise RuntimeError(
            f"معمارية الخادم {machine!r} غير مدعومة تلقائياً. "
            "يلزم Node.js 22 مثبتاً يدوياً عبر NODE_BINARY."
        )
    if sys.platform != "linux":
        raise RuntimeError("التثبيت التلقائي مخصص لخوادم Linux.")
    return mapping[machine]


def find_existing() -> str | None:
    configured = os.getenv("NODE_BINARY", "").strip()
    candidates = []
    if configured:
        candidates.append(configured)
    system_node = shutil.which("node")
    if system_node:
        candidates.append(system_node)
    candidates.append(str(RUNTIME_DIR / "bin" / "node"))
    seen = set()
    for candidate in candidates:
        if candidate in seen:
            continue
        seen.add(candidate)
        if Path(candidate).is_file() and supported(candidate):
            return str(Path(candidate).resolve())
    return None


def install_node22() -> str:
    arch = linux_arch()
    print("[NODE] No supported Node.js 22+ found; resolving latest Node 22 release.", flush=True)
    index = json.loads(fetch("https://nodejs.org/dist/index.json").decode("utf-8"))
    release = next(
        (item for item in index if str(item.get("version", "")).startswith("v22.")
         and bool(item.get("lts"))),
        None,
    )
    if not release:
        release = next((item for item in index if str(item.get("version", "")).startswith("v22.")), None)
    if not release:
        raise RuntimeError("تعذر العثور على إصدار Node.js 22 مستقر.")
    version = release["version"]
    archive_name = f"node-{version}-linux-{arch}.tar.xz"
    base = f"https://nodejs.org/dist/{version}"
    checksums = fetch(f"{base}/SHASUMS256.txt").decode("utf-8", "replace")
    expected = None
    for line in checksums.splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[-1].lstrip("*") == archive_name:
            expected = parts[0].lower()
            break
    if not expected:
        raise RuntimeError(f"لم يتم العثور على بصمة SHA-256 للملف {archive_name}")
    archive = fetch(f"{base}/{archive_name}", timeout=90)
    actual = hashlib.sha256(archive).hexdigest()
    if actual != expected:
        raise RuntimeError("فشل التحقق من SHA-256 لملف Node.js؛ تم إلغاء التثبيت.")
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    target = RUNTIME_DIR / "bin" / "node"
    target.parent.mkdir(parents=True, exist_ok=True)
    member_name = f"node-{version}-linux-{arch}/bin/node"
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:xz") as package:
        member = package.getmember(member_name)
        source = package.extractfile(member)
        if source is None:
            raise RuntimeError("ملف Node.js التنفيذي غير موجود داخل الحزمة.")
        fd, temporary = tempfile.mkstemp(prefix="node22-", dir=str(target.parent))
        try:
            with os.fdopen(fd, "wb") as output:
                shutil.copyfileobj(source, output)
            os.chmod(temporary, os.stat(temporary).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
            os.replace(temporary, target)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
    if not supported(target):
        raise RuntimeError("تم تنزيل Node.js لكن فشل فحص الإصدار بعد التثبيت.")
    print(f"[NODE] Installed verified {version} at {target}", flush=True)
    return str(target.resolve())


def main() -> int:
    try:
        node = find_existing() or install_node22()
        version = version_of(node)
        print(f"[NODE] Ready: {node} (v{'.'.join(map(str, version))})", flush=True)
        print(node)
        return 0
    except Exception as exc:
        print(f"[NODE][FATAL] {type(exc).__name__}: {exc}", file=sys.stderr, flush=True)
        print(
            "[NODE][HELP] Install Node.js 22+ and set NODE_BINARY to its absolute path, "
            "or allow start.sh to access nodejs.org.",
            file=sys.stderr, flush=True,
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
