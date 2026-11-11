"""Run a console program with scripted input and save the real session as a
terminal-style PNG (used for the report screenshots).

usage: python tools/term_shot.py <script.py> <out.png> <inputs-file> [title]
The inputs file holds one input line per line. The typed input is echoed
after the prompt, exactly as it would appear in an interactive console.
"""
import builtins
import io
import runpy
import sys
from contextlib import redirect_stdout
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FONT = "C:/Windows/Fonts/consola.ttf"
FONT_B = "C:/Windows/Fonts/consolab.ttf"
BG, FG, INPUT, BAR = (12, 12, 12), (204, 204, 204), (97, 214, 214), (45, 45, 45)


def capture(script: str, inputs: list[str]) -> str:
    feed = iter(inputs)
    buf = io.StringIO()

    def fake_input(prompt=""):
        buf.write(prompt)
        try:
            value = next(feed)
        except StopIteration:
            raise EOFError
        buf.write("\x01" + value + "\x02\n")      # mark typed input for coloring
        return value

    old = builtins.input
    builtins.input = fake_input
    sys.argv = [script]
    try:
        with redirect_stdout(buf):
            try:
                runpy.run_path(script, run_name="__main__")
            except (EOFError, SystemExit):
                pass
    finally:
        builtins.input = old
    return buf.getvalue()


def render(text: str, out: str, title: str, width_chars: int | None = None):
    font = ImageFont.truetype(FONT, 17)
    bold = ImageFont.truetype(FONT_B, 15)
    lines = text.rstrip("\n").split("\n")
    cw = font.getbbox("M")[2]
    lh = 22
    width_chars = width_chars or max(80, max(len(l.replace("\x01", "").replace("\x02", "")) for l in lines) + 2)
    W = 24 + cw * width_chars
    H = 40 + 16 + lh * len(lines)
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 32], fill=BAR)
    d.text((14, 7), title, font=bold, fill=(230, 230, 230))
    for i, dot in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        d.ellipse([W - 80 + i * 22, 10, W - 66 + i * 22, 24], fill=dot)
    y = 44
    for line in lines:
        x = 12
        color = FG
        seg = ""
        for ch in line:
            if ch in "\x01\x02":
                d.text((x, y), seg, font=font, fill=color)
                x += cw * len(seg)
                seg = ""
                color = INPUT if ch == "\x01" else FG
            else:
                seg += ch
        d.text((x, y), seg, font=font, fill=color)
        y += lh
    img.save(out)


if __name__ == "__main__":
    if sys.argv[1] == "--text":                 # render an existing transcript: --text <file> <out.png> [title]
        txt = Path(sys.argv[2]).read_text(encoding="utf-8")
        txt = "\n".join(("\x01" + l + "\x02") if l.startswith("$ ") else l for l in txt.splitlines())
        render(txt, sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else "bash")
        sys.exit()
    script, out, inputs_file = sys.argv[1:4]
    title = sys.argv[4] if len(sys.argv) > 4 else f"python {Path(script).name}"
    inputs = Path(inputs_file).read_text(encoding="utf-8").splitlines()
    text = capture(script, inputs)
    sys.stdout.reconfigure(encoding="utf-8")
    print(text.replace("\x01", "").replace("\x02", ""))
    render(text, out, title)
