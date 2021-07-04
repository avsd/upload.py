# Uploading files using Python 3 in less than 100 lines

Simple server for listing file directory over HTTP, and uploading files.
Based on `http.server`, this module adds file upload functionality to it.

Just as with `http.server`, you SHOULD NOT use this module in
untrusted environment (such as servers exposed to the Internet
or public Wi-Fi networks): it is not secure!

## Usage

Same as for `http.server`:

    python3 -m upload

or:
    
    python3 upload.py

supported arguments (see `python3 -m upload -h`):

usage: upload.py [-h] [--bind ADDRESS] [--directory DIRECTORY] [port]

    positional arguments:
    port                  Port number [default: 8000]

    optional arguments:
    -h, --help            show this help message and exit
    --bind ADDRESS, -b ADDRESS
                            Bind address [default: all interfaces]
    --directory DIRECTORY, -d DIRECTORY
                            Directory to list [default:current directory]

## License

MIT License, © David Avsajanishvili

See LICENSE
