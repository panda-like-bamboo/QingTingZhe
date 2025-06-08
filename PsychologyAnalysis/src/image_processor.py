# src/image_processor.py
import os
import base64
from openai import OpenAI
import logging
import sys # 添加sys导入

# --- 导入 settings ---
# 确保路径正确，以便能够导入 settings
SRC_DIR_IMAGE_PROC = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT_IMAGE_PROC = os.path.dirname(SRC_DIR_IMAGE_PROC) # PsychologyAnalysis/
if PROJECT_ROOT_IMAGE_PROC not in sys.path:
    sys.path.insert(0, PROJECT_ROOT_IMAGE_PROC)

try:
    from app.core.config import settings
except ImportError as e:
    # 如果无法导入 settings，则使用一个默认的空对象来避免崩溃
    class MockSettings:
        DASHSCOPE_API_KEY = None
        VISION_MODEL = "qwen-vl-plus"
        APP_NAME = "FallbackApp"
    settings = MockSettings()
    print(f"警告: 无法在 image_processor.py 中导入 app.core.config.settings: {e}", file=sys.stderr)

# Get the logger instance setup in app.py or utils.py
logger = logging.getLogger(settings.APP_NAME) # 使用统一的 APP_NAME
if not logger.hasHandlers():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


class ImageProcessor:
    def __init__(self, config):
        """Initializes ImageProcessor with configuration and explicit safe headers."""
        # 从 settings 获取 API Key 和模型名称，不再直接从 config.get() 优先
        self.api_key = settings.DASHSCOPE_API_KEY
        if not self.api_key:
            logger.error("CRITICAL: API Key not found in settings for ImageProcessor.")
            raise ValueError("API Key missing for ImageProcessor.")

        self.model = settings.VISION_MODEL # 从 settings 获取视觉模型
        self.base_url = config.get("base_url", "https://dashscope.aliyuncs.com/compatible-mode/v1") # base_url 仍然可以从传入的 config 获取

        # --- Explicitly set safe default headers ---
        safe_headers = {
            "User-Agent": "MyPsychologyApp-ImageProcessor/1.0",
            "Accept": "application/json",
        }

        try:
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                default_headers=safe_headers
            )
            logger.info(f"ImageProcessor OpenAI client initialized. Base URL: {self.base_url}. Using explicit safe headers.")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client in ImageProcessor: {e}", exc_info=True)
            raise

    def process_image(self, image_path):
        """Processes an image using the configured vision model."""
        logger.info(f"Processing image: {image_path}")
        try:
            with open(image_path, "rb") as image_file:
                image_base64 = base64.b64encode(image_file.read()).decode("utf-8")
        except FileNotFoundError:
            logger.error(f"Image file not found: {image_path}")
            raise FileNotFoundError(f"图片文件未找到: {image_path}")
        except Exception as e:
            logger.error(f"Error reading or encoding image {image_path}: {e}", exc_info=True)
            raise Exception(f"读取或编码图片时出错: {e}") from e

        messages = [
            {
                "role": "system",
                "content": [{"type": "text", "text": "You are a helpful assistant focused on image description."}]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}
                    },
                    {"type": "text", "text": "请详细描述这张图片的内容，包括物体、人物（如有）、场景氛围、颜色和构图等。"}
                ]
            }
        ]

        try:
            logger.debug(f"Calling vision model '{self.model}' for image {os.path.basename(image_path)}")
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
            )
            description = completion.choices[0].message.content
            logger.info(f"Image description received successfully for {os.path.basename(image_path)}.")
            return description
        except Exception as e:
            logger.error(f"Error calling vision API for {os.path.basename(image_path)}: {type(e).__name__} - {e}", exc_info=True)
            raise Exception(f"图像识别失败: {str(e)}") from e