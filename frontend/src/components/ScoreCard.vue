<template>
  <n-card :title="`评分结果 (${judgeTypeLabel})`" :bordered="false" size="small">
    <n-space vertical :size="12">
      <div style="text-align: center; padding: 16px 0;">
        <n-text style="font-size: 48px; font-weight: bold;" :type="scoreType">
          {{ evaluation.overall_score.toFixed(1) }}
        </n-text>
        <n-text depth="3"> / 5.0</n-text>
      </div>

      <div v-if="hasDimensionScores">
        <n-space vertical :size="8">
          <div v-for="dim in dimensions" :key="dim.key">
            <n-space justify="space-between" :size="8">
              <n-text>{{ dim.label }}</n-text>
              <n-text :type="getScoreType(dim.value || 0)">
                {{ dim.value ? dim.value.toFixed(1) : "-" }}
              </n-text>
            </n-space>
            <n-progress
              type="line"
              :percentage="((dim.value || 0) / 5) * 100"
              :color="getProgressColor(dim.value || 0)"
              :height="6"
              :show-indicator="false"
            />
          </div>
        </n-space>
      </div>

      <n-alert v-if="evaluation.judge_reasoning" type="info" :show-icon="true">
        <template #header>评分理由</template>
        {{ evaluation.judge_reasoning }}
      </n-alert>
    </n-space>
  </n-card>
</template>

<script setup lang="ts">
import { computed } from "vue";
import type { EvaluationResult } from "../api/evaluations";

const props = defineProps<{
  evaluation: EvaluationResult;
}>();

const judgeTypeLabel = computed(() => {
  const map: Record<string, string> = {
    rule: "规则评分",
    llm: "LLM 评分",
    none: "未评分",
  };
  return map[props.evaluation.judge_type] || props.evaluation.judge_type;
});

const hasDimensionScores = computed(() =>
  props.evaluation.accuracy_score !== null ||
  props.evaluation.hallucination_score !== null ||
  props.evaluation.tool_correctness_score !== null ||
  props.evaluation.expression_quality_score !== null
);

const dimensions = computed(() => [
  { key: "accuracy", label: "准确性", value: props.evaluation.accuracy_score },
  { key: "hallucination", label: "无幻觉", value: props.evaluation.hallucination_score },
  { key: "tool_correctness", label: "工具调用正确性", value: props.evaluation.tool_correctness_score },
  { key: "expression_quality", label: "表达质量", value: props.evaluation.expression_quality_score },
]);

const scoreType = computed(() => {
  const s = props.evaluation.overall_score;
  if (s >= 4) return "success";
  if (s >= 3) return "warning";
  return "error";
});

function getScoreType(score: number): "success" | "warning" | "error" | "default" {
  if (score >= 4) return "success";
  if (score >= 3) return "warning";
  if (score > 0) return "error";
  return "default";
}

function getProgressColor(score: number): string {
  if (score >= 4) return "#18a058";
  if (score >= 3) return "#f0a020";
  return "#d03050";
}
</script>
