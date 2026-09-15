#!/usr/bin/env bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/00-env.sh"

if [[ ! -f "${KC_PF_PID_FILE}" ]]; then
    echo "No saved Keycloak port-forward PID."
    exit 0
fi

PID=$(cat "${KC_PF_PID_FILE}")

if kill -0 "${PID}" 2>/dev/null; then

    kill "${PID}"

    echo "Stopped Keycloak port-forward PID ${PID}"

else

    echo "Keycloak port-forward PID ${PID} is no longer running."

fi

rm -f "${KC_PF_PID_FILE}"
