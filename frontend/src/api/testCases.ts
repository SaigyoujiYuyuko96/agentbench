import api from "./index";

export interface TestCase {
  id: number;
  title: string;
  input_text: string;
  expected_behavior: string;
  scoring_criteria: string;
  tags: string[];
  difficulty: "easy" | "medium" | "hard";
  category: string;
  created_at: string;
  updated_at: string;
}

export const listTestCases = (params?: { difficulty?: string; tag?: string }) =>
  api.get("/api/test-cases/", { params }).then((r) => r.data);

export const getTestCase = (id: number) =>
  api.get<TestCase>(`/api/test-cases/${id}`).then((r) => r.data);

export const createTestCase = (data: Partial<TestCase>) =>
  api.post<TestCase>("/api/test-cases/", data).then((r) => r.data);

export const updateTestCase = (id: number, data: Partial<TestCase>) =>
  api.put<TestCase>(`/api/test-cases/${id}`, data).then((r) => r.data);

export const deleteTestCase = (id: number) =>
  api.delete(`/api/test-cases/${id}`);
