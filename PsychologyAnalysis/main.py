# 文件路径: main.py
import os
import yaml
import sqlite3
import json
from concurrent.futures import ThreadPoolExecutor, as_completed  # 新增导入
from src.image_processor import ImageProcessor
from src.report_generator import ReportGenerator
from src.data_handler import DataHandler
from src.utils import setup_logging

def process_single_task(image_path, image_processor, report_generator, data_handler, logger):
    """处理单个图片和量表数据的分析任务"""
    logger.info(f"开始处理图片: {image_path}")
    try:
        # 处理图片
        description = image_processor.process_image(image_path)
        desc_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                               f"output/descriptions/{os.path.splitext(os.path.basename(image_path))[0]}_desc.txt")
        os.makedirs(os.path.dirname(desc_file), exist_ok=True)
        with open(desc_file, "w", encoding='utf-8') as f:
            f.write(description)
        logger.info(f"图片描述已保存至: {desc_file}")

        # 加载数据
        subject_info, questionnaire_type, questionnaire_data = data_handler.load_data_by_image(image_path)
        if not subject_info:
            logger.warning(f"图片 {image_path} 无对应量表数据，仅保存描述")
            return

        # 计算得分并生成报告
        score = calculate_score(questionnaire_type, questionnaire_data)
        report = report_generator.generate_report(description, questionnaire_data, subject_info, questionnaire_type, score)
        report_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                 f"output/reports/{os.path.splitext(os.path.basename(image_path))[0]}_report.txt")
        os.makedirs(os.path.dirname(report_file), exist_ok=True)
        with open(report_file, "w", encoding='utf-8') as f:
            f.write(report)
        logger.info(f"报告已保存至: {report_file}")
    except Exception as e:
        logger.error(f"处理 {image_path} 时出错: {str(e)}")

def main(image_paths=None, max_workers=4):
    logger = setup_logging()
    logger.info("心理学图像和数据分析项目启动（并发模式）")

    project_root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_root)
    config_path = os.path.join(project_root, "config/config.yaml")
    with open(config_path, "r", encoding='utf-8') as f:
        config = yaml.safe_load(f)

    # 初始化处理器
    image_processor = ImageProcessor(config)
    report_generator = ReportGenerator(config)
    data_handler = DataHandler(db_path=os.path.join(project_root, "psychology_analysis.db"))

    # 如果没有指定图片路径，处理 input/images 目录下的所有图片
    if not image_paths:
        image_dir = os.path.join(project_root, "input/images")
        image_paths = [os.path.join(image_dir, f) for f in os.listdir(image_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        logger.info(f"未指定图片路径，将处理目录 {image_dir} 中的所有图片: {len(image_paths)} 张")

    if not image_paths:
        logger.warning("没有找到任何图片需要处理")
        return

    # 使用线程池并发处理
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有任务
        future_to_image = {executor.submit(process_single_task, image_path, image_processor, report_generator, data_handler, logger): image_path 
                         for image_path in image_paths}
        
        # 处理完成的任务
        for future in as_completed(future_to_image):
            image_path = future_to_image[future]
            try:
                future.result()  # 获取结果，如果有异常会抛出
                logger.info(f"任务完成: {image_path}")
            except Exception as e:
                logger.error(f"任务 {image_path} 执行失败: {str(e)}")

def calculate_score(questionnaire_type, questionnaire_data):
    """根据量表类型计算总分"""
    scores = [int(value) for value in questionnaire_data.values()]
    total_score = sum(scores)
    return total_score

if __name__ == "__main__":
    # 示例：可以传入特定图片路径列表
    specific_images = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "input/images/TestPic.jpg"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "input/images/testpic1.jpg")
    ]
    main(image_paths=specific_images, max_workers=4)  # 设置最大线程数为4
    # 或不指定图片路径，处理所有图片
    # main(max_workers=4)