<template>
  <div style="padding: 24px;">
    <n-space vertical :size="16">
      <n-space justify="space-between">
        <h2 style="margin: 0;">评测记录</h2>
        <n-space>
          <n-select
            v-model:value="filterAgentId"
            placeholder="选择 Agent"
            :options="agentOptions"
            clearable
            style="width: 200px;"
            @update:value="fetchRuns"
          />
          <n-button @click="fetchRuns">刷新</n-button>
        </n-space>
      </n-space>

      <n-data-table
        :columns="columns"
        :data="runs"
        :loading="loading"
        :pagination="{ pageSize: 10 }"
        bordered
      />
    </n-space>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, h } from "vue";
import { useRouter } from "vue-router";
import { useMessage } from "naive-ui";
import { listTestRuns, type TestRun } from "../api/testRuns";
import { useAgentConfigStore } from "../stores/agentConfigs";
import type { DataTableColumns } from "naive-ui";

const router = useRouter();
const message = useMessage();
const agentStore = useAgentConfigStore();

const runs = ref<TestRun[]>([]);
const loading = ref(false);
const filterAgentId = ref<number | null>(null);

const agentOptions = ref<{ label: string; value: number }[]>([]);

const columns: DataTableColumns = [
  { title: "ID", key: "id", width: 60 },
  { title: "测试用例 ID", key: "test_case_id", width: 120 },
  { title: "Agent ID", key: "agent_config_id", width: 100 },
  {
    title: "状态",
    key: "status",
    width: 100,
    render: (row: any) => {
      const colorMap: Record<string, string> = {
        success: "success",
        error: "error",
        running: "info",
        pending: "default",
      };
      const labelMap: Record<string, string> = {
        success: "成功",
        error: "失败",
        running: "运行中",
        pending: "等待中",
      };
      return h("n-tag", { type: colorMap[row.status] || "default" }, () => labelMap[row.status] || row.status);
    },
  },
  { title: "耗时 (ms)", key: "duration_ms", width: 110 },
  { title: "Tokens", key: "total_tokens", width: 100 },
  {
    title: "创建时间",
    key: "created_at",
    width: 200,
    render: (row: any) => new Date(row.created_at).toLocaleString("zh-CN"),
  },
  {
    title: "操作",
    key: "actions",
    width: 120,
    render: (row: any) =>
      h(
        "n-button",
        { size: "small", type: "primary", onClick: () => router.push(`/run/${row.id}`) },
        () => "查看详情"
      ),
  },
];

async function fetchRuns() {
  loading.value = true;
  try {
    runs.value = await listTestRuns({
      agent_config_id: filterAgentId.value || undefined,
      limit: 50,
    });
  } catch (e: any) {
    message.error("获取评测记录失败");
  } finally {
    loading.value = false;
  }
}

async function loadAgents() {
  try {
    await agentStore.fetchList();
    agentOptions.value = agentStore.items.map((a: any) => ({
      label: a.name,
      value: a.id,
    }));
  } catch (e) {
    // ignore
  }
}

onMounted(() => {
  loadAgents();
  fetchRuns();
});
</script>
