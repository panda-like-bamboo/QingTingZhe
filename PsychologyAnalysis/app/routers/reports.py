# app/routers/reports.py
import logging
import json
import asyncio
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import ValidationError # 确保导入 ValidationError

# --- Core App Imports ---
from app.core.config import settings
from app.schemas.report import ReportResponse, ReportData, ReportStatusResponse

# --- Authentication & Database Imports ---
from app.core.deps import get_current_active_user, get_db
from app import models
from app import crud
from app.models.assessment import STATUS_COMPLETE, STATUS_FAILED, STATUS_PENDING, STATUS_PROCESSING

logger = logging.getLogger(settings.APP_NAME)
router = APIRouter()

@router.get(
    "/{assessment_id}",
    response_model=ReportResponse,
    summary="获取指定评估的分析报告 (仅在完成后)",
    tags=["Reports"],
    responses={
        status.HTTP_200_OK: {"description": "成功获取报告，或报告尚未完成/失败"},
        status.HTTP_404_NOT_FOUND: {"description": "评估记录未找到"},
        status.HTTP_403_FORBIDDEN: {"description": "无权访问此报告"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "服务器内部错误"},
    }
)
async def get_report_by_id(
    assessment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    根据评估 ID 获取单个评估报告的详细信息。
    """
    logger.info(f"[Reports Router - Full] User {current_user.username} requesting full report for ID: {assessment_id}")

    try:
        logger.debug(f"[Reports Router - Full] Fetching assessment ID {assessment_id} using crud.assessment.get")
        assessment: models.Assessment | None = await crud.assessment.get(db=db, id=assessment_id)

        if not assessment:
            logger.warning(f"[Reports Router - Full] Assessment ID {assessment_id} NOT FOUND. Raising 404.")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"评估 ID {assessment_id} 不存在。",
            )

        logger.info(f"[Reports Router - Full] Found assessment ID {assessment_id}. Current status: '{assessment.status}'.")

        # --- 权限检查 (根据需要启用) ---
        # if not current_user.is_superuser and assessment.submitter_id != current_user.id:
        #     logger.warning(...)
        #     raise HTTPException(...)

        # --- 检查状态 ---
        if assessment.status != STATUS_COMPLETE:
            status_message_map = {
                STATUS_PENDING: "报告正在等待处理。",
                STATUS_PROCESSING: "报告正在生成中，请稍后。",
                STATUS_FAILED: "报告生成失败。",
            }
            message = status_message_map.get(assessment.status, "报告处于未知或非完成状态。")
            logger.info(f"[Reports Router - Full] Assessment ID {assessment_id} status is '{assessment.status}'. Returning message: '{message}'")
            return ReportResponse(report=None, message=message)

        # --- 状态是 COMPLETE，检查报告文本 ---
        logger.debug(f"[Reports Router - Full] Status is COMPLETE for ID {assessment_id}. Checking report_text.")
        if not assessment.report_text or assessment.report_text.strip() == "":
            logger.error(f"[Reports Router - Full] CRITICAL: Assessment ID {assessment_id} has status COMPLETE but report_text is empty!")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="报告状态与内容不一致，请联系管理员。"
            )

        # --- 状态是 COMPLETE 且文本存在，准备返回数据 ---
        logger.info(f"[Reports Router - Full] Report text found for completed assessment ID {assessment_id}. Preparing response data.")

        # +++ 修改点：在验证前准备数据，并解析 JSON +++
        data_for_validation = assessment.__dict__.copy() # 复制模型属性到字典
        parsed_q_data = None # 初始化为 None
        q_data_str = data_for_validation.get('questionnaire_data')

        if isinstance(q_data_str, str):
            logger.debug("[Reports Router - Full] Attempting to parse questionnaire_data JSON string before validation.")
            try:
                parsed_q_data = json.loads(q_data_str)
                if not isinstance(parsed_q_data, dict): # 确保解析结果是字典
                    logger.warning(f"[Reports Router - Full] Parsed questionnaire_data is not a dictionary (type: {type(parsed_q_data)}). Setting to None.")
                    parsed_q_data = None
                else:
                    logger.debug("[Reports Router - Full] Successfully parsed questionnaire_data into a dictionary.")
            except json.JSONDecodeError:
                logger.error(f"[Reports Router - Full] Failed to decode questionnaire_data JSON string: {q_data_str[:100]}... Setting to None.")
                parsed_q_data = None # 解析失败则设为 None
        elif q_data_str is not None:
            # 如果数据库中不是字符串也不是 None，记录警告
            logger.warning(f"[Reports Router - Full] questionnaire_data from DB is not a string or None (type: {type(q_data_str)}). Attempting to use as is if schema allows, otherwise will be None.")
            # 尝试直接使用，如果 Pydantic 允许的话，否则保持 None
            parsed_q_data = q_data_str if isinstance(q_data_str, dict) else None

        # 将解析后的（或原始的 None）值放回待验证的数据字典中
        data_for_validation['questionnaire_data'] = parsed_q_data
        # +++ 修改结束 +++

        try:
            # --- 修改点：使用准备好的字典进行验证 ---
            # 不再需要 from_attributes=True，因为我们传入的是字典
            report_data = ReportData.model_validate(data_for_validation)
            # --- 修改结束 ---

            # --- 移除这里冗余的 questionnaire_data 解析逻辑 ---
            # if isinstance(assessment.questionnaire_data, str):
            #    ... (这部分逻辑已移到 model_validate 之前) ...
            # --- 移除结束 ---

            logger.info(f"[Reports Router - Full] Successfully built ReportData for ID {assessment_id}.")
            return ReportResponse(report=report_data, message="报告获取成功。")

        except ValidationError as pydantic_err:
            # 捕获 Pydantic 验证错误 (理论上现在不应该因为 questionnaire_data 类型错误了，但可能还有其他字段问题)
            logger.error(f"[Reports Router - Full] Pydantic validation error creating ReportData for ID {assessment_id}: {pydantic_err}", exc_info=True)
            # 记录导致错误的原始数据 (字典形式)
            logger.debug(f"[Reports Router - Full] Data causing validation error: {data_for_validation}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="处理报告数据格式时出错。"
            )

    except HTTPException as http_exc:
         logger.warning(f"[Reports Router - Full] Raising known HTTPException for ID {assessment_id}: Status={http_exc.status_code}, Detail={http_exc.detail}")
         raise http_exc
    except Exception as e:
        logger.exception(f"[Reports Router - Full] Unexpected error processing request for ID {assessment_id}. User: {current_user.username}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取报告时发生未知错误。",
        )

# --- get_report_status 函数 (保持不变) ---
@router.get(
    "/{assessment_id}/status",
    response_model=ReportStatusResponse,
    summary="获取指定评估的处理状态",
    tags=["Reports"],
    responses={
        status.HTTP_200_OK: {"description": "成功获取状态"},
        status.HTTP_404_NOT_FOUND: {"description": "评估记录未找到"},
        status.HTTP_403_FORBIDDEN: {"description": "无权访问此评估状态"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "服务器内部错误"}
    }
)
async def get_report_status(
    assessment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """获取指定评估 ID 的当前处理状态。包含短暂重试以处理可见性延迟。"""
    logger.info(f"[Reports Router - Status] User {current_user.username} requesting status for ID: {assessment_id}")
    max_retries = 2
    retry_delay = 0.5
    for attempt in range(max_retries):
        try:
            logger.debug(f"[Reports Router - Status] Attempt {attempt + 1}/{max_retries}: Fetching assessment ID {assessment_id}")
            assessment = await crud.assessment.get(db=db, id=assessment_id)
            if assessment:
                logger.info(f"[Reports Router - Status] Attempt {attempt + 1}: Found status '{assessment.status}' for ID: {assessment_id}")
                return ReportStatusResponse(status=assessment.status)
            else:
                logger.warning(f"[Reports Router - Status] Attempt {attempt + 1}: crud.assessment.get returned None for ID {assessment_id}.")
                if attempt < max_retries - 1:
                    logger.info(f"[Reports Router - Status] Waiting {retry_delay}s before retrying fetch for ID {assessment_id}...")
                    await asyncio.sleep(retry_delay)
                else:
                    logger.error(f"[Reports Router - Status] All {max_retries} attempts failed to find assessment ID {assessment_id}. Raising 404.")
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="评估记录未找到或暂不可见")
        except HTTPException as http_exc:
             if http_exc.status_code == 404 and attempt == max_retries - 1:
                 raise http_exc
             if http_exc.status_code == 403:
                 raise http_exc
             logger.warning(f"[Reports Router - Status] Caught handled HTTPException during attempt {attempt + 1}: {http_exc.status_code}, Detail: {http_exc.detail}")
             if attempt == max_retries - 1: raise http_exc
        except Exception as e:
            logger.exception(f"[Reports Router - Status] Unexpected error during attempt {attempt + 1} for ID {assessment_id}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="获取报告状态时发生内部错误"
            )
    logger.error(f"[Reports Router - Status] Reached end of function unexpectedly after retries for ID {assessment_id}.")
    raise HTTPException(status_code=500, detail="处理状态请求时发生意外流程错误。")