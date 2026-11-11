"""Laboratory work no. 2 - frequency-analysis attack on a monoalphabetic cipher.
Variant V2. Author: Zastinceanu Mihai.

The script reproduces the attack step by step: letter frequencies of the
ciphertext (tables + charts), then the substitutions decided at every step.
Convention used in the intermediate texts (as in section 2.3 of the lab sheet):
UPPERCASE = still encrypted, lowercase = already decrypted.
"""
import re
import sys
from collections import Counter
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).parent
CIPHER = (HERE / "ciphertext_v2.txt").read_text(encoding="utf-8")

ENGLISH = {"A": 8.17, "B": 1.49, "C": 2.78, "D": 4.25, "E": 12.70, "F": 2.23, "G": 2.01, "H": 6.09,
           "I": 6.97, "J": 0.15, "K": 0.77, "L": 4.03, "M": 2.41, "N": 6.75, "O": 7.51, "P": 1.93,
           "Q": 0.09, "R": 5.99, "S": 6.33, "T": 9.06, "U": 2.76, "V": 0.98, "W": 2.36, "X": 0.15,
           "Y": 1.97, "Z": 0.07}

# Each step: (substitutions cipher->plain, reasoning). Filled in the order they were found.
STEPS = [
    ({"V": "e", "W": "t"},
     "Cele mai frecvente litere din criptogramă sunt V (11,04%) și W (10,11%); în engleză cele mai "
     "frecvente sunt E (12,70%) și T (9,06%). Presupunem V→e, W→t."),
    ({"Q": "h"},
     "Cel mai frecvent cuvânt din text este „tQe” (30 de apariții) – cel mai frecvent cuvânt de 3 litere "
     "din engleză este „the”, deci Q→h. Confirmare: Q are 4,49%, iar H în engleză 6,09%, iar digraful TH "
     "este cel mai frecvent."),
    ({"T": "a", "G": "n", "O": "d"},
     "Cuvântul dintr-o singură literă „T” apare de 12 ori – în engleză doar „a” și „I” sunt cuvinte de o "
     "literă; deoarece apare și în „thTt” → „tha?” (that) și „thTG” → „than”, T→a. Cuvântul „TGO” apare de "
     "10 ori: „a??” frecvent = „and”, deci G→n, O→d."),
    ({"N": "o", "C": "f"},
     "Cuvântul „WN” = „tN” apare de 14 ori → „to”, deci N→o. Cuvântul de 2 litere „NC” = „oC” este al "
     "doilea cel mai frecvent cuvânt (23 de apariții) → „of”, deci C→f."),
    ({"X": "i", "P": "s"},
     "Cuvintele „XG” = „Xn” (16 apariții) și „XW” = „Xt” (8 apariții) → „in”, „it”, deci X→i. "
     "Atunci „XP” → „iP” = „is”, iar „RaP”, „thXnJP” (plural cu -s) confirmă P→s."),
    ({"R": "w", "I": "r"},
     "„Ras” (6 apariții) → „was”, deci R→w. „foI” (6 apariții) → „for”, deci I→r; confirmă și "
     "„tIansfoIZations” → „transformations”."),
    ({"H": "c", "F": "y", "U": "p", "S": "l", "J": "g"},
     "Cuvântul „HrFUtoSoJF” apare de 5 ori – tema textului (istoria criptografiei) sugerează "
     "„cryptology”: H→c, F→y, U→p, S→l, J→g. Confirmă și „onSF” → „only”, „Jreat” → „great”, "
     "„thinJs” → „things”."),
    ({"Z": "m", "K": "v", "D": "u"},
     "„Zore” → „more”, „tiZe” → „time”, deci Z→m. „haKe” (3 apariții) → „have”, deci K→v. "
     "„trDe” → „true”, „soDght” → „sought”, deci D→u."),
    ({"A": "b", "L": "k", "M": "z", "B": "q", "Y": "x", "E": "j"},
     "Literele rare rămase rezultă din cuvinte aproape descifrate: „Aeginnings” → „beginnings” (A→b), "
     "„Lnown” → „known” (L→k), „puMMle” → „puzzle” (M→z), „Buasi” → „quasi” (B→q), "
     "„eYactly”, „neYt” → „exactly”, „next” (Y→x), „Eust” → „just” (E→j)."),
]


def letters(text):
    return [ch.upper() for ch in text if ch.isascii() and ch.isalpha()]


def apply(text, key):
    """Decrypted letters in lowercase, still-encrypted letters in UPPERCASE."""
    out = []
    for ch in text:
        if ch.isascii() and ch.isalpha():
            out.append(key.get(ch.upper(), ch.upper()))
        else:
            out.append(ch)
    return "".join(out)


def final_plaintext(text, key):
    """Full decryption keeping the original letter case."""
    out = []
    for ch in text:
        if ch.isascii() and ch.isalpha():
            p = key[ch.upper()]
            out.append(p.upper() if ch.isupper() else p)
        else:
            out.append(ch)
    return "".join(out)


def charts(freq_pct):
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.2))
    axes[0].bar(list(ENGLISH), list(ENGLISH.values()), color="#4C72B0")
    axes[0].set_title("Frecvența literelor în limba engleză (%)")
    axes[1].bar(list(freq_pct), list(freq_pct.values()), color="#C44E52")
    axes[1].set_title("Frecvența literelor în criptograma V2 (%)")
    for ax in axes:
        ax.set_ylim(0, 14)
        ax.grid(axis="y", alpha=.3)
    fig.tight_layout()
    fig.savefig(HERE / "img" / "frecvente.png", dpi=130)

    srt = dict(sorted(freq_pct.items(), key=lambda kv: -kv[1]))
    eng = dict(sorted(ENGLISH.items(), key=lambda kv: -kv[1]))
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.2))
    axes[0].bar(list(eng), list(eng.values()), color="#4C72B0")
    axes[0].set_title("Engleză – ordonat descrescător")
    axes[1].bar(list(srt), list(srt.values()), color="#C44E52")
    axes[1].set_title("Criptograma V2 – ordonat descrescător")
    for ax in axes:
        ax.set_ylim(0, 14)
        ax.grid(axis="y", alpha=.3)
    fig.tight_layout()
    fig.savefig(HERE / "img" / "frecvente_sortat.png", dpi=130)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    (HERE / "img").mkdir(exist_ok=True)
    cnt = Counter(letters(CIPHER))
    total = sum(cnt.values())
    freq = {ch: cnt.get(ch, 0) for ch in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"}
    pct = {ch: 100 * n / total for ch, n in freq.items()}
    charts(pct)

    md = ["# Rezultatele atacului (generat de frequency_attack.py)\n",
          f"Număr total de litere în criptogramă: **{total}**\n",
          "## Tabelul 1. Frecvența literelor în criptogramă (alfabetic)\n",
          "| Literă | " + " | ".join(freq) + " |",
          "|---|" + "---|" * 26,
          "| Nr. | " + " | ".join(str(v) for v in freq.values()) + " |",
          "| % | " + " | ".join(f"{v:.2f}".replace(".", ",") for v in pct.values()) + " |\n",
          "## Tabelul 2. Frecvența literelor în criptogramă (descrescător)\n"]
    srt = sorted(pct.items(), key=lambda kv: -kv[1])
    md += ["| Literă | " + " | ".join(k for k, _ in srt) + " |",
           "|---|" + "---|" * 26,
           "| % | " + " | ".join(f"{v:.2f}".replace(".", ",") for _, v in srt) + " |\n"]

    words = Counter(re.findall(r"[a-z]+", CIPHER.lower()))
    md.append("## Tabelul 3. Cele mai frecvente cuvinte din criptogramă\n")
    md.append("| Cuvânt | " + " | ".join(w.upper() for w, _ in words.most_common(12)) + " |")
    md.append("|---|" + "---|" * 12)
    md.append("| Apariții | " + " | ".join(str(n) for _, n in words.most_common(12)) + " |\n")

    key = {}
    for i, (subs, why) in enumerate(STEPS, 1):
        key.update(subs)
        md.append(f"## Pasul {i}: " + ", ".join(f"{c} → {p}" for c, p in subs.items()) + "\n")
        md.append(why + "\n")
        md.append("```text\n" + apply(CIPHER, key).strip() + "\n```\n")

    assert len(key) == 26 and len(set(key.values())) == 26, "key must be a permutation"
    plain = final_plaintext(CIPHER, key)
    (HERE / "plaintext_v2.txt").write_text(plain, encoding="utf-8")
    inv = {p: c for c, p in key.items()}
    md.append("## Cheia reconstituită\n")
    md.append("| Text clar | " + " | ".join("abcdefghijklmnopqrstuvwxyz") + " |")
    md.append("|---|" + "---|" * 26)
    md.append("| Criptogramă | " + " | ".join(inv[p] for p in "abcdefghijklmnopqrstuvwxyz") + " |\n")
    md.append("## Mesajul decriptat\n")
    md.append("```text\n" + plain.strip() + "\n```\n")
    (HERE / "attack_steps.md").write_text("\n".join(md), encoding="utf-8")

    print("Letter frequencies (descending):")
    for ch, v in srt:
        print(f"  {ch}: {freq[ch]:4d}  {v:5.2f}%")
    print("\nRecovered key (plain -> cipher):")
    print("  plain : " + " ".join("abcdefghijklmnopqrstuvwxyz"))
    print("  cipher: " + " ".join(inv[p] for p in "abcdefghijklmnopqrstuvwxyz"))
    print("\nPlaintext:\n" + plain)


if __name__ == "__main__":
    main()
