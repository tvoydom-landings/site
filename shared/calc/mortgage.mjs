// Ипотечный калькулятор «Семейная ипотека» — движок расчёта.
// Повторяет формулы калькулятора ДОМ.РФ (лист «Параметры (партнер)» и график «Со снижением (партнер)»)
// с точностью до копейки. Один код для браузера (лендинг, мини-приложения) и Node (Продажник, бот MAX).
// Без зависимостей. Даты — календарные дни без часовых поясов.
// Все цифры программы (ставки, лимиты, взнос, сроки) — в program.json → rates.mjs (make calc), здесь только формулы.
import { PROGRAM } from './rates.mjs';

const P = PROGRAM;
export { PROGRAM };
const byKids = (obj, f = (v) => v) => Object.fromEntries(Object.entries(obj).map(([k, v]) => [k, f(v)]));
const permille = (percent) => Math.round(percent * 10);   // 20,1 % → 201 ‰: сравниваем целыми, без ошибок округления
export const RATES = {
  source: P.source,
  checked: P.checked,
  byChildren: byKids(P.rateByChildrenPercent, (v) => v / 100),   // детей → ставка; последняя строка = «и более»
  special: P.specialRatePercent / 100,                          // «Семейная ипотека_Особое»
  step: P.rateStepPercent / 100,                                // + к ставке после льготного периода
  maxLoanByChildren: byKids(P.maxLoanByChildren),
};
export const MAX_KIDS = Object.keys(P.rateByChildrenPercent).length;
export const MAX_TERM = P.maxTermYears * 12;
export const MIN_TERM = P.minTermMonths;
export const FIRST_PERIOD = P.subsidyYears * 12; // месяцев по ставке на дату договора
const MIN_DOWN = permille(P.minDownPercent);
const SPECIAL_DOWN = permille(P.specialFromDownPercent);
export const pctText = (x) => String(x).replace('.', ',');   // 20.1 → «20,1»
export const MIN_DOWN_TEXT = `Первоначальный взнос не может быть меньше ${pctText(P.minDownPercent)} % от стоимости объекта`;

// Условия программы одной фразой — для описаний инструментов Продажника (цифры только из program.json).
export const PROGRAM_TEXT = (() => {
  const top = Object.keys(P.rateByChildrenPercent).length;
  const kid = (k) => (Number(k) === top ? `${k}+` : k);
  const rates = Object.entries(P.rateByChildrenPercent).map(([k, v]) => `${kid(k)} — ${pctText(v)} %`).join(', ');
  const limits = Object.entries(P.maxLoanByChildren).map(([k, v]) => `${kid(k)} — ${pctText(v / 1e6)} млн`).join(', ');
  return `Ставка по числу детей: ${rates}; особая ${pctText(P.specialRatePercent)} % (взнос от `
    + `${pctText(P.specialFromDownPercent)} % или ребёнок с инвалидностью, только понижает); лимит кредита: ${limits}; `
    + `взнос от ${pctText(P.minDownPercent)} %; льгота ${P.subsidyYears} лет, затем ставка + ${pctText(P.rateStepPercent)} п.п.; `
    + `срок до ${P.maxTermYears} лет. Условия на ${P.checked}.`;
})();

const DAY_MS = 86400000;

// ROUND из Excel: половина — от нуля. Считаем по кратчайшей десятичной записи числа,
// как это видит Excel, а не по двоичному представлению (1.005 → 1.01).
export function excelRound(x, digits = 0) {
  if (!Number.isFinite(x) || x === 0) return x === 0 ? 0 : x;
  const sign = x < 0 ? -1 : 1;
  const [mant, exp = '0'] = Math.abs(x).toString().split('e');
  const shifted = Math.round(Number(`${mant}e${Number(exp) + digits}`));
  const r = Number(`${shifted}e${-digits}`);
  return r === 0 ? 0 : sign * r;
}

// PMT из Excel (платёж в конце периода, без остаточной стоимости).
export function pmt(rate, nper, pv) {
  if (nper === 0) throw new RangeError('#NUM!');
  if (rate === 0) return -pv / nper;
  const f = (1 + rate) ** nper;
  return -(pv * f) * rate / (f - 1);
}

const kidsKey = (children) => Math.min(Math.max(Math.trunc(children), 1), MAX_KIDS);

// Лимит кредита по числу детей (в файле банка его нет — решение владельца 2026-11-01).
export function maxLoan(children) {
  return RATES.maxLoanByChildren[kidsKey(children)];
}

const KIDS_WORD = { 2: 'двух', 3: 'трёх', 4: 'четырёх', 5: 'пяти', 6: 'шести', 7: 'семи' };

// «при одном ребёнке», «при двух детях»; если лимит тот же и у всех семей с бо́льшим числом детей —
// «при трёх и более детях» (по таблице maxLoanByChildren, без жёстких цифр).
export function kidsPhrase(children) {
  const n = kidsKey(children);
  const limit = maxLoan(n);
  let sameToEnd = true;
  for (let k = n; k <= MAX_KIDS; k++) if (maxLoan(k) !== limit) sameToEnd = false;
  if (sameToEnd) {
    let m = n;
    while (m > 1 && maxLoan(m - 1) === limit) m -= 1;
    if (m === 1) return 'при любом числе детей';
    return `при ${KIDS_WORD[m] ?? m} и более детях`;
  }
  return n === 1 ? 'при одном ребёнке' : `при ${KIDS_WORD[n] ?? n} детях`;
}

export function maxLoanText(children) {
  return `Кредит по семейной ипотеке ${kidsPhrase(children)} — не более ${pctText(maxLoan(children) / 1e6)} млн ₽`;
}

// Минимальный взнос: процент из program.json (вверх до рубля, чтобы не оказаться ниже порога), а если указано
// число детей — не меньше, чем нужно, чтобы кредит уложился в лимит.
export function minDownPayment(price, children) {
  const byPercent = Math.ceil((price * MIN_DOWN) / 1000);
  return children === undefined ? byPercent : Math.max(byPercent, price - maxLoan(children));
}

export function isDownPaymentTooSmall(price, downPayment) {
  return downPayment * 1000 < price * MIN_DOWN;
}

// «192 мес. = 16 лет», «190 мес. = 15 лет 10 мес.»
export function termLabel(months) {
  const y = Math.floor(months / 12);
  const m = months % 12;
  const years = y === 0 ? '' : `${y} ${plural(y, 'год', 'года', 'лет')}`;
  const rest = m === 0 ? '' : `${m} мес.`;
  return `${months} мес. = ${[years, rest].filter(Boolean).join(' ')}`;
}

export const yearsText = (n) => `${n} ${plural(n, 'год', 'года', 'лет')}`;

function plural(n, one, few, many) {
  const d = n % 10, h = n % 100;
  if (d === 1 && h !== 11) return one;
  if (d >= 2 && d <= 4 && (h < 12 || h > 14)) return few;
  return many;
}

// Ставка по таблице файла. «Особая» — если ребёнок-инвалид или ПВ от specialFromDownPercent (50 %).
// Отступления от файла банка (решение владельца 2026-10-28): ровно 50 % тоже даёт особую ставку
// (в файле — строго больше), и особая ставка только понижает: если по детям ниже (4 и 5+), берём её.
export function rateFor({ children, disabledChild = false, price, downPayment }) {
  const byKids = RATES.byChildren[kidsKey(children)];
  const bigDown = downPayment * 1000 >= price * SPECIAL_DOWN;
  if ((disabledChild || bigDown) && RATES.special < byKids) {
    const reason = disabledChild ? 'ребёнок с инвалидностью' : `взнос от ${pctText(P.specialFromDownPercent)} %`;
    return { rate: RATES.special, special: true, reason };
  }
  return { rate: byKids, special: false, reason: null };
}

// Дата → номер дня; 'ГГГГ-ММ-ДД' или Date (берётся календарная дата по местному времени).
function dayNumber(date) {
  if (typeof date === 'string') {
    const [y, m, d] = date.split('-').map(Number);
    return Date.UTC(y, m - 1, d) / DAY_MS;
  }
  return Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()) / DAY_MS;
}

function endOfMonth(day, k) {
  const d = new Date(day * DAY_MS);
  return Date.UTC(d.getUTCFullYear(), d.getUTCMonth() + k + 1, 0) / DAY_MS;
}

function daysInYear(day) {
  const y = new Date(day * DAY_MS).getUTCFullYear();
  return (y % 4 === 0 && y % 100 !== 0) || y % 400 === 0 ? 366 : 365;
}

// «Мягкие» ошибки: расчёт всё равно выполняется, поле подсвечивается красным.
const SOFT_ERRORS = new Set(['minDown', 'maxLoan']);

export function validate({ price, downPayment, termMonths, children }) {
  const errors = [];
  const kidsOk = Number.isInteger(children) && children >= 1;
  if (!(Number.isInteger(price) && price > 0)) errors.push({ field: 'price', message: 'Укажите стоимость объекта' });
  if (!(Number.isInteger(downPayment) && downPayment >= 0 && downPayment < price)) {
    errors.push({ field: 'downPayment', message: 'Первоначальный взнос должен быть меньше стоимости объекта' });
  } else {
    if (isDownPaymentTooSmall(price, downPayment)) {
      errors.push({ field: 'downPayment', code: 'minDown', message: MIN_DOWN_TEXT });
    }
    if (kidsOk && price - downPayment > maxLoan(children)) {
      errors.push({ field: 'downPayment', code: 'maxLoan', message: maxLoanText(children) });
    }
  }
  if (!(Number.isInteger(termMonths) && termMonths >= MIN_TERM && termMonths <= MAX_TERM)) {
    errors.push({ field: 'termMonths', message: `Срок — от ${MIN_TERM} до ${MAX_TERM} мес.` });
  }
  if (!kidsOk) errors.push({ field: 'children', message: 'Укажите число детей' });
  return errors;
}

// Главный расчёт. Вход: price, downPayment (₽, целые; по умолчанию минимальный с учётом лимита
// кредита), termMonths (по умолчанию MAX_TERM), children (1…MAX_KIDS, последнее = «и более»), disabledChild,
// issueDate (по умолчанию сегодня; влияет только на дни в месяцах графика, а значит на платёж
// после 15 лет и переплату — на копейки/рубли).
export function calculate({
  price, children, downPayment = minDownPayment(price, children), termMonths = MAX_TERM,
  disabledChild = false, issueDate = new Date(), withSchedule = false,
}) {
  const errors = validate({ price, downPayment, termMonths, children });
  if (errors.some((e) => !SOFT_ERRORS.has(e.code))) {
    return { valid: false, errors };
  }
  const n = termMonths;
  const loan = price - downPayment;
  const { rate, special, reason } = rateFor({ children, disabledChild, price, downPayment });
  const rateAfter = rate + RATES.step;
  const firstPeriod = Math.min(n, FIRST_PERIOD);
  const payment = excelRound(-pmt(rate / 12, n - 1, loan), 0); // в файле срок − 1: в первом месяце платежа нет

  // График: как в листе «Со снижением (партнер)», строка = месяц.
  const issue = dayNumber(issueDate);
  let prevEnd = issue, balance = loan, accrued = 0, prevInterest = 0, total = 0;
  let paymentAfterRaw = null, balanceAfterFirst = null, firstPayment = null, lastPayment = null;
  const schedule = [];
  for (let k = 1; k <= n; k++) {
    const end = endOfMonth(issue, k - 1);
    const days = end - prevEnd;
    const monthRate = k <= firstPeriod ? rate : rateAfter;
    const debt = balance + accrued;
    const interest = excelRound(balance * monthRate / daysInYear(end) * days, 2);
    let pay;
    if (k === 1) {
      pay = 0;
    } else {
      const regular = k <= firstPeriod ? payment : paymentAfterRaw;
      pay = k === 2
        ? excelRound(Math.min(regular, debt + interest) + prevInterest, 2)
        : excelRound(k === n ? debt + interest : Math.min(regular, debt + interest), 2);
    }
    const paidAccrued = Math.min(pay, accrued);
    const paidInterest = Math.min(pay - paidAccrued, interest);
    const principal = Math.min(pay - paidAccrued - paidInterest, balance);
    const newAccrued = Math.max(interest - paidInterest, 0);
    const startBalance = balance;
    balance = balance - principal;
    accrued = accrued + newAccrued - paidAccrued;
    total += pay;
    if (withSchedule) schedule.push({ month: k, date: isoDate(end), payment: pay, interest, principal, balance, startBalance });
    prevEnd = end;
    prevInterest = interest;
    if (k === firstPeriod) {
      balanceAfterFirst = balance;
      // платёж после льготы (с 181-го месяца): остаток на 180-й месяц, ставка + step, срок − 180 − 1 (как в файле)
      if (n - FIRST_PERIOD - 1 >= 1) paymentAfterRaw = -pmt(rateAfter / 12, n - FIRST_PERIOD - 1, balance);
    }
    if (k === 2) firstPayment = pay;
    if (k === n) lastPayment = pay;
  }
  // Срок 181 мес.: в файле здесь ошибка #ЧИСЛО!; на деле 181-й платёж — последний, гасит остаток.
  const paymentAfter = n <= FIRST_PERIOD ? null
    : paymentAfterRaw === null ? lastPayment : excelRound(paymentAfterRaw, 2);

  return {
    valid: errors.length === 0,
    errors,
    price, downPayment, downPaymentPercent: downPayment / price, loan, termMonths: n, termLabel: termLabel(n),
    maxLoan: maxLoan(children),   // лимит кредита по числу детей — граница поля «сумма кредита»
    minDownPayment: minDownPayment(price, children), // граница поля «первоначальный взнос»
    children, disabledChild, issueDate: isoDate(issue),
    rate, rateAfter15Years: rateAfter, special, specialReason: reason,
    payment,                      // ₽ в месяц, месяцы 2–180 (целые рубли, как в файле)
    firstPayment,                 // первый платёж (2-й месяц): обычный + проценты за дни 1-го месяца
    paymentAfter15Years: paymentAfter, // ₽ с 181-го месяца (до копеек); null — срок не больше 180 мес.
    paymentAfterRaw,
    balanceAfter15Years: n > FIRST_PERIOD ? balanceAfterFirst : null,
    overpayment: total - loan,
    lastPayment,
    schedule: withSchedule ? schedule : undefined,
  };
}

function isoDate(day) {
  return new Date(day * DAY_MS).toISOString().slice(0, 10);
}
