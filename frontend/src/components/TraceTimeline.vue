<template>
  <n-timeline>
    <n-timeline-item
      v-for="step in steps"
      :key="step.id"
      :type="step.status === 'error' ? 'error' : step.latency_ms > 3000 ? 'warning' : 'success'"
      :title="`步骤 ${step.sequence}: ${step.name || step.step_type}`"
    >
      <!-- 注意：Naive UI 的 n-timeline-item 用的是 default slot，
           写成 <template #content> 会被静默忽略，只留下标题。 -->
      <n-space vertical :size="8">
        <n-space>
          <n-tag :type="step.status === 'error' ? 'error' : 'default'" size="small">
            {{ step.step_type }}
          </n-tag>
          <n-tag size="small" type="info">
            {{ step.latency_ms }}ms
          </n-tag>
          <n-tag v-if="step.token_usage_input || step.token_usage_output" size="small" type="success">
            {{ step.token_usage_input }} → {{ step.token_usage_output }} tokens
          </n-tag>
          <n-tag v-if="step.latency_ms > 3000" size="small" type="warning">
            耗时过长
          </n-tag>
        </n-space>
        <n-collapse>
          <n-collapse-item title="查看输入/输出详情" name="detail">
            <n-space vertical :size="8">
              <div>
                <div style="font-weight: bold; margin-bottom: 4px;">输入:</div>
                <pre style="background: #f5f5f5; padding: 8px; border-radius: 4px; overflow-x: auto; margin: 0;">{{ JSON.stringify(step.input_json, null, 2) }}</pre>
              </div>
              <div>
                <div style="font-weight: bold; margin-bottom: 4px;">输出:</div>
                <pre style="background: #f5f5f5; padding: 8px; border-radius: 4px; overflow-x: auto; margin: 0;">{{ JSON.stringify(step.output_json, null, 2) }}</pre>
              </div>
            </n-space>
          </n-collapse-item>
        </n-collapse>
        <n-alert v-if="step.status === 'error' && step.error_message" type="error" :show-icon="true">
          {{ step.error_message }}
        </n-alert>
      </n-space>
    </n-timeline-item>
  </n-timeline>
</template>

<script setup lang="ts">
import type { RunStep } from "../api/testRuns";

defineProps<{
  steps: RunStep[];
}>();
</script>
