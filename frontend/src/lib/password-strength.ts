/**
 * Força da senha, para o indicador visual do cadastro.
 *
 * Mede variedade e comprimento, que é o que o usuário controla no momento de
 * escolher. Não substitui a regra do servidor (mínimo de 8 caracteres) — serve
 * para orientar antes do envio, não para autorizar.
 *
 * Deliberadamente simples: uma biblioteca de entropia acertaria mais, mas
 * carregaria centenas de kB no caminho crítico do cadastro para melhorar um
 * indicador que é orientativo.
 */

export type PasswordStrength = "fraca" | "média" | "forte";

export interface PasswordAssessment {
  strength: PasswordStrength;
  /** 0 a 4 — quantos critérios a senha atende, para desenhar a barra. */
  score: number;
  /** O que falta para melhorar, em uma frase. Vazio quando já está forte. */
  hint: string;
}

export function assessPassword(password: string): PasswordAssessment {
  if (password.length === 0) {
    return { strength: "fraca", score: 0, hint: "" };
  }

  const criterios = [
    password.length >= 10,
    /[a-z]/.test(password) && /[A-Z]/.test(password),
    /\d/.test(password),
    /[^A-Za-z0-9]/.test(password),
  ];
  const score = criterios.filter(Boolean).length;

  // Comprimento mínimo tem peso próprio: uma senha de 8 caracteres variados
  // ainda é curta, e passar "forte" nela daria uma segurança que não existe.
  if (password.length < 8) {
    return { strength: "fraca", score: Math.min(score, 1), hint: "Use ao menos 8 caracteres." };
  }

  if (score <= 1) {
    return { strength: "fraca", score: 1, hint: "Misture letras maiúsculas, números e símbolos." };
  }
  if (score <= 2) {
    return { strength: "média", score: 2, hint: "Acrescente um número ou um símbolo." };
  }
  if (score === 3) {
    return { strength: "média", score: 3, hint: "Quase lá — um símbolo deixa mais difícil." };
  }
  return { strength: "forte", score: 4, hint: "" };
}
