"""Ajudantes de cadastro para os testes.

O cadastro passou a criar a empresa junto com a conta, e cada empresa consome um
CNPJ único. Sem um gerador, cada teste que cria dois usuários esbarraria na
restrição de unicidade — e o autor do teste perderia tempo inventando CNPJs
válidos à mão.

`valid_cnpj` produz números com dígitos verificadores corretos e determinísticos
a partir de uma semente, para o teste que falha ser reproduzível.
"""

from itertools import count

_PESOS_1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
_PESOS_2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]

_sequencia = count(1)


def _digito(base: str, pesos: list[int]) -> int:
    total = sum(int(d) * p for d, p in zip(base, pesos, strict=True))
    resto = total % 11
    return 0 if resto < 2 else 11 - resto


def valid_cnpj(seed: int | None = None) -> str:
    """CNPJ de 14 dígitos com verificadores corretos.

    Sem `seed`, cada chamada devolve um número diferente — o que a maioria dos
    testes quer, já que dois cadastros não podem repetir CNPJ.
    """
    numero = seed if seed is not None else next(_sequencia)
    base = f"{numero:012d}"
    base += str(_digito(base, _PESOS_1))
    base += str(_digito(base, _PESOS_2))
    return base


def register_payload(
    email: str,
    password: str = "s3cr3t!!",
    full_name: str = "Usuário Teste",
    **extra: object,
) -> dict[str, object]:
    """Corpo completo de `POST /auth/register`.

    Concentrado aqui para que a próxima mudança no contrato do cadastro seja um
    ajuste só, e não uma varredura por 28 arquivos de teste.
    """
    payload: dict[str, object] = {
        "email": email,
        "password": password,
        "password_confirmation": password,
        "full_name": full_name,
        "company_name": "Empresa Teste",
        "cnpj": valid_cnpj(),
    }
    payload.update(extra)
    return payload
