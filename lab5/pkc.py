"""Lucrarea de laborator nr. 5 - Criptografia cu chei publice.
Autor: Zastinceanu Mihai

Implementare Python de referință pentru RSA (Sarcina 2.1), ElGamal (2.2) și
Diffie-Hellman + AES-256 (3). Calculele principale se fac în Wolfram (vezi
lab5/wolfram/*.wls); acest script:
  * fără argumente - rulează toți pașii cu numere generate în Python;
  * cu --verify results.json - verifică independent valorile obținute în Wolfram.
"""
import json
import secrets
import sys
from math import gcd
from pathlib import Path

HERE = Path(__file__).parent
MESSAGE = "Zastinceanu Mihai"          # m = Nume Prenume

# p (2048 de biți) și generatorul g din enunț (Sarcinile 2.2 și 3)
P = int(
    "32317006071311007300153513477825163362488057133489075174588434139269806834136210002792056362640164685"
    "45855635793533081692882902308057347262527355474246124574102620252791657297286270630032526342821314576"
    "69314142236542209411113486299916574782680342305530863490506355577122191878903327295696961297438562417"
    "41236237225197346402691855797767976823014625397933058015226858730761197532436467475855460715043896844"
    "94036613049769781285429595865959756705128385213278446852292550456827287911372009893187395914337417583"
    "78260002780349731985520606075332341226032546840881200311059074842810039949669561196969562486290323380"
    "72839127039")
G = 2


# ---------------------------------------------------------------- helpers
def is_probable_prime(n: int, rounds: int = 40) -> bool:
    if n < 2:
        return False
    for sp in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37):
        if n % sp == 0:
            return n == sp
    d, s = n - 1, 0
    while d % 2 == 0:
        d, s = d // 2, s + 1
    for _ in range(rounds):
        a = secrets.randbelow(n - 3) + 2
        x = pow(a, d, n)
        if x in (1, n - 1):
            continue
        for _ in range(s - 1):
            x = pow(x, 2, n)
            if x == n - 1:
                break
        else:
            return False
    return True


def random_prime(bits: int) -> int:
    while True:
        cand = secrets.randbits(bits) | (1 << (bits - 1)) | 1
        if is_probable_prime(cand):
            return cand


def text_to_int(text: str) -> tuple[str, int]:
    """ASCII -> hexadecimal -> decimal (as required in the note of the lab sheet)."""
    hx = text.encode("ascii").hex().upper()
    return hx, int(hx, 16)


def int_to_text(n: int) -> str:
    return bytes.fromhex(f"{n:X}" if len(f"{n:X}") % 2 == 0 else f"0{n:X}").decode("ascii")


# -------------------------------------------------------------------- RSA
def rsa(m: int, p: int | None = None, q: int | None = None, e: int = 65537) -> dict:
    while p is None or q is None:
        p, q = random_prime(1024), random_prime(1024)
        if (p * q).bit_length() < 2048 or p == q:
            p = q = None
    n = p * q
    phi = (p - 1) * (q - 1)
    assert gcd(e, phi) == 1
    d = pow(e, -1, phi)
    c = pow(m, e, n)
    m2 = pow(c, d, n)
    return dict(p=p, q=q, n=n, n_bits=n.bit_length(), phi=phi, e=e, d=d, c=c, m_decrypted=m2)


# ---------------------------------------------------------------- ElGamal
def elgamal(m: int, x: int | None = None, k: int | None = None) -> dict:
    assert m < P
    x = x or secrets.randbelow(P - 3) + 2          # private key, 1 < x < p-1
    y = pow(G, x, P)                                # public key
    while k is None or gcd(k, P - 1) != 1:
        k = secrets.randbelow(P - 3) + 2            # ephemeral key
    c1 = pow(G, k, P)
    c2 = m * pow(y, k, P) % P
    s = pow(c1, x, P)                               # shared secret g^(xk)
    m2 = c2 * pow(s, -1, P) % P
    return dict(x=x, y=y, k=k, c1=c1, c2=c2, s=s, m_decrypted=m2)


# --------------------------------------------------------- Diffie-Hellman
def diffie_hellman(a: int | None = None, b: int | None = None) -> dict:
    a = a or secrets.randbelow(P - 3) + 2           # Alisa's secret, 1 < a < p-1
    b = b or secrets.randbelow(P - 3) + 2           # Bob's secret
    A = pow(G, a, P)                                # sent by Alisa
    B = pow(G, b, P)                                # sent by Bob
    k_alisa = pow(B, a, P)
    k_bob = pow(A, b, P)
    aes_key = k_alisa % 2 ** 256                    # last 256 bits -> AES-256 key
    return dict(a=a, b=b, A=A, B=B, K_alisa=k_alisa, K_bob=k_bob,
                aes_key_hex=f"{aes_key:064X}", equal=k_alisa == k_bob)


def aes_demo(key_hex: str, text: str) -> dict:
    """Show the derived key really works as an AES-256 key (CBC, PKCS#7)."""
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import pad, unpad
    key = bytes.fromhex(key_hex)
    iv = secrets.token_bytes(16)
    ct = AES.new(key, AES.MODE_CBC, iv).encrypt(pad(text.encode(), 16))
    pt = unpad(AES.new(key, AES.MODE_CBC, iv).decrypt(ct), 16).decode()
    return dict(iv=iv.hex().upper(), ciphertext=ct.hex().upper(), decrypted=pt)


# ------------------------------------------------------------- verification
def verify(path: str):
    """Check, independently of Wolfram, every value saved by the .wls scripts."""
    r = json.loads(Path(path).read_text())
    ok = lambda cond, what: print(f"  [{'OK' if cond else 'FAIL'}] {what}") or cond
    hx, m = text_to_int(MESSAGE)
    res = True
    res &= ok(int(r["m"]) == m, "m = decimal(hex(ASCII('Zastinceanu Mihai')))")
    if "rsa" in r:
        x = {k: int(v) for k, v in r["rsa"].items()}
        print("RSA:")
        res &= ok(is_probable_prime(x["p"]) and is_probable_prime(x["q"]), "p și q sunt prime")
        res &= ok(x["n"] == x["p"] * x["q"] and x["n"].bit_length() >= 2048,
                  f"n = p·q, {x['n'].bit_length()} biți (>= 2048)")
        phi = (x["p"] - 1) * (x["q"] - 1)
        res &= ok(gcd(x["e"], phi) == 1 and x["e"] * x["d"] % phi == 1, "e·d ≡ 1 (mod φ(n))")
        res &= ok(pow(m, x["e"], x["n"]) == x["c"], "c = m^e mod n")
        res &= ok(pow(x["c"], x["d"], x["n"]) == m, "c^d mod n = m")
    if "elgamal" in r:
        x = {k: int(v) for k, v in r["elgamal"].items()}
        print("ElGamal:")
        res &= ok(x["y"] == pow(G, x["x"], P), "y = g^x mod p")
        res &= ok(x["c1"] == pow(G, x["k"], P) and x["c2"] == m * pow(x["y"], x["k"], P) % P,
                  "c1 = g^k mod p, c2 = m·y^k mod p")
        res &= ok(x["c2"] * pow(pow(x["c1"], x["x"], P), -1, P) % P == m, "c2·(c1^x)^(-1) mod p = m")
    if "dh" in r:
        x = r["dh"]
        a, b, A, B, K = (int(x[k]) for k in ("a", "b", "A", "B", "K"))
        print("Diffie-Hellman:")
        res &= ok(1 < a < P - 1 and 1 < b < P - 1, "1 < a, b < p-1")
        res &= ok(A == pow(G, a, P) and B == pow(G, b, P), "A = g^a mod p, B = g^b mod p")
        res &= ok(K == pow(B, a, P) == pow(A, b, P), "B^a mod p = A^b mod p = K")
        res &= ok(x["aesKeyHex"].upper() == f"{K % 2 ** 256:064X}", "cheia AES-256 = ultimii 256 de biți ai lui K")
    print("TOATE VERIFICĂRILE AU TRECUT" if res else "EXISTĂ ERORI")
    return res


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) == 3 and sys.argv[1] == "--verify":
        sys.exit(0 if verify(sys.argv[2]) else 1)
    hx, m = text_to_int(MESSAGE)
    print(f"m = '{MESSAGE}' -> hex {hx} -> zecimal {m}\n")
    r = rsa(m)
    print(f"RSA: n are {r['n_bits']} biți, e = {r['e']}")
    print(f"  c = {r['c']}\n  m' = {r['m_decrypted']} -> '{int_to_text(r['m_decrypted'])}'\n")
    eg = elgamal(m)
    print(f"ElGamal: c1 = {eg['c1']}\n  c2 = {eg['c2']}\n  m' -> '{int_to_text(eg['m_decrypted'])}'\n")
    dh = diffie_hellman()
    print(f"Diffie-Hellman: K_Alisa == K_Bob: {dh['equal']}, cheia AES-256 = {dh['aes_key_hex']}")
    print("AES-256 demo:", aes_demo(dh["aes_key_hex"], MESSAGE))


if __name__ == "__main__":
    main()
