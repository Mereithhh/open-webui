from stream_filter import StreamFilter, MatchStatus

def main():
    """
    演示StreamFilter的用法
    """
    print("=== 流式过滤器示例 ===")
    
    # 初始化过滤器，<think>标签不忽略后续内容，</think>标签忽略后续内容
    filter_config = [
        {"pattern": "<think>", "ignore_after": False},
        {"pattern": "</think>", "ignore_after": True}
    ]
    
    print("配置过滤器：")
    print("- 过滤 '<think>'，不忽略后续内容")
    print("- 过滤 '</think>'，忽略后续内容")
    print("\n")
    
    filter = StreamFilter(filter_config)
    
    # 示例1：部分匹配和完全匹配
    print("示例1：部分匹配和完全匹配\n")
    
    # 部分匹配
    chunk = "Hello <th"
    output, intercepted, status = filter.add(chunk)
    print(f"输入: '{chunk}'")
    print(f"输出: '{output}'")
    print(f"是否拦截: {intercepted}")
    print(f"匹配状态: {status}")
    print("\n")
    
    # 完全匹配
    chunk = "ink>这是思考内容"
    output, intercepted, status = filter.add(chunk)
    print(f"输入: '{chunk}'")
    print(f"输出: '{output}'")
    print(f"是否拦截: {intercepted}")
    print(f"匹配状态: {status}")
    print("\n")
    
    # 正常内容
    chunk = "继续思考过程..."
    output, intercepted, status = filter.add(chunk)
    print(f"输入: '{chunk}'")
    print(f"输出: '{output}'")
    print(f"是否拦截: {intercepted}")
    print(f"匹配状态: {status}")
    print("\n")
    
    # 示例2：忽略后续内容
    print("示例2：忽略后续内容\n")
    
    # 部分匹配结束标签
    chunk = "思考结束</th"
    output, intercepted, status = filter.add(chunk)
    print(f"输入: '{chunk}'")
    print(f"输出: '{output}'")
    print(f"是否拦截: {intercepted}")
    print(f"匹配状态: {status}")
    print("\n")
    
    # 完全匹配结束标签
    chunk = "ink>"
    output, intercepted, status = filter.add(chunk)
    print(f"输入: '{chunk}'")
    print(f"输出: '{output}'")
    print(f"是否拦截: {intercepted}")
    print(f"匹配状态: {status}")
    print("\n")
    
    # 尝试添加后续内容
    chunk = "这些内容应该被忽略"
    output, intercepted, status = filter.add(chunk)
    print(f"输入: '{chunk}'")
    print(f"输出: '{output}'")
    print(f"是否拦截: {intercepted}")
    print(f"匹配状态: {status}")
    print("\n")
    
    # 示例3：部分匹配后不匹配
    print("示例3：部分匹配后不匹配\n")
    
    # 重置过滤器
    filter.reset()
    print("重置过滤器")
    print("\n")
    
    # 部分匹配
    chunk = "正常内容<th"
    output, intercepted, status = filter.add(chunk)
    print(f"输入: '{chunk}'")
    print(f"输出: '{output}'")
    print(f"是否拦截: {intercepted}")
    print(f"匹配状态: {status}")
    print("\n")
    
    # 继续输入，但不匹配模式
    chunk = "is is different>这不是思考标签"
    output, intercepted, status = filter.add(chunk)
    print(f"输入: '{chunk}'")
    print(f"输出: '{output}'")
    print(f"是否拦截: {intercepted}")
    print(f"匹配状态: {status}")
    print("\n")
    
    # 添加一个更明确的例子
    print("示例4：更明确的部分匹配后不匹配\n")
    
    filter.reset()
    print("重置过滤器")
    print("\n")
    
    # 部分匹配
    chunk = "文本<th"
    output, intercepted, status = filter.add(chunk)
    print(f"输入: '{chunk}'")
    print(f"输出: '{output}'")
    print(f"是否拦截: {intercepted}")
    print(f"匹配状态: {status}")
    print("\n")
    
    # 完全不匹配的继续
    chunk = "at>完全不同的模式"
    output, intercepted, status = filter.add(chunk)
    print(f"输入: '{chunk}'")
    print(f"输出: '{output}'")
    print(f"是否拦截: {intercepted}")
    print(f"匹配状态: {status}")
    print("\n")
    
    print("=== 示例结束 ===")

if __name__ == "__main__":
    main() 