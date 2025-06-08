# 文件路径: PsychologyAnalysis/app/routers/admin.py

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query, Body, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import class_mapper
from pydantic import BaseModel, Field
from openai import OpenAI

# --- 核心应用导入 ---
from app.core.config import settings
from app.core.deps import get_db, get_current_active_superuser
from app import crud, models, schemas
# --- 导入专项指导方案的响应模型 ---
from app.schemas.guidance import GuidanceWithReportResponse, ReportDataForGuidance

# --- AI & 工具函数导入 ---
try:
    from src.guidance_generator import generate_guidance
except ImportError:
    generate_guidance = None
    logging.getLogger(settings.APP_NAME).warning("未能导入 src.guidance_generator.generate_guidance，相关功能将不可用。")

try:
    from src.interrogation_ai import suggest_next_question
except ImportError:
    suggest_next_question = None
    logging.getLogger(settings.APP_NAME).warning("未能导入 src.interrogation_ai.suggest_next_question，相关功能将不可用。")

# --- 日志和路由设置 ---
logger = logging.getLogger(settings.APP_NAME)
# [核心修改]: 移除了 prefix="/admin"，使所有路径成为根路径下的绝对路径
router = APIRouter(
    tags=["后台管理 (Admin)"],
    dependencies=[Depends(get_current_active_superuser)]
)


# --- 辅助函数 ---
def alchemy_to_dict(obj: Any) -> Dict[str, Any]:
    """将SQLAlchemy对象转换为字典。"""
    if not obj:
        return {}
    column_names = [c.key for c in class_mapper(obj.__class__).columns]
    return {c: getattr(obj, c) for c in column_names}

def get_ai_client():
    """依赖注入函数：获取一个配置好的AI客户端实例。"""
    if not settings.DASHSCOPE_API_KEY:
        logger.error("AI服务未配置：环境变量 DASHSCOPE_API_KEY 未设置。")
        raise HTTPException(status_code=503, detail="AI服务未配置 (缺少API Key)")
    return OpenAI(api_key=settings.DASHSCOPE_API_KEY, base_url="https://dashscope.aliyuncs.com/compatible-mode/v1")


# ====================================================================
# --- 评估记录管理 ---
# ====================================================================

@router.get(
    "/assessments/search",
    response_model=List[schemas.AssessmentSummary],
    summary="查询评估记录"
)
async def search_assessments(
    id_card: Optional[str] = Query(None, description="要查询的身份证号 (可选，不填则返回所有)"),
    db: AsyncSession = Depends(get_db)
):
    """
    根据身份证号查询评估记录。如果未提供身份证号，则返回最近的100条评估记录。
    """
    try:
        if id_card:
            logger.info(f"管理员正在按身份证号 '{id_card}' 查询评估记录")
            assessments = await crud.assessment.get_assessments_by_id_card(db, id_card=id_card)
        else:
            logger.info("管理员正在获取所有评估记录")
            assessments = await crud.assessment.get_multi(db, limit=100)
        
        if not assessments:
            return []
            
        logger.info(f"查询到 {len(assessments)} 条评估记录")
        return [schemas.AssessmentSummary.model_validate(a, from_attributes=True) for a in assessments]
    except Exception as e:
        logger.error(f"查询评估时出错 (ID卡: '{id_card}'): {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="查询评估记录时发生错误")


# ====================================================================
# --- 数据统计与AI分析 ---
# ====================================================================

@router.get(
    "/stats/demographics",
    response_model=schemas.DemographicsStats,
    summary="获取用户人口统计数据"
)
async def get_demographics_stats(db: AsyncSession = Depends(get_db)):
    """
    获取系统中所有已完成评估用户的年龄和性别分布数据。
    """
    logger.info("管理员请求人口统计数据")
    try:
        age_data = await crud.stats.get_age_distribution(db)
        gender_data = await crud.stats.get_gender_distribution(db)
        return schemas.DemographicsStats(ageData=age_data, genderData=gender_data)
    except Exception as e:
        logger.error(f"获取人口统计数据时出错: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取统计数据时发生错误")

@router.post("/stats/ai-analysis", response_model=schemas.AIAnalysisResponse, summary="对统计数据进行AI智能分析")
async def perform_ai_analysis(
    request_data: schemas.AIAnalysisRequest,
    ai_client: OpenAI = Depends(get_ai_client),
    current_user: models.User = Depends(get_current_active_superuser)
):
    """
    接收人口统计数据，调用大语言模型生成专业的分析报告和洞察。
    """
    logger.info(f"管理员 {current_user.username} 请求对统计数据进行AI分析")
    age_data = request_data.demographics.ageData
    gender_data = request_data.demographics.genderData
    age_distribution_str = ", ".join([f"'{label}': {value}人" for label, value in zip(age_data.labels, age_data.values)])
    gender_distribution_str = ", ".join([f"'{label}': {value}人" for label, value in zip(gender_data.labels, gender_data.values)])
    
    prompt = f"""
    作为一名资深的警务数据分析专家，请根据以下系统用户的人口统计数据，撰写一份简洁、深刻的分析报告。
    **任务要求:**
    1.  **解读数据**: 不要仅仅复述数据，要解读数据背后可能反映的现象。
    2.  **识别特征**: 指出用户群体的主要特征。
    3.  **提出洞察**: 结合警务工作场景，提出1-2个基于这些数据特征的潜在洞察或管理建议。
    4.  **语言专业**: 使用专业、客观的分析语言。
    5.  **格式简洁**: 直接输出分析报告正文，无需标题。
    **原始数据:**
    - **年龄分布**: {age_distribution_str}
    - **性别分布**: {gender_distribution_str}
    **分析报告:**
    """
    messages = [{"role": "system", "content": "你是一位数据分析专家，擅长从数据中挖掘警务相关的洞察。"}, {"role": "user", "content": prompt}]
    
    try:
        completion = ai_client.chat.completions.create(model=settings.TEXT_MODEL, messages=messages, temperature=0.5, max_tokens=1000)
        analysis_text = completion.choices[0].message.content
        logger.info("AI 数据分析成功完成")
        return schemas.AIAnalysisResponse(analysis_text=analysis_text)
    except Exception as e:
        logger.error(f"调用AI进行数据分析时出错: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"AI分析服务出错: {e}")


# ====================================================================
# --- 辅助智能审讯笔录 ---
# ====================================================================

@router.post("/interrogation/start", response_model=schemas.InterrogationRecordRead, status_code=status.HTTP_201_CREATED, summary="开始新的审讯")
async def start_interrogation(basic_info: schemas.InterrogationBasicInfo = Body(...), db: AsyncSession = Depends(get_db), current_admin: models.User = Depends(get_current_active_superuser)):
    """
    根据前端提供的基本信息，创建一个新的审讯记录。
    """
    logger.info(f"管理员 {current_admin.username} 正在为 '{basic_info.person_name}' 开始新的审讯")
    filled_basic_info = basic_info.model_dump()
    initial_qas = []
    try:
        new_record = await crud.interrogation.create_interrogation(db=db, interrogator_id=current_admin.id, basic_info=filled_basic_info, qas=initial_qas)
        return schemas.InterrogationRecordRead.model_validate(new_record, from_attributes=True)
    except Exception as e:
        logger.error(f"创建审讯记录时出错: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="无法开始新的审讯记录")

@router.post("/interrogation/{record_id}/suggest", response_model=List[str], summary="获取下一个审讯问题的 AI 建议")
async def suggest_interrogation_question(record_id: int, current_qas: List[schemas.InterrogationQAInput] = Body(...), db: AsyncSession = Depends(get_db)):
    """
    根据当前的审讯历史，调用AI生成下一步的建议问题。
    """
    logger.info(f"管理员请求审讯记录 ID: {record_id} 的下一个问题建议")
    if not suggest_next_question:
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="AI 建议功能未配置")
    record = await crud.interrogation.get_interrogation(db, record_id=record_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="审讯记录未找到")
    
    basic_info = record.basic_info or {}
    try:
        history_dicts = [qa.model_dump() for qa in current_qas]
        suggestions = suggest_next_question(basic_info=basic_info, history=history_dicts)
        return suggestions
    except Exception as e:
        logger.error(f"生成审讯建议时出错 (ID: {record_id}): {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取 AI 建议时出错")

@router.put("/interrogation/{record_id}", response_model=schemas.InterrogationRecordRead, summary="保存更新后的审讯笔录")
async def save_interrogation(record_id: int, record_update: schemas.InterrogationRecordUpdate = Body(...), db: AsyncSession = Depends(get_db)):
    """
    保存对审讯记录的更改，包括基本信息和问答对。
    """
    logger.info(f"管理员正在保存审讯记录 ID: {record_id}")
    try:
        updated_record = await crud.interrogation.update_interrogation(db=db, record_id=record_id, update_data=record_update)
        if not updated_record:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="审讯记录未找到")
        return schemas.InterrogationRecordRead.model_validate(updated_record, from_attributes=True)
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"保存审讯记录时出错 (ID: {record_id}): {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="保存审讯记录时发生错误")

@router.get("/interrogations/{record_id}", response_model=schemas.InterrogationRecordRead, summary="获取单个审讯记录详情")
async def get_interrogation_record(record_id: int, db: AsyncSession = Depends(get_db)):
    """
    根据ID获取单个完整的审讯记录详情。
    """
    logger.info(f"管理员请求审讯记录详情，ID: {record_id}")
    record = await crud.interrogation.get_interrogation(db, record_id=record_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"未找到 ID 为 {record_id} 的审讯记录")
    return record

@router.get("/interrogations", response_model=schemas.InterrogationListResponse, summary="获取审讯记录列表")
async def list_interrogations(db: AsyncSession = Depends(get_db), skip: int = Query(0, ge=0), limit: int = Query(10, ge=1, le=100)):
    """
    分页获取审讯记录列表的摘要信息。
    """
    logger.info(f"管理员请求审讯记录列表，skip={skip}, limit={limit}")
    try:
        records, total_count = await crud.interrogation.get_multi(db=db, skip=skip, limit=limit)
        summaries = [schemas.InterrogationSummary.from_orm(rec) for rec in records]
        return schemas.InterrogationListResponse(total=total_count, records=summaries)
    except Exception as e:
        logger.error(f"获取审讯记录列表时出错: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取审讯记录列表失败")


# ====================================================================
# --- 专项指导方案 ---
# ====================================================================

async def get_guidance_for_person(
    db: AsyncSession,
    id_card: str,
    guidance_type: str
) -> GuidanceWithReportResponse:
    """
    为特定人员生成指导方案的内部核心函数。
    它会查找最新的评估报告，并调用AI生成指导方案，最终返回一个结构化的响应。
    """
    logger.info(f"为身份证号 '{id_card}' 生成 '{guidance_type}' 指导方案")
    if not generate_guidance:
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="指导方案生成功能未配置")

    assessment = await crud.assessment.get_latest_completed_by_id_card(db, id_card=id_card)
    if not assessment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到该身份证号对应的已完成评估报告")
    if not assessment.report_text:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="找到评估记录，但报告内容为空")

    try:
        guidance_text = generate_guidance(report_text=assessment.report_text, scenario=guidance_type)
        if not guidance_text:
            raise ValueError("AI未能生成指导方案文本")
        
        logger.info(f"成功为身份证号 '{id_card}' 生成 '{guidance_type}' 指导方案")

        # 使用 ReportDataForGuidance 模型来验证和构造报告部分
        # from_attributes=True 会自动处理 SQLAlchemy ORM 对象到 Pydantic 模型的转换
        report_data_for_response = ReportDataForGuidance.model_validate(assessment, from_attributes=True)

        return GuidanceWithReportResponse(
            report=report_data_for_response,
            guidance=guidance_text
        )

    except ValueError as ve:
        logger.error(f"生成指导方案时值错误: {ve}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"生成指导方案失败: {ve}")
    except Exception as e:
        logger.error(f"生成指导方案时发生未知错误: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="生成指导方案时发生内部错误")

@router.get(
    "/guidance/{scenario}",
    response_model=GuidanceWithReportResponse,
    summary="获取专项指导方案"
)
async def get_specific_guidance(
    scenario: str,
    id_card: str = Query(..., description="查询对象的身份证号"),
    db: AsyncSession = Depends(get_db)
):
    """
    统一的专项指导方案生成接口。
    - scenario: 'petitioner' (上访户), 'juvenile' (未成年人), 'police' (民辅警)
    """
    if scenario not in ["petitioner", "juvenile", "police"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="无效的指导方案场景。有效值为: petitioner, juvenile, police")
    return await get_guidance_for_person(db, id_card, scenario)


# ====================================================================
# --- 用户管理 ---
# ====================================================================

@router.get("/users", response_model=schemas.UserListResponse, summary="获取用户列表")
async def list_users(db: AsyncSession = Depends(get_db), skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=200)):
    """
    分页获取系统中的所有用户列表。
    """
    logger.info(f"管理员请求用户列表，skip={skip}, limit={limit}")
    try:
        users, total_count = await crud.user.get_users(db, skip=skip, limit=limit)
        return schemas.UserListResponse(total=total_count, users=[schemas.User.model_validate(u, from_attributes=True) for u in users])
    except Exception as e:
        logger.error(f"获取用户列表时出错: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取用户列表失败")

@router.patch("/users/{user_id}", response_model=schemas.User, summary="更新用户信息 (管理员)")
async def update_user_admin(user_id: int, user_in: schemas.UserUpdateAdmin = Body(...), db: AsyncSession = Depends(get_db), current_admin: models.User = Depends(get_current_active_superuser)):
    """
    管理员更新指定用户的部分或全部信息，如用户名、角色等。
    """
    logger.info(f"管理员 {current_admin.username} 正在更新用户 ID: {user_id}")
    db_user = await crud.user.get_user(db, user_id=user_id)
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户未找到")
    try:
        updated_user = await crud.user.update_user_admin(db=db, db_user=db_user, user_in=user_in)
        return schemas.User.model_validate(updated_user, from_attributes=True)
    except Exception as e:
        logger.error(f"管理员更新用户 ID {user_id} 时出错: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="更新用户信息失败")


# ====================================================================
# --- 属性标签管理 (CRUD) ---
# ====================================================================

@router.post("/attributes", response_model=schemas.AttributeRead, status_code=status.HTTP_201_CREATED, summary="创建新属性标签")
async def create_new_attribute(attribute_in: schemas.AttributeCreate, db: AsyncSession = Depends(get_db)):
    """
    创建一个新的属性标签，用于后续给评估记录打标。
    """
    logger.info(f"管理员尝试创建属性: Name='{attribute_in.name}', Category='{attribute_in.category}'")
    try:
        return await crud.attribute.create_attribute(db=db, attribute_in=attribute_in)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(ve))
    except Exception as e:
        logger.error(f"创建属性时发生意外错误: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="创建属性失败")

@router.get("/attributes", response_model=List[schemas.AttributeRead], summary="获取属性标签列表")
async def list_attributes(db: AsyncSession = Depends(get_db), skip: int = 0, limit: int = 100, category: Optional[str] = None):
    """
    获取所有属性标签，可按分类进行筛选。
    """
    logger.info(f"管理员获取属性列表, skip={skip}, limit={limit}, category={category}")
    return await crud.attribute.get_attributes(db=db, skip=skip, limit=limit, category=category)

@router.get("/attributes/{attribute_id}", response_model=schemas.AttributeRead, summary="获取单个属性详情")
async def read_attribute(attribute_id: int, db: AsyncSession = Depends(get_db)):
    """
    获取指定ID的属性标签的详细信息。
    """
    logger.info(f"管理员请求属性详情 ID: {attribute_id}")
    db_attribute = await crud.attribute.get_attribute(db, attribute_id=attribute_id)
    if db_attribute is None:
        logger.warning(f"管理员请求的属性 ID: {attribute_id} 未找到")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="属性未找到")
    return db_attribute

@router.put("/attributes/{attribute_id}", response_model=schemas.AttributeRead, summary="更新属性标签")
async def update_existing_attribute(attribute_id: int, attribute_in: schemas.AttributeUpdate, db: AsyncSession = Depends(get_db)):
    """
    更新一个已存在的属性标签的名称或分类。
    """
    logger.info(f"管理员尝试更新属性 ID: {attribute_id}")
    db_attribute = await crud.attribute.get_attribute(db, attribute_id=attribute_id)
    if not db_attribute:
        raise HTTPException(status_code=404, detail="属性未找到")
    try:
        return await crud.attribute.update_attribute(db=db, db_attribute=db_attribute, attribute_in=attribute_in)
    except ValueError as ve:
        raise HTTPException(status_code=409, detail=str(ve))

@router.delete("/attributes/{attribute_id}", status_code=status.HTTP_204_NO_CONTENT, summary="删除属性标签")
async def delete_existing_attribute(attribute_id: int, db: AsyncSession = Depends(get_db)):
    """
    删除一个属性标签。如果该标签已被使用，可能会删除失败。
    """
    logger.warning(f"管理员尝试删除属性 ID: {attribute_id}")
    deleted = await crud.attribute.delete_attribute(db=db, attribute_id=attribute_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="属性未找到或无法删除")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ====================================================================
# --- 评估与属性关联管理 ---
# ====================================================================

class AssessmentAttributesUpdate(BaseModel):
    attribute_ids: List[int] = Field(..., description="要为评估记录设置的完整属性ID列表，此操作将覆盖所有现有属性关联。")

@router.put("/assessments/{assessment_id}/attributes", response_model=schemas.AssessmentSummary, summary="设置评估记录的所有属性标签")
async def set_assessment_attributes_endpoint(assessment_id: int, attributes_in: AssessmentAttributesUpdate = Body(...), db: AsyncSession = Depends(get_db)):
    """
    一次性设置某条评估记录的所有属性标签。前端发送一个包含所有期望关联的属性ID的列表。
    """
    logger.info(f"管理员正在为评估 ID {assessment_id} 设置属性列表: {attributes_in.attribute_ids}")
    updated_assessment = await crud.assessment.set_assessment_attributes(db=db, assessment_id=assessment_id, attribute_ids=attributes_in.attribute_ids)
    if updated_assessment is None:
        raise HTTPException(status_code=404, detail="评估记录未找到")
    return schemas.AssessmentSummary.model_validate(updated_assessment, from_attributes=True)