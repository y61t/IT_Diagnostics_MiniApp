const screen1 = document.getElementById("screen1");
const screen2 = document.getElementById("screen2");
const screen3 = document.getElementById("screen3");
const screen4 = document.getElementById("screen4");
const insightText = document.getElementById("insight-text");
const contactForm = document.getElementById("contact-form");
const formMessage = document.getElementById("form-message");
const logBox = document.getElementById("log-box");

let selectedScenario = null;
let telegramUserId = null;

function log(msg) {
  console.log(msg);
  logBox.innerHTML += `<div>${msg}</div>`;
  logBox.scrollTop = logBox.scrollHeight;
}

// === Инициализация Telegram WebApp ===
document.addEventListener("DOMContentLoaded", () => {
  log("🟡 DOM загружен, инициализация Telegram WebApp...");

  if (window.Telegram?.WebApp) {
    log("✅ Telegram WebApp найден, вызываем ready()");
    window.Telegram.WebApp.ready();

    const tg = window.Telegram.WebApp;
    log("📦 initData:", tg.initData || "(пусто)");
    log("📦 initDataUnsafe:", JSON.stringify(tg.initDataUnsafe, null, 2));

    telegramUserId = tg.initDataUnsafe?.user?.id || null;
    if (telegramUserId) {
      log(`✅ Получен Telegram user.id: ${telegramUserId}`);
    } else {
      log("⚠️ user.id отсутствует в initDataUnsafe!");
    }
  } else {
    log("❌ Telegram WebApp не найден! Проверь, открыт ли бот через Telegram.");
  }
});

// === Данные сценариев ===
const insights = {
  1: { text: "80% кризисных проектов...", button: "Получить чек-лист «10 признаков»" },
  2: { text: "70% проектов проваливаются...", button: "Получить чек-лист «5 ошибок»" },
  3: { text: "7 из 10 компаний выбирают софт...", button: "Получить чек-лист «7 ошибок импортозамещения»" },
  4: { text: "Подрядчик считает часы...", button: "Получить чек-лист «5 сигналов»" },
  5: { text: "Конкуренты уже автоматизировали...", button: "Получить чек-лист «5 признаков»" },
  6: { text: "ROI никто не считает...", button: "Получить чек-лист «7 признаков»" },
};

// === Сценарии ===
document.querySelectorAll("#scenario-buttons button").forEach(btn => {
  btn.addEventListener("click", () => {
    selectedScenario = btn.dataset.scenario;
    insightText.innerText = insights[selectedScenario].text;
    document.getElementById("next-contact").innerText = insights[selectedScenario].button;
    screen1.classList.add("hidden");
    screen2.classList.remove("hidden");
    log(`🟢 Сценарий выбран: ${selectedScenario}`);
  });
});

document.getElementById("next-contact").addEventListener("click", () => {
  screen2.classList.add("hidden");
  screen3.classList.remove("hidden");
  log("🟢 Переход к экрану формы");
});

// === Отправка формы ===
contactForm.addEventListener("submit", async e => {
  e.preventDefault();
  log("📤 Отправка формы началась");

  const name = contactForm.querySelector("input[name='name']").value.trim();
  const email = contactForm.querySelector("input[name='email']").value.trim();

  if (!name || !email) {
    showMessage("❌ Заполните все поля!", "red");
    return;
  }

  const payload = {
    name,
    email,
    scenario: selectedScenario,
    telegram_user_id: telegramUserId,
  };
  log("📦 Payload к отправке: " + JSON.stringify(payload));

  try {
    const resp = await fetch("/submit", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    const result = await resp.json();
    log("📥 Ответ сервера: " + JSON.stringify(result));

    if (resp.ok && result.status === "ok") {
      showMessage("✅ Чек-лист отправлен!", "green");
      setTimeout(() => {
        screen3.classList.add("hidden");
        screen4.classList.remove("hidden");
      }, 1000);
    } else {
      showMessage(result.message || "Ошибка при отправке.", "red");
    }
  } catch (err) {
    log("❌ Ошибка сети: " + err);
    showMessage("Ошибка сети. Попробуйте позже.", "red");
  }
});

function showMessage(text, color = "black") {
  formMessage.style.display = "block";
  formMessage.style.color = color;
  formMessage.innerText = text;
  log(`💬 MSG: ${text}`);
}
