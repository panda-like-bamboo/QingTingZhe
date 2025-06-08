# app/routers/sse.py
import asyncio
import json
import logging
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sse_starlette.sse import EventSourceResponse
import redis.asyncio as redis # 导入异步 redis 客户端

from app.core.config import settings
from app.core.deps import get_current_active_user # 保护 SSE 端点
from app import models

logger = logging.getLogger(settings.APP_NAME)
router = APIRouter()

# 全局（或更健壮的作用域）Redis 连接池
# 注意：在生产环境中，连接池管理应更完善
redis_pool = None

async def get_redis_pool():
    """获取或创建 Redis 连接池"""
    global redis_pool
    if redis_pool is None:
        try:
            # 使用 from_url 创建连接池
            redis_pool = redis.ConnectionPool.from_url(
                settings.REDIS_URL,
                decode_responses=True, # 自动解码响应为字符串
                max_connections=20     # 示例连接池大小
            )
            logger.info(f"成功创建 Redis 连接池，目标: {settings.REDIS_URL}")
        except Exception as e:
            logger.critical(f"创建 Redis 连接池失败: {e}", exc_info=True)
            raise HTTPException(status_code=503, detail="无法连接到实时通知服务。")
    return redis_pool

@router.get(
    "/sse/report-status/{submission_id}",
    tags=["SSE"],
    summary="订阅报告生成状态更新"
)
async def report_status_stream(
    submission_id: int,
    request: Request, # 用于检测客户端断开连接
    current_user: models.User = Depends(get_current_active_user), # 保护端点
    pool: redis.ConnectionPool = Depends(get_redis_pool) # 注入连接池
):
    """
    为指定提交 ID 创建 SSE 连接，等待报告就绪事件。
    需要用户已登录。
    """
    logger.info(f"用户 '{current_user.username}' (ID: {current_user.id}) 订阅评估 ID: {submission_id} 的状态更新。")

    channel_name = f"report-ready:{submission_id}"

    async def event_generator():
        # 从连接池获取单个连接
        async with redis.Redis(connection_pool=pool) as redis_client:
            # 创建 PubSub 客户端
            pubsub = redis_client.pubsub(ignore_subscribe_messages=True) # 忽略订阅确认消息
            try:
                # 订阅特定频道
                await pubsub.subscribe(channel_name)
                logger.info(f"SSE: 已订阅频道 '{channel_name}'")

                while True:
                    # 检查客户端是否已断开连接
                    if await request.is_disconnected():
                        logger.info(f"SSE: 客户端断开连接，取消订阅频道 '{channel_name}'。")
                        break

                    # 等待来自 Redis 的消息 (带超时)
                    try:
                        # 使用 asyncio.timeout 防止永久阻塞
                        async with asyncio.timeout(60): # 例如，每 60 秒检查一次连接
                            message = await pubsub.get_message() # timeout=None 已移除，由 asyncio.timeout 控制
                        if message:
                            logger.info(f"SSE: 从频道 '{channel_name}' 收到消息: {message}")
                            data = message.get("data")
                            if data:
                                try:
                                    # 假设消息是 JSON 字符串 {"status": "success"} 或 {"status": "failed", "error": "..."}
                                    payload = json.loads(data)
                                    if payload.get("status") == "success":
                                        logger.info(f"SSE: 报告 ID {submission_id} 已就绪，发送 'report_ready' 事件。")
                                        yield json.dumps({"event": "report_ready", "data": json.dumps({"submission_id": submission_id})})
                                        break # 报告就绪，结束此 SSE 流
                                    elif payload.get("status") == "failed":
                                         logger.warning(f"SSE: 报告 ID {submission_id} 生成失败，发送 'report_failed' 事件。 Error: {payload.get('error')}")
                                         yield json.dumps({"event": "report_failed", "data": json.dumps({"submission_id": submission_id, "error": payload.get('error', '未知错误')})})
                                         break # 任务失败，也结束流
                                    else:
                                         logger.warning(f"SSE: 从频道 '{channel_name}' 收到未知状态的消息: {payload}")
                                except json.JSONDecodeError:
                                     logger.error(f"SSE: 无法解码来自频道 '{channel_name}' 的消息: {data}")
                                except Exception as parse_err:
                                     logger.error(f"SSE: 解析消息时出错 ('{channel_name}'): {parse_err}", exc_info=True)
                        # else:
                            # 没有消息，继续等待 (asyncio.timeout 会处理超时)
                            # logger.debug(f"SSE: 频道 '{channel_name}' 无新消息。")
                            # 可以发送 keep-alive 注释
                            # yield ":" # 发送 SSE 注释以保持连接活跃

                    except asyncio.TimeoutError:
                         # 超时期间没有收到消息，发送 keep-alive 并继续循环
                         logger.debug(f"SSE: 频道 '{channel_name}' 等待超时，发送 keep-alive。")
                         yield ":"
                    except Exception as e:
                         logger.error(f"SSE: 处理频道 '{channel_name}' 消息时发生错误: {e}", exc_info=True)
                         # 发生错误时也考虑结束流，防止无限循环
                         break

            finally:
                # 确保取消订阅
                try:
                    if pubsub.connection: # 检查连接是否存在
                         await pubsub.unsubscribe(channel_name)
                         # 关闭 pubsub 连接 (通常由 Redis 客户端的 __aexit__ 处理)
                         # await pubsub.close()
                         logger.info(f"SSE: 已取消订阅频道 '{channel_name}'")
                except Exception as unsub_err:
                     logger.warning(f"SSE: 取消订阅频道 '{channel_name}' 时出错: {unsub_err}")

    # 返回 EventSourceResponse
    return EventSourceResponse(event_generator())