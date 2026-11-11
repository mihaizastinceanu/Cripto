(* ===== Lab 6 - mesajul m = textul decriptat în Lab 2 (UTF-8) ===== *)
msg = ReadByteArray["../message.txt"]; Length[msg]

StringTake[ByteArrayToString[msg, "UTF-8"], 120]

(* ===== Sarcina 2: semnătura RSA, n >= 3072 biți, hash: i = (25 mod 24) + 1 = 2 -> MD5 ===== *)
h = Hash[msg, "MD5"]; {IntegerString[h, 16, 32], h}

(* două numere prime aleatoare de 1537 de biți -> n are peste 3072 de biți *)
p = RandomPrime[{2^1536, 2^1537}]; q = RandomPrime[{2^1536, 2^1537}]; {PrimeQ[p], PrimeQ[q], p != q}

n = p*q

BitLength[n]

phi = (p - 1)*(q - 1); e = 65537; GCD[e, phi]

(* cheia privată d = e^-1 mod phi(n) *)
d = PowerMod[e, -1, phi]

(* semnarea: s = h^d mod n *)
s = PowerMod[h, d, n]

(* validarea: s^e mod n trebuie să fie egal cu MD5(m) *)
{PowerMod[s, e, n], PowerMod[s, e, n] == h}

(* un mesaj modificat (Egypt -> Egipt) nu mai trece validarea *)
msg2 = StringToByteArray[StringReplace[ByteArrayToString[msg, "UTF-8"], "Egypt" -> "Egipt", 1], "UTF-8"]; PowerMod[s, e, n] == Hash[msg2, "MD5"]

(* ===== Sarcina 3: semnătura ElGamal, p și g din enunț, hash: i = 2 -> MD4 ===== *)
pE = 32317006071311007300153513477825163362488057133489075174588434139269806834136210002792056362640164685458556357935330816928829023080573472625273554742461245741026202527916572972862706300325263428213145766931414223654220941111348629991657478268034230553086349050635557712219187890332729569696129743856241741236237225197346402691855797767976823014625397933058015226858730761197532436467475855460715043896844940366130497697812854295958659597567051283852132784468522925504568272879113720098931873959143374175837826000278034973198552060607533234122603254684088120031105907484281003994966956119696956248629032338072839127039; g = 2; {BitLength[pE], PrimeQ[pE]}

hE = Hash[msg, "MD4"]; {IntegerString[hE, 16, 32], hE}

(* cheia privată x și cheia publică y = g^x mod p *)
x = RandomInteger[{2, pE - 2}]

y = PowerMod[g, x, pE]

(* k aleator cu gcd(k, p-1) = 1 *)
k = RandomInteger[{2, pE - 2}]; While[GCD[k, pE - 1] != 1, k = RandomInteger[{2, pE - 2}]]; {k, GCD[k, pE - 1]}

(* semnarea: r = g^k mod p,  s = (h - x r) k^-1 mod (p-1) *)
r = PowerMod[g, k, pE]

sE = Mod[(hE - x*r)*PowerMod[k, -1, pE - 1], pE - 1]

(* validarea: g^h mod p == y^r * r^s mod p *)
v1 = PowerMod[g, hE, pE]

v2 = Mod[PowerMod[y, r, pE]*PowerMod[r, sE, pE], pE]

{0 < r < pE, v1 == v2}

(* mesajul modificat nu trece validarea *)
PowerMod[g, Hash[msg2, "MD4"], pE] == v2

(* salvarea rezultatelor pentru verificarea independentă în Python *)
Export["results.json", <|"rsa" -> <|"hashHex" -> IntegerString[h, 16, 32], "h" -> ToString[h], "p" -> ToString[p], "q" -> ToString[q], "n" -> ToString[n], "e" -> ToString[e], "d" -> ToString[d], "s" -> ToString[s]|>, "elgamal" -> <|"hashHex" -> IntegerString[hE, 16, 32], "h" -> ToString[hE], "x" -> ToString[x], "y" -> ToString[y], "k" -> ToString[k], "r" -> ToString[r], "s" -> ToString[sE]|>|>, "RawJSON"]
