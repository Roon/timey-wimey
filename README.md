# timey-wimey

timey-wimey is a tool which allows you to fake the time read by WSJT-X. It uses a file called .faketimerc which lives in your home directory.

Experimental Tool. Use at Your Own Risk.

## Installation

This tool requires the presence of libfaketime and the faketime wrapper. The souce can be found at https://github.com/wolfcw/libfaketime, but you may be able to install it using your package manager, as shown below.

```bash
git clone https://github.com/Roon/timey-wimey.git
sudo apt-get install faketime
```

## Usage

```bash
sh ./timey-wimey/launch-wsjtx.sh
```

## Contributing

Pull requests are welcome. For major changes, please open an issue first
to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License

[MIT](https://choosealicense.com/licenses/mit/)
