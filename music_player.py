"""Floating music player: a spinning CD in the top-right corner with play/pause and a volume slider.

Streamlit can't run scripts inside st.markdown, so a tiny hidden iframe injects the player into the
parent page once. The parent page isn't re-rendered when you switch sections, so the music keeps playing.
The mp3 is served by Streamlit's static file serving (see .streamlit/config.toml).
"""

import streamlit.components.v1 as components

TRACK = "/app/static/music.mp3"

PLAYER_JS = """
<script>
(function () {
  const p = window.parent, d = p.document;
  if (p.__cdPlayerLoaded) return;
  p.__cdPlayerLoaded = true;

  const style = d.createElement("style");
  style.textContent = `
    #cd-player { position: fixed; top: 62px; right: 16px; z-index: 999999; display: flex; align-items: center;
      gap: 10px; padding: 6px 14px 6px 8px; border-radius: 999px; background: rgba(25,25,28,.88);
      backdrop-filter: blur(6px); box-shadow: 0 2px 10px rgba(0,0,0,.35); color: #fff;
      font: 600 12px system-ui, sans-serif; }
    #cd-btn { all: unset; cursor: pointer; font-size: 30px; line-height: 1; display: block; }
    #cd-btn.spin { animation: cd-spin 2.5s linear infinite; }
    #cd-btn:focus-visible { outline: 2px solid #d62728; border-radius: 50%; }
    @keyframes cd-spin { to { transform: rotate(360deg); } }
    #cd-vol { width: 80px; accent-color: #d62728; cursor: pointer; }
    #cd-label { white-space: nowrap; opacity: .85; }
    @media (max-width: 600px) { #cd-label { display: none; } #cd-vol { width: 60px; } }
  `;
  d.head.appendChild(style);

  const box = d.createElement("div");
  box.id = "cd-player";
  box.innerHTML = `
    <button id="cd-btn" title="Play / pause music" aria-label="Play or pause music">💿</button>
    <span id="cd-label">Music off</span>
    <input id="cd-vol" type="range" min="0" max="100" value="40" title="Volume" aria-label="Volume">`;
  d.body.appendChild(box);

  const audio = new p.Audio("__TRACK__");
  audio.loop = true;
  audio.volume = 0.4;
  const btn = d.getElementById("cd-btn"), label = d.getElementById("cd-label"), vol = d.getElementById("cd-vol");

  btn.addEventListener("click", () => {
    if (audio.paused) audio.play().catch(() => { label.textContent = "Can't play"; });
    else audio.pause();
  });
  audio.addEventListener("play", () => { btn.classList.add("spin"); label.textContent = "Now playing"; });
  audio.addEventListener("pause", () => { btn.classList.remove("spin"); label.textContent = "Paused"; });
  vol.addEventListener("input", () => { audio.volume = vol.value / 100; });
})();
</script>
"""


def render() -> None:
    components.html(PLAYER_JS.replace("__TRACK__", TRACK), height=0)
