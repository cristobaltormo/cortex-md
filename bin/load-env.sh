#!/usr/bin/env bash
if [ -f "$BRAIN/.env" ]; then
  while IFS= read -r line || [ -n "$line" ]; do
    case "$line" in ''|'#'*) continue ;; esac
    key="${line%%=*}"
    value="${line#*=}"
    value="${value%\"}"; value="${value#\"}"
    value="${value%\'}"; value="${value#\'}"
    case "$key" in *[!A-Za-z0-9_]*|'') continue ;; esac
    export "$key=$value"
  done < "$BRAIN/.env"
fi
