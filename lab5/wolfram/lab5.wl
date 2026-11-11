(* ===== Lab 5 - Sarcina 2.1: RSA. Mesajul m = Nume Prenume ===== *)
msg = "Zastinceanu Mihai"

(* codurile ASCII ale caracterelor *)
codes = ToCharacterCode[msg, "ASCII"]

(* reprezentarea hexazecimală a fiecărui caracter, concatenată *)
hex = StringJoin[IntegerString[codes, 16, 2]]

(* reprezentarea zecimală a mesajului *)
m = FromDigits[hex, 16]

(* două numere prime aleatoare de 1025 de biți -> n are peste 2048 de biți *)
p = RandomPrime[{2^1024, 2^1025}]; q = RandomPrime[{2^1024, 2^1025}]; {PrimeQ[p], PrimeQ[q], p != q}

n = p*q

BitLength[n]

phi = (p - 1)*(q - 1);
e = 65537; GCD[e, phi]

(* cheia privată d = e^-1 mod phi(n) *)
d = PowerMod[e, -1, phi]

Mod[e*d, phi]

(* criptarea: c = m^e mod n *)
c = PowerMod[m, e, n]

(* decriptarea: m = c^d mod n *)
mRSA = PowerMod[c, d, n]

{mRSA == m, FromCharacterCode[IntegerDigits[mRSA, 256]]}

(* ===== Sarcina 2.2: ElGamal cu p (2048 de biți) și g = 2 din enunț ===== *)
pE = 32317006071311007300153513477825163362488057133489075174588434139269806834136210002792056362640164685458556357935330816928829023080573472625273554742461245741026202527916572972862706300325263428213145766931414223654220941111348629991657478268034230553086349050635557712219187890332729569696129743856241741236237225197346402691855797767976823014625397933058015226858730761197532436467475855460715043896844940366130497697812854295958659597567051283852132784468522925504568272879113720098931873959143374175837826000278034973198552060607533234122603254684088120031105907484281003994966956119696956248629032338072839127039; g = 2; {BitLength[pE], PrimeQ[pE], PrimeQ[(pE - 1)/2]}

(* cheia privată x (aleatoare, 1 < x < p-1) și cheia publică y = g^x mod p *)
x = RandomInteger[{2, pE - 2}]

y = PowerMod[g, x, pE]

(* cheia efemeră k, cu gcd(k, p-1) = 1 *)
k = RandomInteger[{2, pE - 2}]; While[GCD[k, pE - 1] != 1, k = RandomInteger[{2, pE - 2}]]; k

(* criptarea: c1 = g^k mod p, c2 = m * y^k mod p *)
c1 = PowerMod[g, k, pE]

c2 = Mod[m*PowerMod[y, k, pE], pE]

(* decriptarea: m = c2 * (c1^x)^-1 mod p = c2 * c1^(p-1-x) mod p *)
mEG = Mod[c2*PowerMod[c1, pE - 1 - x, pE], pE]

{mEG == m, FromCharacterCode[IntegerDigits[mEG, 256]]}

(* ===== Sarcina 3: schimbul de chei Diffie-Hellman între Alisa și Bob ===== *)
(* numerele secrete a (Alisa) și b (Bob): aleatoare, 1 < a, b < p-1 *)
a = RandomInteger[{2, pE - 2}]

b = RandomInteger[{2, pE - 2}]

(* Alisa trimite lui Bob A = g^a mod p *)
A = PowerMod[g, a, pE]

(* Bob trimite Alisei B = g^b mod p *)
B = PowerMod[g, b, pE]

(* Alisa calculează K = B^a mod p *)
KAlisa = PowerMod[B, a, pE]

(* Bob calculează K = A^b mod p *)
KBob = PowerMod[A, b, pE]

KAlisa == KBob

(* cheia AES de 256 de biți = ultimii 256 de biți ai secretului comun K *)
aesKey = Mod[KAlisa, 2^256]; {BitLength[aesKey] <= 256, IntegerString[aesKey, 16, 64]}

(* verificare: Alisa criptează cu AES-256, Bob decriptează cu aceeași cheie *)
keyAES = SymmetricKey[<|"Cipher" -> "AES256", "Key" -> ByteArray[IntegerDigits[aesKey, 256, 32]]|>]; enc = Encrypt[keyAES, msg]; {StringJoin[IntegerString[Normal[enc["Data"]], 16, 2]], StringJoin[IntegerString[Normal[enc["InitializationVector"]], 16, 2]], Decrypt[keyAES, enc]}

(* salvarea rezultatelor pentru verificarea independentă în Python *)
Export["results.json", <|"m" -> ToString[m], "rsa" -> <|"p" -> ToString[p], "q" -> ToString[q], "n" -> ToString[n], "e" -> ToString[e], "d" -> ToString[d], "c" -> ToString[c]|>, "elgamal" -> <|"x" -> ToString[x], "y" -> ToString[y], "k" -> ToString[k], "c1" -> ToString[c1], "c2" -> ToString[c2]|>, "dh" -> <|"a" -> ToString[a], "b" -> ToString[b], "A" -> ToString[A], "B" -> ToString[B], "K" -> ToString[KAlisa], "aesKeyHex" -> IntegerString[aesKey, 16, 64]|>|>, "RawJSON"]
