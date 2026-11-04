import api from "./index";

export interface AgentConfig {
  id: number;
  name: string;
  agent_type: "langgraph" | "openai_compatible" | "http" | "python_fn";
  config: Record<string, unknown>;
  description: string;
  created_at: string;
  updated_at: string;
}

export const listAgentConfigs = () =>
  api.get("/api/agent-configs/").then((r) => r.data);

export const getAgentConfig = (id: number) =>
  api.get<AgentConfig>(`/api/agent-configs/${id}`).then((r) => r.data);

export const createAgentConfig = (data: Partial<AgentConfig>) =>
  api.post<AgentConfig>("/api/agent-configs/", data).then((r) => r.data);

export const updateAgentConfig = (id: number, data: Partial<AgentConfig>) =>
  api.put<AgentConfig>(`/api/agent-configs/${id}`, data).then((r) => r.data);

export const deleteAgentConfig = (id: number) =>
  api.delete(`/api/agent-configs/${id}`);
