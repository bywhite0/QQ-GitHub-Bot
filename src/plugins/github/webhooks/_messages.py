"""
@Author         : bywhite0
@Date           : 2026-09-10 21:30:00
@LastEditors    : bywhite0
@LastEditTime   : 2026-09-10 21:30:00
@Description    : Webhook broadcast message templates
@GitHub         : https://github.com/bywhite0
"""

__author__ = "bywhite0"

import re

# Security rules for broadcast texts (2026-08-23 incident):
# 1. Zero-trust fields (sender login of star/fork/watch/issue/comment events,
#    issue/pr titles) must NEVER appear in broadcast texts. GitHub usernames
#    only allow [A-Za-z0-9-], so sensitive words can be built with valid ASCII
#    characters -- character filters cannot stop them.
# 2. Only fields from trusted actions (push / release, i.e. repo collaborators)
#    may be broadcast, and each of them must pass format validation below.
# 3. All wording lives here as constants; no webhook payload may leak into
#    broadcast texts outside these templates.

_REPO_PATTERN = re.compile(r"^[A-Za-z0-9_.\-]+/[A-Za-z0-9_.\-]+$")
_USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9\-]{0,38})?$")
_SHA_PATTERN = re.compile(r"^(?:[0-9a-f]{7,40}|unknown)$")
# control chars / zero-width / bidi overrides must never reach QQ messages
_UNPRINTABLE_PATTERN = re.compile(
    r"[\x00-\x1f\x7f\u200b-\u200f\u202a-\u202e\u2060\ufeff]"
)


def ensure_safe_repo(full_name: str) -> str:
    """Validate a repository full name before broadcasting"""
    if not _REPO_PATTERN.match(full_name):
        raise ValueError(f"Unsafe repository full name: {full_name!r}")
    return full_name


def ensure_safe_username(login: str) -> str:
    """Validate a collaborator login before broadcasting"""
    if not _USERNAME_PATTERN.match(login):
        raise ValueError(f"Unsafe username: {login!r}")
    return login


def ensure_safe_sha(sha: str) -> str:
    """Validate a short/full commit sha before broadcasting"""
    if not _SHA_PATTERN.match(sha):
        raise ValueError(f"Unsafe commit sha: {sha!r}")
    return sha


def ensure_printable(text: str) -> str:
    """Reject control/zero-width/bidi characters in trusted free-form fields"""
    if _UNPRINTABLE_PATTERN.search(text):
        raise ValueError(f"Unprintable characters found: {text!r}")
    return text


def ensure_safe_int(value: int) -> int:
    """Validate an event counter/number before broadcasting"""
    if not isinstance(value, int) or value < 0:
        raise ValueError(f"Unsafe integer: {value!r}")
    return value


def star_created_message(full_name: str, star_count: int) -> str:
    """Star created event text (sender is zero-trust, not broadcast)"""
    return (
        f"{ensure_safe_repo(full_name)} 收到新的 star！"
        f"现共 {ensure_safe_int(star_count)} 颗"
    )


def push_message(
    full_name: str,
    username: str,
    target_type: str,
    target_name: str,
    action: str,
    commit_count: int,
    before: str,
    after: str,
    deleted: bool,
) -> str:
    """Push event text (only collaborators can push, login is trusted)"""
    full_name = ensure_safe_repo(full_name)
    username = ensure_safe_username(username)
    target_name = ensure_printable(target_name)

    if deleted:
        return f"{username} 删除了 {full_name} 的{target_type} {target_name}"

    return (
        f"{username} {action}了 {ensure_safe_int(commit_count)} 个提交到 "
        f"{full_name} 的{target_type} {target_name}"
        f"（{ensure_safe_sha(before)} → {ensure_safe_sha(after)}）"
    )


def issue_opened_message(full_name: str, kind: str, number: int) -> str:
    """Issue/PR opened fallback text (sender and title are zero-trust)"""
    return (
        f"{ensure_safe_repo(full_name)} 收到新的 {kind}" f" #{ensure_safe_int(number)}"
    )


def issue_commented_message(full_name: str, number: int) -> str:
    """Issue/PR comment fallback text (commenter and title are zero-trust)"""
    return f"{ensure_safe_repo(full_name)}#{ensure_safe_int(number)} 有了新的评论"


def issue_closed_message(full_name: str, number: int) -> str:
    """Issue/PR closed fallback text (zero-trust fields not broadcast)"""
    return f"{ensure_safe_repo(full_name)}#{ensure_safe_int(number)} 已关闭"


def issue_reopened_message(full_name: str, number: int) -> str:
    """Issue/PR reopened fallback text (zero-trust fields not broadcast)"""
    return f"{ensure_safe_repo(full_name)}#{ensure_safe_int(number)} 已重新开启"


def pr_synchronize_message(full_name: str, number: int, before: str, after: str) -> str:
    """PR synchronize event text (sender and title are zero-trust)"""
    return (
        f"{ensure_safe_repo(full_name)}#{ensure_safe_int(number)} 更新了提交"
        f"（{ensure_safe_sha(before)} → {ensure_safe_sha(after)}）"
    )


def release_message(full_name: str, tag: str) -> str:
    """Release published fallback text (tag is created by collaborators)"""
    return f"{ensure_safe_repo(full_name)} 发布了新版本 {ensure_printable(tag)}"


def unknown_message(full_name: str) -> str:
    """Unknown event fallback text (no zero-trust field is broadcast)"""
    return f"{ensure_safe_repo(full_name)} 有了新的动态"
