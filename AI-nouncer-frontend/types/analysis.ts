export interface Sentence {
  id: string;
  text: string;
}

export interface AlignmentItem {
  expected: string;
  heard: string;
  type: string; // "match" | "ㅅ 계열 불명확" | "종성 약화" | "sub" | "ins" | "del"
}

export interface Candidate {
  index: number;
  expected: string;
  heard: string;
  type: string;
}

export interface Advice {
  focus: string;
  drills: string[];
  next_sentence?: string;
}

export interface AnalysisResponse {
  transcript: string;
  alignment: AlignmentItem[];
  candidates: Candidate[];
  advice: Advice;
}
