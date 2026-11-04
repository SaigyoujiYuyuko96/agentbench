import { defineStore } from "pinia";
import { ref } from "vue";
import { getTestRun, getRunSteps, runTest, type TestRun, type RunStep } from "../api/testRuns";
import { getEvaluations, evaluateRun, type EvaluationResult } from "../api/evaluations";

export const useTestRunStore = defineStore("testRuns", () => {
  const currentRun = ref<TestRun | null>(null);
  const steps = ref<RunStep[]>([]);
  const evaluations = ref<EvaluationResult[]>([]);
  const loading = ref(false);

  async function fetchRun(id: number) {
    loading.value = true;
    try {
      currentRun.value = await getTestRun(id);
      steps.value = await getRunSteps(id);
      evaluations.value = await getEvaluations(id);
    } finally {
      loading.value = false;
    }
  }

  async function runTestCase(testCaseId: number, agentConfigId: number) {
    const result = await runTest(testCaseId, agentConfigId);
    currentRun.value = result;
    steps.value = await getRunSteps(result.id);
    return result;
  }

  async function evaluateCurrent(rules?: unknown[], useLlmJudge?: boolean) {
    if (!currentRun.value) return null;
    const result = await evaluateRun(currentRun.value.id, rules, useLlmJudge);
    evaluations.value = [...evaluations.value, result];
    return result;
  }

  return { currentRun, steps, evaluations, loading, fetchRun, runTestCase, evaluateCurrent };
});
