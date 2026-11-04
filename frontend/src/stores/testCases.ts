import { defineStore } from "pinia";
import { ref } from "vue";
import { listTestCases, createTestCase, deleteTestCase, type TestCase } from "../api/testCases";

export const useTestCaseStore = defineStore("testCases", () => {
  const items = ref<TestCase[]>([]);
  const total = ref(0);
  const loading = ref(false);

  async function fetchList(params?: { difficulty?: string; tag?: string }) {
    loading.value = true;
    try {
      const data = await listTestCases(params);
      items.value = data.items;
      total.value = data.total;
    } finally {
      loading.value = false;
    }
  }

  async function create(data: Partial<TestCase>) {
    const item = await createTestCase(data);
    items.value.unshift(item);
    total.value += 1;
    return item;
  }

  async function remove(id: number) {
    await deleteTestCase(id);
    items.value = items.value.filter((i) => i.id !== id);
    total.value -= 1;
  }

  return { items, total, loading, fetchList, create, remove };
});
