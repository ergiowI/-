"""Собирает весь сайт в один файл demo/site.html (страницы переключаются по #якорю).
Запуск: python tools/build_demo.py"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGES = ["home", "services", "storage", "gallery", "contacts"]


def build(with_doctype: bool = True) -> str:
    css = (ROOT / "css/style.css").read_text(encoding="utf-8")
    cfg = (ROOT / "js/config.js").read_text(encoding="utf-8")
    main = (ROOT / "js/main.js").read_text(encoding="utf-8")
    mains = "\n".join(f'<main data-page="{p}"></main>' for p in PAGES)
    body = f"""<title>Шиномонтаж на Ветеранов</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Manrope:wght@400;600;700&family=Russo+One&display=swap">
<style>
{css}
</style>
<div id="site-header"></div>
{mains}
<div id="site-footer"></div>
<script>window.SINGLE_FILE = true;</script>
<script>
{cfg}
</script>
<script>
{main}
</script>
"""
    if not with_doctype:
        return body
    return ('<!doctype html>\n<html lang="ru">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
            '</head>\n<body>\n' + body + "</body>\n</html>\n")


if __name__ == "__main__":
    import sys
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "demo/site.html"
    out.write_text(build(with_doctype="--artifact" not in sys.argv), encoding="utf-8")
    print("written", out)
