import json
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.test_case import TestCase
from app.schemas.test_case import TestCaseCreate, TestCaseUpdate

class TestCaseService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, data: TestCaseCreate) -> TestCase:
        tc = TestCase(
            title=data.title,
            input_text=data.input_text,
            expected_behavior=data.expected_behavior,
            scoring_criteria=data.scoring_criteria,
            tags=json.dumps(data.tags, ensure_ascii=False),
            difficulty=data.difficulty,
            category=data.category,
        )
        self.session.add(tc)
        await self.session.commit()
        await self.session.refresh(tc)
        return tc

    async def list_(
        self,
        *,
        difficulty: str | None = None,
        category: str | None = None,
        tag: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[TestCase], int]:
        query = select(TestCase)
        count_query = select(func.count(TestCase.id))
        if difficulty:
            query = query.where(TestCase.difficulty == difficulty)
            count_query = count_query.where(TestCase.difficulty == difficulty)
        if category:
            query = query.where(TestCase.category == category)
            count_query = count_query.where(TestCase.category == category)
        if tag:
            like_pattern = f'%"{tag}"%'
            query = query.where(TestCase.tags.like(like_pattern))
            count_query = count_query.where(TestCase.tags.like(like_pattern))
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0
        query = query.order_by(TestCase.created_at.desc()).offset(skip).limit(limit)
        result = await self.session.execute(query)
        items = list(result.scalars().all())
        return items, total

    async def get_by_id(self, test_case_id: int) -> TestCase | None:
        result = await self.session.execute(
            select(TestCase).where(TestCase.id == test_case_id)
        )
        return result.scalar_one_or_none()

    async def update(self, test_case_id: int, data: TestCaseUpdate) -> TestCase | None:
        tc = await self.get_by_id(test_case_id)
        if tc is None:
            return None
        update_data = data.model_dump(exclude_unset=True)
        if "tags" in update_data and update_data["tags"] is not None:
            update_data["tags"] = json.dumps(update_data["tags"], ensure_ascii=False)
        for key, value in update_data.items():
            setattr(tc, key, value)
        await self.session.commit()
        await self.session.refresh(tc)
        return tc

    async def delete(self, test_case_id: int) -> bool:
        result = await self.session.execute(
            delete(TestCase).where(TestCase.id == test_case_id)
        )
        await self.session.commit()
        return result.rowcount > 0
