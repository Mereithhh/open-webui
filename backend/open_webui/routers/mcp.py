import logging
import yaml
from fastapi import APIRouter, Depends, Request, HTTPException, status
from pydantic import BaseModel
from typing import Dict, Any

from open_webui.utils.auth import get_admin_user
from open_webui.mcp.config_loader import MCPConfig
from open_webui.env import MCP_CONFIG_FILE

log = logging.getLogger(__name__)

router = APIRouter()

class MCPConfigUpdateForm(BaseModel):
    """MCP 配置更新表单"""
    config_yaml: str


@router.get("/config", response_model=Dict[str, Any])
async def get_mcp_config(request: Request, user=Depends(get_admin_user)):
    """
    获取完整的 MCP 配置
    
    返回:
        Dict[str, Any]: 当前的 MCP 配置
    """
    try:
        config = request.app.state.MCP_CONFIG
        return {
            "config": config.model_dump(exclude_none=True),
            "yaml": config.to_full_yaml(),
            "config_file": str(MCP_CONFIG_FILE)
        }
    except Exception as e:
        log.error(f"获取 MCP 配置失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取 MCP 配置失败: {str(e)}",
        )

@router.post("/config", response_model=Dict[str, Any])
async def update_mcp_config(
    request: Request, 
    form_data: MCPConfigUpdateForm, 
    user=Depends(get_admin_user)
):
    """
    更新完整的 MCP 配置
    
    参数:
        form_data: 包含更新后的 YAML 配置
        
    返回:
        Dict[str, Any]: 更新后的 MCP 配置
    """
    try:
        # 解析 YAML 字符串
        yaml_config = yaml.safe_load(form_data.config_yaml)
        
        if not yaml_config:
            raise ValueError("配置为空")
            
        if not isinstance(yaml_config, dict) or 'mcpServers' not in yaml_config:
            raise ValueError("配置格式不正确，缺少 mcpServers 字段")
        
        # 创建新的配置对象
        new_config = MCPConfig(**yaml_config)
        
        # 保存到文件
        new_config.save_to_file()
        
        # 更新应用状态
        request.app.state.MCP_CONFIG = new_config
        
        log.info(f"更新 MCP 配置成功: {new_config.to_full_yaml()}")
        
        # 返回更新后的配置
        return {
            "config": new_config.model_dump(exclude_none=True),
            "yaml": new_config.to_full_yaml(),
            "config_file": str(MCP_CONFIG_FILE)
        }
    except Exception as e:
        log.error(f"更新 MCP 配置失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"更新 MCP 配置失败: {str(e)}",
        )
