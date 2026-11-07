# Landing page media

Everything here was produced on 7 November 2026 from commit `c40de2e` of this
repository (plugin version 3.0.0 on `main`), on macOS with Node.js 22.23.1 and
the locked `uv` environment. Nothing is a mockup.

- `qa-demo.mp4`: screen recording of `examples/qa-repair-retest`, made with
  Playwright in headless Chromium at 960×640 and encoded to H.264 with
  `ffmpeg -movflags +faststart`. It plays in real time with no speed-up or cuts.
  The example folder was copied twice into a scratch directory. For the first
  five seconds the page is served from the copy in which
  `if (!plan) return null;` was replaced as the example README instructs, and
  26 sites with one run each return the `portfolio` plan. After that the page is
  served from the unchanged copy: the same input returns `null`, then 3 sites,
  4 runs and annual billing are calculated, saved, read back after a reload and
  cleared.
- `qa-demo-poster.jpg`: a frame from that recording at 4.2 s.
- `qa-broken.jpg` and `qa-readback.jpg`: full-page screenshots of the same two
  copies at device scale factor 2, cropped to the result and to the saved-result
  panel. After the reload the form returns to its defaults (monthly billing),
  which is why the live result and the saved annual result differ.
- `transcripts.txt`: the command output quoted on the page (router answers,
  envelope validation, installer runs into a throwaway home directory, the
  example's Node tests and the test count). The throwaway home directory is
  shown as `~`, the clone path as `<clone>` and the scratch copies as
  `<scratch>`; nothing else is edited. No installer touched a real host
  directory.

The animated panel at the top of the page is a replay of the router and
validator output in `transcripts.txt`; the two envelopes it shows are the
conformance fixtures `finding-open.json` and `release-no-go-with-blockers.json`
from `fixtures/cwaip-v2/conformance/valid/`.
