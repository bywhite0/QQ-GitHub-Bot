# 冒烟验证：攻击者视角打消息模板（8/23 场景复现）
import sys
import importlib.util

sys.path.insert(0, "src")

_spec = importlib.util.spec_from_file_location(
    "_messages", "src/plugins/github/webhooks/_messages.py"
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

ensure_safe_repo = _mod.ensure_safe_repo
ensure_safe_username = _mod.ensure_safe_username
ensure_printable = _mod.ensure_printable
star_created_message = _mod.star_created_message
push_message = _mod.push_message
issue_opened_message = _mod.issue_opened_message
issue_commented_message = _mod.issue_commented_message
issue_closed_message = _mod.issue_closed_message
issue_reopened_message = _mod.issue_reopened_message
pr_synchronize_message = _mod.pr_synchronize_message
release_message = _mod.release_message
unknown_message = _mod.unknown_message

failures = []


def check(label, cond):
    print(f"{'PASS' if cond else 'FAIL'}  {label}" if cond else f"FAIL  {label}")
    if not cond:
        failures.append(label)


# --- 攻击者用户名（历史事故场景）：不出现在任何消息里 ---
evil_logins = [
    "attacker-login-1",
    "bad-user-2",
    "evil-name-3",
    "troll-name-4",
    "spaced-name-5",
]

for login in evil_logins:
    # star 消息根本不接受用户名参数
    msg = star_created_message("bywhite0/Kaho", 7)
    check(f"star 无用户名 ({login})", login not in msg)

# star 消息形态
m = star_created_message("bywhite0/Kaho", 7)
check("star 文案形态", m == "bywhite0/Kaho 收到新的 star！现共 7 颗")

# --- 不可信标题：issue/PR/评论兜底不接收标题参数 ---
m = issue_opened_message("bywhite0/Kaho", "Issue", 123)
check("issue 兜底形态", m == "bywhite0/Kaho 收到新的 Issue #123")
m = issue_opened_message("bywhite0/Kaho", "Pull Request", 45)
check("PR 兜底形态", m == "bywhite0/Kaho 收到新的 Pull Request #45")
m = issue_commented_message("bywhite0/Kaho", 99)
check("评论兜底形态", m == "bywhite0/Kaho#99 有了新的评论")

# --- 协作者字段（受信任）的校验拒绝异常值 ---
for bad in ["", "user\r\ninjection", "用户名中文", "a" * 50, " spaced-evil "]:
    try:
        ensure_safe_username(bad)
        check(f"用户名校验应拒绝 {bad!r}", False)
    except ValueError:
        check(f"用户名校验拒绝 {bad!r}", True)

# 分支名零宽字符注入（协作者也不该能塞这种东西）
for bad in ["main\u200b", "re\u202etoo"]:
    try:
        ensure_printable(bad)
        check(f"printable 校验应拒绝 {bad!r}", False)
    except ValueError:
        check(f"printable 校验拒绝 {bad!r}", True)

# 畸形仓库全名
for bad in ["", "a/b/c", "a b/c", "a/b c", "a//", "/b"]:
    try:
        ensure_safe_repo(bad)
        check(f"repo 校验应拒绝 {bad!r}", False)
    except ValueError:
        check(f"repo 校验拒绝 {bad!r}", True)

# --- push 消息：正常协作者路径 ---
m = push_message(
    "bywhite0/Kaho",
    "kaho-hanohira",
    "分支",
    "main",
    "推送",
    2,
    "abc1234",
    "def5678",
    False,
)
expected_push = "kaho-hanohira 推送了 2 个提交到 bywhite0/Kaho 的分支 main"
check("push 文案形态", m == expected_push + "（abc1234 → def5678）")
m = push_message(
    "bywhite0/Kaho",
    "kaho-hanohira",
    "分支",
    "dev",
    "删除",
    0,
    "abc1234",
    "0000000",
    True,
)
check("push 删除形态", m == "kaho-hanohira 删除了 bywhite0/Kaho 的分支 dev")

# --- release / unknown / 关闭重开 ---
m = release_message("bywhite0/Kaho", "v1.2.0")
check("release 形态", m == "bywhite0/Kaho 发布了新版本 v1.2.0")
m = unknown_message("bywhite0/Kaho")
check("unknown 形态", m == "bywhite0/Kaho 有了新的动态")
m = issue_closed_message("bywhite0/Kaho", 123)
check("closed 形态", m == "bywhite0/Kaho#123 已关闭")
m = issue_reopened_message("bywhite0/Kaho", 123)
check("reopened 形态", m == "bywhite0/Kaho#123 已重新开启")
m = pr_synchronize_message("bywhite0/Kaho", 45, "abc1234", "def5678")
check("PR 同步形态", m == "bywhite0/Kaho#45 更新了提交（abc1234 → def5678）")

# --- 畸形 sha ---
for bad in ["zzz", "abc", "123z45"]:
    try:
        pr_synchronize_message("bywhite0/Kaho", 1, bad, "def5678")
        check(f"sha 校验应拒绝 {bad!r}", False)
    except ValueError:
        check(f"sha 校验拒绝 {bad!r}", True)

print()
if failures:
    print(f"结果：{len(failures)} 项失败")
    sys.exit(1)
print("结果：全部通过")
