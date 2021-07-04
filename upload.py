import os
import sys
import io
import urllib
from http import server, HTTPStatus
from functools import partial
import contextlib

UPLOAD_LINK = '... click here to upload a file ...'
UPLOAD_PAGE_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
  <meta http-equiv="Content-Type" content="text/html; charset={enc}">
  <title>Upload to {displaypath}</title>
  <script>
    function upload() {{
      var file = document.getElementById("file").files[0];
      if (!file) {{ return; }}
      fetch(document.location.href, {{ method: 'POST', body: file, headers: {{ filename: file.name }} }})
        .catch(console.error)
        .then(() => {{ window.location = document.referrer }});
    }}
  </script>
</head>
<body>
  <h1>Upload to {displaypath}</h1>
  <hr><input id="file" type="file" onchange="upload()"><hr>
</body>
</html>
'''


class SimpleHTTPRequestHandlerWithUpload(server.SimpleHTTPRequestHandler):

    def list_directory(self, path):
        """Adds a link to upload file."""
        try:
            listdir = os.listdir
            os.listdir = lambda path: [UPLOAD_LINK] + listdir(path)
            return super(SimpleHTTPRequestHandlerWithUpload, self).list_directory(path)
        finally:
            os.listdir = listdir

    def send_head(self):
        """Adds special processing to the UPLOAD_LINK path"""
        path = self.translate_path(self.path)
        if os.path.basename(path).startswith(UPLOAD_LINK):
            return self.render_upload_form(os.path.dirname(self.path))
        return super(SimpleHTTPRequestHandlerWithUpload, self).send_head()

    def render_upload_form(self, path):
        enc = sys.getfilesystemencoding()
        try:
            displaypath = urllib.parse.unquote(path, errors='surrogatepass')
        except UnicodeDecodeError:
            displaypath = urllib.parse.unquote(path)
        f = io.BytesIO()
        f.write(UPLOAD_PAGE_TEMPLATE.format(**locals()).encode(enc, 'surrogateescape'))
        f.seek(0)
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-type", "text/html; charset=%s" % enc)
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        return f

    def do_POST(self):
        """Handle file upload."""
        path = self.translate_path(self.path)
        if not os.path.basename(path).startswith(UPLOAD_LINK):
            self.send_error(HTTPStatus.NOT_IMPLEMENTED, "Unsupported method (%r)" % self.command)
            return
        with open(self.headers.get('filename', 'uploaded_file'), 'wb') as f:
            f.write(self.rfile.read(int(self.headers.get('content-length', 0))))
        self.send_error(HTTPStatus.OK, 'File uploaded.')


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--bind', '-b', metavar='ADDRESS', help='Bind address [default: all interfaces]')
    parser.add_argument('--directory', '-d', default=os.getcwd(), help='Directory to list [default:current directory]')
    parser.add_argument('port', action='store', default=8000, type=int, nargs='?', help='Port number [default: 8000]')
    args = parser.parse_args()
    handler_class = partial(SimpleHTTPRequestHandlerWithUpload, directory=args.directory)
    server.test(HandlerClass=handler_class, port=args.port, **({'bind': args.bind} if args.bind else {}))
