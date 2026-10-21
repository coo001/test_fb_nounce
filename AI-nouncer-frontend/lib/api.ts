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

export interface FeedbackRatings {
  q1_understood_problem: number;
  q2_actionable: number;
  q3_practice_helpful: number;
  q4_tone_ok: number;
  q5_would_reuse: number;
}

export interface FeedbackPayload {
  session_id?: string;
  sentence_id?: string;
  expected_text?: string;
  perceived_text?: string;
  relevance_label?: string;
  ratings: FeedbackRatings;
  comment?: string;
}

export async function submitFeedback(payload: FeedbackPayload): Promise<void> {
  const res = await fetch(`${BACKEND}/api/v1/feedback`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `HTTP ${res.status}`);
  }
}
