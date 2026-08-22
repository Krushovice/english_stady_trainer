import { useEffect, useRef, useState } from "react";

type RecorderState = "idle" | "recording" | "recorded";

// MediaRecorder's default output MIME type is browser-chosen (audio/webm in
// Chrome/Firefox, audio/mp4 in Safari) — pass whatever it produces straight
// through rather than guessing a fixed type, and derive the filename
// extension from it so the upload's Content-Type/filename stay consistent.
function pickMimeType(): string {
  const candidates = ["audio/webm", "audio/mp4", "audio/ogg"];
  for (const type of candidates) {
    if (MediaRecorder.isTypeSupported(type)) return type;
  }
  return "";
}

export function AudioRecorder({
  onSubmit,
  submitting,
}: {
  onSubmit: (audio: Blob, filename: string) => void;
  submitting: boolean;
}) {
  const [state, setState] = useState<RecorderState>("idle");
  const [error, setError] = useState<string | null>(null);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const blobRef = useRef<Blob | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
      streamRef.current?.getTracks().forEach((track) => track.stop());
      if (audioUrl) URL.revokeObjectURL(audioUrl);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function startRecording() {
    setError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      const mimeType = pickMimeType();
      const recorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined);
      chunksRef.current = [];

      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) chunksRef.current.push(event.data);
      };
      recorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: mimeType || "audio/webm" });
        blobRef.current = blob;
        setAudioUrl(URL.createObjectURL(blob));
        stream.getTracks().forEach((track) => track.stop());
        streamRef.current = null;
        setState("recorded");
      };

      mediaRecorderRef.current = recorder;
      recorder.start();
      setElapsedSeconds(0);
      timerRef.current = setInterval(() => setElapsedSeconds((s) => s + 1), 1000);
      setState("recording");
    } catch {
      setError("Не удалось получить доступ к микрофону. Проверьте разрешение браузера и попробуйте снова.");
    }
  }

  function stopRecording() {
    if (timerRef.current) clearInterval(timerRef.current);
    mediaRecorderRef.current?.stop();
  }

  function recordAgain() {
    if (audioUrl) URL.revokeObjectURL(audioUrl);
    blobRef.current = null;
    setAudioUrl(null);
    setState("idle");
  }

  function handleSubmit() {
    if (!blobRef.current) return;
    const extension = (mediaRecorderRef.current?.mimeType || "audio/webm").split("/")[1];
    onSubmit(blobRef.current, `recording.${extension}`);
  }

  const minutes = String(Math.floor(elapsedSeconds / 60)).padStart(2, "0");
  const seconds = String(elapsedSeconds % 60).padStart(2, "0");

  return (
    <div className="audio-recorder">
      {error && <p className="status status-error">{error}</p>}

      {state === "idle" && (
        <button type="button" className="btn-primary" onClick={startRecording}>
          🎙 Начать запись
        </button>
      )}

      {state === "recording" && (
        <div className="audio-recorder-active">
          <span className="audio-recorder-timer">
            ● {minutes}:{seconds}
          </span>
          <button type="button" onClick={stopRecording}>
            Стоп
          </button>
        </div>
      )}

      {state === "recorded" && audioUrl && (
        <div className="audio-recorder-preview">
          {/* eslint-disable-next-line jsx-a11y/media-has-caption */}
          <audio src={audioUrl} controls />
          <div className="audio-recorder-actions">
            <button type="button" onClick={recordAgain} disabled={submitting}>
              Записать заново
            </button>
            <button type="button" className="btn-primary" onClick={handleSubmit} disabled={submitting}>
              {submitting ? "Отправка..." : "Отправить"}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
