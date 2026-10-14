# 新增或更新来源

1. 建立 `<harness>/catalog.json`，每条符合 `schemas/entry.schema.json`。使用 `<harness>/<slug>` 稳定 ID，保留来源日期、公开来源引用或摘要。
2. 在 `harnesses.json` 添加该来源、文件路径及预期数量。不要用 WorkBuddy 的导入脚本导入其他来源；该脚本专门对应已授权的 278 条快照。
3. MCP、CLI、Skill 分别分类。没有协议证据的命令不可写成 stdio MCP；缺失或未知协议不猜测。受限条目保留元数据，不保留端点和连接配置。
4. 必填认证参数用 `${UPPERCASE_NAME}` 声明在 `parameters`，禁止私人安装状态、本机路径、用户名、令牌、内网 URL 或凭据 URL。参数 name 与引用必须一致。
5. 执行 `python3 scripts/build.py`；生成逐条记录、统一索引和插件内部数据。
6. 执行 `uv run --frozen python scripts/validate.py` 和 `uv run --frozen python -m unittest discover -s tests -v`。确认 `python3 scripts/build.py --check` 通过。
7. 独立选择需探测的 ID；探测仅用于协议验证。不把结构检查或未携带凭据的认证拒绝标为业务通过。
8. PR 说明来源、数量变化、脱敏处理、适配范围及实际验证。项目代码的 MIT 不自动赋予第三方资料或服务的再分发权利。

更新需要主动处理被移除的生成记录；构建器会拒绝遗留条目，避免它们继续出现在公开树中。
