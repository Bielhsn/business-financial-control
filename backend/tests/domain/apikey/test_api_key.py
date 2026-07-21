from app.domain.apikey.entities import (
    api_key_prefix,
    generate_api_key,
    hash_api_key,
)


def test_generated_key_has_prefix_and_is_unique() -> None:
    a = generate_api_key()
    b = generate_api_key()
    assert a.startswith("aur_")
    assert a != b


def test_prefix_is_short_and_not_the_full_key() -> None:
    raw = generate_api_key()
    prefix = api_key_prefix(raw)
    assert prefix.startswith("aur_")
    assert len(prefix) < len(raw)
    assert raw.startswith(prefix)


def test_hash_is_deterministic_and_secret_dependent() -> None:
    raw = generate_api_key()
    assert hash_api_key(raw, secret="s1") == hash_api_key(raw, secret="s1")
    assert hash_api_key(raw, secret="s1") != hash_api_key(raw, secret="s2")
    # O hash não revela a chave.
    assert raw not in hash_api_key(raw, secret="s1")
