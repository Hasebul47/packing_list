#!/bin/bash
set -e

SSL_ARGS=()

# Check for certificates in /certs
if [ -f "/certs/fullchain.crt" ] && [ -f "/certs/hameemgroup_com_Key.key" ]; then
    echo "=== Loading SSL Certificates for erpaiautomate.hameemgroup.com ==="
    SSL_ARGS+=(
        --server.sslCertFile=/certs/fullchain.crt
        --server.sslKeyFile=/certs/hameemgroup_com_Key.key
    )
elif [ -d "/certs" ]; then
    CERT=$(find /certs -maxdepth 1 \( -name "*fullchain*.crt" -o -name "*STAR*.crt" -o -name "*.crt" -o -name "*cert*.pem" \) ! -name "*ca*" ! -name "*bundle*" 2>/dev/null | head -n 1)
    KEY=$(find /certs -maxdepth 1 \( -name "*.key" -o -name "*privkey*.pem" \) 2>/dev/null | head -n 1)
    if [ -n "$CERT" ] && [ -n "$KEY" ]; then
        echo "=== Found SSL Cert: $CERT and Key: $KEY ==="
        SSL_ARGS+=(
            --server.sslCertFile="$CERT"
            --server.sslKeyFile="$KEY"
        )
    fi
fi

exec streamlit run app.py \
    --server.port=8002 \
    --server.address=0.0.0.0 \
    --server.baseUrlPath=packing-list \
    --server.headless=true \
    --server.enableCORS=false \
    --server.enableXsrfProtection=false \
    --browser.gatherUsageStats=false \
    "${SSL_ARGS[@]}" \
    "$@"
