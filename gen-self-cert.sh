#!/bin/bash
set -eu

title="nodeaffinity-webhook"
csrName=${title}.${title}
tmpdir=$(mktemp -d)
echo "creating certs in tmpdir ${tmpdir} "

openssl genrsa -out ${tmpdir}/ca.key 2048
openssl req -x509 -new -nodes -key ${tmpdir}/ca.key -days 100000 -out ${tmpdir}/ca.crt -subj "/CN=admission_ca"

cat <<EOF >> ${tmpdir}/server.conf
[req]
req_extensions = v3_req
distinguished_name = req_distinguished_name
[req_distinguished_name]
[ v3_req ]
basicConstraints = CA:FALSE
keyUsage = nonRepudiation, digitalSignature, keyEncipherment
extendedKeyUsage = clientAuth, serverAuth
[alt_names]
DNS.1 = ${title}
DNS.2 = ${title}.${title}
DNS.3 = ${title}.${title}.svc
EOF

openssl genrsa -out ${tmpdir}/server.key 2048
openssl req -new -key ${tmpdir}/server.key -out ${tmpdir}/server.csr -subj "/CN=${title}.${title}.svc" -config ${tmpdir}/server.conf

openssl x509 -req -in ${tmpdir}/server.csr -CA ${tmpdir}/ca.crt -CAkey ${tmpdir}/ca.key -CAcreateserial -out ${tmpdir}/server.crt -days 100000 -extensions v3_req -extfile ${tmpdir}/server.conf

# create the secret with CA cert and server cert/key
kubectl create secret generic ${title} \
        --from-file=key.pem=${tmpdir}/server.key \
        --from-file=cert.pem=${tmpdir}/server.crt \
        --from-file=ca.pem=${tmpdir}/ca.crt \
        --dry-run=client -o yaml |
    kubectl -n ${title} apply -f -


echo "update your CABundle with:"
kubectl get secret -n ${title} ${title} -o=jsonpath='{.data.ca\.pem}'  | tr -d '\n'
