import { useEffect, useRef, useState, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import CodePad from '../../components/CodePad'

/* ──────────────────────────────────────────────────────────
   Audio capture helpers
   ────────────────────────────────────────────────────────── */

const SAMPLE_RATE = 16000
const SILENCE_MS = 600       // how long of silence before sending audio_end
const SILENCE_THRESH = 0.015 // RMS amplitude threshold
const BUFFER_SIZE = 2048     // ScriptProcessor buffer (2048 @ 16kHz = 128ms latency)

function createAudioCapture(onChunk, onSilence) {
  let ctx, source, processor, silentGain, stream
  let silenceTimer = null
  let speaking = false

  async function start() {
    stream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false })
    ctx = new AudioContext({ sampleRate: SAMPLE_RATE })
    source = ctx.createMediaStreamSource(stream)
    processor = ctx.createScriptProcessor(BUFFER_SIZE, 1, 1)

    processor.onaudioprocess = (e) => {
      const floatData = e.inputBuffer.getChannelData(0)

      // RMS for VAD
      let sum = 0
      for (let i = 0; i < floatData.length; i++) sum += floatData[i] ** 2
      const rms = Math.sqrt(sum / floatData.length)

      // Convert float32 → int16 PCM
      const pcm = new Int16Array(floatData.length)
      for (let i = 0; i < floatData.length; i++) {
        pcm[i] = Math.max(-32768, Math.min(32767, floatData[i] * 32767))
      }
      onChunk(pcm.buffer)

      // VAD – silence detection
      if (rms > SILENCE_THRESH) {
        speaking = true
        if (silenceTimer) { clearTimeout(silenceTimer); silenceTimer = null }
      } else if (speaking) {
        if (!silenceTimer) {
          silenceTimer = setTimeout(() => {
            speaking = false
            silenceTimer = null
            onSilence()
          }, SILENCE_MS)
        }
      }
    }

    // Route mic → processor → silent gain (gain=0 mutes mic playback through
    // speakers while keeping ScriptProcessorNode active in the audio graph)
    silentGain = ctx.createGain()
    silentGain.gain.value = 0
    source.connect(processor)
    processor.connect(silentGain)
    silentGain.connect(ctx.destination)
  }

  function stop() {
    processor?.disconnect()
    source?.disconnect()
    silentGain?.disconnect()
    stream?.getTracks().forEach(t => t.stop())
    ctx?.close()
    if (silenceTimer) clearTimeout(silenceTimer)
  }

  return { start, stop }
}

/* ──────────────────────────────────────────────────────────
   Audio playback queue
   ────────────────────────────────────────────────────────── */

function createAudioQueue() {
  const queue = []
  let playing = false
  let onIdle = null  // called when queue drains — used to clear aiTalking

  async function enqueue(blob) {
    queue.push(blob)
    if (!playing) playNext()
  }

  async function playNext() {
    if (queue.length === 0) { playing = false; onIdle?.(); return }
    playing = true
    const blob = queue.shift()
    const url = URL.createObjectURL(blob)
    const audio = new Audio(url)
    audio.onended = () => { URL.revokeObjectURL(url); playNext() }
    audio.onerror = () => { URL.revokeObjectURL(url); playNext() }
    await audio.play().catch(() => {})
  }

  return { enqueue, setOnIdle: (fn) => { onIdle = fn } }
}

/* ──────────────────────────────────────────────────────────
   AI Avatar
   ────────────────────────────────────────────────────────── */

function AIAvatar({ talking, thinking }) {
  return (
    <div className={`iv-avatar ${talking ? 'talking' : ''} ${thinking ? 'thinking' : ''}`}>
      <div className="iv-avatar-ring" />
      <div className="iv-avatar-ring ring2" />
      <div className="iv-avatar-face">
        <div className="iv-avatar-icon">🤖</div>
        {thinking && <div className="iv-avatar-dots"><span /><span /><span /></div>}
      </div>
      <div className="iv-avatar-label">AI Interviewer</div>
    </div>
  )
}

/* ──────────────────────────────────────────────────────────
   Candidate Camera
   ────────────────────────────────────────────────────────── */

function CandidateCam({ videoRef, muted }) {
  return (
    <div className="iv-cam">
      <video ref={videoRef} autoPlay muted={muted} playsInline className="iv-video" />
      <div className="iv-cam-label">You</div>
    </div>
  )
}

/* ──────────────────────────────────────────────────────────
   Main Interview Page
   ────────────────────────────────────────────────────────── */

export default function Interview() {
  const { interviewId } = useParams()
  const navigate = useNavigate()

  const [status, setStatus] = useState('connecting') // connecting | live | ended
  const [transcript, setTranscript] = useState([])
  const [aiTalking, setAiTalking] = useState(false)
  const [aiThinking, setAiThinking] = useState(false)
  const [micOn, setMicOn] = useState(true)
  const [codeQuestion, setCodeQuestion] = useState(null)  // null = hidden
  const [codeBusy, setCodeBusy] = useState(false)
  const [error, setError] = useState(null)

  const wsRef = useRef(null)
  const captureRef = useRef(null)
  const audioQueueRef = useRef(createAudioQueue())
  const pendingAudioRef = useRef([])  // accumulate binary chunks until sentence_end
  const videoRef = useRef(null)
  const txBottomRef = useRef(null)
  // Refs so audio callbacks always read latest state without closure staleness
  const micOnRef = useRef(true)
  const aiTalkingRef = useRef(false)

  // ── Keep refs in sync with state (for audio capture closures) ──
  useEffect(() => { micOnRef.current = micOn }, [micOn])
  useEffect(() => { aiTalkingRef.current = aiTalking }, [aiTalking])

  // ── Ungates mic when AI finishes speaking ──────────────────
  useEffect(() => {
    audioQueueRef.current.setOnIdle(() => setAiTalking(false))
  }, [])

  // ── Setup camera ──────────────────────────────────────────
  useEffect(() => {
    navigator.mediaDevices.getUserMedia({ video: true, audio: false })
      .then(stream => {
        if (videoRef.current) videoRef.current.srcObject = stream
      }).catch(() => {})
  }, [])

  // ── Scroll transcript ─────────────────────────────────────
  useEffect(() => {
    txBottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [transcript])

  // ── Push transcript entry ──────────────────────────────────
  const addTx = useCallback((role, text) => {
    setTranscript(prev => [...prev, { role, text, id: Date.now() + Math.random() }])
  }, [])

  // ── Handle incoming WS message ────────────────────────────
  const handleMessage = useCallback((evt) => {
    if (typeof evt.data === 'string') {
      const msg = JSON.parse(evt.data)

      if (msg.type === 'ready') {
        // Server is ready — now start mic capture
        setStatus('live')
        const ws = wsRef.current
        const capture = createAudioCapture(
          (pcmBuffer) => {
            // Don't send mic audio while AI is speaking — avoids echo-triggered STT
            if (ws.readyState === WebSocket.OPEN && micOnRef.current && !aiTalkingRef.current)
              ws.send(pcmBuffer)
          },
          () => {
            if (ws.readyState === WebSocket.OPEN && !aiTalkingRef.current) {
              ws.send(JSON.stringify({ type: 'audio_end' }))
            }
          }
        )
        capture.start().catch(e => setError(`Mic error: ${e.message}`))
        captureRef.current = capture
      } else if (msg.type === 'user_transcript') {
        addTx('user', msg.text)
      } else if (msg.type === 'ai_thinking') {
        setAiThinking(true)
        setAiTalking(false)
      } else if (msg.type === 'ai_transcript') {
        setAiThinking(false)
        setAiTalking(true)
        addTx('ai', msg.text)
      } else if (msg.type === 'sentence_end') {
        // Flush accumulated audio for this sentence
        if (pendingAudioRef.current.length > 0) {
          const blob = new Blob(pendingAudioRef.current, { type: 'audio/mpeg' })
          audioQueueRef.current.enqueue(blob)
          pendingAudioRef.current = []
        }
      } else if (msg.type === 'trigger_code') {
        setCodeQuestion(msg.question)
      } else if (msg.type === 'code_result') {
        setCodeBusy(false)
        setAiThinking(false)
        setAiTalking(true)
      } else if (msg.type === 'interview_end') {
        setStatus('ended')
        setAiTalking(false)
        setTimeout(() => navigate(`/interview-report?report_id=${msg.report_id}`), 2500)
      } else if (msg.type === 'error') {
        setError(msg.message)
        setAiThinking(false)
      }
    } else {
      // Binary frame = TTS audio chunk
      pendingAudioRef.current.push(evt.data)
    }
  }, [addTx, navigate])

  // ── Connect WebSocket ─────────────────────────────────────
  useEffect(() => {
    if (!interviewId) return

    const wsProto = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const ws = new WebSocket(`${wsProto}//${window.location.host}/ws/interview/${interviewId}`)
    wsRef.current = ws
    ws.binaryType = 'blob'

    ws.onopen = () => {
      setStatus('connecting') // wait for 'ready' msg before starting mic
    }

    ws.onmessage = handleMessage
    ws.onerror = () => setError('WebSocket connection error')
    ws.onclose = () => {
      captureRef.current?.stop()
    }

    return () => {
      ws.close()
      captureRef.current?.stop()
    }
  }, [interviewId])  // intentionally only on mount

  // ── Toggle mic ────────────────────────────────────────────
  function toggleMic() {
    setMicOn(m => !m)
  }

  // ── Send code submission ──────────────────────────────────
  function submitCode(code, language) {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return
    setCodeBusy(true)
    wsRef.current.send(JSON.stringify({ type: 'code_submit', code, language }))
  }

  // ── End interview ─────────────────────────────────────────
  function endInterview() {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return
    if (!confirm('End the interview now?')) return
    wsRef.current.send(JSON.stringify({ type: 'end_interview' }))
  }

  // ── Layout ────────────────────────────────────────────────
  const codeOpen = Boolean(codeQuestion)

  if (status === 'ended') {
    return (
      <div className="iv-shell">
        <div className="iv-ended">
          <div style={{ fontSize: 48 }}>✅</div>
          <h2>Interview Complete</h2>
          <p>Generating your report…</p>
        </div>
      </div>
    )
  }

  return (
    <div className="iv-shell">
      {/* Top bar */}
      <div className="iv-topbar">
        <div className="iv-brand">HireForce <span className="iv-live-dot" /> LIVE</div>
        {status === 'connecting' && <span style={{ fontSize: 13, color: 'var(--text-muted)' }}>Connecting…</span>}
        <button className="btn btn-danger btn-sm" onClick={endInterview}>End Interview</button>
      </div>

      <div className="iv-body">
        {/* Left: cams + transcript */}
        <div className={`iv-left ${codeOpen ? 'narrow' : ''}`}>
          {/* Video panels */}
          <div className="iv-cams">
            <AIAvatar talking={aiTalking} thinking={aiThinking} />
            <CandidateCam videoRef={videoRef} muted />
          </div>

          {/* Live transcript */}
          <div className="iv-transcript">
            {transcript.length === 0 && (
              <div className="iv-tx-empty">Transcript will appear here…</div>
            )}
            {transcript.map(t => (
              <div key={t.id} className={`iv-tx-line ${t.role}`}>
                <span className="iv-tx-role">{t.role === 'ai' ? '🤖 AI' : '👤 You'}</span>
                <span className="iv-tx-text">{t.text}</span>
              </div>
            ))}
            {aiThinking && (
              <div className="iv-tx-line ai">
                <span className="iv-tx-role">🤖 AI</span>
                <span className="iv-tx-dots"><span /><span /><span /></span>
              </div>
            )}
            <div ref={txBottomRef} />
          </div>

          {/* Bottom controls */}
          <div className="iv-controls">
            <button
              className={`iv-ctrl-btn ${micOn ? 'active' : 'muted'}`}
              onClick={toggleMic}
              title={micOn ? 'Mute mic' : 'Unmute mic'}
            >
              {micOn ? '🎤' : '🔇'}
              <span>{micOn ? 'Mic On' : 'Muted'}</span>
            </button>
            {error && <div className="iv-error">⚠ {error}</div>}
          </div>
        </div>

        {/* Right: Code pad (slides in) */}
        {codeOpen && (
          <div className="iv-right">
            <CodePad
              question={codeQuestion}
              onSubmit={submitCode}
              busy={codeBusy}
            />
          </div>
        )}
      </div>
    </div>
  )
}
