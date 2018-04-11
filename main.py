import datetime
import html
import json
import re
from base64 import b64encode
from functools import wraps
from os import urandom

import bcrypt
from werkzeug.exceptions import abort, HTTPException, NotFound
from werkzeug.routing import Map, Rule
from werkzeug.urls import url_quote, url_unquote
from werkzeug.utils import redirect

from bakery import render_path
from config import config
from hashpw import checkpw
from secrets import accounts, SECRET
from tantilla import create_app, HTMLResponse


MOUNT_POINT = config["mount_point"]

sessions = {}  # id: (username, expiration)


def abs_to_rel(path):
    if path[:len(MOUNT_POINT)] == MOUNT_POINT:
        return path[len(MOUNT_POINT):]
    return path


def cookie_to_username(id_):
    session = sessions.get(id_)
    if session is None:
        return None
    username, expiration = session
    if username in accounts and expiration > datetime.datetime.now():
        return username
    else:
        del sessions[id_]
        return None


def require_auth(func):
    @wraps(func)
    def new_func(req):
        username = cookie_to_username(req.cookies.get("id"))
        if username:
            return func(req, username)
        else:
            resp = redirect(
                MOUNT_POINT + "login?from=" + url_quote(
                    abs_to_rel(req.full_path)
                ),
                code=303,
            )
            resp.delete_cookie("id")
            return resp
    return new_func


def login(req):
    if req.method == 'POST':
        if "username" not in req.form or "password" not in req.form:
            return abort(400)
        username = req.form["username"]
        hashed = accounts.get(username)
        if hashed is None:
            return HTMLResponse(
                render_path("tmpl/login.htmo", {
                    "base": MOUNT_POINT,
                    "bad_username": True,
                    "bad_password": False,
                }),
                status=403,  # This one is iffy.
            )
        if not checkpw(req.form["password"], hashed):
            return HTMLResponse(
                render_path("tmpl/login.htmo", {
                    "base": MOUNT_POINT,
                    "bad_username": False,
                    "bad_password": True,
                }),
                status=403,  # This one is iffy.
            )

        sessions2 = sessions.copy()
        for id_ in sessions2:
            _, expiration = sessions2[id_]
            if expiration <= datetime.datetime.now():
                del sessions[id_]

        id_ = b64encode(urandom(32)).decode('ascii')
        assert id_ not in sessions  # until I verify this works
        expiration = datetime.datetime.now() + datetime.timedelta(days=14)

        from_ = ""
        if "from" in req.args:
            from_ = url_unquote(req.args["from"])

        resp = redirect(MOUNT_POINT + from_, code=303)
        resp.set_cookie("id", id_, expires=expiration, secure=True)
        sessions[id_] = (username, expiration)
        return resp

    id_ = req.cookies.get("id")
    if id_ and cookie_to_username(id_):
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
         return abort(400)

    id_ = req.cookies.get("id")

    resp = redirect(MOUNT_POINT + "login", code=303)
    if id_ and cookie_to_username(id_):
        del sessions[id_]
        resp.delete_cookie("id")
    return resp


def require_auth_static(name):
    @require_auth
    def inner(req, username):
        with open(name) as f:
            return HTMLResponse(
                f.read()
            )
    return inner


def require_auth_render(name):
    @require_auth
    def inner(req, username):
        return HTMLResponse(
            render_path(name, {
                "base": MOUNT_POINT,
            })
        )
    return inner


@require_auth
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
        raise abort(400)
    try:
        day = datetime.date(*map(int, day_match.groups()))
    except ValueError:
        raise abort(400)

    name = "notes/" + username + "/" + day_str
    one_day = datetime.timedelta(days=1)

    if req.method == 'POST':
        if not "content" in req.form:
            raise abort(400)
        with open(name, "w") \
                as f:
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
    ("", require_auth_render("tmpl/home.htmo")),
    ("note", note),
    ("login", login),
    ("logout", logout),
))
