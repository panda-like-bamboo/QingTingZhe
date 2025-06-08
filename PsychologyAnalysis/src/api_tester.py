# 文件路径: src/api_tester.py
import base64
import os
import sqlite3
import json
from openai import OpenAI
from src.utils import setup_logging
from src.image_processor import ImageProcessor
from src.report_generator import ReportGenerator

class APITester:
    def __init__(self, config):
        """初始化 API 测试模块"""
        self.logger = setup_logging()
        self.config = config
        
        # 统一客户端配置
        self.api_key = config["api_key"]
        self.base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
        )
        
        # 模型名称
        self.vision_model = "qwen-vl-max-latest"
        self.text_model = config["text_model"]  # 从配置中读取，例如 "qwen-plus"
        
        # 初始化数据库路径
        self.db_path = "psychology_analysis.db"
        self.project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # 初始化测试用模块
        self.image_processor = ImageProcessor(config)
        self.report_generator = ReportGenerator(config)

    def setup_test_data(self):
        """为测试准备数据，插入测试用图片路径和量表数据"""
        self.logger.info("准备测试数据...")
        
        # 连接数据库
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 清空现有数据（仅用于测试）
            cursor.execute("DELETE FROM analysis_data")
            
            # 插入测试数据
            test_image_path = os.path.join(self.project_root, "input", "images", "TestPic.jpg")
            subject_info = {"name": "测试用户", "age": 20, "gender": "男"}
            questionnaire_data = {"q1": "yes", "q2": "no", "q3": "sometimes"}
            
            cursor.execute('''
                INSERT INTO analysis_data (image_path, subject_name, age, gender, questionnaire_data)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                test_image_path,
                subject_info["name"],
                subject_info["age"],
                subject_info["gender"],
                json.dumps(questionnaire_data)
            ))
            
            # 插入只有量表数据的记录（无对应图片）
            cursor.execute('''
                INSERT INTO analysis_data (image_path, subject_name, age, gender, questionnaire_data)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                "no_image.jpg",  # 虚拟图片路径
                "无图片用户",
                25,
                "女",
                json.dumps({"q1": "no", "q2": "yes", "q3": "often"})
            ))
            
            conn.commit()
        self.logger.info("测试数据准备完成")

    def cleanup_test_data(self):
        """清理测试数据"""
        self.logger.info("清理测试数据...")
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM analysis_data")
            conn.commit()
        self.logger.info("测试数据清理完成")

    def test_vision_api(self):
        """测试图像处理模型的 API 连通性"""
        self.logger.info("开始测试图像处理模型 API...")
        
        # 使用 input/images/TestPic.jpg 进行测试
        test_image_path = os.path.join(self.project_root, "input", "images", "TestPic.jpg")
        
        if not os.path.exists(test_image_path):
            self.logger.error(f"测试图片 {test_image_path} 不存在，请确保文件已放置在正确位置")
            return False
        
        # 将图片转为 base64 编码
        with open(test_image_path, "rb") as image_file:
            image_base64 = base64.b64encode(image_file.read()).decode("utf-8")

        # 构造消息内容
        messages = [
            {"role": "system", "content": [{"type": "text", "text": "You are a helpful assistant."}]},
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}},
                    {"type": "text", "text": "请简要描述这张图片的内容，用于API测试。"}
                ]
            }
        ]

        try:
            completion = self.client.chat.completions.create(
                model=self.vision_model,
                messages=messages,
            )
            description = completion.choices[0].message.content
            self.logger.info("图像模型 API 测试成功！")
            self.logger.info(f"测试图片描述: {description}")
            return True
        except Exception as e:
            self.logger.error(f"图像模型 API 测试失败: {str(e)}")
            return False

    def test_text_api(self):
        """测试文本生成模型的 API 连通性"""
        self.logger.info("开始测试文本生成模型 API...")
        
        # 构造测试消息
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "这是一个API连通性测试，请回复‘测试成功’。"}
        ]

        try:
            completion = self.client.chat.completions.create(
                model=self.text_model,
                messages=messages,
            )
            text_output = completion.choices[0].message.content
            self.logger.info("文本生成模型 API 测试成功！")
            self.logger.info(f"测试输出: {text_output}")
            return True
        except Exception as e:
            self.logger.error(f"文本生成模型 API 测试失败: {str(e)}")
            return False

    def test_report_with_questionnaire_only(self):
        """测试只有量表数据时是否能生成报告"""
        self.logger.info("开始测试只有量表数据时的报告生成...")
        
        # 从数据库加载只有量表数据的记录
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT subject_name, age, gender, questionnaire_data FROM analysis_data WHERE image_path = ?", ("no_image.jpg",))
            result = cursor.fetchone()
            if not result:
                self.logger.error("未找到只有量表数据的测试记录")
                return False
            
            subject_info = {"name": result[0], "age": result[1], "gender": result[2]}
            questionnaire_data = json.loads(result[3]) if result[3] else None
            
            if not questionnaire_data:
                self.logger.error("量表数据为空，无法生成报告")
                return False

        # 使用空描述生成报告
        description = "无图片输入，仅基于量表数据生成报告"
        try:
            report = self.report_generator.generate_report(description, questionnaire_data, subject_info)
            self.logger.info("仅使用量表数据生成报告成功！")
            self.logger.info(f"生成的报告片段: {report[:100]}...")  # 只打印前100个字符
            return True
        except Exception as e:
            self.logger.error(f"仅使用量表数据生成报告失败: {str(e)}")
            return False

    def test_full_pipeline(self):
        """测试完整流程：图像 + 量表数据"""
        self.logger.info("开始测试完整流程（图像 + 量表数据）...")
        
        # 使用 TestPic.jpg 进行测试
        test_image_path = os.path.join(self.project_root, "input", "images", "TestPic.jpg")
        
        if not os.path.exists(test_image_path):
            self.logger.error(f"测试图片 {test_image_path} 不存在，请确保文件已放置在正确位置")
            return False
        
        # 步骤1: 图像识别
        try:
            description = self.image_processor.process_image(test_image_path)
            self.logger.info("图像描述生成成功")
            self.logger.info(f"描述片段: {description[:100]}...")  # 只打印前100个字符
        except Exception as e:
            self.logger.error(f"图像描述生成失败: {str(e)}")
            return False
        
        # 步骤2: 从数据库加载量表数据
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT subject_name, age, gender, questionnaire_data FROM analysis_data WHERE image_path = ?", (test_image_path,))
            result = cursor.fetchone()
            if not result:
                self.logger.error(f"图片 {test_image_path} 无对应量表数据")
                return False
            
            subject_info = {"name": result[0], "age": result[1], "gender": result[2]}
            questionnaire_data = json.loads(result[3]) if result[3] else None
            
            if not questionnaire_data:
                self.logger.error("量表数据为空，无法生成报告")
                return False

        # 步骤3: 生成报告
        try:
            report = self.report_generator.generate_report(description, questionnaire_data, subject_info)
            self.logger.info("完整流程生成报告成功！")
            self.logger.info(f"生成的报告片段: {report[:100]}...")  # 只打印前100个字符
            return True
        except Exception as e:
            self.logger.error(f"完整流程生成报告失败: {str(e)}")
            return False

    def run_all_tests(self):
        """运行所有 API 测试"""
        self.logger.info("开始运行所有 API 测试...")
        
        # 准备测试数据
        self.setup_test_data()
        
        # 执行所有测试
        vision_result = self.test_vision_api()
        text_result = self.test_text_api()
        questionnaire_only_result = self.test_report_with_questionnaire_only()
        full_pipeline_result = self.test_full_pipeline()
        
        # 清理测试数据
        self.cleanup_test_data()
        
        # 汇总测试结果
        if all([vision_result, text_result, questionnaire_only_result, full_pipeline_result]):
            self.logger.info("所有 API 测试通过！")
            return True
        else:
            self.logger.error("部分或全部 API 测试未通过，请检查日志")
            self.logger.error(f"测试结果 - 图像API: {vision_result}, 文本API: {text_result}, 仅量表: {questionnaire_only_result}, 完整流程: {full_pipeline_result}")
            return False

if __name__ == "__main__":
    import yaml
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(project_root, "config", "config.yaml")
    with open(config_path, "r", encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    tester = APITester(config)
    tester.run_all_tests()