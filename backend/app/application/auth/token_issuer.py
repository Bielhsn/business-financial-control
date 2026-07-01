from datetime import UTC, datetime, timedelta

from app.application.auth.dto import TokenPair
from app.core.config import Settings
from app.domain.auth.ports import TokenService
from app.domain.auth.repository import RefreshTokenRepository


async def issue_token_pair(
    *,
    user_id: str,
    refresh_token_repository: RefreshTokenRepository,
    token_service: TokenService,
    settings: Settings,
) -> TokenPair:
    access_token = token_service.create_access_token(user_id)

    raw_refresh_token = token_service.generate_refresh_token()
    token_hash = token_service.hash_refresh_token(raw_refresh_token)
    expires_at = datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days)

    await refresh_token_repository.create(
        user_id=user_id, token_hash=token_hash, expires_at=expires_at
    )

    return TokenPair(access_token=access_token, refresh_token=raw_refresh_token)
