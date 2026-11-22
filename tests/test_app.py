import io
import os
import tempfile

os.environ["DB_PATH"] = os.path.join(tempfile.mkdtemp(), "test.db")
os.environ["ADMIN_KEY"] = "secret"

from flask.testing import FlaskClient  # noqa: E402

from frases import db  # noqa: E402
from frases.main import app  # noqa: E402


class Client(FlaskClient):
    def open(self, *args, **kwargs):
        kwargs.setdefault("follow_redirects", True)
        return super().open(*args, **kwargs)

    def cookie(self, name):
        found = self.get_cookie(name)
        return found.value if found else None


app.test_client_class = Client
c = app.test_client()
c.set_cookie("lang", "en")  # assertions below match English text


def csv_upload(data):
    return {"file": (io.BytesIO(data), "p.csv")}


def test_passenger_entry_point():
    import passenger_wsgi
    assert passenger_wsgi.application is app  # Passenger gets the Flask WSGI app itself


def test_every_ui_string_is_translated():
    import pathlib
    import re
    from frases.i18n import T
    root = pathlib.Path(__file__).resolve().parent.parent / "frases"
    code = "".join(p.read_text(encoding="utf-8") for p in [*root.glob("templates/*.html"), *root.glob("*.py")])
    used = {a or b for a, b in re.findall(r"""_\(\s*(?:"([^"]+)"|'([^']+)')""", code)} - {"en"}
    from frases.main import MODES
    used |= set(MODES.values())
    assert not used - set(T), used - set(T)


def test_language_switch():
    other = app.test_client()
    assert 'lang="uk"' in other.get("/").text  # default without cookie or header
    assert "Aprende" in other.get("/", headers={"accept-language": "es-ES,es;q=0.9"}).text
    r = other.get("/lang/en", headers={"referer": "http://evil.example//x"}, follow_redirects=False)
    assert r.headers["location"] == "/" and other.cookie("lang") == "en"
    r = other.get("/lang/es", headers={"referer": "http://testserver/phrases?q=a"}, follow_redirects=False)
    assert r.headers["location"] == "/phrases?q=a"
    assert "Clave incorrecta" in other.post("/admin/login", data={"key": "x"}).text


def test_levenshtein_and_similar():
    assert db.levenshtein("kitten", "sitting") == 3
    assert db.levenshtein("", "abc") == 3
    assert db.levenshtein("hola", "hola") == 0
    rows = [{"phrase": "¿Qué tal?"}, {"phrase": "Buenos días"}]
    assert [r["phrase"] for _, r in db.similar("que tal?", rows)] == ["¿Qué tal?"]


def test_csv_parse():
    from frases import csvio
    existing = [{"phrase": "Hola", "translation": "Привіт"}]
    assert "UTF-8" in csvio.parse("phrase,translation\nañ,б".encode("cp1251", "replace") + b"\xff", existing)[0]
    assert "Missing column" in csvio.parse(b"foo,bar\n1,2", existing)[0]
    assert "empty" in csvio.parse(b"  ", existing)[0]
    assert "No data rows" in csvio.parse(b"phrase,translation\n", existing)[0]
    text = "﻿Translation;Phrase;note\nПривіт;hola;x\nДякую;Gracias;\n;Sin traducción;\nДякую;gracias;\n\n\"Бувай\n!\";Adiós;\"a;b\"\n"
    err, rows = csvio.parse(text.encode("utf-8"), existing)
    assert err == ""
    assert [r["problems"] for r in rows] == [
        ["already in the database"], [], ["translation is empty"], ["duplicate of an earlier row"], []]
    assert rows[4]["data"] == {"phrase": "Adiós", "translation": "Бувай\n!", "note": "a;b", "example": ""}
    round_trip = csvio.export([{"phrase": "Hola", "translation": "Привіт", "note": 'say "hi"', "example": "a,b"}])
    assert csvio.parse(round_trip.encode("utf-8"), [])[1][0]["data"]["note"] == 'say "hi"'


def test_full_flow():
    assert c.post("/admin/phrases", data={"phrase": "x", "translation": "y"}).status_code == 200  # redirected to menu
    assert not db.all_rows("phrases")

    assert "Wrong key" in c.post("/admin/login", data={"key": "nope"}).text
    c.post("/admin/login", data={"key": "secret"})
    for es, uk in [("Hola", "Привіт"), ("Gracias", "Дякую"), ("Adiós", "Бувай"), ("Por favor", "Будь ласка")]:
        c.post("/admin/phrases", data={"phrase": es, "translation": uk, "note": "n", "example": "e"})
    assert len(db.all_rows("phrases")) == 4

    page = c.post("/admin/phrases", data={"phrase": "hola!", "translation": "Привіт!"}).text
    assert "Not added yet" in page and 'value="hola!"' in page and len(db.all_rows("phrases")) == 4
    c.post("/admin/phrases", data={"phrase": "hola!", "translation": "Привіт!", "force": "1"})
    assert len(db.all_rows("phrases")) == 5
    db.q("DELETE FROM phrases WHERE phrase = 'hola!'")

    c.post("/suggest", data={"phrase": "Holaa", "translation": "Привіт!"})
    page = c.get("/admin").text
    assert "<table>" in page and "⚠ Hola" in page
    sid = db.q("SELECT id FROM suggestions")[0]["id"]
    assert "Similar phrases already exist" in c.get(f"/admin/suggestions/{sid}").text
    c.post(f"/admin/suggestions/{sid}", data={"action": "reject"})
    assert not db.q("SELECT id FROM suggestions")

    c.post("/suggest", data={"phrase": "Vale", "translation": "Гаразд"})
    sid = db.q("SELECT id FROM suggestions")[0]["id"]
    c.post(f"/admin/suggestions/{sid}", data={"action": "approve", "phrase": "Vale", "translation": "Гаразд"})
    assert db.q("SELECT id FROM phrases WHERE phrase = 'Vale'") and not db.q("SELECT id FROM suggestions")
    db.q("DELETE FROM phrases WHERE phrase = 'Vale'")

    assert "Привіт" in c.get("/phrases", query_string={"q": "привіт"}).text

    c.set_cookie("consent", "1")
    hola = db.q("SELECT id FROM phrases WHERE phrase = 'Hola'")[0]["id"]
    r = c.post("/play/es", data={"phrase_id": hola, "other_id": hola})
    assert "Correct" in r.text and c.cookie("streak_es") == "1" and c.cookie("used_es") == str(hola)
    r = c.post("/play/tf", data={"phrase_id": hola, "other_id": hola, "answer": "no"})
    assert "Not quite" in r.text and c.cookie("streak_tf") == "0"

    assert 'aria-checked="false"' in c.get("/").text  # skip-examples is off by default
    c.get("/skip-examples", headers={"referer": "http://testserver/"})
    assert c.cookie("skip") == "1"
    r = c.post("/play/es", data={"phrase_id": hola, "other_id": hola}, follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"].startswith("/play/es?msg=")
    assert c.cookie("streak_es") == "2"  # streak still counts when the result page is skipped
    r = c.post("/play/tf", data={"phrase_id": hola, "other_id": hola, "answer": "no"})
    assert "Not quite" in r.text  # wrong answers still show the example
    c.get("/skip-examples")
    assert c.cookie("skip") == "0"

    for mode in ("tf", "es", "uk"):
        assert c.get(f"/play/{mode}").status_code == 200

    assert "Edit / delete" in c.get("/phrases").text
    assert "Hola" in c.get(f"/admin/phrases/{hola}").text
    c.post(f"/admin/phrases/{hola}", data={"action": "save", "phrase": "¡Hola!", "translation": "Привіт", "note": "", "example": ""})
    assert db.get("phrases", hola)["phrase"] == "¡Hola!"
    c.post(f"/admin/phrases/{hola}", data={"action": "delete"})
    assert db.get("phrases", hola) is None

    before = len(db.all_rows("phrases"))
    csv_bytes = "phrase,translation\nGracias,Дякую\nNuevo,Нове\n,x\n".encode("utf-8")
    page = c.post("/admin/import", data=csv_upload(csv_bytes)).text
    assert "Will be added: 1. Skipped: 2." in page and "already in the database" in page
    assert len(db.all_rows("phrases")) == before  # preview writes nothing
    token = db.q("SELECT token FROM imports")[0]["token"]
    assert "Imported: 1." in c.post("/admin/import/confirm", data={"token": token}).text
    assert len(db.all_rows("phrases")) == before + 1
    assert "expired" in c.post("/admin/import/confirm", data={"token": token}).text
    assert "Nuevo" in c.get("/phrases.csv").text

    c.post("/admin/logout")
    assert c.post("/admin/import", data=csv_upload(csv_bytes)).request.path == "/"
    gratias = db.q("SELECT id FROM phrases WHERE phrase = 'Gracias'")[0]["id"]
    c.post(f"/admin/phrases/{gratias}", data={"action": "delete"})
    assert db.get("phrases", gratias) is not None  # not admin: no delete
    assert "Edit / delete" not in c.get("/phrases").text
