#!/usr/bin/env python3
"""สร้าง voices.js: ไฟล์เสียงอ่านตัวอักษรและคำศัพท์ทั้งหมดของเกม (ฝังเป็น base64)

เกมจะใช้เสียงจากไฟล์นี้ก่อน จึงมีเสียงอ่านได้ทุกเครื่องแม้ไม่มีเสียงสังเคราะห์ภาษาไทย
รันใหม่ทุกครั้งที่แก้ TH_NAME หรือ WORDS ใน index.html:  python3 make-voices.py
ต้องใช้ macOS (คำสั่ง say) และ ffmpeg
"""
import base64, json, pathlib, re, subprocess, tempfile

HERE = pathlib.Path(__file__).parent
VOICE = {'th': ('Kanya', 150), 'en': ('Samantha', 150)}  # (เสียง, ความเร็วคำต่อนาที)

src = (HERE / 'index.html').read_text(encoding='utf-8')

def block(start, end):
    i = src.index(start)
    return src[i:src.index(end, i)]

texts = {'th': set(), 'en': set()}
texts['th'].update(re.findall(r"'[^']+': '([^']+)'", block('const TH_NAME = {', '};')))
words = block('const WORDS = {', '\n};')
th_at = words.index('th: {')
for lang, part in (('en', words[:th_at]), ('th', words[th_at:])):
    texts[lang].update(re.findall(r"\['([^']+)','[^']*'\]", part))
texts['en'].update('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
texts['th'].add('กอ ไก่ สระ อา ไม้เอก')  # ปุ่มทดสอบเสียง

out = {}
with tempfile.TemporaryDirectory() as tmp:
    aiff, mp3 = f'{tmp}/a.aiff', f'{tmp}/a.mp3'
    for lang, items in texts.items():
        voice, rate = VOICE[lang]
        for text in sorted(items):
            # ตัวอักษรอังกฤษตัวเดียวใส่จุดต่อท้าย ไม่งั้น "A" ถูกอ่านเป็นคำนำหน้านาม
            spoken = text + '.' if lang == 'en' and len(text) == 1 else text.lower() if lang == 'en' else text
            subprocess.run(['say', '-v', voice, '-r', str(rate), '-o', aiff, spoken], check=True)
            subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', aiff, '-ac', '1', '-ar', '22050',
                            '-b:a', '32k', mp3], check=True)
            out[f'{lang}:{text}'] = base64.b64encode(pathlib.Path(mp3).read_bytes()).decode()

js = '// สร้างโดย make-voices.py ห้ามแก้มือ\nwindow.VOICES = ' + json.dumps(out, ensure_ascii=False, separators=(',', ':')) + ';\n'
(HERE / 'voices.js').write_text(js, encoding='utf-8')
print(f'{len(out)} clips, {len(js) / 1024:.0f} KB')
