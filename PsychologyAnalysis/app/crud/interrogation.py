# 文件路径: PsychologyAnalysis/app/crud/interrogation.py

import logging
from typing import Optional, Dict, Any, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, desc  # 确保导入 func 和 desc
from sqlalchemy.exc import SQLAlchemyError

from app.models.interrogation import InterrogationRecord
from app.schemas.interrogation import InterrogationRecordUpdate
from app.core.config import settings

logger = logging.getLogger(settings.APP_NAME)

async def create_interrogation(
    db: AsyncSession, *, interrogator_id: int, basic_info: Dict[str, Any], qas: List[Dict[str, str]]
) -> InterrogationRecord:
    """异步创建一条新的审讯记录。"""
    logger.info(f"CRUD: 准备为审讯员 ID {interrogator_id} 创建新的审讯记录")
    try:
        db_obj = InterrogationRecord(
            interrogator_id=interrogator_id,
            basic_info=basic_info,
            qas=qas,
            status="ongoing"
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        logger.info(f"CRUD: 成功创建审讯记录 ID: {db_obj.id}")
        return db_obj
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(f"CRUD: 创建审讯记录时发生数据库错误: {e}", exc_info=True)
        raise e
    except Exception as e:
        await db.rollback()
        logger.error(f"CRUD: 创建审讯记录时发生意外错误: {e}", exc_info=True)
        raise e

async def get_interrogation(db: AsyncSession, record_id: int) -> Optional[InterrogationRecord]:
    """异步根据 ID 获取审讯记录。"""
    logger.debug(f"CRUD: 尝试查找审讯记录 ID: {record_id}")
    try:
        result = await db.execute(select(InterrogationRecord).filter(InterrogationRecord.id == record_id))
        found_obj = result.scalar_one_or_none()
        if found_obj:
            logger.debug(f"CRUD: 已找到审讯记录 ID: {record_id}")
        else:
            logger.debug(f"CRUD: 未找到审讯记录 ID: {record_id}")
        return found_obj
    except SQLAlchemyError as e:
        logger.error(f"CRUD: 获取审讯记录 ID {record_id} 时发生数据库错误: {e}", exc_info=True)
        raise e

async def update_interrogation(
    db: AsyncSession, *, record_id: int, update_data: InterrogationRecordUpdate
) -> Optional[InterrogationRecord]:
    """异步更新指定的审讯记录。"""
    logger.info(f"CRUD: 准备更新审讯记录 ID: {record_id}")
    db_obj = await get_interrogation(db, record_id=record_id)
    if not db_obj:
        logger.warning(f"CRUD: 更新审讯记录失败，未找到 ID: {record_id}")
        return None
        
    update_dict = update_data.model_dump(exclude_unset=True)
    if not update_dict:
         logger.info(f"CRUD: 没有提供需要更新的字段，审讯记录 ID: {record_id} 未更改。")
         return db_obj

    logger.debug(f"CRUD: 将要更新的字段 (ID: {record_id}): {list(update_dict.keys())}")

    for field, value in update_dict.items():
        setattr(db_obj, field, value)

    db.add(db_obj)
    try:
        await db.commit()
        await db.refresh(db_obj)
        logger.info(f"CRUD: 成功更新审讯记录 ID: {record_id}")
        return db_obj
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(f"CRUD: 更新审讯记录 ID {record_id} 时发生数据库错误: {e}", exc_info=True)
        raise e
    except Exception as e:
        await db.rollback()
        logger.error(f"CRUD: 更新审讯记录 ID {record_id} 时发生意外错误: {e}", exc_info=True)
        raise e

# [+] 新增: 获取审讯记录列表的函数
async def get_multi(db: AsyncSession, *, skip: int = 0, limit: int = 100) -> Tuple[List[InterrogationRecord], int]:
    """
    异步获取审讯记录列表，支持分页，并返回总数。
    """
    logger.info(f"CRUD: 获取审讯记录列表, skip={skip}, limit={limit}")
    try:
        # 查询当前页的记录
        stmt_records = select(InterrogationRecord).order_by(desc(InterrogationRecord.updated_at)).offset(skip).limit(limit)
        result_records = await db.execute(stmt_records)
        records = result_records.scalars().all()
        
        # 查询总记录数
        stmt_count = select(func.count()).select_from(InterrogationRecord)
        result_count = await db.execute(stmt_count)
        total_count = result_count.scalar_one()
        
        logger.info(f"CRUD: 找到 {len(records)} 条审讯记录，总数: {total_count}")
        return list(records), total_count
    except SQLAlchemyError as e:
        logger.error(f"CRUD: 获取审讯记录列表时发生数据库错误: {e}", exc_info=True)
        raise e