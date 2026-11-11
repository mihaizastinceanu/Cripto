"""Lucrarea de laborator nr. 4 - Cifruri bloc. Algoritmul DES.
Sarcina 2.3 (n = 25, 25 mod 11 = 3): în algoritmul DES este dat K+.
Să se determine cheia de rundă Ki pentru un i dat.

Autor: Zastinceanu Mihai

K+ (56 de biți) se poate introduce în binar (56 de cifre 0/1) sau hexazecimal
(14 cifre), se poate genera aleatoriu sau se poate obține din cheia de 8 simboluri
prin PC-1. Programul afișează tabelele folosite și toți pașii intermediari.
"""
import secrets

# Permuted Choice 1 (64 -> 56 biți) - folosită doar pentru a obține K+ din cheia de 8 simboluri
PC1 = [57, 49, 41, 33, 25, 17, 9,
       1, 58, 50, 42, 34, 26, 18,
       10, 2, 59, 51, 43, 35, 27,
       19, 11, 3, 60, 52, 44, 36,
       63, 55, 47, 39, 31, 23, 15,
       7, 62, 54, 46, 38, 30, 22,
       14, 6, 61, 53, 45, 37, 29,
       21, 13, 5, 28, 20, 12, 4]

# Numărul de deplasări circulare la stânga pentru fiecare rundă 1..16
SHIFTS = [1, 1, 2, 2, 2, 2, 2, 2, 1, 2, 2, 2, 2, 2, 2, 1]

# Permuted Choice 2 (56 -> 48 biți)
PC2 = [14, 17, 11, 24, 1, 5,
       3, 28, 15, 6, 21, 10,
       23, 19, 12, 4, 26, 8,
       16, 7, 27, 20, 13, 2,
       41, 52, 31, 37, 47, 55,
       30, 40, 51, 45, 33, 48,
       44, 49, 39, 56, 34, 53,
       46, 42, 50, 36, 29, 32]


class InputError(ValueError):
    pass


def group(bits: str, n: int) -> str:
    return " ".join(bits[i:i + n] for i in range(0, len(bits), n))


def to_hex(bits: str) -> str:
    return f"{int(bits, 2):0{len(bits) // 4}X}"


def permute(bits: str, table: list[int]) -> str:
    """Bit i of the result is bit table[i] of the input (positions start at 1)."""
    return "".join(bits[p - 1] for p in table)


def rotl(bits: str, n: int) -> str:
    return bits[n:] + bits[:n]


def print_table(name: str, table: list[int], cols: int):
    print(f"  {name}:")
    for r in range(0, len(table), cols):
        print("     " + " ".join(f"{v:2d}" for v in table[r:r + cols]))


def round_key(k_plus: str, i: int, verbose=True) -> str:
    """K+ (56 bits) -> Ki (48 bits), printing every intermediate step."""
    c, d = k_plus[:28], k_plus[28:]
    if verbose:
        print("\n Pasul 1. Împărțim K+ în două jumătăți de câte 28 de biți:")
        print(f"   C0 = {group(c, 7)}")
        print(f"   D0 = {group(d, 7)}")
        print("\n Pasul 2. Deplasări circulare la stânga (tabelul deplasărilor):")
        print("   Runda   : " + " ".join(f"{r:2d}" for r in range(1, 17)))
        print("   Deplasări: " + " ".join(f"{s:2d}" for s in SHIFTS))
        print(f"   Pentru i = {i}: numărul total de deplasări = "
              f"{' + '.join(map(str, SHIFTS[:i]))} = {sum(SHIFTS[:i])}")
    for r in range(1, i + 1):
        c, d = rotl(c, SHIFTS[r - 1]), rotl(d, SHIFTS[r - 1])
        if verbose:
            print(f"   C{r:<2}= {group(c, 7)}   (C{r - 1} << {SHIFTS[r - 1]})")
            print(f"   D{r:<2}= {group(d, 7)}   (D{r - 1} << {SHIFTS[r - 1]})")
    cd = c + d
    k = permute(cd, PC2)
    if verbose:
        print(f"\n Pasul 3. Concatenăm C{i}D{i} (56 de biți):")
        print(f"   C{i}D{i} = {group(cd, 7)}")
        print_table("Tabelul PC-2 (56 -> 48 de biți)", PC2, 6)
        print("   Aplicăm PC-2: bitul j al lui K{0} este bitul PC2[j] din C{0}D{0}:".format(i))
        for j in range(0, 48, 6):
            src = ", ".join(f"b{p}={cd[p - 1]}" for p in PC2[j:j + 6])
            print(f"     biții {j + 1:2d}-{j + 6:2d}: {src}  -> {k[j:j + 6]}")
        print(f"\n Rezultat: K{i} = {group(k, 6)}")
        print(f"           K{i} = {to_hex(k)} (hex)")
    return k


def all_round_keys(k_plus: str) -> list[str]:
    return [round_key(k_plus, i, verbose=False) for i in range(1, 17)]


# ------------------------------------------------------------------- input
def parse_kplus(raw: str) -> str:
    s = raw.replace(" ", "").strip()
    if len(s) == 56 and set(s) <= {"0", "1"}:
        return s
    if len(s) == 14 and all(ch in "0123456789abcdefABCDEF" for ch in s):
        return f"{int(s, 16):056b}"
    raise InputError("K+ trebuie să aibă 56 de biți: 56 de cifre binare (0/1) sau 14 cifre hexazecimale "
                     f"(0-9, A-F). Ați introdus {len(s)} caractere.")


def parse_round(raw: str) -> int:
    raw = raw.strip()
    if not raw.isdigit() or not 1 <= int(raw) <= 16:
        raise InputError("numărul rundei i trebuie să fie un întreg de la 1 la 16.")
    return int(raw)


def parse_key8(raw: str) -> str:
    if len(raw) != 8 or not all(32 <= ord(ch) < 127 for ch in raw):
        raise InputError(f"cheia trebuie să conțină exact 8 simboluri ASCII (ați introdus {len(raw)}).")
    return raw


def parse_choice(raw: str) -> str:
    if raw.strip() not in {"0", "1", "2", "3"}:
        raise InputError("alegeți 0, 1, 2 sau 3.")
    return raw.strip()


def ask(prompt, parse):
    while True:
        raw = input(prompt)
        try:
            return parse(raw)
        except InputError as e:
            print(f"  Eroare: {e} Încercați din nou.")


def main():
    print("=" * 74)
    print(" Lab 4 - DES, sarcina 2.3: dat fiind K+, determinăm cheia de rundă Ki")
    print("=" * 74)
    while True:
        print("\n Cum se obține K+?")
        print("  1 - introduc K+ (56 de biți în binar sau 14 cifre hex)")
        print("  2 - K+ generat aleatoriu")
        print("  3 - din cheia DES de 8 simboluri (K+ = PC-1(K))")
        print("  0 - ieșire")
        choice = ask("Opțiunea: ", parse_choice)
        if choice == "0":
            break
        if choice == "1":
            k_plus = ask("K+ = ", parse_kplus)
        elif choice == "2":
            k_plus = f"{secrets.randbits(56):056b}"
            print("  K+ a fost generat aleatoriu.")
        else:
            key = ask("Cheia (8 simboluri): ", parse_key8)
            k64 = "".join(f"{ord(ch):08b}" for ch in key)
            print(f"  K (ASCII)   = {group(k64, 8)}  ({to_hex(k64)})")
            print_table("Tabelul PC-1 (64 -> 56 de biți)", PC1, 7)
            k_plus = permute(k64, PC1)
        print(f"  K+ = {group(k_plus, 7)}")
        print(f"  K+ = {to_hex(k_plus)} (hex)")
        i = ask("Runda i (1..16): ", parse_round)
        round_key(k_plus, i)


if __name__ == "__main__":
    main()
