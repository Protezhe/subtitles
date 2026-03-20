#!/usr/bin/env python3
"""Генерирует HTML-плеер субтитров из .srt файла."""

import json
import re
import sys


def parse_srt(text: str) -> list[dict]:
    blocks = re.split(r"\n\n+", text.strip().replace("\r\n", "\n"))
    subs = []
    for block in blocks:
        lines = block.split("\n")
        if len(lines) < 3:
            continue
        m = re.match(
            r"(\d{2}):(\d{2}):(\d{2}),(\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2}),(\d{3})",
            lines[1],
        )
        if not m:
            continue
        g = [int(x) for x in m.groups()]
        start = (g[0] * 3600 + g[1] * 60 + g[2]) * 1000 + g[3]
        end = (g[4] * 3600 + g[5] * 60 + g[6]) * 1000 + g[7]
        text_content = "\n".join(lines[2:]).strip()
        subs.append({"start": start, "end": end, "text": text_content})
    subs.sort(key=lambda s: s["start"])
    return subs


HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<title>Subtitle Player</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    background: #000; color: #fff;
    font-family: 'Helvetica Neue', Arial, sans-serif;
    height: 100vh; display: flex; flex-direction: column;
    justify-content: flex-end; align-items: center;
    overflow: hidden; cursor: none; user-select: none;
  }}
  #subtitle-area {{
    width: 100%; text-align: center;
    padding: 40px 60px 80px; min-height: 200px;
    display: flex; flex-direction: column;
    justify-content: flex-end; align-items: center;
  }}
  #subtitle-text {{
    font-size: 42px; font-weight: 400; line-height: 1.4;
    text-shadow: 2px 2px 8px rgba(0,0,0,0.9);
    max-width: 90%; transition: opacity 0.2s ease;
  }}
  #subtitle-text.fade {{ opacity: 0; }}
  #timer {{
    position: fixed; top: 20px; right: 30px;
    font-size: 18px; color: #444;
    font-variant-numeric: tabular-nums;
  }}
  #status {{
    position: fixed; top: 20px; left: 30px;
    font-size: 16px; color: #444;
  }}
  #progress {{
    position: fixed; bottom: 0; left: 0; height: 3px;
    background: #555; transition: width 0.3s linear;
  }}
  #counter {{
    position: fixed; bottom: 15px; right: 30px;
    font-size: 14px; color: #333;
  }}
  #help {{
    position: fixed; bottom: 15px; left: 30px;
    font-size: 12px; color: #222;
  }}
</style>
</head>
<body>
<div id="subtitle-area"><div id="subtitle-text"></div></div>
<div id="timer">00:00:00</div>
<div id="status">PAUSED</div>
<div id="progress"></div>
<div id="counter"></div>
<div id="help">Space=play/pause &nbsp; ←→=prev/next &nbsp; PageUp/Down=clicker &nbsp; F=fullscreen</div>
<script>
const subtitles = {subs_json};

let currentIndex = -1, isPlaying = false, startTime = 0, elapsed = 0, timerInterval = null;
const subtitleText = document.getElementById('subtitle-text');
const timerEl = document.getElementById('timer');
const statusEl = document.getElementById('status');
const progressEl = document.getElementById('progress');
const counterEl = document.getElementById('counter');
const totalMs = subtitles.length ? subtitles[subtitles.length - 1].end : 1;

function fmt(ms) {{
  const s = Math.floor(ms / 1000);
  return [s / 3600 | 0, (s % 3600) / 60 | 0, s % 60].map(v => String(v).padStart(2, '0')).join(':');
}}

function updateCounter() {{
  counterEl.textContent = (currentIndex >= 0 ? (currentIndex + 1) : '—') + ' / ' + subtitles.length;
}}
updateCounter();

function showSub(i) {{
  subtitleText.classList.add('fade');
  setTimeout(() => {{ subtitleText.textContent = subtitles[i].text; subtitleText.classList.remove('fade'); }}, 100);
}}

function tick() {{
  const ms = elapsed + (Date.now() - startTime);
  timerEl.textContent = fmt(ms);
  let found = -1;
  for (let i = 0; i < subtitles.length; i++) {{
    if (ms >= subtitles[i].start && ms < subtitles[i].end) {{ found = i; break; }}
  }}
  if (found >= 0 && found !== currentIndex) {{
    currentIndex = found; showSub(currentIndex); updateCounter();
  }} else if (found < 0 && currentIndex >= 0 && ms >= subtitles[currentIndex].end) {{
    subtitleText.textContent = '';
  }}
  progressEl.style.width = Math.min(100, ms / totalMs * 100) + '%';
}}

function togglePlay() {{
  if (isPlaying) {{
    elapsed += Date.now() - startTime;
    isPlaying = false; clearInterval(timerInterval);
    statusEl.textContent = 'PAUSED';
  }} else {{
    startTime = Date.now(); isPlaying = true;
    statusEl.textContent = '▶ PLAYING';
    timerInterval = setInterval(tick, 50);
  }}
}}

function goTo(i) {{
  i = Math.max(0, Math.min(subtitles.length - 1, i));
  const wasPlaying = isPlaying;
  if (isPlaying) clearInterval(timerInterval);
  currentIndex = i; elapsed = subtitles[i].start;
  showSub(i); updateCounter(); timerEl.textContent = fmt(elapsed);
  if (wasPlaying) {{ startTime = Date.now(); timerInterval = setInterval(tick, 50); }}
}}

document.addEventListener('keydown', e => {{
  switch (e.code) {{
    case 'Space': case 'F5': e.preventDefault(); togglePlay(); break;
    case 'ArrowRight': case 'PageDown': case 'KeyN': e.preventDefault(); goTo(currentIndex + 1); break;
    case 'ArrowLeft': case 'PageUp': case 'KeyP': e.preventDefault(); goTo(currentIndex <= 0 ? 0 : currentIndex - 1); break;
    case 'KeyF': e.preventDefault();
      document.fullscreenElement ? document.exitFullscreen() : document.documentElement.requestFullscreen();
      break;
  }}
}});

let ct; document.addEventListener('mousemove', () => {{
  document.body.style.cursor = 'default'; clearTimeout(ct);
  ct = setTimeout(() => document.body.style.cursor = 'none', 2000);
}});
</script>
</body>
</html>
"""


def main():
    if len(sys.argv) < 2:
        print(f"Usage: python {sys.argv[0]} <file.srt> [output.html]")
        sys.exit(1)

    srt_path = sys.argv[1]
    out_path = sys.argv[2] if len(sys.argv) > 2 else srt_path.rsplit(".", 1)[0] + "_player.html"

    with open(srt_path, encoding="utf-8") as f:
        subs = parse_srt(f.read())

    html = HTML_TEMPLATE.format(subs_json=json.dumps(subs, ensure_ascii=False))

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Generated: {out_path} ({len(subs)} subtitles)")


if __name__ == "__main__":
    main()
