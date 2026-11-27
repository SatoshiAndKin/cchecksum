"""Validate repository formatting without publishing changes."""

import os
import subprocess
from pathlib import Path

files = subprocess.check_output(["git", "ls-files", "-z"], text=True).split("\0")
files = [name for name in files if name and Path(name).is_file()]
python_files = [name for name in files if name.endswith(".py")]
if python_files:
    subprocess.run(
        [
            "pyupgrade",
            "--" + os.environ["PYUPGRADE_TARGET"] + "-plus",
            "--exit-zero-even-if-changed",
            *python_files,
        ],
        check=True,
    )
for args in (
    [
        "autoflake",
        "--remove-all-unused-imports",
        "--in-place",
        "--expand-star-imports",
        "--ignore-init-module-imports",
        "-r",
        ".",
    ],
    ["isort", "."],
    ["black", "."],
):
    subprocess.run(args, check=True)
for extensions, args in (
    ((".json", ".yml", ".yaml"), ["npx", "--yes", "prettier@3.8.0", "--write"]),
    ((".md",), ["npx", "--yes", "markdownlint-cli2@0.21.0", "--no-globs", "--fix"]),
    ((".toml",), ["npx", "--yes", "@taplo/cli@0.7.0", "format"]),
):
    selected = [name for name in files if name.endswith(extensions)]
    if selected:
        result = subprocess.run([*args, *selected])
        if extensions == (".md",) and result.returncode:
            print(
                "Markdown retains the existing autofix-only contract; remaining findings are informational."
            )
        else:
            result.check_returncode()
subprocess.run(["git", "diff", "--exit-code"], check=True)
