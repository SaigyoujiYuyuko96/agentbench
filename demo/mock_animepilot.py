import time
import random
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from typing import Optional, List

app = FastAPI(title="Mock AnimePilot")


class AgentChatRequest(BaseModel):
    content: str
    conversation_id: Optional[int] = None


class AgentSource(BaseModel):
    title: str
    url: Optional[str] = None
    snippet: Optional[str] = None


class AgentCard(BaseModel):
    type: str
    title: str
    description: Optional[str] = None


class AgentChatResponse(BaseModel):
    answer: str
    conversation_id: Optional[int] = None
    trace_id: Optional[int] = None
    cards: List[AgentCard] = []
    sources: List[AgentSource] = []
    # AgentBench 的 http runner 会读 trace_field，把这里的步骤原样写进 run_steps。
    # 有了它，运行详情页才能画出真实的调用链，而不是只有一步 "HTTP POST"。
    trace: List[dict] = []


MOCK_DB = {
    "search": {
        "葬送的芙莉莲": {
            "answer": (
                "《葬送的芙莉莲》（葬送のフリーレン）是山田钟人原作、阿部司作画的日本奇幻漫画，"
                "2020 年起在《周刊少年Sunday》连载。故事讲述精灵魔法使芙莉莲在勇者队伍击败魔王后，"
                "以千年寿命的视角重新踏上旅程，理解人类与时间的意义。\n\n"
                "【基本信息】\n"
                "- 原作：山田钟人\n"
                "- 作画：阿部司\n"
                "- 动画制作：MADHOUSE\n"
                "- 首播时间：2023年9月\n"
                "- 集数：28集\n"
                "- 评分：9.8/10\n\n"
                "【获奖情况】\n"
                "- 2024年第71回小学馆漫画赏少年向部门\n"
                "- 2023年这本漫画真厉害！男性篇第1位\n"
                "- 2022年第15回漫画大赏第2位"
            ),
            "cards": [
                {"type": "subject", "title": "葬送的芙莉莲", "description": "奇幻 / 治愈 / 冒险"},
            ],
            "sources": [
                {"title": "Bangumi - 葬送的芙莉莲", "url": "https://bgm.tv/subject/333004", "snippet": "精灵魔法使芙莉莲的千年旅程..."},
                {"title": "维基百科 - 葬送的芙莉莲", "snippet": "山田钟人原作的奇幻漫画作品..."},
            ],
            "intent": "search",
            "steps": [
                {"step_type": "intent_detection", "name": "意图识别", "latency_ms": 45},
                {"step_type": "tool_call", "name": "Bangumi搜索", "latency_ms": 320},
                {"step_type": "rag_retrieval", "name": "知识库检索", "latency_ms": 180},
                {"step_type": "llm_generation", "name": "答案生成", "latency_ms": 890, "token_input": 1200, "token_output": 350},
            ],
        },
        "夏目友人帐": {
            "answer": (
                "《夏目友人帐》（夏目友人帳）是绿川幸创作的日本治愈系漫画，2003年起在《LaLa DX》连载。"
                "故事讲述能看见妖怪的少年夏目贵志，继承了外祖母夏目玲子的「友人帐」——一本记录着"
                "被玲子打败的妖怪们名字的契约书。夏目决定将名字一一还给妖怪们，在这个过程中，"
                "他与妖怪们结下了各式各样的羁绊，也逐渐理解了玲子的内心。\n\n"
                "【基本信息】\n"
                "- 原作：绿川幸\n"
                "- 动画制作：Brain's Base（第1-4季）、朱夏（第5季起）\n"
                "- 首播时间：2008年7月\n"
                "- 季数：共7季\n"
                "- 评分：9.4/10\n\n"
                "【主题】\n"
                "温柔、治愈、人与妖怪的羁绊、孤独与陪伴"
            ),
            "cards": [
                {"type": "subject", "title": "夏目友人帐", "description": "治愈 / 奇幻 / 日常"},
            ],
            "sources": [
                {"title": "Bangumi - 夏目友人帐", "snippet": "能看见妖怪的少年夏目贵志的故事..."},
            ],
            "intent": "search",
            "steps": [
                {"step_type": "intent_detection", "name": "意图识别", "latency_ms": 42},
                {"step_type": "tool_call", "name": "Bangumi搜索", "latency_ms": 280},
                {"step_type": "rag_retrieval", "name": "知识库检索", "latency_ms": 150},
                {"step_type": "llm_generation", "name": "答案生成", "latency_ms": 720, "token_input": 980, "token_output": 280},
            ],
        },
        "京阿尼": {
            "answer": (
                "京都动画（Kyoto Animation），简称「京阿尼」，是日本著名的动画制作公司，1981年成立。"
                "以高质量的作画、细腻的情感描写和稳定的产量著称。\n\n"
                "【代表作】\n"
                "- 《凉宫春日的忧郁》（2006）\n"
                "- 《轻音少女！》（2009-2010）\n"
                "- 《紫罗兰永恒花园》（2018）\n"
                "- 《冰菓》（2012）\n"
                "- 《吹响！上低音号》（2015-2024）\n"
                "- 《CLANNAD》（2007-2008）\n"
                "- 《玉子市场》（2013）\n\n"
                "【特点】\n"
                "- 独立培养动画师，有自己的养成学校\n"
                "- 大量使用原创分镜，作画质量稳定\n"
                "- 擅长日常系、情感系作品\n"
                "- 全员正社员制度，业界良心"
            ),
            "cards": [
                {"type": "subject", "title": "京都动画", "description": "动画制作公司"},
            ],
            "sources": [
                {"title": "维基百科 - 京都动画", "snippet": "日本动画制作公司，总部位于京都府..."},
                {"title": "Bangumi - 京阿尼作品列表", "snippet": "京都动画历年作品一览..."},
            ],
            "intent": "search",
            "steps": [
                {"step_type": "intent_detection", "name": "意图识别", "latency_ms": 50},
                {"step_type": "tool_call", "name": "Bangumi搜索", "latency_ms": 450},
                {"step_type": "rag_retrieval", "name": "知识库检索", "latency_ms": 220},
                {"step_type": "llm_generation", "name": "答案生成", "latency_ms": 950, "token_input": 1500, "token_output": 420},
            ],
        },
    },
    "qa": {
        "虫师为什么评价高": {
            "answer": (
                "《虫师》之所以能获得如此高的评价，我认为有以下几个原因：\n\n"
                "**1. 独特的美学风格**\n"
                "漆原友纪的原作水墨画风格，加上动画制作公司 ART LAND 的还原，"
                "营造出一种空灵、静谧的日式美学氛围。每一集都像一幅会动的浮世绘。\n\n"
                "**2. 单元剧的叙事魅力**\n"
                "每集一个独立的「虫」的故事，主角银古只是过客。这种叙事方式让观众能够"
                "在短时间内体验完整的情感起伏，而每一个故事背后都有对生命、对存在的思考。\n\n"
                "**3. 深刻的主题**\n"
                "《虫师》探讨的不是简单的善恶对立，而是「共生」——人类与自然、"
                "科学与未知、存在与虚无。虫既不是善也不是恶，只是一种存在形式。\n\n"
                "**4. 音乐与氛围**\n"
                "增田俊郎的配乐完美契合了作品的气质，尺八、三味线等传统乐器的运用，"
                "让整部作品的氛围感拉满。\n\n"
                "**5. 治愈与哲思并存**\n"
                "它不是一部会让你热血沸腾的作品，但它会让你在安静中感受到力量，"
                "在看完后久久回味。这种「慢治愈」在快节奏的当下尤为珍贵。"
            ),
            "cards": [],
            "sources": [
                {"title": "Bangumi - 虫师 评论", "snippet": "最安静的动画，最有力量的治愈..."},
                {"title": "知乎 - 如何评价虫师", "snippet": "一部探讨生命本质的作品..."},
            ],
            "intent": "qa",
            "steps": [
                {"step_type": "intent_detection", "name": "意图识别", "latency_ms": 55},
                {"step_type": "rag_retrieval", "name": "知识库检索", "latency_ms": 200},
                {"step_type": "context_building", "name": "上下文构建", "latency_ms": 30},
                {"step_type": "llm_generation", "name": "答案生成", "latency_ms": 1100, "token_input": 1800, "token_output": 520},
            ],
        },
        "推荐类似虫师的作品": {
            "answer": (
                "如果你喜欢《虫师》那种安静、治愈、带点奇幻色彩的作品，我推荐以下几部：\n\n"
                "**1. 《夏目友人帐》**\n"
                "最常被拿来和虫师比较的作品。同样是人与非人存在的相遇，同样温柔治愈。"
                "不同的是夏目更侧重「羁绊」与「陪伴」，而虫师更偏向「过客」与「观照」。\n\n"
                "**2. 《物怪》（ものんく）**\n"
                "改编自日本民间传说，讲述药郎驱魔的故事。浮世绘风格的画面非常有特色，"
                "每个故事都有深刻的人性探讨，氛围和虫师很像。\n\n"
                "**3. 《灰羽联盟》**\n"
                "安倍吉俊的作品，讲述一群失去记忆、长着灰色翅膀的少女在虚构小镇上的生活。"
                "氛围安静、略带忧伤，充满隐喻和哲思。\n\n"
                "**4. 《电脑线圈》**\n"
                "虽然设定是近未来科幻，但那种孩子们在城市角落探索神秘事物的感觉，"
                "和虫师的「探索未知」有异曲同工之妙。\n\n"
                "**5. 《宝石之国》**\n"
                "同样探讨「存在」与「记忆」的主题，画面风格独特，故事后劲很大。"
            ),
            "cards": [
                {"type": "subject", "title": "夏目友人帐", "description": "治愈 / 奇幻"},
                {"type": "subject", "title": "物怪", "description": "怪谈 / 浮世绘"},
                {"type": "subject", "title": "灰羽联盟", "description": "奇幻 / 治愈"},
            ],
            "sources": [
                {"title": "Bangumi - 相似作品推荐", "snippet": "基于标签和评分的相似作品..."},
            ],
            "intent": "recommendation",
            "steps": [
                {"step_type": "intent_detection", "name": "意图识别", "latency_ms": 48},
                {"step_type": "tool_call", "name": "推荐计算", "latency_ms": 150},
                {"step_type": "user_profile", "name": "用户画像匹配", "latency_ms": 60},
                {"step_type": "llm_generation", "name": "推荐理由生成", "latency_ms": 980, "token_input": 1600, "token_output": 480},
            ],
        },
    },
}


def find_best_match(query: str):
    query_lower = query.lower()
    for category in MOCK_DB.values():
        for key, value in category.items():
            if key.lower() in query_lower:
                return value
    return None


def generate_fallback(query: str):
    intents = ["search", "qa", "recommendation"]
    intent = random.choice(intents)
    return {
        "answer": f"关于「{query}」，我在知识库中找到了一些相关信息。这是一个关于动漫的查询，我会尽力为你解答。由于数据有限，答案可能不够完整，建议结合 Bangumi 等专业站点获取更多信息。",
        "cards": [{"type": "subject", "title": query, "description": "动漫作品"}],
        "sources": [{"title": f"搜索结果 - {query}", "snippet": "相关资料片段..."}],
        "intent": intent,
        "steps": [
            {"step_type": "intent_detection", "name": "意图识别", "latency_ms": 50 + random.randint(0, 30)},
            {"step_type": "tool_call", "name": "搜索工具", "latency_ms": 200 + random.randint(0, 200)},
            {"step_type": "llm_generation", "name": "答案生成", "latency_ms": 500 + random.randint(0, 500), "token_input": 500 + random.randint(0, 500), "token_output": 150 + random.randint(0, 200)},
        ],
    }


@app.post("/api/agent/chat", response_model=AgentChatResponse)
async def chat(payload: AgentChatRequest, authorization: Optional[str] = Header(None)):
    # 计时放在 sleep 之前，这样最后一步的耗时才反映真实调用时长
    started = time.perf_counter()

    # 模拟处理时间
    time.sleep(0.3 + random.random() * 0.5)

    result = find_best_match(payload.content)
    if result is None:
        result = generate_fallback(payload.content)

    # 模拟 trace_id
    trace_id = random.randint(1000, 9999)

    # 构造一条像样的调用链：意图识别 → 检索 → 检索命中判断 → 生成。
    # 这不是真 LLM，但步骤形状和真实 Agent 一致，评测平台照单全收。
    total_ms = int((time.perf_counter() - started) * 1000)
    trace = [
        {
            "step_type": "intent",
            "name": "意图识别",
            "input": {"query": payload.content},
            "output": {"intent": result.get("intent", "search")},
            "latency_ms": 42,
            "token_input": 0,
            "token_output": 0,
            "status": "success",
        },
        {
            "step_type": "retrieval",
            "name": "知识库检索",
            "input": {"query": payload.content, "top_k": 5},
            "output": {"hits": len(result.get("cards", []))},
            "latency_ms": 118,
            "token_input": 0,
            "token_output": 0,
            "status": "success",
        },
        {
            "step_type": "generation",
            "name": "生成回答",
            "input": {"context_size": 3},
            "output": {"chars": len(result["answer"])},
            "latency_ms": max(total_ms - 160, 1),
            "token_input": 0,
            "token_output": 0,
            "status": "success",
        },
    ]

    return AgentChatResponse(
        answer=result["answer"],
        conversation_id=payload.conversation_id or 1,
        trace_id=trace_id,
        cards=[AgentCard(**c) for c in result.get("cards", [])],
        sources=[AgentSource(**s) for s in result.get("sources", [])],
        trace=trace,
    )


@app.post("/api/agent/chat-degraded", response_model=AgentChatResponse)
async def chat_degraded(payload: AgentChatRequest, authorization: Optional[str] = Header(None)):
    """故意退化的 Agent：命中时丢掉大部分关键事实，用来验证评测平台能否抓出质量下降。

    这是 demo 的对照组。评测平台若只能给出 5.0 分，说明它区分不出好坏；
    能对同一个用例给出明显更低的分数，才算真的在评测。
    """
    time.sleep(0.1)

    result = find_best_match(payload.content)
    if result is None:
        answer = "抱歉，我不太清楚这个问题。"
        retrieval_hits = 0
    else:
        # 只保留前 40 个字符，模拟「回答被截断 / 事实被丢掉」
        answer = result["answer"][:40] + "……"
        retrieval_hits = len(result.get("cards", []))

    # 同一条调用链，但检索步骤标成"命中率低"，让退化在 trace 上也看得见
    trace = [
        {
            "step_type": "intent",
            "name": "意图识别",
            "input": {"query": payload.content},
            "output": {"intent": "search"},
            "latency_ms": 38,
            "token_input": 0,
            "token_output": 0,
            "status": "success",
        },
        {
            "step_type": "retrieval",
            "name": "知识库检索",
            "input": {"query": payload.content, "top_k": 5},
            "output": {"hits": retrieval_hits},
            "latency_ms": 12,
            "token_input": 0,
            "token_output": 0,
            "status": "error" if retrieval_hits == 0 else "success",
            "error_message": "检索未命中，回退到通用话术" if retrieval_hits == 0 else None,
        },
        {
            "step_type": "generation",
            "name": "生成回答（截断）",
            "input": {"context_size": retrieval_hits},
            "output": {"chars": len(answer)},
            "latency_ms": 20,
            "token_input": 0,
            "token_output": 0,
            "status": "success",
        },
    ]

    return AgentChatResponse(
        answer=answer,
        conversation_id=payload.conversation_id or 1,
        trace=trace,
        trace_id=random.randint(1000, 9999),
        cards=[],
        sources=[],
    )


@app.get("/api/agent/traces/{trace_id}")
async def get_trace(trace_id: int):
    return {
        "id": trace_id,
        "user_id": 1,
        "conversation_id": 1,
        "intent": "search",
        "model": "gpt-4.1-mini",
        "total_latency_ms": 1500,
        "steps": [],
    }


@app.get("/api/system/health")
async def health():
    return {"status": "ok", "app": "MockAnimePilot"}


@app.post("/api/auth/register")
async def register():
    return {"access_token": "mock-jwt-token", "token_type": "bearer", "user": {"id": 1, "email": "test@example.com"}}


@app.post("/api/auth/login")
async def login():
    return {"access_token": "mock-jwt-token", "token_type": "bearer", "user": {"id": 1, "email": "test@example.com"}}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
