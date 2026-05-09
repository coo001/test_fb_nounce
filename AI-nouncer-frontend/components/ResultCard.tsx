"use client";

import { AnalysisResponse } from "@/types/analysis";

interface Props {
  sentence: string;
  result: AnalysisResponse;
  onRetry: () => void;
  onNew: () => void;
}

const UNCLEAR_TYPES = new Set(["ㅅ 계열 불명확", "종성 약화", "sub"]);

export default function ResultCard({ sentence, result, onRetry, onNew }: Props) {
  const { transcript, alignment, candidates, advice } = result;

  return (
    <div className="flex flex-col gap-6 w-full max-w-lg">
      <div className="text-center">
        <p className="text-xs text-gray-400 uppercase tracking-wide mb-1">원문</p>
        <p className="text-lg font-semibold text-gray-700">{sentence}</p>
      </div>

      {/* 나의 발음 */}
      <div className="bg-gray-50 rounded-xl p-4">
        <p className="text-xs text-gray-400 uppercase tracking-wide mb-2">나의 발음</p>
        <p className="text-base text-gray-800">{transcript}</p>
      </div>

      {/* 음절 비교 */}
      {alignment.length > 0 && (
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
      <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 flex flex-col gap-2">
        <p className="text-xs text-blue-400 uppercase tracking-wide">피드백</p>
        <p className="text-base text-blue-900 font-medium">{advice.focus}</p>
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

      {/* 다음 연습 문장 */}
      {advice.next_sentence && (
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-4">
          <p className="text-xs text-amber-500 uppercase tracking-wide mb-2">다음 연습 문장</p>
          <p className="text-lg font-semibold text-amber-900">{advice.next_sentence}</p>
        </div>
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
