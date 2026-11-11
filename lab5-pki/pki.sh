#!/usr/bin/env bash
# Laboratory work nr. 5 (version 2) - internal PKI with OpenSSL + digital signatures
# Author: Zastinceanu Mihai
#
#   ./pki.sh init                      create the root CA (RSA 4096, self-signed, 3650 days)
#   ./pki.sh issue  <user>             generate the user's RSA 2048 private key + certificate (365 days)
#   ./pki.sh revoke <user> [reason]    revoke the user's certificate and regenerate the CRL
#   ./pki.sh sign   <user> <file>      sign a file with the user's private key   -> <file>.<user>.sig
#   ./pki.sh verify <user> <file>      check the certificate (CA + CRL) and the signature
#   ./pki.sh list                      show the CA database (V = valid, R = revoked)
#   ./pki.sh show   <user>             print the user's certificate
set -euo pipefail
export MSYS_NO_PATHCONV=1            # Git Bash on Windows: do not rewrite "/CN=..." as a path

SCRIPT_DIR="$(cd "$(dirname "$0")" && (pwd -W 2>/dev/null || pwd))"   # pwd -W: D:/... form for native openssl on Windows
PKI_DIR="${PKI_DIR:-$SCRIPT_DIR/pki-data}"
CA_DIR="$PKI_DIR/ca"
USERS_DIR="$PKI_DIR/users"
CNF="$CA_DIR/openssl.cnf"
ORG="/C=MD/L=Chisinau/O=UTM FCIM Crypto Lab"

die() { echo "Error: $*" >&2; exit 1; }
step() { echo; echo "==> $*"; }

write_config() {
cat > "$CNF" <<EOF
[ ca ]
default_ca = lab_ca

[ lab_ca ]
dir               = $CA_DIR
database          = \$dir/index.txt
serial            = \$dir/serial
crlnumber         = \$dir/crlnumber
new_certs_dir     = \$dir/newcerts
certificate       = \$dir/ca.crt
private_key       = \$dir/private/ca.key
crl               = \$dir/crl.pem
default_md        = sha256
default_days      = 365
default_crl_days  = 30
policy            = policy_any
unique_subject    = no
copy_extensions   = none
x509_extensions   = user_cert

[ policy_any ]
countryName            = optional
localityName           = optional
organizationName       = optional
commonName             = supplied

[ req ]
distinguished_name = req_dn
prompt             = no
[ req_dn ]
CN = placeholder

[ ca_cert ]
subjectKeyIdentifier   = hash
authorityKeyIdentifier = keyid:always
basicConstraints       = critical, CA:true
keyUsage               = critical, keyCertSign, cRLSign

[ user_cert ]
subjectKeyIdentifier   = hash
authorityKeyIdentifier = keyid
basicConstraints       = critical, CA:false
keyUsage               = critical, digitalSignature, nonRepudiation
extendedKeyUsage       = codeSigning, emailProtection
EOF
}

cmd_init() {
    [[ -f "$CA_DIR/ca.crt" ]] && die "the CA already exists in $CA_DIR (delete pki-data to start over)"
    mkdir -p "$CA_DIR/private" "$CA_DIR/newcerts" "$USERS_DIR"
    chmod 700 "$CA_DIR/private" 2>/dev/null || true
    : > "$CA_DIR/index.txt"
    echo 1000 > "$CA_DIR/serial"
    echo 1000 > "$CA_DIR/crlnumber"
    write_config

    step "Generating the CA root private key (RSA, 4096 bits)"
    openssl genpkey -quiet -algorithm RSA -pkeyopt rsa_keygen_bits:4096 -out "$CA_DIR/private/ca.key"

    step "Creating the self-signed CA certificate (valid 3650 days = 10 years)"
    openssl req -config "$CNF" -new -x509 -sha256 -days 3650 \
        -key "$CA_DIR/private/ca.key" -extensions ca_cert \
        -subj "$ORG/CN=UTM Crypto Lab Root CA" -out "$CA_DIR/ca.crt"

    step "Generating the (empty) certificate revocation list"
    openssl ca -config "$CNF" -gencrl -out "$CA_DIR/crl.pem" 2>/dev/null

    openssl x509 -in "$CA_DIR/ca.crt" -noout -subject -issuer -dates -ext basicConstraints
    echo "Key size: $(openssl pkey -in "$CA_DIR/private/ca.key" -noout -text | head -1)"
    echo "CA ready: $CA_DIR/ca.crt"
}

need_ca() { [[ -f "$CA_DIR/ca.crt" ]] || die "no CA - run './pki.sh init' first"; }
check_user() { [[ "$1" =~ ^[A-Za-z0-9._-]+$ ]] || die "invalid user name '$1' (letters, digits, . _ -)"; }

cmd_issue() {
    need_ca; local user="${1:?usage: issue <user>}"; check_user "$user"
    local d="$USERS_DIR/$user"
    if [[ -f "$d/$user.crt" ]] && grep -q "^V.*/CN=$user\$" "$CA_DIR/index.txt"; then
        die "user '$user' already has a valid certificate (revoke it first)"
    fi
    mkdir -p "$d"
    step "Generating the private key of '$user' (RSA, 2048 bits)"
    openssl genpkey -quiet -algorithm RSA -pkeyopt rsa_keygen_bits:2048 -out "$d/$user.key"
    step "Creating the certificate signing request (CSR)"
    openssl req -new -sha256 -key "$d/$user.key" -subj "$ORG/CN=$user" -out "$d/$user.csr"
    step "The CA signs the request -> certificate valid 365 days"
    openssl ca -config "$CNF" -batch -days 365 -in "$d/$user.csr" -out "$d/$user.crt" 2>&1 \
        | grep -E "Signature ok|Certificate is to be certified|Data Base Updated" || true
    openssl x509 -in "$d/$user.crt" -noout -subject -issuer -serial -dates
    echo "Key size: $(openssl pkey -in "$d/$user.key" -noout -text | head -1)"
    openssl verify -CAfile "$CA_DIR/ca.crt" "$d/$user.crt"
}

cmd_revoke() {
    need_ca; local user="${1:?usage: revoke <user> [reason]}"; local reason="${2:-keyCompromise}"
    check_user "$user"
    local crt="$USERS_DIR/$user/$user.crt"
    [[ -f "$crt" ]] || die "user '$user' has no certificate"
    step "Revoking the certificate of '$user' (reason: $reason)"
    openssl ca -config "$CNF" -revoke "$crt" -crl_reason "$reason" 2>&1 | grep -E "Revoking|Data Base|already revoked" || true
    step "Publishing the new CRL"
    openssl ca -config "$CNF" -gencrl -out "$CA_DIR/crl.pem" 2>/dev/null
    openssl crl -in "$CA_DIR/crl.pem" -noout -text | grep -E "Last Update|Next Update|Serial Number|Reason|        [A-Za-z]+ Compromise|Key Compromise" || true
}

check_certificate() {   # validate the signer's certificate against the CA and the CRL
    local crt="$1"
    openssl verify -crl_check -CAfile "$CA_DIR/ca.crt" -CRLfile "$CA_DIR/crl.pem" "$crt"
}

cmd_sign() {
    need_ca; local user="${1:?usage: sign <user> <file>}" file="${2:?usage: sign <user> <file>}"
    check_user "$user"
    local d="$USERS_DIR/$user"
    [[ -f "$d/$user.key" ]] || die "user '$user' has no private key"
    [[ -f "$file" ]] || die "file '$file' not found"
    step "Checking that the certificate of '$user' is still valid"
    check_certificate "$d/$user.crt" || die "the certificate of '$user' is not valid (revoked or expired) - signing refused"
    step "Signing '$file' (SHA-256 hash, RSA private key of '$user')"
    openssl dgst -sha256 -sign "$d/$user.key" -out "$file.$user.sig" "$file"
    echo "SHA-256($file) = $(openssl dgst -sha256 -r "$file" | cut -d' ' -f1)"
    echo "Signature: $file.$user.sig ($(wc -c < "$file.$user.sig") bytes)"
}

cmd_verify() {
    need_ca; local user="${1:?usage: verify <user> <file>}" file="${2:?usage: verify <user> <file>}"
    check_user "$user"
    local crt="$USERS_DIR/$user/$user.crt" sig="$file.$user.sig"
    [[ -f "$sig" ]] || die "signature '$sig' not found"
    step "1) Is the signer's certificate issued by our CA and not revoked?"
    if ! check_certificate "$crt"; then
        echo "RESULT: signature NOT trusted - the certificate of '$user' is revoked or invalid"; return 1
    fi
    step "2) Does the signature match the file? (public key taken from the certificate)"
    openssl x509 -in "$crt" -noout -pubkey > "$PKI_DIR/.pub.pem"
    if openssl dgst -sha256 -verify "$PKI_DIR/.pub.pem" -signature "$sig" "$file"; then
        echo "RESULT: signature VALID - '$file' was signed by '$user' and was not modified"
    else
        echo "RESULT: signature INVALID - the file was modified or signed by someone else"; return 1
    fi
}

cmd_list() {
    need_ca
    printf "%-6s %-14s %-8s %s\n" "Status" "Expires" "Serial" "Subject"
    awk -F'\t' '{printf "%-6s %-14s %-8s %s\n", $1, $2, $4, $6}' "$CA_DIR/index.txt"
}

case "${1:-}" in
    init)   cmd_init ;;
    issue)  shift; cmd_issue "$@" ;;
    revoke) shift; cmd_revoke "$@" ;;
    sign)   shift; cmd_sign "$@" ;;
    verify) shift; cmd_verify "$@" ;;
    list)   cmd_list ;;
    show)   shift; check_user "${1:?}"; openssl x509 -in "$USERS_DIR/$1/$1.crt" -noout -text | head -40 ;;
    *) sed -n '2,12p' "$0"; exit 1 ;;
esac
