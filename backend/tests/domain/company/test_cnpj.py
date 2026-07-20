from app.domain.company.cnpj import format_cnpj, is_valid_cnpj, normalize_cnpj


def test_normalize_strips_non_digits() -> None:
    assert normalize_cnpj("11.222.333/0001-81") == "11222333000181"


def test_valid_cnpj_passes() -> None:
    assert is_valid_cnpj("11.222.333/0001-81") is True
    assert is_valid_cnpj("11222333000181") is True


def test_invalid_check_digits_fail() -> None:
    assert is_valid_cnpj("11222333000180") is False


def test_wrong_length_fails() -> None:
    assert is_valid_cnpj("1122233300018") is False
    assert is_valid_cnpj("112223330001810") is False


def test_repeated_digits_fail() -> None:
    assert is_valid_cnpj("00000000000000") is False
    assert is_valid_cnpj("11111111111111") is False


def test_format_cnpj() -> None:
    assert format_cnpj("11222333000181") == "11.222.333/0001-81"
    assert format_cnpj("123") == "123"
