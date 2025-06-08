import os
import sys
from tqdm import tqdm

# 定义允许被合并内容的文件扩展名
ALLOWED_EXTENSIONS_FOR_CONTENT = ('.py', '.txt', '.md', '.json', '.xml', '.html', '.css', '.js', '.csv')

# --- 恢复 generate_tree 到原始版本，以包含所有文件 ---
def generate_tree(root_dir):
    """生成类似 tree /f 的目录树字符串 (包含所有文件和目录)"""
    tree_output = [root_dir]
    # os.walk 会自然遍历所有子目录和文件
    for root, dirs, files in os.walk(root_dir):
        level = root.replace(root_dir, '').count(os.sep)
        indent = '    ' * level
        if level > 0:  # 避免重复输出根目录
            tree_output.append(f"{indent}{os.path.basename(root)}")
        
        # --- 在目录树中列出该目录下的所有文件 ---
        sub_indent = indent + '    '
        for file in files:
            # 不进行扩展名过滤，列出所有文件
            tree_output.append(f"{sub_indent}{file}")
            
    return "\n".join(tree_output)

def concatenate_files(root_dir, output_file):
    # 计算总文件数以初始化进度条 (反映遍历的所有文件)
    total_files = sum(len(files) for _, _, files in os.walk(root_dir))

    # 预计算将被合并内容的文件数（可选，如果你想让进度条只反映合并进度）
    # included_files_count = 0
    # for root, dirs, files in os.walk(root_dir):
    #     for file in files:
    #         _, ext = os.path.splitext(file)
    #         if ext.lower() in ALLOWED_EXTENSIONS_FOR_CONTENT:
    #             included_files_count += 1
    # print(f"找到 {included_files_count} 个符合条件的文件将被合并内容。")


    with open(output_file, 'w', encoding='utf-8') as outfile:
        # --- 写入完整的目录树 ---
        outfile.write("Full Project Directory Tree:\n") # 标题明确说明是完整树
        outfile.write(generate_tree(root_dir) + "\n") # 调用未经过滤的 generate_tree
        outfile.write("=====\n\n")
        outfile.write("Concatenated File Content (Filtered):\n") # 明确说明内容是过滤后的

        # 使用 tqdm 显示进度条 (total 仍然是所有文件数，反映遍历进度)
        # 如果使用上面的 included_files_count，这里改为 total=included_files_count
        with tqdm(total=total_files, desc="扫描文件并合并内容", unit="file") as pbar:
            for root, dirs, files in os.walk(root_dir):
                for file in files:
                    file_path = os.path.join(root, file)

                    # --- 核心过滤逻辑：只处理指定扩展名的文件内容 ---
                    _, ext = os.path.splitext(file)

                    # 检查扩展名是否在允许合并内容的列表中
                    if ext.lower() in ALLOWED_EXTENSIONS_FOR_CONTENT:
                        # --- 文件内容合并逻辑 ---
                        try:
                            with open(file_path, 'r', encoding='utf-8') as infile:
                                content = infile.read()
                                outfile.write("FILE: " + file_path + "\n")
                                outfile.write(content + "\n")
                                outfile.write("-----\n")
                            print(f"已合并内容: {file_path} - 成功")
                        except Exception as e:
                            # 即使读取失败，也记录下来
                            outfile.write(f"FILE: {file_path}\n")
                            outfile.write(f"读取文件出错 (尝试合并内容时): {str(e)}\n")
                            outfile.write("-----\n")
                            print(f"尝试合并内容失败: {file_path} - 错误: {str(e)}")
                    else:
                        # --- 文件类型不符，跳过内容合并 ---
                        # 不需要写入文件内容，只在控制台打印信息
                        print(f"已跳过内容合并 (类型不符): {file_path}")

                    # --- 更新进度条 ---
                    # 每个访问的文件都更新进度条
                    pbar.update(1)

if __name__ == "__main__":
    root_dir = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    output_file = 'project_text1.txt'
    print(f"正在扫描目录: {root_dir}")
    print(f"将生成包含所有文件的目录树，并合并后缀为 {', '.join(ALLOWED_EXTENSIONS_FOR_CONTENT)} 的文件内容到: {output_file}")
    concatenate_files(root_dir, output_file)
    print(f"处理完成。输出文件: {output_file}")