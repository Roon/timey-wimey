# Reliability Improvements Design

**Date:** 2026-03-11
**Project:** timey-wimey
**Scope:** Reliability and robustness improvements

## Problem Statement

Two reliability issues affect users:

1. **Missing libfaketime**: Users who haven't installed `libfaketime` see cryptic bash errors or nothing at all, with no guidance on how to fix the problem.
2. **Backwards-time delay**: When the slider moves to a value lower than the previous value, WSJT-X takes time to accept the new offset because `CLOCK_MONOTONIC` cannot go backwards. The current env flags include two non-standard variables (`FAKETIME_CLOCK=real`, `FAKETIME_MONOTONIC=1`) that are silently ignored.

## Design

### 1. Dependency Checking (in `timey_gui.py`)

On startup, before creating the main window, run two checks:

**libfaketime detection:**
- Run `ldconfig -p | grep libfaketime.so` to locate the `.so` file.
- If not found, fall back to scanning common paths (`/usr/lib`, `/usr/local/lib`).
- If still not found, show a `tkinter.messagebox.showerror` dialog with the message:
  > "libfaketime not found. Install it with:\n  sudo apt install libfaketime\nor build from source: https://github.com/wolfcw/libfaketime"
- Call `sys.exit(1)` after the dialog is dismissed.

**wsjtx detection:**
- Use `shutil.which("wsjtx")` to check if `wsjtx` is in `$PATH`.
- If not found, show a `tkinter.messagebox.showerror` dialog:
  > "wsjtx not found. Install it with:\n  sudo apt install wsjtx"
- Call `sys.exit(1)` after the dialog is dismissed.

The `libfaketime.so` path found during the check is written to `~/.faketimerc.sopath` so `launch-wsjtx.sh` can use it directly, avoiding the fragile `dpkg -L` lookup.

### 2. libfaketime Environment Flags (in `launch-wsjtx.sh`)

**Remove** the two non-standard env vars (`FAKETIME_CLOCK=real`, `FAKETIME_MONOTONIC=1`), which are not recognized by libfaketime and are silently ignored.

**Add** `FAKETIME_ALLOW_RESET=1`, which permits the fake monotonic clock to reset immediately when the offset changes backwards. This eliminates the wait caused by `CLOCK_MONOTONIC` refusing to go backwards.

**Add** `FAKETIME_TIMESTAMP_FILE="$HOME/.faketimerc"` explicitly, making the config path unambiguous rather than relying on the library default.

**Read** the `.so` path from `~/.faketimerc.sopath` (written by the GUI on startup) instead of running `dpkg -L libfaketime` at launch time.

Final env block:
```bash
FAKETIME_NO_CACHE=1 \
FAKETIME_ALLOW_RESET=1 \
FAKETIME_TIMESTAMP_FILE="$HOME/.faketimerc" \
LD_PRELOAD="$(cat "$HOME/.faketimerc.sopath")" \
wsjtx
```

### 3. Visual Feedback (in `timey_gui.py`)

Add a status label below the Reset button:

- Displays the current offset at all times, e.g. `Offset: +0.50s`.
- When offset is zero, displays `Offset: 0.00s (no adjustment)`.
- When the slider moves to a value **lower** than the previous value, the label briefly changes to `Applying...` for 1.5 seconds, then reverts to showing the offset. Implemented with Tkinter's `.after()` — no threads required.

## Files Changed

| File | Change |
|------|--------|
| `timey_gui.py` | Add dependency checks on startup; add status label |
| `launch-wsjtx.sh` | Fix env vars; read `.so` path from `~/.faketimerc.sopath` |

## Out of Scope

- Cross-platform support (macOS, Windows)
- Packaging or distribution changes
- Any changes to the slider range, resolution, or window dimensions
