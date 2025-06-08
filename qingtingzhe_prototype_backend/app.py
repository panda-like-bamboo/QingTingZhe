import os
import json
# Add copy for deep copying the template
import copy
from flask import (
    Flask, render_template, request, redirect, url_for, session,
    flash, jsonify, send_file, Response
)

# --- 配置 ---
app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'a_very_insecure_default_secret_key_for_prototype')

# --- 获取数据文件路径 ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
# --- 修改回 JSON 文件路径 ---
INTERROGATION_TEMPLATE_PATH = os.path.join(DATA_DIR, 'interrogation_template.json')
GUIDANCE_PLAN_PATH = os.path.join(DATA_DIR, 'guidance_plan.txt')

# --- 模拟数据加载 (恢复 JSON 加载) ---
try:
    with open(INTERROGATION_TEMPLATE_PATH, 'r', encoding='utf-8') as f:
        # --- 使用 json.load ---
        INTERROGATION_TEMPLATE = json.load(f)
except FileNotFoundError:
    print(f"警告: 审讯模板文件未找到: {INTERROGATION_TEMPLATE_PATH}")
    INTERROGATION_TEMPLATE = {"error": "模板文件丢失", "questions_answers": []} # Provide default structure
except json.JSONDecodeError:
     print(f"警告: 审讯模板文件 JSON 格式错误: {INTERROGATION_TEMPLATE_PATH}")
     INTERROGATION_TEMPLATE = {"error": "模板文件格式错误", "questions_answers": []} # Provide default structure
except Exception as e:
    print(f"加载审讯模板时发生未知错误: {e}")
    INTERROGATION_TEMPLATE = {"error": "加载模板时出错", "questions_answers": []}


try:
    with open(GUIDANCE_PLAN_PATH, 'r', encoding='utf-8') as f:
        GUIDANCE_PLAN_TEXT = f.read()
except FileNotFoundError:
    print(f"警告: 指导方案文件未找到: {GUIDANCE_PLAN_PATH}")
    GUIDANCE_PLAN_TEXT = "错误：指导方案文件丢失。"

# (Keep MOCK_REPORT_ID_20_TEXT and MOCK_USERS as they were)
MOCK_REPORT_ID_20_TEXT = """
综合心理状态分析与建议
... (rest of the text) ...
"""
MOCK_USERS = [
    {"id": 1, "username": "admin", "email": "admin@example.com", "full_name": "管理员", "is_active": True, "is_superuser": True},
    # ... (rest of the users) ...
    {"id": 100, "username": "tech_guan", "email": "guan.tech@example.com", "full_name": "关技术员", "is_active": True, "is_superuser": False},
]


# --- 辅助函数 ---
def login_required(f):
    import functools
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            flash('请先登录', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# --- 路由 ---

@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == 'admin' and password == 'password':
            session['logged_in'] = True
            session['username'] = username
            flash('登录成功!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('用户名或密码错误', 'danger')
            return render_template('login.html', error="用户名或密码错误")
    if 'logged_in' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    flash('您已成功退出登录', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    functions = [
        "查询报告", "数据分析", "辅助智能审讯笔录",
        "上访户情绪疏导", "未成年人犯罪心理辅导",
        "民辅警心理评估报告", "用户管理"
    ]
    return render_template('dashboard.html', functions=functions)

# --- 审讯笔录 ---
@app.route('/interrogation/input')
@login_required
def interrogation_input():
    return render_template('interrogation_input.html')

@app.route('/interrogation/generate', methods=['POST'])
@login_required
def generate_interrogation_record():
    """审讯笔录 - 生成可编辑的表单页面"""
    basic_info = {
        "name": request.form.get('name'),
        "gender": request.form.get('gender'),
        "id_card": request.form.get('id_card'),
        "phone": request.form.get('phone'),
        "address": request.form.get('address'),
        # --- 模拟或计算其他信息 ---
        "age": "未知", # TODO: Calculate from ID card if possible
        "dob": "未知", # TODO: Extract from ID card if possible
        "hukou": request.form.get('hukou', "未知"), # Add if hukou is in input form
    }

    # --- 使用深拷贝，避免修改原始模板 ---
    if "error" in INTERROGATION_TEMPLATE:
         flash(f"无法加载审讯模板: {INTERROGATION_TEMPLATE['error']}", "danger")
         # 可以重定向回输入页或显示错误页
         return redirect(url_for('interrogation_input'))

    template_data = copy.deepcopy(INTERROGATION_TEMPLATE)

    # --- 用 basic_info 填充 template_data ---
    template_data['person_name'] = basic_info.get('name', template_data.get('person_name', ''))
    template_data['person_gender'] = basic_info.get('gender', template_data.get('person_gender', ''))
    template_data['person_id_type_number'] = basic_info.get('id_card', template_data.get('person_id_type_number', ''))
    template_data['person_address'] = basic_info.get('address', template_data.get('person_address', ''))
    template_data['person_contact'] = basic_info.get('phone', template_data.get('person_contact', ''))
    template_data['person_age'] = basic_info.get('age', template_data.get('person_age', ''))
    template_data['person_dob'] = basic_info.get('dob', template_data.get('person_dob', ''))
    template_data['person_hukou'] = basic_info.get('hukou', template_data.get('person_hukou', ''))

    # --- 传递填充后的数据到新的编辑模板 ---
    return render_template('interrogation_edit.html',
                           template_data=template_data)

# --- 新增：处理编辑后提交的路由 ---
@app.route('/interrogation/save', methods=['POST'])
@login_required
def save_interrogation_record():
    """审讯笔录 - 保存编辑后的数据 (模拟)"""
    edited_data = {}
    # --- 重新构建数据结构 ---
    # 获取所有表单字段
    form_data = request.form.to_dict()

    # 简单地将所有表单字段放入 edited_data (这不够健壮，需要精确映射)
    # edited_data = form_data # 这会丢失 questions_answers 的结构

    # --- 更精确地重建 JSON 结构 ---
    # 1. 提取基本信息
    for key in INTERROGATION_TEMPLATE.keys(): # Use original keys as guide
        if key not in ['questions_answers', 'signature_section']:
             edited_data[key] = form_data.get(key) # Get simple fields directly

    # 2. 重建 questions_answers 列表
    edited_qas = []
    qa_indices = set()
    # Find submitted question/answer indices (more robust than assuming fixed count)
    for key in form_data:
        if key.startswith('questions_answers[') and key.endswith('][q]'):
            index = key.split('[')[1].split(']')[0]
            qa_indices.add(int(index))
        elif key.startswith('questions_answers[') and key.endswith('][a]'):
            index = key.split('[')[1].split(']')[0]
            qa_indices.add(int(index))

    for i in sorted(list(qa_indices)): # Process in order
         q_key = f'questions_answers[{i}][q]'
         a_key = f'questions_answers[{i}][a]'
         question = form_data.get(q_key, "") # Default to empty string if missing
         answer = form_data.get(a_key, "")   # Default to empty string if missing
         edited_qas.append({"q": question, "a": answer})
    edited_data['questions_answers'] = edited_qas

    # 3. 重建 signature_section 字典
    edited_data['signature_section'] = {}
    sig_template = INTERROGATION_TEMPLATE.get('signature_section', {})
    for key in sig_template.keys():
         # Naming convention in HTML should be signature_section[key_name]
         form_key = f'signature_section[{key}]'
         edited_data['signature_section'][key] = form_data.get(form_key, sig_template[key]) # Get from form or default

    # --- 模拟保存 ---
    print("--- RECEIVED EDITED RECORD DATA ---")
    print(json.dumps(edited_data, ensure_ascii=False, indent=2))
    # In a real app: save edited_data to a database or a new file

    flash('笔录已更新 (模拟保存成功)', 'success')
    # 可以重定向到查看页面，或者 dashboard
    return redirect(url_for('dashboard'))

# --- PDF 下载路由（保持不变，或修改为基于已保存数据生成） ---
@app.route('/interrogation/pdf')
@login_required
def download_interrogation_pdf():
    # TODO: Implement PDF generation based on saved/edited data
    return Response("PDF 生成功能待实现", mimetype='text/plain', status=501)

# --- 其他路由 (保持不变) ---
@app.route('/petitioner-guidance', methods=['GET', 'POST'])
@login_required
def view_petitioner_guidance():
    if request.method == 'POST':
        name = request.form.get('name')
        id_card = request.form.get('id_card')
        print(f"查询上访户: {name}, 身份证: {id_card}")
        report_text = MOCK_REPORT_ID_20_TEXT
        guidance_text = GUIDANCE_PLAN_TEXT
        return render_template('report_guidance_viewer.html',
                               title=f"{name} - 上访户情绪疏导",
                               report_text=report_text,
                               guidance_text=guidance_text,
                               guidance_title="上访户情绪疏导方案",
                               show_input_form=False,
                               back_link=url_for('view_petitioner_guidance'))
    return render_template('report_guidance_viewer.html',
                            title="上访户情绪疏导",
                            show_input_form=True)

@app.route('/juvenile-counseling', methods=['GET', 'POST'])
@login_required
def view_juvenile_counseling():
    if request.method == 'POST':
        name = request.form.get('name')
        id_card = request.form.get('id_card')
        print(f"查询未成年人: {name}, 身份证: {id_card}")
        report_text = MOCK_REPORT_ID_20_TEXT
        guidance_text = GUIDANCE_PLAN_TEXT
        return render_template('report_guidance_viewer.html',
                               title=f"{name} - 未成年人心理辅导",
                               report_text=report_text,
                               guidance_text=guidance_text,
                               guidance_title="未成年人犯罪心理辅导方案",
                               show_input_form=False,
                               back_link=url_for('view_juvenile_counseling'))
    return render_template('report_guidance_viewer.html',
                           title="未成年人犯罪心理辅导",
                           show_input_form=True)

@app.route('/police-report')
@login_required
def view_police_report():
    report_text = MOCK_REPORT_ID_20_TEXT
    guidance_text = """
    关于提升民辅警队伍心理健康水平的若干建议
    ... (rest of guidance text) ...
    """
    return render_template('report_guidance_viewer.html',
                           title="民辅警心理评估报告",
                           report_text=report_text,
                           guidance_text=guidance_text,
                           guidance_title="民辅警心理调适建议",
                           show_input_form=False)

@app.route('/data-analysis')
@login_required
def data_analysis():
    return render_template('data_analysis.html')

@app.route('/api/data-analysis')
def data_analysis_api():
    mock_data = {
        'ageData': {'labels': ['<18', '18-25', '26-35', '36-45', '46-55', '56+'], 'values': [8, 35, 50, 28, 18, 10]},
        'genderData': {'labels': ['男', '女', '其他'], 'values': [70, 45, 3]}
    }
    return jsonify(mock_data)

@app.route('/user-management')
@login_required
def user_management():
    return render_template('user_management.html', users=MOCK_USERS)


# --- 运行 ---
if __name__ == '__main__':
    os.makedirs(DATA_DIR, exist_ok=True)
    static_css_dir = os.path.join(BASE_DIR, 'static', 'css')
    static_js_dir = os.path.join(BASE_DIR, 'static', 'js')
    os.makedirs(static_css_dir, exist_ok=True)
    os.makedirs(static_js_dir, exist_ok=True)
    print(f"确保目录存在:\n  Data: {DATA_DIR}\n  Static CSS: {static_css_dir}\n  Static JS: {static_js_dir}")

    # --- 确保模板文件存在 (如果不存在，可以创建一个空的JSON) ---
    if not os.path.exists(INTERROGATION_TEMPLATE_PATH):
        print(f"创建空的审讯模板文件: {INTERROGATION_TEMPLATE_PATH}")
        empty_template = {
          "record_number": "第 N 次", "title": "讯问笔录", "time_start": "", "time_end": "", "location": "",
          "interrogator_signature": "", "interrogator_unit": "", "recorder_signature": "", "recorder_unit": "",
          "person_name": "", "person_gender": "", "person_age": "", "person_dob": "", "person_id_type_number": "",
          "person_address": "", "person_contact": "", "person_hukou": "", "arrival_departure_info": "",
          "questions_answers": [{"q": "问题示例1?", "a": "回答示例1"}, {"q": "问题示例2?", "a": ""}],
          "signature_section": {"person_signature": "被讯问人：", "date": "时    间：    年   月   日"}
        }
        try:
            with open(INTERROGATION_TEMPLATE_PATH, 'w', encoding='utf-8') as f:
                json.dump(empty_template, f, ensure_ascii=False, indent=2)
        except IOError as e:
            print(f"创建空模板文件失败: {e}")


    app.run(debug=True, host='0.0.0.0', port=5001)