#!/bin/bash
# ~/launch_wsjtx.sh
# Launch Timey-Wimey GUI and WSJT-X with libfaketime

set -euo pipefail

# Execute timey-wimey
python3 "$HOME/timey-wimey/timey_gui.py" &

# Execute wsjtx
env \
        FAKETIME_NO_CACHE=1 \
        FAKETIME_CLOCK=real \
        FAKETIME_MONOTONIC=1 \
        LD_PRELOAD=/usr/lib/x86_64-linux-gnu/faketime/libfaketime.so.1 \
        /usr/bin/wsjtx

exit 0

### End of File ###
