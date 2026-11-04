import { defineStore } from "pinia";
import { ref } from "vue";
import { listAgentConfigs, createAgentConfig, deleteAgentConfig, type AgentConfig } from "../api/agentConfigs";

export const useAgentConfigStore = defineStore("agentConfigs", () => {
  const items = ref<AgentConfig[]>([]);
  const total = ref(0);
  const loading = ref(false);

  async function fetchList() {
    loading.value = true;
    try {
      const data = await listAgentConfigs();
      items.value = data.items;
      total.value = data.total;
    } finally {
      loading.value = false;
    }
  }

  async function create(data: Partial<AgentConfig>) {
    const item = await createAgentConfig(data);
    items.value.unshift(item);
    total.value += 1;
    return item;
  }

  async function remove(id: number) {
    await deleteAgentConfig(id);
    items.value = items.value.filter((i) => i.id !== id);
    total.value -= 1;
  }

  return { items, total, loading, fetchList, create, remove };
});
