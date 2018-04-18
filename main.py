import datetime
import html
import re

from werkzeug.urls import url_unquote
from werkzeug.utils import redirect

from auth import AuthManager
from bakery import render_path
from config import config
from tantilla import create_app, HTMLResponse, static_redirect, status


MOUNT_POINT = config["mount_point"]

auth_mgr = AuthManager(MOUNT_POINT)


def login(req):
    if req.method == 'POST':
        if "username" not in req.form or "password" not in req.form:
            return status(req, 400)
        username = req.form["username"]
        password = req.form["password"]

        auth_result = auth_mgr.try_log_in(username, password)
        if auth_result == AuthManager.USER_NOT_FOUND:
            return HTMLResponse(
                render_path("tmpl/login.htmo", {
                    "base": MOUNT_POINT,
                    "bad_username": True,
                    "bad_password": False,
                }),
                status=403,  # This one is iffy.
            )
        elif auth_result == AuthManager.PW_WRONG:
            return HTMLResponse(
                render_path("tmpl/login.htmo", {
                    "base": MOUNT_POINT,
                    "bad_username": False,
                    "bad_password": True,
                }),
                status=403,  # This one is iffy.
            )
        else:
            id_, expiration = auth_result
            from_ = url_unquote(req.args.get("from", ""))

            resp = redirect(MOUNT_POINT + from_, code=303)
            resp.set_cookie("id", id_, expires=expiration, secure=True)
            return resp

    if auth_mgr.cookie_to_username(req.cookies.get("id")):
        # Already logged in.
        return redirect(MOUNT_POINT, code=303)
    else:
        resp = HTMLResponse(
            render_path("tmpl/login.htmo", {
                "base": MOUNT_POINT,
                "bad_username": False,
                "bad_password": False,
            }),
        )
        resp.delete_cookie("id")
        return resp


def logout(req):
    if req.method == 'POST':
         return status(req, 400)

    id_ = req.cookies.get("id")

    resp = redirect(MOUNT_POINT + "login", code=303)
    if id_ and cookie_to_username(id_):
        del sessions[id_]
        resp.delete_cookie("id")
    return resp


def require_auth_render(name):
    @auth_mgr.require_auth
    def inner(req, username):
        return HTMLResponse(
            render_path(name, {
                "base": MOUNT_POINT,
            })
        )
    return inner


@auth_mgr.require_auth
def note(req, username):
    if not "day" in req.args:
        return redirect(
            (
                MOUNT_POINT + "note?day="
                + datetime.datetime.now(
                    datetime.timezone(datetime.timedelta(hours=-8))
                ).date().isoformat()
            ),
            code=307,  # like 302 but with more explicit semantics
        )
    day_str = req.args["day"]
    day_match = re.match("^([0-9]{4})-([0-9]{2})-([0-9]{2})$", day_str)
    if not day_match:
        raise status(req, 400)
    try:
        day = datetime.date(*map(int, day_match.groups()))
    except ValueError:
        raise status(req, 400)

    name = "notes/" + username + "/" + day_str
    one_day = datetime.timedelta(days=1)

    if req.method == 'POST':
        if not "content" in req.form:
            raise status(req, 400)
        with open(name, "w") as f:
            f.write(req.form["content"] + "\n")
        return redirect(req.full_path, code=303)

    try:
        with open(name, "r") as f:
            content = f.read()
    except FileNotFoundError:
        content = ""
    return HTMLResponse(
        render_path("tmpl/note.htmo", {
            "base": MOUNT_POINT,
            "title": day_str,
            "day": day_str,
            "yesterday": (day - one_day).isoformat(),
            "tomorrow": (day + one_day).isoformat(),
            "content": html.escape(content)[:-1],
        }),
    )


application = create_app(MOUNT_POINT, (
    ("", static_redirect(MOUNT_POINT + "note")),
    ("note", note),
    ("login", login),
    ("logout", logout),
))
