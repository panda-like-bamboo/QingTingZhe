# 文件路径: PsychologyAnalysis/app/schemas/stats.py

from pydantic import BaseModel, Field
from typing import List, Dict, Any

class ChartData(BaseModel):
    """用于图表展示的数据结构"""
    labels: List[str]
    values: List[int | float]

class DemographicsStats(BaseModel):
    """人口统计数据的响应模型"""
    ageData: ChartData
    genderData: ChartData

# [+] 新增: AI 分析请求体模型
class AIAnalysisRequest(BaseModel):
    demographics: DemographicsStats = Field(..., description="要分析的人口统计数据")
    # 未来可以添加更多数据，例如：
    # assessment_trends: Optional[ChartData] = None

# [+] 新增: AI 分析响应模型
class AIAnalysisResponse(BaseModel):
    analysis_text: str = Field(..., description="由AI生成的分析文本")