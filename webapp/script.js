const screen1 = document.getElementById("screen1");
const screen2 = document.getElementById("screen2");
const screen3 = document.getElementById("screen3");
const screen4 = document.getElementById("screen4");
const insightText = document.getElementById("insight-text");
const contactForm = document.getElementById("contact-form");
const formMessage = document.getElementById("form-message");

let selectedScenario = null;

// Инициализация Telegram WebApp
let tg;
if (window.Telegram && window.Telegram.WebApp) {
  tg = window.Telegram.WebApp;
  tg.ready();
  tg.expand(); // Полноэкранный режим
  tg.enableVerticalSwipes(false); // Отключаем swipe, чтобы не мешал scaling
  console.log("Telegram WebApp initialized. initData:", tg.initData);
} else {
  console.log("Telegram WebApp not detected. Testing outside Telegram?");
}

// Динамическое увеличение шрифта на мобильных устройствах
function adjustFontSize() {
  if (window.innerWidth <= 768) {
    console.log('adjustFontSize called. innerWidth:', window.innerWidth);
    const root = document.documentElement;
    root.style.fontSize = window.innerWidth + 'px'; // Одна буква на экран
    document.body.style.lineHeight = '1';
    document.body.style.fontSize = '1rem';

    // Корректировка элементов
    const elements = document.querySelectorAll('h1, h2, .subtitle, button, input, .insight, .insight li, .cases, .cases li, .primary-link, .message, .container, ul, form');
    elements.forEach(el => {
      el.style.fontSize = '1rem';
      el.style.lineHeight = '1';
      el.style.margin = '0.05rem 0';
      el.style.padding = '0.05rem';
      el.style.overflow = 'auto';
    });
  }
}

// Вызываем сразу, при load, resize и через timeout (на случай задержки рендеринга)
adjustFontSize();
setTimeout(adjustFontSize, 100);
setTimeout(adjustFontSize, 500);
window.addEventListener('load', adjustFontSize);
window.addEventListener('resize', adjustFontSize);
if (tg) {
  tg.onEvent('viewportChanged', adjustFontSize);
}

// Тексты инсайтов и чек-листов (остальное без изменений)
const insights = {
  1: {
    text: `
      <ul>
        <li>80% кризисных проектов срывают сроки и бюджеты из-за подрядчиков, а не технологий.</li>
        <li>Средний перерасход = +30–50% к смете. Это ваш «съеденный ROI».</li>
        <li>Каждый 3-й проект можно спасти за 2–3 недели при правильной архитектуре.</li>
      </ul>`,
    button: 'Получить чек-лист «10 признаков, что проект умирает»'
  },
  // ... (остальные сценарии без изменений)
};

// Валидация и остальной код без изменений (чтобы не ломать функционал)
function validateEmail(email) {
  return /^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$/.test(email);
}

function validateName(name) {
  return /^[А-Яа-яA-Za-zЁё\s-]+$/.test(name);
}

function validateNameLength(name) {
  return name.length >= 2;
}

function showError(message, field = null) {
  formMessage.innerText = message;
  formMessage.style.color = "red";
  formMessage.style.display = "block";
  if (field) field.classList.add("error");
}

function clearError(field = null) {
  formMessage.innerText = "";
  formMessage.style.display = "none";
  if (field) field.classList.remove("error");
}

function showSuccess(message) {
  formMessage.innerText = message;
  formMessage.style.color = "green";
  formMessage.style.display = "block";
}

document.querySelectorAll("#scenario-buttons button").forEach(btn => {
  btn.addEventListener("click", () => {
    selectedScenario = btn.dataset.scenario;
    insightText.innerHTML = insights[selectedScenario].text;
    document.getElementById("next-contact").textContent = insights[selectedScenario].button;
    screen1.classList.add("hidden");
    screen2.classList.remove("hidden");
    adjustFontSize(); // Переприменяем после смены экрана
  });
});

document.getElementById("next-contact").addEventListener("click", () => {
  screen2.classList.add("hidden");
  screen3.classList.remove("hidden");
  adjustFontSize();
});

contactForm.addEventListener("submit", async (e) => {
  e.preventDefault();

  const nameField = contactForm.querySelector("input[name='name']");
  const emailField = contactForm.querySelector("input[name='email']");
  const telegramField = contactForm.querySelector("input[name='telegram']");

  clearError(nameField);
  clearError(emailField);

  const name = nameField.value.trim();
  const email = emailField.value.trim();
  const telegram = telegramField.value.trim();

  if (!name) return showError("Введите имя.", nameField);
  if (!validateName(name)) return showError("Имя должно содержать только буквы, пробелы или дефисы.", nameField);
  if (!validateNameLength(name)) return showError("Имя должно быть минимум 2 символа.", nameField);
  if (!email) return showError("Введите email.", emailField);
  if (!validateEmail(email)) return showError("Введите корректный email.", emailField);

  const data = { name, email, telegram, scenario: selectedScenario };
  if (tg) {
    data.init_data = tg.initData;
    console.log("Отправляем init_data:", data.init_data);
  } else {
    console.log("Нет Telegram WebApp, init_data не передано");
  }

  try {
    const response = await fetch("/submit", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data)
    });

    const result = await response.json();

    if (response.ok && result.status === "ok") {
      showSuccess("Спасибо! Ваши данные отправлены, и вы получите сообщение в Telegram с выбранным сценарием. Наш архитектор свяжется с вами.");
      contactForm.reset();

      setTimeout(() => {
        screen3.classList.add("hidden");
        screen4.classList.remove("hidden");
        adjustFontSize();
      }, 2000);
    } else {
      showError(result.message || "Ошибка отправки. Попробуйте позже.");
    }
  } catch (err) {
    console.error(err);
    showError("Ошибка сети. Попробуйте позже.");
  }
});