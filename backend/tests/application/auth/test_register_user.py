import pytest

from app.application.auth.register_user import RegisterUserUseCase
from app.core.config import Settings
from app.core.exceptions import ConflictError
from tests.fakes import FakePasswordHasher, FakeUserRepository

pytestmark = pytest.mark.anyio

_SETTINGS = Settings(_env_file=None)  # type: ignore[call-arg]


async def test_registers_a_new_user_with_normalized_data_and_hashed_password() -> None:
    use_case = RegisterUserUseCase(FakeUserRepository(), FakePasswordHasher(), _SETTINGS)

    user = await use_case.execute(
        email="Person@Example.com ", password="s3cr3t!!", full_name="  Ana Silva  "
    )

    assert user.email == "person@example.com"
    assert user.full_name == "Ana Silva"
    assert user.hashed_password == "hashed:s3cr3t!!"
    assert user.is_active is True


async def test_raises_conflict_when_email_already_registered() -> None:
    repository = FakeUserRepository()
    use_case = RegisterUserUseCase(repository, FakePasswordHasher(), _SETTINGS)
    await use_case.execute(email="ana@example.com", password="s3cr3t!!", full_name="Ana")

    with pytest.raises(ConflictError):
        await use_case.execute(email="ANA@example.com", password="outrasenha", full_name="Ana 2")
