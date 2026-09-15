#!/usr/bin/env bash
set -euo pipefail

PROM_PORT="19090"
GRAFANA_PORT="13000"

PROM_PID_FILE="/tmp/phase2o-prometheus.pid"
GRAFANA_PID_FILE="/tmp/phase2o-grafana.pid"

PROM_LOG="/tmp/phase2o-prometheus.log"
GRAFANA_LOG="/tmp/phase2o-grafana.log"

echo
echo "Port inventory:"
echo "8080   -> Argo CD"
echo "18080  -> Keycloak"
echo "13000  -> Grafana"
echo "19090  -> Prometheus"

for PORT in \
  "${PROM_PORT}" \
  "${GRAFANA_PORT}"
do
    if ss -ltn |
      grep -q ":${PORT} "
    then
        echo "Port ${PORT} already listening."
    fi
done

if ! ss -ltn |
  grep -q ":${PROM_PORT} "
then

    kubectl port-forward \
      -n observability \
      svc/kube-prometheus-stack-prometheus \
      "${PROM_PORT}:9090" \
      >"${PROM_LOG}" 2>&1 &

    echo $! > "${PROM_PID_FILE}"
fi

if ! ss -ltn |
  grep -q ":${GRAFANA_PORT} "
then

    kubectl port-forward \
      -n observability \
      svc/kube-prometheus-stack-grafana \
      "${GRAFANA_PORT}:80" \
      >"${GRAFANA_LOG}" 2>&1 &

    echo $! > "${GRAFANA_PID_FILE}"
fi

sleep 3

echo
echo "Prometheus:"
curl -fsS \
  http://127.0.0.1:19090/-/ready
echo

echo
echo "Grafana:"
curl -fsS \
  http://127.0.0.1:13000/api/health
echo

echo
echo "Prometheus:"
echo "http://127.0.0.1:19090"
echo
echo "Grafana:"
echo "http://127.0.0.1:13000"
