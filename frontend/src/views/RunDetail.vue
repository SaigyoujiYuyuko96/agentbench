<template>
  <div style="padding: 24px;">
    <n-space vertical :size="16">
      <n-space justify="space-between" align="center">
        <n-space>
          <n-button @click="$router.back()">返回</n-button>
          <h2 style="margin: 0;">运行详情</h2>
        </n-space>
        <n-space v-if="run">
          <n-tag :type="statusType" size="large">
            {{ statusLabel }}
          </n-tag>
          <n-tag type="info" size="large">
            耗时: {{ run.duration_ms }}ms
          </n-tag>
          <n-tag type="success" size="large">
            Tokens: {{ run.total_tokens }}
          </n-tag>
        </n-space>
      </n-space>

      <n-spin :show="store.loading">
        <n-grid :cols="2" :x-gap="16">
          <n-gi :span="2">
            <n-card title="Agent 输出" :bordered="false" size="small">
              <pre style="background: #f5f5f5; padding: 12px; border-radius: 4px; margin: 0; white-space: pre-wrap; word-break: break-all;">
{{ run?.agent_output || "无输出" }}
              </pre>
              <n-alert v-if="run?.error_message" type="error" :show-icon="true" style="margin-top: 12px;">
                {{ run.error_message }}
              </n-alert>
            </n-card>
          </n-gi>

          <n-gi>
            <n-card title="调用链 Trace" :bordered="false" size="small">
              <TraceTimeline v-if="steps.length > 0" :steps="steps" />
              <n-empty v-else description="暂无调用步骤" />
            </n-card>
          </n-gi>

          <n-gi>
            <n-space vertical :size="16" style="width: 100%;">
              <n-card title="评分操作" :bordered="false" size="small">
                <n-space vertical :size="12">
                  <n-button type="primary" block @click="handleEvaluateRules">
                    规则评分
                  </n-button>
                  <n-button type="info" block :loading="evaluatingLlm" @click="handleEvaluateLlm">
                    LLM 评分
                  </n-button>
                </n-space>
              </n-card>

              <ScoreCard
                v-for="(ev, idx) in evaluations"
                :key="idx"
                :evaluation="ev"
              />
            </n-space>
          </n-gi>
        </n-grid>
      </n-spin>
    </n-space>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { useRoute } from "vue-router";
import { useMessage } from "naive-ui";
import { useTestRunStore } from "../stores/testRuns";
import TraceTimeline from "../components/TraceTimeline.vue";
import ScoreCard from "../components/ScoreCard.vue";

const route = useRoute();
const store = useTestRunStore();
const message = useMessage();

const evaluatingLlm = ref(false);

const run = computed(() => store.currentRun);
const steps = computed(() => store.steps);
const evaluations = computed(() => store.evaluations);

const statusLabel = computed(() => {
  const map: Record<string, string> = {
    pending: "等待中",
    running: "运行中",
    success: "成功",
    error: "失败",
  };
  return map[run.value?.status || ""] || run.value?.status;
});

const statusType = computed(() => {
  const map: Record<string, "success" | "error" | "warning" | "info" | "default"> = {
    success: "success",
    error: "error",
    running: "warning",
    pending: "info",
  };
  return map[run.value?.status || ""] || "default";
});

async function handleEvaluateRules() {
  try {
    await store.evaluateCurrent(
      [{ type: "keyword_contains", value: "推荐" }],
      false
    );
    message.success("规则评分完成");
  } catch (e: any) {
    message.error("评分失败");
  }
}

async function handleEvaluateLlm() {
  evaluatingLlm.value = true;
  try {
    await store.evaluateCurrent(undefined, true);
    message.success("LLM 评分完成");
  } catch (e: any) {
    message.error(e.message || "LLM 评分失败");
  } finally {
    evaluatingLlm.value = false;
  }
}

onMounted(async () => {
  const id = route.params.id;
  if (id && typeof id === "string") {
    await store.fetchRun(parseInt(id));
  }
});
</script>
