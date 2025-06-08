# FILE: app/crud/attribute.py
import logging
from typing import List, Optional, Sequence # 导入 Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
import sqlite3

from app.models.attribute import Attribute # 导入 Attribute 模型
from app.schemas.attribute import AttributeCreate, AttributeUpdate # 导入 Pydantic Schemas
from app.core.config import settings

logger = logging.getLogger(settings.APP_NAME)

async def get_attribute(db: AsyncSession, attribute_id: int) -> Optional[Attribute]:
    """根据 ID 异步获取单个属性。"""
    logger.debug(f"CRUD: 尝试获取属性 ID: {attribute_id}")
    result = await db.execute(select(Attribute).filter(Attribute.id == attribute_id))
    attribute = result.scalar_one_or_none()
    if attribute:
        logger.debug(f"CRUD: 找到属性 ID: {attribute_id}, Name: {attribute.name}")
    else:
        logger.warning(f"CRUD: 未找到属性 ID: {attribute_id}")
    return attribute

async def get_attribute_by_name(db: AsyncSession, name: str) -> Optional[Attribute]:
    """根据名称异步获取单个属性 (大小写敏感)。"""
    logger.debug(f"CRUD: 尝试按名称获取属性: {name}")
    # 可以考虑使用 func.lower() 实现不区分大小写查找，但需确保数据库支持且有索引
    # result = await db.execute(select(Attribute).filter(func.lower(Attribute.name) == name.lower()))
    result = await db.execute(select(Attribute).filter(Attribute.name == name))
    attribute = result.scalar_one_or_none()
    if attribute:
        logger.debug(f"CRUD: 找到属性 Name: {name}, ID: {attribute.id}")
    else:
        logger.debug(f"CRUD: 未找到属性 Name: {name}")
    return attribute

async def get_attributes(
    db: AsyncSession, skip: int = 0, limit: int = 100, category: Optional[str] = None
) -> Sequence[Attribute]: # 返回模型序列
    """
    异步获取属性列表，支持分页和按分类过滤。
    返回 Attribute ORM 对象列表。
    """
    logger.info(f"CRUD: 获取属性列表, skip={skip}, limit={limit}, category={category}")
    stmt = select(Attribute).order_by(Attribute.name).offset(skip).limit(limit)
    if category:
        stmt = stmt.filter(Attribute.category == category)

    result = await db.execute(stmt)
    attributes = result.scalars().all()
    logger.info(f"CRUD: 获取到 {len(attributes)} 个属性")
    return attributes # 直接返回 ORM 对象列表

async def create_attribute(db: AsyncSession, *, attribute_in: AttributeCreate) -> Attribute:
    """异步创建新属性。"""
    logger.info(f"CRUD: 尝试创建属性: Name='{attribute_in.name}', Category='{attribute_in.category}'")
    # 检查名称是否已存在
    existing_attribute = await get_attribute_by_name(db, name=attribute_in.name)
    if existing_attribute:
        logger.warning(f"CRUD: 属性名称 '{attribute_in.name}' 已存在，无法创建。")
        raise ValueError(f"属性名称 '{attribute_in.name}' 已存在。") # 抛出 ValueError

    db_attribute = Attribute(**attribute_in.model_dump()) # 从 Pydantic 创建模型实例
    db.add(db_attribute)
    try:
        await db.commit()
        await db.refresh(db_attribute)
        logger.info(f"CRUD: 成功创建属性 ID: {db_attribute.id}, Name: {db_attribute.name}")
        return db_attribute
    except (IntegrityError, sqlite3.IntegrityError) as e: # 捕获唯一约束错误
        await db.rollback()
        logger.error(f"CRUD: 创建属性 '{attribute_in.name}' 时发生数据库完整性错误: {e}", exc_info=False)
        raise ValueError(f"属性名称 '{attribute_in.name}' 可能已存在或违反数据库约束。") from e
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(f"CRUD: 创建属性 '{attribute_in.name}' 时发生数据库错误: {e}", exc_info=True)
        raise e # 重新抛出原始 SQLAlchemy 错误

async def update_attribute(
    db: AsyncSession, *, db_attribute: Attribute, attribute_in: AttributeUpdate
) -> Attribute:
    """异步更新属性。"""
    logger.info(f"CRUD: 尝试更新属性 ID: {db_attribute.id}, Name: {db_attribute.name}")
    update_data = attribute_in.model_dump(exclude_unset=True)

    if not update_data:
        logger.info(f"CRUD: 没有提供更新数据，属性 ID {db_attribute.id} 未更改。")
        return db_attribute

    # 检查新名称是否与现有其他属性冲突
    new_name = update_data.get("name")
    if new_name and new_name != db_attribute.name:
        existing_attribute = await get_attribute_by_name(db, name=new_name)
        if existing_attribute:
            logger.warning(f"CRUD: 更新失败，新的属性名称 '{new_name}' 已被 ID {existing_attribute.id} 使用。")
            raise ValueError(f"属性名称 '{new_name}' 已存在。")

    for field, value in update_data.items():
        setattr(db_attribute, field, value)

    db.add(db_attribute)
    try:
        await db.commit()
        await db.refresh(db_attribute)
        logger.info(f"CRUD: 成功更新属性 ID: {db_attribute.id}")
        return db_attribute
    except (IntegrityError, sqlite3.IntegrityError) as e:
        await db.rollback()
        logger.error(f"CRUD: 更新属性 ID {db_attribute.id} 时发生数据库完整性错误: {e}", exc_info=False)
        raise ValueError(f"更新属性时名称 '{update_data.get('name')}' 可能已存在或违反数据库约束。") from e
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(f"CRUD: 更新属性 ID {db_attribute.id} 时发生数据库错误: {e}", exc_info=True)
        raise e

async def delete_attribute(db: AsyncSession, attribute_id: int) -> bool:
    """异步删除属性 (需要注意关联关系)。"""
    logger.warning(f"CRUD: 尝试删除属性 ID: {attribute_id}")
    db_attribute = await get_attribute(db, attribute_id=attribute_id)
    if not db_attribute:
        logger.error(f"CRUD: 无法删除，未找到属性 ID: {attribute_id}")
        return False

    # 警告：直接删除可能导致 assessment_attributes 表中的外键约束失败（如果数据库强制执行）
    # 或留下孤立的关联记录。最佳实践是先解除关联。
    # 在这里，我们先尝试直接删除，如果失败则提示需要先解除关联。
    # 更安全的做法是先查询是否有评估关联了此属性。
    # stmt_count = select(func.count()).select_from(assessment_attributes_table).where(assessment_attributes_table.c.attribute_id == attribute_id)
    # count_result = await db.execute(stmt_count)
    # associated_count = count_result.scalar_one_or_none()
    # if associated_count and associated_count > 0:
    #     logger.error(f"CRUD: 无法删除属性 ID {attribute_id}，因为它仍关联着 {associated_count} 个评估记录。")
    #     raise ValueError(f"无法删除属性，因为它仍被 {associated_count} 个评估使用。请先解除关联。")

    try:
        await db.delete(db_attribute)
        await db.commit()
        logger.info(f"CRUD: 成功删除属性 ID: {attribute_id}")
        return True
    except (IntegrityError, sqlite3.IntegrityError) as e: # 特别是外键约束错误
         await db.rollback()
         logger.error(f"CRUD: 删除属性 ID {attribute_id} 时发生完整性错误（可能仍被评估使用）: {e}", exc_info=False)
         raise ValueError(f"无法删除属性，可能它仍被某些评估使用。错误: {e}") from e
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(f"CRUD: 删除属性 ID {attribute_id} 时发生数据库错误: {e}", exc_info=True)
        raise e