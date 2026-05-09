"use client";

import { useRef, useState } from "react";

interface Props {
  sentence: string;
  onResult: (blob: Blob) => void;
  loading: boolean;
}

export default function Recorder({ sentence, onResult, loading }: Props) {
  const [recording, setRecording] = useState(false);
  const mediaRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  async function startRecording() {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

    const mimeType = MediaRecorder.isTypeSupported("audio/webm")
      ? "audio/webm"
      : "audio/mp4";

    const recorder = new MediaRecorder(stream, { mimeType });
    chunksRef.current = [];

    recorder.ondataavailable = (e) => {
      if (e.data.size > 0) chunksRef.current.push(e.data);
    };

    recorder.onstop = () => {
      stream.getTracks().forEach((t) => t.stop());
      const blob = new Blob(chunksRef.current, { type: mimeType });
      onResult(blob);
    };

    recorder.start();
    mediaRef.current = recorder;
    setRecording(true);
  }

  function stopRecording() {
    mediaRef.current?.stop();
    setRecording(false);
  }

  function toggle() {
    if (recording) stopRecording();
    else startRecording();
  }

  return (
    <div className="flex flex-col items-center gap-8 w-full max-w-lg">
      <div className="text-center">
        <p className="text-xs text-gray-400 uppercase tracking-wide mb-2">읽을 문장</p>
        <p className="text-2xl font-semibold text-gray-800 leading-relaxed">{sentence}</p>
      </div>

      {loading ? (
        <div className="flex flex-col items-center gap-3">
          <div className="w-16 h-16 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin" />
          <p className="text-sm text-gray-500">분석 중입니다…</p>
        </div>
      ) : (
        <button
          onClick={toggle}
          className={`w-20 h-20 rounded-full flex items-center justify-center text-white text-2xl transition-all shadow-lg ${
            recording
              ? "bg-red-500 hover:bg-red-600 animate-pulse"
              : "bg-gray-700 hover:bg-gray-800"
          }`}
          title={recording ? "녹음 중지" : "녹음 시작"}
        >
          {recording ? "■" : "●"}
        </button>
      )}

      {recording && (
        <p className="text-sm text-red-500 font-medium animate-pulse">● 녹음 중 — 버튼을 눌러 중지</p>
      )}
      {!recording && !loading && (
        <p className="text-sm text-gray-400">버튼을 눌러 녹음을 시작하세요</p>
      )}
    </div>
  );
}
