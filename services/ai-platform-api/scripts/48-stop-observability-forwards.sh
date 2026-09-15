#!/usr/bin/env bash

for ITEM in \
  "Prometheus:/tmp/phase2o-prometheus.pid" \
  "Grafana:/tmp/phase2o-grafana.pid"
do

    NAME="${ITEM%%:*}"
    PID_FILE="${ITEM#*:}"

    if [[ ! -f "${PID_FILE}" ]]
    then
        echo "${NAME}: no saved PID"
        continue
    fi

    PID=$(cat "${PID_FILE}")

    if kill -0 "${PID}" 2>/dev/null
    then
        kill "${PID}"
        echo "Stopped ${NAME} PID ${PID}"
    else
        echo "${NAME} PID ${PID} no longer running"
    fi

    rm -f "${PID_FILE}"

done
