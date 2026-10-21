"use client";

import { useState } from "react";
import { submitFeedback } from "@/lib/api";

interface Props {
  sessionId: string;
  sentenceId?: string;
  expectedText: string;
  perceivedText: string;
  relevanceLabel?: string;
}

const QUESTIONS: { key: keyof Ratings; label: string }[] = [
  { key: "q1_understood_problem", label: "어느 부분이 문제인지 이해할 수 있었다" },
  { key: "q2_actionable", label: "다음 녹음에서 무엇을 바꿔야 할지 알 수 있었다" },
  { key: "q3_practice_helpful", label: "제시된 연습 문장이 도움이 되었다" },
  { key: "q4_tone_ok", label: "피드백이 너무 단정적이거나 불쾌하지 않았다" },
  { key: "q5_would_reuse", label: "다시 사용해보고 싶다" },
];

interface Ratings {
  q1_understood_problem: number;
  q2_actionable: number;
  q3_practice_helpful: number;
  q4_tone_ok: number;
  q5_would_reuse: number;
}

export default function FeedbackForm({
  sessionId,
  sentenceId,
  expectedText,
  perceivedText,
  relevanceLabel,
}: Props) {
  const [ratings, setRatings] = useState<Partial<Ratings>>({});
  const [comment, setComment] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [done, setDone] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const allFilled = QUESTIONS.every((q) => ratings[q.key]);

  function setScore(key: keyof Ratings, score: number) {
    setRatings((r) => ({ ...r, [key]: score }));
  }

  async function handleSubmit() {
    if (!allFilled) return;
    setSubmitting(true);
    setError(null);
    try {
      await submitFeedback({
        session_id: sessionId,
        sentence_id: sentenceId,
        expected_text: expectedText,
        perceived_text: perceivedText,
        relevance_label: relevanceLabel,
        ratings: ratings as Ratings,
        comment: comment.trim() || undefined,
      });
      setDone(true);
    } catch (e) {
      setError(e instanceof Error ? e.message : "제출 실패");
    } finally {
      setSubmitting(false);
    }
  }

  if (done) {
    return (
      <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-4 text-center">
        <p className="text-sm text-emerald-800 font-medium">평가 감사합니다 🙏</p>
      </div>
    );
  }

  return (
    <div className="bg-gray-50 border border-gray-200 rounded-xl p-4 flex flex-col gap-4">
      <div>
        <p className="text-xs text-gray-400 uppercase tracking-wide">피드백 평가</p>
        <p className="text-sm text-gray-600 mt-1">
          이번 분석이 얼마나 도움이 되었는지 1~5점으로 평가해 주세요.
        </p>
      </div>

      <div className="flex flex-col gap-3">
        {QUESTIONS.map((q) => (
          <div key={q.key} className="flex items-center justify-between gap-3">
            <span className="text-sm text-gray-700 flex-1">{q.label}</span>
            <div className="flex gap-1">
              {[1, 2, 3, 4, 5].map((n) => {
                const active = ratings[q.key] === n;
                return (
                  <button
                    key={n}
                    onClick={() => setScore(q.key, n)}
                    className={`w-8 h-8 rounded-md text-sm font-semibold border transition-colors ${
                      active
                        ? "bg-blue-600 text-white border-blue-600"
                        : "bg-white text-gray-500 border-gray-200 hover:border-blue-300"
                    }`}
                  >
                    {n}
                  </button>
                );
              })}
            </div>
          </div>
        ))}
      </div>

      <textarea
        value={comment}
        onChange={(e) => setComment(e.target.value)}
        placeholder="자유 코멘트 (선택)"
        rows={2}
        className="w-full text-sm text-gray-700 bg-white border border-gray-200 rounded-md px-3 py-2 resize-none focus:outline-none focus:border-blue-300"
      />

      {error && (
        <p className="text-xs text-red-600">{error}</p>
      )}

      <button
        onClick={handleSubmit}
        disabled={!allFilled || submitting}
        className={`py-2 rounded-md text-sm font-semibold transition-colors ${
          !allFilled || submitting
            ? "bg-gray-200 text-gray-400 cursor-not-allowed"
            : "bg-blue-600 text-white hover:bg-blue-700"
        }`}
      >
        {submitting ? "제출 중…" : allFilled ? "평가 제출" : "5문항을 모두 선택해 주세요"}
      </button>
    </div>
  );
}
