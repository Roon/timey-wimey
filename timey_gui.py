import tkinter
import os
import glob
import subprocess


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


def main():
    """Launches a Tkinter GUI for adjusting and saving a time offset value.

    This function creates a window with a vertical scale and a reset button,
    allowing users to set and store a time offset in a configuration file.
    """
    home_directory = os.path.expanduser("~")
    filename = ".faketimerc"
    faketime_config = os.path.join(home_directory, filename)

    def set_fakename(my_value, outfile):
        my_value = f"{float(my_value):+.2f}s"
        with open(outfile, "w") as f:
            f.write(my_value + "\n")

    def reset_scale():
        scale.set(0)

    # create root window
    root = tkinter.Tk()

    # root window title and dimension
    root.title("Timey-Wimey")
    # Set geometry(widthxheight)
    root.geometry('350x800')


    scale = tkinter.Scale(root, from_=3, to=-3, orient='vertical', length=750,
                     tickinterval=0.5, resolution=0.05, label='Value',
                     command=lambda value: set_fakename(value, faketime_config))
    scale.pack()

    reset_button = tkinter.Button(root, text="Reset", command=reset_scale)
    reset_button.pack()

    # Execute Tkinter
    root.mainloop()

if __name__ == "__main__":
    main()
