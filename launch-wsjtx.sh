#!/bin/bash
# ~/launch-wsjtx.sh
# Launch Timey-Wimey GUI and WSJT-X with libfaketime

set -eu pipefail

# Execute timey-wimey
python3 "$HOME/timey-wimey/timey_gui.py" &

# Execute wsjtx
env \
        FAKETIME_NO_CACHE=1 \
        FAKETIME_CLOCK=real \
        FAKETIME_MONOTONIC=1 \
        LD_PRELOAD=$(dpkg -L libfaketime | grep libfaketime.so.1) \
        wsjtx

exit 0

### End of File ###
