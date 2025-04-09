from stream_filter import StreamFilter, MatchStatus

def test_partial_match_rollback():
    """测试部分匹配后不匹配的情况"""
    filter_config = [
        {"pattern": "<think>", "ignore_after": False}
    ]
    filter = StreamFilter(filter_config)
    
    # 测试一：常规部分匹配后不匹配
    print("=== 测试一：常规部分匹配后不匹配 ===")
    
    # 部分匹配
    chunk = "文本<th"
    output, intercepted, status = filter.add(chunk)
    print(f"输入: '{chunk}'")
    print(f"输出: '{output}'")
    print(f"是否拦截: {intercepted}")
    print(f"匹配状态: {status}")
    print("")
    
    # 完全不匹配的继续
    chunk = "at>完全不同的模式"
    output, intercepted, status = filter.add(chunk)
    print(f"输入: '{chunk}'")
    print(f"输出: '{output}'")
    print(f"是否拦截: {intercepted}")
    print(f"匹配状态: {status}")
    print("\n")
    
    # 测试二：示例3的情况
    print("=== 测试二：示例3的情况 ===")
    filter.reset()
    
    # 部分匹配
    chunk = "正常内容<th"
    output, intercepted, status = filter.add(chunk)
    print(f"输入: '{chunk}'")
    print(f"输出: '{output}'")
    print(f"是否拦截: {intercepted}")
    print(f"匹配状态: {status}")
    print("")
    
    # 继续输入，但不匹配模式
    chunk = "is is different>这不是思考标签"
    output, intercepted, status = filter.add(chunk)
    print(f"输入: '{chunk}'")
    print(f"输出: '{output}'")
    print(f"是否拦截: {intercepted}")
    print(f"匹配状态: {status}")
    print("\n")
    
    # 测试三：多个匹配规则
    print("=== 测试三：多个匹配规则 ===")
    filter_config = [
        {"pattern": "<think>", "ignore_after": False},
        {"pattern": "</think>", "ignore_after": True},
        {"pattern": "<!--", "ignore_after": False}
    ]
    filter = StreamFilter(filter_config)
    
    # 部分匹配第一个规则
    chunk = "内容<th"
    output, intercepted, status = filter.add(chunk)
    print(f"输入: '{chunk}'")
    print(f"输出: '{output}'")
    print(f"是否拦截: {intercepted}")
    print(f"匹配状态: {status}")
    print("")
    
    # 不匹配继续，应该输出部分匹配的内容
    chunk = "is is>其他内容"
    output, intercepted, status = filter.add(chunk)
    print(f"输入: '{chunk}'")
    print(f"输出: '{output}'")
    print(f"是否拦截: {intercepted}")
    print(f"匹配状态: {status}")
    print("")
    
    # 部分匹配第三个规则
    chunk = "注释<!-"
    output, intercepted, status = filter.add(chunk)
    print(f"输入: '{chunk}'")
    print(f"输出: '{output}'")
    print(f"是否拦截: {intercepted}")
    print(f"匹配状态: {status}")
    print("")
    
    # 不匹配继续，应该输出部分匹配的内容
    chunk = "not>其他注释"
    output, intercepted, status = filter.add(chunk)
    print(f"输入: '{chunk}'")
    print(f"输出: '{output}'")
    print(f"是否拦截: {intercepted}")
    print(f"匹配状态: {status}")
    
if __name__ == "__main__":
    test_partial_match_rollback() 