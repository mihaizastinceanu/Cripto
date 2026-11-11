"""Laboratory Work No. 1 - Caesar cipher and Caesar cipher with a permutation
over the Romanian alphabet (n = 31).

Author: Zastinceanu Mihai

Letters are encoded only through Table 2 of the lab sheet (A = 0 ... Z = 30);
character codes of the language (ord/chr) are never used for the shift.
"""

# Table 2 - letter encoding of the Romanian alphabet (n = 31)
ALPHABET = ["A", "Ă", "Â", "B", "C", "D", "E", "F", "G", "H", "I", "Î", "J", "K", "L", "M",
            "N", "O", "P", "Q", "R", "S", "Ș", "T", "Ț", "U", "V", "W", "X", "Y", "Z"]
N = len(ALPHABET)                                   # 31
CODE = {letter: i for i, letter in enumerate(ALPHABET)}

# lowercase -> uppercase, plus the cedilla variants Ş/Ţ that some keyboards produce
UPPER = {low: up for low, up in zip("aăâbcdefghiîjklmnopqrsștțuvwxyz", ALPHABET)}
UPPER.update({"Ş": "Ș", "ş": "Ș", "Ţ": "Ț", "ţ": "Ț"})
UPPER.update({up: up for up in ALPHABET})

ALLOWED = "A-Z, a-z, Ă Â Î Ș Ț, ă â î ș ț (spaces are removed)"


class InputError(ValueError):
    pass


def normalize(text: str) -> str:
    """Convert to uppercase, drop spaces; reject anything that is not a Romanian letter."""
    out = []
    for pos, ch in enumerate(text, start=1):
        if ch == " ":
            continue
        if ch not in UPPER:
            raise InputError(f"invalid character '{ch}' at position {pos}. Allowed: {ALLOWED}.")
        out.append(UPPER[ch])
    if not out:
        raise InputError("the text is empty - enter at least one letter.")
    return "".join(out)


def parse_key(raw: str) -> int:
    raw = raw.strip()
    if not raw.lstrip("-").isdigit():
        raise InputError(f"'{raw}' is not an integer. The key must be an integer from 1 to {N - 1}.")
    k = int(raw)
    if not 1 <= k <= N - 1:
        raise InputError(f"key {k} is out of range. The key must be an integer from 1 to {N - 1}.")
    return k


def parse_keyword(raw: str) -> str:
    kw = normalize(raw)
    if len(kw) < 7:
        raise InputError(f"the keyword '{kw}' has {len(kw)} letters; it must have at least 7 letters "
                         f"of the Romanian alphabet.")
    return kw


def permuted_alphabet(keyword: str) -> list[str]:
    """Distinct letters of the keyword first (first occurrence kept), then the rest in natural order."""
    order = []
    for letter in keyword + "".join(ALPHABET):
        if letter not in order:
            order.append(letter)
    return order


def shift(text: str, k: int, alphabet: list[str]) -> str:
    """c = (x + k) mod n, where x is the position of the letter in `alphabet`."""
    pos = {letter: i for i, letter in enumerate(alphabet)}
    return "".join(alphabet[(pos[ch] + k) % N] for ch in text)


def encrypt(text: str, k: int, alphabet=ALPHABET) -> str:
    return shift(text, k, alphabet)


def decrypt(text: str, k: int, alphabet=ALPHABET) -> str:
    # (y - k) mod n; Python's % already returns a value in 0..n-1, but we add n to be explicit
    return shift(text, (N - k) % N, alphabet)


# ---------------------------------------------------------------- console UI
def ask(prompt: str, parse):
    while True:
        raw = input(prompt)
        try:
            return parse(raw)
        except InputError as e:
            print(f"  Error: {e} Try again.")


def ask_choice(prompt: str, options: dict[str, str]) -> str:
    def parse(raw):
        raw = raw.strip().upper()
        if raw not in options:
            raise InputError(f"choose one of: {', '.join(options)}.")
        return raw
    return ask(prompt, parse)


def main():
    print("=" * 64)
    print(" Lab 1 - Caesar cipher over the Romanian alphabet (n = 31)")
    print("=" * 64)
    print(" Alphabet:", " ".join(ALPHABET))
    while True:
        print()
        print(" 1 - Caesar cipher (one key, Task 1.1)")
        print(" 2 - Caesar cipher with permutation (two keys, Task 1.2)")
        print(" 0 - Exit")
        variant = ask_choice("Variant: ", {"1": "", "2": "", "0": ""})
        if variant == "0":
            break
        op = ask_choice("Operation - E (encrypt) / D (decrypt): ", {"E": "", "D": ""})
        k1 = ask(f"Key 1 (integer 1..{N - 1}): ", parse_key)
        alphabet = ALPHABET
        if variant == "2":
            k2 = ask("Key 2 (keyword, >= 7 Romanian letters): ", parse_keyword)
            alphabet = permuted_alphabet(k2)
            print(" Permuted alphabet:", " ".join(alphabet))
        label = "Message" if op == "E" else "Ciphertext"
        text = ask(f"{label}: ", normalize)
        print(f" Prepared text: {text}")
        if op == "E":
            print(f" Ciphertext   : {encrypt(text, k1, alphabet)}")
        else:
            print(f" Message      : {decrypt(text, k1, alphabet)}")


if __name__ == "__main__":
    main()
