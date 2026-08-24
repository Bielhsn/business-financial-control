/**
 * Máscara e validação de CNPJ no cliente.
 *
 * A validação daqui é conveniência — dizer "confira os números" antes de gastar
 * uma ida ao servidor. A regra que vale continua sendo a do backend, que além
 * dos dígitos confronta o CNPJ com a Receita e garante a unicidade no banco.
 */

const PESOS_1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2];
const PESOS_2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2];

export function onlyDigits(value: string): string {
  return value.replace(/\D/g, "");
}

/** Formata progressivamente enquanto a pessoa digita: 00.000.000/0000-00 */
export function maskCnpj(value: string): string {
  const digits = onlyDigits(value).slice(0, 14);
  if (digits.length <= 2) return digits;
  if (digits.length <= 5) return `${digits.slice(0, 2)}.${digits.slice(2)}`;
  if (digits.length <= 8) return `${digits.slice(0, 2)}.${digits.slice(2, 5)}.${digits.slice(5)}`;
  if (digits.length <= 12)
    return `${digits.slice(0, 2)}.${digits.slice(2, 5)}.${digits.slice(5, 8)}/${digits.slice(8)}`;
  return `${digits.slice(0, 2)}.${digits.slice(2, 5)}.${digits.slice(5, 8)}/${digits.slice(
    8,
    12,
  )}-${digits.slice(12)}`;
}

function checkDigit(base: string, pesos: number[]): number {
  const total = base
    .split("")
    .reduce((soma, digito, index) => soma + Number(digito) * (pesos[index] ?? 0), 0);
  const resto = total % 11;
  return resto < 2 ? 0 : 11 - resto;
}

export function isValidCnpj(value: string): boolean {
  const cnpj = onlyDigits(value);
  // Sequências repetidas (00000000000000) passam na conta dos dígitos
  // verificadores e não existem — o descarte precisa ser explícito.
  if (cnpj.length !== 14 || /^(\d)\1{13}$/.test(cnpj)) {
    return false;
  }
  return (
    Number(cnpj[12]) === checkDigit(cnpj.slice(0, 12), PESOS_1) &&
    Number(cnpj[13]) === checkDigit(cnpj.slice(0, 13), PESOS_2)
  );
}
