# -*- coding: utf-8 -*-
# FILE: app/crud/assessment.py (修改后，包含属性关联操作)
import logging
import traceback
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
import sqlite3

# --- 模型和配置导入 ---
from app.models.assessment import Assessment, STATUS_COMPLETE, STATUS_PENDING, STATUS_PROCESSING, STATUS_FAILED
# +++ 导入 Attribute 模型 +++
from app.models.attribute import Attribute
# ++++++++++++++++++++++++
from app.core.config import settings

logger = logging.getLogger(settings.APP_NAME)

# --- 评估记录 (Assessment) 的 CRUD 操作 ---

async def get(db: AsyncSession, id: int) -> Optional[Assessment]:
    """
    异步根据 ID 获取评估记录。
    """
    logger.debug(f"CRUD GET: 尝试查找 ID 为 {id} 的评估记录")
    try:
        # 使用 SQLAlchemy 2.0 风格的 select
        result = await db.execute(select(Assessment).filter(Assessment.id == id))
        found_obj = result.scalar_one_or_none()
        if found_obj:
            logger.debug(f"CRUD GET: 已找到 ID 为 {id} 的评估记录")
        else:
            logger.debug(f"CRUD GET: 在数据库中未找到 ID 为 {id} 的评估记录")
        return found_obj
    except SQLAlchemyError as e:
        logger.error(f"CRUD GET: 获取评估记录 ID {id} 时发生数据库错误: {e}", exc_info=True)
        # 不在 CRUD 层抛出 HTTPException，让上层调用者处理
        raise e # 或者根据调用者期望返回 None

async def create(db: AsyncSession, **kwargs: Any) -> Assessment:
    """
    异步创建一条新的评估记录。
    kwargs 应包含 Assessment 模型所需的所有字段（除了自动生成的 id, created_at, updated_at）。
    确保在成功时返回带有 ID 的对象，否则引发异常。
    """
    logger.info(f"CRUD CREATE: 准备为 '{kwargs.get('subject_name', '未知主题')}' 创建评估记录")
    try:
        # 移除不允许由用户指定的字段，或由数据库自动处理的字段
        kwargs.pop('id', None)
        kwargs.pop('created_at', None)
        kwargs.pop('updated_at', None)
        # 确保 status 使用默认值 'pending'
        if 'status' in kwargs:
            logger.warning("CRUD CREATE: 在参数中提供了 'status' 字段，将忽略并使用模型默认值。")
            kwargs.pop('status', None)
        # --- 移除 attributes 字段，关联应单独处理 ---
        if 'attributes' in kwargs:
             logger.warning("CRUD CREATE: 在参数中提供了 'attributes' 字段，应通过关联函数处理，已忽略。")
             kwargs.pop('attributes', None)
        # -----------------------------------------

        db_obj = Assessment(**kwargs)
        logger.debug("CRUD CREATE: 评估对象已在内存中创建。")
    except TypeError as te:
        logger.error(f"CRUD CREATE: 创建 Assessment 实例时发生 TypeError。提供的参数: {kwargs}", exc_info=True)
        raise TypeError(f"模型初始化字段不匹配或类型错误: {te}") from te

    db.add(db_obj)
    logger.debug("CRUD CREATE: 评估对象已添加到 SQLAlchemy 会话中。")

    try:
        logger.info("CRUD CREATE: 尝试提交数据库事务以保存新的评估记录...")
        await db.commit()
        logger.info("CRUD CREATE: 数据库提交成功。")

        # 验证对象是否仍在会话中（健全性检查）
        if db_obj not in db and hasattr(db, 'is_active') and db.is_active:
             logger.error("CRUD CREATE: 严重错误 - 对象在成功提交后意外地从会话中移除！")
             await db.rollback() # 尽管提交成功，但状态异常，回滚可能意义不大，但记录错误
             raise SQLAlchemyError("对象在提交后从会话中丢失")

        logger.debug(f"CRUD CREATE: 尝试刷新对象状态。刷新前的对象 ID (如果内存中存在): {getattr(db_obj, 'id', 'N/A')}")
        await db.refresh(db_obj)
        logger.info(f"CRUD CREATE: 评估对象已成功刷新。")

        # 验证 ID 是否已分配
        if db_obj.id is None:
            logger.critical(f"CRUD CREATE: 严重错误 - 对象已刷新但其 ID 仍为 None！回滚可能无效，需检查数据库。")
            # 回滚可能无法撤销已提交的更改，但尝试一下
            try: await db.rollback()
            except: pass
            raise SQLAlchemyError("数据库在提交和刷新操作后未能成功分配 ID")

        logger.info(f"CRUD CREATE: 成功创建并刷新评估记录，最终 ID: {db_obj.id}")
        return db_obj

    except (IntegrityError, sqlite3.IntegrityError) as ie:
        error_msg = f"数据库完整性错误: {ie}"
        logger.error(f"CRUD CREATE: {error_msg}", exc_info=False) # 通常不需要完整堆栈
        logger.info("CRUD CREATE: 由于发生完整性错误，正在回滚会话...")
        await db.rollback()
        # 抛出更具体的错误给上层
        raise IntegrityError(f"数据保存冲突或违反约束: {ie}", orig=ie, params=kwargs) from ie
    except (SQLAlchemyError, sqlite3.OperationalError) as db_err: # 捕获更广泛的 DB 错误
        error_msg = f"数据库操作错误: {type(db_err).__name__} - {db_err}"
        logger.error(f"CRUD CREATE: {error_msg}", exc_info=True)
        logger.info("CRUD CREATE: 由于发生数据库错误，正在回滚会话...")
        await db.rollback()
        raise SQLAlchemyError(f"数据库操作失败: {db_err}") from db_err
    except Exception as e: # 捕获其他意外错误
        error_msg = f"创建评估记录期间发生意外错误: {e}"
        logger.error(f"CRUD CREATE: {error_msg}", exc_info=True)
        logger.info("CRUD CREATE: 由于发生一般错误，正在回滚会话...")
        try:
            await db.rollback()
        except Exception as rollback_err:
            logger.error(f"CRUD CREATE: 在错误处理中尝试回滚会话时再次发生错误: {rollback_err}", exc_info=True)
        raise e # 重新抛出原始错误

async def update_status(db: AsyncSession, assessment_id: int, new_status: str) -> Optional[Assessment]:
    """仅更新指定评估记录的状态。"""
    logger.info(f"CRUD UPDATE STATUS: 尝试将评估记录 ID {assessment_id} 的状态更新为 '{new_status}'")
    db_obj = await get(db, id=assessment_id)
    if not db_obj:
        logger.warning(f"CRUD UPDATE STATUS: 未找到评估记录 ID {assessment_id}。无法更新状态。")
        return None

    if db_obj.status == new_status:
        logger.info(f"CRUD UPDATE STATUS: 评估记录 ID {assessment_id} 的状态已经是 '{new_status}'，无需更新。")
        return db_obj

    logger.debug(f"CRUD UPDATE STATUS: 找到评估记录 ID {assessment_id}。当前状态: '{db_obj.status}'。正在更新为 '{new_status}'。")
    db_obj.status = new_status
    db.add(db_obj) # 将更改添加到会话

    try:
        logger.info(f"CRUD UPDATE STATUS: 尝试提交数据库事务以更新状态 (ID: {assessment_id}, 新状态: {new_status})...")
        await db.commit()
        logger.info(f"CRUD UPDATE STATUS: 数据库提交成功，状态已更新 (ID: {assessment_id})。")
        await db.refresh(db_obj)
        logger.info(f"CRUD UPDATE STATUS: 评估记录对象 ID {assessment_id} 在状态更新后已刷新。")
        return db_obj
    except (sqlite3.OperationalError, sqlite3.IntegrityError, SQLAlchemyError) as db_err: # 捕获可能的数据库错误
        error_msg = f"更新状态时数据库错误 (ID: {assessment_id}): {type(db_err).__name__} - {db_err}"
        logger.error(f"CRUD UPDATE STATUS: {error_msg}", exc_info=True)
        logger.info(f"CRUD UPDATE STATUS: 由于数据库错误，正在回滚会话 (ID: {assessment_id})...")
        await db.rollback()
        raise db_err # 重新抛出错误
    except Exception as e:
        error_msg = f"更新状态期间发生一般错误 (ID: {assessment_id}): {e}"
        logger.error(f"CRUD UPDATE STATUS: {error_msg}", exc_info=True)
        logger.info(f"CRUD UPDATE STATUS: 由于一般错误，正在回滚会话 (ID: {assessment_id})...")
        await db.rollback()
        raise e

async def update_report_text(db: AsyncSession, assessment_id: int, report_text: str) -> Optional[Assessment]:
    """仅更新指定评估记录的 report_text 字段。"""
    logger.info(f"CRUD UPDATE REPORT TEXT: 尝试更新评估记录 ID: {assessment_id} 的报告文本")
    db_obj = await get(db, id=assessment_id)
    if not db_obj:
        logger.warning(f"CRUD UPDATE REPORT TEXT: 未找到评估记录 ID {assessment_id}。无法更新报告。")
        return None

    # 比较之前，确保两个值都是字符串类型（如果 report_text 可能为 None）
    current_report = db_obj.report_text if db_obj.report_text is not None else ""
    new_report = report_text if report_text is not None else ""

    if current_report == new_report:
         logger.info(f"CRUD UPDATE REPORT TEXT: 评估记录 ID {assessment_id} 的报告文本未更改，无需更新。")
         return db_obj

    logger.debug(f"CRUD UPDATE REPORT TEXT: 找到评估记录 ID {assessment_id}。正在更新 report_text。")
    db_obj.report_text = report_text # 更新为传入的值，可以是 None
    db.add(db_obj) # 将更改添加到会话

    try:
        logger.info(f"CRUD UPDATE REPORT TEXT: 尝试提交数据库事务以更新报告文本 (ID: {assessment_id})...")
        await db.commit()
        logger.info(f"CRUD UPDATE REPORT TEXT: 数据库提交成功，报告文本已更新 (ID: {assessment_id})。")
        await db.refresh(db_obj)
        logger.info(f"CRUD UPDATE REPORT TEXT: 评估记录对象 ID {assessment_id} 在报告更新后已刷新。")
        return db_obj
    except (sqlite3.OperationalError, sqlite3.IntegrityError, SQLAlchemyError) as db_err:
        error_msg = f"更新报告文本时数据库错误 (ID: {assessment_id}): {type(db_err).__name__} - {db_err}"
        logger.error(f"CRUD UPDATE REPORT TEXT: {error_msg}", exc_info=True)
        logger.info(f"CRUD UPDATE REPORT TEXT: 由于数据库错误，正在回滚会话 (ID: {assessment_id})...")
        await db.rollback()
        raise db_err
    except Exception as e:
        error_msg = f"更新报告文本期间发生一般错误 (ID: {assessment_id}): {e}"
        logger.error(f"CRUD UPDATE REPORT TEXT: {error_msg}", exc_info=True)
        logger.info(f"CRUD UPDATE REPORT TEXT: 由于一般错误，正在回滚会话 (ID: {assessment_id})...")
        await db.rollback()
        raise e

# --- 后台管理查询函数 ---

async def get_assessments_by_id_card(db: AsyncSession, id_card: str) -> List[Assessment]:
    """
    异步根据身份证号获取所有相关的评估记录列表，按创建时间降序排列。
    """
    logger.info(f"CRUD: 尝试按身份证号 '{id_card}' 查找评估记录")
    if not id_card:
        logger.warning("CRUD: 尝试按空身份证号查询，返回空列表。")
        return []
    try:
        stmt = select(Assessment).filter(Assessment.id_card == id_card).order_by(desc(Assessment.created_at))
        result = await db.execute(stmt)
        assessments = result.scalars().all()
        logger.info(f"CRUD: 找到 {len(assessments)} 条身份证号为 '{id_card}' 的评估记录")
        return list(assessments) # 确保返回列表
    except SQLAlchemyError as e:
        logger.error(f"CRUD: 按身份证号 '{id_card}' 获取评估记录时发生数据库错误: {e}", exc_info=True)
        raise e

async def get_latest_completed_by_id_card(db: AsyncSession, id_card: str) -> Optional[Assessment]:
    """
    异步根据身份证号获取最新一条状态为 'complete' 的评估记录。
    """
    logger.info(f"CRUD: 尝试按身份证号 '{id_card}' 查找最新的已完成评估记录")
    if not id_card:
         logger.warning("CRUD: 尝试按空身份证号查询最新完成记录，返回 None。")
         return None
    try:
        stmt = (
            select(Assessment)
            .filter(Assessment.id_card == id_card)
            .filter(Assessment.status == STATUS_COMPLETE) # 使用导入的状态常量
            .order_by(desc(Assessment.created_at)) # 按创建时间降序排列
            .limit(1) # 只取最新的一条
        )
        result = await db.execute(stmt)
        assessment = result.scalar_one_or_none()
        if assessment:
            logger.info(f"CRUD: 找到身份证号 '{id_card}' 的最新已完成评估记录 ID: {assessment.id}")
        else:
            logger.info(f"CRUD: 未找到身份证号 '{id_card}' 的已完成评估记录")
        return assessment
    except SQLAlchemyError as e:
        logger.error(f"CRUD: 按身份证号 '{id_card}' 获取最新已完成评估时发生数据库错误: {e}", exc_info=True)
        raise e

# --- +++ 新增：处理评估与属性关联的 CRUD 函数 +++ ---

async def add_attribute_to_assessment(
    db: AsyncSession, *, assessment_id: int, attribute_id: int
) -> Optional[Assessment]:
    """
    将一个属性关联到一个评估记录（通过 ID）。

    Args:
        db: 数据库会话。
        assessment_id: 评估记录的 ID。
        attribute_id: 要关联的属性的 ID。

    Returns:
        更新后的 Assessment 对象 (如果成功) 或 None (如果任一 ID 未找到)。
    """
    logger.info(f"CRUD Assoc: 尝试将属性 ID {attribute_id} 添加到评估 ID {assessment_id}")
    # 1. 获取评估对象
    assessment = await get(db, id=assessment_id)
    if not assessment:
        logger.warning(f"CRUD Assoc: 未找到评估 ID {assessment_id}，无法添加属性。")
        return None

    # 2. 获取属性对象 (需要导入 crud.attribute)
    try:
        from app.crud import attribute as crud_attribute # 在函数内部导入以避免循环依赖问题
    except ImportError:
         logger.error("CRUD Assoc: 无法导入 crud.attribute 模块！")
         raise RuntimeError("Attribute CRUD module is not available.")

    attribute = await crud_attribute.get_attribute(db, attribute_id=attribute_id)
    if not attribute:
        logger.warning(f"CRUD Assoc: 未找到属性 ID {attribute_id}，无法添加到评估 {assessment_id}。")
        return None # 返回 None 表示属性未找到，或者可以返回 assessment 让调用者知道

    # 3. 检查是否已关联
    #    注意：直接检查 assessment.attributes 需要 ORM 加载关联数据，
    #    对于仅添加操作，可以直接尝试添加，让数据库处理唯一性约束（如果有）。
    #    或者，先查询关联表是否存在记录 (更安全但多一次查询)。
    #    这里我们直接尝试添加，依赖于数据库的复合主键或唯一约束。
    if attribute in assessment.attributes: # 如果已加载，可以检查
        logger.debug(f"CRUD Assoc: 属性 ID {attribute.id} 已关联到评估 ID {assessment.id}，无需重复添加。")
        return assessment

    # 4. 添加关联
    assessment.attributes.append(attribute) # SQLAlchemy 会在 commit 时处理关联表的插入
    db.add(assessment) # 标记 assessment 对象已更改（虽然 append 通常会自动标记）

    try:
        await db.commit()
        # 提交后，assessment.attributes 应该会包含新添加的属性 (如果 lazy loading 策略允许或 refresh)
        # await db.refresh(assessment) # 刷新以确保看到最新的关联列表
        logger.info(f"CRUD Assoc: 成功将属性 ID {attribute.id} 添加到评估 ID {assessment.id}")
        return assessment
    except (IntegrityError, sqlite3.IntegrityError) as e: # 捕获可能的复合主键冲突
        await db.rollback()
        logger.error(f"CRUD Assoc: 添加属性关联时发生完整性错误 (评估ID: {assessment_id}, 属性ID: {attribute.id}): {e}", exc_info=False)
        # 这种情况通常意味着关联已存在，即使上面的 `if attribute in assessment.attributes` 检查没发现（可能因为未加载）
        logger.warning(f"CRUD Assoc: 属性 ID {attribute_id} 可能已关联到评估 ID {assessment.id} (数据库层面)。")
        # 可以选择返回 assessment，表示操作幂等完成
        return assessment # 或者抛出异常 raise ValueError(...)
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(f"CRUD Assoc: 添加属性关联时发生数据库错误 (评估ID: {assessment_id}, 属性ID: {attribute.id}): {e}", exc_info=True)
        raise e

async def remove_attribute_from_assessment(
    db: AsyncSession, *, assessment_id: int, attribute_id: int
) -> Optional[Assessment]:
    """
    从评估记录解除一个属性的关联（通过 ID）。

    Args:
        db: 数据库会话。
        assessment_id: 评估记录的 ID。
        attribute_id: 要解除关联的属性的 ID。

    Returns:
        更新后的 Assessment 对象 (如果成功) 或 None (如果任一 ID 未找到)。
    """
    logger.info(f"CRUD Assoc: 尝试从评估 ID {assessment_id} 移除属性 ID {attribute_id}")
    # 1. 获取评估对象
    assessment = await get(db, id=assessment_id)
    if not assessment:
        logger.warning(f"CRUD Assoc: 未找到评估 ID {assessment_id}，无法移除属性。")
        return None

    # 2. 获取属性对象 (确保它存在，虽然移除时理论上可以不获取，但获取更安全)
    try:
        from app.crud import attribute as crud_attribute
    except ImportError:
        logger.error("CRUD Assoc: 无法导入 crud.attribute 模块！")
        raise RuntimeError("Attribute CRUD module is not available.")

    attribute = await crud_attribute.get_attribute(db, attribute_id=attribute_id)
    if not attribute:
        logger.warning(f"CRUD Assoc: 未找到属性 ID {attribute_id}，无法从评估 {assessment_id} 移除。")
        return None

    # 3. 检查关联是否存在并移除
    #    同样，依赖于 assessment.attributes 是否已加载
    if attribute in assessment.attributes:
        assessment.attributes.remove(attribute) # SQLAlchemy 处理关联表的删除
        db.add(assessment) # 标记对象已更改
        try:
            await db.commit()
            # 移除后通常不需要 refresh
            logger.info(f"CRUD Assoc: 成功从评估 ID {assessment_id} 移除属性 ID {attribute_id}")
            return assessment
        except SQLAlchemyError as e:
            await db.rollback()
            logger.error(f"CRUD Assoc: 移除属性关联时发生数据库错误 (评估ID: {assessment_id}, 属性ID: {attribute.id}): {e}", exc_info=True)
            raise e
    else:
        # 如果关系未加载，或者属性确实未关联
        # 可以尝试直接查询关联表判断是否存在，但通常直接返回表示“已完成”或“无操作”即可
        logger.warning(f"CRUD Assoc: 属性 ID {attribute.id} 未关联到评估 ID {assessment.id} 或关联未加载，无法移除。")
        return assessment # 返回未修改的对象

async def set_assessment_attributes(
    db: AsyncSession, *, assessment_id: int, attribute_ids: List[int]
) -> Optional[Assessment]:
    """
    设置评估记录的属性列表，移除不再包含的属性，添加新增的属性。

    Args:
        db: 数据库会话。
        assessment_id: 评估记录的 ID。
        attribute_ids: 要设置的属性 ID 列表。

    Returns:
        更新后的 Assessment 对象或 None。
    """
    logger.info(f"CRUD Assoc: 正在设置评估 ID {assessment_id} 的属性列表为: {attribute_ids}")
    assessment = await get(db, id=assessment_id)
    if not assessment:
        logger.warning(f"CRUD Assoc: 未找到评估 ID {assessment_id}，无法设置属性。")
        return None

    try:
        from app.crud import attribute as crud_attribute
    except ImportError:
        logger.error("CRUD Assoc: 无法导入 crud.attribute 模块！")
        raise RuntimeError("Attribute CRUD module is not available.")

    # 1. 获取目标属性对象列表
    target_attributes = []
    invalid_ids = []
    if attribute_ids: # 只有当列表不为空时才查询
        stmt = select(Attribute).filter(Attribute.id.in_(attribute_ids))
        result = await db.execute(stmt)
        target_attributes = list(result.scalars().all()) # 获取所有有效的属性对象
        found_ids = {attr.id for attr in target_attributes}
        invalid_ids = [id for id in attribute_ids if id not in found_ids]
        if invalid_ids:
             logger.warning(f"CRUD Assoc: 尝试关联到评估 {assessment_id} 时，发现无效/不存在的属性 IDs: {invalid_ids}")

    # 2. 使用集合操作计算差异 (需要确保 assessment.attributes 已加载)
    #    为确保加载，可以重新查询评估并指定加载策略
    #    或者直接覆盖关系列表 (SQLAlchemy 通常能处理好)
    logger.debug(f"CRUD Assoc: 将评估 {assessment_id} 的属性更新为 ID 列表对应的对象 (找到 {len(target_attributes)} 个)")
    assessment.attributes = target_attributes # 直接将关系列表设置为新的对象列表

    db.add(assessment) # 标记对象已更改
    try:
        await db.commit()
        # await db.refresh(assessment) # 刷新以获取最新状态
        logger.info(f"CRUD Assoc: 成功设置评估 ID {assessment_id} 的属性列表。")
        if invalid_ids:
             logger.warning(f"CRUD Assoc: 在设置评估 {assessment_id} 属性时，以下无效 ID 已被忽略: {invalid_ids}")
        return assessment
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(f"CRUD Assoc: 设置评估 {assessment_id} 属性列表时发生数据库错误: {e}", exc_info=True)
        raise e

async def get_multi(db: AsyncSession, *, skip: int = 0, limit: int = 100) -> List[Assessment]:
    """
    异步获取评估记录列表，按创建时间降序排列。
    """
    logger.info(f"CRUD: 获取评估记录列表 (skip={skip}, limit={limit})")
    try:
        stmt = (
            select(Assessment)
            .order_by(desc(Assessment.created_at))
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(stmt)
        assessments = result.scalars().all()
        logger.info(f"CRUD: 找到 {len(assessments)} 条评估记录")
        return list(assessments)
    except SQLAlchemyError as e:
        logger.error(f"CRUD: 获取评估记录列表时发生数据库错误: {e}", exc_info=True)
        raise e
# --- 结束文件 ---