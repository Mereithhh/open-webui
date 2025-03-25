import json
import html
import time
from typing import Dict, List, Any, Optional, Tuple
import re

def format_tool_call_name(name: str) -> str:
    """
    格式化工具调用名称，使其更美观
    
    Args:
        name: 原始工具名称
        
    Returns:
        格式化后的工具名称
    """
    # 将驼峰命名转换为空格分隔的单词
    formatted_name = ""
    for i, char in enumerate(name):
        if i > 0 and char.isupper() and not name[i-1].isupper():
            formatted_name += " "
        formatted_name += char
    
    # 将下划线转换为空格
    formatted_name = formatted_name.replace("_", " ")
    
    # 首字母大写
    return formatted_name.strip().title()

def format_tool_execution_time(start_time: float, end_time: Optional[float] = None) -> str:
    """
    格式化工具执行时间
    
    Args:
        start_time: 开始时间戳
        end_time: 结束时间戳，如果为None则使用当前时间
        
    Returns:
        格式化后的执行时间字符串
    """
    if end_time is None:
        end_time = time.time()
    
    duration = end_time - start_time
    
    if duration < 0.1:
        return "瞬间"
    elif duration < 1:
        return f"{int(duration * 1000)}毫秒"
    elif duration < 60:
        return f"{duration:.1f}秒"
    elif duration < 3600:
        minutes = int(duration // 60)
        seconds = int(duration % 60)
        return f"{minutes}分{seconds}秒"
    else:
        hours = int(duration // 3600)
        minutes = int((duration % 3600) // 60)
        return f"{hours}小时{minutes}分钟"

def get_tool_status_emoji(status: str) -> str:
    """
    根据工具执行状态获取对应的表情符号
    
    Args:
        status: 执行状态
        
    Returns:
        状态对应的表情符号
    """
    status_map = {
        "executing": "⚙️",  # 执行中
        "success": "✅",     # 成功
        "error": "❌",       # 错误
        "waiting": "⏳",     # 等待中
    }
    return status_map.get(status, "🔄")

def is_url(text: str) -> bool:
    """
    检查文本是否为URL
    
    Args:
        text: 要检查的文本
        
    Returns:
        是否为URL
    """
    url_pattern = re.compile(
        r'^(https?:\/\/)?' # http:// or https://
        r'(([a-z\d]([a-z\d-]*[a-z\d])*)\.)+[a-z]{2,}|' # domain name
        r'((\d{1,3}\.){3}\d{1,3})' # OR ip (v4) address
        r'(\:\d+)?(\/[-a-z\d%_.~+]*)*' # port and path
        r'(\?[;&a-z\d%_.~+=-]*)?' # query string
        r'(\#[-a-z\d_]*)?$', # fragment locator
        re.IGNORECASE
    )
    return bool(url_pattern.match(text))

def format_tool_result(result: str) -> str:
    """
    格式化工具执行结果，使其更易读
    
    Args:
        result: 原始结果字符串
        
    Returns:
        格式化后的结果
    """
    # 首先检查是否为空字符串
    if not result:
        return "操作成功完成（无返回内容）"
    
    # 检查是否为URL
    if is_url(result):
        # 如果是图片URL，显示为图片
        if any(ext in result.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
            return f"![图片]({result})"
        # 普通URL，添加链接
        return f"[{result.split('/')[-1] or '链接'}]({result})"
    
    # 尝试解析JSON
    try:
        json_result = json.loads(result)
        if isinstance(json_result, dict) or isinstance(json_result, list):
            # 以代码块形式展示JSON数据，但不添加额外的缩进
            # 在引用块中会自动处理
            return f"```json\n{json.dumps(json_result, ensure_ascii=False, indent=2)}\n```"
    except:
        pass
    
    # 处理可能包含HTML的内容
    if '<html' in result.lower() or '<body' in result.lower():
        return f"```html\n{result[:500]}...\n```\n*（返回了HTML内容，已截断显示）*"
    
    # 检查是否为长文本
    # if len(result) > 1000:
    #     # 对长文本进行截断
    #     return f"```\n{result[:1000]}...\n```\n*（结果较长，已截断显示）*"
    
    # 如果不是JSON或解析失败，处理普通文本
    lines = result.split("\n")
    if len(lines) > 1:
        # 对多行文本使用代码块
        return f"```\n{result}\n```"
    
    return result

def generate_tool_call_display(
    tool_call: Dict[str, Any], 
    result: Optional[Dict[str, Any]] = None,
    is_raw: bool = False
) -> str:
    """
    生成单个工具调用的显示内容
    
    Args:
        tool_call: 工具调用信息
        result: 工具调用结果
        is_raw: 是否使用原始格式
        
    Returns:
        格式化后的显示内容
    """
    function_info = tool_call.get("function", {})
    tool_name = function_info.get("name", "未知工具")
    formatted_name = format_tool_call_name(tool_name)
    
    # 获取参数
    arguments_str = function_info.get("arguments", "{}")
    try:
        arguments = json.loads(arguments_str)
        # 简化参数为代码块展示
        if isinstance(arguments, dict) and arguments:
            arguments_display = json.dumps(arguments, ensure_ascii=False, indent=2)
        else:
            arguments_display = "无参数"
    except:
        arguments_display = arguments_str
    
    if result:
        # 已完成的工具调用
        result_content = result.get("content", "")
        
        # 检查是否是错误结果
        is_error = False
        if result.get("success") is False or "error" in result_content.lower() or "调用失败" in result_content:
            is_error = True
        
        # 简化结果展示
        if is_raw:
            return f"工具调用: {tool_name}\n参数: {arguments_str}\n结果: {result_content}"
        
        # 格式化结果内容
        formatted_result = format_tool_result(result_content).strip()
        
        # 构建引用块内容
        content = f"> **{formatted_name}**" + (" (失败)" if is_error else "") + "\n>\n"
        content += f"> **参数**:\n"
        
        # 添加参数内容到引用块
        if arguments_display == "无参数":
            content += f"> 无参数\n"
        else:
            content += f"> ```json\n"
            for line in arguments_display.splitlines():
                content += f"> {line}\n"
            content += f"> ```\n"
        
        content += ">\n"
        content += f"> **{('错误信息' if is_error else '结果')}**:\n"
        
        # 检查结果是否已经包含代码块格式
        if formatted_result.startswith("```") and formatted_result.endswith("```"):
            # 已经是代码块，需要正确处理在引用内
            lines = formatted_result.splitlines()
            content += f"> {lines[0]}\n"  # 添加代码块开始标记（包括语言）
            for line in lines[1:-1]:  # 跳过开始和结束的```
                content += f"> {line}\n"
            content += f"> {lines[-1]}"  # 添加代码块结束标记
        else:
            # 普通文本，直接添加
            for line in formatted_result.splitlines():
                content += f"> {line}\n"
        
        return content
    else:
        # 进行中的工具调用
        if is_raw:
            return f"工具调用: {tool_name}\n参数: {arguments_str}"
        
        # 构建引用块内容
        content = f"> **{formatted_name}**\n>\n"
        content += f"> **参数**:\n"
        
        # 添加参数内容到引用块
        if arguments_display == "无参数":
            content += f"> 无参数\n"
        else:
            content += f"> ```json\n"
            for line in arguments_display.splitlines():
                content += f"> {line}\n"
            content += f"> ```\n"
        
        content += ">\n"
        content += f"> **状态**: 执行中...\n"
        
        return content

def format_mcp_tool_calls(
    block_content: List[Dict[str, Any]], 
    results: Optional[List[Dict[str, Any]]] = None,
    is_raw: bool = False
) -> Tuple[str, Dict[str, Any]]:
    """
    格式化MCP工具调用区块，生成美观的显示内容和元数据
    
    Args:
        block_content: 工具调用内容
        results: 工具调用结果
        is_raw: 是否使用原始格式
        
    Returns:
        元组，包含格式化后的显示内容和元数据
    """
    if not block_content:
        return "", {}
    
    tool_displays = []
    metadata = {
        "type": "mcp_tool_calls",
        "execution_status": "complete" if results else "executing",
        "tool_count": len(block_content),
        "start_time": time.time(),
    }
    
    # 结果映射，用于快速查找
    result_map = {}
    if results:
        for result in results:
            result_map[result.get("tool_call_id", "")] = result
    
    # 处理每个工具调用
    for i, tool_call in enumerate(block_content):
        tool_call_id = tool_call.get("id", "")
        result = result_map.get(tool_call_id) if results else None
        
        tool_display = generate_tool_call_display(tool_call, result, is_raw)
        tool_displays.append(tool_display)
    
    # 生成最终显示内容
    if is_raw:
        return "\n\n".join(tool_displays), metadata
    
    # 计算工具执行总结信息（用于元数据，不用于显示）
    if results:
        metadata["end_time"] = time.time()
        metadata["duration"] = metadata["end_time"] - metadata["start_time"]
    
    # 拼接工具调用显示内容 - 引用块已经处理了格式，直接连接即可
    display_content = "\n".join(tool_displays)
    
    return display_content, metadata

def serialize_mcp_tool_calls(
    block: Dict[str, Any], 
    is_raw: bool = False
) -> str:
    """
    序列化MCP工具调用区块为展示内容
    
    Args:
        block: 工具调用区块
        is_raw: 是否使用原始格式
        
    Returns:
        序列化后的内容
    """
    block_content = block.get("content", [])
    results = block.get("results", [])
    
    # 获取时间戳
    started_at = block.get("started_at", time.time())
    ended_at = block.get("ended_at")
    
    # 获取格式化内容和元数据
    content, metadata = format_mcp_tool_calls(block_content, results, is_raw)
    
    if is_raw:
        return content
    
    # 检查是否有错误
    has_error = False
    if results:
        for result in results:
            if result.get("success") is False or "error" in result.get("content", "").lower() or "调用失败" in result.get("content", ""):
                has_error = True
                break
    
    # 创建摘要信息
    tool_count = len(block_content)
    if results:
        if ended_at and started_at:
            duration = format_tool_execution_time(started_at, ended_at)
            if has_error:
                summary = f"MCP工具执行完成 - {tool_count}个工具，耗时{duration}，有错误"
            else:
                summary = f"MCP工具执行完成 - {tool_count}个工具，耗时{duration}"
        else:
            if has_error:
                summary = f"MCP工具执行完成 - {tool_count}个工具，有错误"
            else:
                summary = f"MCP工具执行完成 - {tool_count}个工具"
    else:
        summary = f"MCP工具执行中... - {tool_count}个工具"
    
    # 使用简单的CSS类
    class_name = "mcp-tool-calls"
    
    if results:
        return f'''<details type="tool_calls" class="{class_name}" done="true" content="{html.escape(json.dumps(block_content))}" results="{html.escape(json.dumps(results))}">
<summary>{summary}</summary>
{content}
</details>
'''
    else:
        return f'''<details type="tool_calls" class="{class_name}" done="false" content="{html.escape(json.dumps(block_content))}">
<summary>{summary}</summary>
{content}
</details>
''' 