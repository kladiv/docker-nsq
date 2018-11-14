#!/bin/bash
set -eo pipefail
host="$(hostname --ip-address || echo '127.0.0.1')"
if nc -z "$host" "${NSQLOOKUP_PORT:=4161}"; then
	exit 0
fi
exit 1
