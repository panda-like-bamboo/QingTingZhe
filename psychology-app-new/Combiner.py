import os
import sys
from tqdm import tqdm

# --- 配置区 ---

# 定义允许被合并内容的文件扩展名
ALLOWED_EXTENSIONS_FOR_CONTENT = ('.py', '.vue', '.js', '.css', '.html', '.md', '.json') # 可以根据需要添加更多

# 定义需要排除（不访问、不包含在目录树和合并内容中）的目录名称列表
EXCLUDED_DIRS = ['node_modules', '.git', '__pycache__', 'dist', 'build', 'venv', '.env', '.vscode', '.idea'] # 添加了常见的排除项

# --- 函数定义 ---

def generate_tree(root_dir):
    """
    生成类似 tree /f 的目录树字符串，但会排除 EXCLUDED_DIRS 中指定的目录。
    """
    tree_output = [os.path.basename(root_dir)] # 使用 basename 获取根目录名
    
    # 使用 os.walk 遍历目录
    # topdown=True (默认) 意味着先访问父目录，再访问子目录，允许我们修改 dirs 列表来阻止访问某些子目录
    for root, dirs, files in os.walk(root_dir, topdown=True):
        # --- 核心过滤逻辑：排除指定的目录 ---
        # 使用列表推导式原地修改 dirs 列表，移除需要排除的目录
        # 这样 os.walk 就不会再进入这些被移除的目录
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]

        # 计算当前层级和缩进
        # 注意：root 包含完整路径，我们需要计算相对于 root_dir 的深度
        # 如果 root_dir 是 '.' 或相对路径，这可能需要调整，但对于绝对路径或简单子目录通常有效
        relative_path = os.path.relpath(root, root_dir)
        level = relative_path.count(os.sep) if relative_path != '.' else 0
        
        # 避免在根目录下额外缩进 basename
        if relative_path != '.':
            indent = '    ' * level
            tree_output.append(f"{indent}└── {os.path.basename(root)}") # 使用更像 tree 的前缀

        # 列出当前目录下的文件（这些文件所在的目录已经通过了 EXCLUDED_DIRS 的过滤）
        sub_indent = '    ' * (level + 1)
        for file in files:
            # 在目录树中列出所有未被排除目录下的文件
            tree_output.append(f"{sub_indent}├── {file}") # 使用更像 tree 的前缀
            
    return "\n".join(tree_output)

def calculate_total_files(root_dir):
    """
    计算需要处理的文件总数（排除了 EXCLUDED_DIRS 目录下的文件）。
    用于 TQDM 进度条。
    """
    total_files = 0
    for root, dirs, files in os.walk(root_dir, topdown=True):
        # --- 同样应用目录排除逻辑 ---
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
        
        # 只计算文件总数，不区分扩展名，因为进度条反映的是扫描进度
        total_files += len(files)
    return total_files

def concatenate_files(root_dir, output_file):
    """
    合并指定目录下符合条件的文件内容到输出文件中，并包含过滤后的目录树。
    会排除 EXCLUDED_DIRS 中指定的目录。
    """
    # --- 1. 计算需要扫描的文件总数 (已排除 EXCLUDED_DIRS) ---
    total_files = calculate_total_files(root_dir)
    print(f"排除 {', '.join(EXCLUDED_DIRS)} 后，预计扫描文件总数: {total_files}")
    
    # 可以在这里也计算一下会被合并内容的文件数（可选）
    included_files_count = 0
    files_to_include = []
    for root, dirs, files in os.walk(root_dir, topdown=True):
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
        for file in files:
             _, ext = os.path.splitext(file)
             if ext.lower() in ALLOWED_EXTENSIONS_FOR_CONTENT:
                 included_files_count += 1
                 files_to_include.append(os.path.join(root, file)) # 记录待合并的文件路径
    print(f"找到 {included_files_count} 个符合扩展名条件 ({', '.join(ALLOWED_EXTENSIONS_FOR_CONTENT)}) 的文件将被合并内容。")


    with open(output_file, 'w', encoding='utf-8') as outfile:
        # --- 2. 写入过滤后的目录树 ---
        outfile.write("项目目录结构 (已过滤部分目录):\n") # 标题明确说明是过滤后的树
        outfile.write("=================================\n")
        tree_content = generate_tree(root_dir)
        outfile.write(tree_content + "\n")
        outfile.write("=================================\n\n")
        outfile.write("合并的文件内容 (仅限指定类型):\n") # 明确说明内容是过滤后的
        outfile.write("=================================\n\n")

        # --- 3. 遍历文件并合并内容 ---
        # 使用 tqdm 显示进度条 (total 是排除目录后的文件总数)
        with tqdm(total=total_files, desc="扫描文件并合并内容", unit="个文件", bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]") as pbar:
            processed_files_count = 0 # 用于实际处理的文件计数器
            for root, dirs, files in os.walk(root_dir, topdown=True):
                # --- 核心过滤逻辑：再次排除指定的目录 ---
                # 确保在主处理循环中也应用这个过滤
                dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]

                for file in files:
                    file_path = os.path.join(root, file)
                    relative_file_path = os.path.relpath(file_path, root_dir) # 获取相对路径，更通用

                    # --- 检查文件扩展名是否允许合并 ---
                    _, ext = os.path.splitext(file)
                    if ext.lower() in ALLOWED_EXTENSIONS_FOR_CONTENT:
                        # --- 文件内容合并逻辑 ---
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as infile: # 添加 errors='ignore' 避免解码错误中断
                                content = infile.read()
                                outfile.write(f"--- 文件: {relative_file_path} ---\n") # 使用相对路径更清晰
                                outfile.write(content + "\n")
                                outfile.write(f"--- 文件结束: {relative_file_path} ---\n\n")
                            # print(f"已合并内容: {relative_file_path}") # 可以在 tqdm 中显示，减少控制台输出噪音
                            pbar.set_postfix_str(f"正在合并: {relative_file_path[-50:]}", refresh=True) # 显示当前正在处理的文件（部分）
                        except Exception as e:
                            # 记录读取或写入错误
                            outfile.write(f"--- 文件: {relative_file_path} ---\n")
                            outfile.write(f"!!! 读取或写入文件时出错: {str(e)} !!!\n")
                            outfile.write(f"--- 文件结束 (错误): {relative_file_path} ---\n\n")
                            pbar.set_postfix_str(f"合并错误: {relative_file_path[-50:]}", refresh=True)
                            # print(f"合并内容失败: {relative_file_path} - 错误: {str(e)}") # 可以在 tqdm 中显示
                    else:
                        # --- 文件类型不符，跳过内容合并 ---
                        # print(f"已跳过内容合并 (类型不符): {relative_file_path}") # 可以在 tqdm 中显示
                        pbar.set_postfix_str(f"已跳过: {relative_file_path[-50:]}", refresh=True) # 显示当前跳过的文件（部分）

                    # --- 更新进度条 ---
                    # 每个访问的文件（无论是否合并内容）都更新进度条
                    pbar.update(1)
                    processed_files_count += 1 # 增加处理计数

            # 确保进度条达到 100% (有时由于计数误差可能不到)
            if pbar.n < total_files:
                 pbar.n = total_files
                 pbar.refresh()
            # 检查处理的文件数是否与预期扫描数匹配
            if processed_files_count != total_files:
                 print(f"\n警告：扫描到的文件数 ({total_files}) 与实际处理的文件数 ({processed_files_count}) 不匹配。请检查过滤逻辑或文件系统变化。")


# --- 主程序入口 ---
if __name__ == "__main__":
    # 获取目标目录，默认为当前工作目录
    root_dir = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    # 标准化路径，确保 C:\path 和 C:\path/ 不同
    root_dir = os.path.normpath(root_dir) 
    
    # 定义输出文件名
    output_file = 'project_content_aggregator_output.txt' # 使用更具描述性的文件名

    print(f"[*] 目标扫描目录: {root_dir}")
    print(f"[*] 将要排除的目录: {', '.join(EXCLUDED_DIRS)}")
    print(f"[*] 将合并以下类型文件的内容: {', '.join(ALLOWED_EXTENSIONS_FOR_CONTENT)}")
    print(f"[*] 输出文件将保存为: {output_file}")
    
    # 执行合并操作
    try:
        concatenate_files(root_dir, output_file)
        print(f"\n[+] 处理完成。输出文件已生成: {output_file}")
    except FileNotFoundError:
        print(f"[!] 错误：指定的目录不存在: {root_dir}")
    except Exception as e:
        print(f"[!] 处理过程中发生意外错误: {str(e)}")