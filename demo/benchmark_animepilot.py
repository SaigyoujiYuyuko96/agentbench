import asyncio
import json
import httpx


BASE_URL = "http://127.0.0.1:8090"

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

AGENT_CONFIG = {
    "name": "AnimePilot-Eval",
    "agent_type": "http",
    "description": "Mock AnimePilot 动漫百科 Agent - 用于评测演示",
    "config": {
        "endpoint": "http://127.0.0.1:8003/api/agent/chat",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
            "Authorization": "Bearer mock-jwt-token",
        },
        "timeout": 30,
        "request_body_template": {
            "content": "{input}"
        },
        "output_field": "answer",
    },
}


async def main():
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30) as client:
        print("=" * 60)
        print("🚀 AgentBench 评测 AnimePilot 演示")
        print("=" * 60)

        print("\n📋 步骤 1: 创建 Agent 配置...")
        resp = await client.post("/api/agent-configs/", json=AGENT_CONFIG)
        agent_config = resp.json()
        agent_id = agent_config["id"]
        print(f"   ✅ Agent 配置已创建: ID={agent_id}, 名称={agent_config['name']}")

        print("\n📝 步骤 2: 创建测试用例...")
        test_case_ids = []
        for i, tc in enumerate(TEST_CASES):
            resp = await client.post("/api/test-cases/", json=tc)
            created = resp.json()
            test_case_ids.append(created["id"])
            print(f"   ✅ [{i+1}/{len(TEST_CASES)}] {created['title']}")

        print("\n🏃 步骤 3: 运行测试用例...")
        run_ids = []
        for i, (tc_id, tc) in enumerate(zip(test_case_ids, TEST_CASES)):
            print(f"   运行 [{i+1}/{len(TEST_CASES)}]: {tc['title']}...", end=" ", flush=True)
            resp = await client.post(
                "/api/test-runs/",
                params={"test_case_id": tc_id, "agent_config_id": agent_id},
            )
            run = resp.json()
            run_ids.append(run["id"])
            status_icon = "✅" if run["status"] == "success" else "❌"
            print(f"{status_icon} 状态={run['status']}, 耗时={run['duration_ms']}ms, Tokens={run['total_tokens']}")

        print("\n📊 步骤 4: 执行规则评分...")
        scores = []
        for i, (run_id, tc) in enumerate(zip(run_ids, TEST_CASES)):
            print(f"   评分 [{i+1}/{len(TEST_CASES)}]: {tc['title']}...", end=" ", flush=True)
            resp = await client.post(
                "/api/evaluations/",
                json={
                    "test_run_id": run_id,
                    "rules": tc["rules"],
                    "use_llm_judge": False,
                },
            )
            eval_result = resp.json()
            scores.append(eval_result["overall_score"])
            print(f"得分={eval_result['overall_score']}/5.0")

        avg_score = sum(scores) / len(scores) if scores else 0

        print("\n" + "=" * 60)
        print("📈 评测结果汇总")
        print("=" * 60)
        print(f"被测 Agent: {agent_config['name']}")
        print(f"测试用例数: {len(TEST_CASES)}")
        print(f"平均分: {avg_score:.2f}/5.0")
        print()

        print(f"{'#':<3} {'测试用例':<20} {'分类':<8} {'难度':<6} {'得分':<8}")
        print("-" * 50)
        for i, (tc, score) in enumerate(zip(TEST_CASES, scores)):
            print(f"{i+1:<3} {tc['title']:<20} {tc['category']:<8} {tc['difficulty']:<6} {score:.1f}/5.0")

        print()
        print("🔗 前端查看: http://localhost:5173/")
        print("=" * 60)

        return {
            "agent_config_id": agent_id,
            "test_case_ids": test_case_ids,
            "run_ids": run_ids,
            "scores": scores,
            "average_score": avg_score,
        }


if __name__ == "__main__":
    asyncio.run(main())
