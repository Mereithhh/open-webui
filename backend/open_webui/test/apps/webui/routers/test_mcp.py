import json
import pytest
import yaml
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from open_webui.main import app
from open_webui.mcp.config_loader import MCPConfig, MCPServerConfig

# 测试客户端
client = TestClient(app)

# 模拟管理员用户
@pytest.fixture
def mock_admin_user():
    with patch('open_webui.utils.auth.get_admin_user') as mock:
        mock.return_value = MagicMock(id="admin_id", role="admin")
        yield mock

# 模拟MCP配置
@pytest.fixture
def mock_mcp_config():
    config = MCPConfig()
    config.mcpServers = {
        "test-server": MCPServerConfig(
            id="test-server",
            displayName="Test Server",
            description="A test server",
            enabled=True,
            url="http://test-server:8000"
        ),
        "test-server-2": MCPServerConfig(
            id="test-server-2",
            displayName="Test Server 2",
            description="Another test server",
            enabled=False,
            command="test-command",
            args=["--arg1", "--arg2"]
        )
    }
    
    with patch('open_webui.main.app.state.MCP_CONFIG', config):
        yield config

# 测试获取MCP配置
def test_get_mcp_config(mock_admin_user, mock_mcp_config):
    response = client.get("/api/v1/mcp/config")
    assert response.status_code == 200
    
    data = response.json()
    assert "config" in data
    assert "yaml" in data
    assert "config_file" in data
    
    # 验证配置内容
    assert "mcpServers" in data["config"]
    assert len(data["config"]["mcpServers"]) == 2
    assert "test-server" in data["config"]["mcpServers"]
    assert "test-server-2" in data["config"]["mcpServers"]

# 测试获取所有MCP服务器
def test_get_mcp_servers(mock_admin_user, mock_mcp_config):
    response = client.get("/api/v1/mcp/servers")
    assert response.status_code == 200
    
    data = response.json()
    assert "servers" in data
    assert len(data["servers"]) == 2
    assert "test-server" in data["servers"]
    assert "test-server-2" in data["servers"]
    
    # 验证服务器内容
    assert data["servers"]["test-server"]["displayName"] == "Test Server"
    assert data["servers"]["test-server"]["enabled"] == True
    assert data["servers"]["test-server-2"]["enabled"] == False

# 测试获取单个MCP服务器
def test_get_mcp_server(mock_admin_user, mock_mcp_config):
    response = client.get("/api/v1/mcp/servers/test-server")
    assert response.status_code == 200
    
    data = response.json()
    assert "server" in data
    assert data["server"]["id"] == "test-server"
    assert data["server"]["displayName"] == "Test Server"
    assert data["server"]["enabled"] == True

# 测试获取不存在的MCP服务器
def test_get_nonexistent_mcp_server(mock_admin_user, mock_mcp_config):
    response = client.get("/api/v1/mcp/servers/nonexistent-server")
    assert response.status_code == 404

# 测试添加新的MCP服务器
@patch('open_webui.mcp.config_loader.MCPConfig.save_to_file')
def test_add_mcp_server(mock_save, mock_admin_user, mock_mcp_config):
    mock_save.return_value = None
    
    new_server = {
        "id": "new-server",
        "displayName": "New Server",
        "description": "A new test server",
        "enabled": True,
        "url": "http://new-server:8000"
    }
    
    response = client.post(
        "/api/v1/mcp/servers",
        json={
            "server_id": "new-server",
            "server_config": new_server
        }
    )
    
    assert response.status_code == 200
    assert mock_save.called
    
    data = response.json()
    assert "server" in data
    assert data["server"]["id"] == "new-server"
    
    # 验证服务器已添加到配置中
    assert "new-server" in mock_mcp_config.mcpServers
    assert mock_mcp_config.mcpServers["new-server"].displayName == "New Server"

# 测试删除MCP服务器
@patch('open_webui.mcp.config_loader.MCPConfig.save_to_file')
def test_delete_mcp_server(mock_save, mock_admin_user, mock_mcp_config):
    mock_save.return_value = None
    
    response = client.delete("/api/v1/mcp/servers/test-server")
    
    assert response.status_code == 200
    assert mock_save.called
    
    data = response.json()
    assert data["success"] == True
    
    # 验证服务器已从配置中删除
    assert "test-server" not in mock_mcp_config.mcpServers

# 测试删除不存在的MCP服务器
def test_delete_nonexistent_mcp_server(mock_admin_user, mock_mcp_config):
    response = client.delete("/api/v1/mcp/servers/nonexistent-server")
    assert response.status_code == 404

# 测试更新MCP配置
@patch('open_webui.mcp.config_loader.MCPConfig.save_to_file')
def test_update_mcp_config(mock_save, mock_admin_user, mock_mcp_config):
    mock_save.return_value = None
    
    # 创建新的配置YAML
    new_config = {
        "mcpServers": {
            "updated-server": {
                "id": "updated-server",
                "displayName": "Updated Server",
                "description": "An updated test server",
                "enabled": True,
                "url": "http://updated-server:8000"
            }
        }
    }
    
    response = client.post(
        "/api/v1/mcp/config",
        json={
            "config_yaml": yaml.dump(new_config)
        }
    )
    
    assert response.status_code == 200
    assert mock_save.called
    
    data = response.json()
    assert "config" in data
    assert "yaml" in data
    
    # 验证配置已更新
    assert "mcpServers" in data["config"]
    assert len(data["config"]["mcpServers"]) == 1
    assert "updated-server" in data["config"]["mcpServers"]

# 测试重新加载MCP配置
@patch('open_webui.mcp.config_loader.load_mcp_config')
def test_reload_mcp_config(mock_load, mock_admin_user, mock_mcp_config):
    # 创建新的配置
    new_config = MCPConfig()
    new_config.mcpServers = {
        "reloaded-server": MCPServerConfig(
            id="reloaded-server",
            displayName="Reloaded Server",
            description="A reloaded test server",
            enabled=True,
            url="http://reloaded-server:8000"
        )
    }
    
    mock_load.return_value = new_config
    
    response = client.post("/api/v1/mcp/reload")
    
    assert response.status_code == 200
    assert mock_load.called
    
    data = response.json()
    assert "config" in data
    
    # 验证配置已重新加载
    assert "mcpServers" in data["config"]
    assert len(data["config"]["mcpServers"]) == 1
    assert "reloaded-server" in data["config"]["mcpServers"] 