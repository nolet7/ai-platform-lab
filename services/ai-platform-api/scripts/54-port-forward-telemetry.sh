#!/usr/bin/env bash
set -euo pipefail

LOKI_PID_FILE="/tmp/phase2p-loki.pid"
TEMPO_PID_FILE="/tmp/phase2p-tempo.pid"

if ! ss -ltn | grep -q ':13100 '
then

  kubectl port-forward \
    -n observability \
    svc/loki \
    13100:3100 \
    >/tmp/phase2p-loki.log 2>&1 &

  echo $! > "${LOKI_PID_FILE}"

fi


if ! ss -ltn | grep -q ':13200 '
then

  kubectl port-forward \
    -n observability \
    svc/tempo \
    13200:3200 \
    >/tmp/phase2p-tempo.log 2>&1 &

  echo $! > "${TEMPO_PID_FILE}"

fi


sleep 3

echo
echo "Loki:"

curl -fsS \
  http://127.0.0.1:13100/ready

echo
echo

echo "Tempo:"

curl -fsS \
  http://127.0.0.1:13200/ready

echo
echo

echo "Loki:  http://127.0.0.1:13100"
echo "Tempo: http://127.0.0.1:13200"
echo "Grafana: http://127.0.0.1:13000"
