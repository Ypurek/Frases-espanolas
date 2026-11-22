import hashlib
import hmac
import json
import os
import random
import secrets
from urllib.parse import quote, urlsplit

from flask import Flask, Response, make_response, redirect, render_template, request

from . import csvio, db
from .i18n import LANGS, pick_lang, translator

ADMIN_KEY = os.environ.get("ADMIN_KEY", "")
MAX_AGE = 400 * 24 * 3600  # browsers cap cookie lifetime at 400 days
USED_LIMIT = 300  # shortcut: keeps the cookie under 4KB; oldest ids drop off, raise only with server-side storage
MODES = {"tf": "True or false", "es": "Pick: Spanish → Ukrainian", "uk": "Pick: Ukrainian → Spanish"}

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 10_000_000  # hard cap; csvio rejects anything over 2 MB with a friendly message
db.init()


def admin_token():
    return hmac.new(ADMIN_KEY.encode(), b"admin", hashlib.sha256).hexdigest()


def is_admin():
    return bool(ADMIN_KEY) and hmac.compare_digest(request.cookies.get("admin", ""), admin_token())


def consented():
    return request.cookies.get("consent") == "1"


def skip_examples():
    return request.cookies.get("skip") == "1"


def tr():
    return translator(pick_lang(request))


def render(name, **ctx):
    lang = pick_lang(request)
    ctx = {"is_admin": is_admin(), "consent": request.cookies.get("consent"), "lang": lang, "langs": LANGS,
           "_": translator(lang), "skip": skip_examples(), "msg": request.args.get("msg", ""), **ctx}
    return make_response(render_template(name, **ctx))


def set_cookie(resp, key, value):
    resp.set_cookie(key, str(value), max_age=MAX_AGE, httponly=True, samesite="Lax", secure=request.is_secure)


def used_ids(mode):
    return [int(x) for x in request.cookies.get(f"used_{mode}", "").split(".") if x.isdigit()]


def int_cookie(key):
    v = request.cookies.get(key, "")
    return int(v) if v.isdigit() else 0


def form_fields():
    return [request.form.get(f, "") for f in db.FIELDS]


def clean(phrase, translation, note, example):
    data = {k: v.strip()[:1000] for k, v in zip(db.FIELDS, (phrase, translation, note, example))}
    return data if data["phrase"] and data["translation"] else None


def back(url="/", msg=""):
    if msg:  # msg is already translated; it rides in the URL so it survives the redirect
        url += ("&" if "?" in url else "?") + "msg=" + quote(msg)
    return redirect(url, 303)


def back_to_referer():
    ref = urlsplit(request.headers.get("referer", ""))
    target = (ref.path or "/") + (f"?{ref.query}" if ref.query else "")  # path only: never redirect off-site
    return back(target if target.startswith("/") and not target.startswith("//") else "/")


# ---------- public ----------

@app.get("/")
def menu():
    pending = db.q("SELECT COUNT(*) AS n FROM suggestions")[0]["n"] if is_admin() else 0
    return render("menu.html", modes=MODES, pending=pending)


@app.get("/phrases")
def phrases():
    q = request.args.get("q", "")
    rows = db.all_rows("phrases")
    needle = q.casefold().strip()
    if needle:  # shortcut: filters in Python because SQLite LIKE ignores Cyrillic case; fine for thousands of rows
        rows = [r for r in rows if needle in r["phrase"].casefold() or needle in r["translation"].casefold()]
    return render("phrases.html", rows=rows, q=q)


@app.get("/lang/<code>")
def set_lang(code):
    resp = back_to_referer()
    if code in LANGS:
        set_cookie(resp, "lang", code)
    return resp


@app.get("/skip-examples")
def toggle_skip_examples():
    resp = back_to_referer()
    set_cookie(resp, "skip", "0" if skip_examples() else "1")
    return resp


@app.get("/phrases.csv")
def phrases_csv():
    return Response(csvio.export(db.all_rows("phrases")), content_type="text/csv; charset=utf-8",
                    headers={"Content-Disposition": 'attachment; filename="phrases.csv"'})


@app.get("/suggest")
def suggest_form():
    return render("suggest.html")


@app.post("/suggest")
def suggest():
    data = clean(*form_fields())
    if not data:
        return back("/suggest")
    db.add("suggestions", data)
    return back("/", tr()("Thanks! Your phrase is waiting for approval."))


# ---------- games ----------

@app.get("/play/<mode>")
def play(mode):
    if mode not in MODES:
        return back()
    need = 2 if mode == "tf" else 4
    if len(db.q("SELECT id FROM phrases LIMIT ?", (need,))) < need:
        return back("/", tr()("Need at least {n} phrases for this game.", n=need))

    p = db.random_phrase(used_ids(mode))
    reset = p is None
    if reset:  # every phrase seen: start a new round
        p = db.random_phrase([])
    ctx = {"mode": mode, "title": MODES[mode], "p": p, "streak": int_cookie(f"streak_{mode}")}

    if mode == "tf":
        others = [o for o in db.random_others(p["id"]) if o["translation"] != p["translation"]]
        ctx["shown"] = p if random.random() < 0.5 or not others else others[0]
    else:
        field = "translation" if mode == "es" else "phrase"
        options, seen = [p], {p[field]}
        for o in db.random_others(p["id"]):
            if o[field] not in seen and len(options) < 4:
                options.append(o)
                seen.add(o[field])
        random.shuffle(options)
        ctx.update(options=options, field=field, question=p["phrase" if mode == "es" else "translation"])

    resp = render("play.html", **ctx)
    if reset and consented():
        set_cookie(resp, f"used_{mode}", "")
    return resp


@app.post("/play/<mode>")
def answer(mode):
    p = db.get("phrases", request.form.get("phrase_id", type=int))
    other = db.get("phrases", request.form.get("other_id", type=int))
    if mode not in MODES or not p or not other:
        return back(f"/play/{mode}" if mode in MODES else "/")

    if mode == "tf":
        correct = (p["translation"] == other["translation"]) == (request.form.get("answer") == "yes")
    else:
        field = "translation" if mode == "es" else "phrase"
        correct = p[field] == other[field]

    s = int_cookie(f"streak_{mode}") + 1 if correct else 0
    best = max(s, int_cookie(f"best_{mode}"))
    if correct and skip_examples():  # straight to the next phrase; the banner confirms the answer
        resp = back(f"/play/{mode}", tr()("Correct! ¡Muy bien!"))
    else:
        resp = render("result.html", mode=mode, title=MODES[mode], p=p, other=other,
                      correct=correct, streak=s, best=best)
    if consented():
        used = [i for i in used_ids(mode) if i != p["id"]] + [p["id"]]
        set_cookie(resp, f"used_{mode}", ".".join(map(str, used[-USED_LIMIT:])))
        set_cookie(resp, f"streak_{mode}", s)
        set_cookie(resp, f"best_{mode}", best)
    return resp


# ---------- admin ----------

@app.post("/admin/login")
def login():
    key = request.form.get("key", "")
    if not ADMIN_KEY or not hmac.compare_digest(key.encode(), ADMIN_KEY.encode()):
        return back("/", tr()("Wrong key."))
    resp = back("/admin")
    set_cookie(resp, "admin", admin_token())
    return resp


@app.post("/admin/logout")
def logout():
    resp = back()
    resp.delete_cookie("admin")
    return resp


def admin_page(phrases, **ctx):
    suggestions = [(s, db.similar(s["phrase"], phrases)) for s in db.q("SELECT * FROM suggestions ORDER BY id")]
    return render("admin.html", suggestions=suggestions, count=len(phrases), **ctx)


@app.get("/admin")
def admin():
    if not is_admin():
        return back()
    return admin_page(db.all_rows("phrases"))


@app.post("/admin/phrases")
def admin_add():
    if not is_admin():
        return back()
    data = clean(*form_fields())
    if not data:
        return back("/admin", tr()("Phrase and translation are required."))
    phrases = db.all_rows("phrases")
    similar = db.similar(data["phrase"], phrases)
    if similar and not request.form.get("force"):  # show the form again with a warning; "Add anyway" resubmits with force
        return admin_page(phrases, draft=data, add_similar=similar)
    db.add("phrases", data)
    return back("/admin", tr()("Phrase added."))


@app.get("/admin/import")
def import_form():
    if not is_admin():
        return back()
    return render("import.html")


@app.errorhandler(413)
def too_large(_err):
    return back("/admin/import", tr()("File is larger than 2 MB."))


@app.post("/admin/import")
def import_preview():
    if not is_admin():
        return back()
    file = request.files.get("file")
    if not file:
        return back("/admin/import")
    error, rows = csvio.parse(file.read(csvio.MAX_BYTES + 1), db.all_rows("phrases"), tr())
    valid = [r["data"] for r in rows if not r["problems"]]
    token = ""
    if valid:  # parsed rows wait server-side until confirmed; only the latest preview is kept
        token = secrets.token_urlsafe(16)
        db.q("DELETE FROM imports")
        db.q("INSERT INTO imports (token, data) VALUES (?, ?)", (token, json.dumps(valid)))
    return render("import.html", error=error, rows=rows, valid=len(valid), token=token, filename=file.filename)


@app.post("/admin/import/confirm")
def import_confirm():
    if not is_admin():
        return back()
    found = db.q("SELECT data FROM imports WHERE token = ?", (request.form.get("token", ""),))
    if not found:
        return back("/admin/import", tr()("This preview expired. Upload the file again."))
    rows = [d for d in (clean(**r) for r in json.loads(found[0]["data"])) if d]
    db.add_many("phrases", rows)
    db.q("DELETE FROM imports")
    return back("/admin/import", tr()("Imported: {n}.", n=len(rows)))


@app.get("/admin/phrases/<int:id>")
def admin_edit_form(id):
    row = db.get("phrases", id)
    if not is_admin() or not row:
        return back("/admin" if is_admin() else "/")
    return render("edit.html", row=row)


@app.post("/admin/phrases/<int:id>")
def admin_edit(id):
    if not is_admin():
        return back()
    if request.form.get("action") == "delete":
        db.delete("phrases", id)
        return back("/phrases")
    data = clean(*form_fields())
    if not data:
        return back(f"/admin/phrases/{id}")
    db.update("phrases", id, data)
    return back("/phrases?q=" + quote(data["phrase"]))


@app.get("/admin/suggestions/<int:id>")
def admin_review_form(id):
    row = db.get("suggestions", id)
    if not is_admin() or not row:
        return back("/admin#suggestions" if is_admin() else "/")
    return render("suggestion.html", row=row, similar=db.similar(row["phrase"], db.all_rows("phrases")))


@app.post("/admin/suggestions/<int:id>")
def admin_review(id):
    if not is_admin():
        return back()
    approve = request.form.get("action") == "approve"
    if approve:
        data = clean(*form_fields())
        if not data:
            return back("/admin", tr()("Phrase and translation are required."))
        db.add("phrases", data)
    db.delete("suggestions", id)
    return back("/admin", tr()("Approved." if approve else "Rejected."))


application = app  # the WSGI callable passenger_wsgi.py imports
