# # app/services/invite.py
# import secrets
# from datetime import datetime, timedelta
# from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy.future import select
# from app.models.invite import GroupInvite

# INVITE_TOKEN_BYTES = 32
# DEFAULT_EXPIRE_DAYS = 7

# async def create_group_invite(db: AsyncSession, group_id: int, expires_days: int = DEFAULT_EXPIRE_DAYS, max_uses: int | None = None) -> GroupInvite:
#     token = secrets.token_urlsafe(INVITE_TOKEN_BYTES)
#     expires_at = datetime.utcnow() + timedelta(days=expires_days) if expires_days else None
#     invite = GroupInvite(group_id=group_id, token=token, expires_at=expires_at, max_uses=max_uses)
#     db.add(invite)
#     await db.commit()
#     await db.refresh(invite)
#     return invite

# async def get_invite_by_token(db: AsyncSession, token: str) -> GroupInvite | None:
#     q = await db.execute(select(GroupInvite).where(GroupInvite.token == token, GroupInvite.is_active == True))
#     return q.scalars().first()

# async def consume_invite(db: AsyncSession, invite: GroupInvite) -> None:
#     invite.uses += 1
#     if invite.max_uses is not None and invite.uses >= invite.max_uses:
#         invite.is_active = False
#     db.add(invite)
#     await db.commit()
#     await db.refresh(invite)
