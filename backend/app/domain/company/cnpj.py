"""Validação e normalização de CNPJ — regra pura, sem I/O (testável isolada)."""


def normalize_cnpj(raw: str) -> str:
    """Remove tudo que não for dígito."""
    return "".join(ch for ch in raw if ch.isdigit())


def _check_digit(digits: str, weights: list[int]) -> int:
    total = sum(int(d) * w for d, w in zip(digits, weights, strict=True))
    remainder = total % 11
    return 0 if remainder < 2 else 11 - remainder


def is_valid_cnpj(raw: str) -> bool:
    """Valida os dígitos verificadores do CNPJ (mesmo algoritmo da Receita).

    Rejeita comprimento != 14 e sequências repetidas (ex.: 00000000000000),
    que passam na aritmética mas nunca são CNPJs reais."""
    cnpj = normalize_cnpj(raw)
    if len(cnpj) != 14 or cnpj == cnpj[0] * 14:
        return False
    first = _check_digit(cnpj[:12], [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2])
    second = _check_digit(cnpj[:13], [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2])
    return cnpj[12] == str(first) and cnpj[13] == str(second)


def format_cnpj(raw: str) -> str:
    """Formata para 00.000.000/0000-00 (retorna o original se não tiver 14 dígitos)."""
    cnpj = normalize_cnpj(raw)
    if len(cnpj) != 14:
        return raw
    return f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"
