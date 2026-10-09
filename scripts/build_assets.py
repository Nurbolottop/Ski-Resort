"""Сборка фронтенда: style.css + glass.css → site.min.css, *.js → *.min.js.

Запускать после любой правки CSS/JS и коммитить результат:
    pip install rcssmin rjsmin
    python scripts/build_assets.py
"""
from pathlib import Path

import rcssmin
import rjsmin

STATIC = Path(__file__).resolve().parent.parent / 'app' / 'static'

CSS_BUNDLE = ['css/style.css', 'css/glass.css']
JS_FILES = ['js/main.js', 'js/snow.js']


def write(rel, text, source_size):
    path = STATIC / rel
    path.write_text(text, encoding='utf-8', newline='\n')
    print(f'{rel}: {source_size // 1024} KB -> {len(text.encode()) // 1024} KB')


css = '\n'.join((STATIC / f).read_text(encoding='utf-8') for f in CSS_BUNDLE)
write('css/site.min.css', rcssmin.cssmin(css), len(css.encode()))

for f in JS_FILES:
    js = (STATIC / f).read_text(encoding='utf-8')
    write(f.replace('.js', '.min.js'), rjsmin.jsmin(js), len(js.encode()))
