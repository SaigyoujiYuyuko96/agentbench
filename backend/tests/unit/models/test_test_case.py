import pytest
from datetime import datetime
from agentbench.models.test_case import TestCase

class TestTestCaseModel:
    @pytest.mark.asyncio
    async def test_create_test_case_with_defaults(self, db_session):
        tc = TestCase(
            title="搜索番剧测试",
            input_text="推荐一部治愈系动画",
            expected_behavior="返回一部治愈系动漫的推荐",
            scoring_criteria="推荐内容应与治愈系相关",
        )
        db_session.add(tc)
        await db_session.commit()
        await db_session.refresh(tc)
        assert tc.id is not None
        assert tc.difficulty == "medium"
        assert tc.category == ""
        assert tc.tags == "[]"
        assert isinstance(tc.created_at, datetime)

    @pytest.mark.asyncio
    async def test_create_test_case_with_all_fields(self, db_session):
        tc = TestCase(
            title="完整用例",
            input_text="搜索 CLANNAD",
            expected_behavior="返回 CLANNAD 的详细信息",
            scoring_criteria="必须包含评分、简介",
            tags='["搜索", "精确匹配"]',
            difficulty="hard",
            category="搜索",
        )
        db_session.add(tc)
        await db_session.commit()
        await db_session.refresh(tc)
        assert tc.difficulty == "hard"
        assert tc.category == "搜索"
        assert tc.tags == '["搜索", "精确匹配"]'
