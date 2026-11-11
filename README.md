# Cryptography labs — Zastinceanu Mihai, FAF-243

| Lab | Topic | Folder | Run |
|---|---|---|---|
| 1 | Caesar cipher and Caesar with a keyword permutation (Romanian alphabet, n = 31) | `lab1` | `python lab1/caesar.py` |
| 2 | Cryptanalysis of monoalphabetic ciphers — frequency attack, variant V2 | `lab2` | `python lab2/frequency_attack.py` |
| 3 | Polyalphabetic ciphers — Playfair for Romanian (task 3.1) | `lab3` | `python lab3/playfair.py` |
| 4 | DES — round key Ki from K+ (task 2.3) | `lab4` | `python lab4/des_round_key.py` |
| 5 | Public-key cryptography: RSA, ElGamal, Diffie-Hellman + AES-256 (Wolfram) | `lab5` | `wolframscript -file tools/wl_session.wls lab5/wolfram/lab5.wl lab5/wolfram/transcript.txt` |
| 5 v2 | PKI with OpenSSL: CA, issue/revoke certificates, sign/verify files | `lab5-pki` | `./lab5-pki/pki.sh init` |
| 6 | Hash functions and digital signatures: RSA/MD5, ElGamal/MD4 (Wolfram) | `lab6` | `wolframscript -file tools/wl_session.wls lab6/wolfram/lab6.wl lab6/wolfram/transcript.txt` |

Each folder contains the sources, `report.md` and the report as `.docx`.
Requirements: Python 3.11+, `pycryptodome`, `matplotlib`, `pillow`, `python-docx`; OpenSSL 3 (Git Bash); Wolfram Engine for labs 5–6.
