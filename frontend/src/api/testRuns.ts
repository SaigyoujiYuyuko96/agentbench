import api from "./index";

export interface RunStep {
  id: number;
  sequence: number;
  step_type: string;
  name: string;
  input_json: Record<string, unknown>;
  output_json: Record<string, unknown>;
  latency_ms: number;
  token_usage_input: number;
  token_usage_output: number;
  status: "success" | "error";
  error_message: string | null;
}

export interface TestRun {
  id: number;
  test_case_id: number;
  agent_config_id: number;
  status: "pending" | "running" | "success" | "error";
  agent_output: string;
  duration_ms: number;
  total_tokens: number;
  cost_estimate: number;
  error_message: string | null;
  created_at: string;
}

export const runTest = (test_case_id: number, agent_config_id: number) =>
  api.post<TestRun>("/api/test-runs/", null, { params: { test_case_id, agent_config_id } }).then((r) => r.data);

export const listTestRuns = (params?: { test_case_id?: number; agent_config_id?: number; limit?: number; offset?: number }) =>
  api.get<TestRun[]>("/api/test-runs/", { params }).then((r) => r.data);

export const getTestRun = (id: number) =>
  api.get<TestRun>(`/api/test-runs/${id}`).then((r) => r.data);

export const getRunSteps = (testRunId: number) =>
  api.get<RunStep[]>(`/api/test-runs/${testRunId}/steps`).then((r) => r.data);
