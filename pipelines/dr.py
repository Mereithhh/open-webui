"""
title: Deep Research Pipeline
author: Claude
description: 在 Open WebUI 中展示 deep-research 模型的思维链和引用
version: 1.0.0
licence: MIT
"""

import json
import httpx
import re
import html
from typing import AsyncGenerator, Callable, Awaitable, Dict, Any, List, Optional
from pydantic import BaseModel, Field
import asyncio
import time  # Added
import uuid  # Added


class Pipe:
    class Valves(BaseModel):
        API_BASE_URL: str = Field(
            default="http://10.51.30.249:8080/v1",
            description="Deep Research API的基础请求地址"
        )
        API_KEY: str = Field(
            default="tLJURLIcLm3OvU7xgG2T85ZgMvVuOWoWtaxa3uKMNEU0lAUkBRo6Y7PXymcGi9ha",
            description="用于身份验证的API密钥"
        )
        MODEL_NAME: str = Field(
            default="deep-research",
            description="API请求的模型名称"
        )

    def __init__(self):
        self.valves = self.Valves()
        self.data_prefix = "data:"
        self.emitter = None
        self.citations = []
        self.blocks = []
        self.current_acc_content = ""
        self.thinking_mode = False
        self.request_id = ""

    def pipes(self):
        return [
            {
                "id": self.valves.MODEL_NAME,
                "name": self.valves.MODEL_NAME,
            }
        ]

    def _format_openai_chunk(
        self,
        content: Optional[str] = None,
        role: Optional[str] = None,
        finish_reason: Optional[str] = None,
    ) -> str:
        """Formats a chunk into the OpenAI SSE format."""
        # Ensure request_id is set before calling this
        # Fallback if request_id was somehow not initialized
        req_id = self.request_id if hasattr(self, 'request_id') and self.request_id else f"chatcmpl-fallback-{uuid.uuid4()}"
        chunk = {
            "id": req_id,
            "object": "chat.completion.chunk",
            "created": int(time.time()),
            "model": self.valves.MODEL_NAME, # Access model name
            "choices": [
                {
                    "index": 0,
                    "delta": {},
                    "finish_reason": finish_reason,
                }
            ],
            # Usage is typically in the *last* chunk in OpenAI spec, omit here.
        }
        delta = chunk["choices"][0]["delta"]
        if role:
            delta["role"] = role
        if content is not None:
            delta["content"] = content

        # Avoid yielding empty delta unless it's the final chunk with a finish_reason
        if not delta and not finish_reason:
             print("Warning: Attempted to yield an empty OpenAI chunk delta.")
             # Return empty string instead of invalid SSE
             return ""

        # SSE format requires 'data: ' prefix and double newline suffix
        # Ensure json.dumps handles potential unicode correctly
        return f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"

    async def pipe(
        self, body: dict, __event_emitter__: Callable[[dict], Awaitable[None]] = None
    ) -> AsyncGenerator[str, None]:
        """处理 deep-research 模型的流式响应并格式化为 OpenAI SSE"""
        self.emitter = __event_emitter__
        self.citations = []    # 重置引用列表
        self.current_acc_content = "" # Reset accumulated content for this request
        self.thinking_mode = False # Reset thinking mode flag
        # Generate a default request ID, may be overwritten by the first response chunk
        self.request_id = f"chatcmpl-{uuid.uuid4()}"
        first_chunk = True # Flag to add "role: assistant" to the first content chunk

        # 验证配置
        if not self.valves.API_KEY:
            # Yield error in simple JSON format, Open WebUI should handle this
            yield json.dumps({"error": "未配置API密钥"}, ensure_ascii=False) + "\n\n"
            return

        # 准备请求参数
        headers = {
            "Authorization": f"Bearer {self.valves.API_KEY}",
            "Content-Type": "application/json",
        }

        try:
            # 使用模型的原始ID
            payload = {
                "model": self.valves.MODEL_NAME,
                "messages": body.get("messages", []),
                "stream": True,
                "max_tokens": body.get("max_tokens", 1024)
            }

            # 保留其他参数
            for key in ["temperature", "top_p", "frequency_penalty", "presence_penalty"]:
                if key in body:
                    payload[key] = body[key]

            async with httpx.AsyncClient(timeout=300) as client:
                async with client.stream(
                    "POST",
                    f"{self.valves.API_BASE_URL}/chat/completions",
                    json=payload,
                    headers=headers,
                ) as response:
                    # 错误处理
                    if response.status_code != 200:
                        error_text = await response.aread()
                        # Use the original _format_error for HTTP errors
                        yield self._format_error(response.status_code, error_text) + "\n\n"
                        return

                    # 流式处理响应
                    async for line in response.aiter_lines():
                        if not line.startswith(self.data_prefix):
                            continue

                        # 截取JSON字符串
                        json_str = line[len(self.data_prefix):].strip()

                        # 检查是否为结束标记
                        if json_str == "[DONE]":
                            # 确保思考标签已关闭
                            if self.thinking_mode:
                                yield self._format_openai_chunk(content="\n</think>\n\n")
                                self.thinking_mode = False # Ensure state is updated

                            # 添加累积的引用部分（如果有）
                            if self.citations:
                                citations_html = self._format_citations()
                                # Yield citations as a final content chunk before stop
                                yield self._format_openai_chunk(content=f"\n\n{citations_html}\n")
                                self.citations = [] # Clear citations after yielding

                            # 发送最终的停止信号块
                            yield self._format_openai_chunk(finish_reason="stop")
                            return

                        try:
                            data = json.loads(json_str)
                            # 尝试从第一个有效的消息块中获取真实的 request_id
                            # Use hasattr check for safety
                            current_req_id = self.request_id if hasattr(self, 'request_id') else None
                            if current_req_id and current_req_id.startswith("chatcmpl-") and data.get("message", {}).get("request_id"):
                                self.request_id = data["message"]["request_id"]
                        except json.JSONDecodeError:
                            print(f"WARN: JSONDecodeError for line: {line}")
                            continue # 忽略无法解析的行

                        message = data.get("message", {})
                        if not message:
                            continue

                        # 如果 request_id 仍然是默认值，再次尝试更新
                        # Use hasattr check for safety
                        current_req_id = self.request_id if hasattr(self, 'request_id') else None
                        if current_req_id and current_req_id.startswith("chatcmpl-") and message.get("request_id"):
                             self.request_id = message["request_id"]

                        content_status = message.get("status", "")
                        content_obj = message.get("content", {})
                        if not content_obj:
                            continue

                        content_type = content_obj.get("content_type", "")
                        content_chunk = content_obj.get("content", "") # 这是实际的增量内容
                        metadata = message.get("metadata", {}) # 获取元数据

                        # --- 根据内容类型处理和格式化输出 ---

                        current_role = "assistant" if first_chunk else None

                        # 处理 'think' 类型
                        if content_type == "think":
                            self.current_acc_content += content_chunk # 累积用于内部逻辑

                            # 检查累积内容的最后部分，以跳过思考过程中的中间 FC 输出
                            # 注意：这种检查依赖于 `</think>` 紧邻 FC 内容
                            # Let's simplify this check: if a chunk *contains* </think> but is not completed, skip.
                            if "</think>" in content_chunk and content_status != "completed":
                                print("检测到中间的 </think>，可能为 FC 前奏，跳过当前块的输出")
                                continue # 跳过这个增量块的 yield

                            # 处理完成的 'think' 块 (通常包含最终的 FC 调用信息)
                            if content_status == "completed":
                                # 如果仍在思考模式，先关闭标签
                                if self.thinking_mode:
                                    # Yield the part *before* </think> if it exists, then close tag
                                    pre_think_content = None
                                    if "</think>" in content_chunk:
                                         pre_think_content = content_chunk.split("</think>", 1)[0]
                                    # Avoid yielding only </think> if pre_think_content is empty
                                    if pre_think_content:
                                         yield self._format_openai_chunk(content=pre_think_content)
                                    yield self._format_openai_chunk(content="\n</think>\n\n")
                                    self.thinking_mode = False

                                # 从 *当前块* 的 content 中提取 FC 字符串 (假设 FC 信息在 </think> 之后)
                                fc_str = ""
                                if "</think>" in content_chunk:
                                    fc_str = content_chunk.split("</think>", 1)[-1].strip()
                                    # Try to parse FC structure for a cleaner display
                                    try:
                                        # Handle potential non-JSON content after </think>
                                        if fc_str.startswith('{') and fc_str.endswith('}'):
                                            fc_data = json.loads(fc_str)
                                            fc_name = fc_data.get("name", "未知函数")
                                            # Use ensure_ascii=False for args display
                                            fc_args = json.dumps(fc_data.get("arguments", {}), ensure_ascii=False, separators=(',', ':'))
                                            fc_display = f"函数调用: `{fc_name}({fc_args})`"
                                        else:
                                            # If it's not JSON, display raw (if non-empty)
                                            fc_display = f"思考后附加信息: `{fc_str}`" if fc_str else None
                                    except json.JSONDecodeError:
                                        # If JSON parsing fails, display raw (if non-empty)
                                        fc_display = f"原始函数调用信息: `{fc_str}`" if fc_str else None
                                else:
                                    # If completed think chunk has no </think>, no FC expected
                                    fc_display = None

                                print(f"思考完成。提取的 FC/附加信息：{fc_str}")

                                # Output FC call information (if extracted and non-empty)
                                if fc_display:
                                    yield self._format_openai_chunk(content=f"\n{fc_display}\n")

                                # 清理累积内容，因为此轮思考已完成
                                self.current_acc_content = ""
                                print("一轮调用结束 (think completed)，清理 acc_content")
                                continue # 处理下一行

                            # 处理常规的 'think' 增量内容 (not completed)
                            else:
                                # If not yet in thinking mode, output start tag
                                if not self.thinking_mode:
                                    self.thinking_mode = True
                                    # Pass role only on the very first chunk of the response
                                    yield self._format_openai_chunk(content="<think>\n", role=current_role)
                                    if first_chunk: first_chunk = False
                                    # After the first chunk, current_role will be None
                                # Yield the current thinking content chunk
                                # We already skipped chunks with intermediate </think>
                                # Pass role=None because it's handled above
                                yield self._format_openai_chunk(content=content_chunk)
                                # No need to set first_chunk=False here again

                        # 处理 'text' 类型 (最终用户可见的回复)
                        elif content_type == "text":
                            # If previously in thinking mode, end it first
                            if self.thinking_mode:
                                yield self._format_openai_chunk(content="\n</think>\n\n")
                                self.thinking_mode = False

                            # Output the text content chunk
                            # Pass role only on the very first chunk of the response
                            yield self._format_openai_chunk(content=content_chunk, role=current_role)
                            if first_chunk: first_chunk = False

                            # Handle completed 'text' block (check for citations)
                            if content_status == "completed":
                                if metadata:
                                    citations = metadata.get("citations", [])
                                    if citations:
                                        self._collect_citations(citations)
                                        # Citations are accumulated and yielded at the end ([DONE])

                                # Clear accumulated content (though not used for text)
                                self.current_acc_content = ""
                                print("一轮调用结束 (text completed)，清理 acc_content")
                                # Usage info comes from the API response if needed, not handled per chunk here

                        # 处理 'browser_result' 类型 (mainly for citations)
                        elif content_type == "browser_result":
                            # End thinking mode if active (less common for this type)
                            if self.thinking_mode:
                                yield self._format_openai_chunk(content="\n</think>\n\n")
                                self.thinking_mode = False

                            if metadata:
                                # Key is 'metadata_list' based on original code comment
                                citations = metadata.get("metadata_list", [])
                                if citations:
                                    print("处理浏览器结果中的引用")
                                    self._collect_citations(citations)
                                    # Citations accumulated, yielded at [DONE]

                            # Clear accumulated content if this signifies an end step
                            if content_status == "completed":
                                self.current_acc_content = ""
                                print("一轮调用结束 (browser_result completed)，清理 acc_content")

                        # Add handling or logging for other content_types if necessary
                        # else:
                        #    print(f"未处理的 content_type: {content_type}")

        except Exception as e:
            # Format exception and send as a simple error JSON
            error_detail_str = self._format_exception(e) # Gets JSON string
            try:
                # Try to extract just the error message
                error_msg = json.loads(error_detail_str).get("error", str(e))
            except:
                error_msg = str(e) # Fallback to raw exception string

            # Yield simple error JSON (ensure final newline for SSE)
            yield json.dumps({"error": f"Pipeline 处理异常: {error_msg}"}, ensure_ascii=False) + "\n\n"

    def _collect_citations(self, citations: List[Dict[str, Any]]) -> None:
        """收集引用信息 (保持不变)"""
        for citation in citations:
            # Simple deduplication based on URL
            # Check if citation dict itself is already present for simplicity
            # This assumes citation dicts are consistent if URL is the same
            if citation not in self.citations:
                # More robust check based on URL if metadata structure is consistent
                # existing_urls = {c.get("metadata", {}).get("url") for c in self.citations if c.get("metadata")}
                # current_url = citation.get("metadata", {}).get("url")
                # if not current_url or current_url not in existing_urls:
                 self.citations.append(citation)

    def _format_citations(self) -> str:
        """格式化引用信息为HTML (保持不变)"""
        if not self.citations:
            return ""
            
        html_output = "<details type=\"source_documents\">\n<summary>参考资料</summary>\n"
        
        for i, citation in enumerate(self.citations, 1):
            metadata = citation.get("metadata", {})
            if not metadata:
                continue
                
            title = metadata.get("title", "未知标题")
            url = metadata.get("url", "#")
            text = metadata.get("text", "")
            
            # 简化文本内容（截取前200个字符）
            text_preview = text[:200] + "..." if len(text) > 200 else text
            
            html_output += f"<div class=\"source-document\">\n"
            html_output += f"<h3>{i}. <a href=\"{url}\" target=\"_blank\">{html.escape(title)}</a></h3>\n"
            html_output += f"<blockquote>{html.escape(text_preview)}</blockquote>\n"
            html_output += f"</div>\n"
            
        html_output += "</details>"
        return html_output

    def _format_error(self, status_code: int, error: bytes) -> str:
        """格式化错误响应 (保持不变, 返回简单 JSON 字符串)"""
        if isinstance(error, str):
            error_str = error
        else:
            # Use 'ignore' or 'replace' for robustness
            error_str = error.decode(errors="ignore")
        try:
            # Limit error message length
            err_msg = json.loads(error_str).get("message", error_str)[:200]
        except Exception:
            err_msg = error_str[:200]
        # Return simple error JSON string (calling code adds \n\n)
        return json.dumps(
            {"error": f"HTTP {status_code}: {err_msg}"}, ensure_ascii=False
        )

    def _format_exception(self, e: Exception) -> str:
        """格式化异常 (保持不变, 返回简单 JSON 字符串)"""
        err_type = type(e).__name__
        # Return simple error JSON string (calling code adds \n\n)
        return json.dumps({"error": f"{err_type}: {str(e)}"}, ensure_ascii=False)