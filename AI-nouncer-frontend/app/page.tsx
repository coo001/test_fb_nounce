"use client";

import { useEffect, useState } from "react";
import SentenceInput from "@/components/SentenceInput";
import Recorder from "@/components/Recorder";
import ResultCard from "@/components/ResultCard";
import { fetchSentences, analyzeFree } from "@/lib/api";
import { AnalysisResponse, Sentence } from "@/types/analysis";

type Stage = "select" | "recording" | "result";

export default function Home() {
  const [sentences, setSentences] = useState<Sentence[]>([]);
  const [stage, setStage] = useState<Stage>("select");
  const [selected, setSelected] = useState<Sentence | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AnalysisResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchSentences()
      .then(setSentences)
      .catch(() => setError("문장 목록을 불러오지 못했습니다. 백엔드가 실행 중인지 확인하세요."));
  }, []);

  function handleSelect(sentence: Sentence) {
    setSelected(sentence);
    setResult(null);
    setError(null);
    setStage("recording");
  }

  async function handleAudio(blob: Blob) {
    if (!selected) return;
    setLoading(true);
    setError(null);
    try {
      const data = await analyzeFree(blob, selected.text);
      setResult(data);
      setStage("result");
    } catch (e) {
      setError(e instanceof Error ? e.message : "분석 중 오류가 발생했습니다.");
      setStage("recording");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-white flex flex-col items-center justify-center px-4 py-12">
      {error && (
        <div className="mb-6 w-full max-w-lg bg-red-50 border border-red-200 rounded-xl px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {stage === "select" && (
        <SentenceInput sentences={sentences} onSelect={handleSelect} />
      )}

      {stage === "recording" && selected && (
        <Recorder
          sentence={selected.text}
          onResult={handleAudio}
          loading={loading}
        />
      )}

      {stage === "result" && result && selected && (
        <ResultCard
          sentence={selected.text}
          result={result}
          onRetry={() => setStage("recording")}
          onNew={() => setStage("select")}
        />
      )}
    </main>
  );
}
