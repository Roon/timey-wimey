# Reliability Improvements Design

**Date:** 2026-03-11
**Project:** timey-wimey
**Scope:** Reliability and robustness improvements

## Problem Statement

Two reliability issues affect users:

1. **Missing libfaketime**: Users who haven't installed `libfaketime` see cryptic bash errors or nothing at all, with no guidance on how to fix the problem.
2. **Backwards-time delay**: When the slider moves to a value lower than the previous value, WSJT-X takes time to accept the new offset because `CLOCK_MONOTONIC` cannot go backwards. The current env block also includes two non-standard variables (`FAKETIME_CLOCK=real`, `FAKETIME_MONOTONIC=1`) that libfaketime does not recognize and silently ignores.

## Design

### 1. Dependency Checking (in `timey_gui.py`)

On startup, before showing the main window, check for libfaketime. A hidden root window must be created first so `tkinter.messagebox` has a parent: `root = tk.Tk(); root.withdraw()`. If the check passes, the root window is shown normally; if it fails, the error dialog is shown and `sys.exit(1)` is called.

**libfaketime detection:**
- Run `ldconfig -p | grep libfaketime.so` to locate the `.so` file.
- Parse each matching line using `maxsplit=1` to handle paths that might contain ` => `: `parts = line.split(" => ", 1); path = parts[1].strip() if len(parts) == 2 else None`. Verify the path exists with `os.path.isfile(path)` before returning it. Return the first valid result.
- If not found via `ldconfig`, fall back to scanning these paths with `glob.glob`: `/usr/lib/libfaketime.so*`, `/usr/local/lib/libfaketime.so*`, `/usr/lib/x86_64-linux-gnu/libfaketime.so*`, `/usr/lib/aarch64-linux-gnu/libfaketime.so*`. Return the first match where `os.path.isfile` is true.
- If still not found, show a `tkinter.messagebox.showerror` dialog:
  > "libfaketime not found. Install it with:\n  sudo apt install libfaketime\nor build from source:\n  https://github.com/wolfcw/libfaketime"
- Call `sys.exit(1)` after the dialog is dismissed.

The detection function calls `sys.exit(1)` (after showing the dialog) if libfaketime is not found, and returns normally if it is. `LD_PRELOAD` is set by the shell script, not Python.

**wsjtx is not checked here.** The GUI's sole responsibility is adjusting the time offset; wsjtx check belongs in `launch-wsjtx.sh`.

**Note on startup state:** The current GUI does not read `~/.faketimerc` on startup — the slider always initialises at `0`. This spec does not change that behaviour.

### 2. libfaketime Environment Flags (in `launch-wsjtx.sh`)

**Fix the `set` line:** Change `set -eu pipefail` to `set -euo pipefail`. `set` treats each word after the option string as a positional parameter, so `set -eu pipefail` sets `-e` and `-u` but assigns `pipefail` to `$1` — `pipefail` mode is never enabled. The fix is to include it in the option string as `-euo pipefail`.

**libfaketime detection in the shell script:**
The script independently detects the libfaketime `.so` path using the same fallback list as the GUI, implemented in bash:
```bash
LIBFAKETIME_PATH=$(ldconfig -p | grep 'libfaketime\.so' | awk -F' => ' '{print $2}' | head -1)
# Verify the ldconfig result actually exists
[ -n "$LIBFAKETIME_PATH" ] && [ ! -e "$LIBFAKETIME_PATH" ] && LIBFAKETIME_PATH=""
if [ -z "$LIBFAKETIME_PATH" ]; then
    for dir in /usr/lib /usr/local/lib /usr/lib/x86_64-linux-gnu /usr/lib/aarch64-linux-gnu; do
        for f in "$dir"/libfaketime.so*; do
            [ -e "$f" ] && LIBFAKETIME_PATH="$f" && break 2
        done
    done
fi
if [ -z "$LIBFAKETIME_PATH" ]; then
    echo "libfaketime not found. Install it with: sudo apt install libfaketime"
    echo "Or build from source: https://github.com/wolfcw/libfaketime"
    exit 1
fi
```
*Note: Detection logic exists in both Python and bash. A shared helper was considered but rejected to avoid adding a new file. If the fallback path list changes, update both files.*

**wsjtx check:**
```bash
if ! command -v wsjtx >/dev/null 2>&1; then
    echo "wsjtx not found. Download and install it from: https://wsjt.physics.wisc.edu"
    exit 1
fi
```

**Remove** the two non-standard env vars (`FAKETIME_CLOCK=real`, `FAKETIME_MONOTONIC=1`).

**Add** `DONT_FAKE_MONOTONIC=1` (note: no `FAKETIME_` prefix — this is the correct libfaketime variable name), which tells libfaketime not to fake `CLOCK_MONOTONIC`. FT8 timing windows are wall-clock based (`CLOCK_REALTIME`), so faking only `CLOCK_REALTIME` should be sufficient. This avoids the backwards-time delay for `CLOCK_MONOTONIC`-based timers. *Assumption: WSJT-X does not rely on `CLOCK_MONOTONIC` for any timing that needs to match the faked offset. If it does, a split-brain clock (REALTIME shifted, MONOTONIC unshifted) could cause issues — but this is expected to be safe for FT8 use.*

**Keep** `FAKETIME_NO_CACHE=1` (already present): tells libfaketime to re-read `~/.faketimerc` on every clock call so WSJT-X always sees the current slider position.

**Add** `FAKETIME_TIMESTAMP_FILE="$HOME/.faketimerc"` explicitly. libfaketime's compiled-in default for per-user config may vary by build (system default is `/etc/faketimerc`); setting this variable ensures the correct path is used regardless of build configuration. The file format written by `timey_gui.py` is a relative offset string (e.g. `+0.50s`).

Final env block:
```bash
FAKETIME_NO_CACHE=1 \
DONT_FAKE_MONOTONIC=1 \
FAKETIME_TIMESTAMP_FILE="$HOME/.faketimerc" \
LD_PRELOAD="$LIBFAKETIME_PATH" \
wsjtx
```

### 3. Visual Feedback (in `timey_gui.py`)

Add a status label below the Reset button showing the current offset at all times:

- Positive non-zero: `Offset: +0.50s`
- Negative: `Offset: -1.00s`
- Zero: `Offset: 0.00s (no adjustment)`

The label updates on every slider change. No flash or transient state.

## Files Changed

| File | Change |
|------|--------|
| `timey_gui.py` | Add libfaketime check on startup (with hidden root window); add status label |
| `launch-wsjtx.sh` | Fix `set -euo pipefail`; portable libfaketime detection with existence check; fix env vars; add wsjtx check |

## Out of Scope

- Cross-platform support (macOS, Windows)
- Packaging or distribution changes
- Any changes to the slider range, resolution, or window dimensions
