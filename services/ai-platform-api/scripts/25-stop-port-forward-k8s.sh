#!/usr/bin/env bash

PID_FILE="/tmp/ai-platform-api-k8s-port-forward.pid"

if [[ ! -f "${PID_FILE}" ]]; then
    echo "No saved Phase 2M port-forward PID."
    exit 0
fi

PID=$(cat "${PID_FILE}")

if kill -0 "${PID}" 2>/dev/null; then

    kill "${PID}"

    echo "Stopped Phase 2M port-forward PID ${PID}"

else

    echo "PID ${PID} is no longer running."

fi

rm -f "${PID_FILE}"
