const demoInput = document.querySelector('#demo-input');
const demoOutput = document.querySelector('#demo-output');

const demoPhrases = new Map([
  ['ami banglay likhi', 'আমি বাংলায় লিখি'],
  ['amar bangla', 'আমার বাংলা'],
  ['bangla amar bhasha', 'বাংলা আমার ভাষা'],
  ['bhalo achi', 'ভালো আছি'],
  ['dhonnobad', 'ধন্যবাদ'],
  ['bongo', 'বঙ্গ']
]);

function updateDemo() {
  const input = demoInput.value.trim().toLowerCase();
  demoOutput.textContent = demoPhrases.get(input) || (input ? 'বাংলা লিখুন…' : 'এখানে বাংলা দেখুন');
}

demoInput?.addEventListener('input', updateDemo);

const tabs = [...document.querySelectorAll('[role="tab"]')];
function activateTab(tab) {
  tabs.forEach((item) => {
    const selected = item === tab;
    item.setAttribute('aria-selected', String(selected));
    item.tabIndex = selected ? 0 : -1;
    document.querySelector(`#${item.getAttribute('aria-controls')}`).hidden = !selected;
  });
  tab.focus();
}

tabs.forEach((tab, index) => {
  tab.addEventListener('click', () => activateTab(tab));
  tab.addEventListener('keydown', (event) => {
    if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return;
    event.preventDefault();
    let next = index;
    if (event.key === 'ArrowLeft') next = (index - 1 + tabs.length) % tabs.length;
    if (event.key === 'ArrowRight') next = (index + 1) % tabs.length;
    if (event.key === 'Home') next = 0;
    if (event.key === 'End') next = tabs.length - 1;
    activateTab(tabs[next]);
  });
});

const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
const reveals = document.querySelectorAll('.reveal');
if (reducedMotion || !('IntersectionObserver' in window)) {
  reveals.forEach((element) => element.classList.add('visible'));
} else {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.12 });
  reveals.forEach((element) => observer.observe(element));
}
