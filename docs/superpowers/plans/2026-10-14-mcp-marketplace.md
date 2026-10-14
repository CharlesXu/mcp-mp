# mcp-mp Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. 推荐在当前会话直接执行；独立审查按该技能执行要求安排。

**Goal:** 建立 CharlesXu/mcp-mp 公开仓库，导入 WorkBuddy 278 条目录，提供可验证的 Codex、Claude Code、Cherry 接入方式。

**Architecture:** harness 目录中的归一化清单是数据源，构建脚本生成跨来源索引与自包含目录 MCP 插件。客户端适配器按单条 MCP 配方导出配置；验证状态独立于导入、生成和安装状态。目录服务只读，不代理业务工具或自动修改客户端配置。

**Tech Stack:** Python 3.11+、官方 MCP Python SDK、JSON Schema、unittest、uv 锁定依赖、GitHub Actions、git/gh。SDK 用于协议服务和握手测试；离线导入与导出尽量使用标准库。

**Spec:** `docs/design.md`

## Global Constraints

- 目标公开仓库：`CharlesXu/mcp-mp`；来源目录：`workbuddy/`；稳定 ID：`harness/slug`。
- 首批 278 条均保留名称、来源、适配状态和验证状态；CLI 与 Skill 不冒充 MCP。
- 原始 MD、CSV、JSON 保持不变，不把原始文件未经处理直接公开。
- 不复制第三方 Skill、二进制或服务端源码；保留来源和第三方权利边界。
- 不导入个人启用状态、用户路径、账号或令牌；内网条目不发布端点、仓库和连接配置。
- 认证参数使用具名占位符；未知协议保留待确认状态。
- 不借用 WorkBuddy 私有凭据进行探测；不调用业务工具。
- Codex SSE 不输出为直接 HTTP 配置；Claude Code 与 Cherry 分别适配其字段。
- 使用独立测试配置目录，不修改用户现有客户端配置。
- 发布前执行离线检查，发布后独立回读远端及 CI；认证与业务结果不得由结构检查推断。

## Review Focus

- 缺失或未知协议：记录待确认，不因 URL 后缀或 HTTP 200 推断 MCP 可用。
- URL 查询参数、认证头和本机路径：脱敏后才能公开，保留必填参数说明。
- CLI 的 command/args：没有 MCP 协议证据时不可转为 stdio 配方。
- 导出受限或未验证条目：默认拒绝不可适配项；候选模板必须显式选择并携带提示。
- SDK/客户端版本差异及网络超时：报告具体检查范围，失败不覆盖已有验证证据。

---

### Task 1: 归一化与公开数据边界

**Files:** `scripts/import_workbuddy.py`、`schemas/entry.schema.json`、`workbuddy/catalog.json`、`workbuddy/README.md`、`tests/test_import.py`。

**Interfaces:**
- Consumes: 用户指定的 `connectors-source-list.json`（278 行），以及本机市场目录中的 MCP 定义；不读取账号凭据文件。
- Produces: `normalize(row: dict, definition: dict | None) -> dict`；条目包含 `id`、`name`、`description`、`kind`、`provenance`、`connection`、`parameters`、`availability`、`verification`。
- `connection` 允许 null 或 `transport` 为 `stdio`、`streamable-http`、`sse` 的配方；存在但无法判定的配置归入待确认。

- [ ] 编写测试：278 行数量与唯一 ID；CLI 无 MCP 配方；内网端点移除；Authorization 和 token/apikey 参数脱敏；嵌套本机路径不能泄漏。
- [ ] 运行 `python3 -m unittest discover -s tests -p 'test_import.py' -v`，确认未实现时失败。
- [ ] 实现归一化、凭据参数声明和 provenance（来源日期、导入文件摘要、配置来源类型）；公开描述采用简短归纳并链接来源，不复制 Skill 正文。
- [ ] 从只读源文件导入，记录类型与适配状态统计；运行同一测试，确认通过。

### Task 2: 跨 harness 构建与校验

**Files:** `scripts/build.py`、`scripts/validate.py`、`catalog/index.json`、`workbuddy/entries/<slug>/entry.json`、`tests/test_catalog.py`。

**Interfaces:**
- Consumes: Task 1 的 `entry` 与 `schemas/entry.schema.json`。
- Produces: `build(root: Path) -> None`；`validate(root: Path) -> list[str]`（空列表表示通过）；索引使用稳定 ID 和仓库内相对路径，不携带本机路径。

- [ ] 编写测试：重复 ID、路径越界、缺失引用、违规占位符、恶意 URL 用户信息被拒绝；第二个测试 harness 可加入且不破坏 WorkBuddy 数量。
- [ ] 运行测试确认失败，然后实现确定性排序、生成索引和逐条文件；离线 schema 与敏感信息扫描。
- [ ] 运行 `python3 scripts/build.py`、`python3 scripts/validate.py`；二次构建内容摘要完全一致。

### Task 3: 客户端配置适配

**Files:** `plugins/mcp-mp-catalog/adapter.py`、`scripts/export.py`、`tests/test_adapters.py`、`docs/clients.md`。

**Interfaces:**
- Consumes: Task 1 的单条 entry。
- Produces: `export_entry(entry: dict, client: str, allow_candidate: bool = False) -> str`；client 为 `codex`、`claude`、`cherry`；不可适配时抛出 ValueError。
- Codex 输出 TOML；Claude Code 输出 `mcpServers` JSON；Cherry 输出 JSON 导入模板及所需参数说明。

- [ ] 测试 TOML/JSON 可解析；SSE 在 Codex 直接导出被拒绝；CLI/Skill、内网、协议未知项被拒绝；认证字段不含实值；候选配置必须显式选择。
- [ ] 读取当前官方客户端配置规则，特别核对 Cherry 的 JSON 导入实现；实现三种适配，URL/参数不得通过 shell 字符串拼接执行。
- [ ] 运行 `python3 -m unittest discover -s tests -p 'test_adapters.py' -v`；导出代表性条目并解析，不写入用户客户端配置。
- [ ] 文档说明配置导出与实际连接的区别，以及 OAuth/服务商申请凭据、SSE 限制和 Cherry 手工填参步骤。

### Task 4: 只读目录 MCP 与原生插件入口

**Files:** `plugins/mcp-mp-catalog/server.py`、`plugins/mcp-mp-catalog/pyproject.toml`、`plugins/mcp-mp-catalog/uv.lock`、`plugins/mcp-mp-catalog/catalog.json`、`plugins/mcp-mp-catalog/.codex-plugin/plugin.json`、`plugins/mcp-mp-catalog/.claude-plugin/plugin.json`、插件 MCP 配置文件、`.agents/plugins/marketplace.json`、`.claude-plugin/marketplace.json`、`tests/test_protocol.py`。

**Interfaces:**
- Consumes: Task 2 的聚合目录和 Task 3 的 `export_entry`。
- Produces: 官方 SDK stdio MCP 工具 `catalog_search(query: str, harness: str = '', limit: int = 20)`、`catalog_get(id: str)`、`catalog_export(id: str, client: str, allow_candidate: bool = False)`；工具只返回数据，不执行安装或业务请求。

- [ ] 编写 SDK ClientSession 测试：initialize、tools/list、搜索、查看、导出；非法 ID、limit 越界、未知 client 给出可读错误。
- [ ] 实现 SDK 服务，锁定依赖；生成插件内部数据，使安装后的插件不依赖源仓库的父目录。
- [ ] 按当前客户端规则分别配置插件路径与启动命令，不能假设二者使用同一种路径变量。
- [ ] 用 SDK 真实握手运行测试；在独立 `CODEX_HOME` 和 Claude 配置目录执行市场发现、插件安装和清单回读；测试目录仅包含本次产物。
- [ ] Cherry 目录 MCP 给出明确启动命令和可导入配置，按当前导入规则验证；未操作桌面 UI 时报告为配置验证。

### Task 5: 明确选择的协议探测

**Files:** `scripts/probe.py`、`reports/verification.json`、`docs/verification.md`、`tests/test_probe.py`。

**Interfaces:**
- Consumes: 单条公开 entry，显式指定的 ID；默认不接受私人凭据，不执行 stdio 候选中的任意命令。
- Produces: `probe(entry: dict, timeout_seconds: int = 15) -> dict`；包含 ID、UTC 时间、transport、`initialize` 和 `tools/list` 结果、错误类别；业务验证固定为未执行。

- [ ] 测试：HTTP 200 非 MCP 不能通过；401 记录需认证；超时记录失败；分页 tools/list 和不匹配请求 ID 正确处理；敏感错误内容不进入报告。
- [ ] 使用官方 SDK 实现无凭据远程握手，不追随私人/内网重定向，不自动安装程序或开启 OAuth 登录。
- [ ] 选择配置证据明确、无认证参数的公开远程条目探测并记录真实结果；需认证与受限项保持对应状态，不能标为通过。
- [ ] 更新报告及验证说明，逐项标出结构检查、协议验证、客户端安装验证与业务调用的不同含义。

### Task 6: 文档、持续验证与发布

**Files:** `README.md`、`CONTRIBUTING.md`、`LICENSE`、`NOTICE.md`、`.gitignore`、`.github/workflows/validate.yml`、`reports/release-checklist.md`。

**Interfaces:**
- Consumes: Tasks 1–5 的数据、工具、测试和报告。
- Produces: 可公开发布的仓库与可重复执行的离线 CI；`NOTICE.md` 单独标明导入元数据和服务商的权利，项目代码许可不覆盖第三方服务或内容。

- [ ] 写明三种客户端的安装方法、前置依赖、278 条覆盖率及可适配/待确认/受限统计；补充新增 harness 的操作方式。
- [ ] 配置 CI：锁定依赖安装、build 确定性检查、validate、unittest、Claude manifest 检查或本地验证结果记录；联网探测与离线发布检查分开。
- [ ] 完成一次整体审查，修复导入、配置适配及敏感信息边界问题；不宣称未测试客户端业务已可用。
- [ ] 发布前运行上述检查、`git diff --check` 和暂存内容扫描；确认未包含原始私人文件、测试 home、缓存或凭据。
- [ ] 初始化该新项目 Git，创建 `CharlesXu/mcp-mp` 公开仓库，提交并推送；用户原始请求已明确授权创建与公开发布，发布前说明最终公开内容范围。
- [ ] 通过 `gh repo view`、远端文件回读与 GitHub Actions 结果确认公开仓库、默认分支、提交和 CI 状态；失败则修复后重验。
- [ ] 报告仓库地址、实际发布数量、验证结果和需认证/未验证的限制；保持原始清单和现有客户端配置不变。
