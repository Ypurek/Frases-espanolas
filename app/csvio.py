import csv
import io

from .db import FIELDS
from .i18n import translator

MAX_BYTES = 2_000_000
MAX_ROWS = 5000
MAX_LEN = 1000
REQUIRED = ("phrase", "translation")


def export(rows):
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(FIELDS)
    for r in rows:
        w.writerow([r[f] for f in FIELDS])
    return "﻿" + out.getvalue()  # BOM so Excel opens Cyrillic correctly


def parse(raw, existing, _=translator("en")):
    """Validate an uploaded CSV without writing anything.

    Returns (error, rows): error is a file-level message ("" if the file is usable);
    rows are {"line", "data", "problems"} and only rows with no problems get imported.
    """
    if len(raw) > MAX_BYTES:
        return _("File is larger than 2 MB."), []
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        return _("File must be UTF-8 encoded (in Excel: Save As → “CSV UTF-8”)."), []
    if not text.strip():
        return _("File is empty."), []
    try:
        dialect = csv.Sniffer().sniff(text[:4096], delimiters=",;\t")
    except csv.Error:
        dialect = csv.excel

    reader = csv.reader(io.StringIO(text), dialect)
    try:
        header = [h.strip().lower() for h in next(reader)]
        missing = [f for f in REQUIRED if f not in header]
        if missing:
            return _("Missing column(s): {cols}. First row must be: {fields}.",
                         cols=", ".join(missing), fields=", ".join(FIELDS)), []
        idx = {f: header.index(f) for f in FIELDS if f in header}
        in_db = {(r["phrase"].casefold(), r["translation"].casefold()) for r in existing}
        in_file = set()
        rows = []
        for cells in reader:
            if not any(c.strip() for c in cells):
                continue
            if len(rows) >= MAX_ROWS:
                return _("Too many rows (max {n}). Split the file.", n=MAX_ROWS), []
            data = {f: cells[idx[f]].strip() if f in idx and idx[f] < len(cells) else "" for f in FIELDS}
            problems = [_("{field} is empty", field=f) for f in REQUIRED if not data[f]]
            problems += [_("{field} is longer than {n} characters", field=f, n=MAX_LEN) for f in FIELDS if len(data[f]) > MAX_LEN]
            key = (data["phrase"].casefold(), data["translation"].casefold())
            if not problems and key in in_db:
                problems.append(_("already in the database"))
            elif not problems and key in in_file:
                problems.append(_("duplicate of an earlier row"))
            in_file.add(key)
            rows.append({"line": reader.line_num, "data": data, "problems": problems})
    except csv.Error as e:
        return _("Broken CSV near line {n}: {e}", n=reader.line_num, e=e), []
    if not rows:
        return _("No data rows found below the header."), []
    return "", rows
