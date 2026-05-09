"use client";

import { Sentence } from "@/types/analysis";

interface Props {
  sentences: Sentence[];
  onSelect: (sentence: Sentence) => void;
}

export default function SentenceInput({ sentences, onSelect }: Props) {
  return (
    <div className="flex flex-col gap-6 w-full max-w-lg">
      <div className="text-center">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">AI-nouncer</h1>
        <p className="text-gray-500 text-sm">
          연습할 문장을 선택하고 녹음하면 발음 피드백을 드립니다
        </p>
      </div>

      <div className="flex flex-col gap-3">
        {sentences.map((s, i) => (
          <button
            key={s.id}
            onClick={() => onSelect(s)}
            className="flex items-center gap-4 text-left bg-gray-50 hover:bg-blue-50 border border-gray-200 hover:border-blue-300 rounded-xl px-5 py-4 transition-colors group"
          >
            <span className="text-xs font-bold text-gray-400 group-hover:text-blue-400 w-5 shrink-0">
              {i + 1}
            </span>
            <span className="text-base text-gray-800">{s.text}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
