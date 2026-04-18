from app.extensions import db
from app.models import AIChatMessage
from app.services.config_service import get_config_value


def get_history_limit():
    """中文注释：聊天记录上限按每个用户限制，最大 1000 条。"""
    try:
        limit = int(get_config_value("ai_chat_history_limit", "1000"))
    except ValueError:
        limit = 1000
    return min(max(limit, 1), 1000)


def get_history(user_id, limit=None):
    """中文注释：按时间正序返回当前用户的聊天记录。"""
    history_limit = limit or get_history_limit()
    items = (
        AIChatMessage.query.filter_by(user_id=user_id)
        .order_by(AIChatMessage.created_at.desc(), AIChatMessage.id.desc())
        .limit(history_limit)
        .all()
    )
    return [item.to_dict() for item in reversed(items)]


def save_exchange(user_id, user_content, assistant_content, model):
    """中文注释：AI 成功回复后同时保存用户问题和助手回复。"""
    db.session.add(
        AIChatMessage(
            user_id=user_id,
            role="user",
            content=str(user_content or "").strip(),
            model=model,
        )
    )
    db.session.add(
        AIChatMessage(
            user_id=user_id,
            role="assistant",
            content=str(assistant_content or "").strip(),
            model=model,
        )
    )
    db.session.commit()
    prune_history(user_id)


def clear_history(user_id):
    """中文注释：只清空当前登录用户自己的 AI 聊天记录。"""
    AIChatMessage.query.filter_by(user_id=user_id).delete()
    db.session.commit()


def prune_history(user_id):
    """中文注释：超过上限时删除最旧的消息。"""
    limit = get_history_limit()
    total = AIChatMessage.query.filter_by(user_id=user_id).count()
    overflow = total - limit
    if overflow <= 0:
        return

    old_items = (
        AIChatMessage.query.filter_by(user_id=user_id)
        .order_by(AIChatMessage.created_at.asc(), AIChatMessage.id.asc())
        .limit(overflow)
        .all()
    )
    for item in old_items:
        db.session.delete(item)
    db.session.commit()
