import datetime
import html
import re
import toml

from werkzeug.utils import redirect

from bakery import render_path
from tantilla import create_app, HTMLResponse, static_redirect, status


def note(req):
    if not "day" in req.args:
        return redirect(
            (
                "note?day="
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

    name = "notes/me/" + day_str
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
            "base": "/",
            "title": day_str,
            "day": day_str,
            "yesterday": (day - one_day).isoformat(),
            "tomorrow": (day + one_day).isoformat(),
            "content": html.escape(content)[:-1],
        }),
    )


application = create_app("/", (
    ("note", note),
))
