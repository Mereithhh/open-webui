# MCP (Model Control Protocol) 配置

本模块提供了从 YAML 文件加载 MCP 服务器配置的功能。

## 配置文件

Open WebUI 可以从配置文件中加载 MCP 服务器配置。默认情况下，配置文件的路径为 `DATA_DIR/mcp.yaml`。您可以通过设置环境变量 `MCP_CONFIG_FILE` 来指定不同的配置文件路径。

## 配置文件格式

配置文件是一个 YAML 文件，其中包含 `mcpServers` 对象，每个服务器配置都是该对象的一个属性。

示例配置：

```yaml
mcpServers:
  # 使用 STDIO 协议
  playwright-mcp:
    id: "playwright-mcp"
    displayName: "Playwright 浏览器自动化"
    description: "用于 Web 浏览器自动化的 MCP 服务器"
    enabled: true
    command: "npx"
    args: ["@executeautomation/playwright-mcp-server"]
    env:
      PLAYWRIGHT_HEADLESS: "true"
  
  # 使用 SSE 协议
  sse-server:
    id: "sse-server"
    displayName: "SSE 服务器"
    description: "通过 SSE 连接的 MCP 服务器"
    enabled: true
    url: "http://localhost:3000/sse"
```

## 配置参数

每个 MCP 服务器配置可以包含以下参数：

- `id`: 服务器的唯一标识符（必需）
- `displayName`: 用于显示的服务器名称
- `description`: 服务器描述
- `enabled`: 是否启用此服务器（默认为 true）

对于 SSE 协议，还需要：
- `url`: 服务器的 SSE URL

对于 STDIO 协议，还需要：
- `command`: 要执行的命令
- `args`: 命令行参数列表
- `env`: 环境变量字典

## 使用方法

```python
from open_webui.mcp import load_mcp_config, get_mcp_server_config, get_all_mcp_servers

# 加载所有 MCP 配置
mcp_config = load_mcp_config()

# 获取特定 MCP 服务器的配置
playwright_config = get_mcp_server_config("playwright-mcp")

# 获取所有已启用的 MCP 服务器配置
enabled_servers = get_all_mcp_servers()

# 检查 MCP 服务器是否已启用
from open_webui.mcp import is_mcp_server_enabled
is_enabled = is_mcp_server_enabled("playwright-mcp")
```

## 示例文件

请参考 `example.yaml` 获取完整的配置示例。 