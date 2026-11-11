// Тема «Samara»: эффекты старого лендинга «Капелла Плюс» своим кодом вместо GSAP с зарубежного CDN —
// меню, параллакс фона, появление блоков, счётчики, комнаты планировки, перетаскивание галереи.
// Калькулятор, копирование КН, карта, просмотр фото — общий landing.js.
const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;

// меню: появляется и уплотняется при прокрутке
const nav = document.getElementById('navbar');
if (nav) {
  requestAnimationFrame(() => nav.classList.add('ready'));
  const onScroll = () => nav.classList.toggle('scrolled', scrollY > 80);
  addEventListener('scroll', onScroll, { passive: true });
  onScroll();
}

// параллакс фона первого экрана и баннера (как scrub в GSAP: 32 % и 20 % высоты)
const layers = [['heroBg', 0.32], ['winterBg', 0.2]]
  .map(([id, k]) => [document.getElementById(id), k]).filter(([el]) => el);
if (layers.length && !reduce) {
  let ticking = false;
  const move = () => {
    for (const [el, k] of layers) {
      const box = el.parentElement.getBoundingClientRect();
      if (box.bottom < 0 || box.top > innerHeight) continue;
      // первый экран: от «верх у верха» до «низ у верха»; баннер: от «верх у низа» до «низ у верха»
      const progress = el.id === 'heroBg'
        ? Math.max(-box.top, 0) / box.height
        : (innerHeight - box.top) / (innerHeight + box.height);
      el.style.transform = `translateY(${progress * k * box.height}px)`;
    }
    ticking = false;
  };
  addEventListener('scroll', () => { if (!ticking) { ticking = true; requestAnimationFrame(move); } }, { passive: true });
  move();
}

// счётчик: 0 → data-to (с запятой для дробных, как 199,9)
function count(el) {
  const to = Number(el.dataset.to);
  const digits = (el.dataset.to.split('.')[1] || '').length;
  const fmt = (x) => x.toFixed(digits).replace('.', ',');
  if (reduce) { el.textContent = fmt(to); return; }
  const t0 = performance.now(), dur = 1600;
  const step = (t) => {
    const p = Math.min((t - t0) / dur, 1);
    el.textContent = fmt(to * (1 - (1 - p) ** 2));
    if (p < 1) requestAnimationFrame(step);
  };
  requestAnimationFrame(step);
}

// появление блоков и запуск счётчиков при прокрутке
const fu = document.querySelectorAll('.fu');
const counters = document.querySelectorAll('.cnt');
if ('IntersectionObserver' in window && !reduce) {
  const io = new IntersectionObserver((entries) => entries.forEach((e) => {
    if (!e.isIntersecting) return;
    e.target.classList.contains('cnt') ? count(e.target) : e.target.classList.add('in');
    io.unobserve(e.target);
  }), { rootMargin: '0px 0px -11% 0px' });
  fu.forEach((el) => io.observe(el));
  counters.forEach((el) => io.observe(el));
} else {
  fu.forEach((el) => el.classList.add('in'));
  counters.forEach(count);
}

// комнаты планировки: раскрывается одна
document.querySelectorAll('.room').forEach((room) => room.addEventListener('click', () => {
  document.querySelectorAll('.room').forEach((r) => r.classList.toggle('on', r === room));
}));

// галерея: на компьютере ленту можно тянуть мышью
const track = document.getElementById('galleryScroll');
if (track) {
  let down = false, x0 = 0, left0 = 0, moved = false;
  track.addEventListener('mousedown', (e) => { down = true; moved = false; x0 = e.pageX; left0 = track.scrollLeft; track.style.cursor = 'grabbing'; });
  addEventListener('mouseup', () => { down = false; track.style.cursor = ''; });
  track.addEventListener('mousemove', (e) => {
    if (!down) return;
    if (Math.abs(e.pageX - x0) > 5) moved = true;
    e.preventDefault();
    track.scrollLeft = left0 - (e.pageX - x0) * 1.6;
  });
  // протянули — это не нажатие на фото
  track.addEventListener('click', (e) => { if (moved) { e.stopPropagation(); e.preventDefault(); } }, true);
}
