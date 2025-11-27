# app.py (добавлена поддержка dots_only)
# app.py (добавлена поддержка изменения сетки)
#⚙️app.py с встроенным JavaScript для динамического пересчёта при изменении высоты букв;
#🧾и с пояснением под шагом вертикальных линий (по ГОСТ).

# ================================================================
#  app.py — Flask-приложение для генерации титульных листов по ГОСТ
# ================================================================
#  Реализовано:
#   ✅ Генерация PDF и PNG с ГОСТ-сеткой и шрифтом
#   ✅ Динамический расчёт толщины линий шрифта (font_size / 14)
#   ✅ Выбор шрифта из папки fonts/
#   ✅ Загрузка текста из .txt или textarea
#   ✅ Переключение ГОСТ/Классическая сетка
#   ✅ Показ сетки, букв, точек — в любых комбинациях
# ================================================================
#  Добавлено:
#   ✅ Опция "Стандартная толщина линий шрифта"
#   ✅ Возможность ручного задания толщины при снятой галочке
#   ✅ Автопересчёт шагов сетки при изменении font_size
#   ✅ Чекбокс "Использовать серую палитру" (0.6 / 0.4 / 0.6)
# ================================================================

from flask import Flask, render_template_string, request, send_file
import io
import os
from Font_on_TEMP5_to_GOST import TextRenderer, render_training_letter_images
import getpass
from datetime import datetime

# ------------------------------------------------
#  ИНИЦИАЛИЗАЦИЯ ПРИЛОЖЕНИЯ
# ------------------------------------------------
app = Flask(__name__)

# ------------------------------------------------
#  НАСТРОЙКИ
# ------------------------------------------------
# Папка со шрифтами (ищем относительно текущего файла)
BASE_DIR = os.path.dirname(__file__)
FONTS_DIR = os.path.join(BASE_DIR, "fonts")

# Доступные шрифты и подписи
# Названия шрифтов с человекочитаемыми подписями

FONT_LABELS = {
    "gost.ttf": "ГОСТ стандарт",
    "gost_0.ttf": "ГОСТ 0",
    "gost_au.ttf": "ГОСТ AU",
    "gost_bu.ttf": "ГОСТ BU",
    "gost_type_a.ttf": "ГОСТ тип A",
    "gost_type_a_italic.ttf": "ГОСТ тип A (наклонный)",
    "gost_type_b.ttf": "ГОСТ тип B",
    "gost_type_b_italic.ttf": "ГОСТ тип B (наклонный)"
}

# Собираем список шрифтов в папке fonts/
AVAILABLE_FONTS = sorted([
    f for f in os.listdir(FONTS_DIR)
    if f.lower().endswith((".ttf", ".otf"))
]) if os.path.isdir(FONTS_DIR) else []

# ------------------------------------------------
#  HTML-ФОРМА
# ------------------------------------------------

# Прямая вставка HTML с динамическим JavaScript для пересчёта толщины линий
HTML_FORM = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>ГОСТ титул</title>
  <style>
    body {
      font-family: Arial, sans-serif;
      margin: 30px;
      background-color: #f9f9f9;
    }
    form {
      background: #fff;
      padding: 20px;
      border: 1px solid #ccc;
      border-radius: 8px;
      max-width: 800px;
    }
    label {
      font-weight: bold;
    }
    input[type="text"], input[type="number"], input[type="file"], textarea, select {
      width: 100%;
      padding: 6px;
      margin-top: 5px;
      margin-bottom: 8px;
      border: 1px solid #ccc;
      border-radius: 4px;
      box-sizing: border-box;
    }
    input[type="submit"] {
      padding: 10px 18px;
      background-color: #4682B4;
      color: white;
      border: none;
      border-radius: 5px;
      cursor: pointer;
      margin-top: 10px;
    }
    input[type="submit"]:hover {
      background-color: #4169E1;
    }
    a {
      display: inline-block;
      margin-right: 15px;
      margin-top: 10px;
      color: #4B0082;
      text-decoration: none;
    }
    a:hover {
      text-decoration: underline;
    }
  </style>
</head>
<body>
  <h2 style="color: #FF9800;">Тест-тренажер написания шрифта</h2>
  <form method="post" enctype="multipart/form-data">

    <label>Интервал между словами (мм):</label>
    <input type="number" name="spacing" value="4.2" step="0.1">

    <label>Высота прописных букв, h (мм):</label>
    <input type="number" name="font_size" id="font_size" value="10" step="0.1">

    <input type="checkbox" id="auto_line_width" name="auto_line_width" checked>
    Стандартная толщина линий шрифта, d (мм), тип А d=1/14h

    <label>Толщина линий шрифта (мм):</label>
    <input type="number" id="line_width" name="line_width" value="0.7" step="0.1">

    <label>Шаг горизонтальных линий (мм):</label>
    <input type="number" id="thin_step_h" name="thin_step_h" value="1.4" step="0.1">

    <label>Шаг вертикальных линий (мм):</label>
    <input type="number" id="thin_step_v" name="thin_step_v" value="1.4" step="0.1">
    <span style="font-size: 0.8em; font-style: italic;">
    По стандарту шаг вертикальных линий равен шагу горизонтальных линий и равен толщине линий шрифта.
    </span><br><br>

    <b>Цвета элементов:</b><br>

    <label for="frame_color">Цвет рамки:</label>
    <select name="frame_color" id="frame_color">
      <option value="#B3E5FC" selected>Light Sky Blue (#B3E5FC)</option>
      <option value="#AAAAAA">Gray (#AAAAAA)</option>
    </select>


    <label for="grid_color">Цвет сетки:</label>
    <select name="grid_color" id="grid_color">
      <option value="#81D4FA" selected>Sky Blue (#81D4FA)</option>
      <option value="whitesmoke">White Smoke (F5F5F5)</option>
      <option value="#CCCCCC">Light Gray (#CCCCCC)</option>
      <option value="#AAAAAA">closer to silver (#AAAAAA)</option>
      <option value="#999999">Gray (#999999)</option>
      <option value="#000000">Black (#000000)</option>
    </select>

    <label for="font_color">Цвет букв:</label>
    <select name="font_color" id="font_color">
      <option value="lightgray" selected>Light Gray (D3D3D3)</option>
      <option value="whitesmoke">White Smoke (F5F5F5)</option>
    </select>
    <input type="checkbox" id="use_gray" name="use_gray">
    <span style="font-size: 0.9em;">Использовать серую палитру</span><br><br>

    <input type="checkbox" name="show_grid" checked> Показать сетку<br>
    <input type="checkbox" name="show_font" checked> Показать буквы<br>
    <input type="checkbox" name="dots_only"> Только точки<br>
    <input type="checkbox" name="classic_grid"> Классическая сетка<br><br>

    <label>Выберите шрифт:</label>
    <select name="font_file">
      {% for f in fonts %}
          {% if f.lower() == "gost_type_a_italic.ttf" %}
              <option value="{{f}}" selected>{{ labels.get(f.lower(), f) }}</option>
          {% else %}
              <option value="{{f}}">{{ labels.get(f.lower(), f) }}</option>
          {% endif %}
      {% endfor %}
    </select>
    <p>
    <label>Введите текст ниже или выберите файл</label>
    <span style="font-size: 0.8em; color: #FF8C00; margin-left: 8px;">
            *Минимум строк и символов для Render, зависит от h
      </span>
    <p>
    <textarea name="text" rows="6" cols="60">Автор
Yakutsenak 2025</textarea>

    Загрузить текстовый файл (.txt):
    <input type="file" name="textfile">

    <input type="checkbox" name="training_real">
    <span style="font-size: 0.8em; color: #708090;">
      Режим обучения (символы кириллицы и латиницы из текста. Без знаков! см. gif)
    </span>


    <input type="submit" value="Сгенерировать gif(V), PDF, PNG и SVG">

    {% if generated %}
    #<p><a href="/download/gif">🎞️ Скачать training_images.gif</a></p>
      <p style="margin-top: 20px;">

      <div style="line-height: 0.4em;">

      <p><a href="/download/pdf">📄 Скачать PDF</a></p>
      <p><a href="/download/png">🖼️ Скачать PNG</a></p>
      <p>
      <a href="/download/svg">🧬 Скачать SVG</a>
      <span style="font-size: 0.8em; color: #FF8C00; margin-left: 8px;">
        *Функция не поддерживается на Render (малые инстансы, 512MB памяти)
      </span>
    </p>
    {% endif %}
  </form>

  <script>
    function updateLineWidth() {
        const fontSizeInput = document.getElementById("font_size");
        const lineWidthInput = document.getElementById("line_width");
        const autoCheckbox = document.getElementById("auto_line_width");
        const stepH = document.getElementById("thin_step_h");
        const stepV = document.getElementById("thin_step_v");
        const fontSize = parseFloat(fontSizeInput.value);

        if (autoCheckbox.checked && !isNaN(fontSize)) {
            const lw = (fontSize / 14).toFixed(1);
            lineWidthInput.value = lw;
            if (stepH) stepH.value = lw;
            if (stepV) stepV.value = lw;
            lineWidthInput.readOnly = true;
            lineWidthInput.style.background = "#f4f4f4";
        } else {
            lineWidthInput.readOnly = false;
            lineWidthInput.style.background = "white";
        }
    }

    document.getElementById("use_gray").addEventListener("change", function() {
        const grayMode = this.checked;
        document.getElementById("frame_color").value = grayMode ? "0.6" : "#B3E5FC";
        document.getElementById("grid_color").value = grayMode ? "0.4" : "#81D4FA";
        document.getElementById("font_color").value = grayMode ? "0.6" : "lightgray";
    });

    document.addEventListener("DOMContentLoaded", updateLineWidth);
    document.getElementById("font_size").addEventListener("input", updateLineWidth);
    document.getElementById("auto_line_width").addEventListener("change", updateLineWidth);
  </script>
</body>
</html>
"""

# ------------------------------------------------
#  ОСНОВНОЙ МАРШРУТ
# ------------------------------------------------
@app.route("/", methods=["GET", "POST"])
def index():
    """
    Основной маршрут: обрабатывает форму, создаёт PDF и PNG.
    """
    global generated_pdf, generated_png, generated_svg
    generated = False

    if request.method == "POST":
        # --- 1. Текст: приоритет — файл .txt ---
        lines = []
        if "textfile" in request.files:
            file = request.files["textfile"]
            if file and file.filename.lower().endswith(".txt"):
                try:
                    content = file.read().decode("utf-8")
                except UnicodeDecodeError:
                    content = file.read().decode("cp1251", errors="ignore")
                lines = [ln.strip() for ln in content.splitlines() if ln.strip()]
        # Если файла нет — берём текст из textarea       
        if not lines:
            text = request.form.get("text", "")
            lines = [ln.strip() for ln in text.splitlines() if ln.strip()]

        # --- 2. Чтение числовых параметров ---
        def _f(name, default):
            try:
                return float(request.form.get(name, default))
            except (TypeError, ValueError):
                return default

        font_size_str = request.form.get("font_size", "10").strip()
        spacing_str = request.form.get("spacing", "").strip()

        try:
            font_size = float(font_size_str)
        except ValueError:
            font_size = 10.0

        if spacing_str:
            try:
                spacing = float(spacing_str)
            except ValueError:
                spacing = font_size * 0.42
        else:
            spacing = font_size * 0.42
        thin_step_h = _f("thin_step_h", round(font_size / 14.0, 1))
        thin_step_v = _f("thin_step_v", round(font_size / 14.0, 1))

        # --- Толщина линий (новая логика) ---
        auto_line_width = "auto_line_width" in request.form
        if auto_line_width:
            line_width = round(font_size / 14.0, 1)
        else:
            line_width = _f("line_width", round(font_size / 14.0, 1))

        # --- 3. Цвета и флаги ---
        frame_color = request.form.get("frame_color", "#B3E5FC")
        grid_color  = request.form.get("grid_color",  "#81D4FA")
        font_color  = request.form.get("font_color",  "lightgray")

        show_grid    = "show_grid" in request.form
        show_font    = "show_font" in request.form
        dots_only    = "dots_only" in request.form
        classic_grid = "classic_grid" in request.form

        # --- Выбор шрифта ---
        font_file = request.form.get("font_file", "gost_type_a_italic.ttf")

        # Если имя шрифта не из списка доступных — сбрасываем на дефолт
        if font_file not in AVAILABLE_FONTS:
            font_file = "gost_type_a_italic.ttf"

        font_path = os.path.join(FONTS_DIR, font_file)

        # Проверка: файл реально существует на сервере (на случай ошибок деплоя)
        if not os.path.isfile(font_path):
            return "❌ Ошибка: файл шрифта не найден на сервере. Проверь папку fonts/ и Git.", 400

        font_file = request.form.get("font_file", "gost_type_a_italic.ttf")
        if not font_file or font_file not in AVAILABLE_FONTS:
            font_file = "gost_type_a_italic.ttf"
        font_path = os.path.join(FONTS_DIR, font_file)
        
        # --- Режим обучения (реальные символы) — создаёт training_real.gif ---
        if "training_real" in request.form:
            try:
                from Font_on_TEMP5_to_GOST import render_training_letter_images
                output_dir = request.form.get("output_dir")
                if not output_dir or output_dir.strip() == "":
                    from datetime import datetime
                    import getpass
                    username = getpass.getuser()
                    date_str = datetime.now().strftime("%Y-%m-%d")
                    output_dir = f"output_{date_str}_{username}" # Выбор папки для GIF анимации

                os.makedirs(output_dir, exist_ok=True)

                gif_path = os.path.join(output_dir, "training_images.gif")
                render_training_letter_images(lines, save_path=gif_path)

                print(f"✅ training_images.gif сохранён в: {gif_path}")

                print("✅ training_images.gif сохранён (по PNG)")
                
            except Exception as e:
                print("⚠️ Ошибка при создании training_real.gif:", e)


                # --- Рендер ---
        renderer = TextRenderer(
            font_path=font_path,
            spacing=spacing,
            font_size=font_size,
            frame_color=frame_color,
            grid_color=grid_color,
            font_color=font_color,
            line_width=line_width
        )

        fig = renderer.render_to_figure(
            lines,
            show_grid=show_grid,
            show_font=show_font,
            dots_only=dots_only,
            classic_grid=classic_grid,
            thin_step_h=thin_step_h,
            thin_step_v=thin_step_v
        )

        # Генерация SVG
        #svg_buffer = io.BytesIO()
        #fig.savefig(svg_buffer, format="svg", bbox_inches="tight")
        #svg_buffer.seek(0)
        #generated_svg = svg_buffer
        generated_svg = None

        # --- Сохранение PDF и PNG в память ---
        buf_pdf, buf_png = io.BytesIO(), io.BytesIO()
        fig.savefig(buf_pdf, format="pdf", bbox_inches="tight")
        fig.savefig(buf_png, format="png", dpi=300, bbox_inches="tight")
        buf_pdf.seek(0), buf_png.seek(0)

        # Сохраняем буферы в глобальные переменные (для скачивания)
        global generated_pdf, generated_png
        generated_pdf, generated_png = buf_pdf, buf_png
        generated = True

    return render_template_string(HTML_FORM,
                                  generated=generated,
                                  fonts=AVAILABLE_FONTS,
                                  labels=FONT_LABELS)

# ------------------------------------------------
#  СКАЧИВАНИЕ PDF / PNG
# ------------------------------------------------
@app.route("/download/pdf")
def download_pdf():
    """
    Возвращает PDF. Создаёт новый поток из сохранённого содержимого,
    чтобы избежать ошибки "I/O operation on closed file" при повторном скачивании.
    """
    global generated_pdf
    if generated_pdf:
        try:
            # Считываем данные из потока (даже если он закрыт)
            data = generated_pdf.getvalue()
        except ValueError:
            # Если поток уже закрыт Flask'ом — просто игнорируем
            data = b""
        # Создаём новый BytesIO для отправки клиенту
        buffer_copy = io.BytesIO(data)
        buffer_copy.seek(0)
        return send_file(buffer_copy,
                         as_attachment=True,
                         download_name="gost_titul.pdf",
                         mimetype="application/pdf")
    return "PDF не создан"


@app.route("/download/png")
def download_png():
    """
    Возвращает PNG. Создаёт новый поток из сохранённого содержимого,
    чтобы избежать ошибки "I/O operation on closed file" при повторном скачивании.
    """
    global generated_png
    if generated_png:
        try:
            data = generated_png.getvalue()
        except ValueError:
            data = b""
        buffer_copy = io.BytesIO(data)
        buffer_copy.seek(0)
        return send_file(buffer_copy,
                         as_attachment=True,
                         download_name="gost_titul.png",
                         mimetype="image/png")
    return "PNG не создан"

@app.route("/download/svg")
def download_svg():
    global generated_svg
    if not generated_svg:
        return "SVG не сгенерирован", 404
    return send_file(generated_svg, mimetype="image/svg+xml", as_attachment=True, download_name="gost_output.svg")    


# ------------------------------------------------
#  ЗАПУСК
# ------------------------------------------------

@app.route("/download/gif")
def download_gif():
    import os, glob
    from flask import send_file
    from datetime import datetime

    date_str = datetime.now().strftime('%Y-%m-%d')
    folders = glob.glob(f"output_{date_str}_*")
    if folders:
        output_dir = folders[0]
        gif_path = os.path.join(output_dir, "training_images.gif")
        if os.path.exists(gif_path):
            return send_file(gif_path,
                             as_attachment=True,
                             download_name="training_images.gif",
                             mimetype="image/gif")
    return "GIF не найден", 404


if __name__ == "__main__":
    """
    Запуск Flask-приложения локально.
    Хост 0.0.0.0 — доступ с других устройств в сети.
    """
    app.run(host="0.0.0.0", port=5000, debug=True)
