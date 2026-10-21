"use client";

import { useEffect, useState } from "react";
import { AnalysisResponse } from "@/types/analysis";
import FeedbackForm from "@/components/FeedbackForm";

interface Props {
  sentence: string;
  sentenceId?: string;
  result: AnalysisResponse;
  audioBlob: Blob | null;
  sessionId: string;
  onRetry: () => void;
  onNew: () => void;
}

const UNCLEAR_TYPES = new Set(["ㅅ 계열 불명확", "종성 약화/탈락", "종성 약화", "sub"]);

export default function ResultCard({ sentence, sentenceId, result, audioBlob, sessionId, onRetry, onNew }: Props) {
  const { transcript, alignment, candidates, advice, next_practice, relevance } = result;

  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  useEffect(() => {
    if (!audioBlob) {
      setAudioUrl(null);
      return;
    }
    const url = URL.createObjectURL(audioBlob);
    setAudioUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [audioBlob]);

  const isUnrelated = relevance?.label === "unrelated";

  return (
    <div className="flex flex-col gap-6 w-full max-w-lg">
      <div className="text-center">
        <p className="text-xs text-gray-400 uppercase tracking-wide mb-1">원문</p>
        <p className="text-lg font-semibold text-gray-700">{sentence}</p>
      </div>

      {/* 무관도 경고 (전혀 다른 문장이 인식된 경우) */}
      {isUnrelated && (
        <div className="bg-amber-50 border-2 border-amber-300 rounded-xl p-5 flex flex-col gap-2">
          <p className="text-sm font-bold text-amber-700">⚠ 원문과 다른 음성으로 인식되었습니다</p>
          <p className="text-sm text-amber-800">
            정렬 일치율 {Math.round((relevance.match_ratio ?? 0) * 100)}%
            ({relevance.match_syllables}/{relevance.expected_syllables} 음절 일치).
            원문과 다른 문장을 읽으셨거나, 마이크/주변 환경 문제로 인식이 어려운 상태일 수 있습니다.
          </p>
        </div>
      )}

      {/* 내가 녹음한 음성 */}
      {audioUrl && (
        <div className="bg-gray-50 rounded-xl p-4">
          <p className="text-xs text-gray-400 uppercase tracking-wide mb-2">내가 녹음한 음성</p>
          <audio controls src={audioUrl} className="w-full" />
        </div>
      )}

      {/* STT가 들은 텍스트 */}
      <div className="bg-gray-50 rounded-xl p-4">
        <p className="text-xs text-gray-400 uppercase tracking-wide mb-2">STT가 들은 텍스트</p>
        <p className="text-base text-gray-800">{transcript}</p>
        {relevance && !isUnrelated && (
          <p className="text-xs text-gray-400 mt-2">
            일치율 {Math.round(relevance.match_ratio * 100)}% — {relevance.label === "match" ? "정상" : "일부 불명확"}
          </p>
        )}
      </div>

      {/* 음절 비교 — unrelated 인 경우 큰 의미가 없으므로 숨김 */}
      {!isUnrelated && alignment.length > 0 && (
        <div className="bg-gray-50 rounded-xl p-4">
          <p className="text-xs text-gray-400 uppercase tracking-wide mb-3">음절 비교</p>
          <div className="flex flex-wrap gap-1">
            {alignment.map((item, i) => {
              const isUnclear = UNCLEAR_TYPES.has(item.type);
              return (
                <span
                  key={i}
                  title={isUnclear ? `들린 발음: ${item.heard} (${item.type})` : undefined}
                  className={`inline-block px-2 py-1 rounded-md text-sm font-medium ${
                    isUnclear
                      ? "bg-red-100 text-red-700 border border-red-300"
                      : "bg-white text-gray-700 border border-gray-200"
                  }`}
                >
                  {item.expected}
                  {isUnclear && (
                    <span className="text-xs ml-0.5 opacity-60">→{item.heard}</span>
                  )}
                </span>
              );
            })}
          </div>
          {candidates.length === 0 && (
            <p className="text-sm text-green-600 mt-2">불명확한 음절이 없습니다 🎉</p>
          )}
        </div>
      )}

      {/* 피드백 */}
      <div className={`rounded-xl p-4 flex flex-col gap-2 border ${
        isUnrelated
          ? "bg-gray-50 border-gray-200"
          : "bg-blue-50 border-blue-200"
      }`}>
        <p className={`text-xs uppercase tracking-wide ${isUnrelated ? "text-gray-400" : "text-blue-400"}`}>
          {isUnrelated ? "안내" : "피드백"}
        </p>
        <p className={`text-base font-medium ${isUnrelated ? "text-gray-800" : "text-blue-900"}`}>
          {advice.focus}
        </p>
      </div>

      {/* 연습 방법 */}
      {advice.drills.length > 0 && (
        <div className="bg-gray-50 rounded-xl p-4">
          <p className="text-xs text-gray-400 uppercase tracking-wide mb-3">연습 방법</p>
          <ul className="flex flex-col gap-2">
            {advice.drills.map((drill, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-gray-700">
                <span className="text-blue-500 font-bold mt-0.5">{i + 1}.</span>
                {drill}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* 연습 단어 */}
      {!isUnrelated && next_practice?.practice_words?.length > 0 && (
        <div className="bg-gray-50 rounded-xl p-4">
          <p className="text-xs text-gray-400 uppercase tracking-wide mb-2">
            {next_practice.mode === "challenge" ? "다음 도전 단어" : "연습 단어"}
          </p>
          <div className="flex flex-wrap gap-2">
            {next_practice.practice_words.map((w, i) => (
              <span
                key={i}
                className="inline-block px-3 py-1 bg-white border border-gray-200 rounded-md text-sm text-gray-700"
              >
                {w}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* 다음 연습 문장 — remediation: 황색, challenge: 녹색 */}
      {!isUnrelated && next_practice?.next_sentence && (
        <div
          className={
            next_practice.mode === "challenge"
              ? "bg-emerald-50 border border-emerald-200 rounded-xl p-4"
              : "bg-amber-50 border border-amber-200 rounded-xl p-4"
          }
        >
          <p
            className={
              next_practice.mode === "challenge"
                ? "text-xs text-emerald-600 uppercase tracking-wide mb-2"
                : "text-xs text-amber-500 uppercase tracking-wide mb-2"
            }
          >
            {next_practice.mode === "challenge" ? "잘하셨어요 — 다음 도전 문장" : "다음 연습 문장"}
          </p>
          <p
            className={
              next_practice.mode === "challenge"
                ? "text-lg font-semibold text-emerald-900"
                : "text-lg font-semibold text-amber-900"
            }
          >
            {next_practice.next_sentence}
          </p>
        </div>
      )}

      {/* 평가 위젯 */}
      {sessionId && (
        <FeedbackForm
          sessionId={sessionId}
          sentenceId={sentenceId}
          expectedText={sentence}
          perceivedText={transcript}
          relevanceLabel={relevance?.label}
        />
      )}

      {/* 버튼 */}
      <div className="flex gap-3">
        <button
          onClick={onRetry}
          className="flex-1 bg-gray-700 hover:bg-gray-800 text-white font-semibold py-3 rounded-xl transition-colors"
        >
          다시 녹음
        </button>
        <button
          onClick={onNew}
          className="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 rounded-xl transition-colors"
        >
          새 문장
        </button>
      </div>
    </div>
  );
}
