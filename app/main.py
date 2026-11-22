import hashlib
import hmac
import json
import os
import random
import secrets
from pathlib import Path
from urllib.parse import quote, urlsplit

from a2wsgi import ASGIMiddleware
from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.responses import RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from . import csvio, db
from .i18n import LANGS, pick_lang, translator

BASE = Path(__file__).resolve().parent
ADMIN_KEY = os.environ.get("ADMIN_KEY", "")
MAX_AGE = 400 * 24 * 3600  # browsers cap cookie lifetime at 400 days
USED_LIMIT = 300  # shortcut: keeps the cookie under 4KB; oldest ids drop off, raise only with server-side storage
MODES = {"tf": "True or false", "es": "Pick: Spanish → Ukrainian", "uk": "Pick: Ukrainian → Spanish"}

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")
templates = Jinja2Templates(directory=BASE / "templates")
db.init()


def admin_token():
    return hmac.new(ADMIN_KEY.encode(), b"admin", hashlib.sha256).hexdigest()


def is_admin(req):
    return bool(ADMIN_KEY) and hmac.compare_digest(req.cookies.get("admin", ""), admin_token())


def consented(req):
    return req.cookies.get("consent") == "1"


def skip_examples(req):
    return req.cookies.get("skip") == "1"


def tr(req):
    return translator(pick_lang(req))


def render(req, name, **ctx):
    lang = pick_lang(req)
    return templates.TemplateResponse(req, name, {
        "is_admin": is_admin(req), "consent": req.cookies.get("consent"),
        "lang": lang, "langs": LANGS, "_": translator(lang), "skip": skip_examples(req), **ctx})


def set_cookie(resp, key, value):
    resp.set_cookie(key, str(value), max_age=MAX_AGE, httponly=True, samesite="lax")


def used_ids(req, mode):
    return [int(x) for x in req.cookies.get(f"used_{mode}", "").split(".") if x.isdigit()]


def int_cookie(req, key):
    v = req.cookies.get(key, "")
    return int(v) if v.isdigit() else 0


def clean(phrase, translation, note, example):
    data = {k: v.strip()[:1000] for k, v in zip(db.FIELDS, (phrase, translation, note, example))}
    return data if data["phrase"] and data["translation"] else None


def back(url="/", msg=""):
    if msg:  # msg is already translated; it rides in the URL so it survives the redirect
        url += ("&" if "?" in url else "?") + "msg=" + quote(msg)
    return RedirectResponse(url, status_code=303)


# ---------- public ----------

@app.get("/")
def menu(req: Request, msg: str = ""):
    pending = db.q("SELECT COUNT(*) AS n FROM suggestions")[0]["n"] if is_admin(req) else 0
    return render(req, "menu.html", modes=MODES, msg=msg, pending=pending)


@app.get("/phrases")
def phrases(req: Request, q: str = ""):
    rows = db.all_rows("phrases")
    needle = q.casefold().strip()
    if needle:  # shortcut: filters in Python because SQLite LIKE ignores Cyrillic case; fine for thousands of rows
        rows = [r for r in rows if needle in r["phrase"].casefold() or needle in r["translation"].casefold()]
    return render(req, "phrases.html", rows=rows, q=q)


def back_to_referer(req):
    ref = urlsplit(req.headers.get("referer", ""))
    target = (ref.path or "/") + (f"?{ref.query}" if ref.query else "")  # path only: never redirect off-site
    return back(target if target.startswith("/") and not target.startswith("//") else "/")


@app.get("/lang/{code}")
def set_lang(req: Request, code: str):
    resp = back_to_referer(req)
    if code in LANGS:
        set_cookie(resp, "lang", code)
    return resp


@app.get("/skip-examples")
def toggle_skip_examples(req: Request):
    resp = back_to_referer(req)
    set_cookie(resp, "skip", "0" if skip_examples(req) else "1")
    return resp


@app.get("/phrases.csv")
def phrases_csv():
    return Response(csvio.export(db.all_rows("phrases")), media_type="text/csv; charset=utf-8",
                    headers={"Content-Disposition": 'attachment; filename="phrases.csv"'})


@app.get("/suggest")
def suggest_form(req: Request):
    return render(req, "suggest.html")


@app.post("/suggest")
def suggest(req: Request, phrase: str = Form(...), translation: str = Form(...), note: str = Form(""), example: str = Form("")):
    data = clean(phrase, translation, note, example)
    if not data:
        return back("/suggest")
    db.add("suggestions", data)
    return back("/", tr(req)("Thanks! Your phrase is waiting for approval."))


# ---------- games ----------

@app.get("/play/{mode}")
def play(req: Request, mode: str, msg: str = ""):
    if mode not in MODES:
        return back()
    need = 2 if mode == "tf" else 4
    if len(db.q("SELECT id FROM phrases LIMIT ?", (need,))) < need:
        return back("/", tr(req)("Need at least {n} phrases for this game.", n=need))

    used = used_ids(req, mode)
    p = db.random_phrase(used)
    reset = p is None
    if reset:  # every phrase seen: start a new round
        p = db.random_phrase([])
    ctx = {"mode": mode, "title": MODES[mode], "p": p, "streak": int_cookie(req, f"streak_{mode}"), "msg": msg}

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

    resp = render(req, "play.html", **ctx)
    if reset and consented(req):
        set_cookie(resp, f"used_{mode}", "")
    return resp


@app.post("/play/{mode}")
def answer(req: Request, mode: str, phrase_id: int = Form(...), other_id: int = Form(...), answer: str = Form("")):
    p, other = db.get("phrases", phrase_id), db.get("phrases", other_id)
    if mode not in MODES or not p or not other:
        return back(f"/play/{mode}" if mode in MODES else "/")

    if mode == "tf":
        correct = (p["translation"] == other["translation"]) == (answer == "yes")
    else:
        field = "translation" if mode == "es" else "phrase"
        correct = p[field] == other[field]

    s = int_cookie(req, f"streak_{mode}") + 1 if correct else 0
    best = max(s, int_cookie(req, f"best_{mode}"))
    if correct and skip_examples(req):  # straight to the next phrase; the banner confirms the answer
        resp = back(f"/play/{mode}", tr(req)("Correct! ¡Muy bien!"))
    else:
        resp = render(req, "result.html", mode=mode, title=MODES[mode], p=p, other=other,
                      correct=correct, streak=s, best=best)
    if consented(req):
        used = [i for i in used_ids(req, mode) if i != p["id"]] + [p["id"]]
        set_cookie(resp, f"used_{mode}", ".".join(map(str, used[-USED_LIMIT:])))
        set_cookie(resp, f"streak_{mode}", s)
        set_cookie(resp, f"best_{mode}", best)
    return resp


# ---------- admin ----------

@app.post("/admin/login")
def login(req: Request, key: str = Form(...)):
    if not ADMIN_KEY or not hmac.compare_digest(key.encode(), ADMIN_KEY.encode()):
        return back("/", tr(req)("Wrong key."))
    resp = back("/admin")
    set_cookie(resp, "admin", admin_token())
    return resp


@app.post("/admin/logout")
def logout():
    resp = back()
    resp.delete_cookie("admin")
    return resp


@app.get("/admin")
def admin(req: Request, msg: str = ""):
    if not is_admin(req):
        return back()
    return admin_page(req, db.all_rows("phrases"), msg=msg)


def admin_page(req, phrases, **ctx):
    suggestions = [(s, db.similar(s["phrase"], phrases)) for s in db.q("SELECT * FROM suggestions ORDER BY id")]
    return render(req, "admin.html", suggestions=suggestions, count=len(phrases), **ctx)


@app.post("/admin/phrases")
def admin_add(req: Request, phrase: str = Form(...), translation: str = Form(...),
              note: str = Form(""), example: str = Form(""), force: str = Form("")):
    if not is_admin(req):
        return back()
    data = clean(phrase, translation, note, example)
    if not data:
        return back("/admin", tr(req)("Phrase and translation are required."))
    phrases = db.all_rows("phrases")
    similar = db.similar(data["phrase"], phrases)
    if similar and not force:  # show the form again with a warning; "Add anyway" resubmits with force
        return admin_page(req, phrases, draft=data, add_similar=similar)
    db.add("phrases", data)
    return back("/admin", tr(req)("Phrase added."))


@app.get("/admin/import")
def import_form(req: Request, msg: str = ""):
    if not is_admin(req):
        return back()
    return render(req, "import.html", msg=msg)


@app.post("/admin/import")
def import_preview(req: Request, file: UploadFile = File(...)):
    if not is_admin(req):
        return back()
    error, rows = csvio.parse(file.file.read(csvio.MAX_BYTES + 1), db.all_rows("phrases"), tr(req))
    valid = [r["data"] for r in rows if not r["problems"]]
    token = ""
    if valid:  # parsed rows wait server-side until confirmed; only the latest preview is kept
        token = secrets.token_urlsafe(16)
        db.q("DELETE FROM imports")
        db.q("INSERT INTO imports (token, data) VALUES (?, ?)", (token, json.dumps(valid)))
    return render(req, "import.html", error=error, rows=rows, valid=len(valid), token=token,
                  filename=file.filename)


@app.post("/admin/import/confirm")
def import_confirm(req: Request, token: str = Form(...)):
    if not is_admin(req):
        return back()
    found = db.q("SELECT data FROM imports WHERE token = ?", (token,))
    if not found:
        return back("/admin/import", tr(req)("This preview expired. Upload the file again."))
    rows = [d for d in (clean(**r) for r in json.loads(found[0]["data"])) if d]
    db.add_many("phrases", rows)
    db.q("DELETE FROM imports")
    return back("/admin/import", tr(req)("Imported: {n}.", n=len(rows)))


@app.get("/admin/phrases/{id}")
def admin_edit_form(req: Request, id: int):
    row = db.get("phrases", id)
    if not is_admin(req) or not row:
        return back("/admin" if is_admin(req) else "/")
    return render(req, "edit.html", row=row)


@app.post("/admin/phrases/{id}")
def admin_edit(req: Request, id: int, action: str = Form(...), phrase: str = Form(""),
               translation: str = Form(""), note: str = Form(""), example: str = Form("")):
    if not is_admin(req):
        return back()
    if action == "delete":
        db.delete("phrases", id)
        return back("/phrases")
    data = clean(phrase, translation, note, example)
    if not data:
        return back(f"/admin/phrases/{id}")
    db.update("phrases", id, data)
    return back("/phrases?q=" + quote(data["phrase"]))


@app.get("/admin/suggestions/{id}")
def admin_review_form(req: Request, id: int):
    row = db.get("suggestions", id)
    if not is_admin(req) or not row:
        return back("/admin#suggestions" if is_admin(req) else "/")
    return render(req, "suggestion.html", row=row, similar=db.similar(row["phrase"], db.all_rows("phrases")))


@app.post("/admin/suggestions/{id}")
def admin_review(req: Request, id: int, action: str = Form(...), phrase: str = Form(""),
                 translation: str = Form(""), note: str = Form(""), example: str = Form("")):
    if not is_admin(req):
        return back()
    if action == "approve":
        data = clean(phrase, translation, note, example)
        if not data:
            return back("/admin", tr(req)("Phrase and translation are required."))
        db.add("phrases", data)
    db.delete("suggestions", id)
    return back("/admin", tr(req)("Approved." if action == "approve" else "Rejected."))


application = ASGIMiddleware(app)
