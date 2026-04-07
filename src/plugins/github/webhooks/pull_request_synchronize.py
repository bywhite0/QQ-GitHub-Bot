"""
@Author         : yanyongyu
@Date           : 2026-04-07 11:26:30
@LastEditors    : yanyongyu
@LastEditTime   : 2026-04-07 11:26:30
@Description    : Webhook pull request synchronize broadcast
@GitHub         : https://github.com/yanyongyu
"""

__author__ = "yanyongyu"

import asyncio
from datetime import timedelta

from nonebot.params import Depends
from nonebot import logger, on_type
from nonebot.plugin import PluginMetadata
from nonebot.adapters.github import PullRequestSynchronize

from src.plugins.github import config
from src.plugins.github.cache.message_tag import PullRequestTag

from ._dependencies import (
    SUBSCRIBERS,
    SEND_INTERVAL,
    Throttle,
    send_subscriber_text,
)

__plugin_meta__ = PluginMetadata(
    "GitHub Pull Request 同步事件通知",
    "订阅 GitHub pull_request/synchronize 事件来接收通知",
    "通知示例：\n"
    "用户 yanyongyu 同步了 Pull Request"
    " cscs181/QQ-GitHub-Bot#1: Update README (abc1234 -> def5678)",
)

THROTTLE_EXPIRE = timedelta(seconds=60)

pull_request_synchronize = on_type(
    PullRequestSynchronize,
    priority=config.github_webhook_priority,
    block=True,
)


def _short_sha(sha: str | None) -> str:
    return sha[:7] if sha else "unknown"


@pull_request_synchronize.handle(
    parameterless=(Depends(Throttle((PullRequestSynchronize,), THROTTLE_EXPIRE)),)
)
async def handle_pull_request_synchronize_event(
    event: PullRequestSynchronize, subscribers: SUBSCRIBERS
):
    if not subscribers:
        return

    repo_name = event.payload.repository.full_name
    owner, repo = repo_name.split("/", 1)

    pull_request = event.payload.pull_request
    before = _short_sha(event.payload.before)
    after = _short_sha(event.payload.after)

    message = (
        f"用户 {event.payload.sender.login} 同步了 Pull Request "
        f"{repo_name}#{pull_request.number}: {pull_request.title}"
        f" ({before} -> {after})"
    )

    tag = PullRequestTag(
        owner=owner, repo=repo, number=pull_request.number, is_receive=False
    )

    for target in subscribers:
        try:
            await send_subscriber_text(target.to_subscriber_info(), message, tag)
        except Exception as e:
            logger.opt(exception=e).warning(
                "Send message to subscriber failed: {e}",
                target_info=target.to_subscriber_info(),
                e=e,
            )

        await asyncio.sleep(SEND_INTERVAL)
