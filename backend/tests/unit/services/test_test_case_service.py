import pytest
from agentbench.models.test_case import TestCase
from agentbench.schemas.test_case import TestCaseCreate, TestCaseUpdate
from agentbench.services.test_case_service import TestCaseService

class TestTestCaseService:
    @pytest.mark.asyncio
    async def test_create_test_case(self, db_session):
        service = TestCaseService(db_session)
        data = TestCaseCreate(
            title="测试用例1",
            input_text="搜索新海诚的作品",
            expected_behavior="返回新海诚相关动漫列表",
        )
        tc = await service.create(data)
        assert tc.id is not None
        assert tc.title == "测试用例1"

    @pytest.mark.asyncio
    async def test_list_test_cases(self, db_session):
        service = TestCaseService(db_session)
        for i in range(3):
            await service.create(TestCaseCreate(
                title=f"用例{i}", input_text=f"输入{i}",
                expected_behavior=f"期望{i}",
            ))
        items, total = await service.list_()
        assert total == 3
        assert len(items) == 3

    @pytest.mark.asyncio
    async def test_get_test_case(self, db_session):
        service = TestCaseService(db_session)
        created = await service.create(TestCaseCreate(
            title="获取测试", input_text="输入", expected_behavior="期望",
        ))
        fetched = await service.get_by_id(created.id)
        assert fetched is not None
        assert fetched.title == "获取测试"

    @pytest.mark.asyncio
    async def test_update_test_case(self, db_session):
        service = TestCaseService(db_session)
        created = await service.create(TestCaseCreate(
            title="原标题", input_text="输入", expected_behavior="期望",
        ))
        updated = await service.update(created.id, TestCaseUpdate(title="新标题"))
        assert updated.title == "新标题"

    @pytest.mark.asyncio
    async def test_delete_test_case(self, db_session):
        service = TestCaseService(db_session)
        created = await service.create(TestCaseCreate(
            title="删除测试", input_text="输入", expected_behavior="期望",
        ))
        await service.delete(created.id)
        fetched = await service.get_by_id(created.id)
        assert fetched is None

    @pytest.mark.asyncio
    async def test_list_with_filters(self, db_session):
        service = TestCaseService(db_session)
        await service.create(TestCaseCreate(
            title="简单用例", input_text="输入", expected_behavior="期望",
            difficulty="easy", category="搜索", tags=["搜索"],
        ))
        await service.create(TestCaseCreate(
            title="困难用例", input_text="输入", expected_behavior="期望",
            difficulty="hard", category="推荐", tags=["推荐"],
        ))
        items, total = await service.list_(difficulty="easy")
        assert total == 1
        assert items[0].difficulty == "easy"
