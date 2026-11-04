<template>
  <div style="padding: 24px;">
    <n-space vertical :size="16">
      <n-space justify="space-between">
        <h2 style="margin: 0;">Agent 配置</h2>
        <n-button type="primary" @click="showCreateModal = true">
          新建配置
        </n-button>
      </n-space>

      <n-data-table
        :columns="columns"
        :data="store.items"
        :loading="store.loading"
        :pagination="{ pageSize: 10 }"
        bordered
      />
    </n-space>

    <n-modal v-model:show="showCreateModal" preset="card" title="新建 Agent 配置" style="width: 600px;">
      <n-form ref="formRef" :model="formData" :rules="rules" label-placement="top">
        <n-form-item label="名称" path="name">
          <n-input v-model:value="formData.name" placeholder="配置名称，如 animepilot-v1" />
        </n-form-item>
        <n-form-item label="类型" path="agent_type">
          <n-select v-model:value="formData.agent_type" :options="agentTypeOptions" />
        </n-form-item>
        <n-form-item label="描述">
          <n-input v-model:value="formData.description" type="textarea" :rows="2" placeholder="配置描述" />
        </n-form-item>
        <n-form-item label="配置 (JSON)">
          <n-input
            v-model:value="configJson"
            type="textarea"
            :rows="6"
            placeholder='{"endpoint": "http://localhost:8000/chat", "model": "gpt-4.1"}'
          />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showCreateModal = false">取消</n-button>
          <n-button type="primary" @click="handleCreate">确定</n-button>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, h } from "vue";
import { useMessage } from "naive-ui";
import { useAgentConfigStore } from "../stores/agentConfigs";
import type { DataTableColumns } from "naive-ui";

const store = useAgentConfigStore();
const message = useMessage();

const showCreateModal = ref(false);
const formRef = ref();
const configJson = ref("{}");

const formData = ref({
  name: "",
  agent_type: "http" as "langgraph" | "openai_compatible" | "http" | "python_fn",
  description: "",
});

const rules = {
  name: { required: true, message: "请输入名称", trigger: "blur" },
  agent_type: { required: true, message: "请选择类型", trigger: "change" },
};

const agentTypeOptions = [
  { label: "LangGraph", value: "langgraph" },
  { label: "OpenAI 兼容", value: "openai_compatible" },
  { label: "HTTP 端点", value: "http" },
  { label: "Python 函数", value: "python_fn" },
];

const columns: DataTableColumns = [
  { title: "ID", key: "id", width: 60 },
  { title: "名称", key: "name" },
  {
    title: "类型",
    key: "agent_type",
    width: 140,
    render: (row: any) => {
      const labelMap: Record<string, string> = {
        langgraph: "LangGraph",
        openai_compatible: "OpenAI 兼容",
        http: "HTTP 端点",
        python_fn: "Python 函数",
      };
      return h("n-tag", { type: "info" }, () => labelMap[row.agent_type] || row.agent_type);
    },
  },
  { title: "描述", key: "description", ellipsis: true },
  {
    title: "操作",
    key: "actions",
    width: 150,
    render: (row: any) =>
      h(
        "n-space",
        {},
        () => [
          h("n-button", { size: "small", onClick: () => handleDelete(row.id) }, () => "删除"),
        ]
      ),
  },
];

async function fetchList() {
  await store.fetchList();
}

async function handleCreate() {
  try {
    await formRef.value?.validate();
    let config = {};
    try {
      config = JSON.parse(configJson.value);
    } catch (e) {
      message.error("JSON 格式错误");
      return;
    }
    await store.create({ ...formData.value, config });
    message.success("创建成功");
    showCreateModal.value = false;
    formData.value = { name: "", agent_type: "http", description: "" };
    configJson.value = "{}";
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

onMounted(fetchList);
</script>
