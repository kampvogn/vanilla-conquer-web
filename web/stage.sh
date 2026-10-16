#!/bin/sh
# Put the page and the build together in web/stage. The game data (data/*.MIX, EA's 2008 freeware
# release) is not in this repository: fetch it with web/data (see README) into web/stage/data.
set -e
WEB=$(cd "$(dirname "$0")" && pwd)
SRC=$(dirname "$WEB")
ST=${STAGE:-$WEB/stage}
mkdir -p "$ST/data"
cp "$WEB/index.html" "$ST/"
cp "$SRC/${BUILD_DIR:-build-wasm}/vanillara.js" "$SRC/${BUILD_DIR:-build-wasm}/vanillara.wasm" "$ST/"
echo "staged in $ST"
