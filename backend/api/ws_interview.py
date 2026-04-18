"""
WebSocket Interview Endpoint
============================
ws://host/ws/interview/{interview_id}

Accepts interview_id (not session_id).
Creates or resumes a session automatically on connect.
Sends the AI greeting immediately via TTS.

Client → Server JSON:
  { "type": "audio_end" }
  { "type": "code_submit", "code": "...", "language": "python" }
  { "type": "end_interview" }

Client → Server binary:
  Raw 16-bit signed mono PCM at 16 kHz

Server → Client JSON:
  { "type": "ready" }
  { "type": "user_transcript", "text": "..." }
  { "type": "ai_thinking" }
  { "type": "ai_transcript",  "text": "..." }
  { "type": "sentence_end" }
  { "type": "trigger_code",   "question": {...} }
  { "type": "code_result",    "evaluation": {...}, "agent_message": "..." }
  { "type": "interview_end",  "report_id": "..." }
  { "type": "error",          "message": "..." }

Server → Client binary:
  MP3 audio chunks (one blob per sentence, followed by sentence_end JSON)
"""
import json
import logging
import re

from fastapi import WebSocket, WebSocketDisconnect
from fastapi.routing import APIRouter

from orchestration import get_next_turn, submit_code, end_interview, start_interview
from repositories.interview_repo import get_interview
from services.stt_service import transcribe_pcm
from services.tts_service import stream_tts

logger = logging.getLogger(__name__)

ws_router = APIRouter()

_CODE_TRIGGER_RE = re.compile(
    r"(open the code|coding (problem|question|challenge)|write (a |the )?code|"
    r"implement|solve|let('s| us) code|code pad|editor)",
    re.IGNORECASE,
)


async def _send_json(ws: WebSocket, data: dict):
    await ws.send_text(json.dumps(data))


async def _tts_and_send(ws: WebSocket, text: str):
    """Synthesise text sentence-by-sentence and stream MP3 to client."""
    async for audio_bytes in stream_tts(text):
        try:
            await ws.send_bytes(audio_bytes)
            await _send_json(ws, {"type": "sentence_end"})
        except (WebSocketDisconnect, RuntimeError):
            return


@ws_router.websocket("/ws/interview/{interview_id}")
async def interview_ws(websocket: WebSocket, interview_id: str):
    await websocket.accept()

    # ── Validate interview ──────────────────────────────────────
    interview = get_interview(interview_id)
    if not interview:
        await _send_json(websocket, {"type": "error", "message": "Interview not found"})
        await websocket.close()
        return

    # ── Find or create session ──────────────────────────────────
    from config.db import get_db
    from models import SESSION_COLLECTION

    db = get_db()
    existing = db[SESSION_COLLECTION].find_one({"interview_id": interview_id})

    if existing:
        session_id = str(existing["_id"])
        # Replay existing transcript so UI restores history
        for entry in existing.get("transcript", []):
            msg_type = "ai_transcript" if entry["role"] == "agent" else "user_transcript"
            await _send_json(websocket, {"type": msg_type, "text": entry["text"]})
        first_message = None
    else:
        try:
            result = await start_interview(interview_id=interview_id)
        except Exception as e:
            await _send_json(websocket, {"type": "error", "message": f"Could not start interview: {e}"})
            await websocket.close()
            return
        session_id = result["session_id"]
        first_message = result.get("agent_message", "")

    coding_question = interview.get("coding_question") or {}
    logger.info("Interview WS connected: interview=%s session=%s", interview_id, session_id)

    # ── Send initial greeting (with TTS) ───────────────────────
    if first_message:
        await _send_json(websocket, {"type": "ai_transcript", "text": first_message})
        await _tts_and_send(websocket, first_message)

    await _send_json(websocket, {"type": "ready"})

    # ── Main message loop ───────────────────────────────────────
    audio_buffer = bytearray()
    code_triggered = False

    try:
        while True:
            message = await websocket.receive()

            # Binary = PCM audio chunk
            if message.get("bytes") is not None:
                audio_buffer.extend(message["bytes"])
                continue

            # Text = JSON control
            raw = message.get("text")
            if raw is None:
                continue
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                continue

            msg_type = data.get("type")

            # ── audio_end ─────────────────────────────────────
            if msg_type == "audio_end":
                pcm = bytes(audio_buffer)
                audio_buffer.clear()
                if not pcm:
                    continue

                try:
                    user_text = await transcribe_pcm(pcm)
                except Exception as e:
                    logger.error("STT error: %s", e)
                    await _send_json(websocket, {"type": "error", "message": f"STT failed: {e}"})
                    continue

                if not user_text:
                    continue

                await _send_json(websocket, {"type": "user_transcript", "text": user_text})
                await _send_json(websocket, {"type": "ai_thinking"})

                try:
                    turn = await get_next_turn(session_id=session_id, candidate_message=user_text)
                    agent_msg = turn.get("agent_message", "")
                except Exception as e:
                    logger.error("Agent error: %s", e)
                    await _send_json(websocket, {"type": "error", "message": f"Agent error: {e}"})
                    continue

                await _send_json(websocket, {"type": "ai_transcript", "text": agent_msg})
                await _tts_and_send(websocket, agent_msg)

                if not code_triggered and _CODE_TRIGGER_RE.search(agent_msg) and coding_question.get("title"):
                    code_triggered = True
                    await _send_json(websocket, {"type": "trigger_code", "question": coding_question})

            # ── code_submit ───────────────────────────────────
            elif msg_type == "code_submit":
                code = data.get("code", "")
                language = data.get("language", "python")
                await _send_json(websocket, {"type": "ai_thinking"})

                try:
                    res = await submit_code(session_id=session_id, code=code, language=language)
                except Exception as e:
                    logger.error("Code eval error: %s", e)
                    await _send_json(websocket, {"type": "error", "message": f"Code eval failed: {e}"})
                    continue

                agent_msg = res.get("agent_message", "")
                await _send_json(websocket, {
                    "type": "code_result",
                    "evaluation": res.get("evaluation", {}),
                    "agent_message": agent_msg,
                })
                await _send_json(websocket, {"type": "ai_transcript", "text": agent_msg})
                await _tts_and_send(websocket, agent_msg)

            # ── end_interview ─────────────────────────────────
            elif msg_type == "end_interview":
                await _send_json(websocket, {"type": "ai_thinking"})
                try:
                    res = await end_interview(session_id=session_id)
                except Exception as e:
                    logger.error("End interview error: %s", e)
                    await _send_json(websocket, {"type": "error", "message": str(e)})
                    continue

                await _send_json(websocket, {
                    "type": "interview_end",
                    "report_id": res.get("report_id"),
                    "verdict": res.get("verdict"),
                })
                break

    except WebSocketDisconnect:
        logger.info("Interview WS disconnected: interview=%s", interview_id)
    except RuntimeError as e:
        # Starlette raises RuntimeError instead of WebSocketDisconnect when the
        # client disconnects while we're doing async work outside receive()
        # (e.g. during TTS streaming).  Treat it as a normal disconnect.
        if "disconnect" in str(e).lower():
            logger.info("Interview WS disconnected (runtime): interview=%s", interview_id)
        else:
            logger.error("Interview WS error: %s", e, exc_info=True)
            try:
                await _send_json(websocket, {"type": "error", "message": str(e)})
            except Exception:
                pass
    except Exception as e:
        logger.error("Interview WS error: %s", e, exc_info=True)
        try:
            await _send_json(websocket, {"type": "error", "message": str(e)})
        except Exception:
            pass
