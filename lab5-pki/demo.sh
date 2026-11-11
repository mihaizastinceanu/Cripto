#!/usr/bin/env bash
# Demonstration scenario for the report: every command is echoed with a "$ " prompt.
cd "$(dirname "$0")"
run() { echo "\$ $*"; "$@"; echo; }
part="${1:-all}"
if [[ $part == 1 || $part == all ]]; then
  rm -rf pki-data contract.txt contract.txt.*.sig
  run ./pki.sh init
fi
if [[ $part == 2 || $part == all ]]; then
  run ./pki.sh issue alice
  run ./pki.sh issue bob
  run ./pki.sh list
fi
if [[ $part == 3 || $part == all ]]; then
  echo "Contract nr. 25: Alice sells Bob 10 books for 500 MDL." > contract.txt
  run cat contract.txt
  run ./pki.sh sign alice contract.txt
  run ./pki.sh verify alice contract.txt
  run cp contract.txt.alice.sig contract.txt.bob.sig   # forgery: Alice's signature presented as Bob's
  run ./pki.sh verify bob contract.txt
  run sed -i "s/500 MDL/5 MDL/" contract.txt          # someone modifies the signed document
  run cat contract.txt
  run ./pki.sh verify alice contract.txt
fi
if [[ $part == 4 || $part == all ]]; then
  echo "Contract nr. 25: Alice sells Bob 10 books for 500 MDL." > contract.txt
  run ./pki.sh revoke alice keyCompromise
  run ./pki.sh verify alice contract.txt
  run ./pki.sh sign alice contract.txt
  run ./pki.sh list
  run ./pki.sh issue alice
  run ./pki.sh sign alice contract.txt
  run ./pki.sh verify alice contract.txt
fi
