
# 将文件夹下内容转化为txt文件，方便一次性导入导出
# 该脚本会遍历指定目录下的所有文件和子目录，并将可读的文本文件内容写入到一个输出文件中
# 目录树结构也会被写入到输出文件的开头

import os
import argparse
from pathlib import Path
import sys

# --- 配置 ---

# 硬编码的根目录路径
HARDCODED_ROOT_DIR = r"C:\Users\ymh33\Desktop\Project\PythonProject\QingtingzheDemoProject"

# 默认输出文件名
DEFAULT_OUTPUT_FILENAME = "dump0608.txt" # 可以改成更具体的名字

# 识别为可读文本文件的扩展名 (小写)
READABLE_EXTENSIONS = {
    # Code files
    '.py', '.js', '.ts', '.java', '.c', '.cpp', '.h', '.hpp', '.cs', '.go',
    '.rb', '.php', '.swift', '.kt', '.scala', '.rs', '.lua', '.pl', '.sh',
    '.bat', '.ps1',
    # Markup & Data
    '.html', '.htm', '.css', '.scss', '.less', '.md', '.rst', '.json', '.yaml',
    '.yml', '.xml', '.toml', '.ini', '.cfg', '.env', '.sql',
    # Text & Docs
    # '.txt', '.log', '.csv', '.tsv', '.tex',
    # Config files
    # '.gitignore', '.dockerignore', 'dockerfile', '.editorconfig',
    # '.babelrc', '.eslintrc', '.prettierrc',
    # Add more as needed
}

# 识别为可读的特定文件名 (小写，不含扩展名或完整文件名)
READABLE_FILENAMES = {
    'readme', 'license', 'contributing', 'changelog', 'makefile', 'dockerfile',
    'requirements.txt', 'pipfile', 'gemfile', 'package.json', 'composer.json',
    'pom.xml', 'build.gradle', 'setup.py',
    # Add more specific filenames
}

# 需要完全排除扫描的目录名称
EXCLUDE_DIRS = {
    '.git', '.svn', '.hg', '.vscode', '.idea', '__pycache__', 'node_modules',
    'vendor', 'build', 'dist', 'target', 'out', 'bin', 'obj', 'venv', 'env',
    '.pytest_cache', '.mypy_cache', '.tox', '.nox', 'site-packages', 'migrations'
    # Add more directories to exclude
}

# 需要排除的特定文件名称
EXCLUDE_FILES = {
    '.DS_Store', 'Thumbs.db',
    # Add specific files to exclude by name
}

# --- 辅助函数 ---

def generate_tree(start_path, exclude_dirs):
    """生成目录树结构字符串"""
    tree_lines = []
    start_path = Path(start_path).resolve() # 确保是绝对路径

    def build_tree_recursive(directory, prefix="", is_last=False):
        try:
            # 获取目录内容，排序以保证一致性
            items = sorted(
                [item for item in directory.iterdir()],
                key=lambda x: (x.is_file(), x.name.lower()) # 文件夹优先，然后按名称排序
            )
        except PermissionError:
            tree_lines.append(f"{prefix}└── [Error: Permission Denied]")
            return
        except OSError as e:
            tree_lines.append(f"{prefix}└── [Error: {e}]")
            return

        # 过滤掉需要排除的目录和文件（主要用于树状图显示）
        items = [
            item for item in items
            if not (item.is_dir() and item.name in exclude_dirs) and \
               not (item.is_file() and item.name in EXCLUDE_FILES)
        ]

        for i, item in enumerate(items):
            is_current_last = (i == len(items) - 1)
            connector = "└── " if is_current_last else "├── "
            tree_lines.append(f"{prefix}{connector}{item.name}")

            if item.is_dir():
                new_prefix = prefix + ("    " if is_current_last else "│   ")
                build_tree_recursive(item, new_prefix, is_current_last)

    tree_lines.append(f"{start_path.name}/")
    build_tree_recursive(start_path) # 初始调用
    return "\n".join(tree_lines)

def is_readable_file(file_path: Path) -> bool:
    """检查文件是否根据配置被认为是可读的文本文件"""
    # 1. 检查是否在排除的文件列表中
    if file_path.name in EXCLUDE_FILES:
        return False

    # 2. 检查特定文件名 (不区分大小写)
    if file_path.name.lower() in READABLE_FILENAMES:
        return True

    # 3. 检查文件扩展名 (不区分大小写)
    if file_path.suffix.lower() in READABLE_EXTENSIONS:
        return True

    # 4. 检查无扩展名的特定文件名（如 Dockerfile）
    if file_path.stem.lower() in READABLE_FILENAMES and not file_path.suffix:
         return True

    # 默认不是可读文件
    return False

# --- 主函数 ---

def main(output_file): # 注意：移除了 root_dir 参数
    root_path = Path(HARDCODED_ROOT_DIR).resolve() # 使用硬编码的路径
    output_path = Path(output_file)

    if not root_path.is_dir():
        # 使用硬编码的路径显示错误消息
        print(f"Error: Root directory '{HARDCODED_ROOT_DIR}' not found or is not a directory.", file=sys.stderr)
        sys.exit(1)

    all_content = []

    # 1. 生成目录树
    print(f"Generating directory tree for '{root_path}'...") # root_path 现在是硬编码路径解析后的结果
    try:
        tree_structure = generate_tree(root_path, EXCLUDE_DIRS)
        all_content.append("--- Directory Tree ---")
        all_content.append(tree_structure)
        all_content.append("\n" + "="*80 + "\n") # 分隔符
    except Exception as e:
        print(f"Error generating directory tree: {e}", file=sys.stderr)
        all_content.append(f"--- Error Generating Directory Tree ---\n{e}\n")
        all_content.append("\n" + "="*80 + "\n")

    # 2. 遍历文件并读取内容
    print("Scanning and reading files...")
    file_contents = []
    processed_files = 0
    skipped_binary_or_excluded = 0
    read_errors = 0

    # 使用 os.walk 来高效地排除目录，起始路径使用 root_path
    for root, dirs, files in os.walk(root_path, topdown=True, onerror=lambda err: print(f"Warning: Cannot access {err.filename} - {err.strerror}", file=sys.stderr)):
        # --- 排除目录 ---
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]

        current_root_path = Path(root)

        # 对文件进行排序，保证输出顺序一致
        files.sort()

        for filename in files:
            file_path = current_root_path / filename
            # 计算相对路径时，仍然相对于硬编码的根路径
            relative_path = file_path.relative_to(root_path)

            # 检查是否是可读文件
            if is_readable_file(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    file_contents.append(f"--- File: {relative_path} ---")
                    file_contents.append(content)
                    file_contents.append("\n" + "="*80 + "\n") # 文件间分隔符
                    processed_files += 1
                    if processed_files % 100 == 0: # 每处理 100 个文件打印一次进度
                        print(f"  Processed {processed_files} files...")
                except Exception as e:
                    print(f"  Warning: Could not read file {relative_path}: {e}", file=sys.stderr)
                    file_contents.append(f"--- File: {relative_path} ---")
                    file_contents.append(f"[Error reading file: {e}]")
                    file_contents.append("\n" + "="*80 + "\n")
                    read_errors += 1
            else:
                skipped_binary_or_excluded += 1
                # 可选：打印被跳过的文件信息
                # print(f"  Skipping non-readable or excluded file: {relative_path}")

    print(f"Finished scanning.")
    print(f"  Processed {processed_files} readable files.")
    print(f"  Skipped {skipped_binary_or_excluded} non-readable/excluded files.")
    if read_errors > 0:
        print(f"  Encountered {read_errors} errors while reading files.")

    all_content.extend(file_contents)

    # 3. 写入到输出文件
    print(f"Writing output to '{output_path}'...")
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(all_content))
        print(f"Successfully created output file: '{output_path}'")
    except Exception as e:
        print(f"Error writing to output file '{output_path}': {e}", file=sys.stderr)
        sys.exit(1)

# --- 脚本入口 ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=f"Convert readable files in '{HARDCODED_ROOT_DIR}' into a single TXT file.", # 更新描述
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    # 移除了 root_dir 参数
    parser.add_argument(
        "-o", "--output",
        default=DEFAULT_OUTPUT_FILENAME,
        help=f"The name of the output TXT file (default: {DEFAULT_OUTPUT_FILENAME})"
    )

    args = parser.parse_args()

    # 调用 main 时只传递 output 文件名
    main(args.output)