import { createRouter, createWebHistory } from "vue-router";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", redirect: "/test-runs" },
    { path: "/test-cases", component: () => import("../views/TestCases.vue") },
    { path: "/test-cases/new", component: () => import("../views/TestCaseEdit.vue") },
    { path: "/agent-configs", component: () => import("../views/AgentConfigs.vue") },
    { path: "/agent-configs/new", component: () => import("../views/AgentConfigEdit.vue") },
    { path: "/test-runs", component: () => import("../views/TestRuns.vue") },
    { path: "/run/:id", component: () => import("../views/RunDetail.vue") },
  ],
});

export default router;
