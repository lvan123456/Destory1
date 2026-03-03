# 知识费曼化 + 记忆宫殿可视化

一个完整的本地可运行项目：
- **Python FastAPI 后端**：知识解析、费曼化生成、记忆宫殿生成。
- **前端单页**：输入知识、展示费曼解释、交互式宫殿场景、历史记录、深浅色模式。

## 目录结构

```bash
.
├── backend/
│   └── main.py
├── frontend/
│   └── index.html
└── requirements.txt
```

## 一键本地运行

### 1) 安装依赖

```bash
python -m venv .venv
source .venv/bin/activate  # Windows 使用 .venv\Scripts\activate
pip install -r requirements.txt
```

### 2) 启动后端

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### 3) 启动前端

在另一个终端运行（任意静态服务方式即可）：

```bash
python -m http.server 5500 --directory frontend
```

浏览器打开：`http://127.0.0.1:5500`

## 前后端联调说明

- 前端默认请求地址：`http://127.0.0.1:8000/api`
- 若后端端口改变，请修改 `frontend/index.html` 中 `API_BASE` 常量。
- 后端已开启 CORS（允许本地开发跨域）。

## RESTful API 文档

### 1) 提交知识

- **POST** `/api/knowledge/submit`
- 请求体：

```json
{
  "title": "HTTP",
  "content": "HTTP 是超文本传输协议...（至少 30 字，建议 5 句以上）"
}
```

- 返回示例：

```json
{
  "submission_id": "uuid",
  "title": "HTTP",
  "core_definition": "...",
  "logic_framework": "步骤1:... → 步骤2:...",
  "key_points": ["..."],
  "keywords": ["..."],
  "created_at": "2026-01-01T00:00:00Z"
}
```

### 2) 获取费曼化内容

- **GET** `/api/feynman/{submission_id}`
- 返回字段：
  - `plain_definition` 通俗定义
  - `life_analogy` 生活类比
  - `practical_example` 实战例子
  - `pitfalls` 易错点提醒

### 3) 获取记忆宫殿数据

- **GET** `/api/palace/{submission_id}`
- 返回字段：
  - `palace_theme` 宫殿主题
  - `scenes[]` 每个场景包含 `room / point / scene_description / memory_hint`

### 4) 健康检查

- **GET** `/api/health`

## 说明

- 当前项目使用 Python 文本规则与关键词统计实现知识提取，无需额外模型即可运行。
- 若后续需要更高性能，可在 `backend` 中将 `parse_knowledge`/`generate_palace` 核心逻辑替换为 C++ 扩展模块（如 `pybind11`）。
