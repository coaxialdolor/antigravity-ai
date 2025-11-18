// backend-adapter.js
// Swap these stubs with your real endpoints.
// For example, sendChatMessage -> POST /api/chat with { text, files, model, voice, personality }.
// Image generation -> POST /api/image.
// Transcription -> POST /api/transcribe with audio blob.
// Live voice -> Initiate WebRTC with your Realtime server (return RTCPeerConnection + mic stream).

const backendAdapter = (() => {
  const DEMO_MODE = true;

  async function sendChatMessage({ text, files = [], model, voice, personality }) {
    if (!DEMO_MODE) {
      // Example:
      // const res = await fetch('/api/chat', { method: 'POST', body: JSON.stringify({ text, files, model, voice, personality }), headers: { 'Content-Type': 'application/json' } });
      // const data = await res.json();
      // return data.markdown;
    }

    // Demo: pretend the assistant saw attachments and returns code examples with Preview buttons.
    const fileLine = files.length ? `I got ${files.length} file(s).` : '';
    const persona = personality?.charAt(0).toUpperCase() + personality?.slice(1);

    const reply = [
      `Model: ${model} • Voice: ${voice} • Personality: ${persona}`,
      fileLine,
      text ? `You said: "${text}"` : '',
      ``,
      `Here are some runnable snippets:`,
      ``,
      `HTML:`,
      "```html",
      "<div style='padding:16px; font-family: system-ui'>",
      "  <h2>Hello from Preview!</h2>",
      "  <p>This HTML is running inside a sandboxed iframe.</p>",
      "</div>",
      "```",
      ``,
      `JavaScript:`,
      "```javascript",
      "document.body.style.background = 'papayawhip';",
      "const el = document.createElement('div');",
      "el.innerHTML = '<h3 style=\"font-family: system-ui\">JS Preview Running ✅</h3>';",
      "document.body.appendChild(el);",
      "```",
      ``,
      `Python:`,
      "```python",
      "print('Hello from Python Preview!')",
      "for i in range(3):",
      "    print('Line', i+1)",
      "```"
    ].filter(Boolean).join('\n');

    // Simulate network delay
    await new Promise(r => setTimeout(r, 600));
    return reply;
  }

  async function transcribeAudio(blob, { model }) {
    if (!DEMO_MODE) {
      // const form = new FormData();
      // form.append('audio', blob, 'audio.webm');
      // form.append('model', model);
      // const res = await fetch('/api/transcribe', { method: 'POST', body: form });
      // const data = await res.json();
      // return data.text;
    }

    await new Promise(r => setTimeout(r, 500));
    return '(demo) Transcribed text from your recording.';
  }

  async function generateImage({ prompt, size, style, model }) {
    if (!DEMO_MODE) {
      // const res = await fetch('/api/image', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({ prompt, size, style, model }) });
      // const arrayBuf = await res.arrayBuffer();
      // return new Blob([arrayBuf], { type: 'image/png' });
    }

    // Demo: generate a placeholder PNG via canvas
    const [w, h] = size.split('x').map(Number);
    const cvs = new OffscreenCanvas(w, h);
    const ctx = cvs.getContext('2d');
    ctx.fillStyle = '#1f2937'; ctx.fillRect(0, 0, w, h);
    const grad = ctx.createLinearGradient(0, 0, w, h);
    grad.addColorStop(0, '#60a5fa'); grad.addColorStop(1, '#a78bfa');
    ctx.fillStyle = grad;
    ctx.beginPath();
    ctx.arc(w/2, h/2, Math.min(w,h)*0.35, 0, Math.PI*2);
    ctx.fill();
    ctx.fillStyle = 'white';
    ctx.font = `${Math.max(16, w*0.03)}px Inter, sans-serif`;
    ctx.textAlign = 'center';
    ctx.fillText(style, w/2, h/2 - Math.max(10, h*0.03));
    ctx.fillText(prompt.slice(0, 30) + (prompt.length>30?'…':''), w/2, h/2 + Math.max(20, h*0.05));
    const blob = await cvs.convertToBlob({ type: 'image/png' });
    return blob;
  }

  async function connectRealtimeVoice({ model, voice }) {
    // This sets up a WebRTC connection in real life. For demo, we simulate failure unless you implement it.
    // Outline:
    // 1) const pc = new RTCPeerConnection();
    // 2) const mic = await navigator.mediaDevices.getUserMedia({ audio: true });
    // 3) mic.getTracks().forEach(t => pc.addTrack(t, mic));
    // 4) const audioEl = new Audio(); pc.ontrack = e => audioEl.srcObject = e.streams[0]; audioEl.play();
    // 5) const offer = await pc.createOffer(); await pc.setLocalDescription(offer);
    // 6) POST offer.sdp to your /realtime endpoint; get answer.sdp; pc.setRemoteDescription(answer)
    // 7) Return { peer: pc, stream: mic }

    if (location.protocol !== 'https:') {
      throw new Error('Live voice requires HTTPS in browsers.');
    }

    // Demo: show a fake connection that toggles state
    const pc = new RTCPeerConnection();
    const mic = await navigator.mediaDevices.getUserMedia({ audio: true });
    mic.getTracks().forEach(t => pc.addTrack(t, mic));

    // In a real impl, you would signal with your server here.

    // Close automatically in 2 minutes in demo
    setTimeout(() => pc.close(), 2 * 60 * 1000);

    return { peer: pc, stream: mic };
  }

  return {
    sendChatMessage,
    transcribeAudio,
    generateImage,
    connectRealtimeVoice
  };
})();

