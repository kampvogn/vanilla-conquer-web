#!/bin/sh
# Two players through a relay container on a private docker network. The relay lives in
# github.com/kampvogn/taradino-web (web/relay); RELAY_DIR uses a local copy instead.
# Env: ACTIONS, ROOM, STAGE, LOGLINES (relay log lines, 5), PW_NODE_MODULES, RELAY_DIR
T=$(cd "$(dirname "$0")" && pwd); WEB=$(dirname "$T")
mkdir -p "$WEB/shots"
docker build -q -t kampvogn-relay "${RELAY_DIR:-https://github.com/kampvogn/taradino-web.git#browser:web/relay}" >/dev/null
docker network create ra-test >/dev/null 2>&1
docker rm -f ra-relay-test >/dev/null 2>&1
docker run -d --rm --name ra-relay-test --network ra-test -e ORIGINS=http://localhost:8099 kampvogn-relay >/dev/null
docker run --rm --shm-size=2g --network ra-test -e ACTIONS -e URL="http://localhost:8099/?net=ws://ra-relay-test:8081/redalert/net${ROOM:+#room=$ROOM}" \
  -v "${PW_NODE_MODULES:-$T/node_modules}":/pw/node_modules -v "$T":/s -v "$WEB/shots":/out -v "${STAGE:-$WEB/stage}":/web \
  mcr.microsoft.com/playwright:v1.62.1-jammy sh -c "cd /web && (python3 -m http.server 8099 >/dev/null 2>&1 &) && sleep 1 && timeout 400 node /s/mp.cjs"
docker logs ra-relay-test 2>&1 | tail -${LOGLINES:-5}
docker stop ra-relay-test >/dev/null
