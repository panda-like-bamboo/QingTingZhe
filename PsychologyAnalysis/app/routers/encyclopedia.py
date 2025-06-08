# 文件: app/routers/encyclopedia.py
import logging
import random
from typing import Optional, List, Dict
from fastapi import APIRouter, HTTPException, Query, status

from app.core.config import settings
from app.schemas.encyclopedia import EncyclopediaEntry, CategoriesResponse, EntriesResponse # 导入模型

logger = logging.getLogger(settings.APP_NAME)
router = APIRouter()

# --- 辅助函数：从加载的条目中获取数据 ---
def get_all_entries() -> List[Dict[str, str]]:
    """安全地获取配置中的百科条目列表"""
    entries = settings.PSYCHOLOGY_ENTRIES
    if not isinstance(entries, list):
        logger.error("配置中的 PSYCHOLOGY_ENTRIES 不是列表！")
        return []
    return entries

# --- 端点 1: 获取分类 ---
@router.get(
    "/encyclopedia/categories",
    response_model=CategoriesResponse,
    tags=["Encyclopedia"],
    summary="获取所有心理百科分类"
)
async def get_encyclopedia_categories():
    """
    返回所有心理百科条目的唯一分类名称列表。
    """
    all_entries = get_all_entries()
    if not all_entries:
        return CategoriesResponse(categories=[])

    # 提取所有分类并去重，然后排序
    try:
        categories = sorted(list(set(entry.get("category", "未分类") for entry in all_entries)))
        return CategoriesResponse(categories=categories)
    except Exception as e:
         logger.error(f"提取百科分类时出错: {e}", exc_info=True)
         raise HTTPException(status_code=500, detail="处理分类列表时出错")


# --- 端点 2: 获取条目 (包含过滤和随机功能) ---
@router.get(
    "/encyclopedia/entries",
    # 响应模型根据情况可能是列表或单个条目，用 Union 或 Any，或者为随机单独建模型/端点
    # 为清晰起见，我们让它主要返回列表，随机情况特殊处理返回单个条目模型
    response_model=EntriesResponse, # 主要返回列表
    tags=["Encyclopedia"],
    summary="获取心理百科条目"
)
async def get_encyclopedia_entries(
    category: Optional[str] = Query(None, description="按分类过滤条目"),
    random_tip: Optional[bool] = Query(False, description="是否从'心理小贴士'分类中随机获取一条") # 参数名改为 random_tip
    # 可以添加分页参数: page: int = Query(1, ge=1), size: int = Query(10, ge=1, le=100)
):
    """
    获取心理百科条目。
    - 提供 `category` 参数以按分类过滤。
    - 提供 `random_tip=true` 以获取一条随机的“心理小贴士”。(此时忽略 category 参数)
    """
    all_entries = get_all_entries()
    if not all_entries:
        if random_tip:
             # 返回一个默认的 EncyclopediaEntry 结构
             return EntriesResponse(entries=[EncyclopediaEntry(category="心理小贴士", title="提示", content="暂无可用小贴士。")])
        else:
             return EntriesResponse(entries=[]) # 返回空列表

    target_entries = all_entries

    # --- 处理随机小贴士逻辑 ---
    if random_tip:
        tips_category_name = "心理小贴士" # 明确指定分类名称
        tip_entries = [entry for entry in all_entries if entry.get("category") == tips_category_name]

        if not tip_entries:
            logger.warning("请求随机小贴士，但 '心理小贴士' 分类下没有条目。")
            # 返回一个默认的 EncyclopediaEntry 结构，放入列表中
            return EntriesResponse(entries=[EncyclopediaEntry(category=tips_category_name, title="提示", content="暂无可用小贴士。")])

        selected_entry_dict = random.choice(tip_entries)
        # 将选中的字典包装在列表中返回，以匹配 EntriesResponse
        selected_entry_model = EncyclopediaEntry(**selected_entry_dict)
        return EntriesResponse(entries=[selected_entry_model]) # 返回包含单个随机条目的列表

    # --- 处理按分类过滤逻辑 (如果不是请求随机小贴士) ---
    if category:
        target_entries = [entry for entry in all_entries if entry.get("category") == category]
        if not target_entries:
             # 如果指定了分类但找不到，返回空列表是合理的
             logger.info(f"请求分类 '{category}'，但未找到条目。")
             return EntriesResponse(entries=[])

    # --- (可选) 实现分页 ---
    # total = len(target_entries)
    # start = (page - 1) * size
    # end = start + size
    # paged_entries_dicts = target_entries[start:end]

    # --- 将字典列表转换为 Pydantic 模型列表 ---
    # 如果没有分页，直接使用 target_entries
    try:
        result_entries = [EncyclopediaEntry(**entry_dict) for entry_dict in target_entries]
    except Exception as e:
         logger.error(f"将百科条目字典转换为 Pydantic 模型时出错: {e}", exc_info=True)
         raise HTTPException(status_code=500, detail="处理百科条目数据时出错")

    # 返回结果
    return EntriesResponse(entries=result_entries) # , total=total, page=page, size=size) 如果实现分页