import api from "./index";

export interface EvaluationResult {
  id: number;
  test_run_id: number;
  judge_type: string;
  overall_score: number;
  accuracy_score: number | null;
  hallucination_score: number | null;
  tool_correctness_score: number | null;
  expression_quality_score: number | null;
  judge_reasoning: string;
  rule_results: Record<string, unknown>[] | null;
  created_at: string;
}

export const evaluateRun = (test_run_id: number, rules?: unknown[], use_llm_judge?: boolean) =>
  api.post<EvaluationResult>("/api/evaluations/", { test_run_id, rules, use_llm_judge }).then((r) => r.data);

export const getEvaluations = (testRunId: number) =>
  api.get<EvaluationResult[]>(`/api/evaluations/run/${testRunId}`).then((r) => r.data);
