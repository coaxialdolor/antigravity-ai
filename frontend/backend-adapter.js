// backend-adapter.js
// Backend adapter for Antigravity API

const backendAdapter = (() => {
  const API_BASE = window.location.origin;
  let currentSessionId = null;

  // Initialize session
  async function initSession() {
    if (!currentSessionId) {
      try {
        const res = await fetch(`${API_BASE}/api/session`, { method: 'POST' });
        const data = await res.json();
        currentSessionId = data.session_id;
      } catch (e) {
        console.error('Failed to create session:', e);
      }
    }
    return currentSessionId;
  }

  async function sendChatMessage({ text, files = [], model, voice, personality }) {
    try {
      await initSession();
      
      const res = await fetch(`${API_BASE}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text,
          files,
          model,
          voice,
          personality: personality || 'helpful',
          session_id: currentSessionId
        })
      });

      if (!res.ok) {
        throw new Error(`API error: ${res.status}`);
      }

      const data = await res.json();
      if (data.session_id) {
        currentSessionId = data.session_id;
      }
      return data.markdown || data.text || 'No response';
    } catch (e) {
      console.error('Chat error:', e);
      throw e;
    }
  }

  async function transcribeAudio(blob, { model }) {
    try {
      const form = new FormData();
      form.append('audio', blob, 'audio.webm');
      
      const res = await fetch(`${API_BASE}/api/transcribe`, {
        method: 'POST',
        body: form
      });

      if (!res.ok) {
        throw new Error(`Transcription error: ${res.status}`);
      }

      const data = await res.json();
      return data.text || 'Transcription failed';
    } catch (e) {
      console.error('Transcription error:', e);
      throw e;
    }
  }

  async function generateImage({ prompt, size, style, model }) {
    try {
      const res = await fetch(`${API_BASE}/api/image`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt, size, style, model })
      });

      if (!res.ok) {
        throw new Error(`Image generation error: ${res.status}`);
      }

      const blob = await res.blob();
      return blob;
    } catch (e) {
      console.error('Image generation error:', e);
      throw e;
    }
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

