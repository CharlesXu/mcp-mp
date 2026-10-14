# 客户端接入

本仓库支持两步使用：先连接目录 MCP，检索接入条件；再按需安装选定的下游 MCP。目录 MCP 不动态代理下游工具、不申请凭据、不自动安装 278 个服务。

## Codex

```bash
codex plugin marketplace add CharlesXu/mcp-mp
codex plugin add mcp-mp-catalog@mcp-mp
codex plugin list --json
```

插件需要 uv 和 Python 3.11+。重新开启会话以加载工具。如果桌面 UI 未刷新，可先从 CLI 回读插件是否安装并启用。

也可以克隆仓库后运行 `python3 scripts/catalog_config.py --client codex`，得到目录 MCP 的 TOML 配置。只合并需要的服务器段，不覆盖原有 `config.toml`。

下游 HTTP 配方使用 `url`、`http_headers`、`env_http_headers`。后者的值是环境变量名字，不是令牌；若头名为 Authorization，变量值必须包含服务商要求的完整 `Bearer ...` 前缀。此项目拒绝把 SSE 或需要动态 URL 替换的配方当成可直接导入的 Codex HTTP 配置。请先向服务商获得可用的 Streamable HTTP 接入方式。

参考：[官方 MCP 配置](https://learn.chatgpt.com/docs/extend/mcp?surface=cli)。

## Claude Code

```bash
claude plugin marketplace add CharlesXu/mcp-mp
claude plugin install mcp-mp-catalog@mcp-mp
claude plugin list --json
```

插件里的 `${CLAUDE_PLUGIN_ROOT}` 由 Claude Code 替换。下游 JSON 配方使用 `type: http` 或 `sse`；标准输入输出服务使用 `stdio`。

把 `scripts/export.py` 输出的服务器段合并到项目 `.mcp.json` 或按官方 `claude mcp add-json` 方法添加。填入此仓库声明的专用环境变量，不能直接借用 WorkBuddy 登录令牌。若服务商提供标准 OAuth，安装后在 `/mcp` 中完成授权；服务商仍可能要求客户端注册、付费或组织权限。

这里的 Claude 指 Claude Code。Claude Desktop 的本地配置/远程连接方式不同，未声明支持其插件市场。

参考：[官方 MCP 文档](https://code.claude.com/docs/en/mcp)、[插件配置](https://code.claude.com/docs/en/plugins-reference)。

## Cherry Studio

克隆本仓库后：

```bash
python3 scripts/catalog_config.py --client cherry
```

在 MCP 设置中选择从 JSON 添加，将输出粘贴进去。启动命令是 uv，参数指向本机克隆中的 `plugins/mcp-mp-catalog`；生成器会填入本机绝对路径。移动克隆目录后需要重新生成。

下游配置使用 `mcpServers`、`type: streamableHttp` / `sse`、`url`、`headers`。所有 `${WB_...}` 均为待填写模板，先手工替换再导入，不能假设 Cherry 会像 Claude 一样展开环境变量。Cherry 导入可能主动连接服务器，因此导入前完成参数填写并确认所选服务。

本项目没有修改 Cherry 的内置市场，也没有宣称 Cherry 自动订阅任意 GitHub 仓库。提供的是目录 MCP 和当前官方实现接受的 JSON 导入格式。

核对依据：[官方 JSON 导入实现](https://github.com/CherryHQ/cherry-studio/blob/main/src/renderer/pages/settings/McpSettings/AddMcpServerModal.tsx)、[配置校验规则](https://github.com/CherryHQ/cherry-studio/blob/main/src/renderer/types/mcp.ts)。

## 目录工具示例

1. `catalog_search(query="网盘", harness="workbuddy")`。
2. `catalog_get(id="workbuddy/baidu-netdisk")`，查看协议、授权要求和最新检查。
3. `catalog_export(id="workbuddy/baidu-netdisk", client="cherry", allow_candidate=true)`。
4. 独立申请授权、填写模板，在客户端完成协议和业务验证。

CLI/Skill、受限来源和待审查项可以查看详情，但导出工具会明确拒绝。配置模板不会证明服务可用。
