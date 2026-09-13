"""Instalacao isolada e launcher Headroom/Codex, sem dependencias no bootstrap."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import venv

ROOT = Path(__file__).resolve().parent
VERSION = "0.37.0"


def environment(runtime: Path) -> dict[str, str]:
    env = os.environ.copy()
    scripts = runtime / ("Scripts" if os.name == "nt" else "bin")
    env["PATH"] = str(scripts) + os.pathsep + env.get("PATH", "")
    env.update({
        "HEADROOM_BEACON": "off",
        "HEADROOM_TELEMETRY": "off",
        "HEADROOM_CCR_BACKEND": "memory",
        "HEADROOM_STATELESS": "true",
        "HEADROOM_CODE_MEMORY": "none",
    })
    return env


def executables(runtime: Path) -> tuple[Path, Path]:
    folder = runtime / ("Scripts" if os.name == "nt" else "bin")
    return (folder / ("python.exe" if os.name == "nt" else "python"),
            folder / ("headroom.exe" if os.name == "nt" else "headroom"))


def mcp_config(headroom: Path) -> str:
    # JSON strings are valid TOML basic strings, including escaped Windows paths.
    command = json.dumps(str(headroom), ensure_ascii=False)
    return (
        "# Gerado por headroom_codex.py; valido somente nesta maquina.\n"
        "[mcp_servers.headroom]\n"
        f"command = {command}\n"
        'args = ["mcp", "serve"]\n'
        "startup_timeout_sec = 60\n"
        "[mcp_servers.headroom.env]\n"
        'HEADROOM_BEACON = "off"\n'
        'HEADROOM_TELEMETRY = "off"\n'
        'HEADROOM_CCR_BACKEND = "memory"\n'
        'HEADROOM_STATELESS = "true"\n'
        'HEADROOM_PROXY_URL = "http://127.0.0.1:8787"\n'
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime", type=Path, default=ROOT / ".venv-headroom",
                        help="venv isolado; padrao: .venv-headroom na raiz do repo")
    parser.add_argument("action", choices=["install", "check", "run", "proxy", "configure-mcp"])
    parser.add_argument("codex_args", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    runtime = args.runtime.expanduser().resolve()
    python, headroom = executables(runtime)
    env = environment(runtime)
    extra = args.codex_args
    if extra[:1] == ["--"]:
        extra = extra[1:]
    if extra and args.action != "run":
        parser.error("argumentos adicionais sao permitidos apenas em run")

    if args.action == "install":
        if not python.exists():
            venv.EnvBuilder(with_pip=True).create(runtime)
        subprocess.run([str(python), "-m", "pip", "install", "-r",
                        str(Path(__file__).with_name("requirements-headroom.txt"))], check=True, env=env)
        return subprocess.call([str(python), "-m", "pip", "check"], env=env)

    if not headroom.exists() or not python.exists():
        parser.error("runtime ausente; execute install primeiro (ou informe --runtime)")
    installed = subprocess.check_output(
        [str(python), "-c", "from importlib.metadata import version; print(version('headroom-ai'))"],
        text=True, env=env).strip()
    if installed != VERSION:
        parser.error(f"versao esperada {VERSION}; encontrada {installed}. Execute install.")

    if args.action == "configure-mcp":
        target = ROOT / ".codex" / "config.toml"
        content = mcp_config(headroom)
        if target.exists():
            if target.read_text(encoding="utf-8") == content:
                print("MCP do projeto ja configurado.")
                return 0
            parser.error(".codex/config.toml ja existe e difere; revisar antes de alterar")
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("x", encoding="utf-8", newline="\n") as output:
            output.write(content)
        print(f"MCP configurado em {target}. Abra o projeto confiavel em nova sessao do Codex.")
        return 0

    if args.action == "check":
        subprocess.run([str(python), "-m", "pip", "check"], check=True, env=env)
        subprocess.run([str(headroom), "--version"], check=True, env=env)
        codex = shutil.which("codex", path=env["PATH"])
        if not codex:
            parser.error("Codex CLI nao encontrado no PATH")
        return subprocess.call([codex, "--version"], env=env)

    if args.action == "proxy":
        command = [str(headroom), "proxy", "--host", "127.0.0.1", "--port", "8787",
                   "--stateless", "--no-telemetry"]
    else:
        if not shutil.which("codex", path=env["PATH"]):
            parser.error("Codex CLI nao encontrado no PATH")
        # Opcoes do Codex ficam depois de --: nao podem habilitar learn/memory no Headroom.
        command = [str(headroom), "wrap", "codex", "--code-memory", "none", "--", *extra]
    return subprocess.call(command, env=env, cwd=ROOT)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, subprocess.CalledProcessError) as exc:
        print(f"Falha: {exc}", file=sys.stderr)
        raise SystemExit(1)
