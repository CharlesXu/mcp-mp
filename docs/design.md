# mcp-mp 设计与验收标准

目标：CharlesXu/mcp-mp 公开仓库，按来源 harness 分目录；首批导入 WorkBuddy 278 条连接器。提供 Codex、Claude Code 原生插件市场入口、Cherry 配置导入和统一只读目录 MCP。目录 MCP 负责检索、查看、生成安装配置；下游 MCP 仍由客户端单独安装认证，不能通过 GitHub URL 自动成为远程 MCP 服务。

## 结构

- workbuddy/catalog.json：脱敏后的 278 条目录；workbuddy/entries/<slug>/entry.json 是生成的单条清单。
- catalog/index.json：跨 harness 的索引，稳定 ID 为 harness/slug。
- plugins/mcp-mp-catalog：自包含目录 MCP；分别声明 Codex 与 Claude 的配置入口。
- .agents/plugins/marketplace.json / .claude-plugin/marketplace.json：原生市场入口。
- scripts：离线验证、静态客户端配置导出、显式选择条目的协议探测。
- tests、.github/workflows：协议、导出边界、脱敏与可重复构建验证。

## 导入与发布边界

仅归一化条目及 MCP 连接配方，不复制第三方 Skill、二进制或服务端源码。CLI 和仅 Skill 条目可检索，不冒充 stdio MCP。认证头和 URL 凭据参数变成显式环境变量；不导入个人启用状态、用户路径、账号或令牌。内网来源仅保留名称与受限状态，不发布内网端点、仓库或配置。未知协议保留待确认状态，不凭 URL 后缀自动标为已验证。

## 验证

结构检查（schema、唯一 ID、数量、引用、配置格式、泄漏扫描）为发布门槛。MCP initialize + tools/list 的结果单独记录时间和环境；HTTP 200/401、生成配置和市场安装均不代表业务可用。认证探测不借用 WorkBuddy 私有凭据。实际业务调用不纳入本次自动验证。

## 客户端

Codex 支持 stdio 和 Streamable HTTP 配方；SSE 不直接输出为 Codex HTTP。Claude Code 输出 stdio/http/sse 的 mcpServers。Cherry 输出可手动导入的 mcpServers 模板，标明占位符必须填写。目录 MCP 不自动安装、不执行任意命令，也不代理下游业务工具。

## 验收

278 条均有溯源、适配状态和验证状态；不可移植条目明确原因。目录 MCP 通过真实 SDK 握手测试，客户端导出通过语法和适配测试；Codex 和 Claude 在独立配置目录完成原生市场发现/安装检查；Cherry 使用当前官方实现的 JSON 导入规则验证，不宣称桌面 UI 已实测。发布前通过 CI 同等检查；发布后读取远端仓库与 CI 结果。

## 参考

- https://github.com/Kilo-Org/kilo-marketplace/tree/main/mcps ：逐条定义、聚合目录、参数声明。
- https://github.com/CherryHQ/mcpmarket ：目录发现与安装配方分离；当前实现不等价于 Cherry Studio 内置市场。
- https://github.com/xpack-ai/XPack-MCP-Marketplace ：服务信息与认证描述；首版不部署交易、计费或 MCP 代理后台。
