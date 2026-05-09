import { AnalysisResponse, Sentence } from "@/types/analysis";

const BACKEND = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";

export async function fetchSentences(): Promise<Sentence[]> {
  const res = await fetch(`${BACKEND}/api/v1/sentences`);
  if (!res.ok) throw new Error("문장 목록을 불러오지 못했습니다.");
  return res.json();
}

export async function analyzeFree(
  audioBlob: Blob,
  sentenceText: string
): Promise<AnalysisResponse> {
  const form = new FormData();
  form.append("audio", audioBlob, "audio.webm");
  form.append("sentence_text", sentenceText);

  const res = await fetch(`${BACKEND}/api/v1/analyze/free`, {
    method: "POST",
    body: form,
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `HTTP ${res.status}`);
  }

  return res.json();
}
