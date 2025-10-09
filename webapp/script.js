// === Элементы интерфейса ===
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

// === Логгер ===
function log(msg) {
  console.log(msg);
  logBox.innerHTML += `<div>${msg}</div>`;
  logBox.scrollTop = logBox.scrollHeight;
}

// === Telegram WebApp инициализация ===
document.addEventListener("DOMContentLoaded", () => {
  log("🟡 DOM загружен, проверка Telegram WebApp...");

  // Проверка, доступен ли объект Telegram.WebApp
  if (window.Telegram?.WebApp) {
    const tg = window.Telegram.WebApp;
    tg.ready();
    log("✅ Telegram WebApp найден, инициализация завершена");
    log("📦 initData:", tg.initData || "(пусто)");
    log("📦 initDataUnsafe:", JSON.stringify(tg.initDataUnsafe, null, 2));

    // Получаем Telegram user.id
    telegramUserId = tg.initDataUnsafe?.user?.id || null;
    if (telegramUserId) {
      log(`✅ Telegram user.id: ${telegramUserId}`);
      log("🟢 Соединение с Telegram Mini App установлено");
      document.body.classList.add("connected");
    } else {
      log("⚠️ user.id отсутствует в initDataUnsafe!");
      document.body.classList.add("not-connected");
    }
  } else {
    log("❌ Telegram WebApp не найден!");
    log("🔴 Открой это приложение через Telegram Mini App!");
    document.body.classList.add("not-connected");
  }

  // Проверка кнопки для ручного открытия Mini App
  const btnCheck = document.getElementById("tg-open-check");
  if (btnCheck) {
    btnCheck.addEventListener("click", () => {
      log("🧭 Нажата тестовая кнопка для открытия Mini App");
      window.open("https://t.me/ИМЯ_ТВОЕГО_БОТА", "_blank");
    });
  }
});

// === Данные сценариев ===
const insights = {
  1: { text: "80% кризисных проектов срываются из-за потери прозрачности процессов.", button: "Получить чек-лист «10 признаков»" },
  2: { text: "70% проектов проваливаются из-за отсутствия контроля над изменениями.", button: "Получить чек-лист «5 ошибок»" },
  3: { text: "7 из 10 компаний выбирают софт неправильно при импортозамещении.", button: "Получить чек-лист «7 ошибок импортозамещения»" },
  4: { text: "Подрядчик считает часы, а не результат — тревожный сигнал.", button: "Получить чек-лист «5 сигналов»" },
  5: { text: "Конкуренты уже автоматизировали отчётность, а вы — ещё нет?", button: "Получить чек-лист «5 признаков отставания»" },
  6: { text: "ROI проекта никто не считает — вы рискуете потратить бюджет впустую.", button: "Получить чек-лист «7 признаков»" },
};

// === Выбор сценария ===
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

// === Переход к форме ===
document.getElementById("next-contact").addEventListener("click", () => {
  screen2.classList.add("hidden");
  screen3.classList.remove("hidden");
  log("🟢 Переход к экрану формы контактов");
});

// === Отправка формы ===
contactForm.addEventListener("submit", async e => {
  e.preventDefault();
  log("📤 Отправка формы началась...");

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
      showMessage("✅ Чек-лист успешно отправлен!", "green");
      setTimeout(() => {
        screen3.classList.add("hidden");
        screen4.classList.remove("hidden");
        log("🎉 Переход к экрану успеха");
      }, 1000);
    } else {
      showMessage(result.message || "Ошибка при отправке данных.", "red");
    }
  } catch (err) {
    log("❌ Ошибка сети: " + err);
    showMessage("Ошибка сети. Попробуйте позже.", "red");
  }
});

// === Вспомогательная функция ===
function showMessage(text, color = "black") {
  formMessage.style.display = "block";
  formMessage.style.color = color;
  formMessage.innerText = text;
  log(`💬 MSG: ${text}`);
}
