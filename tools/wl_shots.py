"""Render a Wolfram session transcript (from wl_session.wls) as terminal-style
screenshots, one image per range of cells.

usage: python tools/wl_shots.py <transcript.txt> <out-prefix> <first-last> [<first-last> ...]
e.g.   python tools/wl_shots.py lab5/wolfram/transcript.txt lab5/img/wl_rsa 1-13
"""
import re
import sys
import textwrap
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from term_shot import render  # noqa: E402

WIDTH = 132


def cells(text: str) -> dict[int, list[str]]:
    out, cur = {}, None
    for line in text.splitlines():
        m = re.match(r"(In|Out)\[(\d+)\]", line)
        if m:
            cur = int(m.group(2))
        if cur is not None:
            out.setdefault(cur, []).append(line)
    return out


def wrap(line: str) -> list[str]:
    if len(line) <= WIDTH:
        return [line]
    indent = " " * (len(line) - len(line.lstrip()) if not line.startswith(("In[", "Out[")) else
                    line.index("=") + 2)
    return textwrap.wrap(line, WIDTH, subsequent_indent=indent, break_long_words=True,
                         break_on_hyphens=False)


def main():
    src, prefix, *ranges = sys.argv[1:]
    cs = cells(Path(src).read_text(encoding="utf-8"))
    for rg in ranges:
        a, b = map(int, rg.split("-"))
        lines = []
        for i in range(a, b + 1):
            for line in cs.get(i, []):
                is_in = line.startswith("In[") or (lines and lines[-1].startswith("\x01") and line.startswith("        "))
                for w in wrap(line):
                    lines.append("\x01" + w + "\x02" if is_in else w)
            lines.append("")
        out = f"{prefix}.png" if len(ranges) == 1 else f"{prefix}_{a}-{b}.png"
        render("\n".join(lines), out, "Wolfram Engine 15.0 - wolframscript", width_chars=WIDTH + 4)
        print("saved", out)


if __name__ == "__main__":
    main()
