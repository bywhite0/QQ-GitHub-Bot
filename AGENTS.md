# QQ-GitHub-Bot AGENTS 指南

本文件是仓库级协作契约，面向 AI 代理优先，同时可供人工贡献者参考。目标是让改动严格贴合现有代码与提交风格，减少无关差异与返工。

## 项目速览与目录边界

- 运行入口是 `bot.py`，基于 NoneBot2，核心业务在 `src/`。
- `src/plugins/` 放业务插件（GitHub、状态、健康检查等），`src/providers/` 放平台与基础设施提供方（Redis、Postgres、Playwright、平台抽象）。
- `scripts/` 放开发与运维脚本（数据库迁移入口、HTML 生成工具等）。
- `migrations/` 放 Alembic 迁移脚本。
- `k8s/`、`docker/`、`.devcontainer/` 是部署与开发环境配置。
- `assets/` 放静态资源。

边界约定：

- 优先在既有目录内扩展，不随意新增平行层级。
- 新功能优先复用现有 provider / dependency / helper 结构，不重复造轮子。
- 不在一次提交中混入无关目录的重排或样式清扫。

## 开发与验证命令

推荐使用 Poetry 工作流：

```bash
poetry install
poetry run pre-commit install --hook-type pre-commit --hook-type prepare-commit-msg
poetry run playwright install chromium
poetry run python scripts/database.py upgrade
poetry run python bot.py
```

提交前统一检查：

```bash
poetry run pre-commit run --all-files
poetry run pyright
```

说明：

- `pre-commit` 是本地统一入口，覆盖 `ruff + isort + black`，并安装 `prepare-commit-msg` 钩子。
- CI 重点检查是 `Ruff` 与 `Pyright`（见 `.github/workflows/ruff.yml`、`.github/workflows/pyright.yml`）。
- 当前仓库无独立 `tests/` 目录，最小可行验证为“静态检查 + 受影响功能冒烟验证”。

## 代码风格硬规则

- Python 版本基线是 3.11。
- Python 格式化与静态规范以 `black + isort + ruff + pyright` 为准，不手写对抗工具结果。
- 行宽 88（Python 代码、导入、注解都按该限制）。
- 缩进与换行遵循 `.editorconfig`：
- `*.py` 使用 4 空格缩进。
- 其他多数文本文件使用 2 空格缩进。
- 统一 UTF-8、LF、保留文件末尾换行。
- 导入顺序交给 `isort`，不要手工打乱分组或长度排序策略。
- 类型标注保持与现有代码一致，新增逻辑优先补充显式类型。
- 异常处理优先“具体异常在前，兜底异常在后”，日志信息应包含上下文。

文件头注释策略（已确认）：

- 采用“按邻近继承”：同目录同类型文件普遍有 `@Author/@Date/...` 文件头时保持一致。
- 如果同目录同类型文件普遍没有文件头，则不强制新增。
- 不为满足格式而批量补历史文件头，避免引入无关 diff。

## 按目录的实现约定

`src/`：

- 保持现有插件式组织方式，按 `config/dependencies/helpers/libs/models/plugins/webhooks` 分层。
- NoneBot handler 延续现有写法：明确 matcher、参数依赖、消息发送分支与异常分层处理。
- 与平台类型相关的分发逻辑保持 `match/case` 与类型联合的一致风格。

`scripts/`：

- 脚本以可执行、可读为主，允许 `print` 输出（仓库已在 Ruff 中对 `scripts/*` 放宽 `T201`）。
- 参数解析、入口函数、异步执行模式保持现有脚本习惯。

`migrations/`：

- 只做迁移所需最小变更，保证 `upgrade/downgrade` 对称与可回滚。
- 不在迁移脚本夹带业务逻辑重构。

`k8s/`：

- 保持 Helm 模板风格与 2 空格缩进，不改动既有 values key 语义。
- 新增配置必须可被 `values.yaml` 覆盖，并与现有命名风格一致。

模板与样式（`*.html.jinja`、`*.css`）：

- 维持现有模板命名和组织方式，避免无关 HTML 结构重排。
- 样式修改应聚焦问题本身，禁止整文件格式化导致大面积噪音 diff。

## 提交与 PR 风格

提交标题格式：

```text
:<gitmoji>: <祈使句短标题>
```

硬性要求：

- 使用 `:bug:` 这类 gitmoji shortcode，不使用 Unicode emoji。
- 标题单行、简短、无句号，直接描述本次改动。
- 标题语言允许中文、英文或中英混合，但格式必须统一。
- 标题应与改动类型匹配，常用前缀沿用仓库历史高频语义。

推荐前缀语义：

- `:bug:` 缺陷修复
- `:sparkles:` 新功能
- `:arrow_up:` 依赖升级
- `:wrench:` 配置或工具链调整
- `:memo:` 文档变更
- `:bookmark:` 版本 bump
- `:lipstick:` UI/样式优化
- `:rotating_light:` 代码质量修复（lint/type）

与历史一致的标题示例：

- `:bug: fix syntax error`
- `:sparkles: add contribution details`
- `:arrow_up: upgrade dependencies`
- `:bookmark: bump version 3.0.4`
- `:memo: Docs: 补充配置项说明`

PR 约定：

- 一个 PR 聚焦一个问题域，避免混合重构、格式化、功能改动。
- 描述里写清动机、主要改动、验证方式、潜在风险。
- 禁止“无关重排/大面积格式噪音提交”。

## 变更完成定义（DoD）

满足以下条件才算完成：

- 改动范围最小化，无无关文件变更。
- `poetry run pre-commit run --all-files` 通过。
- 涉及 Python 逻辑改动时，`poetry run pyright` 通过。
- 完成受影响路径的最小冒烟验证：
- 服务入口相关改动可启动 `bot.py`。
- 脚本相关改动可执行对应 `scripts/*.py` 命令。
- 迁移相关改动可执行数据库迁移命令并确认无异常。
- 提交信息符合本文件的 gitmoji 规则。

## 规则依据（事实来源）

- 代码与工具配置：`pyproject.toml`
- 编辑器与换行约束：`.editorconfig`
- 本地钩子与格式化入口：`.pre-commit-config.yaml`
- CI 检查项：`.github/workflows/ruff.yml`、`.github/workflows/pyright.yml`
- 提交风格基线：`git log` 近期历史
