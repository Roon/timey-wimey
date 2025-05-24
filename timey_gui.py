import tkinter
import os

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

main()
