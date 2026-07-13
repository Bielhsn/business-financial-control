import { parseCurrencyToCents } from "@/lib/money";

/**
 * Parser CSV minimalista com suporte a campos entre aspas (descrições de extrato
 * costumam conter vírgulas) e detecção automática de delimitador (`;` — padrão
 * de bancos brasileiros — ou `,`).
 */
export function parseCsv(text: string): string[][] {
  const firstLine = text.slice(0, text.indexOf("\n") === -1 ? undefined : text.indexOf("\n"));
  const delimiter =
    (firstLine.match(/;/g)?.length ?? 0) >= (firstLine.match(/,/g)?.length ?? 0) ? ";" : ",";

  const rows: string[][] = [];
  let field = "";
  let row: string[] = [];
  let inQuotes = false;

  const pushField = () => {
    row.push(field.trim());
    field = "";
  };
  const pushRow = () => {
    pushField();
    if (row.some((value) => value !== "")) {
      rows.push(row);
    }
    row = [];
  };

  for (let i = 0; i < text.length; i++) {
    const char = text[i];
    if (inQuotes) {
      if (char === '"') {
        if (text[i + 1] === '"') {
          field += '"';
          i++;
        } else {
          inQuotes = false;
        }
      } else {
        field += char;
      }
    } else if (char === '"') {
      inQuotes = true;
    } else if (char === delimiter) {
      pushField();
    } else if (char === "\n") {
      pushRow();
    } else if (char !== "\r") {
      field += char;
    }
  }
  if (field !== "" || row.length > 0) {
    pushRow();
  }
  return rows;
}

export interface ParsedImportRow {
  date: string; // ISO
  description: string;
  amount_cents: number; // assinado: negativo = despesa
  category_name: string | null;
  paid: boolean;
}

export interface ImportParseResult {
  rows: ParsedImportRow[];
  errors: string[];
}

const DATE_HEADERS = ["data", "date", "dia"];
const DESCRIPTION_HEADERS = ["descricao", "descrição", "description", "historico", "histórico"];
const AMOUNT_HEADERS = ["valor", "amount", "value", "montante"];
const CATEGORY_HEADERS = ["categoria", "category"];

function parseDate(raw: string): string | null {
  const brazilian = raw.match(/^(\d{2})[/-](\d{2})[/-](\d{4})$/);
  if (brazilian) {
    const day = Number(brazilian[1]);
    const month = Number(brazilian[2]);
    const year = Number(brazilian[3]);
    const date = new Date(year, month - 1, day);
    // O Date do JS "rola" valores fora do intervalo (mês 99 vira ano seguinte);
    // o round-trip garante que a data informada existe de verdade.
    const roundTrips =
      date.getFullYear() === year && date.getMonth() === month - 1 && date.getDate() === day;
    return roundTrips ? date.toISOString() : null;
  }
  const iso = raw.match(/^(\d{4})-(\d{2})-(\d{2})/);
  if (iso) {
    const date = new Date(raw);
    return Number.isNaN(date.getTime()) ? null : date.toISOString();
  }
  return null;
}

/** Valor assinado de extrato: "-1.234,56", "1234.56", "R$ 100,00". */
function parseSignedCents(raw: string): number | null {
  const negative = raw.trim().startsWith("-");
  const cents = parseCurrencyToCents(raw.replace(/^-/, "").trim());
  if (cents === null) {
    return null;
  }
  return negative ? -cents : cents;
}

/**
 * Converte um CSV de extrato/planilha em linhas de importação.
 * Com cabeçalho reconhecido, mapeia por nome de coluna; sem cabeçalho,
 * assume a ordem posicional: data, descrição, valor[, categoria].
 */
export function parseImportCsv(text: string): ImportParseResult {
  const table = parseCsv(text);
  if (table.length === 0) {
    return { rows: [], errors: ["Arquivo vazio."] };
  }

  const header = table[0]!.map((cell) => cell.toLowerCase());
  const dateIdx = header.findIndex((h) => DATE_HEADERS.includes(h));
  const hasHeader = dateIdx !== -1;
  const descriptionIdx = hasHeader ? header.findIndex((h) => DESCRIPTION_HEADERS.includes(h)) : 1;
  const amountIdx = hasHeader ? header.findIndex((h) => AMOUNT_HEADERS.includes(h)) : 2;
  const categoryIdx = hasHeader ? header.findIndex((h) => CATEGORY_HEADERS.includes(h)) : 3;

  if (hasHeader && (descriptionIdx === -1 || amountIdx === -1)) {
    return {
      rows: [],
      errors: ["Cabeçalho encontrado, mas faltam as colunas de descrição e/ou valor."],
    };
  }

  const dataRows = hasHeader ? table.slice(1) : table;
  const rows: ParsedImportRow[] = [];
  const errors: string[] = [];

  dataRows.forEach((cells, index) => {
    const lineNumber = index + (hasHeader ? 2 : 1);
    const date = parseDate(cells[hasHeader ? dateIdx : 0] ?? "");
    const description = cells[descriptionIdx] ?? "";
    const amount = parseSignedCents(cells[amountIdx] ?? "");
    if (date === null) {
      errors.push(`Linha ${lineNumber}: data inválida (use DD/MM/AAAA ou AAAA-MM-DD).`);
      return;
    }
    if (description.trim() === "") {
      errors.push(`Linha ${lineNumber}: descrição vazia.`);
      return;
    }
    if (amount === null || amount === 0) {
      errors.push(`Linha ${lineNumber}: valor inválido.`);
      return;
    }
    rows.push({
      date,
      description: description.trim(),
      amount_cents: amount,
      category_name: categoryIdx !== -1 ? cells[categoryIdx]?.trim() || null : null,
      paid: true,
    });
  });

  return { rows, errors };
}
