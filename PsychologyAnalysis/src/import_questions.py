# 文件路径: src/import_questions.py
import os
import json
import sqlite3
# Correct import assuming data_handler.py is in the same directory (src)
try:
    from data_handler import DataHandler
except ImportError:
    print("Error: data_handler.py not found in the same directory.")
    # Fallback for running directly from PsychologyAnalysis root
    try:
        # 修正：从 src 包导入
        from src.data_handler import DataHandler
    except ImportError:
         print("Error: Could not import DataHandler. Make sure you run this script correctly.")
         exit(1)


def import_questions_from_json():
    """Loads scale questions from JSON files in input/questionnaires/ into the SQLite DB."""
    # 获取项目根目录（假设此脚本在 src 下，根目录是上一级）
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(project_root, "psychology_analysis.db") # 数据库文件在根目录
    handler = DataHandler(db_path=db_path)
    questionnaire_dir = os.path.join(project_root, "input", "questionnaires") # 问卷目录

    print(f"Scanning for JSON questionnaires in: {questionnaire_dir}")

    # 确保目录存在
    if not os.path.isdir(questionnaire_dir):
        print(f"Error: Questionnaire directory not found: {questionnaire_dir}")
        return

    json_files = [f for f in os.listdir(questionnaire_dir) if f.endswith('.json')]
    if not json_files:
        print(f"No .json files found in {questionnaire_dir}")
        return

    imported_count = 0
    error_count = 0

    # --- 更新映射 ---
    # Define mapping from filename (or title) to scale type code and name
    # Prioritize title if available, otherwise use filename mapping
    scale_mapping = {
        "1测你性格最真实的一面.json": {"code": "Personality", "name": "测你性格最真实的一面"},
        "2亲子关系问卷量表.json": {"code": "ParentChild", "name": "亲子关系问卷量表"},
        "3焦虑症自评量表 (SAS).json": {"code": "SAS", "name": "焦虑症自评量表 (SAS)"},
        "4标准量表：抑郁症自测量表 (SDS).json": {"code": "SDS", "name": "抑郁症自测量表 (SDS)"},
        "5人际关系综合诊断量表.json": {"code": "InterpersonalRelationship", "name": "人际关系综合诊断量表"},
        "6情绪稳定性测验量表.json": {"code": "EmotionalStability", "name": "情绪稳定性测验量表"},
        "7汉密尔顿抑郁量表HAMD24.json": {"code": "HAMD24", "name": "汉密尔顿抑郁量表 (HAMD-24)"},
        "8艾森克人格问卷EPQ85成人版.json": {"code": "EPQ85", "name": "艾森克人格问卷 (EPQ-85成人版)"},
        # +++ 添加新量表的映射 +++
        "9开心测试.json": {"code": "HappyTest", "name": "开心测试"},
        # Add more mappings as needed
    }
    # 也可以基于 title 映射，如果 JSON 文件中有 title 字段
    title_mapping = {
        "测你性格最真实的一面": {"code": "Personality", "name": "测你性格最真实的一面"},
        "亲子关系问卷量表": {"code": "ParentChild", "name": "亲子关系问卷量表"},
        "焦虑症自评量表 (SAS)": {"code": "SAS", "name": "焦虑症自评量表 (SAS)"},
        "标准量表：抑郁症自测量表 (SDS)": {"code": "SDS", "name": "抑郁症自测量表 (SDS)"},
        "人际关系综合诊断量表": {"code": "InterpersonalRelationship", "name": "人际关系综合诊断量表"},
        "情绪稳定性测验量表": {"code": "EmotionalStability", "name": "情绪稳定性测验量表"},
        "汉密尔顿抑郁量表HAMD24": {"code": "HAMD24", "name": "汉密尔顿抑郁量表 (HAMD-24)"}, # 移除 .json
        "艾森克人格问卷EPQ85成人版": {"code": "EPQ85", "name": "艾森克人格问卷 (EPQ-85成人版)"}, # 移除 .json
        # +++ 添加新量表的 title 映射 +++
        "开心测试": {"code": "HappyTest", "name": "开心测试"},
    }
    # --- 映射结束 ---


    for json_file in json_files:
        file_path = os.path.join(questionnaire_dir, json_file)
        print(f"\nProcessing file: {json_file}")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Determine scale type code and name
            title = data.get("title")
            scale_info = None
            # 优先使用 title 映射
            if title and title in title_mapping:
                scale_info = title_mapping[title]
            # 其次使用文件名映射
            elif json_file in scale_mapping:
                 scale_info = scale_mapping[json_file]
            # 最后使用后备方案
            else:
                # Fallback: use filename without extension as code and title as name
                scale_code = os.path.splitext(json_file)[0]
                scale_name = title if title else scale_code # Use title if present, else filename part
                scale_info = {"code": scale_code, "name": scale_name}
                print(f"  Warning: No specific mapping found for file '{json_file}' or title '{title}'. Using fallback code='{scale_code}', name='{scale_name}'.")

            questionnaire_type = scale_info["code"]
            scale_display_name = scale_info["name"]

            print(f"  Identified as: Code='{questionnaire_type}', Name='{scale_display_name}'")

            # Clear old questions for this type before inserting new ones (optional but recommended)
            with sqlite3.connect(handler.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM questionnaire_questions WHERE questionnaire_type = ?", (questionnaire_type,))
                conn.commit()
            print(f"  Cleared existing questions for type '{questionnaire_type}'.")


            # Insert questions
            questions_in_file = data.get("questions", [])
            if not questions_in_file:
                 print(f"  Warning: No 'questions' array found in {json_file}")
                 error_count += 1
                 continue

            for question in questions_in_file:
                try:
                    q_num = question["number"]
                    q_text = question["text"]
                    # Prepare options as JSON string, ensuring 'text' and 'score' keys exist
                    # Provide defaults if keys are missing in the source JSON
                    options_list = []
                    raw_options = question.get("options", [])
                    if isinstance(raw_options, list): # Check if options is actually a list
                        options_list = [
                            {"text": opt.get("text", "N/A"), "score": opt.get("score", 0)}
                            for opt in raw_options
                            if isinstance(opt, dict) # Ensure each option is a dictionary
                        ]
                    else:
                        print(f"    Warning: 'options' for question {q_num} is not a list, skipping options.")

                    options_json = json.dumps(options_list, ensure_ascii=False)

                    # Use the enhanced insert_question method
                    handler.insert_question(
                        questionnaire_type,
                        q_num,
                        q_text,
                        options_json, # Pass JSON string directly
                        scale_display_name # Pass the scale name
                        )
                    imported_count += 1
                except KeyError as ke:
                     print(f"    Error processing question in {json_file}: Missing key {ke}")
                     error_count += 1
                except TypeError as te:
                    print(f"    Error processing options for question {question.get('number', 'N/A')} in {json_file}: Likely not a list of dicts. Details: {te}")
                    error_count += 1
                except Exception as e_inner:
                     print(f"    Error processing question {question.get('number', 'N/A')} in {json_file}: {e_inner}")
                     error_count += 1

        except json.JSONDecodeError as jde:
            print(f"  Error decoding JSON from {json_file}: {jde}")
            error_count += 1
        except Exception as e_outer:
            print(f"  Error processing file {json_file}: {e_outer}")
            error_count += 1

    print(f"\nImport finished. Successfully imported {imported_count} questions.")
    if error_count > 0:
        print(f"Encountered {error_count} errors during import.")

if __name__ == "__main__":
    import_questions_from_json()
    # Optional: Check DB content after import
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_file_path = os.path.join(project_root, "psychology_analysis.db")
    try:
        # 修正：从 src 包导入
        from src.data_handler import check_db_content
        check_db_content(db_file_path)
    except ImportError:
         print("\nRun `python src/data_handler.py` to check database content.")
    except Exception as e:
        print(f"\nError checking DB content after import: {e}")