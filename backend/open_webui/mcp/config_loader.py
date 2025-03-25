import os
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Union

import yaml
from pydantic import BaseModel, Field

from open_webui.env import MCP_CONFIG_FILE

log = logging.getLogger(__name__)


class MCPServerConfig(BaseModel):
    """MCP 服务器配置模型"""
    id: str = Field(..., description="MCP 服务器的唯一标识符")
    displayName: Optional[str] = Field(None, description="用于显示的服务器名称")
    description: Optional[str] = Field(None, description="服务器描述")
    enabled: bool = Field(True, description="是否启用此服务器")
    
    # SSE 协议配置
    url: Optional[str] = Field(None, description="服务器 sse URL")
    
    # STDIO 协议配置
    command: Optional[str] = Field(None, description="要执行的命令")
    args: Optional[List[str]] = Field(None, description="命令行参数")
    env: Optional[Dict[str, str]] = Field(None, description="环境变量")


class MCPConfig(BaseModel):
    """完整的 MCP 配置模型"""
    mcpServers: Dict[str, MCPServerConfig] = Field(default_factory=dict, description="MCP 服务器配置")
    
    def to_app_config(self) -> dict:
        """将 MCP 配置转换为 app 配置"""
        return {
            "mcp_servers": [
                {
                    "name": server.id,
                    "description": server.description,
                }
                for server in self.mcpServers.values()
            ]
        }
    def filter_avalible_servers(self, server_ids: List[str]) -> List[MCPServerConfig]:
        """过滤已启用的 MCP 服务器"""
        l =  [server for server in self.mcpServers.values() if server.enabled]
        return [server for server in l if server.id in server_ids]
    def to_full_yaml(self) -> str:
        """将完整的 MCP 配置转换为 YAML 字符串，用于保存配置文件"""
        # 首先将模型转换为字典
        config_dict = self.model_dump(exclude_none=True)
        # 然后使用 yaml.dump 将字典转换为 YAML 字符串
        return yaml.dump(config_dict, allow_unicode=True, sort_keys=False)
    
    def save_to_file(self, file_path: Optional[str] = None) -> None:
        """将配置保存到文件
        
        参数:
            file_path: 文件路径，如果为 None 则使用默认配置文件路径
        """
        save_path = Path(file_path) if file_path else Path(MCP_CONFIG_FILE)
        yaml_content = self.to_full_yaml()
        
        try:
            # 确保目录存在
            save_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 写入文件
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(yaml_content)
                
            log.info(f"MCP 配置已保存到: {save_path}")
        except Exception as e:
            log.error(f"保存 MCP 配置失败: {str(e)}")
            raise


def load_mcp_config() -> MCPConfig:
    """
    从 YAML 文件加载 MCP 配置
    
    返回:
        MCPConfig: 包含 MCP 服务器配置的对象
    """
    log.info(f"加载 MCP 配置文件: {MCP_CONFIG_FILE}")
    config_path = Path(MCP_CONFIG_FILE)
    
    # 默认配置
    default_config = MCPConfig()
    
    if not config_path.exists():
        log.info(f"MCP 配置文件不存在: {config_path}，使用默认空配置")
        return default_config
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            yaml_config = yaml.safe_load(f)
            
        if not yaml_config:
            log.warning(f"MCP 配置文件为空: {config_path}")
            return default_config
            
        if not isinstance(yaml_config, dict) or 'mcpServers' not in yaml_config:
            log.warning(f"MCP 配置文件格式不正确: {config_path}，缺少 mcpServers 字段")
            return default_config
        
        # 解析配置
        mcp_config = MCPConfig(**yaml_config)
        log.info(f"已成功加载 MCP 配置，包含 {len(mcp_config.mcpServers)} 个服务器")
        return mcp_config
        
    except Exception as e:
        log.error(f"加载 MCP 配置文件失败: {str(e)}")
        return default_config


def get_mcp_server_config(server_id: str) -> Optional[MCPServerConfig]:
    """
    获取指定 ID 的 MCP 服务器配置
    
    参数:
        server_id: 服务器 ID
        
    返回:
        Optional[MCPServerConfig]: 服务器配置对象，如果不存在则返回 None
    """
    config = load_mcp_config()
    return config.mcpServers.get(server_id)


def get_all_mcp_servers() -> List[MCPServerConfig]:
    """
    获取所有已启用的 MCP 服务器配置
    
    返回:
        List[MCPServerConfig]: 服务器配置对象列表
    """
    config = load_mcp_config()
    return [server for server in config.mcpServers.values() if server.enabled]


def is_mcp_server_enabled(server_id: str) -> bool:
    """
    检查指定的 MCP 服务器是否已启用
    
    参数:
        server_id: 服务器 ID
        
    返回:
        bool: 如果服务器存在且已启用则返回 True
    """
    server_config = get_mcp_server_config(server_id)
    return server_config is not None and server_config.enabled

