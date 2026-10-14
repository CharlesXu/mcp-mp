# mcp-mp

[![Validate marketplace](https://github.com/CharlesXu/mcp-mp/actions/workflows/validate.yml/badge.svg)](https://github.com/CharlesXu/mcp-mp/actions/workflows/validate.yml)

按来源 harness 组织的 MCP 连接器目录。首批收录 **WorkBuddy 278 条**，提供 Codex、Claude Code 插件市场入口、Cherry Studio JSON 配置模板和只读目录 MCP。

目录 MCP 可以搜索条目、查看接入要求、导出选定服务的配置。下游服务由客户端分别安装和认证；仓库 URL 是目录入口，不是远程 MCP 服务地址。

## 使用

前置条件：安装 [uv](https://docs.astral.sh/uv/getting-started/installation/)；启动时需要 Python 3.11+，uv 会依据锁文件准备官方 MCP SDK。首次启动需要能访问 Python 包源。

### Codex

```bash
codex plugin marketplace add CharlesXu/mcp-mp
codex plugin add mcp-mp-catalog@mcp-mp
```

重新打开会话后，让 Codex 调用 `catalog_search` 搜索服务、`catalog_get` 查看接入条件、`catalog_export` 导出单条配置。未做协议验证的配方需要明确 `allow_candidate=true`。

### Claude Code

```text
/plugin marketplace add CharlesXu/mcp-mp
/plugin install mcp-mp-catalog@mcp-mp
```

或者使用 CLI：

```bash
claude plugin marketplace add CharlesXu/mcp-mp
claude plugin install mcp-mp-catalog@mcp-mp
```

### Cherry Studio

```bash
git clone https://github.com/CharlesXu/mcp-mp.git
cd mcp-mp
python3 scripts/catalog_config.py --client cherry
```

将输出的 JSON 导入 Cherry Studio 的 MCP 设置。这份配置提供目录工具；检索到所需服务后，单独导出并导入该服务。也可按 [客户端说明](docs/clients.md)手动填写启动命令。

### 导出选定服务

```bash
python3 scripts/export.py workbuddy/qcc-company --client codex --allow-candidate
python3 scripts/export.py workbuddy/baidu-netdisk --client claude --allow-candidate
python3 scripts/export.py workbuddy/baidu-netdisk --client cherry --allow-candidate
```

输出是配置模板，不写入客户端配置。`${WB_...}` 声明需要独立从服务商获取的参数：Claude Code 可从环境变量展开；Cherry 需手工替换；Codex 的认证头通过 `env_http_headers` 读取完整头值。Codex 不直接导出旧式 SSE 或带动态 URL 参数的配方。

## WorkBuddy 覆盖范围

| 分类 | 数量 | 可用方式 |
|---|---:|---|
| 候选 MCP 配方 | 201 | 190 条 Streamable HTTP、11 条 SSE；需独立验证与认证 |
| CLI / Skill | 56 | 可检索；不作为 MCP 安装 |
| 待补充协议或启动依据 | 13 | 可检索；暂不导出连接配置 |
| 受限来源 | 8 | 保留条目；不公开端点和连接配置 |
| 总计 | **278** | 全部有来源、分类和验证状态 |

其中 62 条候选配方包含必填参数。未知授权条件不等于无需认证。源码地址来自原清单，标为“尚未独立核验”；有公开仓库也不保证它就是托管服务的实现。

查看 [WorkBuddy 清单](workbuddy/README.md)、[统一索引](catalog/index.json)、[客户端验证报告](reports/client-smoke.json)和[协议抽检报告](reports/verification.json)。

## 验证范围

- 离线检查：数量、唯一 ID、JSON Schema、参数声明、公开数据边界、生成文件一致性和客户端配置解析。
- 目录 MCP：真实 SDK stdio 握手、工具发现、分页检索、查看、导出、错误处理及插件安装副本启动。
- Codex / Claude：在独立配置目录验证原生市场添加、安装和回读；SDK 验证安装副本。未运行模型会话或下游业务工具。
- Cherry：对照当前官方 JSON 导入规则验证模板；尚未操作桌面 UI。
- 远程服务：显式选择条目进行无凭据 `initialize` 和 `tools/list`，不调用业务工具。首次四条抽检因本机非公开 DNS 映射被跳过，不能据此判断服务不可用。

目录条目的 `verification` 反映导入/离线阶段；最新远程检查单独放在报告和 `catalog_get.latest_protocol_check` 中。框架验证通过与某一业务服务可用是不同结论。

## 目录与扩展

```text
workbuddy/                       # 来源清单和生成的单条记录
catalog/index.json                # 所有 harness 的统一索引
harnesses.json                    # 数据源登记和预期数量
schemas/entry.schema.json         # 统一条目契约
plugins/mcp-mp-catalog/            # 自包含的只读目录 MCP
.agents/plugins/marketplace.json  # Codex 原生市场入口
.claude-plugin/marketplace.json    # Claude Code 原生市场入口
scripts/                         # 导入、构建、验证、导出、探测
reports/                         # 带范围和时间的验证证据
```

后续来源放到 `<harness>/catalog.json`，在 `harnesses.json` 登记。稳定 ID 为 `<harness>/<slug>`；同一个服务来自多个 harness 时保留独立来源，不默默合并认证配方。步骤见 [贡献说明](CONTRIBUTING.md)。

```bash
uv sync --frozen
uv run --frozen python scripts/build.py --check
uv run --frozen python scripts/validate.py
uv run --frozen python -m unittest discover -s tests -v
```

协议探测需要明确选定 ID：

```bash
uv run --frozen python scripts/probe.py workbuddy/qcc-company --timeout 15
python3 scripts/build.py
```

## 参考与权利

框架参考 [Kilo MCP 条目与聚合目录](https://github.com/Kilo-Org/kilo-marketplace/tree/main/mcps)、[CherryHQ/mcpmarket 的发现与配置流程](https://github.com/CherryHQ/mcpmarket)、[XPack 的服务目录与认证描述](https://github.com/xpack-ai/XPack-MCP-Marketplace)。没有复制这些仓库的代码。

项目原创代码采用 [MIT](LICENSE)。第三方元数据、服务、软件和商标的权利另见 [NOTICE](NOTICE.md)；这里不分发服务商的 Skill 正文、二进制或服务端代码。
