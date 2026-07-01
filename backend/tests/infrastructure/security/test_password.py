from app.infrastructure.security.password import Argon2PasswordHasher


def test_hash_and_verify_roundtrip() -> None:
    hasher = Argon2PasswordHasher()
    hashed = hasher.hash("s3cr3t!!")

    assert hashed != "s3cr3t!!"
    assert hasher.verify("s3cr3t!!", hashed) is True


def test_verify_returns_false_for_wrong_password() -> None:
    hasher = Argon2PasswordHasher()
    hashed = hasher.hash("s3cr3t!!")

    assert hasher.verify("outra-senha", hashed) is False


def test_verify_returns_false_for_malformed_hash() -> None:
    hasher = Argon2PasswordHasher()

    assert hasher.verify("s3cr3t!!", "not-a-valid-hash") is False
