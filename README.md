# Algonquin Titans Soccer

A deployable browser version of Hinata and Evan's Python/Pygame soccer game.

The game is still written in Python with Pygame. `pygbag` compiles it into a static
browser build, and Vercel serves that static output.

## Play Locally

```powershell
python -m pip install -r requirements.txt
npm install
npm run build
npm run serve
```

Open the local URL printed by `serve`.

## Controls

Blue team:

- `Q`, `W`, `E`: select blue players
- `X`: steal when close to the ball
- `F`, `S`, `D`: pass to B1, B2, B3
- `A`, `Z`: move blue keeper

Red team:

- `I`, `O`, `P`: select red players
- `L`: steal when close to the ball
- `M`, `J`, `K`: pass to R1, R2, R3
- `H`, `N`: move red keeper

Ball and match:

- Click the field after selecting a player to move them
- `V`, then click: shoot
- `R`: restart

## Deploying to Vercel

This repo is ready for Vercel. The Vercel build command installs the Python
requirements, builds the Pygame web bundle, and serves `dist`.

```powershell
vercel
```

For production:

```powershell
vercel --prod
```

## Multiplayer Plan

The first Vercel version is a reliable single-device two-player game. For online
multiplayer, Vercel should host the app while a realtime provider handles room
sync. Vercel Functions do not act as WebSocket servers, so use Pusher, Ably,
Supabase Realtime, Liveblocks, or PartyKit for the realtime layer.

The game is already shaped for that future work: the central `GameState` object
contains scores, players, targets, keepers, ball position, possession, and match
timer. An online version can serialize that state, send player inputs to a room,
and reconcile the latest shared state in the browser.
