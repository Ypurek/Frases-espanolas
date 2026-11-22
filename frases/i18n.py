LANGS = {"uk": "УКР", "es": "ES", "en": "EN"}
DEFAULT = "uk"

# English text is the key; missing entries fall back to English.
T = {
    # layout
    "Toggle light/dark mode": ("Світла/темна тема", "Tema claro/oscuro"),
    "Admin": ("Адмін", "Admin"),
    "Language": ("Мова", "Idioma"),
    "Cookie policy": ("Політика cookies", "Política de cookies"),
    "We use cookies to remember the phrases you have already played, your win streak, theme and language. No tracking, no ads.": (
        "Ми використовуємо cookies, щоб пам'ятати зіграні фрази, вашу серію перемог, тему та мову. Без стеження й реклами.",
        "Usamos cookies para recordar las frases que ya has jugado, tu racha de aciertos, el tema y el idioma. Sin rastreo ni anuncios."),
    "Accept": ("Прийняти", "Aceptar"),
    "Decline": ("Відхилити", "Rechazar"),
    "Menu": ("Меню", "Menú"),
    "Skip the example after a correct answer": ("Пропускати приклад після правильної відповіді",
                                                "Saltar el ejemplo tras una respuesta correcta"),
    "Cancel": ("Скасувати", "Cancelar"),
    # menu
    "Learn Spanish phrases": ("Вивчай іспанські фрази", "Aprende frases en español"),
    "Play": ("Грати", "Jugar"),
    "Phrases": ("Фрази", "Frases"),
    "Browse & search all phrases": ("Переглянути й шукати фрази", "Ver y buscar todas las frases"),
    "Suggest a phrase": ("Запропонувати фразу", "Proponer una frase"),
    "Download all phrases (CSV)": ("Завантажити всі фрази (CSV)", "Descargar todas las frases (CSV)"),
    "Add a phrase": ("Додати фразу", "Añadir una frase"),
    "Review suggestions": ("Переглянути пропозиції", "Revisar propuestas"),
    "Edit / delete phrases": ("Редагувати / видалити фрази", "Editar / borrar frases"),
    "Import phrases (CSV)": ("Імпорт фраз (CSV)", "Importar frases (CSV)"),
    "Log out": ("Вийти", "Cerrar sesión"),
    "Admin secret key": ("Секретний ключ адміна", "Clave secreta de admin"),
    "Log in": ("Увійти", "Entrar"),
    "Wrong key.": ("Невірний ключ.", "Clave incorrecta."),
    # games
    "True or false": ("Правда чи ні", "Verdadero o falso"),
    "Pick: Spanish → Ukrainian": ("Вибір: іспанська → українська", "Elige: español → ucraniano"),
    "Pick: Ukrainian → Spanish": ("Вибір: українська → іспанська", "Elige: ucraniano → español"),
    "Need at least {n} phrases for this game.": ("Для цієї гри потрібно щонайменше {n} фрази.",
                                                  "Se necesitan al menos {n} frases para este juego."),
    "Win streak": ("Серія перемог", "Racha de aciertos"),
    "Is this translation correct?": ("Чи правильний цей переклад?", "¿Es correcta esta traducción?"),
    "True": ("Правда", "Verdadero"),
    "False": ("Неправда", "Falso"),
    "Correct! ¡Muy bien!": ("Правильно! ¡Muy bien!", "¡Correcto! ¡Muy bien!"),
    "Not quite": ("Не зовсім", "No exactamente"),
    "You picked: {x}": ("Ви вибрали: {x}", "Elegiste: {x}"),
    "“{a}” means “{b}”": ("«{a}» означає «{b}»", "«{a}» significa «{b}»"),
    "Best streak: {n}": ("Найкраща серія: {n}", "Mejor racha: {n}"),
    "Next": ("Далі", "Siguiente"),
    # phrase list
    "All phrases": ("Усі фрази", "Todas las frases"),
    "Search Spanish or Ukrainian": ("Пошук іспанською чи українською", "Buscar en español o ucraniano"),
    "Search": ("Шукати", "Buscar"),
    "Phrases: {n}": ("Кількість фраз: {n}", "Frases: {n}"),
    "No notes yet.": ("Приміток ще немає.", "Aún no hay notas."),
    "Edit / delete": ("Редагувати / видалити", "Editar / borrar"),
    "Nothing found.": ("Нічого не знайдено.", "No se encontró nada."),
    # phrase form
    "Spanish phrase": ("Фраза іспанською", "Frase en español"),
    "Ukrainian translation": ("Переклад українською", "Traducción al ucraniano"),
    "Note / description": ("Примітка / опис", "Nota / descripción"),
    "Example": ("Приклад", "Ejemplo"),
    "Send suggestion": ("Надіслати пропозицію", "Enviar propuesta"),
    "Thanks! Your phrase is waiting for approval.": ("Дякуємо! Ваша фраза чекає на схвалення.",
                                                     "¡Gracias! Tu frase está pendiente de aprobación."),
    # admin
    "Phrases in the database: {n}.": ("Фраз у базі: {n}.", "Frases en la base de datos: {n}."),
    "To edit or delete a phrase, expand it in": ("Щоб редагувати чи видалити фразу, розгорніть її в розділі",
                                                 "Para editar o borrar una frase, ábrela en"),
    "Not added yet: similar phrases already exist.": ("Ще не додано: схожі фрази вже є.",
                                                      "Aún no se ha añadido: ya existen frases parecidas."),
    "Similar phrases already exist:": ("Схожі фрази вже є:", "Ya existen frases parecidas:"),
    "distance": ("відстань", "distancia"),
    "Add anyway": ("Все одно додати", "Añadir de todos modos"),
    "Add phrase": ("Додати фразу", "Añadir frase"),
    "Suggestions": ("Пропозиції", "Propuestas"),
    "Phrase": ("Фраза", "Frase"),
    "Translation": ("Переклад", "Traducción"),
    "Similar in database": ("Схожі в базі", "Parecidas en la base"),
    "Actions": ("Дії", "Acciones"),
    "Approve": ("Схвалити", "Aprobar"),
    "Edit": ("Редагувати", "Editar"),
    "Reject": ("Відхилити", "Rechazar"),
    "No pending suggestions.": ("Нових пропозицій немає.", "No hay propuestas pendientes."),
    "Review suggestion": ("Перегляд пропозиції", "Revisar propuesta"),
    "Phrase and translation are required.": ("Фраза й переклад обов'язкові.",
                                             "La frase y la traducción son obligatorias."),
    "Phrase added.": ("Фразу додано.", "Frase añadida."),
    "Approved.": ("Схвалено.", "Aprobada."),
    "Rejected.": ("Відхилено.", "Rechazada."),
    "Edit phrase": ("Редагувати фразу", "Editar frase"),
    "Save": ("Зберегти", "Guardar"),
    "Delete": ("Видалити", "Borrar"),
    "Delete this phrase? This cannot be undone.": ("Видалити цю фразу? Це не можна скасувати.",
                                                   "¿Borrar esta frase? No se puede deshacer."),
    # import
    "Import only adds phrases. Nothing already in the database is changed or removed.": (
        "Імпорт лише додає фрази. Те, що вже є в базі, не змінюється й не видаляється.",
        "La importación solo añade frases. No se cambia ni se borra nada de lo que ya hay en la base de datos."),
    "The file must be UTF-8 CSV (comma, semicolon or tab separated) and the first row must hold the column names:": (
        "Файл має бути CSV у кодуванні UTF-8 (роздільник — кома, крапка з комою або табуляція), а в першому рядку — назви колонок:",
        "El archivo debe ser CSV en UTF-8 (separado por comas, punto y coma o tabulaciones) y la primera fila debe contener los nombres de las columnas:"),
    "phrase and translation are required. A row is skipped if that exact phrase + translation already exists.": (
        "phrase і translation обов'язкові. Рядок пропускається, якщо така сама фраза з таким самим перекладом уже є.",
        "phrase y translation son obligatorias. Se omite una fila si ya existe exactamente la misma frase con la misma traducción."),
    "Download the current phrases (CSV) to use as a template.": (
        "Завантажте поточні фрази (CSV), щоб використати їх як шаблон.",
        "Descarga las frases actuales (CSV) para usarlas como plantilla."),
    "CSV file": ("CSV-файл", "Archivo CSV"),
    "Check file": ("Перевірити файл", "Comprobar archivo"),
    "File: {name}": ("Файл: {name}", "Archivo: {name}"),
    "Can't import this file:": ("Не вдається імпортувати цей файл:", "No se puede importar este archivo:"),
    "Will be added: {n}. Skipped: {m}.": ("Буде додано: {n}. Пропущено: {m}.", "Se añadirán: {n}. Omitidas: {m}."),
    "Import ({n})": ("Імпортувати ({n})", "Importar ({n})"),
    "Nothing to import.": ("Нічого імпортувати.", "No hay nada que importar."),
    "Skipped rows": ("Пропущені рядки", "Filas omitidas"),
    "Will be added": ("Буде додано", "Se añadirán"),
    "Line": ("Рядок", "Línea"),
    "Why": ("Причина", "Motivo"),
    "Choose another file": ("Вибрати інший файл", "Elegir otro archivo"),
    "This preview expired. Upload the file again.": ("Попередній перегляд застарів. Завантажте файл ще раз.",
                                                     "La vista previa ha caducado. Sube el archivo de nuevo."),
    "Imported: {n}.": ("Імпортовано: {n}.", "Importadas: {n}."),
    # CSV validation
    "File is larger than 2 MB.": ("Файл більший за 2 МБ.", "El archivo supera los 2 MB."),
    "File must be UTF-8 encoded (in Excel: Save As → “CSV UTF-8”).": (
        "Файл має бути в кодуванні UTF-8 (в Excel: Зберегти як → «CSV UTF-8»).",
        "El archivo debe estar en UTF-8 (en Excel: Guardar como → «CSV UTF-8»)."),
    "File is empty.": ("Файл порожній.", "El archivo está vacío."),
    "Missing column(s): {cols}. First row must be: {fields}.": (
        "Бракує колонок: {cols}. Перший рядок має бути: {fields}.",
        "Faltan columnas: {cols}. La primera fila debe ser: {fields}."),
    "Too many rows (max {n}). Split the file.": ("Забагато рядків (максимум {n}). Розділіть файл.",
                                                 "Demasiadas filas (máximo {n}). Divide el archivo."),
    "{field} is empty": ("{field}: порожньо", "{field}: vacío"),
    "{field} is longer than {n} characters": ("{field}: довше за {n} символів", "{field}: más de {n} caracteres"),
    "already in the database": ("вже є в базі", "ya está en la base de datos"),
    "duplicate of an earlier row": ("повторює попередній рядок", "repite una fila anterior"),
    "Broken CSV near line {n}: {e}": ("Пошкоджений CSV біля рядка {n}: {e}", "CSV dañado cerca de la línea {n}: {e}"),
    "No data rows found below the header.": ("Під заголовком немає рядків із даними.",
                                             "No hay filas de datos debajo del encabezado."),
}
_COL = {"uk": 0, "es": 1}


def pick_lang(req):
    lang = req.cookies.get("lang")
    if lang in LANGS:
        return lang
    for part in req.headers.get("accept-language", "").split(","):
        code = part.split(";")[0].strip()[:2].lower()
        if code in LANGS:
            return code
    return DEFAULT


def translator(lang):
    def _(text, **kw):
        if lang in _COL and text in T:
            text = T[text][_COL[lang]]
        return text.format(**kw) if kw else text
    return _

