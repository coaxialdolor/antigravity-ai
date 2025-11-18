# Multimodal Chat Frontend

A complete, modern, single-page frontend for a multimodal chatbot with file uploads, image generation, voice recording, and code preview capabilities.

## Features

- **Chat Interface**: Single chat window where all responses appear
- **File Upload**: Upload any files or images
- **Screenshot Capture**: Screen capture with snipping overlay for cropping
- **Image Generation**: Generate images from text prompts
- **Voice Recording**: Record audio for transcription
- **Live Voice**: WebRTC-ready voice-to-voice communication
- **Code Preview**: Preview HTML, JavaScript, and Python code blocks with Copy + Preview buttons
- **Model Selection**: Choose between different AI models
- **Voice Selection**: Select different voice options
- **Personality Selection**: Choose assistant personality
- **Dark/Light Theme**: Toggle between themes
- **Drag & Drop**: Drag files or paste images directly into the chat
- **Responsive Layout**: Works on desktop and mobile devices

## Files

- `index.html` - Main HTML structure and layout
- `styles.css` - Complete styling with dark/light theme support
- `app.js` - All UI logic and multimodal features
- `backend-adapter.js` - Demo backend adapter (replace with your API endpoints)

## Usage

1. **Open the frontend**: Simply open `index.html` in a modern browser
   - For HTTPS features (screenshot, microphone), you may need to serve via a local server

2. **Demo Mode**: The frontend runs in demo mode by default. To connect to your backend:
   - Edit `backend-adapter.js`
   - Set `DEMO_MODE = false`
   - Replace the stub functions with your actual API calls

## Backend Integration

The `backend-adapter.js` file contains placeholder functions that you should replace with your actual API endpoints:

### `sendChatMessage({ text, files, model, voice, personality })`
- Sends chat messages with optional file attachments
- Should return markdown text

### `transcribeAudio(blob, { model })`
- Transcribes audio recordings
- Should return transcribed text

### `generateImage({ prompt, size, style, model })`
- Generates images from text prompts
- Should return an image blob

### `connectRealtimeVoice({ model, voice })`
- Sets up WebRTC connection for live voice
- Should return `{ peer: RTCPeerConnection, stream: MediaStream }`

## Browser Requirements

- Modern browser with ES6+ support
- For screenshot capture: Requires HTTPS context
- For microphone: Requires HTTPS context and user permission
- For WebRTC: Requires HTTPS context

## Local Development Server

To test HTTPS features locally, you can use a simple HTTP server:

```bash
# Python 3
python -m http.server 8000

# Node.js (with http-server)
npx http-server -p 8000

# Then open http://localhost:8000/frontend/index.html
```

For HTTPS, you can use tools like `mkcert` or serve via a framework that supports HTTPS.

## Code Preview Features

- **HTML/XML**: Renders in a sandboxed iframe
- **JavaScript**: Executes in a sandboxed iframe with console logging
- **Python**: Uses Pyodide (loaded on-demand) to run Python code in the browser

## Notes

- Screenshot capture and microphone require user permissions (HTTPS context)
- Python preview loads Pyodide (~10MB) on first use
- All code previews run in sandboxed environments for security
- The frontend is completely standalone and can be integrated with any backend

