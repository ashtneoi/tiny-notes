from functools import partial, wraps
from traceback import print_exc

from werkzeug.exceptions import \
    abort, BadRequestKeyError, HTTPException, NotFound
from werkzeug.routing import Map, Rule
from werkzeug.utils import redirect
from werkzeug.wrappers import Request, Response


HTMLResponse = partial(Response, content_type='text/html')


def status(req, code):
    if code == 404:
        with open("special/404.html") as f:
            return HTMLResponse(
                f.read(), status=code,
            )
    elif 500 <= code < 600:
        with open("special/50x.html") as f:
            return HTMLResponse(
                f.read(), status=code,
            )
    else:
        print("warning: unhandled status code {}".format(code))
        abort(code)


def static_redirect(to):
    def inner(req):
        return redirect(to)
    return inner


def create_single_page_app(handler, status=status):
    def app(environ, start_response):
        print(environ)
        with Request(environ) as req:
            try:
                if req.method in ('GET', 'POST'):
                    resp = handler(req)
                else:
                    resp = status(req, 400)(environ, start_response)
            except NotFound:
                resp = status(req, 404)
            except BadRequestKeyError as e:
                # raised when indexing req.args or req.form fails
                print_exc()
                resp = status(req, 500)
            except HTTPException as e:
                resp = e
            return resp(environ, start_response)
    return app
