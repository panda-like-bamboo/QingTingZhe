# 文件路径: src/data_entry.py
import os
import sys

# 获取项目根目录（PsychologyAnalysis/）
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
# 将项目根目录添加到模块搜索路径
sys.path.append(project_root)

from src.data_handler import DataHandler

def main():
    # 初始化 DataHandler
    handler = DataHandler(db_path=os.path.join(project_root, "psychology_analysis.db"))

    # 定义测试数据
    data_entries = [
        {
            "image_path": os.path.join(project_root, "input\images\image1.jpg"),
            "subject_info": {"name": "张三", "age": 13, "gender": "男"},
            "questionnaire_data": {"q1": "yes", "q2": "no", "q3": "sometimes"}
        },
        {
            "image_path": os.path.join(project_root, "input\images\TestPic.jpg"),
            "subject_info": {"name": "李四", "age": 15, "gender": "女"},
            "questionnaire_data": {"q1": "no", "q2": "yes", "q3": "often"}
        },
        {
            "image_path": "no_image.jpg",  # 没有对应图片，仅量表数据
            "subject_info": {"name": "王五", "age": 20, "gender": "男"},
            "questionnaire_data": {"q1": "yes", "q2": "yes", "q3": "rarely"}
        }
    ]

    # 录入数据
    for entry in data_entries:
        image_path = entry["image_path"]
        subject_info = entry["subject_info"]
        questionnaire_data = entry["questionnaire_data"]

        # 检查图片文件是否存在（如果 image_path 不是虚拟路径）
        if image_path != "no_image.jpg" and not os.path.exists(image_path):
            print(f"警告: 图片文件 {image_path} 不存在，跳过录入")
            continue

        try:
            handler.save_data(image_path, subject_info, questionnaire_data)
            print(f"成功录入数据: 图片路径 {image_path}, 被测者 {subject_info['name']}")
        except Exception as e:
            print(f"录入数据失败: 图片路径 {image_path}, 错误: {str(e)}")

if __name__ == "__main__":
    main()
    from src.data_handler import check_db_content
    check_db_content(os.path.join(project_root, "psychology_analysis.db"))
    
    