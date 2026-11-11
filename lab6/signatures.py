"""Lucrarea de laborator nr. 6 - Funcții hash și semnături digitale.
Autor: Zastinceanu Mihai (k = 25)

Mesajul m = textul decriptat în Lab 2 (message.txt, UTF-8, sfârșit de linie LF).
  Sarcina 2: semnătura RSA, n >= 3072 biți, hash i = (25 mod 24) + 1 = 2 -> MD5 (lista 1)
  Sarcina 3: semnătura ElGamal, p și g din enunț, hash i = 2 -> MD4 (lista 2)

Calculele principale se fac în Wolfram (wolfram/lab6.wls). Acest script:
  * fără argumente - realizează ambele semnături în Python;
  * --verify results.json - verifică independent valorile obținute în Wolfram.
"""
import hashlib
import json
import secrets
import sys
from math import gcd
from pathlib import Path

from Crypto.Hash import MD4          # MD4 is not available in hashlib with OpenSSL 3

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lab5"))
from pkc import P, G, is_probable_prime, random_prime  # noqa: E402  (same p, g as in Lab 5)

HERE = Path(__file__).parent
MESSAGE = (HERE / "message.txt").read_bytes()


def md5_int(data: bytes) -> tuple[str, int]:
    hx = hashlib.md5(data).hexdigest().upper()
    return hx, int(hx, 16)


def md4_int(data: bytes) -> tuple[str, int]:
    hx = MD4.new(data).hexdigest().upper()
    return hx, int(hx, 16)


# ------------------------------------------------------------ RSA signature
def rsa_keys(bits: int = 3072, e: int = 65537) -> dict:
    while True:
        p, q = random_prime(bits // 2), random_prime(bits // 2)
        n, phi = p * q, (p - 1) * (q - 1)
        if p != q and n.bit_length() >= bits and gcd(e, phi) == 1:
            return dict(p=p, q=q, n=n, phi=phi, e=e, d=pow(e, -1, phi))


def rsa_sign(h: int, k: dict) -> int:
    return pow(h, k["d"], k["n"])                   # s = h^d mod n


def rsa_verify(h: int, s: int, n: int, e: int) -> bool:
    return pow(s, e, n) == h                        # s^e mod n == h ?


# -------------------------------------------------------- ElGamal signature
def elgamal_keys() -> dict:
    x = secrets.randbelow(P - 3) + 2                # private key 1 < x < p-1
    return dict(x=x, y=pow(G, x, P))                # public key y = g^x mod p


def elgamal_sign(h: int, x: int) -> dict:
    while True:
        k = secrets.randbelow(P - 3) + 2            # ephemeral key, gcd(k, p-1) = 1
        if gcd(k, P - 1) == 1:
            break
    r = pow(G, k, P)                                # r = g^k mod p
    s = (h - x * r) * pow(k, -1, P - 1) % (P - 1)   # s = (h - x·r)·k^(-1) mod (p-1)
    return dict(k=k, r=r, s=s)


def elgamal_verify(h: int, r: int, s: int, y: int) -> bool:
    if not (0 < r < P and 0 < s < P - 1):
        return False
    return pow(G, h, P) == pow(y, r, P) * pow(r, s, P) % P   # g^h ≡ y^r · r^s (mod p)


# -------------------------------------------------------------- verification
def verify(path: str) -> bool:
    r = json.loads(Path(path).read_text())
    ok = lambda c, w: print(f"  [{'OK' if c else 'FAIL'}] {w}") or c
    res = True
    hx5, h5 = md5_int(MESSAGE)
    hx4, h4 = md4_int(MESSAGE)
    if "rsa" in r:
        x = {k: int(v) for k, v in r["rsa"].items() if k != "hashHex"}
        print("Semnătura RSA (MD5):")
        res &= ok(r["rsa"]["hashHex"].upper() == hx5 and x["h"] == h5, f"MD5(m) = {hx5}")
        res &= ok(is_probable_prime(x["p"]) and is_probable_prime(x["q"]), "p, q prime")
        res &= ok(x["n"] == x["p"] * x["q"] and x["n"].bit_length() >= 3072, f"n = p·q, {x['n'].bit_length()} biți")
        phi = (x["p"] - 1) * (x["q"] - 1)
        res &= ok(x["e"] * x["d"] % phi == 1, "e·d ≡ 1 (mod φ(n))")
        res &= ok(pow(h5, x["d"], x["n"]) == x["s"], "s = h^d mod n")
        res &= ok(rsa_verify(h5, x["s"], x["n"], x["e"]), "s^e mod n = h  -> semnătură validă")
    if "elgamal" in r:
        x = {k: int(v) for k, v in r["elgamal"].items() if k != "hashHex"}
        print("Semnătura ElGamal (MD4):")
        res &= ok(r["elgamal"]["hashHex"].upper() == hx4 and x["h"] == h4, f"MD4(m) = {hx4}")
        res &= ok(x["y"] == pow(G, x["x"], P), "y = g^x mod p")
        res &= ok(gcd(x["k"], P - 1) == 1 and x["r"] == pow(G, x["k"], P), "gcd(k, p-1) = 1, r = g^k mod p")
        res &= ok(x["s"] == (h4 - x["x"] * x["r"]) * pow(x["k"], -1, P - 1) % (P - 1), "s = (h - x·r)·k^(-1) mod (p-1)")
        res &= ok(elgamal_verify(h4, x["r"], x["s"], x["y"]), "g^h ≡ y^r · r^s (mod p) -> semnătură validă")
    print("TOATE VERIFICĂRILE AU TRECUT" if res else "EXISTĂ ERORI")
    return res


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) == 3 and sys.argv[1] == "--verify":
        sys.exit(0 if verify(sys.argv[2]) else 1)
    print(f"Mesajul m: {len(MESSAGE)} octeți, începe cu: {MESSAGE[:60].decode()}...")
    hx, h = md5_int(MESSAGE)
    keys = rsa_keys()
    s = rsa_sign(h, keys)
    print(f"\nRSA: n are {keys['n'].bit_length()} biți\n  MD5(m) = {hx} = {h}")
    print(f"  s = {str(s)[:80]}...\n  verificare: {rsa_verify(h, s, keys['n'], keys['e'])}")
    tampered = MESSAGE.replace(b"Egypt", b"Egipt", 1)
    print(f"  mesaj modificat -> verificare: {rsa_verify(md5_int(tampered)[1], s, keys['n'], keys['e'])}")
    hx, h = md4_int(MESSAGE)
    ek = elgamal_keys()
    sig = elgamal_sign(h, ek["x"])
    print(f"\nElGamal:\n  MD4(m) = {hx} = {h}")
    print(f"  r = {str(sig['r'])[:80]}...\n  s = {str(sig['s'])[:80]}...")
    print(f"  verificare: {elgamal_verify(h, sig['r'], sig['s'], ek['y'])}")
    print(f"  mesaj modificat -> verificare: {elgamal_verify(md4_int(tampered)[1], sig['r'], sig['s'], ek['y'])}")


if __name__ == "__main__":
    main()
