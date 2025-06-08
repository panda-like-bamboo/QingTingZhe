# -*- coding: utf-8 -*-
import os
import datetime

# --- 配置区域 ---
# 请根据您的需求修改以下配置

# 1. 目标文件扩展名列表 (请明确写出希望包含的扩展名，例如：['.py', '.vue', '.js', '.html', '.css', '.md'])
TARGET_EXTENSIONS = ['.py', '.vue', '.html', '.css','.js']

# 2. 输出文件名
OUTPUT_FILENAME = "collected_project_code_with_tree.txt"

# 3. 是否递归扫描子目录 (True 表示递归, False 表示仅当前目录)
RECURSIVE_SCAN = True

# 4. 要排除的目录名称列表 (这些目录及其内容将被完全忽略)
# 常见排除项：'.git', 'node_modules', '__pycache__', '.vscode', '.idea', 'dist', 'build'
EXCLUDE_DIRS = ['.git', 'node_modules', '__pycache__', '.venv', 'venv', 'env', '.DS_Store']

# 5. 要排除的特定文件名列表 (这些文件将被忽略，即使扩展名匹配)
# 脚本自身和输出文件会自动加入排除列表
EXCLUDE_FILES = []

# 6. 是否在输出文件中包含目录树
INCLUDE_DIRECTORY_TREE = True

# 7. 目录树显示的最大深度 (设置为 None 则不限制深度)
# 对于非常大的项目，建议设置一个合理的深度，例如 3 或 5
MAX_TREE_DEPTH = 5

# 8. 目录树中是否显示文件大小 (True/False)
SHOW_FILE_SIZE_IN_TREE = True

# --- 脚本核心逻辑 ---

def get_file_size_str(size_bytes):
    """将文件大小（字节）转换为可读的字符串格式"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024**2:
        return f"{size_bytes/1024:.1f} KB"
    elif size_bytes < 1024**3:
        return f"{size_bytes/1024**2:.1f} MB"
    else:
        return f"{size_bytes/1024**3:.1f} GB"

def generate_directory_tree(start_path, prefix="", level=0, current_max_depth=MAX_TREE_DEPTH, exclude_dirs=None, exclude_files=None, target_extensions=None):
    """
    生成目录结构树。
    """
    if exclude_dirs is None:
        exclude_dirs = []
    if exclude_files is None:
        exclude_files = []
    if target_extensions is None:
        target_extensions = []

    tree_output = []
    # 获取规范化的绝对路径
    abs_start_path = os.path.abspath(start_path)
    
    # 获取当前目录下的条目，并排序（文件夹在前，文件在后，然后按名称排序）
    try:
        entries = sorted(os.listdir(abs_start_path), key=lambda x: (os.path.isfile(os.path.join(abs_start_path, x)), x.lower()))
    except OSError as e:
        tree_output.append(f"{prefix}错误：无法访问目录 {abs_start_path}: {e}\n")
        return "".join(tree_output)

    pointers = ['├── '] * (len(entries) -1) + ['└── '] if entries else []

    for i, entry_name in enumerate(entries):
        entry_path = os.path.join(abs_start_path, entry_name)
        
        # 检查是否应排除此条目
        if entry_name in exclude_dirs or entry_name in exclude_files:
            continue
        # 如果是脚本文件自身或输出文件，也跳过
        if os.path.abspath(entry_path) == os.path.abspath(__file__) or entry_name == OUTPUT_FILENAME:
            continue

        size_info = ""
        if os.path.isfile(entry_path) and SHOW_FILE_SIZE_IN_TREE:
            try:
                size_bytes = os.path.getsize(entry_path)
                size_info = f" ({get_file_size_str(size_bytes)})"
            except OSError:
                size_info = " (大小未知)"


        if os.path.isdir(entry_path):
            # 如果是目录，则添加到树中并递归（如果未达到最大深度）
            tree_output.append(f"{prefix}{pointers[i]}{entry_name}/\n")
            if current_max_depth is None or level < current_max_depth -1:
                extension = '│   ' if pointers[i] == '├── ' else '    '
                tree_output.append(generate_directory_tree(entry_path, prefix + extension, level + 1, current_max_depth, exclude_dirs, exclude_files, target_extensions))
        else:
            # 如果是文件，检查其扩展名是否在目标列表中
            _, file_ext = os.path.splitext(entry_name)
            is_target_file = file_ext.lower() in [ext.lower() for ext in target_extensions]
            
            # 仅当文件是目标文件时，才在目录树中突出显示或特殊标记（可选）
            # 这里我们简单地列出所有非排除文件
            if is_target_file:
                tree_output.append(f"{prefix}{pointers[i]}{entry_name}{size_info}  <-- [目标文件]\n")
            else:
                tree_output.append(f"{prefix}{pointers[i]}{entry_name}{size_info}\n")
                
    return "".join(tree_output)


def collect_code_and_generate_report():
    """
    主函数：收集代码文件内容并生成报告。
    """
    script_name = os.path.basename(__file__)
    # 自动将脚本自身和输出文件加入排除列表
    effective_exclude_files = EXCLUDE_FILES + [script_name, OUTPUT_FILENAME]

    current_directory = os.getcwd()
    print(f"信息：脚本 '{script_name}' 开始执行。")
    print(f"信息：扫描目录: '{current_directory}'")
    print(f"信息：目标文件扩展名: {', '.join(TARGET_EXTENSIONS)}")
    print(f"信息：输出文件: '{OUTPUT_FILENAME}'")
    print(f"信息：递归扫描: {'是' if RECURSIVE_SCAN else '否'}")
    print(f"信息：排除目录: {', '.join(EXCLUDE_DIRS) if EXCLUDE_DIRS else '无'}")
    print(f"信息：排除文件: {', '.join(effective_exclude_files) if effective_exclude_files else '无'}")
    print(f"信息：包含目录树: {'是' if INCLUDE_DIRECTORY_TREE else '否'}")
    if INCLUDE_DIRECTORY_TREE:
        print(f"信息：目录树最大深度: {MAX_TREE_DEPTH if MAX_TREE_DEPTH is not None else '无限制'}")

    collected_files_paths = []

    if RECURSIVE_SCAN:
        for root, dirs, files in os.walk(current_directory, topdown=True):
            # 排除指定的目录
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
            
            for filename in files:
                # 排除指定的文件
                if filename in effective_exclude_files:
                    continue
                
                _, file_extension = os.path.splitext(filename)
                if file_extension.lower() in [ext.lower() for ext in TARGET_EXTENSIONS]:
                    file_path = os.path.join(root, filename)
                    collected_files_paths.append(file_path)
                    print(f"信息：发现目标文件 (递归): {os.path.relpath(file_path, current_directory)}")
    else:
        for item in os.listdir(current_directory):
            item_full_path = os.path.join(current_directory, item)
            if os.path.isfile(item_full_path):
                if item in effective_exclude_files:
                    continue
                _, file_extension = os.path.splitext(item)
                if file_extension.lower() in [ext.lower() for ext in TARGET_EXTENSIONS]:
                    collected_files_paths.append(item_full_path)
                    print(f"信息：发现目标文件 (当前目录): {item}")

    if not collected_files_paths:
        print(f"警告：在指定范围内未找到任何目标文件。输出文件 '{OUTPUT_FILENAME}' 将只包含头部信息。")
    else:
        print(f"\n信息：共找到 {len(collected_files_paths)} 个目标文件。开始写入到 '{OUTPUT_FILENAME}'...")

    # 按路径排序，确保输出顺序一致
    collected_files_paths.sort()

    try:
        with open(OUTPUT_FILENAME, 'w', encoding='utf-8') as outfile:
            # 写入报告头部信息
            outfile.write("=" * 80 + "\n")
            outfile.write(f"代码汇总报告\n")
            outfile.write(f"生成时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            outfile.write(f"扫描根目录: {current_directory}\n")
            outfile.write(f"目标文件类型: {', '.join(TARGET_EXTENSIONS)}\n")
            outfile.write(f"递归扫描: {'是' if RECURSIVE_SCAN else '否'}\n")
            outfile.write(f"排除目录: {', '.join(EXCLUDE_DIRS) if EXCLUDE_DIRS else '无'}\n")
            outfile.write(f"排除文件 (含自动): {', '.join(effective_exclude_files) if effective_exclude_files else '无'}\n")
            outfile.write("=" * 80 + "\n\n")

            # 写入目录树 (如果启用)
            if INCLUDE_DIRECTORY_TREE:
                outfile.write("项目目录结构树 (仅显示相关文件和目录):\n")
                outfile.write("-" * 40 + "\n")
                # 注意：这里的 generate_directory_tree 的 exclude_dirs 和 exclude_files 应该与主逻辑一致
                # 为了简化，我们直接使用全局配置的 EXCLUDE_DIRS 和 effective_exclude_files
                # 传递 target_extensions 以便在树中标记目标文件
                tree_str = generate_directory_tree(
                    current_directory, 
                    exclude_dirs=EXCLUDE_DIRS, 
                    exclude_files=effective_exclude_files, 
                    target_extensions=TARGET_EXTENSIONS,
                    current_max_depth=MAX_TREE_DEPTH
                )
                outfile.write(tree_str)
                outfile.write("-" * 40 + "\n\n")
            
            outfile.write("=" * 80 + "\n")
            outfile.write("汇总文件内容\n")
            outfile.write("=" * 80 + "\n\n")

            for file_path in collected_files_paths:
                relative_file_path = os.path.relpath(file_path, current_directory)
                outfile.write(f"--- 文件开始: {relative_file_path} ---\n\n")
                try:
                    with open(file_path, 'r', encoding='utf-8') as infile:
                        content = infile.read()
                        outfile.write(content)
                    # 确保文件末尾有换行，且与下一个文件标记之间有足够间隔
                    if not content.endswith('\n'):
                        outfile.write("\n")
                    outfile.write(f"\n\n--- 文件结束: {relative_file_path} ---\n")
                    outfile.write("=" * 60 + "\n\n") # 更明显的分隔符
                    print(f"信息：已成功处理并添加文件: {relative_file_path}")
                except UnicodeDecodeError:
                    error_msg = f"错误：无法以UTF-8编码读取文件 {relative_file_path}。文件可能使用了其他编码或为二进制文件。\n"
                    outfile.write(error_msg)
                    outfile.write(f"--- 文件结束 (读取错误): {relative_file_path} ---\n")
                    outfile.write("=" * 60 + "\n\n")
                    print(f"错误：读取文件 {relative_file_path} 时发生编码错误。已跳过其内容。")
                except Exception as e:
                    error_msg = f"错误：读取文件 {relative_file_path} 时发生未知错误: {e}\n"
                    outfile.write(error_msg)
                    outfile.write(f"--- 文件结束 (读取错误): {relative_file_path} ---\n")
                    outfile.write("=" * 60 + "\n\n")
                    print(f"错误：处理文件 {relative_file_path} 时发生错误: {e}")
            
            outfile.write("=" * 80 + "\n")
            outfile.write("代码汇总结束。\n")
            outfile.write("=" * 80 + "\n")

        print(f"\n成功：所有目标文件内容已汇总到 '{OUTPUT_FILENAME}'")

    except IOError as e:
        print(f"严重错误：无法写入输出文件 '{OUTPUT_FILENAME}'。请检查权限或磁盘空间。错误详情: {e}")
    except Exception as e:
        print(f"严重错误：在写入汇总文件过程中发生未知错误: {e}")

if __name__ == "__main__":
    # 运行主函数
    collect_code_and_generate_report()
    
    # 提示用户按键退出，以便在从命令行独立运行时查看输出
    # 在某些IDE中运行可能不需要这个
    try:
        input("\n脚本执行完毕。按 Enter 键退出...")
    except EOFError: # 如果在没有tty的环境下运行（如某些CI/CD），input会失败
        pass