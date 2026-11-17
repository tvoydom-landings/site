// Лендинг объекта: калькулятор (тот же движок, что у Продажника — calc/mortgage.mjs, цифры — data/mortgage.json), копирование КН,
// просмотр фото, липкая кнопка на телефоне. Без зависимостей и внешних скриптов.
import {
  calculate, minDownPayment, maxLoan, maxLoanText, kidsPhrase, termLabel, yearsText, pctText,
  MAX_TERM, MAX_KIDS, FIRST_PERIOD, PROGRAM, RATES,
} from './calc/mortgage.mjs';

const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];
const rub = (n) => new Intl.NumberFormat('ru-RU', { maximumFractionDigits: 0 }).format(Math.round(n));
const kop = (n) => new Intl.NumberFormat('ru-RU', { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(n);
const pct = (x) => `${String(Math.round(x * 1000) / 10).replace('.', ',')} %`;
const digits = (s) => Number(String(s).replace(/\D/g, '')) || 0;

// ---------- калькулятор ----------
function initCalc(box) {
  const price = Number(box.dataset.price);
  const st = { kids: 2, disabled: false, term: MAX_TERM, down: minDownPayment(price, 2), note: '' };
  const down = $('#down', box), downRange = $('#down-range', box), loan = $('#loan', box), term = $('#term', box);
  const maxDown = Math.round(price * 0.9);

  const clampDown = () => {
    st.down = Math.min(Math.max(st.down, minDownPayment(price, st.kids)), maxDown);
  };

  $$('[data-kids]', box).forEach((b) => b.addEventListener('click', () => {
    st.kids = Number(b.dataset.kids);
    const min = minDownPayment(price, st.kids);
    st.note = st.down < min ? `Взнос поднят до ${rub(min)} ₽: ${maxLoanText(st.kids).toLowerCase()}` : '';
    clampDown();
    render(true);
  }));
  $('#disabled', box).addEventListener('change', (e) => { st.disabled = e.target.checked; render(true); });
  down.addEventListener('input', () => { st.down = digits(down.value); st.note = ''; render(false, down); });
  loan.addEventListener('input', () => { st.down = price - digits(loan.value); st.note = ''; render(false, loan); });
  for (const el of [down, loan]) el.addEventListener('change', () => { clampDown(); render(true); });
  downRange.addEventListener('input', () => { st.down = Number(downRange.value); st.note = ''; render(true); });
  term.addEventListener('input', () => { st.term = Number(term.value); render(true); });

  function render(syncInputs, typing = null) {
    const r = calculate({ price, children: st.kids, downPayment: st.down, termMonths: st.term, disabledChild: st.disabled });
    const minDown = minDownPayment(price, st.kids), limit = maxLoan(st.kids);
    $$('[data-kids]', box).forEach((b) => b.setAttribute('aria-pressed', String(Number(b.dataset.kids) === st.kids)));
    downRange.min = String(minDown);
    downRange.max = String(maxDown);
    downRange.step = '10000';
    if (syncInputs || typing !== down) down.value = rub(st.down);
    if (syncInputs || typing !== loan) loan.value = rub(Math.max(price - st.down, 0));
    downRange.value = String(st.down);
    $('#term-label', box).textContent = termLabel(st.term);

    const soft = (code) => (r.errors || []).find((e) => e.code === code);
    const tooSmall = soft('minDown'), tooBig = soft('maxLoan');
    $('#f-down', box).classList.toggle('bad', Boolean(tooSmall || tooBig));
    $('#f-loan', box).classList.toggle('bad', Boolean(tooBig));
    $('#down-hint', box).textContent = st.note
      || (tooBig ? `${tooBig.message}: взнос от ${rub(minDown)} ₽`
        : tooSmall ? `Минимум ${pctText(PROGRAM.minDownPercent)} % — ${rub(minDown)} ₽`
          : `${pct(st.down / price)} от цены · минимум ${rub(minDown)} ₽`);
    $('#loan-hint', box).textContent = `Не больше ${rub(Math.min(limit, price - minDownPayment(price)))} ₽ ${kidsPhrase(st.kids)}`;

    if (!r.price) {                       // ввод не разобрался — ждём исправления
      $('#pay', box).textContent = '—';
      return;
    }
    $('#pay', box).textContent = rub(r.payment);
    $('#pay-sub', box).textContent = st.term > FIRST_PERIOD ? `первые ${yearsText(PROGRAM.subsidyYears)}` : `весь срок — ${termLabel(st.term)}`;
    $('#r-rate', box).textContent = pct(r.rate);
    $('#r-down', box).textContent = `${rub(r.downPayment)} ₽`;
    $('#r-loan', box).textContent = `${rub(r.loan)} ₽`;
    $('#r-term', box).textContent = termLabel(r.termMonths);
    const after = $('#after15', box);
    after.hidden = r.paymentAfter15Years === null;
    if (!after.hidden) {
      after.innerHTML = `С ${PROGRAM.subsidyYears + 1}-го года: <b>${kop(r.paymentAfter15Years)} ₽/мес.</b> — ставка ${pct(r.rateAfter15Years)}`;
    }
    const special = $('#special', box);
    special.hidden = !r.special;
    special.textContent = r.special ? `Ставка ${pct(RATES.special)} — ${r.specialReason}` : '';
    table();
  }

  function table() {
    $('#kids-rows', box).innerHTML = Array.from({ length: MAX_KIDS }, (_, i) => i + 1).map((k) => {
      const r = calculate({ price, children: k, termMonths: st.term });
      const after = r.paymentAfter15Years === null ? '—' : `${rub(r.paymentAfter15Years)} ₽`;
      return `<tr${k === st.kids ? ' class="current"' : ''}><td>${k === MAX_KIDS ? `${k}+` : k}</td><td>${pct(r.rate)}</td>`
        + `<td class="wide">${rub(maxLoan(k) / 1e6)} млн</td><td>${rub(r.downPayment)} ₽</td><td>${rub(r.payment)} ₽</td>`
        + `<td class="wide">${after}</td></tr>`;
    }).join('');
  }

  term.max = String(MAX_TERM);
  term.value = String(st.term);
  render(true);
}

// ---------- кадастровые номера: копирование одним нажатием ----------
function initCopy() {
  $$('[data-copy]').forEach((b) => {
    const label = $('.copied', b);
    const text = label.textContent;
    b.addEventListener('click', async () => {
      try {
        await navigator.clipboard.writeText(b.dataset.copy);
        label.textContent = 'скопировано ✓';
      } catch {
        label.textContent = 'выделите и скопируйте';
      }
      setTimeout(() => { label.textContent = text; }, 2000);
    });
  });
}

// ---------- просмотр фото ----------
function initGallery() {
  const items = $$('[data-full]');
  const lb = $('.lightbox');
  if (!items.length || !lb) return;
  let i = 0;
  const img = $('img', lb);
  const show = (n) => {
    i = (n + items.length) % items.length;
    img.src = items[i].dataset.full;
    img.alt = items[i].querySelector('img').alt;
    $('.lb-count', lb).textContent = `${i + 1} из ${items.length}`;
  };
  const close = () => { lb.classList.remove('open'); document.body.style.overflow = ''; };
  items.forEach((b, n) => b.addEventListener('click', () => {
    show(n); lb.classList.add('open'); document.body.style.overflow = 'hidden'; $('.lb-close', lb).focus();
  }));
  $('.lb-close', lb).addEventListener('click', close);
  $('.lb-prev', lb).addEventListener('click', () => show(i - 1));
  $('.lb-next', lb).addEventListener('click', () => show(i + 1));
  lb.addEventListener('click', (e) => { if (e.target === lb) close(); });
  document.addEventListener('keydown', (e) => {
    if (!lb.classList.contains('open')) return;
    if (e.key === 'Escape') close();
    if (e.key === 'ArrowLeft') show(i - 1);
    if (e.key === 'ArrowRight') show(i + 1);
  });
  let x0 = null;
  lb.addEventListener('touchstart', (e) => { x0 = e.touches[0].clientX; }, { passive: true });
  lb.addEventListener('touchend', (e) => {
    if (x0 === null) return;
    const dx = e.changedTouches[0].clientX - x0;
    if (Math.abs(dx) > 50) show(i + (dx < 0 ? 1 : -1));
    x0 = null;
  });
}

// ---------- липкая кнопка: видна, пока не на первом экране и не у калькулятора ----------
function initSticky() {
  const sticky = $('.sticky'), hero = $('.hero'), calc = $('#calc');
  if (!sticky || !hero || !calc || !('IntersectionObserver' in window)) return;
  const seen = new Map();
  const io = new IntersectionObserver((entries) => {
    entries.forEach((e) => seen.set(e.target, e.isIntersecting));
    sticky.classList.toggle('hide', Boolean(seen.get(hero) || seen.get(calc)));
  });
  io.observe(hero);
  io.observe(calc);
}

const calcBox = $('.calc');
if (calcBox) initCalc(calcBox);
initCopy();
initGallery();
initSticky();
