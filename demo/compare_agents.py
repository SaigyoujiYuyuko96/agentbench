"""A/B 对比演示：同一个测试集，跑两个质量不同的 Agent，看平台能否区分。

为什么要有这个脚本：
    只有一个 Agent 时，5 条用例全拿 5.0 分——这证明不了评测平台有用，
    只证明了关键词规则能匹配上。评测平台的价值在于「区分」，所以这里放一个
    故意退化的对照组：同样的输入，它把答案截断到 40 字，丢掉大部分事实。

    如果两个 Agent 分数拉不开差距，说明规则设计得不对；拉得开，说明平台在干活。

用法：
    1. 先起后端：  cd backend && uvicorn app.main:app --port 8090
    2. 再起 mock：  python demo/mock_animepilot.py          # 监听 8003
    3. 跑本脚本：  PYTHONIOENCODING=utf-8 python demo/compare_agents.py
"""

import asyncio
import httpx

BASE_URL = "http://127.0.0.1:8090"
MOCK_URL = "http://127.0.0.1:8003"

TEST_CASES = [
    {
        "title": "搜索葬送的芙莉莲",
        "input_text": "搜索葬送的芙莉莲",
        "expected_behavior": "返回葬送的芙莉莲的详细信息，包括原作、动画制作、播出时间、集数、评分等基本信息",
        "scoring_criteria": "答案应包含葬送的芙莉莲的基本信息（原作、动画制作公司、播出时间、集数、评分）",
        "tags": ["搜索", "作品信息"],
        "difficulty": "easy",
        "category": "搜索",
        "rules": [
            {"type": "keyword_contains", "value": "葬送的芙莉莲"},
            {"type": "keyword_contains", "value": "山田钟人"},
            {"type": "keyword_contains", "value": "MADHOUSE"},
            {"type": "keyword_contains", "value": "2023"},
        ],
    },
    {
        "title": "搜索夏目友人帐",
        "input_text": "夏目友人帐是什么",
        "expected_behavior": "返回夏目友人帐的详细介绍，包括原作、动画制作、播出时间、季数、主题等",
        "scoring_criteria": "答案应包含夏目友人帐的基本信息和主题描述",
        "tags": ["搜索", "作品信息"],
        "difficulty": "easy",
        "category": "搜索",
        "rules": [
            {"type": "keyword_contains", "value": "夏目友人帐"},
            {"type": "keyword_contains", "value": "绿川幸"},
            {"type": "keyword_contains", "value": "治愈"},
            {"type": "keyword_contains", "value": "妖怪"},
        ],
    },
    {
        "title": "京阿尼代表作查询",
        "input_text": "京阿尼有哪些代表作",
        "expected_behavior": "列出京都动画的多部代表作品，如凉宫春日、轻音、冰菓、紫罗兰永恒花园等",
        "scoring_criteria": "答案应至少列出3部京阿尼的代表作品",
        "tags": ["搜索", "公司作品"],
        "difficulty": "medium",
        "category": "搜索",
        "rules": [
            {"type": "keyword_contains", "value": "京都动画"},
            {"type": "keyword_contains", "value": "轻音少女"},
            {"type": "keyword_contains", "value": "冰菓"},
            {"type": "keyword_contains", "value": "紫罗兰永恒花园"},
            {"type": "keyword_contains", "value": "凉宫春日"},
        ],
    },
    {
        "title": "虫师评价分析",
        "input_text": "虫师为什么评价高",
        "expected_behavior": "从美学风格、叙事方式、主题深度、音乐等多个角度分析虫师获得高评价的原因",
        "scoring_criteria": "答案应从多个维度分析虫师的优点，至少包含3个不同的分析角度",
        "tags": ["问答", "作品分析"],
        "difficulty": "hard",
        "category": "问答",
        "rules": [
            {"type": "keyword_contains", "value": "虫师"},
            {"type": "keyword_contains", "value": "银古"},
            {"type": "keyword_contains", "value": "治愈"},
            {"type": "keyword_contains", "value": "音乐"},
            {"type": "keyword_contains", "value": "美学"},
        ],
    },
    {
        "title": "类似虫师的推荐",
        "input_text": "推荐类似虫师的作品",
        "expected_behavior": "推荐多部与虫师风格类似的动漫作品，如夏目友人帐、物怪、灰羽联盟等，并给出推荐理由",
        "scoring_criteria": "应至少推荐3部作品，每部有简短的推荐理由",
        "tags": ["推荐", "相似作品"],
        "difficulty": "medium",
        "category": "推荐",
        "rules": [
            {"type": "keyword_contains", "value": "夏目友人帐"},
            {"type": "keyword_contains", "value": "推荐"},
            {"type": "keyword_contains", "value": "治愈"},
        ],
    },
]


def agent_config(name: str, description: str, path: str) -> dict:
    return {
        "name": name,
        "agent_type": "http",
        "description": description,
        "config": {
            "endpoint": f"{MOCK_URL}/api/agent/{path}",
            "method": "POST",
            "headers": {
                "Content-Type": "application/json",
                "Authorization": "Bearer mock-jwt-token",
            },
            "timeout": 30,
            "request_body_template": {"content": "{input}"},
            "output_field": "answer",
        },
    }


async def evaluate_one_agent(client: httpx.AsyncClient, config: dict) -> dict:
    """创建 Agent 配置，跑完全部用例并评分，返回汇总。"""
    resp = await client.post("/api/agent-configs/", json=config)
    resp.raise_for_status()
    agent = resp.json()

    scores: list[float] = []
    for tc in TEST_CASES:
        resp = await client.post("/api/test-cases/", json=tc)
        resp.raise_for_status()
        case = resp.json()

        resp = await client.post(
            "/api/test-runs/",
            params={"test_case_id": case["id"], "agent_config_id": agent["id"]},
        )
        resp.raise_for_status()
        run = resp.json()

        resp = await client.post(
            "/api/evaluations/",
            json={
                "test_run_id": run["id"],
                "rules": tc["rules"],
                "use_llm_judge": False,
            },
        )
        resp.raise_for_status()
        scores.append(resp.json()["overall_score"])

    return {
        "agent": agent["name"],
        "scores": scores,
        "average": round(sum(scores) / len(scores), 2) if scores else 0.0,
    }


async def main() -> None:
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=60) as client:
        # 每次跑前清空，避免同名 Agent 冲突
        existing = (await client.get("/api/agent-configs/", params={"limit": 100})).json()
        for item in existing.get("items", []):
            await client.delete(f"/api/agent-configs/{item['id']}")

        good = await evaluate_one_agent(
            client,
            agent_config(
                "AnimePilot (baseline)",
                "Mock AnimePilot，答案完整",
                "chat",
            ),
        )
        bad = await evaluate_one_agent(
            client,
            agent_config(
                "AnimePilot (degraded)",
                "同一套知识库，但答案被截断到 40 字，用于验证评测能否抓出退化",
                "chat-degraded",
            ),
        )

    print("=" * 68)
    print("AgentBench A/B 对比：同一个测试集，两个质量不同的 Agent")
    print("=" * 68)
    print(f"{'#':<3} {'测试用例':<18} {'baseline':>10} {'degraded':>10} {'差距':>8}")
    print("-" * 68)
    for i, tc in enumerate(TEST_CASES):
        a, b = good["scores"][i], bad["scores"][i]
        print(f"{i + 1:<3} {tc['title']:<18} {a:>10.1f} {b:>10.1f} {a - b:>8.1f}")
    print("-" * 68)
    print(
        f"{'':3} {'平均分':<18} {good['average']:>10.2f} {bad['average']:>10.2f} "
        f"{good['average'] - bad['average']:>8.2f}"
    )
    print("=" * 68)
    print()
    print(f"baseline 平均 {good['average']}/5.0   degraded 平均 {bad['average']}/5.0")
    print("差距越大，说明规则越能抓住「答案里的事实是否完整」，而不是只看格式。")


if __name__ == "__main__":
    asyncio.run(main())
