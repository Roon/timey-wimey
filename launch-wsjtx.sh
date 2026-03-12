#!/bin/bash
# launch-wsjtx.sh
# Launch Timey-Wimey GUI and WSJT-X with libfaketime

set -euo pipefail

# Find libfaketime shared library
LIBFAKETIME_PATH=$(dpkg -L libfaketime | grep libfaketime.so.1)
# Verify the ldconfig result actually exists on disk
[ -n "$LIBFAKETIME_PATH" ] && [ ! -e "$LIBFAKETIME_PATH" ] && LIBFAKETIME_PATH=""


if [ -z "$LIBFAKETIME_PATH" ]; then
   LIBFAKETIME_PATH=$(ldconfig -p | grep 'libfaketime\.so' | awk -F' => ' '{print $2}' | head -1)
fi


if [ -z "$LIBFAKETIME_PATH" ]; then
    for dir in /usr/lib /usr/local/lib /usr/lib/x86_64-linux-gnu /usr/lib/aarch64-linux-gnu /usr/lib/x86_64-linux-gnu/faketime ; do
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
