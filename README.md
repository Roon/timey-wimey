# Timey-Wimey WSJT-X Launcher

**Timey-Wimey** is a Linux utility for ham radio operators using FT8 mode who want to temporarily adjust the perceived system clock (via `libfaketime`) **only for WSJT-X**, without affecting the rest of their system.

It includes a simple GUI slider for setting an offset of ±3 seconds in 0.05s increments and launches WSJT-X with that offset.

Experimental Tool. Use at Your Own Risk.

## Features

- Fake system time only for WSJT-X (using `libfaketime`)
- Simple GUI with a vertical slider
- Respects high-resolution time APIs
- Safe and reversible — does not touch actual system clock

## Requirements

- Linux
- `libfaketime` (e.g., `sudo apt install libfaketime` or build from source at at https://github.com/wolfcw/libfaketime)
- `tkinter` for GUI (typically preinstalled with Python)
- WSJT-X installed and in your `$PATH`


## Installation

```bash
git clone https://github.com/Roon/timey-wimey.git
cd timey-wimey
chmod +x launch_wsjtx.sh
```

## Usage

```bash
sh ./launch-wsjtx.sh
```

## Notes
The time offset is stored in ~/.faketimerc

This tool does not modify your system time globally.

When adjusting the time in a negative direction, WSJT-X waits the amount of the time delta before accepting the new time. 

## Contributing

Pull requests are welcome. For major changes, please open an issue first
to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License

[MIT](https://choosealicense.com/licenses/mit/)
