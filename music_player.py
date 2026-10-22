"""Floating music player: a spinning CD in the top-right corner with play/pause and a volume slider.

Streamlit can't run scripts inside st.markdown, so a tiny hidden iframe injects the player into the
parent page once. The parent page isn't re-rendered when you switch sections, so the music keeps playing.
The mp3 is served through st.audio (Streamlit's media server), which also works on Streamlit Community Cloud;
the hidden st.audio element is only used to find that URL.
"""

from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

TRACK = Path(__file__).parent / "static" / "music.mp3"

PLAYER_JS = """
<script>
(function () {
  const p = window.parent, d = p.document;
  if (p.__cdPlayerLoaded) return;
  p.__cdPlayerLoaded = true;

  const style = d.createElement("style");
  style.textContent = `
    [data-testid="stAudio"] { display: none; }
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
  const btn = d.getElementById("cd-btn"), label = d.getElementById("cd-label"), vol = d.getElementById("cd-vol");

  // our own Audio object keeps playing when Streamlit swaps the page's elements
  let audio = null;
  function getAudio() {
    if (audio) return audio;
    const el = d.querySelector('[data-testid="stAudio"] audio') || d.querySelector("audio");
    const src = el && (el.currentSrc || el.src);
    if (!src) return null;
    audio = new p.Audio(src);
    audio.loop = true;
    audio.volume = vol.value / 100;
    audio.addEventListener("play", () => { btn.classList.add("spin"); label.textContent = "Now playing"; });
    audio.addEventListener("pause", () => { btn.classList.remove("spin"); label.textContent = "Paused"; });
    audio.addEventListener("error", () => { label.textContent = "Can't play (error " + (audio.error ? audio.error.code : "?") + ")"; audio = null; });
    return audio;
  }

  btn.addEventListener("click", () => {
    const a = getAudio();
    if (!a) { label.textContent = "Loading…"; return; }
    if (a.paused) a.play().catch(e => { label.textContent = "Can't play: " + e.name; });
    else a.pause();
  });
  vol.addEventListener("input", () => { if (audio) audio.volume = vol.value / 100; });
})();
</script>
"""


def render() -> None:
    st.audio(str(TRACK), format="audio/mpeg")
    components.html(PLAYER_JS, height=0)
