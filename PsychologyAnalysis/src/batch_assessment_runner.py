# 文件路径: PsychologyAnalysis/src/batch_assessment_runner.py
import os
import sys
import json
import random
import time
import logging

# --- 路径设置，确保能找到项目模块 ---
# 这个脚本位于 src 目录，项目根目录是上一级
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# 动态导入 requests，如果不存在则提示安装
try:
    import requests
except ImportError:
    print("错误: 'requests' 库未安装。请运行 'pip install requests' 进行安装。")
    sys.exit(1)

# --- 基本配置 ---
# 确保你的 FastAPI 服务器正在这个地址和端口上运行
BASE_URL = "http://0.0.0.0:8000"
LOGIN_URL = f"{BASE_URL}/api/v1/auth/token"
SUBMIT_URL = f"{BASE_URL}/api/v1/assessments/submit"

# 用于登录获取 Token 的管理员凭据 (请替换为你的实际凭据)
# 重要提示：在生产环境中，不应硬编码凭据。
ADMIN_USERNAME = "admin"  # 或者你创建的任何管理员用户名
ADMIN_PASSWORD = "password"      # 对应的密码

# 要创建的评估记录数量
NUMBER_OF_RECORDS_TO_CREATE = 5

# --- 日志配置 ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("BatchRunner")


# --- 辅助函数 ---

def login_and_get_token(username, password):
    """使用管理员账户登录并获取JWT令牌。"""
    logger.info(f"正在尝试以用户 '{username}' 登录...")
    login_data = {
        "username": username,
        "password": password
    }
    try:
        # FastAPI的OAuth2PasswordRequestForm需要 'application/x-www-form-urlencoded' 格式
        response = requests.post(LOGIN_URL, data=login_data)
        response.raise_for_status()  # 如果状态码是 4xx 或 5xx，则抛出异常
        token_data = response.json()
        token = token_data.get("access_token")
        if not token:
            logger.error("登录成功，但响应中未找到 'access_token'。")
            return None
        logger.info("登录成功，已获取到访问令牌。")
        return token
    except requests.exceptions.HTTPError as e:
        logger.error(f"登录失败，HTTP 错误: {e.response.status_code} - {e.response.text}")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"登录请求失败: {e}")
        return None

def load_questionnaires(questionnaire_dir):
    """从目录加载所有量表JSON文件。"""
    logger.info(f"正在从 '{questionnaire_dir}' 加载量表文件...")
    questionnaires = {}
    if not os.path.isdir(questionnaire_dir):
        logger.error(f"量表目录未找到: {questionnaire_dir}")
        return {}
    
    # 艾森克人格问卷的计分规则 (从其 JSON 文件中提取)
    epq_scoring_rules = None
        
    for filename in os.listdir(questionnaire_dir):
        if filename.endswith(".json"):
            file_path = os.path.join(questionnaire_dir, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # 使用文件名（不含扩展名）作为 scale_type 的 code
                    scale_code = os.path.splitext(filename)[0].split(' ')[0] # e.g., '1测你性格最真实的一面' -> '1测你性格最真实的一面'
                    questionnaires[scale_code] = data
                    logger.debug(f"已加载量表: {filename} (code: {scale_code})")
                    # 特别处理 EPQ
                    if "EPQ" in filename:
                        epq_scoring_rules = data.get("scoring_rules")
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"解析文件 '{filename}' 失败: {e}")
    
    if epq_scoring_rules:
        questionnaires['EPQ85']['scoring_rules'] = epq_scoring_rules
        
    logger.info(f"成功加载 {len(questionnaires)} 个量表。")
    return questionnaires

def generate_mock_data(questionnaires):
    """生成一条随机的评估数据。"""
    # 模拟基本信息
    first_names = ["张", "王", "李", "赵", "刘", "陈", "杨", "黄", "周", "吴"]
    last_names = ["伟", "芳", "娜", "敏", "静", "强", "磊", "军", "洋", "勇"]
    occupations = ["学生", "工人", "农民", "教师", "医生", "工程师", "无业"]
    case_types = ["电信诈骗", "网络赌博", "寻衅滋事", "交通肇事", "故意伤害"]

    basic_info = {
        "name": random.choice(first_names) + random.choice(last_names),
        "gender": random.choice(["男", "女"]),
        "age": random.randint(14, 65),
        "id_card": f"{random.randint(110000, 650000)}{random.randint(1950, 2008)}{random.randint(1,12):02d}{random.randint(1,28):02d}{random.randint(1000,9999)}",
        "occupation": random.choice(occupations),
        "case_name": f"{random.choice(case_types)}案-{random.randint(100,999)}",
        "case_type": random.choice(case_types),
        "identity_type": "犯罪嫌疑人",
        "person_type": "普通人员",
        "marital_status": random.choice(["未婚", "已婚", "离异"]),
        "children_info": random.choice(["无", "有，独立生活", "有，共同生活"]),
        "criminal_record": random.choice([0, 1]),
        "health_status": random.choice(["良好", "一般", "患有慢性病"]),
        "phone_number": f"1{random.randint(30,99):02d}{random.randint(10000000,99999999)}",
        "domicile": "模拟地区"
    }

    # 随机选择一个量表并模拟答案
    # 排除 EPQ，因为它的答案不是数字分数
    available_scales = {k: v for k, v in questionnaires.items() if "EPQ" not in k}
    if not available_scales:
        logger.warning("没有可用于生成随机答案的量表（已排除EPQ）。")
        return basic_info, None, {}

    scale_code = random.choice(list(available_scales.keys()))
    scale_data = available_scales[scale_code]
    answers = {}
    
    for question in scale_data.get("questions", []):
        q_num = question.get("number")
        options = question.get("options")
        if q_num and options:
            # 随机选择一个选项的 score
            selected_option = random.choice(options)
            answers[f"q{q_num}"] = selected_option.get("score")
    
    return basic_info, scale_code, answers


def submit_one_assessment(token, data_payload):
    """发送单次评估提交请求。"""
    headers = {
        "Authorization": f"Bearer {token}"
    }
    # multipart/form-data 格式，使用 requests 的 files 参数
    # requests 会自动处理 Content-Type 和 boundary
    files_payload = {}
    for key, value in data_payload.items():
        # 将非文件字段构造成 (None, value) 的元组
        files_payload[key] = (None, str(value))
    
    logger.info(f"正在为 '{data_payload.get('name')}' 提交评估...")
    logger.debug(f"提交的表单数据: {files_payload}")
    
    try:
        response = requests.post(SUBMIT_URL, headers=headers, files=files_payload)
        response.raise_for_status()
        response_data = response.json()
        logger.info(f"提交成功！响应: {response_data}")
        return response_data
    except requests.exceptions.HTTPError as e:
        logger.error(f"提交失败，HTTP 错误: {e.response.status_code} - {e.response.text}")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"提交请求失败: {e}")
        return None


def main():
    """主执行函数"""
    logger.info("--- 批量评估提交脚本启动 ---")

    # 1. 登录
    token = login_and_get_token(ADMIN_USERNAME, ADMIN_PASSWORD)
    if not token:
        logger.critical("无法获取认证令牌，脚本终止。")
        return

    # 2. 加载量表
    questionnaire_dir = os.path.join(PROJECT_ROOT, "input", "questionnaires")
    questionnaires = load_questionnaires(questionnaire_dir)
    if not questionnaires:
        logger.critical("未能加载任何量表，无法生成数据，脚本终止。")
        return
        
    # 3. 循环生成并提交数据
    success_count = 0
    failure_count = 0
    for i in range(NUMBER_OF_RECORDS_TO_CREATE):
        logger.info(f"\n--- 准备创建第 {i + 1}/{NUMBER_OF_RECORDS_TO_CREATE} 条记录 ---")
        
        # 生成模拟数据
        basic_info, scale_type, answers = generate_mock_data(questionnaires)
        
        # 准备请求负载
        payload = {
            **basic_info,
            "scale_type": scale_type,
            **answers
        }
        
        # 提交评估
        result = submit_one_assessment(token, payload)
        
        if result and result.get('submission_id'):
            success_count += 1
        else:
            failure_count += 1
            
        # 增加延时，避免对服务器造成过大压力
        time.sleep(1) 

    logger.info("\n--- 批量提交完成 ---")
    logger.info(f"成功: {success_count} 条")
    logger.info(f"失败: {failure_count} 条")

if __name__ == "__main__":
    main()