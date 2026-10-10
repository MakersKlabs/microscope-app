"""Registratore video compresso basato su PyAV (FFmpeg).

I frame BGR provenienti dal thread di acquisizione vengono accodati e codificati
in un thread separato, così da non rallentare l'anteprima. Se il codificatore
non riesce a stare al passo, i frame in eccesso vengono scartati.
"""

from __future__ import annotations

import queue
import threading
import time
from fractions import Fraction

#: Sequenza di codificatori provata in ordine di preferenza.
CODEC_FALLBACKS = ("libx264", "libx265", "mpeg4", "mpeg2video")

CODEC_LABELS = {
    "libx264": "H.264 (x264)",
    "libx265": "H.265 (x265)",
    "mpeg4": "MPEG-4",
    "mpeg2video": "MPEG-2",
}


def available_encoders() -> list:
    """Restituisce i codificatori realmente disponibili."""
    try:
        import av
    except Exception:
        return []
    found = []
    for name in CODEC_FALLBACKS:
        try:
            av.codec.Codec(name, "w")
        except Exception:
            continue
        found.append(name)
    return found


class VideoRecorder:
    """Codifica una sequenza di frame in un file compresso."""

    def __init__(
        self,
        path: str,
        width: int,
        height: int,
        fps: float = 30.0,
        codec: str = "libx264",
        crf: int = 23,
        preset: str = "veryfast",
    ) -> None:
        self.path = path
        # yuv420p richiede dimensioni pari.
        self.width = int(width) - (int(width) % 2)
        self.height = int(height) - (int(height) % 2)
        self.fps = float(fps) if fps and fps > 0 else 30.0
        self.codec = codec
        self.crf = int(crf)
        self.preset = preset

        self.error: str | None = None
        self.frames_written = 0
        self.frames_dropped = 0

        self._queue: "queue.Queue" = queue.Queue(maxsize=8)
        self._thread = threading.Thread(
            target=self._run, name="microscope-recorder", daemon=True
        )
        self._started = False

    # -- API pubblica ------------------------------------------------------
    def start(self) -> None:
        if not self._started:
            self._thread.start()
            self._started = True

    def submit(self, frame) -> None:
        """Accoda un frame (BGR). Scarta il frame più vecchio se pieno."""
        try:
            self._queue.put_nowait(frame)
        except queue.Full:
            self.frames_dropped += 1

    def close(self) -> None:
        if not self._started:
            return
        # Sentinella di fine stream; se la coda è piena rimuoviamo un frame.
        while True:
            try:
                self._queue.put_nowait(None)
                break
            except queue.Full:
                try:
                    self._queue.get_nowait()
                except queue.Empty:
                    pass
        self._thread.join(timeout=15)

    # -- Interno -----------------------------------------------------------
    def _pick_codec(self):
        import av

        for name in (self.codec, *CODEC_FALLBACKS):
            if not name:
                continue
            try:
                av.codec.Codec(name, "w")
                return name
            except Exception:
                continue
        return "mpeg4"

    def _run(self) -> None:
        try:
            import av
        except Exception as exc:  # pragma: no cover - dipendenza mancante
            self.error = f"PyAV non disponibile: {exc}"
            return

        container = None
        try:
            codec = self._pick_codec()
            container = av.open(self.path, mode="w")
            stream = container.add_stream(codec, rate=int(round(self.fps)) or 30)
            stream.width = self.width
            stream.height = self.height
            stream.pix_fmt = "yuv420p"
            stream.time_base = Fraction(1, 1000)

            if codec in ("libx264", "libx265"):
                stream.options = {
                    "preset": self.preset,
                    "crf": str(self.crf),
                }
            elif codec == "mpeg4":
                stream.options = {"qscale": str(max(1, min(31, self.crf)))}
            elif codec == "mpeg2video":
                stream.options = {"qscale": str(max(1, min(31, self.crf)))}

            start = time.monotonic()
            while True:
                frame = self._queue.get()
                if frame is None:
                    break
                # Ritaglio di sicurezza per dimensioni pari.
                if frame.shape[1] > self.width or frame.shape[0] > self.height:
                    frame = frame[: self.height, : self.width]
                video_frame = av.VideoFrame.from_ndarray(frame, format="bgr24")
                video_frame.pts = int((time.monotonic() - start) * 1000)
                video_frame.time_base = Fraction(1, 1000)
                for packet in stream.encode(video_frame):
                    container.mux(packet)
                self.frames_written += 1

            for packet in stream.encode(None):
                container.mux(packet)
        except Exception as exc:
            self.error = f"Errore di registrazione: {exc}"
        finally:
            if container is not None:
                try:
                    container.close()
                except Exception:
                    pass
