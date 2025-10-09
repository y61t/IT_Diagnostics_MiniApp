// ---------- config ----------
const BOT_USERNAME = "IT_DiagnosticsBot"; // <-- Замените на username вашего бота без @, например: my_bot
// -----------------------------

const screen1 = document.getElementById("screen1");
const screen2 = document.getElementById("screen2");
const screen3 = document.getElementById("screen3");
const screen4 = document.getElementById("screen4");
const insightText = document.getElementById("insight-text");
const contactForm = document.getElementById("contact-form");
const formMessage = document.getElementById("form-message");

// optional container in index.html for Telegram Login Widget
// <div id="tg-login"></div>
const tgLoginContainerId = "tg-login";

let selectedScenario = null;
let telegramAuth = null; // will store Telegram Login Widget result if user auths

// Minimal insights (same as before)
const insights = {
  1: { text: "<ul><li>80% кризисных проектов...</li></ul>", button: 'Получить чек-лист «10 признаков»' },
  2: { text: "<ul><li>70% проектов проваливаются...</li></ul>", button: 'Получить чек-лист «5 ошибок»' },
  3: { text: "<ul><li>7 из 10 компаний выбирают софт...</li></ul>", button: 'Получить чек-лист «7 ошибок импортозамещения»' },
  4: { text: "<ul><li>Подрядчик считает часы...</li></ul>", button: 'Получить чек-лист «5 сигналов»' },
  5: { text: "<ul><li>Конкуренты уже автоматизировали...</li></ul>", button: 'Получить чек-лист «5 признаков»' },
  6: { text: "<ul><li>ROI никто не считает...</li></ul>", button: 'Получить чек-лист «7 признаков»' }
};

// Validation
function validateEmail(email) {
  return /^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$/.test(email);
}
function validateName(name) {
  return /^[А-Яа-яA-Za-zЁё\s-]+$/.test(name) && name.length >= 2;
}

// UI helpers
function showError(message, field = null) {
  console.log("❌ Ошибка:", message);
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
  console.log("✅ Успех:", message);
  formMessage.innerText = message;
  formMessage.style.color = "green";
  formMessage.style.display = "block";
}

// Render Telegram Login Widget (if container exists)
function renderTelegramLoginWidget() {
  const container = document.getElementById(tgLoginContainerId);
  if (!container) return;
  // Remove existing widget script if any
  container.innerHTML = "";
  // Create widget script tag
  const script = document.createElement("script");
  script.src = "https://telegram.org/js/telegram-widget.js?15";
  script.setAttribute("data-telegram-login", BOT_USERNAME);
  script.setAttribute("data-size", "medium");
  script.setAttribute("data-userpic", "false");
  script.setAttribute("data-request-access", "write");
  script.setAttribute("data-onauth", "onTelegramAuth");
  script.async = true;
  container.appendChild(script);
  console.log("🔸 Telegram Login Widget rendered (replace BOT_USERNAME in script.js if needed)");
}

// Callback invoked by Telegram Login Widget
window.onTelegramAuth = function(user) {
  console.log("🔐 onTelegramAuth:", user);
  // user contains id, first_name, last_name (opt), username (opt), photo_url (opt), auth_date, hash
  telegramAuth = user;
  showSuccess("Вход через Telegram выполнен — готово к отправке чек-листа.");
};

// Try to render widget on load (if user added <div id="tg-login"></div>)
document.addEventListener("DOMContentLoaded", () => {
  renderTelegramLoginWidget();
});

// Scenario buttons
document.querySelectorAll("#scenario-buttons button").forEach(btn => {
  btn.addEventListener("click", () => {
    selectedScenario = btn.dataset.scenario;
    console.log("Выбран сценарий:", selectedScenario);
    insightText.innerHTML = insights[selectedScenario].text;
    document.getElementById("next-contact").textContent = insights[selectedScenario].button;
    screen1.classList.add("hidden");
    screen2.classList.remove("hidden");
  });
});

// Next -> show form
document.getElementById("next-contact").addEventListener("click", () => {
  console.log("Переход к форме контакта");
  screen2.classList.add("hidden");
  screen3.classList.remove("hidden");
});

// Submit handler
contactForm.addEventListener("submit", async (e) => {
  e.preventDefault();

  const nameField = contactForm.querySelector("input[name='name']");
  const emailField = contactForm.querySelector("input[name='email']");
  const telegramField = contactForm.querySelector("input[name='telegram']");

  clearError(nameField);
  clearError(emailField);

  const name = nameField.value.trim();
  const email = emailField.value.trim();
  const telegramText = telegramField ? telegramField.value.trim() : "";

  if (!name) return showError("Введите имя.", nameField);
  if (!validateName(name)) return showError("Имя должно быть минимум 2 буквы и без цифр.", nameField);
  if (!email) return showError("Введите email.", emailField);
  if (!validateEmail(email)) return showError("Введите корректный email.", emailField);

  // 1) If Telegram WebApp inside Telegram, we can get user.id:
  const webappUserId = window.Telegram?.WebApp?.initDataUnsafe?.user?.id || null;
  console.log("webappUserId:", webappUserId);

  // 2) telegramAuth from Login Widget (if used)
  console.log("telegramAuth (widget):", telegramAuth);

  const payload = {
    name,
    email,
    telegram: telegramText,
    scenario: selectedScenario,
    // include both possibilities; server will pick verified one in order
    telegram_user_id: webappUserId || null,
    telegram_auth: telegramAuth || null
  };

  console.log("Отправляем payload:", payload);

  try {
    const resp = await fetch("/submit", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    const result = await resp.json();
    console.log("Ответ сервера:", result);

    if (resp.ok && result.status === "ok") {
      showSuccess("Спасибо! Чек-лист отправлен в Telegram (если мы получили ваш Telegram).");
      contactForm.reset();
      setTimeout(() => {
        screen3.classList.add("hidden");
        screen4.classList.remove("hidden");
      }, 1000);
    } else {
      showError(result.message || "Ошибка отправки. Попробуйте позже.");
    }
  } catch (err) {
    console.error("Ошибка fetch:", err);
    showError("Ошибка сети. Попробуйте позже.");
  }
});
