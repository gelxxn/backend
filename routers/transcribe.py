import numpy as np
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from config import whisper_model

router = APIRouter(tags=["Transcribe"])


@router.websocket("/stream-transcribe")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("Flutter connected to Streaming STT!")

    audio_buffer = bytearray()

    try:
        while True:
            chunk = await websocket.receive_bytes()
            audio_buffer.extend(chunk)

            if len(audio_buffer) >= 32000:
                audio_np = (
                    np.frombuffer(audio_buffer, dtype=np.int16)
                    .astype(np.float32) / 32768.0
                )
                segments, _ = whisper_model.transcribe(
                    audio_np, beam_size=5, language="th"
                )
                text_result = "".join(s.text for s in segments).strip()
                audio_buffer.clear()

                if text_result:
                    await websocket.send_text(text_result)

    except WebSocketDisconnect:
        print("Flutter disconnected.")
    except Exception as e:
        print(f"Error: {e}")
        try:
            await websocket.send_text(f"(เกิดข้อผิดพลาด: {str(e)})")
        except Exception:
            pass