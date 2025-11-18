// app.js
(() => {
  const qs = (sel, el = document) => el.querySelector(sel);
  const qsa = (sel, el = document) => Array.from(el.querySelectorAll(sel));

  // Elements
  const chatLog = qs('#chatLog');
  const messageInput = qs('#messageInput');
  const sendBtn = qs('#sendBtn');
  const uploadAnyBtn = qs('#uploadAnyBtn');
  const uploadImageBtn = qs('#uploadImageBtn');
  const anyFileInput = qs('#anyFileInput');
  const imageFileInput = qs('#imageFileInput');
  const attachmentTray = qs('#attachmentTray');
  const micBtn = qs('#micBtn');
  const stopMicBtn = qs('#stopMicBtn');
  const screenshotBtn = qs('#screenshotBtn');
  const imageGenBtn = qs('#imageGenBtn');
  const imageGenModal = qs('#imageGenModal');
  const closeImageGenBtn = qs('#closeImageGenBtn');
  const runImageGenBtn = qs('#runImageGenBtn');
  const imageGenPrompt = qs('#imageGenPrompt');
  const imageGenSize = qs('#imageGenSize');
  const imageGenStyle = qs('#imageGenStyle');
  const modelSelect = qs('#modelSelect');
  const voiceSelect = qs('#voiceSelect');
  const personalitySelect = qs('#personalitySelect');
  const connectLiveBtn = qs('#connectLiveBtn');
  const liveVoiceStatus = qs('#liveVoiceStatus');
  const clearChatBtn = qs('#clearChatBtn');
  const conversationBtn = qs('#conversationBtn');
  const previewModal = qs('#previewModal');
  const previewContainer = qs('#previewContainer');
  const closePreviewBtn = qs('#closePreviewBtn');
  const snipOverlay = qs('#snipOverlay');
  const snipImage = qs('#snipImage');
  const snipSelection = qs('#snipSelection');
  const snipCancelBtn = qs('#snipCancelBtn');
  const snipConfirmBtn = qs('#snipConfirmBtn');

  // State
  const state = {
    attachments: [], // {file, url, previewUrl, kind}
    isRecording: false,
    mediaRecorder: null,
    recordedChunks: [],
    liveVoiceConnected: false,
    liveVoicePeer: null,
    liveMicStream: null,
    config: {
      model: modelSelect.value,
      voice: voiceSelect.value,
      personality: personalitySelect.value
    }
  };

  // Setup
  hljs.configure({ ignoreUnescapedHTML: true });
  marked.setOptions({
    breaks: true,
    gfm: true,
    headerIds: false
  });

  // Helpers
  const autoGrowTextarea = (ta) => {
    ta.style.height = 'auto';
    ta.style.height = Math.min(300, ta.scrollHeight) + 'px';
  };

  const scrollToBottom = () => {
    chatLog.scrollTop = chatLog.scrollHeight;
  };

  function createMessageEl({ role, markdown, attachments = [], timestamp = new Date() }) {
    const el = document.createElement('div');
    el.className = `message ${role}`;
    el.innerHTML = `
      <div class="avatar">${role === 'user' ? '🧑' : '🤖'}</div>
      <div class="bubble">
        <div class="meta">${role === 'user' ? 'You' : 'Assistant'} • ${timestamp.toLocaleTimeString()}</div>
        <div class="content"></div>
      </div>
    `;
    const content = qs('.content', el);
    // Render markdown safely
    const html = marked.parse(markdown || '');
    content.innerHTML = html;

    // Enhance code blocks (assistant only)
    if (role === 'assistant') {
      enhanceCodeBlocks(content);
    } else {
      // Still highlight user code if any
      qsa('pre code', content).forEach(block => hljs.highlightElement(block));
    }

    // Render attachments thumbnails if any
    if (attachments.length > 0) {
      const attachWrap = document.createElement('div');
      attachWrap.className = 'attachments';
      attachments.forEach(att => {
        const pill = document.createElement('div');
        pill.className = 'attachment-pill';
        if (att.kind === 'image' || att.kind === 'screenshot') {
          const img = document.createElement('img');
          img.src = att.previewUrl || att.url;
          pill.appendChild(img);
        } else {
          pill.innerHTML += '📎';
        }
        const span = document.createElement('span');
        span.textContent = att.file?.name || att.url?.split('/').pop() || att.kind;
        pill.appendChild(span);
        attachWrap.appendChild(pill);
      });
      qs('.bubble', el).appendChild(attachWrap);
    }

    return el;
  }

  function enhanceCodeBlocks(container) {
    const pres = qsa('pre', container);
    pres.forEach(pre => {
      const code = pre.querySelector('code');
      if (!code) return;

      // Syntax highlight
      hljs.highlightElement(code);

      // Toolbar
      const wrap = document.createElement('div');
      wrap.className = 'code-wrap';
      pre.parentNode.insertBefore(wrap, pre);
      wrap.appendChild(pre);

      const toolbar = document.createElement('div');
      toolbar.className = 'code-toolbar';

      const copyBtn = document.createElement('button');
      copyBtn.textContent = 'Copy';
      copyBtn.addEventListener('click', () => {
        navigator.clipboard.writeText(code.innerText);
        copyBtn.textContent = 'Copied!';
        setTimeout(() => (copyBtn.textContent = 'Copy'), 1200);
      });

      const previewBtn = document.createElement('button');
      previewBtn.textContent = 'Preview';
      previewBtn.addEventListener('click', () => {
        const lang = (code.className || '').replace('language-', '').trim().toLowerCase();
        openPreviewModal(code.innerText, lang);
      });

      toolbar.appendChild(copyBtn);
      // Only show Preview for supported languages
      const supported = ['html', 'xml', 'javascript', 'js', 'python', 'py'];
      if (supported.includes((code.className || '').replace('language-', '').trim().toLowerCase())) {
        toolbar.appendChild(previewBtn);
      }

      wrap.appendChild(toolbar);
    });
  }

  // Message operations
  function addUserMessage(markdown, attachments = []) {
    const el = createMessageEl({ role: 'user', markdown, attachments });
    chatLog.appendChild(el);
    scrollToBottom();
    return el;
  }

  function addAssistantMessage(markdown, attachments = []) {
    const el = createMessageEl({ role: 'assistant', markdown, attachments });
    chatLog.appendChild(el);
    scrollToBottom();
    return el;
  }

  function addAssistantThinking() {
    const el = document.createElement('div');
    el.className = 'message assistant';
    el.innerHTML = `
      <div class="avatar">🤖</div>
      <div class="bubble">
        <div class="meta">Assistant • ${new Date().toLocaleTimeString()}</div>
        <div class="content">Thinking<span class="dots">...</span></div>
      </div>
    `;
    chatLog.appendChild(el);
    scrollToBottom();
    return el;
  }

  function updateAssistantMessage(el, markdown) {
    const content = qs('.content', el);
    content.innerHTML = marked.parse(markdown);
    enhanceCodeBlocks(content);
    scrollToBottom();
  }

  // Attachment handling
  function addAttachment(file, kind) {
    const att = { file, kind };
    att.previewUrl = kind === 'image' || kind === 'screenshot' ? URL.createObjectURL(file) : null;
    state.attachments.push(att);
    renderAttachmentTray();
  }

  function removeAttachment(index) {
    const att = state.attachments[index];
    if (att?.previewUrl) URL.revokeObjectURL(att.previewUrl);
    state.attachments.splice(index, 1);
    renderAttachmentTray();
  }

  function renderAttachmentTray() {
    attachmentTray.innerHTML = '';
    state.attachments.forEach((att, i) => {
      const pill = document.createElement('div');
      pill.className = 'attachment-pill';
      if (att.previewUrl) {
        const img = document.createElement('img');
        img.src = att.previewUrl;
        pill.appendChild(img);
      } else {
        pill.innerHTML += '📎';
      }
      const span = document.createElement('span');
      span.textContent = att.file?.name || att.kind;
      const rm = document.createElement('button');
      rm.textContent = '✖';
      rm.addEventListener('click', () => removeAttachment(i));
      pill.appendChild(span);
      pill.appendChild(rm);
      attachmentTray.appendChild(pill);
    });
  }

  // Send message
  async function sendMessage() {
    const text = messageInput.value.trim();
    const hasAttachments = state.attachments.length > 0;
    if (!text && !hasAttachments) return;

    const userEl = addUserMessage(text || '(sent attachments)', state.attachments);

    // Prepare payload
    const payload = {
      text,
      model: state.config.model,
      voice: state.config.voice,
      personality: state.config.personality,
      files: await Promise.all(state.attachments.map(att => fileToPayload(att.file, att.kind)))
    };

    // Clear composer
    messageInput.value = '';
    autoGrowTextarea(messageInput);
    state.attachments = [];
    renderAttachmentTray();

    // Assistant placeholder
    const thinkingEl = addAssistantThinking();

    try {
      const responseMarkdown = await backendAdapter.sendChatMessage(payload);
      updateAssistantMessage(thinkingEl, responseMarkdown);
    } catch (err) {
      updateAssistantMessage(thinkingEl, `Sorry, there was an error: ${err.message || err}`);
    }
  }

  async function fileToPayload(file, kind) {
    const b64 = await fileToBase64(file);
    return {
      name: file.name,
      type: file.type,
      size: file.size,
      kind,
      dataUrl: b64
    };
  }

  function fileToBase64(file) {
    return new Promise((resolve, reject) => {
      const r = new FileReader();
      r.onload = () => resolve(r.result);
      r.onerror = reject;
      r.readAsDataURL(file);
    });
  }

  // Screenshot & Snipping
  async function captureScreenshot() {
    let stream;
    try {
      stream = await navigator.mediaDevices.getDisplayMedia({ video: true });
      const track = stream.getVideoTracks()[0];
      const imageCapture = new ImageCapture(track);
      const bitmap = await imageCapture.grabFrame();
      track.stop();

      // Convert to dataURL
      const canvas = document.createElement('canvas');
      canvas.width = bitmap.width;
      canvas.height = bitmap.height;
      const ctx = canvas.getContext('2d');
      ctx.drawImage(bitmap, 0, 0);
      const dataUrl = canvas.toDataURL('image/png');

      openSnippingOverlay(dataUrl, bitmap.width, bitmap.height);
    } catch (err) {
      console.error('Screen capture error:', err);
      alert('Unable to capture screen (permission denied or unsupported).');
    } finally {
      if (stream) stream.getTracks().forEach(t => t.stop());
    }
  }

  let snipState = {
    imgNaturalWidth: 0,
    imgNaturalHeight: 0,
    startX: 0, startY: 0,
    endX: 0, endY: 0,
    selecting: false
  };

  function openSnippingOverlay(dataUrl, originalW, originalH) {
    snipImage.src = dataUrl;
    snipState.imgNaturalWidth = originalW;
    snipState.imgNaturalHeight = originalH;
    snipSelection.hidden = true;
    snipConfirmBtn.disabled = true;
    snipOverlay.style.display = 'grid';
  }

  // Snip events
  snipImage.addEventListener('load', () => {
    // ready
  });

  snipImage.addEventListener('mousedown', (e) => {
    const r = snipImage.getBoundingClientRect();
    snipState.selecting = true;
    snipState.startX = e.clientX - r.left;
    snipState.startY = e.clientY - r.top;
    snipSelection.hidden = false;
    Object.assign(snipSelection.style, { left: `${snipState.startX}px`, top: `${snipState.startY}px`, width: '0px', height: '0px' });
  });

  snipImage.addEventListener('mousemove', (e) => {
    if (!snipState.selecting) return;
    const r = snipImage.getBoundingClientRect();
    snipState.endX = e.clientX - r.left;
    snipState.endY = e.clientY - r.top;
    const x = Math.min(snipState.startX, snipState.endX);
    const y = Math.min(snipState.startY, snipState.endY);
    const w = Math.abs(snipState.endX - snipState.startX);
    const h = Math.abs(snipState.endY - snipState.startY);
    Object.assign(snipSelection.style, { left: `${x}px`, top: `${y}px`, width: `${w}px`, height: `${h}px` });
  });

  snipImage.addEventListener('mouseup', () => {
    snipState.selecting = false;
    const rect = snipSelection.getBoundingClientRect();
    if (rect.width > 10 && rect.height > 10) {
      snipConfirmBtn.disabled = false;
    }
  });

  snipCancelBtn.addEventListener('click', () => {
    snipOverlay.style.display = 'none';
  });

  snipConfirmBtn.addEventListener('click', async () => {
    // Crop to canvas
    const imgRect = snipImage.getBoundingClientRect();
    const selRect = snipSelection.getBoundingClientRect();

    // Relative to image
    const scaleX = snipState.imgNaturalWidth / imgRect.width;
    const scaleY = snipState.imgNaturalHeight / imgRect.height;
    const sx = (selRect.left - imgRect.left) * scaleX;
    const sy = (selRect.top - imgRect.top) * scaleY;
    const sw = selRect.width * scaleX;
    const sh = selRect.height * scaleY;

    const cvs = document.createElement('canvas');
    cvs.width = Math.max(1, Math.round(sw));
    cvs.height = Math.max(1, Math.round(sh));
    const ctx = cvs.getContext('2d');

    const tempImg = new Image();
    tempImg.onload = () => {
      ctx.drawImage(tempImg, sx, sy, sw, sh, 0, 0, cvs.width, cvs.height);
      cvs.toBlob((blob) => {
        if (!blob) return;
        const file = new File([blob], `screenshot-${Date.now()}.png`, { type: 'image/png' });
        addAttachment(file, 'screenshot');
        snipOverlay.style.display = 'none';
      }, 'image/png', 0.95);
    };
    tempImg.src = snipImage.src;
  });

  // Code Preview Modal
  async function openPreviewModal(code, lang) {
    previewContainer.innerHTML = '';
    previewModal.style.display = 'grid';

    const normalized = (lang || '').toLowerCase();
    if (['html', 'xml'].includes(normalized)) {
      const iframe = document.createElement('iframe');
      iframe.style.width = '100%';
      iframe.style.height = '70vh';
      iframe.sandbox = 'allow-scripts allow-forms';
      iframe.srcdoc = code;
      previewContainer.appendChild(iframe);
    } else if (['javascript', 'js'].includes(normalized)) {
      const iframe = document.createElement('iframe');
      iframe.style.width = '100%';
      iframe.style.height = '70vh';
      iframe.sandbox = 'allow-scripts allow-forms';
      iframe.srcdoc = `<!doctype html><html><head><meta charset="utf-8"/><title>JS Preview</title></head>
      <body><div id="app" style="font-family: system-ui; padding:12px;">JS code is running. Open devtools console for logs.</div>
      <script>
      try {
        ${code}
      } catch (e) {
        document.body.innerHTML += '<pre style="color:red">'+(e?.stack || e)+'</pre>';
      }
      </script></body></html>`;
      previewContainer.appendChild(iframe);
    } else if (['python', 'py'].includes(normalized)) {
      const wrap = document.createElement('div');
      wrap.innerHTML = `
        <div style="display:flex; gap:8px; margin-bottom:8px;">
          <button id="runPyBtn" class="primary-btn">Run</button>
          <button id="clearPyBtn" class="secondary-btn">Clear</button>
          <div id="pyStatus" style="margin-left:auto; color: var(--muted)">Loading Pyodide...</div>
        </div>
        <div style="display:grid; grid-template-columns:1fr 1fr; gap:12px;">
          <textarea id="pyInput" style="height:70vh">${code.replace(/</g, '&lt;')}</textarea>
          <pre id="pyOutput" style="height:70vh; overflow:auto; margin:0;"></pre>
        </div>
      `;
      previewContainer.appendChild(wrap);

      // Load Pyodide on demand
      const statusEl = qs('#pyStatus', wrap);
      await ensurePyodide(statusEl);
      statusEl.textContent = 'Ready';

      const runBtn = qs('#runPyBtn', wrap);
      const clearBtn = qs('#clearPyBtn', wrap);
      const input = qs('#pyInput', wrap);
      const output = qs('#pyOutput', wrap);

      runBtn.onclick = async () => {
        output.textContent += '>>> Running...\n';
        try {
          const result = await runPythonInPyodide(input.value);
          if (result !== undefined && result !== null) {
            output.textContent += String(result) + '\n';
          }
        } catch (e) {
          output.textContent += (e?.message || String(e)) + '\n';
        }
      };

      clearBtn.onclick = () => output.textContent = '';
    } else {
      const p = document.createElement('p');
      p.textContent = `Preview not supported for "${lang}".`;
      previewContainer.appendChild(p);
    }
  }

  closePreviewBtn.addEventListener('click', () => {
    previewModal.style.display = 'none';
    previewContainer.innerHTML = '';
  });

  previewModal.addEventListener('click', (e) => {
    if (e.target === previewModal) closePreviewBtn.click();
  });

  // Pyodide
  let pyodideReady = null;
  async function ensurePyodide(statusEl) {
    if (pyodideReady) return pyodideReady;

    statusEl && (statusEl.textContent = 'Loading Pyodide...');
    pyodideReady = new Promise(async (resolve, reject) => {
      try {
        const script = document.createElement('script');
        script.src = 'https://cdn.jsdelivr.net/pyodide/v0.26.1/full/pyodide.js';
        script.onload = async () => {
          try {
            window.pyodide = await loadPyodide();
            // Redirect print to return value; we capture stdout to a buffer
            await pyodide.runPythonAsync(`
import sys
from js import console
class _CapOut:
    def __init__(self):
        self.buf = ''
    def write(self, s):
        self.buf += s
    def flush(self):
        pass
sys.stdout = _CapOut()
sys.stderr = _CapOut()
`);
            resolve(window.pyodide);
          } catch (err) {
            reject(err);
          }
        };
        script.onerror = reject;
        document.body.appendChild(script);
      } catch (e) { reject(e); }
    });
    await pyodideReady;
  }

  async function runPythonInPyodide(code) {
    // Clear buffers before run
    const res = await pyodide.runPythonAsync(`
sys.stdout.buf = ''
sys.stderr.buf = ''
${code}
sys.stdout.buf + (('\\n' + sys.stderr.buf) if sys.stderr.buf else '')
`);
    return res;
  }

  // Transcription
  async function startRecording() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      state.isRecording = true;
      state.recordedChunks = [];
      state.mediaRecorder = new MediaRecorder(stream);
      state.mediaRecorder.ondataavailable = (e) => e.data.size && state.recordedChunks.push(e.data);
      state.mediaRecorder.onstop = handleRecordingStop;
      state.mediaRecorder.start();
      micBtn.style.display = 'none';
      stopMicBtn.style.display = 'inline-flex';
    } catch (e) {
      alert('Microphone access denied or unsupported.');
    }
  }

  async function stopRecording() {
    if (state.mediaRecorder && state.isRecording) {
      state.mediaRecorder.stop();
      state.isRecording = false;
      micBtn.style.display = 'inline-flex';
      stopMicBtn.style.display = 'none';
      state.mediaRecorder.stream.getTracks().forEach(t => t.stop());
    }
  }

  async function handleRecordingStop() {
    const blob = new Blob(state.recordedChunks, { type: 'audio/webm' });
    // Show quick pill that we recorded something
    addUserMessage('(voice message)');
    const thinkingEl = addAssistantThinking();
    try {
      const text = await backendAdapter.transcribeAudio(blob, { model: state.config.model });
      updateAssistantMessage(thinkingEl, `Transcription: ${text}`);
    } catch (err) {
      updateAssistantMessage(thinkingEl, `Transcription failed: ${err.message || err}`);
    }
  }

  // Live voice to voice (WebRTC)
  async function connectLiveVoice() {
    if (state.liveVoiceConnected) {
      // Disconnect
      try {
        if (state.liveVoicePeer) state.liveVoicePeer.close();
        if (state.liveMicStream) state.liveMicStream.getTracks().forEach(t => t.stop());
      } finally {
        state.liveVoicePeer = null;
        state.liveMicStream = null;
        state.liveVoiceConnected = false;
        liveVoiceStatus.classList.remove('active');
        connectLiveBtn.innerHTML = '<span class="icon">🎧</span><span>Connect</span>';
      }
      return;
    }

    try {
      const { peer, stream } = await backendAdapter.connectRealtimeVoice({
        model: state.config.model,
        voice: state.config.voice
      });
      state.liveVoicePeer = peer;
      state.liveMicStream = stream;
      state.liveVoiceConnected = true;
      liveVoiceStatus.classList.add('active');
      connectLiveBtn.innerHTML = '<span class="icon">🔌</span><span>Disconnect</span>';
    } catch (e) {
      alert('Failed to connect to live voice server: ' + (e?.message || e));
    }
  }

  // Image generation modal
  function openImageGen() {
    imageGenModal.style.display = 'grid';
    imageGenPrompt.focus();
  }

  function closeImageGen() {
    imageGenModal.style.display = 'none';
  }

  async function runImageGen() {
    const prompt = imageGenPrompt.value.trim();
    if (!prompt) return alert('Please enter a prompt.');

    closeImageGen();

    addUserMessage(`Generate an image: "${prompt}"`);
    const thinkingEl = addAssistantThinking();

    try {
      const size = imageGenSize.value;
      const style = imageGenStyle.value;
      const blob = await backendAdapter.generateImage({ prompt, size, style, model: state.config.model });
      const file = new File([blob], `generated-${Date.now()}.png`, { type: 'image/png' });
      const url = URL.createObjectURL(blob);

      updateAssistantMessage(thinkingEl, `Here is your generated image (${size}, ${style}):`);

      const msgEl = chatLog.lastElementChild;
      const attachmentsDiv = document.createElement('div');
      attachmentsDiv.className = 'attachments';
      const pill = document.createElement('div');
      pill.className = 'attachment-pill';
      const img = document.createElement('img');
      img.src = url;
      pill.appendChild(img);
      const span = document.createElement('span');
      span.textContent = file.name;
      pill.appendChild(span);
      attachmentsDiv.appendChild(pill);
      qs('.bubble', msgEl).appendChild(attachmentsDiv);

      scrollToBottom();
    } catch (e) {
      updateAssistantMessage(thinkingEl, `Image generation failed: ${e?.message || e}`);
    }
  }

  // Events
  sendBtn.addEventListener('click', sendMessage);

  messageInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });

  messageInput.addEventListener('input', () => autoGrowTextarea(messageInput));
  window.addEventListener('load', () => autoGrowTextarea(messageInput));

  uploadAnyBtn.addEventListener('click', () => anyFileInput.click());
  uploadImageBtn.addEventListener('click', () => imageFileInput.click());

  anyFileInput.addEventListener('change', () => {
    Array.from(anyFileInput.files).forEach(f => addAttachment(f, 'file'));
    anyFileInput.value = '';
  });

  imageFileInput.addEventListener('change', () => {
    Array.from(imageFileInput.files).forEach(f => addAttachment(f, 'image'));
    imageFileInput.value = '';
  });

  // Drag & drop / paste
  document.addEventListener('dragover', (e) => e.preventDefault());
  document.addEventListener('drop', (e) => {
    e.preventDefault();
    const files = Array.from(e.dataTransfer.files || []);
    files.forEach(f => addAttachment(f, f.type.startsWith('image/') ? 'image' : 'file'));
  });

  document.addEventListener('paste', (e) => {
    const items = Array.from(e.clipboardData?.items || []);
    items.forEach(item => {
      if (item.type.startsWith('image/')) {
        const file = item.getAsFile();
        if (file) addAttachment(file, 'image');
      }
    });
  });

  // Screenshot
  screenshotBtn.addEventListener('click', captureScreenshot);

  // Mic
  micBtn.addEventListener('click', startRecording);
  stopMicBtn.addEventListener('click', stopRecording);

  // Live
  connectLiveBtn.addEventListener('click', connectLiveVoice);

  // Image Gen modal
  imageGenBtn.addEventListener('click', openImageGen);
  closeImageGenBtn.addEventListener('click', closeImageGen);
  imageGenModal.addEventListener('click', (e) => {
    if (e.target === imageGenModal) closeImageGen();
  });
  runImageGenBtn.addEventListener('click', runImageGen);

  // Clear chat
  clearChatBtn.addEventListener('click', () => {
    chatLog.innerHTML = '';
  });

  // New conversation
  conversationBtn.addEventListener('click', () => {
    chatLog.innerHTML = '';
    addAssistantMessage(
`Hi! I'm your multimodal assistant.

- Upload files or images, snip a screenshot, record audio, or generate images.

- I can attach a Preview button to code blocks (HTML, JS, Python). Try me!`
    );
  });

  // Dropdowns -> update state
  modelSelect.addEventListener('change', () => state.config.model = modelSelect.value);
  voiceSelect.addEventListener('change', () => state.config.voice = voiceSelect.value);
  personalitySelect.addEventListener('change', () => state.config.personality = personalitySelect.value);

  // Initial system greeting
  addAssistantMessage(
`Hi! I'm your multimodal assistant.

- Upload files or images, snip a screenshot, record audio, or generate images.

- I can attach a Preview button to code blocks (HTML, JS, Python). Try me!`
  );

})();

