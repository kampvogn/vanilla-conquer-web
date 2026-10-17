# Command & Conquer: Red Alert in the browser

This branch (`browser`) of [Vanilla Conquer](https://github.com/TheAssemblyArmada/Vanilla-Conquer)
builds Red Alert to WebAssembly with Emscripten, with network play in the browser. It runs at
<https://kampvogn.dk/games/redalert/>.

## Changes to Vanilla Conquer

The commits on this branch on top of upstream:

1. **Running in the browser:** the game keeps its own loops; `Web_Yield` (`common/mssleep.h`) gives
   the browser a turn from the input pump, the timer and the movie player (Asyncify). The page can
   turn sound off (`Module.noSound`) when the browser cannot play audio, because movies are timed by
   the audio clock; the theme player copes with missing music files; touch panning from the page
   (`Web_Scroll`); no quit in a browser tab.
2. **Network play:** `WebInterfaceClass` (`common/wspweb.*`) replaces the UDP transport. The page
   holds a WebSocket to a relay, which gives every player a random 4-byte address in a room (a
   virtual LAN); packets pass through `EM_JS` calls and queues. The game's own IPX/LAN lobby works
   unchanged on top of it.

## The page, the data and the relay

- `web/index.html` is the whole page: loading the data, sound and touch controls, player name and
  invite link (`#room=`), and the glue to the relay.
- **Game data** is EA's 2008 freeware release and is not in this repository. `web/data/` is a small
  server that serves the `.MIX` files the page needs: each file is described in `manifest.json` as
  byte ranges in the CD images on archive.org (plus our own small MIX header for `MAIN.MIX`). A
  missing file is streamed from archive.org while it is written to the data directory, and kept only
  if its SHA-1 matches. `web/tools/` made the manifest (`bin2iso.py` converts the raw Soviet disc
  image, `offsets.py` finds and verifies every file in the images).
- **The relay** is shared with Rise of the Triad and lives in
  [taradino-web](https://github.com/kampvogn/taradino-web/tree/browser/web/relay) (`web/relay/`),
  including its limits and an nginx example. The page connects to `/redalert/net` on its own host.

To fill a local data directory, for example for the tests:

```sh
docker build -t ra-data web/data
mkdir -p web/stage/data
docker run -d --rm --name ra-data -u "$(id -u):$(id -g)" -p 8080:8080 \
  -v "$PWD/web/stage/data:/data" -v "$PWD/web/data/manifest.json:/manifest.json:ro" ra-data
for f in REDALERT.MIX MAIN.MIX SCORES.MIX MOVIES1.MIX MOVIES2.MIX; do curl -so /dev/null http://localhost:8080/$f; done
docker stop ra-data
```

(`MOVIES*.MIX` are large and optional; the page works without them, minus the videos.)

## Building

```sh
docker build -t ra-emsdk -f web/Dockerfile.emsdk web   # Emscripten 4.0.10 + SDL2
web/build-wasm.sh                                       # → build-wasm/vanillara.{js,wasm}
web/stage.sh                                            # page + build → web/stage/
```

Serve `web/stage/` with any static web server (`.wasm` as `application/wasm`; it compresses well,
14 MB → 5 MB with gzip). Bump `vanillara.js?v=N` in `index.html` when a cached copy must be replaced.

## Tests

Playwright in Docker; screenshots go to `web/shots/`.

```sh
npm i --prefix web/test playwright-core@1.62.1
ACTIONS="click:0.5,0.5;wait:30000;shot:menu" web/test/run.sh
ACTIONS="..." web/test/mp.sh     # two players and a relay container on a private network
```

`ACTIONS` is split on `;`, so JavaScript in a `js:` step cannot contain one.

## Licences

Vanilla Conquer is GPL-3.0 with EA's additional terms (see `License.txt`), and so are these changes.
Red Alert's data is © Electronic Arts; it is not part of this repository.
