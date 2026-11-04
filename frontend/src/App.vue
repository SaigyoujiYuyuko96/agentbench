<template>
  <n-config-provider>
    <n-message-provider>
      <n-dialog-provider>
        <n-layout has-sider>
          <n-layout-sider :width="200" bordered>
            <div style="padding: 20px; font-weight: bold; font-size: 18px;">
              AgentBench
            </div>
            <n-menu :options="menuOptions" :value="activeMenu" @update:value="handleMenuClick" />
          </n-layout-sider>
          <n-layout>
            <n-layout-content>
              <router-view />
            </n-layout-content>
          </n-layout>
        </n-layout>
      </n-dialog-provider>
    </n-message-provider>
  </n-config-provider>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import type { MenuOption } from 'naive-ui'

const route = useRoute()
const router = useRouter()

const menuOptions: MenuOption[] = [
  { label: '评测记录', key: '/test-runs' },
  { label: '测试用例', key: '/test-cases' },
  { label: 'Agent 配置', key: '/agent-configs' },
]

const activeMenu = computed(() => {
  const path = route.path
  if (path.startsWith('/test-runs') || path.startsWith('/run/')) return '/test-runs'
  if (path.startsWith('/test-cases')) return '/test-cases'
  if (path.startsWith('/agent-configs')) return '/agent-configs'
  return '/test-runs'
})

function handleMenuClick(key: string) {
  router.push(key)
}
</script>
