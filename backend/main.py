from __future__ import annotations

import re
import uuid
from collections import Counter
from datetime import datetime
from typing import Dict, List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field


app = FastAPI(title="知识费曼化+记忆宫殿 API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


STOPWORDS = {
    "的", "了", "和", "是", "在", "就", "都", "而", "及", "与", "着", "或", "一个", "我们", "你", "我",
    "他们", "它", "通过", "进行", "可以", "以及", "中", "对", "为", "也", "并", "将", "被", "从", "到",
}

PALACE_ROOMS = [
    "宫殿大门",
    "迎宾长廊",
    "中央客厅",
    "藏书书房",
    "实验工坊",
    "镜面卧室",
    "观景阳台",
    "星空塔楼",
]


class KnowledgeSubmitRequest(BaseModel):
    content: str = Field(..., min_length=30, description="用户输入知识内容")
    title: str | None = Field(default="未命名主题")


class AnalyzeResult(BaseModel):
    submission_id: str
    title: str
    core_definition: str
    logic_framework: str
    key_points: List[str]
    keywords: List[str]
    created_at: str


class FeynmanResult(BaseModel):
    submission_id: str
    plain_definition: str
    life_analogy: str
    practical_example: str
    pitfalls: List[str]


class PalaceScene(BaseModel):
    room: str
    point: str
    scene_description: str
    memory_hint: str


class PalaceResult(BaseModel):
    submission_id: str
    palace_theme: str
    scenes: List[PalaceScene]


STORE: Dict[str, Dict] = {}


def split_sentences(content: str) -> List[str]:
    lines = [line.strip(" -#\t") for line in content.splitlines() if line.strip()]
    text = "。".join(lines)
    sentences = [s.strip() for s in re.split(r"[。！？!?；;\n]", text) if len(s.strip()) > 8]
    return sentences


def extract_keywords(content: str, top_k: int = 10) -> List[str]:
    tokens = re.findall(r"[\u4e00-\u9fffA-Za-z0-9_]{2,}", content)
    filtered = [t for t in tokens if t not in STOPWORDS and not t.isdigit()]
    freq = Counter(filtered)
    return [w for w, _ in freq.most_common(top_k)]


def parse_knowledge(title: str, content: str) -> Dict:
    sentences = split_sentences(content)
    if len(sentences) < 5:
        raise HTTPException(status_code=400, detail="内容过短，请至少输入 5 句有意义的知识描述。")

    keywords = extract_keywords(content)
    core_definition = sentences[0]

    ranked = sorted(
        sentences,
        key=lambda s: sum(1 for k in keywords[:8] if k in s) + min(len(s), 80) / 80,
        reverse=True,
    )
    key_points = []
    for sent in ranked:
        normalized = sent.strip()
        if normalized not in key_points:
            key_points.append(normalized)
        if len(key_points) >= 7:
            break

    while len(key_points) < 5:
        key_points.append(f"补充要点 {len(key_points)+1}：请进一步展开「{title}」中的关键机制与应用场景。")

    framework = " → ".join([f"步骤{i+1}:{p[:16]}..." for i, p in enumerate(key_points[:5])])

    return {
        "title": title,
        "core_definition": core_definition,
        "logic_framework": framework,
        "key_points": key_points,
        "keywords": keywords,
    }


def generate_feynman(parsed: Dict) -> Dict:
    title = parsed["title"]
    kps = parsed["key_points"]
    keywords = parsed["keywords"]
    plain_definition = (
        f"「{title}」可以理解为：把复杂内容拆成几个小积木，先看它解决什么问题，再看它怎么一步步发挥作用。"
        f"你只要能说清『输入是什么、过程怎么走、结果有什么价值』，就算掌握了核心。"
    )
    anchor = keywords[0] if keywords else title
    life_analogy = (
        f"把{anchor}想成做一桌菜：先准备食材（基础概念），再按顺序下锅（关键流程），"
        "最后调味摆盘（应用与优化）。如果某一步乱了，整道菜就会失去味道。"
    )
    practical_example = (
        f"实战例子：当你向同学讲解「{title}」时，可以按 3 分钟结构说：\n"
        f"1) 先用一句话定义；2) 选 {kps[0][:18]} 作为切入点；3) 用一个真实场景说明收益；"
        "4) 最后补一句常见误区，帮助对方少踩坑。"
    )
    pitfalls = [
        "只记结论不看因果：容易会背不会用。",
        "步骤顺序混乱：听起来都懂，做起来卡壳。",
        "忽略边界条件：在新场景中套用时容易出错。",
        "术语堆砌过多：别人听不懂，你也难以检验是否真懂。",
    ]
    return {
        "plain_definition": plain_definition,
        "life_analogy": life_analogy,
        "practical_example": practical_example,
        "pitfalls": pitfalls,
    }


def generate_palace(parsed: Dict) -> Dict:
    title = parsed["title"]
    scenes = []
    for i, point in enumerate(parsed["key_points"]):
        room = PALACE_ROOMS[i % len(PALACE_ROOMS)]
        scenes.append(
            {
                "room": room,
                "point": point,
                "scene_description": (
                    f"你走进{room}，墙上出现动态投影：{point[:28]}。"
                    "每靠近一步，画面就把抽象概念变成动作流程。"
                ),
                "memory_hint": (
                    f"把「{room}」和关键词「{parsed['keywords'][i % len(parsed['keywords'])] if parsed['keywords'] else title}」绑定，"
                    "回忆时先想房间，再反推要点。"
                ),
            }
        )
    return {"palace_theme": f"欧式学习宫殿：{title}", "scenes": scenes}


@app.get("/api/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/api/knowledge/submit", response_model=AnalyzeResult)
def submit_knowledge(payload: KnowledgeSubmitRequest) -> AnalyzeResult:
    parsed = parse_knowledge(payload.title or "未命名主题", payload.content)
    submission_id = str(uuid.uuid4())
    STORE[submission_id] = {
        "created_at": datetime.utcnow().isoformat() + "Z",
        "content": payload.content,
        **parsed,
    }
    return AnalyzeResult(submission_id=submission_id, created_at=STORE[submission_id]["created_at"], **parsed)


@app.get("/api/feynman/{submission_id}", response_model=FeynmanResult)
def get_feynman(submission_id: str) -> FeynmanResult:
    item = STORE.get(submission_id)
    if not item:
        raise HTTPException(status_code=404, detail="submission_id 不存在")
    result = generate_feynman(item)
    return FeynmanResult(submission_id=submission_id, **result)


@app.get("/api/palace/{submission_id}", response_model=PalaceResult)
def get_palace(submission_id: str) -> PalaceResult:
    item = STORE.get(submission_id)
    if not item:
        raise HTTPException(status_code=404, detail="submission_id 不存在")
    result = generate_palace(item)
    return PalaceResult(submission_id=submission_id, **result)
