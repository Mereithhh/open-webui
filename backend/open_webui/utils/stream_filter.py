from enum import Enum
from typing import List, Tuple, Optional, Dict


class MatchStatus(Enum):
    """匹配状态枚举"""
    NO_MATCH = 0        # 无匹配
    PARTIAL_MATCH = 1   # 部分匹配
    FULL_MATCH = 2      # 完全匹配
    IGNORED_AFTER = 3   # 忽略后续内容


class FilterConfig:
    """过滤器配置"""
    def __init__(self, pattern: str, ignore_after: bool = False):
        self.pattern = pattern
        self.ignore_after = ignore_after


class StreamFilter:
    """流式字符串过滤器"""
    
    def __init__(self, configs: List[Dict]):
        """
        初始化过滤器
        
        Args:
            configs: 过滤配置列表，每项包含 pattern 和 ignore_after
        """
        self.filter_configs = []
        for config in configs:
            pattern = config.get("pattern", "")
            ignore_after = config.get("ignore_after", False)
            if pattern:
                self.filter_configs.append(FilterConfig(pattern, ignore_after))
        
        self.buffer = ""
        self.current_matches = {i: 0 for i in range(len(self.filter_configs))}
        self.ignore_remaining = False
    
    def add(self, chunk: str) -> Tuple[str, bool, MatchStatus]:
        """
        添加新的字符串片段
        
        Args:
            chunk: 新添加的字符串片段
        
        Returns:
            Tuple[str, bool, MatchStatus]: 
                - 可以输出的字符串
                - 当前chunk是否被拦截
                - 匹配状态
        """
        if self.ignore_remaining:
            return "", True, MatchStatus.IGNORED_AFTER
        
        self.buffer += chunk
        intercepted = False
        match_status = MatchStatus.NO_MATCH
        output = ""
        
        # 处理缓冲区
        pos = 0
        while pos < len(self.buffer):
            current_match_status = MatchStatus.NO_MATCH
            matched_config_idx = -1
            
            # 检查每个过滤规则
            for config_idx, config in enumerate(self.filter_configs):
                pattern = config.pattern
                match_length = self.current_matches[config_idx]
                
                # 检查当前字符是否继续匹配
                if pos < len(self.buffer) and match_length < len(pattern) and self.buffer[pos] == pattern[match_length]:
                    self.current_matches[config_idx] += 1
                    
                    # 完全匹配
                    if self.current_matches[config_idx] == len(pattern):
                        current_match_status = MatchStatus.FULL_MATCH
                        matched_config_idx = config_idx
                        break
                    # 部分匹配
                    else:
                        current_match_status = MatchStatus.PARTIAL_MATCH
                        matched_config_idx = config_idx
                else:
                    # 匹配失败，但先不要重置状态
                    pass
            
            # 根据匹配状态决定如何处理
            if current_match_status == MatchStatus.FULL_MATCH:
                # 完全匹配，检查是否需要忽略后续内容
                if self.filter_configs[matched_config_idx].ignore_after:
                    self.ignore_remaining = True
                    match_status = MatchStatus.IGNORED_AFTER
                else:
                    match_status = MatchStatus.FULL_MATCH
                
                # 重置所有匹配状态
                self.current_matches = {i: 0 for i in range(len(self.filter_configs))}
                pos += 1
                intercepted = True
            elif current_match_status == MatchStatus.PARTIAL_MATCH:
                # 部分匹配，继续处理下一个字符
                match_status = MatchStatus.PARTIAL_MATCH
                pos += 1
                intercepted = True
            else:
                # 无匹配，检查是否有之前部分匹配但现在不匹配的情况
                if any(count > 0 for count in self.current_matches.values()):
                    # 找出匹配最长的模式
                    best_match_idx = max(self.current_matches, key=lambda k: self.current_matches[k])
                    best_match_len = self.current_matches[best_match_idx]
                    
                    if best_match_len > 0:
                        # 只输出匹配最长的模式
                        pattern = self.filter_configs[best_match_idx].pattern
                        output += pattern[:best_match_len]
                        match_status = MatchStatus.NO_MATCH
                        intercepted = False
                        
                        # 重置所有匹配状态
                        self.current_matches = {i: 0 for i in range(len(self.filter_configs))}
                
                # 将当前字符添加到输出
                output += self.buffer[pos]
                pos += 1
        
        # 清空缓冲区
        self.buffer = ""
        
        return output, intercepted, match_status
    
    def flush(self) -> str:
        """
        刷新并返回缓冲区中的所有内容
        
        Returns:
            str: 缓冲区内容
        """
        if self.ignore_remaining:
            self.buffer = ""
            return ""
        
        # 检查是否有部分匹配的内容需要输出
        output = ""
        if any(count > 0 for count in self.current_matches.values()):
            # 找出匹配最长的模式
            best_match_idx = max(self.current_matches, key=lambda k: self.current_matches[k])
            best_match_len = self.current_matches[best_match_idx]
            
            if best_match_len > 0:
                # 只输出匹配最长的模式
                pattern = self.filter_configs[best_match_idx].pattern
                output += pattern[:best_match_len]
                
                # 重置所有匹配状态
                self.current_matches = {i: 0 for i in range(len(self.filter_configs))}
        
        output += self.buffer
        self.buffer = ""
        return output
    
    def reset(self):
        """重置过滤器状态"""
        self.buffer = ""
        self.current_matches = {i: 0 for i in range(len(self.filter_configs))}
        self.ignore_remaining = False
