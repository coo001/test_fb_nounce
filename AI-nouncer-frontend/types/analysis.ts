export interface Sentence {
  id: string;
  text: string;
}

export interface AlignmentItem {
  expected: string;
  heard: string;
  type: string;
}

export interface Candidate {
  index: number;
  expected: string;
  heard: string;
  type: string;
  pattern_id?: string | null;
}

export interface Classification {
  position: number;
  pattern_id: string;
  evidence: string;
  confidence: number;
  source: "rule" | "llm";
}

export interface Advice {
  focus: string;
  drills: string[];
}

export interface NextPractice {
  focus_pattern_id?: string | null;
  practice_words: string[];
  next_sentence?: string | null;
}

export interface Relevance {
  label: "match" | "partial" | "unrelated";
  match_ratio: number;
  expected_syllables: number;
  match_syllables: number;
}

export interface AnalysisResponse {
  transcript: string;
  alignment: AlignmentItem[];
  candidates: Candidate[];
  classifications: Classification[];
  advice: Advice;
  next_practice: NextPractice;
  relevance: Relevance;
}
