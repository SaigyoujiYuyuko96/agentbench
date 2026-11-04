<template>
  <div style="padding: 24px;">
    <n-space vertical :size="16">
      <n-space justify="space-between">
        <h2 style="margin: 0;">测试用例</h2>
        <n-space>
          <n-select
            v-model:value="filterDifficulty"
            placeholder="难度筛选"
            :options="difficultyOptions"
            clearable
            style="width: 120px;"
            @update:value="fetchList"
          />
          <n-button type="primary" @click="showCreateModal = true">
            新建用例
          </n-button>
        </n-space>
      </n-space>

      <n-data-table
        :columns="columns"
        :data="store.items"
        :loading="store.loading"
        :pagination="{ pageSize: 10 }"
        bordered
      />
    </n-space>

    <n-modal v-model:show="showCreateModal" preset="card" title="新建测试用例" style="width: 600px;">
      <n-form ref="formRef" :model="formData" :rules="rules" label-placement="top">
        <n-form-item label="标题" path="title">
          <n-input v-model:value="formData.title" placeholder="输入用例标题" />
        </n-form-item>
        <n-form-item label="用户输入" path="input_text">
          <n-input v-model:value="formData.input_text" type="textarea" :rows="3" placeholder="输入测试的用户问题" />
        </n-form-item>
        <n-form-item label="期望行为" path="expected_behavior">
          <n-input v-model:value="formData.expected_behavior" type="textarea" :rows="3" placeholder="描述期望的输出行为" />
        </n-form-item>
        <n-form-item label="评分标准">
          <n-input v-model:value="formData.scoring_criteria" type="textarea" :rows="2" placeholder="描述评分标准" />
        </n-form-item>
        <n-space>
          <n-form-item label="难度" style="width: 150px;">
            <n-select v-model:value="formData.difficulty" :options="difficultyOptions" />
          </n-form-item>
          <n-form-item label="分类" style="flex: 1;">
            <n-input v-model:value="formData.category" placeholder="如：搜索、推荐" />
          </n-form-item>
        </n-space>
        <n-form-item label="标签">
          <n-select v-model:value="formData.tags" :options="tagOptions" filterable taggable multiple />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showCreateModal = false">取消</n-button>
          <n-button type="primary" @click="handleCreate">确定</n-button>
        </n-space>
      </template>
    </n-modal>

    <n-modal v-model:show="showRunModal" preset="card" title="运行测试用例" style="width: 500px;">
      <n-form label-placement="top">
        <n-form-item label="选择 Agent 配置">
          <n-select v-model:value="selectedAgentId" :options="agentOptions" placeholder="选择要测试的 Agent" />
        </n-form-item>
        <n-alert v-if="runTestCase" type="info" :show-icon="true">
          当前用例：{{ runTestCase.title }}
        </n-alert>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showRunModal = false">取消</n-button>
          <n-button type="primary" :loading="running" @click="handleRun">
            开始运行
          </n-button>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, h } from "vue";
import { useRouter } from "vue-router";
import { useMessage } from "naive-ui";
import { useTestCaseStore } from "../stores/testCases";
import { useAgentConfigStore } from "../stores/agentConfigs";
import { runTest } from "../api/testRuns";
import type { DataTableColumns } from "naive-ui";

const store = useTestCaseStore();
const agentStore = useAgentConfigStore();
const message = useMessage();
const router = useRouter();

const filterDifficulty = ref<string | null>(null);
const showCreateModal = ref(false);
const showRunModal = ref(false);
const formRef = ref();
const running = ref(false);
const runTestCase = ref<any>(null);
const selectedAgentId = ref<number | null>(null);
const agentOptions = ref<{ label: string; value: number }[]>([]);

const formData = ref({
  title: "",
  input_text: "",
  expected_behavior: "",
  scoring_criteria: "",
  difficulty: "medium" as "easy" | "medium" | "hard",
  category: "",
  tags: [] as string[],
});

const rules = {
  title: { required: true, message: "请输入标题", trigger: "blur" },
  input_text: { required: true, message: "请输入用户输入", trigger: "blur" },
  expected_behavior: { required: true, message: "请输入期望行为", trigger: "blur" },
};

const difficultyOptions = [
  { label: "简单", value: "easy" },
  { label: "中等", value: "medium" },
  { label: "困难", value: "hard" },
];

const tagOptions = [
  { label: "搜索", value: "搜索" },
  { label: "推荐", value: "推荐" },
  { label: "多轮", value: "多轮" },
  { label: "工具调用", value: "工具调用" },
];

const columns: DataTableColumns = [
  { title: "ID", key: "id", width: 60 },
  { title: "标题", key: "title", ellipsis: true },
  {
    title: "难度",
    key: "difficulty",
    width: 100,
    render: (row: any) => {
      const colorMap: Record<string, string> = { easy: "success", medium: "warning", hard: "error" };
      const labelMap: Record<string, string> = { easy: "简单", medium: "中等", hard: "困难" };
      return h("n-tag", { type: colorMap[row.difficulty] || "default" }, () => labelMap[row.difficulty] || row.difficulty);
    },
  },
  { title: "分类", key: "category", width: 120 },
  {
    title: "标签",
    key: "tags",
    width: 200,
    render: (row: any) =>
      h(
        "n-space",
        { size: 4 },
        () => row.tags?.map((tag: string) => h("n-tag", { size: "small" }, () => tag)) || []
      ),
  },
  {
    title: "操作",
    key: "actions",
    width: 180,
    render: (row: any) =>
      h(
        "n-space",
        { size: 4 },
        () => [
          h("n-button", { size: "small", type: "primary", onClick: () => openRunModal(row) }, () => "运行"),
          h("n-button", { size: "small", onClick: () => handleDelete(row.id) }, () => "删除"),
        ]
      ),
  },
];

async function fetchList() {
  await store.fetchList({ difficulty: filterDifficulty.value || undefined });
}

async function handleCreate() {
  try {
    await formRef.value?.validate();
    await store.create(formData.value);
    message.success("创建成功");
    showCreateModal.value = false;
    formData.value = {
      title: "",
      input_text: "",
      expected_behavior: "",
      scoring_criteria: "",
      difficulty: "medium",
      category: "",
      tags: [],
    };
  } catch (e: any) {
    message.error(e.message || "创建失败");
  }
}

async function handleDelete(id: number) {
  try {
    await store.remove(id);
    message.success("删除成功");
  } catch (e: any) {
    message.error("删除失败");
  }
}

function openRunModal(row: any) {
  runTestCase.value = row;
  selectedAgentId.value = agentOptions.value[0]?.value || null;
  showRunModal.value = true;
}

async function handleRun() {
  if (!selectedAgentId.value || !runTestCase.value) {
    message.error("请选择 Agent 配置");
    return;
  }
  running.value = true;
  try {
    const result = await runTest(runTestCase.value.id, selectedAgentId.value);
    message.success("运行成功");
    showRunModal.value = false;
    router.push(`/run/${result.id}`);
  } catch (e: any) {
    message.error(e.message || "运行失败");
  } finally {
    running.value = false;
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
  fetchList();
  loadAgents();
});
</script>
