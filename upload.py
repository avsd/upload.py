import os
import sys
import io
import urllib
from http import server, HTTPStatus
from functools import partial

UPLOAD_LINK = '... click here to upload files ...'
UPLOAD_PAGE_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
  <meta http-equiv="Content-Type" content="text/html; charset={enc}">
  <title>Upload to {displaypath}</title>
  <script>
    function upload() {{
      var files = Array.from(document.getElementById("file").files);
      if (!files.length) {{ return; }}
      document.write('<h2>Uploading ' + files.length + 'files...</h2>');
      files.reduce((acc, file, i) => acc.then(
          () => fetch(document.location.href, {{ method: 'POST', body: file, headers: {{ filename: file.name }} }})
        ).then(() => document.write('<br>' + (i + 1) + '. Uploaded: <b>' + file.name + '</b>')).catch(console.error),
        new Promise(resolve => resolve())
      ).then(() => {{ window.location = document.referrer }});
    }}
  </script>
</head>
<body>
  <h1>Upload to {displaypath}</h1>
  <hr><input id="file" type="file" onchange="upload()" multiple><hr>
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
        encoded = UPLOAD_PAGE_TEMPLATE.format(**locals()).encode(enc, 'surrogateescape')
        f.write(encoded)
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
    if sys.version_info.minor > 6:
        parser.add_argument(
            '--directory', '-d', default=os.getcwd(), help='Directory to list [default:current directory]')
    parser.add_argument('port', action='store', default=8000, type=int, nargs='?', help='Port number [default: 8000]')
    args = vars(parser.parse_args())
    handler_class = (
        partial(SimpleHTTPRequestHandlerWithUpload, directory=args.pop('directory'))
        if sys.version_info.minor > 6
        else SimpleHTTPRequestHandlerWithUpload
    )
    if not args.get('bind'):
        args.pop('bind')
    server.test(HandlerClass=handler_class, **args)
