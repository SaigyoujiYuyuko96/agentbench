import pytest

class TestTestRunsAPI:
    @pytest.mark.asyncio
    async def test_get_test_run_not_found(self, client):
        resp = await client.get("/api/test-runs/999")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_get_run_steps_empty(self, client):
        tc_resp = await client.post("/api/test-cases/", json={
            "title": "测试", "input_text": "hi", "expected_behavior": "hello",
        })
        ac_resp = await client.post("/api/agent-configs/", json={
            "name": "test-ac", "agent_type": "http",
            "config": {"endpoint": "http://localhost:9999"},
        })
        tc_id = tc_resp.json()["id"]
        ac_id = ac_resp.json()["id"]

        resp = await client.post("/api/test-runs/", params={
            "test_case_id": tc_id, "agent_config_id": ac_id,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["test_case_id"] == tc_id
        assert data["agent_config_id"] == ac_id
        assert data["status"] == "error"
        assert data["error_message"] is not None

        steps_resp = await client.get(f"/api/test-runs/{data['id']}/steps")
        assert steps_resp.status_code == 200
        steps = steps_resp.json()
        assert len(steps) >= 1
        assert steps[0]["status"] == "error"
