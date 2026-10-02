"""Собирает весь сайт в один файл (страницы переключаются по #якорю).
Запуск:
  python tools/build_demo.py                                   -> demo/site.html (js/config.js)
  python tools/build_demo.py --config examples/grooming.config.js demo/grooming.html
  --artifact  — без <!doctype>/<head> (для публикации как артефакт)"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGES = ["home", "services", "storage", "gallery", "contacts"]


def build(with_doctype: bool = True, config: Path | None = None) -> str:
    css = (ROOT / "css/style.css").read_text(encoding="utf-8")
    cfg = (config or ROOT / "js/config.js").read_text(encoding="utf-8")
    main = (ROOT / "js/main.js").read_text(encoding="utf-8")
    import re
    title = re.search(r'name:\s*"((?:[^"\\]|\\.)*)"', cfg).group(1)
    mains = "\n".join(f'<main data-page="{p}"></main>' for p in PAGES)
    body = f"""<title>{title}</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Manrope:wght@400;600;700&family=Russo+One&family=Comfortaa:wght@600;700&display=swap">
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
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("out", nargs="?", default=str(ROOT / "demo/site.html"))
    ap.add_argument("--config", help="другой файл конфигурации, например examples/grooming.config.js")
    ap.add_argument("--artifact", action="store_true")
    a = ap.parse_args()
    cfg = Path(a.config) if a.config else None
    if cfg and not cfg.is_absolute():
        cfg = ROOT / cfg
    Path(a.out).write_text(build(with_doctype=not a.artifact, config=cfg), encoding="utf-8")
    print("written", a.out)
