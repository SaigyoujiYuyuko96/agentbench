import pytest
from agentbench.schemas.test_case import TestCaseCreate

class TestTestCaseAPI:
    @pytest.mark.asyncio
    async def test_create_test_case(self, client):
        resp = await client.post("/api/test-cases/", json={
            "title": "API 测试用例",
            "input_text": "推荐动漫",
            "expected_behavior": "返回推荐结果",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "API 测试用例"
        assert data["id"] is not None

    @pytest.mark.asyncio
    async def test_list_test_cases(self, client):
        for i in range(2):
            await client.post("/api/test-cases/", json={
                "title": f"用例{i}", "input_text": "输入",
                "expected_behavior": "期望",
            })
        resp = await client.get("/api/test-cases/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2

    @pytest.mark.asyncio
    async def test_get_test_case(self, client):
        create_resp = await client.post("/api/test-cases/", json={
            "title": "获取测试", "input_text": "输入",
            "expected_behavior": "期望",
        })
        test_case_id = create_resp.json()["id"]
        resp = await client.get(f"/api/test-cases/{test_case_id}")
        assert resp.status_code == 200
        assert resp.json()["title"] == "获取测试"

    @pytest.mark.asyncio
    async def test_update_test_case(self, client):
        create_resp = await client.post("/api/test-cases/", json={
            "title": "原标题", "input_text": "输入",
            "expected_behavior": "期望",
        })
        test_case_id = create_resp.json()["id"]
        resp = await client.put(f"/api/test-cases/{test_case_id}", json={"title": "新标题"})
        assert resp.status_code == 200
        assert resp.json()["title"] == "新标题"

    @pytest.mark.asyncio
    async def test_delete_test_case(self, client):
        create_resp = await client.post("/api/test-cases/", json={
            "title": "删除测试", "input_text": "输入",
            "expected_behavior": "期望",
        })
        test_case_id = create_resp.json()["id"]
        resp = await client.delete(f"/api/test-cases/{test_case_id}")
        assert resp.status_code == 204
        resp = await client.get(f"/api/test-cases/{test_case_id}")
        assert resp.status_code == 404
