# FILE: app/crud/stats.py (新建)
import logging
from typing import Dict, List, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func # 导入 SQL 函数

from app.models.user import User # 导入 User 模型 (如果按性别统计需要 User 表)
from app.models.assessment import Assessment # 导入 Assessment 模型 (如果按年龄统计需要 Assessment 表)
from app.core.config import settings

logger = logging.getLogger(settings.APP_NAME)

async def get_age_distribution(db: AsyncSession) -> Dict[str, List[Any]]:
    """
    异步获取评估记录中的年龄分布统计数据。
    注意: 这依赖于 Assessment 模型中 'age' 列有数据。
    """
    logger.info("CRUD Stats: 计算年龄分布")
    # 定义年龄段
    age_bins = {
        '<18': (0, 17),
        '18-25': (18, 25),
        '26-35': (26, 35),
        '36-45': (36, 45),
        '46-55': (46, 55),
        '56+': (56, 999), # 使用一个较大的上限
        '未知': (None, None) # 处理空值
    }
    labels = list(age_bins.keys())
    values = [0] * len(labels)

    try:
        # 查询所有有效的年龄
        stmt = select(Assessment.age)
        result = await db.execute(stmt)
        ages = result.scalars().all()

        # 在 Python 中进行分组计数
        for age in ages:
            found = False
            for i, (label, (min_age, max_age)) in enumerate(age_bins.items()):
                 if label == '未知': continue # 跳过未知标签的 bin 定义
                 if age is None:
                     if label == '未知': # 应该不会执行到这里，但作为后备
                         values[labels.index('未知')] += 1
                         found = True
                         break
                     continue # 非未知标签不匹配 None age

                 # 确保 age 是数字类型
                 if isinstance(age, (int, float)):
                     if min_age is not None and max_age is not None and min_age <= age <= max_age:
                         values[i] += 1
                         found = True
                         break
                 else:
                      logger.warning(f"CRUD Stats: 在年龄分布计算中遇到非数字年龄值: {age} (类型: {type(age)})，已忽略。")

            if not found: # 处理 None 和未匹配的年龄
                 if age is None:
                    values[labels.index('未知')] += 1
                 else:
                    logger.warning(f"CRUD Stats: 年龄 {age} 未落入任何定义的区间，已忽略。")

        logger.info(f"CRUD Stats: 年龄分布计算完成 - Labels: {labels}, Values: {values}")
        return {"labels": labels, "values": values}

    except Exception as e:
        logger.error(f"CRUD Stats: 计算年龄分布时出错: {e}", exc_info=True)
        # 返回空或默认值，避免 API 失败
        return {"labels": labels, "values": [0] * len(labels)}


async def get_gender_distribution(db: AsyncSession) -> Dict[str, List[Any]]:
    """
    异步获取评估记录中的性别分布统计数据。
    注意: 这依赖于 Assessment 模型中 'gender' 列有数据。
    """
    logger.info("CRUD Stats: 计算性别分布")
    labels = []
    values = []
    try:
        # 使用 SQLAlchemy 的 func.count 和 group_by 进行聚合查询
        stmt = (
            select(Assessment.gender, func.count(Assessment.id).label('count'))
            .group_by(Assessment.gender)
            .order_by(Assessment.gender) # 按性别排序以保持一致
        )
        result = await db.execute(stmt)
        rows = result.all() # 获取所有 (gender, count) 对

        # 处理结果
        if not rows:
            logger.info("CRUD Stats: 性别分布数据为空。")
            return {"labels": ["无数据"], "values": [0]}

        for row in rows:
            gender = row.gender if row.gender else "未知" # 处理 NULL 值
            count = row.count
            labels.append(gender)
            values.append(count)

        logger.info(f"CRUD Stats: 性别分布计算完成 - Labels: {labels}, Values: {values}")
        return {"labels": labels, "values": values}

    except Exception as e:
        logger.error(f"CRUD Stats: 计算性别分布时出错: {e}", exc_info=True)
        return {"labels": ["错误"], "values": [0]}

# --- (可选) 其他统计函数 ---
# async def get_scale_usage(db: AsyncSession) -> Dict[str, List[Any]]: ...
# async def get_assessment_status_distribution(db: AsyncSession) -> Dict[str, List[Any]]: ...