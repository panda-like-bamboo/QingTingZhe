# 文件路径: PsychologyAnalysis/app/schemas/__init__.py (最终修复版)

# --- 用户相关 ---
from .user import (
    User, UserCreate, UserUpdate, UserUpdateAdmin, UserListResponse, UserInDB, UserBase
)
# --- 认证相关 ---
from .token import Token, TokenData
# --- 量表相关 ---
from .scale import (
    ScaleOption, ScaleQuestion, ScaleInfo, ScaleQuestionsResponse, AvailableScalesResponse
)
# --- 评估相关 ---
from .assessment import AssessmentSubmitResponse, AssessmentSummary
# --- 报告相关 ---
from .report import ReportData, ReportResponse, ReportStatusResponse
# --- 百科相关 ---
from .encyclopedia import EncyclopediaEntry, CategoriesResponse, EntriesResponse
# --- 统计相关 ---
from .stats import DemographicsStats, ChartData, AIAnalysisRequest, AIAnalysisResponse
# --- 审讯相关 ---
from .interrogation import (
    InterrogationBasicInfo, InterrogationQAInput, InterrogationRecordCreate,
    InterrogationRecordUpdate, InterrogationRecordRead, InterrogationSummary,
    InterrogationListResponse
)
# --- 属性相关 ---
from .attribute import AttributeRead, AttributeCreate, AttributeUpdate

# --- [核心修复] 指导方案相关 ---
# 我们从 guidance.py 中导入新的、正确的模型名称
from .guidance import GuidanceWithReportResponse

# --- 定义公开接口 (__all__) ---
__all__ = [
    # User
    "User", "UserCreate", "UserUpdate", "UserUpdateAdmin", "UserListResponse", "UserInDB", "UserBase",
    # Token
    "Token", "TokenData",
    # Scale
    "ScaleOption", "ScaleQuestion", "ScaleInfo", "ScaleQuestionsResponse", "AvailableScalesResponse",
    # Assessment
    "AssessmentSubmitResponse", "AssessmentSummary",
    # Report
    "ReportData", "ReportResponse", "ReportStatusResponse",
    # Encyclopedia
    "EncyclopediaEntry", "CategoriesResponse", "EntriesResponse",
    # Stats
    "DemographicsStats", "ChartData", "AIAnalysisRequest", "AIAnalysisResponse",
    # Interrogation
    "InterrogationBasicInfo", "InterrogationQAInput", "InterrogationRecordCreate",
    "InterrogationRecordUpdate", "InterrogationRecordRead",
    "InterrogationSummary", "InterrogationListResponse",
    # Attribute
    "AttributeRead", "AttributeCreate", "AttributeUpdate",
    # [核心修复] Guidance
    "GuidanceWithReportResponse",
]