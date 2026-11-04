import pytest

class TestAgentConfigAPI:
    @pytest.mark.asyncio
    async def test_create_and_get(self, client):
        resp = await client.post("/api/agent-configs/", json={
            "name": "test-config",
            "agent_type": "http",
            "config": {"endpoint": "http://localhost:9000"},
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "test-config"
        resp = await client.get(f"/api/agent-configs/{data['id']}")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_list(self, client):
        for i in range(2):
            await client.post("/api/agent-configs/", json={
                "name": f"cfg-{i}", "agent_type": "http", "config": {},
            })
        resp = await client.get("/api/agent-configs/")
        assert resp.json()["total"] == 2

    @pytest.mark.asyncio
    async def test_invalid_agent_type(self, client):
        resp = await client.post("/api/agent-configs/", json={
            "name": "bad", "agent_type": "invalid_type", "config": {},
        })
        assert resp.status_code == 422
