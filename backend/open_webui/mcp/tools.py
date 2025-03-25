import json
import logging
import asyncio
import uuid
from typing import Any, Dict, List, Optional, Tuple
from fastapi import Request
from mcp.types import CallToolResult

from open_webui.models.users import UserModel
from open_webui.socket.main import get_event_emitter

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


def convert_mcp_tool_to_openai_function(tool: Dict[str, Any]) -> Dict[str, Any]:
    """
    将 MCP 工具转换为 OpenAI 函数格式
    
    Args:
        tool: MCP 工具信息
    
    Returns:
        符合 OpenAI function calling 格式的工具定义
    """
    # 确保输入模式符合规范
    input_schema = tool["inputSchema"]
    if "type" not in input_schema:
        input_schema["type"] = "object"
    
    return {
        "type": "function",
        "function": {
            "name": tool["name"],
            "description": tool["description"],
            "parameters": input_schema
        }
    }


async def handle_mcp_tool_call(
    server: Any,
    tool_name: str,
    tool_call_id: str,
    arguments: Dict[str, Any],
    event_emitter
) -> Any:
    """
    处理 MCP 工具调用
    
    Args:
        server: MCP 服务器实例
        tool_name: 工具名称
        tool_call_id: 工具调用 ID
        arguments: 工具调用参数
        event_emitter: 事件发射器
    
    Returns:
        工具调用结果
    """
    log.info(f"执行 MCP 工具: {tool_name}, 参数: {arguments}")
    
    # 发送工具请求事件
    if event_emitter:
        await event_emitter({
            "type": "mcp:tool:request",
            "data": {
                "call_id": tool_call_id,
                "name": tool_name,
                "description": "",
                "arguments": json.dumps(arguments)
            },
        })
    
    # 执行工具调用
    try:
        result = await server.execute_tool(tool_name, arguments)
        log.info(f"MCP 工具调用结果: {result}")
        
        # 提取结果中的纯文本内容
        result_text = ""
        
        # 检查结果格式并提取文本
        if hasattr(result, "content") and isinstance(result.content, list):
            # 从 content 列表中提取文本和图片
            for item in result.content:
                if hasattr(item, "type"):
                    if item.type == "text" and hasattr(item, "text"):
                        result_text += item.text
                    elif item.type == "image" and hasattr(item, "data"):
                        # 处理图片内容
                        img_type = getattr(item, "mimeType", "image/png")
                        result_text += f"\n![图片](data:{img_type};base64,{item.data})\n"
                    elif item.type == "resource" and hasattr(item, "resource"):
                        # 处理嵌入资源
                        resource = item.resource
                        if hasattr(resource, "text"):
                            result_text += resource.text
                        elif hasattr(resource, "blob"):
                            mime_type = getattr(resource, "mimeType", "application/octet-stream")
                            if "image" in mime_type:
                                result_text += f"\n![资源图片](data:{mime_type};base64,{resource.blob})\n"
                            else:
                                result_text += f"\n[嵌入资源 ({mime_type})]({resource.uri})\n"
        elif isinstance(result, str):
            # 如果结果本身就是字符串
            result_text = result
        else:
            # 尝试转换为字符串
            try:
                result_text = str(result)
            except:
                result_text = "工具执行成功，但结果格式无法处理"
        
        # 发送工具结果事件
        if event_emitter:
            await event_emitter({
                "type": "mcp:tool:result",
                "data": {
                    "call_id": tool_call_id,
                    "result": result_text,
                    "success": True,
                    "err_message": "",
                    "code": 0
                },
            })
        
        return result_text
    except Exception as e:
        error_message = f"调用失败: {str(e)}"
        log.error(f"执行 MCP 工具出错: {error_message}")
        
        # 发送工具错误事件
        if event_emitter:
            await event_emitter({
                "type": "mcp:tool:result",
                "data": {
                    "call_id": tool_call_id,
                    "result": "",
                    "success": False,
                    "err_message": error_message,
                    "code": 1
                },
            })
        
        return error_message


async def get_mcp_tools(request: Request, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    获取 MCP 服务器中的所有工具
    
    Args:
        request: FastAPI 请求对象
        metadata: 请求元数据
    
    Returns:
        MCP 工具列表，转换为 OpenAI 函数格式
    """
    mcp_servers = metadata.get("mcp_servers", [])
    if not mcp_servers:
        return []
    
    all_tools = []
    
    for server in mcp_servers:
        try:
            tools = await server.list_tools()
            for tool in tools:
                tool_spec = convert_mcp_tool_to_openai_function({
                    "name": tool.name,
                    "description": tool.description,
                    "inputSchema": tool.input_schema
                })
                all_tools.append(tool_spec)
        except Exception as e:
            log.error(f"获取 MCP 工具列表失败: {e}")
    
    return all_tools


async def process_mcp_tools(
    request: Request, 
    form_data: Dict[str, Any], 
    user: UserModel, 
    metadata: Dict[str, Any]
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    处理 MCP 工具调用，将工具添加到请求中
    
    Args:
        request: FastAPI 请求对象
        form_data: 请求表单数据
        user: 用户对象
        metadata: 请求元数据
    
    Returns:
        处理后的表单数据和额外的元数据标志
    """
    mcp_servers = metadata.get("mcp_servers", [])
    if not mcp_servers:
        return form_data, {}
    
    # 获取所有 MCP 工具，转换为 OpenAI 格式
    tools = await get_mcp_tools(request, metadata)
    
    if not tools:
        return form_data, {}
    
    # 将 MCP 工具添加到请求中
    form_data["tools"] = tools
    
    # 如果模型原来已有工具，合并它们
    if "tools" in form_data:
        existing_tools = form_data.get("tools", [])
        if isinstance(existing_tools, list):
            form_data["tools"] = existing_tools + tools
    
    # 存储 MCP 服务器和工具到元数据中，方便后续响应处理
    metadata["mcp_enabled"] = True
    
    return form_data, {}


async def handle_mcp_response_tool_calls(
    tool_calls: List[Dict[str, Any]],
    metadata: Dict[str, Any],
    event_emitter = None
) -> List[Dict[str, Any]]:
    """
    处理响应中的 MCP 工具调用
    
    Args:
        tool_calls: 工具调用列表
        metadata: 请求元数据
        event_emitter: 事件发射器
    
    Returns:
        工具调用结果列表
    """
    if not metadata.get("mcp_enabled", False):
        return []
    
    mcp_servers = metadata.get("mcp_servers", [])
    if not mcp_servers:
        return []
    
    results = []
    log.info(f"处理 MCP 工具调用: {len(tool_calls)} 个工具")
    
    for tool_call in tool_calls:
        tool_call_id = tool_call.get("id", f"call_{uuid.uuid4()}")
        tool_name = tool_call.get("function", {}).get("name", "")
        tool_arguments_str = tool_call.get("function", {}).get("arguments", "{}")
        
        log.info(f"处理工具调用: {tool_name}, ID: {tool_call_id}")
        
        try:
            # 尝试解析参数
            tool_arguments = json.loads(tool_arguments_str)
        except json.JSONDecodeError:
            log.error(f"解析工具调用参数失败: {tool_arguments_str}")
            tool_arguments = {}
        
        # 在所有 MCP 服务器中查找并执行工具
        tool_result = None
        for server in mcp_servers:
            try:
                # 检查服务器是否有此工具
                server_tools = await server.list_tools()
                server_tool_names = [t.name for t in server_tools]
                
                if tool_name in server_tool_names:
                    log.info(f"在服务器上找到工具 {tool_name}，开始执行")
                    tool_result = await handle_mcp_tool_call(
                        server, 
                        tool_name, 
                        tool_call_id,
                        tool_arguments,
                        event_emitter
                    )
                    log.info(f"工具 {tool_name} 执行结果: {tool_result[:100]}...")
                    break
            except Exception as e:
                log.error(f"MCP 工具调用失败: {e}")
                tool_result = f"调用失败: {str(e)}"
        
        if tool_result is None:
            tool_result = f"未找到工具: {tool_name}"
            log.warning(f"未找到工具: {tool_name}")
        
        results.append({
            "tool_call_id": tool_call_id,
            "content": tool_result,
        })
    
    return results 