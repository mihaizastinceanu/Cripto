"""Lucrarea de laborator nr. 3 - Sarcina 3.1: cifrul Playfair pentru limba română.
Autor: Zastinceanu Mihai (nr. 25 în lista grupei -> număr impar -> sarcina 3.1).

Alfabetul român are 31 de litere. Matricea folosită are 5 linii x 6 coloane = 30 de
celule, deci o literă trebuie eliminată - la fel cum în engleză J se înlocuiește cu I.
Se elimină Q (frecvența 0,00% în limba română, apare doar în cuvinte străine) și se
înlocuiește cu K, care are același sunet; la decriptare se restabilește intuitiv.
"""

ALPHABET = ["A", "Ă", "Â", "B", "C", "D", "E", "F", "G", "H", "I", "Î", "J", "K", "L", "M",
            "N", "O", "P", "Q", "R", "S", "Ș", "T", "Ț", "U", "V", "W", "X", "Y", "Z"]
ROWS, COLS = 5, 6
DROPPED, REPLACEMENT = "Q", "K"
MATRIX_LETTERS = [ch for ch in ALPHABET if ch != DROPPED]          # 30 letters
FILLER, FILLER2 = "X", "Y"          # inserted between double letters / at the end

UPPER = {low: up for low, up in zip("aăâbcdefghiîjklmnopqrsștțuvwxyz", ALPHABET)}
UPPER.update({"ş": "Ș", "Ş": "Ș", "ţ": "Ț", "Ţ": "Ț"})
UPPER.update({up: up for up in ALPHABET})
ALLOWED = "'A'-'Z', 'a'-'z' și Ă Â Î Ș Ț / ă â î ș ț (spațiile se elimină)"


class InputError(ValueError):
    pass


def normalize(text: str) -> str:
    out = []
    for pos, ch in enumerate(text, 1):
        if ch == " ":
            continue
        if ch not in UPPER:
            raise InputError(f"caracterul '{ch}' (poziția {pos}) nu este permis. "
                             f"Caractere permise: {ALLOWED}.")
        out.append(UPPER[ch])
    if not out:
        raise InputError("textul este gol.")
    return "".join(out)


def parse_key(raw: str) -> str:
    key = normalize(raw)
    if len(key) < 7:
        raise InputError(f"cheia '{key}' are {len(key)} litere; lungimea cheii trebuie să fie de cel puțin 7.")
    return key


# ------------------------------------------------------------------ matrix
def build_matrix(key: str) -> list[list[str]]:
    """Key letters first (repetitions removed, Q->K), then the rest of the alphabet in order."""
    seen = []
    for ch in key.replace(DROPPED, REPLACEMENT) + "".join(MATRIX_LETTERS):
        if ch not in seen:
            seen.append(ch)
    return [seen[r * COLS:(r + 1) * COLS] for r in range(ROWS)]


def positions(matrix):
    return {ch: (r, c) for r, row in enumerate(matrix) for c, ch in enumerate(row)}


# ----------------------------------------------------------- text preparation
def prepare(text: str) -> list[str]:
    """Q->K, split into pairs, insert X between two equal letters of a pair, pad to even length."""
    text = text.replace(DROPPED, REPLACEMENT)
    pairs, i = [], 0
    while i < len(text):
        a = text[i]
        b = text[i + 1] if i + 1 < len(text) else None
        if b is None:
            pairs.append(a + (FILLER if a != FILLER else FILLER2))
            i += 1
        elif a == b:
            pairs.append(a + (FILLER if a != FILLER else FILLER2))
            i += 1
        else:
            pairs.append(a + b)
            i += 2
    return pairs


# ------------------------------------------------------------ encrypt/decrypt
def transform_pair(pair: str, pos, matrix, step: int) -> tuple[str, str]:
    """step = +1 for encryption, -1 for decryption. Returns (result, rule used)."""
    (r1, c1), (r2, c2) = pos[pair[0]], pos[pair[1]]
    if r1 == r2:                                    # same row -> right / left neighbour
        return matrix[r1][(c1 + step) % COLS] + matrix[r2][(c2 + step) % COLS], "aceeași linie"
    if c1 == c2:                                    # same column -> below / above
        return matrix[(r1 + step) % ROWS][c1] + matrix[(r2 + step) % ROWS][c2], "aceeași coloană"
    return matrix[r1][c2] + matrix[r2][c1], "dreptunghi"   # rectangle -> swap columns


def encrypt(text: str, key: str, verbose=False) -> str:
    matrix = build_matrix(key)
    pos = positions(matrix)
    pairs = prepare(text)
    out = []
    for p in pairs:
        res, rule = transform_pair(p, pos, matrix, +1)
        out.append(res)
        if verbose:
            print(f"   {p} -> {res}  ({rule})")
    return "".join(out)


def decrypt(cipher: str, key: str, verbose=False) -> str:
    if len(cipher) % 2:
        raise InputError(f"criptograma are {len(cipher)} litere; trebuie să aibă un număr par de litere.")
    matrix = build_matrix(key)
    pos = positions(matrix)
    if DROPPED in cipher:
        raise InputError(f"litera {DROPPED} nu poate apărea într-o criptogramă Playfair (nu e în matrice).")
    out = []
    for i in range(0, len(cipher), 2):
        p = cipher[i:i + 2]
        if p[0] == p[1]:
            raise InputError(f"perechea '{p}' are două litere egale - nu poate fi produsă de Playfair.")
        res, rule = transform_pair(p, pos, matrix, -1)
        out.append(res)
        if verbose:
            print(f"   {p} -> {res}  ({rule})")
    return "".join(out)


def strip_fillers(text: str) -> str:
    """Helper for the reader: remove X put between equal letters and a final filler."""
    out = list(text)
    i = 1
    res = [out[0]] if out else []
    while i < len(out):
        if out[i] in (FILLER, FILLER2) and i + 1 < len(out) and out[i - 1] == out[i + 1] and i % 2 == 1:
            i += 1
            continue
        res.append(out[i])
        i += 1
    if len(res) > 1 and res[-1] in (FILLER, FILLER2) and len(text) % 2 == 0:
        res.pop()
    return "".join(res)


# --------------------------------------------------------------------- UI
def ask(prompt, parse):
    while True:
        raw = input(prompt)
        try:
            return parse(raw)
        except InputError as e:
            print(f"  Eroare: {e} Încercați din nou.")


def ask_choice(prompt, options):
    def parse(raw):
        raw = raw.strip().upper()
        if raw not in options:
            raise InputError(f"alegeți una din variantele: {', '.join(options)}.")
        return raw
    return ask(prompt, parse)


def print_matrix(matrix):
    print("  Matricea de criptare (5 x 6):")
    for row in matrix:
        print("     " + "  ".join(row))


def main():
    print("=" * 66)
    print(" Lab 3 - Cifrul Playfair pentru limba română (31 de litere)")
    print("=" * 66)
    print(f" Matrice 5x6 = 30 de celule: litera {DROPPED} (frecvență 0% în română) se înlocuiește cu "
          f"{REPLACEMENT}.")
    print(f" Literă de umplere: {FILLER} (între două litere egale dintr-o pereche și la final).")
    while True:
        print()
        op = ask_choice("Operația - C (criptare) / D (decriptare) / 0 (ieșire): ", ["C", "D", "0"])
        if op == "0":
            break
        key = ask("Cheia (cel puțin 7 litere): ", parse_key)
        matrix = build_matrix(key)
        print_matrix(matrix)
        if op == "C":
            text = ask("Mesajul: ", normalize)
            print(f"  Text pregătit : {text}")
            pairs = prepare(text)
            print(f"  Perechi       : {' '.join(pairs)}")
            print("  Criptarea perechilor:")
            c = encrypt(text, key, verbose=True)
            print(f"  Criptograma   : {c}")
        else:
            def parse_cipher(raw):
                c = normalize(raw)
                decrypt(c, key)              # validates (even length, no Q, no double pairs)
                return c
            c = ask("Criptograma: ", parse_cipher)
            print(f"  Perechi       : {' '.join(c[i:i + 2] for i in range(0, len(c), 2))}")
            print("  Decriptarea perechilor:")
            m = decrypt(c, key, verbose=True)
            print(f"  Mesaj decriptat       : {m}")
            print(f"  Fără literele X de umplere (sugestie): {strip_fillers(m)}")
            print("  Spațiile și literele Q se restabilesc manual, după sens.")


if __name__ == "__main__":
    main()
