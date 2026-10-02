#!/bin/sh
# Собирает webapp/index.html (для хостинга мини-приложения) из demo.html
cd "$(dirname "$0")"
{
  printf '<!doctype html>\n<html lang="ru"><head><meta charset="utf-8">\n'
  printf '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
  printf '<script src="https://telegram.org/js/telegram-web-app.js"></script>\n'
  sed -n '1,/<\/style>/p' demo.html | grep -v -e '^<!doctype' -e '^<meta charset' -e '^<meta name="viewport"'
  printf '</head><body>\n'
  sed '1,/<\/style>/d' demo.html
  printf '</body></html>\n'
} > webapp/index.html
