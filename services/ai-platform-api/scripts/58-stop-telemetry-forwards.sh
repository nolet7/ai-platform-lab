#!/usr/bin/env bash

for ITEM in \
  "Loki:/tmp/phase2p-loki.pid" \
  "Tempo:/tmp/phase2p-tempo.pid"
do

  NAME="${ITEM%%:*}"
  FILE="${ITEM#*:}"

  if [[ ! -f "${FILE}" ]]
  then
    echo "${NAME}: no PID file"
    continue
  fi

  PID=$(cat "${FILE}")

  if kill -0 "${PID}" 2>/dev/null
  then

    kill "${PID}"

    echo "Stopped ${NAME} PID ${PID}"

  fi

  rm -f "${FILE}"

done
