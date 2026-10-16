#!/bin/sh
# Build Vanilla Conquer (Red Alert) to WebAssembly in the ra-emsdk image.
# First: docker build -t ra-emsdk -f web/Dockerfile.emsdk web
# Env: BUILD_TYPE (Release), NETWORKING (ON: the WebSocket transport), BUILD_DIR (build-wasm), IMAGE (ra-emsdk)
set -e
WEB=$(cd "$(dirname "$0")" && pwd)
SRC=$(dirname "$WEB")
I=/emsdk/upstream/emscripten/cache/sysroot/include
docker run --rm -u "$(id -u):$(id -g)" -e HOME=/tmp -v "$SRC":/src -w /src ${IMAGE:-ra-emsdk} sh -c "
mkdir -p wasm-stub && emar rcs wasm-stub/libnone.a
emcmake cmake -G Ninja -B ${BUILD_DIR:-build-wasm} -DCMAKE_BUILD_TYPE=${BUILD_TYPE:-Release} -DBUILD_VANILLATD=OFF -DNETWORKING=${NETWORKING:-ON} \
 -DSDL2_INCLUDE_DIR=$I/SDL2 -DSDL2_LIBRARY=-sUSE_SDL=2 \
 -DOPENAL_INCLUDE_DIR=$I/AL -DOPENAL_LIBRARY=/src/wasm-stub/libnone.a \
 -DCMAKE_C_FLAGS=-sUSE_SDL=2 -DCMAKE_CXX_FLAGS=-sUSE_SDL=2 \
 '-DCMAKE_EXE_LINKER_FLAGS=-lopenal -lidbfs.js -sUSE_SDL=2 -sASYNCIFY -sASYNCIFY_STACK_SIZE=262144 -sSTACK_SIZE=4MB -sALLOW_MEMORY_GROWTH -sINITIAL_MEMORY=128MB -sFORCE_FILESYSTEM -sINVOKE_RUN=0 -sEXIT_RUNTIME=0 -sENVIRONMENT=web -sEXPORTED_RUNTIME_METHODS=FS,callMain' . >/dev/null
cmake --build ${BUILD_DIR:-build-wasm}"
