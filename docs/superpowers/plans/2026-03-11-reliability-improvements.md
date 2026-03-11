# Reliability Improvements Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add friendly dependency error messages for missing libfaketime, fix the bash script's portability and env flags, and add a live offset status label to the GUI.

**Architecture:** Two files are modified. `launch-wsjtx.sh` gets a portable libfaketime `.so` detection block, a wsjtx presence check, and corrected libfaketime env vars. `timey_gui.py` gets a `if __name__ == "__main__":` guard (prerequisite for tests), a startup libfaketime check with a Tkinter error dialog on failure, and a persistent status label. A new `tests/test_timey_gui.py` covers the pure-Python logic.

**Tech Stack:** Python 3, tkinter, pytest, bash

---

## Chunk 1: Shell Script Fixes

### Task 1: Fix `set` flags and env vars in `launch-wsjtx.sh`

**Files:**
- Modify: `launch-wsjtx.sh`

Context: The current script has `set -eu pipefail` (broken — `pipefail` is a positional arg, not a flag). It also uses two non-existent libfaketime env vars and resolves the `.so` path via the Debian-only `dpkg -L` command.

- [ ] **Step 1: Open `launch-wsjtx.sh` and read it in full**

  Confirm the current content matches:
  ```bash
  set -eu pipefail
  ...
  LD_PRELOAD=$(dpkg -L libfaketime | grep libfaketime.so.1) \
  FAKETIME_NO_CACHE=1 \
  FAKETIME_CLOCK=real \
  FAKETIME_MONOTONIC=1 \
  ```

- [ ] **Step 2: Replace the full script with the corrected version**

  Write the following as the complete new contents of `launch-wsjtx.sh`:
  ```bash
  #!/bin/bash
  # launch-wsjtx.sh
  # Launch Timey-Wimey GUI and WSJT-X with libfaketime

  set -euo pipefail

  # Find libfaketime shared library
  LIBFAKETIME_PATH=$(ldconfig -p | grep 'libfaketime\.so' | awk -F' => ' '{print $2}' | head -1)
  # Verify the ldconfig result actually exists on disk
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

  # Check wsjtx is available
  if ! command -v wsjtx >/dev/null 2>&1; then
      echo "wsjtx not found. Download and install it from: https://wsjt.physics.wisc.edu"
      exit 1
  fi

  # Launch Timey-Wimey GUI in background
  python3 "$HOME/timey-wimey/timey_gui.py" &

  # Launch WSJT-X with libfaketime
  env \
      FAKETIME_NO_CACHE=1 \
      DONT_FAKE_MONOTONIC=1 \
      FAKETIME_TIMESTAMP_FILE="$HOME/.faketimerc" \
      LD_PRELOAD="$LIBFAKETIME_PATH" \
      wsjtx

  exit 0

  ### End of File ###
  ```

- [ ] **Step 3: Verify the script is syntactically valid**

  Run from the repo root: `bash -n launch-wsjtx.sh`
  Expected: no output, exit code 0

- [ ] **Step 4: Commit**

  ```bash
  git add launch-wsjtx.sh
  git commit -m "fix: portable libfaketime detection and correct env vars in launch script"
  ```

---

## Chunk 2: Python GUI — Libfaketime Detection

### Task 2: Set up pytest and test infrastructure

**Files:**
- Create: `conftest.py`
- Create: `tests/__init__.py`
- Create: `tests/test_timey_gui.py`

- [ ] **Step 1: Install pytest**

  Run: `pip install pytest`
  Expected: pytest installed successfully

- [ ] **Step 2: Create repo-root `conftest.py` so pytest can import `timey_gui`**

  Create `conftest.py` at the repo root with these contents:
  ```python
  import sys
  import os
  sys.path.insert(0, os.path.dirname(__file__))
  ```
  This ensures `import timey_gui` works from any working directory when pytest runs.

- [ ] **Step 3: Create the tests directory and placeholder test file**

  ```bash
  mkdir -p tests
  touch tests/__init__.py
  ```

  Write the following to `tests/test_timey_gui.py`:
  ```python
  # Tests for timey_gui.py
  ```

- [ ] **Step 4: Confirm pytest discovers the file without errors**

  Run: `pytest tests/ -v`
  Expected: `no tests ran` — zero errors, zero failures

---

### Task 3: Guard `main()` with `if __name__ == "__main__":`

**Files:**
- Modify: `timey_gui.py`

Currently `timey_gui.py` calls `main()` at module level. Importing the module in tests would call `main()`, create a real Tk window, and block on `mainloop()`. The guard prevents this.

- [ ] **Step 1: Replace the bare `main()` call at the bottom of `timey_gui.py`**

  Find this line at the end of `timey_gui.py`:
  ```python
  main()
  ```

  Replace it with:
  ```python
  if __name__ == "__main__":
      main()
  ```

- [ ] **Step 2: Verify the GUI still launches correctly**

  Run: `python3 timey_gui.py`
  Expected: the Timey-Wimey window appears normally

- [ ] **Step 3: Verify the module can now be imported without hanging**

  Run: `python3 -c "import timey_gui; print('OK')"`
  Expected: prints `OK` immediately with no Tk window

- [ ] **Step 4: Commit**

  ```bash
  git add timey_gui.py conftest.py tests/__init__.py tests/test_timey_gui.py
  git commit -m "chore: guard main() call and add test infrastructure"
  ```

---

### Task 4: Extract and test `find_libfaketime()`

**Files:**
- Modify: `timey_gui.py` (add `find_libfaketime` function)
- Modify: `tests/test_timey_gui.py`

The function returns the path to the libfaketime `.so` if found, or `None` if not. It does NOT show dialogs or call `sys.exit()` — the caller handles failure.

- [ ] **Step 1: Write the failing tests**

  Replace `tests/test_timey_gui.py` with:
  ```python
  import pytest
  from unittest.mock import patch, MagicMock
  import timey_gui


  class TestFindLibfaketime:
      def test_found_via_ldconfig(self):
          ldconfig_output = "libfaketime.so.1 (libc6,x86-64) => /usr/lib/x86_64-linux-gnu/libfaketime.so.1\n"
          with patch("timey_gui.subprocess.run") as mock_run, \
               patch("timey_gui.os.path.isfile", return_value=True):
              mock_run.return_value = MagicMock(stdout=ldconfig_output, returncode=0)
              result = timey_gui.find_libfaketime()
          assert result == "/usr/lib/x86_64-linux-gnu/libfaketime.so.1"

      def test_ldconfig_stale_path_falls_through_to_glob(self):
          """ldconfig returns a path that doesn't exist on disk — falls through to glob."""
          ldconfig_output = "libfaketime.so.1 (libc6,x86-64) => /stale/path/libfaketime.so.1\n"
          with patch("timey_gui.subprocess.run") as mock_run, \
               patch("timey_gui.os.path.isfile", side_effect=lambda p: p == "/usr/lib/libfaketime.so.1"), \
               patch("timey_gui.glob.glob", return_value=["/usr/lib/libfaketime.so.1"]):
              mock_run.return_value = MagicMock(stdout=ldconfig_output, returncode=0)
              result = timey_gui.find_libfaketime()
          assert result == "/usr/lib/libfaketime.so.1"

      def test_found_via_glob_fallback(self):
          """ldconfig finds nothing; glob finds the .so."""
          with patch("timey_gui.subprocess.run") as mock_run, \
               patch("timey_gui.glob.glob", return_value=["/usr/local/lib/libfaketime.so.1"]), \
               patch("timey_gui.os.path.isfile", return_value=True):
              mock_run.return_value = MagicMock(stdout="", returncode=0)
              result = timey_gui.find_libfaketime()
          assert result == "/usr/local/lib/libfaketime.so.1"

      def test_not_found_returns_none(self):
          with patch("timey_gui.subprocess.run") as mock_run, \
               patch("timey_gui.glob.glob", return_value=[]), \
               patch("timey_gui.os.path.isfile", return_value=False):
              mock_run.return_value = MagicMock(stdout="", returncode=0)
              result = timey_gui.find_libfaketime()
          assert result is None
  ```

- [ ] **Step 2: Run the tests — expect AttributeError (function doesn't exist yet)**

  Run: `pytest tests/test_timey_gui.py -v`
  Expected: ERRORS — `timey_gui` has no attribute `find_libfaketime`

- [ ] **Step 3: Add imports and `find_libfaketime()` to `timey_gui.py`**

  Add to the top of `timey_gui.py` after the existing imports:
  ```python
  import glob
  import subprocess
  ```

  Add the following function before `def main():`:
  ```python
  def find_libfaketime():
      """Return the path to libfaketime.so if found, or None."""
      try:
          result = subprocess.run(
              ["ldconfig", "-p"],
              capture_output=True, text=True, timeout=5
          )
          for line in result.stdout.splitlines():
              if "libfaketime.so" in line:
                  parts = line.split(" => ", 1)
                  if len(parts) == 2:
                      path = parts[1].strip()
                      if os.path.isfile(path):
                          return path
      except Exception:
          pass

      fallback_patterns = [
          "/usr/lib/libfaketime.so*",
          "/usr/local/lib/libfaketime.so*",
          "/usr/lib/x86_64-linux-gnu/libfaketime.so*",
          "/usr/lib/aarch64-linux-gnu/libfaketime.so*",
      ]
      for pattern in fallback_patterns:
          matches = glob.glob(pattern)
          for match in matches:
              if os.path.isfile(match):
                  return match

      return None
  ```

- [ ] **Step 4: Run the tests — expect all to pass**

  Run: `pytest tests/test_timey_gui.py -v`
  Expected:
  ```
  tests/test_timey_gui.py::TestFindLibfaketime::test_found_via_ldconfig PASSED
  tests/test_timey_gui.py::TestFindLibfaketime::test_ldconfig_stale_path_falls_through_to_glob PASSED
  tests/test_timey_gui.py::TestFindLibfaketime::test_found_via_glob_fallback PASSED
  tests/test_timey_gui.py::TestFindLibfaketime::test_not_found_returns_none PASSED
  ```

- [ ] **Step 5: Commit**

  ```bash
  git add timey_gui.py tests/test_timey_gui.py
  git commit -m "feat: add find_libfaketime() with tests"
  ```

---

### Task 5: Call `find_libfaketime()` on startup with error dialog

**Files:**
- Modify: `timey_gui.py`

The check runs before the main window appears. Tkinter requires a root window before `messagebox` can be called, so we create it hidden (`root.withdraw()`), run the check, then show it (`root.deiconify()`) only on success.

- [ ] **Step 1: Add imports for `sys` and `tkinter.messagebox`**

  Add to the imports at the top of `timey_gui.py`:
  ```python
  import sys
  import tkinter.messagebox
  ```

- [ ] **Step 2: Restructure the start of `main()` to hide the window until the check passes**

  Find this block near the start of `main()`:
  ```python
  # create root window
  root = tkinter.Tk()

  # root window title and dimension
  root.title("Timey-Wimey")
  # Set geometry(widthxheight)
  root.geometry('350x800')
  ```

  Replace it with:
  ```python
  # Create root window hidden until dependency check passes
  root = tkinter.Tk()
  root.withdraw()

  lib_path = find_libfaketime()
  if lib_path is None:
      tkinter.messagebox.showerror(
          "Missing dependency",
          "libfaketime not found.\n\n"
          "Install it with:\n"
          "  sudo apt install libfaketime\n\n"
          "Or build from source:\n"
          "  https://github.com/wolfcw/libfaketime"
      )
      sys.exit(1)

  root.title("Timey-Wimey")
  root.geometry('350x800')
  root.deiconify()
  ```

  Note: the result is stored in `lib_path` (not discarded) to avoid a redundant second call if it is needed later.

- [ ] **Step 3: Add an automated test for the error-dialog path**

  Add the following test to `TestFindLibfaketime` in `tests/test_timey_gui.py` (append inside the class):
  ```python
      def test_startup_shows_error_and_exits_when_not_found(self):
          """main() shows an error dialog and sys.exit(1) when libfaketime is missing."""
          with patch("timey_gui.find_libfaketime", return_value=None), \
               patch("timey_gui.tkinter.messagebox.showerror") as mock_error, \
               patch("timey_gui.sys.exit", side_effect=SystemExit(1)) as mock_exit, \
               patch("timey_gui.tkinter.Tk"):
              with pytest.raises(SystemExit):
                  timey_gui.main()
          mock_error.assert_called_once()
          mock_exit.assert_called_once_with(1)
  ```

  Also add `import pytest` to the imports at the top of `tests/test_timey_gui.py`.

  Run: `pytest tests/test_timey_gui.py::TestFindLibfaketime::test_startup_shows_error_and_exits_when_not_found -v`
  Expected: FAIL (the main() restructure from Step 2 hasn't been applied yet — that's correct TDD order.)

- [ ] **Step 4: Verify the check works manually without libfaketime**

  Simulate absence by monkey-patching in a throwaway script. Create `/tmp/test_missing.py`:
  ```python
  import timey_gui
  timey_gui.find_libfaketime = lambda: None
  timey_gui.main()
  ```
  Run: `python3 /tmp/test_missing.py`
  Expected: error dialog appears; after dismissing, the process exits.
  Delete `/tmp/test_missing.py` when done.

- [ ] **Step 5: Run the full test suite to confirm nothing broke**

  Run: `pytest tests/test_timey_gui.py -v`
  Expected: all 5 tests pass (4 original + the new startup test)

- [ ] **Step 6: Commit**

  ```bash
  git add timey_gui.py tests/test_timey_gui.py
  git commit -m "feat: check for libfaketime on startup with friendly error dialog"
  ```

---

## Chunk 3: Python GUI — Status Label

### Task 6: Extract and test `format_offset_label()`

**Files:**
- Modify: `timey_gui.py` (add `format_offset_label` function)
- Modify: `tests/test_timey_gui.py`

The label-text formatting is a pure function — extract it to test it without a Tk window.

- [ ] **Step 1: Write the failing tests**

  Add the following class to the end of `tests/test_timey_gui.py`:
  ```python
  class TestFormatOffsetLabel:
      def test_positive_value(self):
          assert timey_gui.format_offset_label(0.5) == "Offset: +0.50s"

      def test_negative_value(self):
          assert timey_gui.format_offset_label(-1.0) == "Offset: -1.00s"

      def test_zero(self):
          assert timey_gui.format_offset_label(0.0) == "Offset: 0.00s (no adjustment)"

      def test_positive_large(self):
          assert timey_gui.format_offset_label(3.0) == "Offset: +3.00s"

      def test_negative_large(self):
          assert timey_gui.format_offset_label(-3.0) == "Offset: -3.00s"
  ```

- [ ] **Step 2: Run tests — expect AttributeError**

  Run: `pytest tests/test_timey_gui.py::TestFormatOffsetLabel -v`
  Expected: ERRORS — `timey_gui` has no attribute `format_offset_label`

- [ ] **Step 3: Add `format_offset_label()` to `timey_gui.py`**

  Add after `find_libfaketime()` and before `def main()`:
  ```python
  def format_offset_label(value: float) -> str:
      """Return the display string for the offset status label."""
      if value == 0.0:
          return "Offset: 0.00s (no adjustment)"
      return f"Offset: {value:+.2f}s"
  ```

- [ ] **Step 4: Run tests — expect all 5 to pass**

  Run: `pytest tests/test_timey_gui.py::TestFormatOffsetLabel -v`
  Expected: all 5 tests pass

- [ ] **Step 5: Run full test suite — expect all 10 tests pass**

  Run: `pytest tests/test_timey_gui.py -v`
  Expected: all 10 tests pass (5 from `TestFindLibfaketime` including the startup test, 5 from `TestFormatOffsetLabel`)

- [ ] **Step 6: Commit**

  ```bash
  git add timey_gui.py tests/test_timey_gui.py
  git commit -m "feat: add format_offset_label() with tests"
  ```

---

### Task 7: Add status label to the GUI

**Files:**
- Modify: `timey_gui.py`

Wire `format_offset_label` into the Tkinter layout. The label appears below the Reset button and updates on every slider change. The `set_fakename` and `reset_scale` inner functions reference `status_label` via Python's late-binding closure, so `status_label` only needs to be assigned before `root.mainloop()` is called (not before the inner functions are defined).

**Step ordering is critical:** Step 1 (creating `status_label`) MUST be applied before Steps 2 and 3. Both `set_fakename` and `reset_scale` reference `status_label` as a closure variable. Python closures are late-binding — `status_label` is looked up at call time, not at definition time — so the functions can be defined before `status_label` is assigned, as long as `status_label` exists by the time `root.mainloop()` starts. Tkinter only invokes widget callbacks (Scale command, Button command) after `mainloop()` begins, and `mainloop()` is the last statement in `main()`, after `status_label` is created. The same late-binding pattern is already used by `reset_scale` referencing `scale` in the current code. Applying Step 1 before Steps 2/3 is required so the replacement code has a `status_label` to reference.

- [ ] **Step 1: Add the `status_label` widget immediately after `reset_button.pack()`**

  Find:
  ```python
  reset_button = tkinter.Button(root, text="Reset", command=reset_scale)
  reset_button.pack()
  ```

  Replace with:
  ```python
  reset_button = tkinter.Button(root, text="Reset", command=reset_scale)
  reset_button.pack()

  status_label = tkinter.Label(root, text=format_offset_label(0.0))
  status_label.pack()
  ```

- [ ] **Step 2: Update `set_fakename` to refresh the label**

  Find:
  ```python
  def set_fakename(my_value, outfile):
      my_value = f"{float(my_value):+.2f}s"
      with open(outfile, "w") as f:
          f.write(my_value + "\n")
  ```

  Replace with:
  ```python
  def set_fakename(my_value, outfile):
      value = float(my_value)
      with open(outfile, "w") as f:
          f.write(f"{value:+.2f}s\n")
      status_label.config(text=format_offset_label(value))
  ```

- [ ] **Step 3: Update `reset_scale` to reset the label**

  Find:
  ```python
  def reset_scale():
      scale.set(0)
  ```

  Replace with:
  ```python
  def reset_scale():
      scale.set(0)
      status_label.config(text=format_offset_label(0.0))
  ```

- [ ] **Step 4: Manual smoke test**

  Run: `python3 timey_gui.py`
  - Window opens with label `Offset: 0.00s (no adjustment)`
  - Drag slider to a positive value → label updates to e.g. `Offset: +0.50s`
  - Drag slider to a negative value → label updates to e.g. `Offset: -1.00s`
  - Click Reset → label returns to `Offset: 0.00s (no adjustment)`

- [ ] **Step 5: Run full test suite**

  Run: `pytest tests/test_timey_gui.py -v`
  Expected: all 10 tests pass

- [ ] **Step 6: Commit**

  ```bash
  git add timey_gui.py
  git commit -m "feat: add live offset status label to GUI"
  ```
