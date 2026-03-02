"""
@Author         : yanyongyu
@Date           : 2026-04-07 23:40:20
@LastEditors    : yanyongyu
@LastEditTime   : 2026-04-07 23:40:20
@Description    : Webhook push event broadcast
@GitHub         : https://github.com/yanyongyu
"""

__author__ = "yanyongyu"

import asyncio

from nonebot import logger, on_type
from nonebot.adapters.github import Push
from nonebot.plugin import PluginMetadata
from nonebot.adapters.github.utils import get_attr_or_item

from src.plugins.github import config
from src.plugins.github.cache.message_tag import RepoTag, CommitTag

from ._dependencies import SUBSCRIBERS, SEND_INTERVAL, send_subscriber_text

__plugin_meta__ = PluginMetadata(
    "GitHub Push 事件通知",
    "订阅 GitHub push 事件来接收通知",
    "通知示例：\n"
    "用户 yanyongyu 推送到仓库 cscs181/QQ-GitHub-Bot 的分支 master"
    " (2 个提交, abc1234 -> def5678)",
)

push = on_type(Push, priority=config.github_webhook_priority, block=True)


def _short_sha(sha: str | None) -> str:
    return sha[:7] if sha else "unknown"


def _is_valid_commit_sha(sha: str | None) -> bool:
    if not sha:
        return False
    return any(char != "0" for char in sha)


def _parse_ref(ref: str | None) -> tuple[str, str]:
    if not ref:
        return "引用", "unknown"

    if ref.startswith("refs/heads/"):
        return "分支", ref.replace("refs/heads/", "", 1)
    if ref.startswith("refs/tags/"):
        return "标签", ref.replace("refs/tags/", "", 1)
    return "引用", ref


def _parse_action(created: bool, deleted: bool, forced: bool) -> str:
    if deleted:
        return "删除了"
    if forced:
        return "强制推送到"
    if created:
        return "创建并推送到"
    return "推送到"


@push.handle()
async def handle_push_event(event: Push, subscribers: SUBSCRIBERS):
    if not subscribers:
        return

    repo_name = event.payload.repository.full_name
    owner, repo = repo_name.split("/", 1)

    username: str = get_attr_or_item(get_attr_or_item(event.payload, "sender"), "login")
    if not username:
        username = "unknown"
    target_type, target_name = _parse_ref(event.payload.ref)
    action = _parse_action(
        bool(event.payload.created),
        bool(event.payload.deleted),
        bool(event.payload.forced),
    )

    before = _short_sha(event.payload.before)
    after = _short_sha(event.payload.after)
    commit_count = len(event.payload.commits or [])

    message = (
        f"用户 {username} {action} 仓库 {repo_name} 的{target_type} {target_name} "
        f"({commit_count} 个提交, {before} -> {after})"
    )

    if _is_valid_commit_sha(event.payload.after):
        tag = CommitTag(
            owner=owner,
            repo=repo,
            commit=event.payload.after,
            is_receive=False,
        )
    else:
        tag = RepoTag(owner=owner, repo=repo, is_receive=False)

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