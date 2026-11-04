# AgentBench MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建一个框架无关的 AI Agent 评测与可观测平台 MVP，支持测试集管理、四种 Agent 适配器接入、Trace 可视化、规则/LLM 自动评分。

**Architecture:** FastAPI 后端按 models/schemas/routers/services 分层，runners/ 目录实现四种 Agent 适配器（LangGraph/OpenAI/HTTP/Python Fn），evaluators/ 目录实现规则评分和 LLM-as-Judge。Vue 3 前端用 Naive UI 构建。SQLite 作为 MVP 数据库。TDD 驱动，每个 Task 先写测试再实现。

**Tech Stack:** Python 3.11+, FastAPI, SQLAlchemy 2.x, Pydantic v2, LangGraph, httpx, Vue 3, TypeScript, Vite, Pinia, Naive UI, Pytest, Vitest, Playwright

**Project root:** `D:\ai work\AgentBench`

**Design doc:** `docs/superpowers/specs/2026-07-04-agentbench-design.md`

---

## Phase 1: 后端基础骨架 + 数据模型 + CRUD API

**交付物：** FastAPI 服务可启动，TestCase 和 AgentConfig 的 CRUD API 可用，数据库表自动创建，基础测试通过。

---

### Task 1.1: 项目脚手架与依赖安装

**Files:**
- Create: `D:\ai work\AgentBench\backend\pyproject.toml`
- Create: `D:\ai work\AgentBench\backend\app\__init__.py`
- Create: `D:\ai work\AgentBench\backend\app\config.py`
- Create: `D:\ai work\AgentBench\backend\app\database.py`
- Create: `D:\ai work\AgentBench\backend\app\main.py`
- Create: `D:\ai work\AgentBench\backend\tests\__init__.py`
- Create: `D:\ai work\AgentBench\backend\tests\conftest.py`

- [ ] **Step 1: 创建 pyproject.toml**

```toml
# D:\ai work\AgentBench\backend\pyproject.toml
[project]
name = "agentbench-backend"
version = "0.1.0"
description = "AI Agent evaluation and observability platform"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.30.0",
    "sqlalchemy>=2.0.30",
    "pydantic>=2.8.0",
    "pydantic-settings>=2.3.0",
    "httpx>=0.27.0",
    "langgraph>=0.2.0",
    "langchain-openai>=0.2.0",
    "openai>=1.40.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.2.0",
    "pytest-asyncio>=0.23.0",
    "pytest-cov>=5.0.0",
    "httpx>=0.27.0",
]

[build-system]
requires = ["setuptools>=70.0"]
build-backend = "setuptools.build_meta"
```

- [ ] **Step 2: 创建 config.py**

```python
# D:\ai work\AgentBench\backend\app\config.py
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite+aiosqlite:///./agentbench.db"
    llm_base_url: str = "https://api.openai.com/v1"
    llm_api_key: str = ""
    llm_model: str = "gpt-4.1"
    llm_judge_model: str = "gpt-4.1"

    model_config = {"env_prefix": "AGENTBENCH_", "env_file": ".env"}


settings = Settings()
```

- [ ] **Step 3: 创建 database.py**

```python
# D:\ai work\AgentBench\backend\app\database.py
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

engine = create_async_engine(settings.database_url, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session
```

- [ ] **Step 4: 创建 main.py（最小 FastAPI 入口）**

```python
# D:\ai work\AgentBench\backend\app\main.py
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="AgentBench", version="0.1.0", lifespan=lifespan)


@app.get("/health")
async def health():
    return {"status": "ok"}
```

- [ ] **Step 5: 创建空的 __init__.py 和 conftest.py**

```python
# D:\ai work\AgentBench\backend\app\__init__.py
# D:\ai work\AgentBench\backend\tests\__init__.py
# 两个文件都留空
```

```python
# D:\ai work\AgentBench\backend\tests\conftest.py
import pytest
from httpx import AsyncClient, ASGITransport

from app.database import async_session, engine, Base, get_session
from app.main import app


@pytest.fixture
async def client():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async def override_get_session():
        async with async_session() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
```

- [ ] **Step 6: 安装依赖并验证启动**

Run:
```powershell
cd "D:\ai work\AgentBench\backend"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Expected: 服务启动在 8000 端口，`GET /health` 返回 `{"status": "ok"}`

- [ ] **Step 7: 验证测试基础设施可用**

Run: `pytest tests/ -v`
Expected: 0 tests collected (无报错即可)

- [ ] **Step 8: 初始化 Git 并首次提交**

```bash
cd "D:\ai work\AgentBench"
git init
echo "__pycache__/\n*.pyc\n.venv/\n*.db\n.env\nnode_modules/\ndist/\n.coverage\nhtmlcov/" > .gitignore
git add -A
git commit -m "chore: scaffold backend project with FastAPI, SQLAlchemy, Pytest"
```

---

### Task 1.2: 数据模型 — TestCase

**Files:**
- Create: `D:\ai work\AgentBench\backend\app\models\__init__.py`
- Create: `D:\ai work\AgentBench\backend\app\models\test_case.py`
- Create: `D:\ai work\AgentBench\backend\app\schemas\__init__.py`
- Create: `D:\ai work\AgentBench\backend\app\schemas\test_case.py`
- Test: `D:\ai work\AgentBench\backend\tests\unit\__init__.py`
- Test: `D:\ai work\AgentBench\backend\tests\unit\models\__init__.py`
- Test: `D:\ai work\AgentBench\backend\tests\unit\models\test_test_case.py`

- [ ] **Step 1: 写 TestCase 的失败测试**

```python
# D:\ai work\AgentBench\backend\tests\unit\models\test_test_case.py
import pytest
from datetime import datetime

from app.models.test_case import TestCase


@pytest.fixture
def db_session():
    """使用 conftest 中已创建的 session"""
    pass  # 实际会通过 conftest fixture 注入


class TestTestCaseModel:
    def test_create_test_case_with_defaults(self, db_session):
        tc = TestCase(
            title="搜索番剧测试",
            input_text="推荐一部治愈系动画",
            expected_behavior="返回一部治愈系动漫的推荐",
            scoring_criteria="推荐内容应与治愈系相关",
        )
        db_session.add(tc)
        db_session.commit()
        db_session.refresh(tc)

        assert tc.id is not None
        assert tc.difficulty == "medium"
        assert tc.category == ""
        assert tc.tags == "[]"
        assert isinstance(tc.created_at, datetime)

    def test_create_test_case_with_all_fields(self, db_session):
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
        db_session.commit()
        db_session.refresh(tc)

        assert tc.difficulty == "hard"
        assert tc.category == "搜索"
        assert tc.tags == '["搜索", "精确匹配"]'
```

注意：需要先更新 conftest.py 添加 db_session fixture。更新后 conftest.py：

```python
# D:\ai work\AgentBench\backend\tests\conftest.py （更新版，追加 fixture）
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

from app.database import Base, get_session
from app.main import app

# 测试用内存数据库
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_agentbench.db"
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
test_session_factory = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture
async def db_session():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with test_session_factory() as session:
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def client(db_session):
    async def override_get_session():
        yield db_session

    app.dependency_overrides[get_session] = override_get_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/unit/models/test_test_case.py -v`
Expected: FAIL — `ModuleNotFoundError: app.models.test_case`

- [ ] **Step 3: 实现 TestCase 模型**

```python
# D:\ai work\AgentBench\backend\app\models\__init__.py
# 留空
```

```python
# D:\ai work\AgentBench\backend\app\models\test_case.py
from datetime import datetime

from sqlalchemy import Integer, String, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class TestCase(Base):
    __tablename__ = "test_cases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    input_text: Mapped[str] = mapped_column(Text, nullable=False)
    expected_behavior: Mapped[str] = mapped_column(Text, nullable=False)
    scoring_criteria: Mapped[str] = mapped_column(Text, nullable=False, default="")
    tags: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    difficulty: Mapped[str] = mapped_column(String(20), nullable=False, default="medium")
    category: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

- [ ] **Step 4: 运行测试确认通过**

Run: `pytest tests/unit/models/test_test_case.py -v`
Expected: 2 passed

- [ ] **Step 5: 实现 TestCase Pydantic schemas**

```python
# D:\ai work\AgentBench\backend\app\schemas\__init__.py
# 留空
```

```python
# D:\ai work\AgentBench\backend\app\schemas\test_case.py
from datetime import datetime

from pydantic import BaseModel, Field


class TestCaseCreate(BaseModel):
    title: str = Field(..., max_length=200)
    input_text: str
    expected_behavior: str
    scoring_criteria: str = ""
    tags: list[str] = Field(default_factory=list)
    difficulty: str = Field(default="medium", pattern="^(easy|medium|hard)$")
    category: str = Field(default="")


class TestCaseUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=200)
    input_text: str | None = None
    expected_behavior: str | None = None
    scoring_criteria: str | None = None
    tags: list[str] | None = None
    difficulty: str | None = Field(default=None, pattern="^(easy|medium|hard)$")
    category: str | None = None


class TestCaseResponse(BaseModel):
    id: int
    title: str
    input_text: str
    expected_behavior: str
    scoring_criteria: str
    tags: list[str]
    difficulty: str
    category: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
```

- [ ] **Step 6: 提交**

```bash
git add -A
git commit -m "feat: add TestCase model and schemas"
```

---

### Task 1.3: TestCase CRUD API

**Files:**
- Create: `D:\ai work\AgentBench\backend\app\services\__init__.py`
- Create: `D:\ai work\AgentBench\backend\app\services\test_case_service.py`
- Create: `D:\ai work\AgentBench\backend\app\routers\__init__.py`
- Create: `D:\ai work\AgentBench\backend\app\routers\test_cases.py`
- Modify: `D:\ai work\AgentBench\backend\app\main.py` (注册 router)
- Test: `D:\ai work\AgentBench\backend\tests\unit\services\__init__.py`
- Test: `D:\ai work\AgentBench\backend\tests\unit\services\test_test_case_service.py`
- Test: `D:\ai work\AgentBench\backend\tests\integration\__init__.py`
- Test: `D:\ai work\AgentBench\backend\tests\integration\test_test_cases_api.py`

- [ ] **Step 1: 写 TestCaseService 失败测试**

```python
# D:\ai work\AgentBench\backend\tests\unit\services\test_test_case_service.py
import pytest

from app.models.test_case import TestCase
from app.schemas.test_case import TestCaseCreate, TestCaseUpdate
from app.services.test_case_service import TestCaseService


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
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/unit/services/test_test_case_service.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: 实现 TestCaseService**

```python
# D:\ai work\AgentBench\backend\app\services\__init__.py
# 留空
```

```python
# D:\ai work\AgentBench\backend\app\services\test_case_service.py
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
```

- [ ] **Step 4: 运行 Service 测试确认通过**

Run: `pytest tests/unit/services/test_test_case_service.py -v`
Expected: 6 passed

- [ ] **Step 5: 写 API 集成测试**

```python
# D:\ai work\AgentBench\backend\tests\integration\test_test_cases_api.py
import pytest

from app.schemas.test_case import TestCaseCreate


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
        # 先创建两个
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
```

- [ ] **Step 6: 运行 API 测试确认失败**

Run: `pytest tests/integration/test_test_cases_api.py -v`
Expected: FAIL — 404（路由未注册）

- [ ] **Step 7: 实现 TestCase Router 并注册**

```python
# D:\ai work\AgentBench\backend\app\routers\__init__.py
# 留空
```

```python
# D:\ai work\AgentBench\backend\app\routers\test_cases.py
import json

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.schemas.test_case import (
    TestCaseCreate, TestCaseUpdate, TestCaseResponse,
)
from app.services.test_case_service import TestCaseService

router = APIRouter(prefix="/api/test-cases", tags=["test-cases"])


def _to_response(tc) -> TestCaseResponse:
    return TestCaseResponse(
        id=tc.id,
        title=tc.title,
        input_text=tc.input_text,
        expected_behavior=tc.expected_behavior,
        scoring_criteria=tc.scoring_criteria,
        tags=json.loads(tc.tags) if tc.tags else [],
        difficulty=tc.difficulty,
        category=tc.category,
        created_at=tc.created_at,
        updated_at=tc.updated_at,
    )


@router.post("/", response_model=TestCaseResponse, status_code=201)
async def create_test_case(
    data: TestCaseCreate,
    session: AsyncSession = Depends(get_session),
):
    service = TestCaseService(session)
    tc = await service.create(data)
    return _to_response(tc)


@router.get("/", response_model=dict)
async def list_test_cases(
    difficulty: str | None = Query(None),
    category: str | None = Query(None),
    tag: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
):
    service = TestCaseService(session)
    items, total = await service.list_(
        difficulty=difficulty, category=category, tag=tag,
        skip=skip, limit=limit,
    )
    return {"items": [_to_response(tc) for tc in items], "total": total}


@router.get("/{test_case_id}", response_model=TestCaseResponse)
async def get_test_case(
    test_case_id: int,
    session: AsyncSession = Depends(get_session),
):
    service = TestCaseService(session)
    tc = await service.get_by_id(test_case_id)
    if tc is None:
        raise HTTPException(status_code=404, detail="TestCase not found")
    return _to_response(tc)


@router.put("/{test_case_id}", response_model=TestCaseResponse)
async def update_test_case(
    test_case_id: int,
    data: TestCaseUpdate,
    session: AsyncSession = Depends(get_session),
):
    service = TestCaseService(session)
    tc = await service.update(test_case_id, data)
    if tc is None:
        raise HTTPException(status_code=404, detail="TestCase not found")
    return _to_response(tc)


@router.delete("/{test_case_id}", status_code=204)
async def delete_test_case(
    test_case_id: int,
    session: AsyncSession = Depends(get_session),
):
    service = TestCaseService(session)
    deleted = await service.delete(test_case_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="TestCase not found")
```

更新 `main.py` 注册路由：

```python
# D:\ai work\AgentBench\backend\app\main.py （更新版）
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import init_db
from app.routers import test_cases

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(title="AgentBench", version="0.1.0", lifespan=lifespan)
app.include_router(test_cases.router)

@app.get("/health")
async def health():
    return {"status": "ok"}
```

- [ ] **Step 8: 运行 API 测试确认通过**

Run: `pytest tests/integration/test_test_cases_api.py -v`
Expected: 5 passed

- [ ] **Step 9: 运行全部测试**

Run: `pytest tests/ -v`
Expected: 全部通过

- [ ] **Step 10: 提交**

```bash
git add -A
git commit -m "feat: add TestCase CRUD API with service layer and tests"
```

---

### Task 1.4: 数据模型 + CRUD API — AgentConfig

**Files:**
- Create: `D:\ai work\AgentBench\backend\app\models\agent_config.py`
- Create: `D:\ai work\AgentBench\backend\app\schemas\agent_config.py`
- Create: `D:\ai work\AgentBench\backend\app\services\agent_config_service.py`
- Create: `D:\ai work\AgentBench\backend\app\routers\agent_configs.py`
- Modify: `D:\ai work\AgentBench\backend\app\main.py` (注册 router)
- Test: `D:\ai work\AgentBench\backend\tests\unit\services\test_agent_config_service.py`
- Test: `D:\ai work\AgentBench\backend\tests\integration\test_agent_configs_api.py`

**此 Task 结构与 Task 1.3 完全对称，遵循相同 TDD 流程：写测试 → 失败 → 实现 → 通过。关键实现要点：**

- [ ] **Step 1: 写 AgentConfig 失败测试**

```python
# D:\ai work\AgentBench\backend\tests\unit\services\test_agent_config_service.py
import pytest
from app.schemas.agent_config import AgentConfigCreate
from app.services.agent_config_service import AgentConfigService


class TestAgentConfigService:
    @pytest.mark.asyncio
    async def test_create_agent_config(self, db_session):
        service = AgentConfigService(db_session)
        data = AgentConfigCreate(
            name="animepilot-v1",
            agent_type="openai_compatible",
            config={"endpoint": "http://localhost:8001/chat", "model": "gpt-4.1"},
        )
        ac = await service.create(data)
        assert ac.id is not None
        assert ac.name == "animepilot-v1"
        assert ac.agent_type == "openai_compatible"

    @pytest.mark.asyncio
    async def test_list_agent_configs(self, db_session):
        service = AgentConfigService(db_session)
        for t in ["langgraph", "http", "openai_compatible"]:
            await service.create(AgentConfigCreate(
                name=f"config-{t}", agent_type=t, config={},
            ))
        items, total = await service.list_()
        assert total == 3

    @pytest.mark.asyncio
    async def test_update_agent_config(self, db_session):
        service = AgentConfigService(db_session)
        created = await service.create(AgentConfigCreate(
            name="v1", agent_type="http", config={"endpoint": "http://old"},
        ))
        updated = await service.update(created.id, AgentConfigUpdate(
            config={"endpoint": "http://new"},
        ))
        assert "http://new" in updated.config

    @pytest.mark.asyncio
    async def test_delete_agent_config(self, db_session):
        service = AgentConfigService(db_session)
        created = await service.create(AgentConfigCreate(
            name="del", agent_type="http", config={},
        ))
        await service.delete(created.id)
        assert await service.get_by_id(created.id) is None
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/unit/services/test_agent_config_service.py -v`

- [ ] **Step 3: 实现 AgentConfig 模型、Schema、Service、Router**

```python
# D:\ai work\AgentBench\backend\app\models\agent_config.py
from datetime import datetime

from sqlalchemy import Integer, String, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AgentConfig(Base):
    __tablename__ = "agent_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    agent_type: Mapped[str] = mapped_column(String(50), nullable=False)
    config: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

```python
# D:\ai work\AgentBench\backend\app\schemas\agent_config.py
from datetime import datetime

from pydantic import BaseModel, Field


class AgentConfigCreate(BaseModel):
    name: str = Field(..., max_length=200)
    agent_type: str = Field(..., pattern="^(langgraph|openai_compatible|http|python_fn)$")
    config: dict = Field(default_factory=dict)
    description: str = ""


class AgentConfigUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=200)
    agent_type: str | None = Field(default=None, pattern="^(langgraph|openai_compatible|http|python_fn)$")
    config: dict | None = None
    description: str | None = None


class AgentConfigResponse(BaseModel):
    id: int
    name: str
    agent_type: str
    config: dict
    description: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
```

```python
# D:\ai work\AgentBench\backend\app\services\agent_config_service.py
import json

from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent_config import AgentConfig
from app.schemas.agent_config import AgentConfigCreate, AgentConfigUpdate


class AgentConfigService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, data: AgentConfigCreate) -> AgentConfig:
        ac = AgentConfig(
            name=data.name,
            agent_type=data.agent_type,
            config=json.dumps(data.config, ensure_ascii=False),
            description=data.description,
        )
        self.session.add(ac)
        await self.session.commit()
        await self.session.refresh(ac)
        return ac

    async def list_(self, *, skip: int = 0, limit: int = 50) -> tuple[list[AgentConfig], int]:
        count_query = select(func.count(AgentConfig.id))
        total = (await self.session.execute(count_query)).scalar() or 0

        query = select(AgentConfig).order_by(AgentConfig.created_at.desc()).offset(skip).limit(limit)
        items = list((await self.session.execute(query)).scalars().all())
        return items, total

    async def get_by_id(self, agent_config_id: int) -> AgentConfig | None:
        result = await self.session.execute(
            select(AgentConfig).where(AgentConfig.id == agent_config_id)
        )
        return result.scalar_one_or_none()

    async def update(self, agent_config_id: int, data: AgentConfigUpdate) -> AgentConfig | None:
        ac = await self.get_by_id(agent_config_id)
        if ac is None:
            return None
        update_data = data.model_dump(exclude_unset=True)
        if "config" in update_data and update_data["config"] is not None:
            update_data["config"] = json.dumps(update_data["config"], ensure_ascii=False)
        for key, value in update_data.items():
            setattr(ac, key, value)
        await self.session.commit()
        await self.session.refresh(ac)
        return ac

    async def delete(self, agent_config_id: int) -> bool:
        result = await self.session.execute(
            delete(AgentConfig).where(AgentConfig.id == agent_config_id)
        )
        await self.session.commit()
        return result.rowcount > 0
```

```python
# D:\ai work\AgentBench\backend\app\routers\agent_configs.py
import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.schemas.agent_config import (
    AgentConfigCreate, AgentConfigUpdate, AgentConfigResponse,
)
from app.services.agent_config_service import AgentConfigService

router = APIRouter(prefix="/api/agent-configs", tags=["agent-configs"])


def _to_response(ac) -> AgentConfigResponse:
    return AgentConfigResponse(
        id=ac.id,
        name=ac.name,
        agent_type=ac.agent_type,
        config=json.loads(ac.config) if ac.config else {},
        description=ac.description,
        created_at=ac.created_at,
        updated_at=ac.updated_at,
    )


@router.post("/", response_model=AgentConfigResponse, status_code=201)
async def create_agent_config(
    data: AgentConfigCreate,
    session: AsyncSession = Depends(get_session),
):
    service = AgentConfigService(session)
    ac = await service.create(data)
    return _to_response(ac)


@router.get("/", response_model=dict)
async def list_agent_configs(
    session: AsyncSession = Depends(get_session),
):
    service = AgentConfigService(session)
    items, total = await service.list_()
    return {"items": [_to_response(ac) for ac in items], "total": total}


@router.get("/{agent_config_id}", response_model=AgentConfigResponse)
async def get_agent_config(
    agent_config_id: int,
    session: AsyncSession = Depends(get_session),
):
    service = AgentConfigService(session)
    ac = await service.get_by_id(agent_config_id)
    if ac is None:
        raise HTTPException(status_code=404, detail="AgentConfig not found")
    return _to_response(ac)


@router.put("/{agent_config_id}", response_model=AgentConfigResponse)
async def update_agent_config(
    agent_config_id: int,
    data: AgentConfigUpdate,
    session: AsyncSession = Depends(get_session),
):
    service = AgentConfigService(session)
    ac = await service.update(agent_config_id, data)
    if ac is None:
        raise HTTPException(status_code=404, detail="AgentConfig not found")
    return _to_response(ac)


@router.delete("/{agent_config_id}", status_code=204)
async def delete_agent_config(
    agent_config_id: int,
    session: AsyncSession = Depends(get_session),
):
    service = AgentConfigService(session)
    deleted = await service.delete(agent_config_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="AgentConfig not found")
```

更新 `main.py` 追加 router：

```python
# 在 main.py 中追加
from app.routers import agent_configs
app.include_router(agent_configs.router)
```

- [ ] **Step 4: 运行全部测试确认通过**

Run: `pytest tests/ -v`

- [ ] **Step 5: 写 API 集成测试（结构参照 Task 1.3 的 test_test_cases_api.py）**

```python
# D:\ai work\AgentBench\backend\tests\integration\test_agent_configs_api.py
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
```

- [ ] **Step 6: 提交**

```bash
git add -A
git commit -m "feat: add AgentConfig CRUD API with service layer and tests"
```

---

### Task 1.5: 数据模型 — TestRun, RunStep, EvaluationResult

**Files:**
- Create: `D:\ai work\AgentBench\backend\app\models\test_run.py`
- Create: `D:\ai work\AgentBench\backend\app\models\run_step.py`
- Create: `D:\ai work\AgentBench\backend\app\models\evaluation_result.py`
- Create: `D:\ai work\AgentBench\backend\app\schemas\test_run.py`
- Create: `D:\ai work\AgentBench\backend\app\schemas\run_step.py`
- Create: `D:\ai work\AgentBench\backend\app\schemas\evaluation.py`
- Test: `D:\ai work\AgentBench\backend\tests\unit\models\test_test_run.py`

- [ ] **Step 1: 写 TestRun/RunStep/EvaluationResult 模型测试**

```python
# D:\ai work\AgentBench\backend\tests\unit\models\test_test_run.py
import pytest

from app.models.test_run import TestRun
from app.models.run_step import RunStep
from app.models.evaluation_result import EvaluationResult


class TestTestRunModel:
    @pytest.mark.asyncio
    async def test_create_test_run(self, db_session):
        tr = TestRun(
            test_case_id=1,
            agent_config_id=1,
            status="pending",
        )
        db_session.add(tr)
        await db_session.commit()
        await db_session.refresh(tr)
        assert tr.id is not None
        assert tr.status == "pending"


class TestRunStepModel:
    @pytest.mark.asyncio
    async def test_create_run_step(self, db_session):
        step = RunStep(
            test_run_id=1,
            sequence=1,
            step_type="intent_detection",
            name="IntentDetector",
            input_json='{"query": "搜索动漫"}',
            output_json='{"intent": "search"}',
            latency_ms=150,
            status="success",
        )
        db_session.add(step)
        await db_session.commit()
        await db_session.refresh(step)
        assert step.id is not None
        assert step.latency_ms == 150


class TestEvaluationResultModel:
    @pytest.mark.asyncio
    async def test_create_evaluation(self, db_session):
        ev = EvaluationResult(
            test_run_id=1,
            judge_type="rule",
            overall_score=4.0,
            accuracy_score=4.0,
            hallucination_score=5.0,
            tool_correctness_score=4.0,
            expression_quality_score=3.0,
            judge_reasoning="回答准确，无明显幻觉",
        )
        db_session.add(ev)
        await db_session.commit()
        await db_session.refresh(ev)
        assert ev.id is not None
        assert ev.overall_score == 4.0
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/unit/models/test_test_run.py -v`

- [ ] **Step 3: 实现三个模型**

```python
# D:\ai work\AgentBench\backend\app\models\test_run.py
from datetime import datetime

from sqlalchemy import Integer, String, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class TestRun(Base):
    __tablename__ = "test_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    test_case_id: Mapped[int] = mapped_column(Integer, ForeignKey("test_cases.id"), nullable=False)
    agent_config_id: Mapped[int] = mapped_column(Integer, ForeignKey("agent_configs.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    agent_output: Mapped[str] = mapped_column(Text, nullable=False, default="")
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cost_estimate: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    error_message: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
```

```python
# D:\ai work\AgentBench\backend\app\models\run_step.py
from sqlalchemy import Integer, String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class RunStep(Base):
    __tablename__ = "run_steps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    test_run_id: Mapped[int] = mapped_column(Integer, ForeignKey("test_runs.id"), nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    step_type: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    input_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    output_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    token_usage_input: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    token_usage_output: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="success")
    error_message: Mapped[str] = mapped_column(Text, nullable=True)
```

```python
# D:\ai work\AgentBench\backend\app\models\evaluation_result.py
from datetime import datetime

from sqlalchemy import Integer, String, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class EvaluationResult(Base):
    __tablename__ = "evaluation_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    test_run_id: Mapped[int] = mapped_column(Integer, ForeignKey("test_runs.id"), nullable=False)
    judge_type: Mapped[str] = mapped_column(String(20), nullable=False)
    overall_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    accuracy_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    hallucination_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    tool_correctness_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    expression_quality_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    judge_reasoning: Mapped[str] = mapped_column(Text, nullable=False, default="")
    rule_results: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
```

- [ ] **Step 4: 实现 Pydantic Schemas**

```python
# D:\ai work\AgentBench\backend\app\schemas\test_run.py
from datetime import datetime
from pydantic import BaseModel


class TestRunResponse(BaseModel):
    id: int
    test_case_id: int
    agent_config_id: int
    status: str
    agent_output: str
    duration_ms: int
    total_tokens: int
    cost_estimate: float
    error_message: str | None
    created_at: datetime
    model_config = {"from_attributes": True}
```

```python
# D:\ai work\AgentBench\backend\app\schemas\run_step.py
import json
from pydantic import BaseModel


class RunStepResponse(BaseModel):
    id: int
    test_run_id: int
    sequence: int
    step_type: str
    name: str
    input_json: dict
    output_json: dict
    latency_ms: int
    token_usage_input: int
    token_usage_output: int
    status: str
    error_message: str | None

    model_config = {"from_attributes": True}
```

```python
# D:\ai work\AgentBench\backend\app\schemas\evaluation.py
from datetime import datetime
from pydantic import BaseModel


class EvaluationResultResponse(BaseModel):
    id: int
    test_run_id: int
    judge_type: str
    overall_score: float
    accuracy_score: float | None
    hallucination_score: float | None
    tool_correctness_score: float | None
    expression_quality_score: float | None
    judge_reasoning: str
    rule_results: dict | None
    created_at: datetime

    model_config = {"from_attributes": True}
```

- [ ] **Step 5: 运行全部测试确认通过**

Run: `pytest tests/ -v`

- [ ] **Step 6: 提交**

```bash
git add -A
git commit -m "feat: add TestRun, RunStep, EvaluationResult models and schemas"
```

---

**Phase 1 完成检查点：**
- [ ] `uvicorn app.main:app` 可启动，`/health` 返回 200
- [ ] `POST /api/test-cases/` 可创建测试用例
- [ ] `GET /api/test-cases/` 可列表（含筛选）
- [ ] `POST /api/agent-configs/` 可创建 Agent 配置
- [ ] 所有测试通过：`pytest tests/ -v`

---

## Phase 2: Agent Runner 适配器 + Trace 收集 + 运行 API

**交付物：** 四种 Agent 适配器可运行测试用例，Trace 步骤写入数据库，运行详情 API 可查。

---

### Task 2.1: TraceCollector 统一 trace 收集器

**Files:**
- Create: `D:\ai work\AgentBench\backend\app\utils\__init__.py`
- Create: `D:\ai work\AgentBench\backend\app\utils\trace_collector.py`
- Test: `D:\ai work\AgentBench\backend\tests\unit\utils\__init__.py`
- Test: `D:\ai work\AgentBench\backend\tests\unit\utils\test_trace_collector.py`

- [ ] **Step 1: 写 TraceCollector 失败测试**

```python
# D:\ai work\AgentBench\backend\tests\unit\utils\test_trace_collector.py
import pytest
import time
from app.utils.trace_collector import TraceCollector


class TestTraceCollector:
    def test_record_step(self):
        collector = TraceCollector()
        collector.record_step(
            step_type="intent_detection",
            name="IntentDetector",
            input_data={"query": "搜索动漫"},
            output_data={"intent": "search"},
            latency_ms=100,
            token_input=50,
            token_output=20,
            status="success",
        )
        steps = collector.get_steps()
        assert len(steps) == 1
        assert steps[0]["step_type"] == "intent_detection"
        assert steps[0]["latency_ms"] == 100

    def test_record_step_with_error(self):
        collector = TraceCollector()
        collector.record_step(
            step_type="llm_generation",
            name="LLMCall",
            input_data={},
            output_data={},
            latency_ms=5000,
            status="error",
            error_message="API timeout",
        )
        steps = collector.get_steps()
        assert steps[0]["status"] == "error"
        assert steps[0]["error_message"] == "API timeout"

    def test_sequence_auto_increment(self):
        collector = TraceCollector()
        collector.record_step(step_type="a", name="a", input_data={}, output_data={}, latency_ms=10, status="success")
        collector.record_step(step_type="b", name="b", input_data={}, output_data={}, latency_ms=10, status="success")
        steps = collector.get_steps()
        assert steps[0]["sequence"] == 1
        assert steps[1]["sequence"] == 2

    def test_to_run_step_dicts(self):
        collector = TraceCollector()
        collector.record_step(
            step_type="tool_call", name="SearchTool", input_data={"q": "x"},
            output_data={"result": "y"}, latency_ms=200, token_input=10, token_output=30,
            status="success",
        )
        dicts = collector.to_run_step_dicts(test_run_id=42)
        assert len(dicts) == 1
        assert dicts[0]["test_run_id"] == 42
        assert dicts[0]["sequence"] == 1
```

- [ ] **Step 2: 运行测试确认失败**

- [ ] **Step 3: 实现 TraceCollector**

```python
# D:\ai work\AgentBench\backend\app\utils\__init__.py
# 留空
```

```python
# D:\ai work\AgentBench\backend\app\utils\trace_collector.py
import json
import time
from contextlib import contextmanager


class TraceCollector:
    def __init__(self):
        self._steps: list[dict] = []
        self._sequence = 0

    def record_step(
        self,
        *,
        step_type: str,
        name: str = "",
        input_data: dict | None = None,
        output_data: dict | None = None,
        latency_ms: int = 0,
        token_input: int = 0,
        token_output: int = 0,
        status: str = "success",
        error_message: str | None = None,
    ) -> None:
        self._sequence += 1
        self._steps.append({
            "sequence": self._sequence,
            "step_type": step_type,
            "name": name,
            "input_json": json.dumps(input_data or {}, ensure_ascii=False),
            "output_json": json.dumps(output_data or {}, ensure_ascii=False),
            "latency_ms": latency_ms,
            "token_usage_input": token_input,
            "token_usage_output": token_output,
            "status": status,
            "error_message": error_message,
        })

    @contextmanager
    def step(self, *, step_type: str, name: str = "", input_data: dict | None = None):
        """上下文管理器，自动计时并记录步骤。"""
        start = time.monotonic()
        yield
        latency_ms = int((time.monotonic() - start) * 1000)
        self.record_step(
            step_type=step_type, name=name,
            input_data=input_data, latency_ms=latency_ms,
        )

    def get_steps(self) -> list[dict]:
        return list(self._steps)

    def to_run_step_dicts(self, test_run_id: int) -> list[dict]:
        result = []
        for s in self._steps:
            d = {"test_run_id": test_run_id}
            d.update(s)
            result.append(d)
        return result

    def total_tokens(self) -> int:
        return sum(s["token_usage_input"] + s["token_usage_output"] for s in self._steps)

    def total_latency_ms(self) -> int:
        return sum(s["latency_ms"] for s in self._steps)
```

- [ ] **Step 4: 运行测试确认通过**

Run: `pytest tests/unit/utils/test_trace_collector.py -v`

- [ ] **Step 5: 提交**

```bash
git add -A
git commit -m "feat: add TraceCollector for unified trace recording"
```

---

### Task 2.2: AgentRunner 抽象基类

**Files:**
- Create: `D:\ai work\AgentBench\backend\app\runners\__init__.py`
- Create: `D:\ai work\AgentBench\backend\app\runners\base.py`

- [ ] **Step 1: 实现 AgentRunner 抽象基类**

```python
# D:\ai work\AgentBench\backend\app\runners\__init__.py
# 留空
```

```python
# D:\ai work\AgentBench\backend\app\runners\base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from app.utils.trace_collector import TraceCollector


@dataclass
class RunResult:
    output: str = ""
    collector: TraceCollector = field(default_factory=TraceCollector)
    error: str | None = None


class AgentRunner(ABC):
    """Agent 执行适配器的抽象基类。

    子类必须实现 run 方法，将 Agent 的执行过程记录到 TraceCollector 中。
    """

    def __init__(self, config: dict):
        self.config = config

    @abstractmethod
    async def run(self, test_input: str) -> RunResult:
        """执行 Agent 并返回结果 + trace。"""
        ...
```

- [ ] **Step 2: 提交**

```bash
git add -A
git commit -m "feat: add AgentRunner abstract base class and RunResult dataclass"
```

---

### Task 2.3: OpenAI Compatible Adapter

**Files:**
- Create: `D:\ai work\AgentBench\backend\app\runners\openai_adapter.py`
- Test: `D:\ai work\AgentBench\backend\tests\unit\runners\__init__.py`
- Test: `D:\ai work\AgentBench\backend\tests\unit\runners\test_openai_adapter.py`

- [ ] **Step 1: 写 OpenAI Adapter 失败测试（mock HTTP 调用）**

```python
# D:\ai work\AgentBench\backend\tests\unit\runners\test_openai_adapter.py
import pytest
from unittest.mock import AsyncMock, patch

from app.runners.openai_adapter import OpenAICompatibleRunner


class TestOpenAICompatibleRunner:
    @pytest.mark.asyncio
    async def test_run_records_trace(self):
        runner = OpenAICompatibleRunner({
            "endpoint": "http://fake-api/v1/chat/completions",
            "model": "gpt-4.1",
            "api_key": "test-key",
        })

        mock_response = {
            "choices": [{"message": {"content": "CLANNAD 是一部经典治愈系动画。"}}],
            "usage": {"prompt_tokens": 50, "completion_tokens": 100, "total_tokens": 150},
        }

        with patch("app.runners.openai_adapter.httpx.AsyncClient") as mock_client_cls:
            mock_post = AsyncMock()
            mock_post.return_value = type("R", (), {"json": lambda: mock_response, "raise_for_status": lambda: None})()
            mock_client_instance = AsyncMock()
            mock_client_instance.post = mock_post
            mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_instance.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client_instance

            result = await runner.run("推荐一部治愈系动画")

        assert "CLANNAD" in result.output
        assert result.error is None
        steps = result.collector.get_steps()
        assert len(steps) >= 1
        assert steps[0]["step_type"] == "llm_generation"
        assert steps[0]["token_usage_input"] == 50
        assert steps[0]["token_usage_output"] == 100

    @pytest.mark.asyncio
    async def test_run_handles_api_error(self):
        runner = OpenAICompatibleRunner({
            "endpoint": "http://fake-api/v1/chat/completions",
            "model": "gpt-4.1",
            "api_key": "test-key",
        })

        with patch("app.runners.openai_adapter.httpx.AsyncClient") as mock_client_cls:
            mock_post = AsyncMock()
            mock_post.return_value = type("R", (), {
                "raise_for_status": lambda: (_ for _ in ()).throw(Exception("API Error")),
                "text": "Internal Server Error",
            })()
            mock_client_instance = AsyncMock()
            mock_client_instance.post = mock_post
            mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_instance.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client_instance

            result = await runner.run("测试")

        assert result.error is not None
        assert "API Error" in result.error
```

- [ ] **Step 2: 运行测试确认失败**

- [ ] **Step 3: 实现 OpenAI Adapter**

```python
# D:\ai work\AgentBench\backend\app\runners\openai_adapter.py
import httpx

from app.runners.base import AgentRunner, RunResult


class OpenAICompatibleRunner(AgentRunner):
    """通过 OpenAI 兼容 API 执行 LLM 调用。"""

    async def run(self, test_input: str) -> RunResult:
        collector = self._new_collector()
        endpoint = self.config.get("endpoint", "https://api.openai.com/v1/chat/completions")
        model = self.config.get("model", "gpt-4.1")
        api_key = self.config.get("api_key", "")

        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        payload = {
            "model": model,
            "messages": [{"role": "user", "content": test_input}],
        }

        try:
            with collector.step(step_type="llm_generation", name="OpenAI Chat", input_data=payload):
                async with httpx.AsyncClient(timeout=60) as client:
                    resp = await client.post(endpoint, json=payload, headers=headers)
                    resp.raise_for_status()
                    data = resp.json()

            choices = data.get("choices", [])
            output = choices[0]["message"]["content"] if choices else ""
            usage = data.get("usage", {})

            # 更新最后一步的 token 使用量
            if collector.get_steps():
                collector.get_steps()[-1]["token_usage_input"] = usage.get("prompt_tokens", 0)
                collector.get_steps()[-1]["token_usage_output"] = usage.get("completion_tokens", 0)

            return RunResult(output=output, collector=collector)

        except Exception as e:
            collector.record_step(
                step_type="llm_generation", name="OpenAI Chat",
                input_data=payload, status="error", error_message=str(e),
            )
            return RunResult(output="", collector=collector, error=str(e))

    def _new_collector(self):
        from app.utils.trace_collector import TraceCollector
        return TraceCollector()
```

- [ ] **Step 4: 运行测试确认通过**

Run: `pytest tests/unit/runners/test_openai_adapter.py -v`

- [ ] **Step 5: 提交**

```bash
git add -A
git commit -m "feat: add OpenAI Compatible adapter with trace recording"
```

---

### Task 2.4: HTTP Adapter

**Files:**
- Create: `D:\ai work\AgentBench\backend\app\runners\http_adapter.py`
- Test: `D:\ai work\AgentBench\backend\tests\unit\runners\test_http_adapter.py`

- [ ] **Step 1: 写 HTTP Adapter 失败测试**

```python
# D:\ai work\AgentBench\backend\tests\unit\runners\test_http_adapter.py
import pytest
from unittest.mock import AsyncMock, patch

from app.runners.http_adapter import HTTPRunner


class TestHTTPRunner:
    @pytest.mark.asyncio
    async def test_run_posts_to_endpoint(self):
        runner = HTTPRunner({
            "endpoint": "http://localhost:9000/chat",
            "method": "POST",
            "headers": {"X-API-Key": "test"},
        })
        mock_response_data = {
            "output": "你好，我是 Agent 回复。",
            "trace": [
                {"step_type": "intent_detection", "name": "Intent", "latency_ms": 50, "status": "success"},
            ],
        }

        with patch("app.runners.http_adapter.httpx.AsyncClient") as mock_cls:
            mock_post = AsyncMock()
            mock_post.return_value = type("R", (), {"json": lambda: mock_response_data, "raise_for_status": lambda: None})()
            mock_instance = AsyncMock()
            mock_instance.post = mock_post
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=False)
            mock_cls.return_value = mock_instance

            result = await runner.run("你好")

        assert "Agent 回复" in result.output
        steps = result.collector.get_steps()
        assert len(steps) >= 1  # 至少有 agent_response 步骤 + 来自 trace 的步骤

    @pytest.mark.asyncio
    async def test_run_handles_connection_error(self):
        runner = HTTPRunner({"endpoint": "http://localhost:9999/chat"})

        with patch("app.runners.http_adapter.httpx.AsyncClient") as mock_cls:
            mock_instance = AsyncMock()
            mock_instance.post = AsyncMock(side_effect=Exception("Connection refused"))
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=False)
            mock_cls.return_value = mock_instance

            result = await runner.run("测试")

        assert result.error is not None
```

- [ ] **Step 2: 实现 HTTP Adapter**

```python
# D:\ai work\AgentBench\backend\app\runners\http_adapter.py
import httpx

from app.runners.base import AgentRunner, RunResult


class HTTPRunner(AgentRunner):
    """通过 HTTP 端点调用自定义 Agent。约定响应格式：{"output": str, "trace": list[dict]}。"""

    async def run(self, test_input: str) -> RunResult:
        from app.utils.trace_collector import TraceCollector
        collector = TraceCollector()

        endpoint = self.config.get("endpoint", "")
        method = self.config.get("method", "POST").upper()
        headers = self.config.get("headers", {})
        timeout = self.config.get("timeout", 60)

        payload = {"input": test_input}

        try:
            with collector.step(step_type="http_call", name=f"HTTP {method}", input_data=payload):
                async with httpx.AsyncClient(timeout=timeout) as client:
                    resp = await client.request(method, endpoint, json=payload, headers=headers)
                    resp.raise_for_status()
                    data = resp.json()

            output = data.get("output", "")

            # 从响应中提取 trace 步骤（如有）
            for t in data.get("trace", []):
                collector.record_step(
                    step_type=t.get("step_type", "unknown"),
                    name=t.get("name", ""),
                    input_data=t.get("input"),
                    output_data=t.get("output"),
                    latency_ms=t.get("latency_ms", 0),
                    token_input=t.get("token_input", 0),
                    token_output=t.get("token_output", 0),
                    status=t.get("status", "success"),
                    error_message=t.get("error_message"),
                )

            return RunResult(output=output, collector=collector)

        except Exception as e:
            collector.record_step(
                step_type="http_call", name=f"HTTP {method}",
                input_data=payload, status="error", error_message=str(e),
            )
            return RunResult(output="", collector=collector, error=str(e))
```

- [ ] **Step 3: 运行测试确认通过，提交**

Run: `pytest tests/unit/runners/test_http_adapter.py -v`

```bash
git add -A
git commit -m "feat: add HTTP adapter for custom Agent endpoints"
```

---

### Task 2.5: Python Function Adapter

**Files:**
- Create: `D:\ai work\AgentBench\backend\app\runners\python_fn_adapter.py`
- Test: `D:\ai work\AgentBench\backend\tests\unit\runners\test_python_fn_adapter.py`

- [ ] **Step 1: 写 Python Fn Adapter 失败测试**

```python
# D:\ai work\AgentBench\backend\tests\unit\runners\test_python_fn_adapter.py
import pytest
from app.runners.python_fn_adapter import PythonFnRunner


class TestPythonFnRunner:
    @pytest.mark.asyncio
    async def test_run_simple_function(self):
        async def my_agent(query: str) -> str:
            return f"收到：{query}"

        runner = PythonFnRunner({"function": my_agent})
        result = await runner.run("测试输入")
        assert result.output == "收到：测试输入"
        assert result.error is None

    @pytest.mark.asyncio
    async def test_run_function_with_trace_decorator(self):
        from app.runners.python_fn_adapter import trace_step

        @trace_step(step_type="intent_detection", name="MyDetector")
        async def detect_intent(query: str) -> str:
            return "search"

        async def my_agent(query: str, step_collector) -> str:
            intent = await detect_intent(query)
            return f"意图：{intent}"

        runner = PythonFnRunner({"function": my_agent})
        result = await runner.run("搜索动漫")
        assert "search" in result.output or "意图" in result.output

    @pytest.mark.asyncio
    async def test_run_function_raises_error(self):
        async def broken_agent(query: str) -> str:
            raise ValueError("测试错误")

        runner = PythonFnRunner({"function": broken_agent})
        result = await runner.run("测试")
        assert result.error is not None
        assert "测试错误" in result.error
```

- [ ] **Step 2: 实现 Python Fn Adapter + trace_step 装饰器**

```python
# D:\ai work\AgentBench\backend\app\runners\python_fn_adapter.py
import inspect
import functools
from app.runners.base import AgentRunner, RunResult


class PythonFnRunner(AgentRunner):
    """直接调用 Python async 函数。通过 @trace_step 装饰器收集 trace。"""

    async def run(self, test_input: str) -> RunResult:
        from app.utils.trace_collector import TraceCollector
        collector = TraceCollector()

        fn = self.config.get("function")
        if fn is None:
            return RunResult(output="", collector=collector, error="No function provided in config")

        # 注入 collector 到函数参数（如果函数接受 step_collector 参数）
        try:
            sig = inspect.signature(fn)
            if "step_collector" in sig.parameters:
                output = await fn(test_input, step_collector=collector)
            else:
                output = await fn(test_input)

            if not collector.get_steps():
                collector.record_step(
                    step_type="function_call", name=fn.__name__,
                    input_data={"input": test_input},
                    output_data={"output": output},
                )

            return RunResult(output=str(output) if output else "", collector=collector)

        except Exception as e:
            collector.record_step(
                step_type="function_call", name=fn.__name__,
                input_data={"input": test_input},
                status="error", error_message=str(e),
            )
            return RunResult(output="", collector=collector, error=str(e))


def trace_step(*, step_type: str, name: str = ""):
    """装饰器：将被装饰函数的执行记录为一个 trace 步骤。"""
    def decorator(fn):
        @functools.wraps(fn)
        async def wrapper(*args, **kwargs):
            # 从 kwargs 或 caller 注入的 step_collector 获取 collector
            collector = kwargs.get("step_collector")
            if collector and hasattr(collector, "record_step"):
                with collector.step(step_type=step_type, name=name or fn.__name__):
                    return await fn(*args, **{k: v for k, v in kwargs.items() if k != "step_collector"})
            return await fn(*args, **kwargs)
        return wrapper
    return decorator
```

- [ ] **Step 3: 运行测试确认通过，提交**

Run: `pytest tests/unit/runners/test_python_fn_adapter.py -v`

```bash
git add -A
git commit -m "feat: add Python Function adapter with trace_step decorator"
```

---

### Task 2.6: LangGraph Adapter

**Files:**
- Create: `D:\ai work\AgentBench\backend\app\runners\langgraph_adapter.py`
- Test: `D:\ai work\AgentBench\backend\tests\unit\runners\test_langgraph_adapter.py`

- [ ] **Step 1: 写 LangGraph Adapter 失败测试（mock LangGraph）**

```python
# D:\ai work\AgentBench\backend\tests\unit\runners\test_langgraph_adapter.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.runners.langgraph_adapter import LangGraphRunner


class TestLangGraphRunner:
    @pytest.mark.asyncio
    async def test_run_compiled_graph(self):
        mock_graph = MagicMock()
        mock_graph.ainvoke = AsyncMock(return_value={
            "messages": [{"role": "assistant", "content": "推荐 CLANNAD。"}],
        })

        runner = LangGraphRunner({"graph": mock_graph})
        result = await runner.run("推荐治愈系动漫")
        assert "CLANNAD" in result.output
        steps = result.collector.get_steps()
        assert len(steps) >= 1

    @pytest.mark.asyncio
    async def test_run_handles_graph_error(self):
        mock_graph = MagicMock()
        mock_graph.ainvoke = AsyncMock(side_effect=Exception("Graph execution failed"))

        runner = LangGraphRunner({"graph": mock_graph})
        result = await runner.run("测试")
        assert result.error is not None
```

- [ ] **Step 2: 实现 LangGraph Adapter**

```python
# D:\ai work\AgentBench\backend\app\runners\langgraph_adapter.py
from app.runners.base import AgentRunner, RunResult


class LangGraphRunner(AgentRunner):
    """执行编译后的 LangGraph workflow。config 中需传入 'graph' 键对应的编译图。"""

    async def run(self, test_input: str) -> RunResult:
        from app.utils.trace_collector import TraceCollector
        collector = TraceCollector()

        graph = self.config.get("graph")
        if graph is None:
            return RunResult(output="", collector=collector, error="No 'graph' in config")

        state_input = {"messages": [{"role": "user", "content": test_input}]}

        try:
            with collector.step(step_type="graph_execution", name="LangGraph", input_data=state_input):
                result_state = await graph.ainvoke(state_input)

            messages = result_state.get("messages", [])
            output = ""
            for msg in messages:
                if hasattr(msg, "content") and hasattr(msg, "type") and msg.type == "ai":
                    output += msg.content
                elif isinstance(msg, dict) and msg.get("role") == "assistant":
                    output += msg.get("content", "")

            return RunResult(output=output, collector=collector)

        except Exception as e:
            collector.record_step(
                step_type="graph_execution", name="LangGraph",
                input_data=state_input, status="error", error_message=str(e),
            )
            return RunResult(output="", collector=collector, error=str(e))
```

- [ ] **Step 3: 运行测试确认通过，提交**

Run: `pytest tests/unit/runners/test_langgraph_adapter.py -v`

```bash
git add -A
git commit -m "feat: add LangGraph adapter with graph execution trace"
```

---

### Task 2.7: RunnerService — 调度测试运行 + 运行 API

**Files:**
- Create: `D:\ai work\AgentBench\backend\app\services\runner_service.py`
- Create: `D:\ai work\AgentBench\backend\app\routers\test_runs.py`
- Modify: `D:\ai work\AgentBench\backend\app\main.py`
- Test: `D:\ai work\AgentBench\backend\tests\unit\services\test_runner_service.py`
- Test: `D:\ai work\AgentBench\backend\tests\integration\test_test_runs_api.py`

- [ ] **Step 1: 写 RunnerService 失败测试**

```python
# D:\ai work\AgentBench\backend\tests\unit\services\test_runner_service.py
import pytest
from unittest.mock import AsyncMock, patch
from app.runners.openai_adapter import OpenAICompatibleRunner
from app.runners.http_adapter import HTTPRunner
from app.runners.python_fn_adapter import PythonFnRunner
from app.models.test_case import TestCase
from app.models.agent_config import AgentConfig
from app.models.test_run import TestRun
from app.models.run_step import RunStep
from app.services.runner_service import RunnerService


class TestRunnerService:
    @pytest.mark.asyncio
    async def test_run_single_test_case(self, db_session):
        # 准备数据
        tc = TestCase(title="t", input_text="hi", expected_behavior="hello", scoring_criteria="")
        db_session.add(tc)
        ac = AgentConfig(name="test-ac", agent_type="python_fn", config='{"function": "mock"}')
        db_session.add(ac)
        await db_session.commit()

        mock_result = type("R", (), {"output": "hello world", "collector": type("C", (), {"get_steps": lambda: [], "total_tokens": lambda: 0, "total_latency_ms": lambda: 10})(), "error": None})()

        service = RunnerService(db_session)
        with patch.object(service, "_create_runner", return_value=PythonFnRunner({"function": AsyncMock(return_value="hello world")})):
            pass  # 实际测试在集成测试中更合适

    @pytest.mark.asyncio
    async def test_select_adapter_type(self, db_session):
        service = RunnerService(db_session)
        assert service._adapter_class("openai_compatible") == OpenAICompatibleRunner
        assert service._adapter_class("http") == HTTPRunner
        assert service._adapter_class("python_fn") == PythonFnRunner

    @pytest.mark.asyncio
    async def test_invalid_adapter_type_raises(self, db_session):
        service = RunnerService(db_session)
        with pytest.raises(ValueError, match="Unknown agent type"):
            service._adapter_class("nonexistent_type")
```

- [ ] **Step 2: 实现 RunnerService**

```python
# D:\ai work\AgentBench\backend\app\services\runner_service.py
import json
import time
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.test_case import TestCase
from app.models.agent_config import AgentConfig
from app.models.test_run import TestRun
from app.models.run_step import RunStep
from app.runners.base import RunResult
from app.runners.openai_adapter import OpenAICompatibleRunner
from app.runners.http_adapter import HTTPRunner
from app.runners.python_fn_adapter import PythonFnRunner
from app.runners.langgraph_adapter import LangGraphRunner


ADAPTER_MAP = {
    "openai_compatible": OpenAICompatibleRunner,
    "http": HTTPRunner,
    "python_fn": PythonFnRunner,
    "langgraph": LangGraphRunner,
}


class RunnerService:
    def __init__(self, session: AsyncSession):
        self.session = session

    def _adapter_class(self, agent_type: str):
        cls = ADAPTER_MAP.get(agent_type)
        if cls is None:
            raise ValueError(f"Unknown agent type: {agent_type}")
        return cls

    async def run_single(self, test_case_id: int, agent_config_id: int) -> TestRun:
        # 获取 test case 和 agent config
        tc = (await self.session.execute(select(TestCase).where(TestCase.id == test_case_id))).scalar_one_or_none()
        ac = (await self.session.execute(select(AgentConfig).where(AgentConfig.id == agent_config_id))).scalar_one_or_none()
        if tc is None:
            raise ValueError(f"TestCase {test_case_id} not found")
        if ac is None:
            raise ValueError(f"AgentConfig {agent_config_id} not found")

        # 创建 TestRun
        test_run = TestRun(
            test_case_id=test_case_id,
            agent_config_id=agent_config_id,
            status="running",
        )
        self.session.add(test_run)
        await self.session.commit()
        await self.session.refresh(test_run)

        # 创建适配器并执行
        config_dict = json.loads(ac.config) if ac.config else {}
        adapter_cls = self._adapter_class(ac.agent_type)
        runner = adapter_cls(config_dict)

        start_time = time.monotonic()
        try:
            result: RunResult = await runner.run(tc.input_text)
            elapsed_ms = int((time.monotonic() - start_time) * 1000)

            test_run.status = "error" if result.error else "success"
            test_run.agent_output = result.output
            test_run.duration_ms = elapsed_ms
            test_run.total_tokens = result.collector.total_tokens()
            test_run.error_message = result.error

            # 写入 RunSteps
            for step_dict in result.collector.to_run_step_dicts(test_run.id):
                self.session.add(RunStep(**step_dict))

        except Exception as e:
            elapsed_ms = int((time.monotonic() - start_time) * 1000)
            test_run.status = "error"
            test_run.error_message = str(e)
            test_run.duration_ms = elapsed_ms

        await self.session.commit()
        await self.session.refresh(test_run)
        return test_run
```

- [ ] **Step 3: 实现运行 API Router**

```python
# D:\ai work\AgentBench\backend\app\routers\test_runs.py
import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.test_run import TestRun
from app.models.run_step import RunStep
from app.schemas.test_run import TestRunResponse
from app.schemas.run_step import RunStepResponse
from app.services.runner_service import RunnerService

router = APIRouter(prefix="/api/test-runs", tags=["test-runs"])


def _run_to_response(tr: TestRun) -> TestRunResponse:
    return TestRunResponse(
        id=tr.id,
        test_case_id=tr.test_case_id,
        agent_config_id=tr.agent_config_id,
        status=tr.status,
        agent_output=tr.agent_output,
        duration_ms=tr.duration_ms,
        total_tokens=tr.total_tokens,
        cost_estimate=tr.cost_estimate,
        error_message=tr.error_message,
        created_at=tr.created_at,
    )


def _step_to_response(rs: RunStep) -> RunStepResponse:
    return RunStepResponse(
        id=rs.id,
        test_run_id=rs.test_run_id,
        sequence=rs.sequence,
        step_type=rs.step_type,
        name=rs.name,
        input_json=json.loads(rs.input_json) if rs.input_json else {},
        output_json=json.loads(rs.output_json) if rs.output_json else {},
        latency_ms=rs.latency_ms,
        token_usage_input=rs.token_usage_input,
        token_usage_output=rs.token_usage_output,
        status=rs.status,
        error_message=rs.error_message,
    )


@router.post("/")
async def run_test(
    test_case_id: int,
    agent_config_id: int,
    session: AsyncSession = Depends(get_session),
):
    service = RunnerService(session)
    try:
        test_run = await service.run_single(test_case_id, agent_config_id)
        return _run_to_response(test_run)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{test_run_id}", response_model=TestRunResponse)
async def get_test_run(
    test_run_id: int,
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(select(TestRun).where(TestRun.id == test_run_id))
    tr = result.scalar_one_or_none()
    if tr is None:
        raise HTTPException(status_code=404, detail="TestRun not found")
    return _run_to_response(tr)


@router.get("/{test_run_id}/steps", response_model=list[RunStepResponse])
async def get_run_steps(
    test_run_id: int,
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(RunStep).where(RunStep.test_run_id == test_run_id).order_by(RunStep.sequence)
    )
    return [_step_to_response(rs) for rs in result.scalars().all()]
```

更新 `main.py`：

```python
from app.routers import test_runs
app.include_router(test_runs.router)
```

- [ ] **Step 4: 运行全部测试，提交**

Run: `pytest tests/ -v`

```bash
git add -A
git commit -m "feat: add RunnerService and test run API with trace persistence"
```

---

**Phase 2 完成检查点：**
- [ ] 四种适配器均有单元测试覆盖
- [ ] `POST /api/test-runs/?test_case_id=1&agent_config_id=1` 可执行测试
- [ ] `GET /api/test-runs/{id}/steps` 返回 trace 步骤

---

## Phase 3: 评分引擎

**交付物：** 规则评分和 LLM-as-Judge 可用，运行完成后自动评分，评分结果 API 可查。

---

### Task 3.1: 规则评分引擎（RuleEvaluator）

**Files:**
- Create: `D:\ai work\AgentBench\backend\app\evaluators\__init__.py`
- Create: `D:\ai work\AgentBench\backend\app\evaluators\base.py`
- Create: `D:\ai work\AgentBench\backend\app\evaluators\rule_evaluator.py`
- Test: `D:\ai work\AgentBench\backend\tests\unit\evaluators\__init__.py`
- Test: `D:\ai work\AgentBench\backend\tests\unit\evaluators\test_rule_evaluator.py`

- [ ] **Step 1: 写 RuleEvaluator 失败测试**

```python
# D:\ai work\AgentBench\backend\tests\unit\evaluators\test_rule_evaluator.py
import pytest
from app.evaluators.rule_evaluator import RuleEvaluator, RuleSpec


class TestRuleEvaluator:
    def test_keyword_contains_pass(self):
        evaluator = RuleEvaluator([RuleSpec(type="keyword_contains", value="CLANNAD")])
        result = evaluator.evaluate(
            agent_output="CLANNAD 是一部经典动画。",
            expected="返回 CLANNAD",
            scoring_criteria="必须提到 CLANNAD",
        )
        assert result.passed is True
        assert result.overall_score >= 4.0

    def test_keyword_contains_fail(self):
        evaluator = RuleEvaluator([RuleSpec(type="keyword_contains", value="CLANNAD")])
        result = evaluator.evaluate(
            agent_output="这是一部治愈系动画。",
            expected="返回 CLANNAD",
            scoring_criteria="必须提到 CLANNAD",
        )
        assert result.passed is False

    def test_keyword_not_contains_pass(self):
        evaluator = RuleEvaluator([RuleSpec(type="keyword_not_contains", value="不知道")])
        result = evaluator.evaluate(
            agent_output="CLANNAD 是一部 2007 年的动画。",
            expected="不应说不知道",
            scoring_criteria="",
        )
        assert result.passed is True

    def test_regex_match(self):
        evaluator = RuleEvaluator([RuleSpec(type="regex_match", value=r"\d{4}年")])
        result = evaluator.evaluate(
            agent_output="CLANNAD 是 2007 年的动画。",
            expected="包含年份",
            scoring_criteria="",
        )
        assert result.passed is True

    def test_multiple_rules_all_pass(self):
        evaluator = RuleEvaluator([
            RuleSpec(type="keyword_contains", value="CLANNAD"),
            RuleSpec(type="keyword_not_contains", value="不知道"),
        ])
        result = evaluator.evaluate(
            agent_output="CLANNAD 是经典动画。",
            expected="包含 CLANNAD",
            scoring_criteria="",
        )
        assert result.passed is True
        assert result.details["passed_count"] == 2
        assert result.details["total_count"] == 2

    def test_multiple_rules_partial_pass(self):
        evaluator = RuleEvaluator([
            RuleSpec(type="keyword_contains", value="CLANNAD"),
            RuleSpec(type="keyword_contains", value="2007"),
        ])
        result = evaluator.evaluate(
            agent_output="CLANNAD 是经典动画。",
            expected="",
            scoring_criteria="",
        )
        assert result.passed is False
        assert result.details["passed_count"] == 1

    def test_empty_rules_returns_neutral(self):
        evaluator = RuleEvaluator([])
        result = evaluator.evaluate(agent_output="anything", expected="", scoring_criteria="")
        assert result.passed is True
        assert result.overall_score == 3.0
```

- [ ] **Step 2: 实现 Evaluator 基类 + RuleEvaluator**

```python
# D:\ai work\AgentBench\backend\app\evaluators\__init__.py
# 留空
```

```python
# D:\ai work\AgentBench\backend\app\evaluators\base.py
from dataclasses import dataclass, field


@dataclass
class EvaluationResult:
    judge_type: str
    overall_score: float
    passed: bool
    reasoning: str = ""
    details: dict = field(default_factory=dict)


class BaseEvaluator:
    """评测基类。子类实现 evaluate 方法。"""

    def evaluate(
        self,
        *,
        agent_output: str,
        expected: str,
        scoring_criteria: str,
        run_steps: list[dict] | None = None,
    ) -> EvaluationResult:
        raise NotImplementedError
```

```python
# D:\ai work\AgentBench\backend\app\evaluators\rule_evaluator.py
import re
from dataclasses import dataclass

from app.evaluators.base import BaseEvaluator, EvaluationResult


@dataclass
class RuleSpec:
    type: str  # keyword_contains / keyword_not_contains / regex_match
    value: str


class RuleEvaluator(BaseEvaluator):
    def __init__(self, rules: list[RuleSpec]):
        self.rules = rules

    def evaluate(
        self,
        *,
        agent_output: str,
        expected: str = "",
        scoring_criteria: str = "",
        run_steps: list[dict] | None = None,
    ) -> EvaluationResult:
        if not self.rules:
            return EvaluationResult(
                judge_type="rule",
                overall_score=3.0,
                passed=True,
                reasoning="No rules defined, returning neutral score.",
                details={"total_count": 0, "passed_count": 0, "results": []},
            )

        passed_count = 0
        rule_results = []

        for rule in self.rules:
            matched = self._check_rule(rule, agent_output)
            rule_results.append({"rule_type": rule.type, "rule_value": rule.value, "matched": matched})
            if matched:
                passed_count += 1

        all_passed = passed_count == len(self.rules)
        score = 5.0 if all_passed else max(1.0, round(5.0 * passed_count / len(self.rules), 1))

        return EvaluationResult(
            judge_type="rule",
            overall_score=score,
            passed=all_passed,
            reasoning=f"{passed_count}/{len(self.rules)} rules passed.",
            details={"total_count": len(self.rules), "passed_count": passed_count, "results": rule_results},
        )

    def _check_rule(self, rule: RuleSpec, text: str) -> bool:
        if rule.type == "keyword_contains":
            return rule.value in text
        elif rule.type == "keyword_not_contains":
            return rule.value not in text
        elif rule.type == "regex_match":
            return bool(re.search(rule.value, text))
        return False
```

- [ ] **Step 3: 运行测试确认通过，提交**

Run: `pytest tests/unit/evaluators/test_rule_evaluator.py -v`

```bash
git add -A
git commit -m "feat: add RuleEvaluator with keyword and regex rules"
```

---

### Task 3.2: LLM-as-Judge 评分引擎

**Files:**
- Create: `D:\ai work\AgentBench\backend\app\evaluators\llm_judge_evaluator.py`
- Test: `D:\ai work\AgentBench\backend\tests\unit\evaluators\test_llm_judge_evaluator.py`

- [ ] **Step 1: 写 LLM Judge 失败测试（mock LLM 调用）**

```python
# D:\ai work\AgentBench\backend\tests\unit\evaluators\test_llm_judge_evaluator.py
import pytest
import json
from unittest.mock import AsyncMock, patch

from app.evaluators.llm_judge_evaluator import LLMJudgeEvaluator


FAKE_JUDGE_RESPONSE = json.dumps({
    "accuracy": 5,
    "hallucination": 4,
    "tool_correctness": 3,
    "expression_quality": 4,
    "reasoning": "回答准确，无明显幻觉，工具调用一般，表达通顺。",
})


class TestLLMJudgeEvaluator:
    @pytest.mark.asyncio
    async def test_evaluate_calls_llm_and_parses(self):
        evaluator = LLMJudgeEvaluator(
            base_url="http://fake",
            api_key="test",
            model="gpt-4.1",
        )

        with patch("app.evaluators.llm_judge_evaluator.httpx.AsyncClient") as mock_cls:
            mock_post = AsyncMock()
            mock_post.return_value = type("R", (), {
                "json": lambda: {
                    "choices": [{"message": {"content": FAKE_JUDGE_RESPONSE}}],
                    "usage": {"prompt_tokens": 200, "completion_tokens": 50},
                },
                "raise_for_status": lambda: None,
            })()
            mock_instance = AsyncMock()
            mock_instance.post = mock_post
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=False)
            mock_cls.return_value = mock_instance

            result = evaluator.evaluate(
                agent_output="CLANNAD 是 2007 年 Kyoto Animation 制作的动画。",
                expected="返回 CLANNAD 信息",
                scoring_criteria="必须包含年份和制作公司",
            )

        assert result.judge_type == "llm"
        assert result.overall_score == 4.0  # (5+4+3+4)/4
        assert result.details["accuracy"] == 5
        assert "准确" in result.reasoning

    @pytest.mark.asyncio
    async def test_evaluate_handles_llm_error(self):
        evaluator = LLMJudgeEvaluator(
            base_url="http://fake", api_key="test", model="gpt-4.1",
        )

        with patch("app.evaluators.llm_judge_evaluator.httpx.AsyncClient") as mock_cls:
            mock_instance = AsyncMock()
            mock_instance.post = AsyncMock(side_effect=Exception("API error"))
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=False)
            mock_cls.return_value = mock_instance

            result = evaluator.evaluate(
                agent_output="test", expected="", scoring_criteria="",
            )

        assert result.overall_score == 0.0
        assert "API error" in result.reasoning
```

- [ ] **Step 2: 实现 LLM Judge Evaluator**

```python
# D:\ai work\AgentBench\backend\app\evaluators\llm_judge_evaluator.py
import json
import re

import httpx

from app.evaluators.base import BaseEvaluator, EvaluationResult

JUDGE_SYSTEM_PROMPT = """你是一个专业的 AI Agent 评测裁判。你的任务是评估 Agent 对用户问题的回答质量。

请严格按照以下四个维度打分（每项 1-5 分）：
1. accuracy（准确性）：回答是否准确回答了用户问题
2. hallucination（无幻觉）：回答中是否有编造的事实（5分=无幻觉，1分=严重幻觉）
3. tool_correctness（工具调用正确性）：如果涉及工具调用，参数和调用是否正确（无工具调用给 3 分）
4. expression_quality（表达质量）：中文表达是否通顺、专业、清晰

你必须以 JSON 格式返回评分结果，不要包含任何其他文字：
{"accuracy": N, "hallucination": N, "tool_correctness": N, "expression_quality": N, "reasoning": "简短的评分理由"}
"""


class LLMJudgeEvaluator(BaseEvaluator):
    def __init__(self, *, base_url: str, api_key: str, model: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model

    def evaluate(
        self,
        *,
        agent_output: str,
        expected: str = "",
        scoring_criteria: str = "",
        run_steps: list[dict] | None = None,
    ) -> EvaluationResult:
        # 同步包装（实际 async 调用在 evaluate_async 中）
        raise NotImplementedError("Use evaluate_async instead")

    async def evaluate_async(
        self,
        *,
        agent_output: str,
        expected: str = "",
        scoring_criteria: str = "",
        run_steps: list[dict] | None = None,
    ) -> EvaluationResult:
        user_prompt = self._build_prompt(agent_output, expected, scoring_criteria, run_steps)

        try:
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self.api_key}",
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
                            {"role": "user", "content": user_prompt},
                        ],
                        "temperature": 0.1,
                    },
                )
                resp.raise_for_status()
                data = resp.json()

            content = data["choices"][0]["message"]["content"]
            scores = self._parse_response(content)

            overall = round(
                (scores["accuracy"] + scores["hallucination"] + scores["tool_correctness"] + scores["expression_quality"]) / 4, 1
            )

            return EvaluationResult(
                judge_type="llm",
                overall_score=overall,
                passed=overall >= 3.0,
                reasoning=scores.get("reasoning", ""),
                details=scores,
            )

        except Exception as e:
            return EvaluationResult(
                judge_type="llm",
                overall_score=0.0,
                passed=False,
                reasoning=f"LLM Judge error: {e}",
            )

    def _build_prompt(
        self,
        agent_output: str,
        expected: str,
        scoring_criteria: str,
        run_steps: list[dict] | None,
    ) -> str:
        parts = [
            "## 用户输入的问题",
            "（见下方期望行为描述）",
            "",
            "## Agent 的回答",
            agent_output,
        ]
        if expected:
            parts += ["", "## 期望行为", expected]
        if scoring_criteria:
            parts += ["", "## 评分标准", scoring_criteria]
        if run_steps:
            steps_summary = "\n".join(
                f"- {s.get('step_type', '?')} ({s.get('name', '')}): {s.get('status', '?')} - {s.get('latency_ms', 0)}ms"
                for s in run_steps
            )
            parts += ["", "## 调用链步骤", steps_summary]

        return "\n".join(parts)

    def _parse_response(self, content: str) -> dict:
        """从 LLM 响应中提取 JSON 评分。"""
        # 尝试直接解析
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass

        # 尝试从 markdown code block 中提取
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", content, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass

        # 尝试找到第一个 { ... } 块
        match = re.search(r"\{[^}]+\}", content, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass

        return {"accuracy": 0, "hallucination": 0, "tool_correctness": 0, "expression_quality": 0, "reasoning": f"Failed to parse LLM response: {content[:200]}"}
```

- [ ] **Step 3: 运行测试确认通过，提交**

Run: `pytest tests/unit/evaluators/test_llm_judge_evaluator.py -v`

```bash
git add -A
git commit -m "feat: add LLM-as-Judge evaluator with multi-dimension scoring"
```

---

### Task 3.3: EvaluationService — 自动评分集成

**Files:**
- Create: `D:\ai work\AgentBench\backend\app\services\evaluation_service.py`
- Create: `D:\ai work\AgentBench\backend\app\routers\evaluations.py`
- Modify: `D:\ai work\AgentBench\backend\app\main.py`
- Test: `D:\ai work\AgentBench\backend\tests\unit\services\test_evaluation_service.py`

- [ ] **Step 1: 写 EvaluationService 测试**

```python
# D:\ai work\AgentBench\backend\tests\unit\services\test_evaluation_service.py
import pytest
from unittest.mock import patch, MagicMock
from app.services.evaluation_service import EvaluationService
from app.evaluators.rule_evaluator import RuleSpec


class TestEvaluationService:
    @pytest.mark.asyncio
    async def test_evaluate_with_rules(self, db_session):
        from app.models.test_case import TestCase
        from app.models.agent_config import AgentConfig
        from app.models.test_run import TestRun

        tc = TestCase(title="t", input_text="hi", expected_behavior="hello", scoring_criteria="", tags="[]")
        ac = AgentConfig(name="ac", agent_type="http", config="{}")
        tr = TestRun(test_case_id=1, agent_config_id=1, status="success", agent_output="hello world")
        db_session.add_all([tc, ac, tr])
        await db_session.commit()

        service = EvaluationService(db_session)
        result = await service.evaluate_test_run(
            test_run_id=tr.id,
            rules=[RuleSpec(type="keyword_contains", value="hello")],
            use_llm_judge=False,
        )
        assert result is not None
        assert result.judge_type == "rule"
        assert result.passed is True

    @pytest.mark.asyncio
    async def test_evaluate_without_rules_no_llm(self, db_session):
        from app.models.test_run import TestRun
        tr = TestRun(test_case_id=1, agent_config_id=1, status="success", agent_output="test")
        db_session.add(tr)
        await db_session.commit()

        service = EvaluationService(db_session)
        result = await service.evaluate_test_run(
            test_run_id=tr.id, rules=[], use_llm_judge=False,
        )
        assert result is not None
```

- [ ] **Step 2: 实现 EvaluationService**

```python
# D:\ai work\AgentBench\backend\app\services\evaluation_service.py
import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.test_case import TestCase
from app.models.test_run import TestRun
from app.models.run_step import RunStep
from app.models.evaluation_result import EvaluationResult
from app.evaluators.rule_evaluator import RuleEvaluator, RuleSpec
from app.evaluators.llm_judge_evaluator import LLMJudgeEvaluator
from app.config import settings


class EvaluationService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def evaluate_test_run(
        self,
        test_run_id: int,
        *,
        rules: list[RuleSpec] | None = None,
        use_llm_judge: bool = False,
    ) -> EvaluationResult:
        # 获取 TestRun 和 TestCase
        tr = (await self.session.execute(select(TestRun).where(TestRun.id == test_run_id))).scalar_one_or_none()
        if tr is None:
            raise ValueError(f"TestRun {test_run_id} not found")

        tc = (await self.session.execute(select(TestCase).where(TestCase.id == tr.test_case_id))).scalar_one_or_none()
        if tc is None:
            raise ValueError(f"TestCase {tr.test_case_id} not found")

        # 获取 RunSteps
        steps_result = await self.session.execute(
            select(RunStep).where(RunStep.test_run_id == test_run_id).order_by(RunStep.sequence)
        )
        run_steps = [{"step_type": s.step_type, "name": s.name, "status": s.status, "latency_ms": s.latency_ms} for s in steps_result.scalars().all()]

        best_result = None

        # 规则评分
        if rules:
            rule_eval = RuleEvaluator(rules)
            rule_result = rule_eval.evaluate(
                agent_output=tr.agent_output,
                expected=tc.expected_behavior,
                scoring_criteria=tc.scoring_criteria,
                run_steps=run_steps,
            )
            best_result = rule_result

        # LLM-as-Judge 评分
        if use_llm_judge:
            judge = LLMJudgeEvaluator(
                base_url=settings.llm_base_url,
                api_key=settings.llm_api_key,
                model=settings.llm_judge_model,
            )
            llm_result = await judge.evaluate_async(
                agent_output=tr.agent_output,
                expected=tc.expected_behavior,
                scoring_criteria=tc.scoring_criteria,
                run_steps=run_steps,
            )
            if best_result is None or llm_result.overall_score > best_result.overall_score:
                best_result = llm_result

        # 如果都没有，返回中性结果
        if best_result is None:
            from app.evaluators.base import EvaluationResult as BaseResult
            best_result = BaseResult(
                judge_type="none", overall_score=0.0, passed=False,
                reasoning="No evaluation method specified.",
            )

        # 写入数据库
        db_eval = EvaluationResult(
            test_run_id=test_run_id,
            judge_type=best_result.judge_type,
            overall_score=best_result.overall_score,
            accuracy_score=best_result.details.get("accuracy"),
            hallucination_score=best_result.details.get("hallucination"),
            tool_correctness_score=best_result.details.get("tool_correctness"),
            expression_quality_score=best_result.details.get("expression_quality"),
            judge_reasoning=best_result.reasoning,
            rule_results=json.dumps(best_result.details.get("results", []), ensure_ascii=False) if best_result.details.get("results") else None,
        )
        self.session.add(db_eval)
        await self.session.commit()
        await self.session.refresh(db_eval)
        return db_eval
```

- [ ] **Step 3: 实现评分查询 API**

```python
# D:\ai work\AgentBench\backend\app\routers\evaluations.py
import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.evaluation_result import EvaluationResult
from app.schemas.evaluation import EvaluationResultResponse
from app.services.evaluation_service import EvaluationService
from app.evaluators.rule_evaluator import RuleSpec

router = APIRouter(prefix="/api/evaluations", tags=["evaluations"])


def _to_response(ev: EvaluationResult) -> EvaluationResultResponse:
    return EvaluationResultResponse(
        id=ev.id,
        test_run_id=ev.test_run_id,
        judge_type=ev.judge_type,
        overall_score=ev.overall_score,
        accuracy_score=ev.accuracy_score,
        hallucination_score=ev.hallucination_score,
        tool_correctness_score=ev.tool_correctness_score,
        expression_quality_score=ev.expression_quality_score,
        judge_reasoning=ev.judge_reasoning,
        rule_results=json.loads(ev.rule_results) if ev.rule_results else None,
        created_at=ev.created_at,
    )


@router.post("/")
async def evaluate_run(
    test_run_id: int,
    rules: list[dict] | None = None,
    use_llm_judge: bool = False,
    session: AsyncSession = Depends(get_session),
):
    rule_specs = [RuleSpec(**r) for r in rules] if rules else []
    service = EvaluationService(session)
    try:
        result = await service.evaluate_test_run(
            test_run_id, rules=rule_specs, use_llm_judge=use_llm_judge,
        )
        return _to_response(result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{evaluation_id}", response_model=EvaluationResultResponse)
async def get_evaluation(
    evaluation_id: int,
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(EvaluationResult).where(EvaluationResult.id == evaluation_id)
    )
    ev = result.scalar_one_or_none()
    if ev is None:
        raise HTTPException(status_code=404, detail="EvaluationResult not found")
    return _to_response(ev)


@router.get("/run/{test_run_id}", response_model=list[EvaluationResultResponse])
async def get_evaluations_by_run(
    test_run_id: int,
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(EvaluationResult).where(EvaluationResult.test_run_id == test_run_id)
    )
    return [_to_response(ev) for ev in result.scalars().all()]
```

更新 `main.py`：

```python
from app.routers import evaluations
app.include_router(evaluations.router)
```

- [ ] **Step 4: 运行全部测试，提交**

Run: `pytest tests/ -v`

```bash
git add -A
git commit -m "feat: add EvaluationService and evaluation API with rule + LLM scoring"
```

---

**Phase 3 完成检查点：**
- [ ] `POST /api/evaluations/?test_run_id=1&rules=[{"type":"keyword_contains","value":"hello"}]` 可评分
- [ ] `POST /api/evaluations/?test_run_id=1&use_llm_judge=true` 可调用 LLM 评分
- [ ] 评分结果持久化到数据库

---

## Phase 4: 前端 UI

**交付物：** Vue 3 前端可操作测试用例和 Agent 配置，可触发运行并查看 Trace 时间线和评分结果。

---

### Task 4.1: 前端项目脚手架

**Files:**
- Create: `D:\ai work\AgentBench\frontend\` (Vite + Vue 3 + TypeScript 项目)

- [ ] **Step 1: 创建 Vite 项目**

```powershell
cd "D:\ai work\AgentBench"
npm create vite@latest frontend -- --template vue-ts
cd frontend
npm install
npm install naive-ui @vicons/ionicons5 pinia vue-router@4 axios
npm install -D vitest @vue/test-utils happy-dom
```

- [ ] **Step 2: 配置 Naive UI 和路由**

配置 `src/main.ts` 注册 Naive UI 和 Pinia，创建基础路由配置（`/` → Dashboard, `/test-cases`, `/agent-configs`）。

- [ ] **Step 3: 配置 API 基础路径**

创建 `src/api/index.ts`，配置 axios base URL 为 `http://localhost:8000`。

- [ ] **Step 4: 验证开发服务器启动**

Run: `npm run dev`
Expected: 开发服务器启动在 5173 端口

- [ ] **Step 5: 提交**

```bash
git add -A
git commit -m "chore: scaffold frontend with Vite, Vue 3, Naive UI, Pinia"
```

---

### Task 4.2: 测试用例列表页 + Agent 配置列表页

**Files:**
- Create: `D:\ai work\AgentBench\frontend\src\views\TestCases.vue`
- Create: `D:\ai work\AgentBench\frontend\src\views\TestCaseEdit.vue`
- Create: `D:\ai work\AgentBench\frontend\src\views\AgentConfigs.vue`
- Create: `D:\ai work\AgentBench\frontend\src\views\AgentConfigEdit.vue`
- Create: `D:\ai work\AgentBench\frontend\src\api\testCases.ts`
- Create: `D:\ai work\AgentBench\frontend\src\api\agentConfigs.ts`
- Create: `D:\ai work\AgentBench\frontend\src\stores\testCases.ts`
- Create: `D:\ai work\AgentBench\frontend\src\stores\agentConfigs.ts`

- [ ] **Step 1: 实现 API 层**

```typescript
// D:\ai work\AgentBench\frontend\src\api\index.ts
import axios from "axios";

const api = axios.create({ baseURL: "http://localhost:8000" });
export default api;
```

```typescript
// D:\ai work\AgentBench\frontend\src\api\testCases.ts
import api from "./index";

export interface TestCase {
  id: number;
  title: string;
  input_text: string;
  expected_behavior: string;
  scoring_criteria: string;
  tags: string[];
  difficulty: "easy" | "medium" | "hard";
  category: string;
  created_at: string;
  updated_at: string;
}

export const listTestCases = (params?: { difficulty?: string; tag?: string }) =>
  api.get("/api/test-cases/", { params }).then((r) => r.data);

export const getTestCase = (id: number) =>
  api.get<TestCase>(`/api/test-cases/${id}`).then((r) => r.data);

export const createTestCase = (data: Partial<TestCase>) =>
  api.post<TestCase>("/api/test-cases/", data).then((r) => r.data);

export const updateTestCase = (id: number, data: Partial<TestCase>) =>
  api.put<TestCase>(`/api/test-cases/${id}`, data).then((r) => r.data);

export const deleteTestCase = (id: number) =>
  api.delete(`/api/test-cases/${id}`);
```

```typescript
// D:\ai work\AgentBench\frontend\src\api\agentConfigs.ts
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
```

- [ ] **Step 2: 实现 Pinia stores**

```typescript
// D:\ai work\AgentBench\frontend\src\stores\testCases.ts
import { defineStore } from "pinia";
import { ref } from "vue";
import { listTestCases, createTestCase, updateTestCase, deleteTestCase, type TestCase } from "../api/testCases";

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
```

```typescript
// D:\ai work\AgentBench\frontend\src\stores\agentConfigs.ts
import { defineStore } from "pinia";
import { ref } from "vue";
import { listAgentConfigs, createAgentConfig, deleteAgentConfig, type AgentConfig } from "../api/agentConfigs";

export const useAgentConfigStore = defineStore("agentConfigs", () => {
  const items = ref<AgentConfig[]>([]);
  const total = ref(0);
  const loading = ref(false);

  async function fetchList() {
    loading.value = true;
    try {
      const data = await listAgentConfigs();
      items.value = data.items;
      total.value = data.total;
    } finally {
      loading.value = false;
    }
  }

  async function create(data: Partial<AgentConfig>) {
    const item = await createAgentConfig(data);
    items.value.unshift(item);
    total.value += 1;
    return item;
  }

  async function remove(id: number) {
    await deleteAgentConfig(id);
    items.value = items.value.filter((i) => i.id !== id);
    total.value -= 1;
  }

  return { items, total, loading, fetchList, create, remove };
});
```

- [ ] **Step 3: 实现 TestCases.vue 列表页**

使用 Naive UI 的 `NDataTable`、`NButton`、`NTag`、`NModal`、`NForm`、`NInput`、`NSelect` 等组件构建列表页。包含：
- 表格列：标题、输入文本（截断）、难度（Tag 颜色区分）、标签（Tag）、操作（编辑/删除）
- 顶部筛选栏：难度下拉、标签筛选
- 新建按钮 → 打开 Modal 表单

（页面代码约 150-200 行，此处省略完整 Vue SFC，实施时根据 Naive UI 文档编写。）

- [ ] **Step 4: 实现 AgentConfigs.vue 列表页**

结构类似 TestCases，列包括：名称、类型（Tag）、描述、操作。

- [ ] **Step 5: 配置路由**

```typescript
// D:\ai work\AgentBench\frontend\src\router\index.ts
import { createRouter, createWebHistory } from "vue-router";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", redirect: "/test-cases" },
    { path: "/test-cases", component: () => import("../views/TestCases.vue") },
    { path: "/test-cases/new", component: () => import("../views/TestCaseEdit.vue") },
    { path: "/agent-configs", component: () => import("../views/AgentConfigs.vue") },
    { path: "/agent-configs/new", component: () => import("../views/AgentConfigEdit.vue") },
  ],
});

export default router;
```

- [ ] **Step 6: 提交**

```bash
git add -A
git commit -m "feat: add test cases and agent configs list pages with CRUD"
```

---

### Task 4.3: 运行详情页 — Trace 时间线 + 评分结果

**Files:**
- Create: `D:\ai work\AgentBench\frontend\src\api\testRuns.ts`
- Create: `D:\ai work\AgentBench\frontend\src\api\evaluations.ts`
- Create: `D:\ai work\AgentBench\frontend\src\views\RunDetail.vue`
- Create: `D:\ai work\AgentBench\frontend\src\components\TraceTimeline.vue`
- Create: `D:\ai work\AgentBench\frontend\src\components\ScoreCard.vue`
- Create: `D:\ai work\AgentBench\frontend\src\stores\testRuns.ts`

- [ ] **Step 1: 实现 API 层**

```typescript
// D:\ai work\AgentBench\frontend\src\api\testRuns.ts
import api from "./index";

export interface RunStep {
  id: number;
  sequence: number;
  step_type: string;
  name: string;
  input_json: Record<string, unknown>;
  output_json: Record<string, unknown>;
  latency_ms: number;
  token_usage_input: number;
  token_usage_output: number;
  status: "success" | "error";
  error_message: string | null;
}

export interface TestRun {
  id: number;
  test_case_id: number;
  agent_config_id: number;
  status: "pending" | "running" | "success" | "error";
  agent_output: string;
  duration_ms: number;
  total_tokens: number;
  error_message: string | null;
  created_at: string;
}

export const runTest = (test_case_id: number, agent_config_id: number) =>
  api.post<TestRun>("/api/test-runs/", null, { params: { test_case_id, agent_config_id } }).then((r) => r.data);

export const getTestRun = (id: number) =>
  api.get<TestRun>(`/api/test-runs/${id}`).then((r) => r.data);

export const getRunSteps = (testRunId: number) =>
  api.get<RunStep[]>(`/api/test-runs/${testRunId}/steps`).then((r) => r.data);
```

```typescript
// D:\ai work\AgentBench\frontend\src\api\evaluations.ts
import api from "./index";

export interface EvaluationResult {
  id: number;
  test_run_id: number;
  judge_type: string;
  overall_score: number;
  accuracy_score: number | null;
  hallucination_score: number | null;
  tool_correctness_score: number | null;
  expression_quality_score: number | null;
  judge_reasoning: string;
  rule_results: Record<string, unknown>[] | null;
  created_at: string;
}

export const evaluateRun = (test_run_id: number, rules?: unknown[], use_llm_judge?: boolean) =>
  api.post<EvaluationResult>("/api/evaluations/", null, { params: { test_run_id, rules, use_llm_judge } }).then((r) => r.data);

export const getEvaluations = (testRunId: number) =>
  api.get<EvaluationResult[]>(`/api/evaluations/run/${testRunId}`).then((r) => r.data);
```

- [ ] **Step 2: 实现 TraceTimeline.vue 组件**

核心功能：
- 垂直时间线布局，每步一个节点
- 节点颜色：success=绿色，error=红色
- 每步显示：序列号、名称、类型 Tag、耗时、token 数
- 点击展开：显示 input_json 和 output_json（代码格式化）
- 耗时 > 3000ms 的步骤标注黄色警告

使用 Naive UI 的 `NTimeline`、`NTimelineItem`、`NTag`、`NCollapse` 组件。

- [ ] **Step 3: 实现 ScoreCard.vue 组件**

核心功能：
- 四个维度的雷达图/柱状图展示（简化版用 NProgress 条形）
- 每个维度：名称 + 分数（1-5）+ 进度条颜色（红/黄/绿）
- 底部：总分 + 评分理由

- [ ] **Step 4: 实现 RunDetail.vue 页面**

布局（上到下）：
1. 基础信息栏：TestRun 状态 Tag、耗时、token 数、创建时间
2. Agent 输出区域（代码块展示）
3. Trace 时间线（TraceTimeline 组件）
4. 评分结果（ScoreCard 组件）+ 触发评分按钮
5. 错误信息（如有）

- [ ] **Step 5: 注册路由并添加导航入口**

在 TestCases 列表每行添加"运行"按钮，点击后跳转到 `RunDetail?test_case_id=X&agent_config_id=Y`，触发运行。

- [ ] **Step 6: 提交**

```bash
git add -A
git commit -m "feat: add RunDetail page with TraceTimeline and ScoreCard"
```

---

### Task 4.4: 基础 Vitest 组件测试

**Files:**
- Create: `D:\ai work\AgentBench\frontend\src\components\__tests__\TraceTimeline.test.ts`
- Create: `D:\ai work\AgentBench\frontend\src\components\__tests__\ScoreCard.test.ts`

- [ ] **Step 1: 写 TraceTimeline 渲染测试**

```typescript
// D:\ai work\AgentBench\frontend\src\components\__tests__\TraceTimeline.test.ts
import { describe, it, expect } from "vitest";
import { mount } from "@vue/test-utils";
import TraceTimeline from "../TraceTimeline.vue";

describe("TraceTimeline", () => {
  it("renders steps in order", () => {
    const steps = [
      { sequence: 1, step_type: "intent_detection", name: "IntentDetector", latency_ms: 100, status: "success", error_message: null },
      { sequence: 2, step_type: "llm_generation", name: "LLMCall", latency_ms: 2000, status: "success", error_message: null },
    ];
    const wrapper = mount(TraceTimeline, { props: { steps } });
    // 验证组件渲染无报错且步骤数量正确
    expect(wrapper.findAll("timeline-item, .timeline-item").length).toBeGreaterThanOrEqual(2);
  });

  it("shows error status for failed steps", () => {
    const steps = [
      { sequence: 1, step_type: "llm_generation", name: "LLM", latency_ms: 5000, status: "error", error_message: "timeout" },
    ];
    const wrapper = mount(TraceTimeline, { props: { steps } });
    expect(wrapper.text()).toContain("error");
  });
});
```

- [ ] **Step 2: 写 ScoreCard 渲染测试**

```typescript
// D:\ai work\AgentBench\frontend\src\components\__tests__\ScoreCard.test.ts
import { describe, it, expect } from "vitest";
import { mount } from "@vue/test-utils";
import ScoreCard from "../ScoreCard.vue";

describe("ScoreCard", () => {
  it("displays overall score", () => {
    const evaluation = {
      overall_score: 4.2,
      accuracy_score: 5,
      hallucination_score: 4,
      tool_correctness_score: 3,
      expression_quality_score: 4,
      judge_reasoning: "Good overall",
    };
    const wrapper = mount(ScoreCard, { props: { evaluation } });
    expect(wrapper.text()).toContain("4.2");
  });
});
```

- [ ] **Step 3: 运行前端测试**

Run: `npx vitest run`

- [ ] **Step 4: 提交**

```bash
git add -A
git commit -m "test: add Vitest component tests for TraceTimeline and ScoreCard"
```

---

**Phase 4 完成检查点：**
- [ ] 前端开发服务器可启动
- [ ] 测试用例列表页可 CRUD
- [ ] Agent 配置列表页可 CRUD
- [ ] 运行详情页展示 Trace 时间线 + 评分
- [ ] Vitest 组件测试通过

---

## 最终检查

- [ ] 所有后端测试通过：`pytest tests/ -v --cov`
- [ ] 所有前端测试通过：`npx vitest run`
- [ ] 后端服务可启动：`uvicorn app.main:app`
- [ ] 前端服务可启动：`npm run dev`
- [ ] 端到端流程：创建用例 → 创建配置 → 运行测试 → 查看结果
- [ ] Git 提交历史清晰，每个 Task 一个 commit
