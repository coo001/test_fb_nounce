"use client";

import { LengthTier, Sentence } from "@/types/analysis";

interface Props {
  sentences: Sentence[];
  onSelect: (sentence: Sentence) => void;
}

const TIER_ORDER: LengthTier[] = ["short", "long", "paragraph"];
const TIER_META: Record<LengthTier, { label: string; hint: string }> = {
  short: { label: "짧은 문장", hint: "10~20자 — 빠른 워밍업" },
  long: { label: "긴 문장", hint: "25~35자 — 다양한 발음 변별" },
  paragraph: { label: "문단", hint: "긴 호흡으로 종합 연습" },
};

export default function SentenceInput({ sentences, onSelect }: Props) {
  const grouped: Record<LengthTier, Sentence[]> = {
    short: [],
    long: [],
    paragraph: [],
  };
  sentences.forEach((s) => {
    const tier = (s.length_tier ?? "short") as LengthTier;
    grouped[tier].push(s);
  });

  return (
    <div className="flex flex-col gap-8 w-full max-w-lg">
      <div className="text-center">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">AI-nouncer</h1>
        <p className="text-gray-500 text-sm">
          연습할 문장을 선택하고 녹음하면 발음 피드백을 드립니다
        </p>
      </div>

      {TIER_ORDER.map((tier) => {
        const items = grouped[tier];
        if (items.length === 0) return null;
        const meta = TIER_META[tier];
        return (
          <section key={tier} className="flex flex-col gap-3">
            <div className="flex items-baseline justify-between border-b border-gray-200 pb-1">
              <h2 className="text-sm font-bold text-gray-700">{meta.label}</h2>
              <span className="text-xs text-gray-400">{meta.hint}</span>
            </div>
            <div className="flex flex-col gap-2">
              {items.map((s, i) => (
                <button
                  key={s.id}
                  onClick={() => onSelect(s)}
                  className="flex items-start gap-4 text-left bg-gray-50 hover:bg-blue-50 border border-gray-200 hover:border-blue-300 rounded-xl px-5 py-4 transition-colors group"
                >
                  <span className="text-xs font-bold text-gray-400 group-hover:text-blue-400 w-6 shrink-0 mt-0.5">
                    {i + 1}
                  </span>
                  <span className="text-base text-gray-800 leading-relaxed">{s.text}</span>
                </button>
              ))}
            </div>
          </section>
        );
      })}
    </div>
  );
}
