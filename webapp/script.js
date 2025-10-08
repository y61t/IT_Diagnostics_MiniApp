const screen1 = document.getElementById("screen1");
const screen2 = document.getElementById("screen2");
const screen3 = document.getElementById("screen3");
const screen4 = document.getElementById("screen4");
const insightText = document.getElementById("insight-text");
const contactForm = document.getElementById("contact-form");
const formMessage = document.getElementById("form-message");

let selectedScenario = null;

// Тексты инсайтов
const insights = {
  1: { text: "<ul><li>80% кризисных проектов...</li></ul>", button: 'Получить чек-лист «10 признаков»' },
  2: { text: "<ul><li>70% проектов проваливаются...</li></ul>", button: 'Получить чек-лист «5 ошибок»' },
  3: { text: "<ul><li>7 из 10 компаний выбирают софт...</li></ul>", button: 'Получить чек-лист «7 ошибок импортозамещения»' },
  4: { text: "<ul><li>Подрядчик считает часы...</li></ul>", button: 'Получить чек-лист «5 сигналов»' },
  5: { text: "<ul><li>Конкуренты уже автоматизировали...</li></ul>", button: 'Получить чек-лист «5 признаков»' },
  6: { text: "<ul><li>ROI никто не считает...</li></ul>", button: 'Получить чек-лист «7 признаков»' }
};

// Валидация
function validateEmail(email) {
  return /^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$/.test(email);
}
function validateName(name) {
  return /^[А-Яа-яA-Za-zЁё\s-]+$/.test(name) && name.length >= 2;
}

// Сообщения
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

// Выбор сценария
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

// Переход к форме контакта
document.getElementById("next-contact").addEventListener("click", () => {
  console.log("Переход к форме контакта");
  screen2.classList.add("hidden");
  screen3.classList.remove("hidden");
});

// Отправка формы
contactForm.addEventListener("submit", async (e) => {
  e.preventDefault();

  const nameField = contactForm.querySelector("input[name='name']");
  const emailField = contactForm.querySelector("input[name='email']");

  clearError(nameField);
  clearError(emailField);

  const name = nameField.value.trim();
  const email = emailField.value.trim();

  if (!name) return showError("Введите имя.", nameField);
  if (!validateName(name)) return showError("Имя должно быть минимум 2 буквы и без цифр.", nameField);
  if (!email) return showError("Введите email.", emailField);
  if (!validateEmail(email)) return showError("Введите корректный email.", emailField);

  // Telegram WebApp user id
  const telegram_user_id = window.Telegram?.WebApp?.initDataUnsafe?.user?.id;
  console.log("Telegram WebApp объект:", window.Telegram);
  console.log("Telegram user_id:", telegram_user_id);
  if (!telegram_user_id) return showError("Не удалось определить Telegram user_id. Откройте WebApp в Telegram.");

  const data = { name, email, telegram_user_id, scenario: selectedScenario };
  console.log("Отправляем данные на сервер:", data);

  try {
    const response = await fetch("/submit", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data)
    });
    const result = await response.json();
    console.log("Ответ сервера:", result);

    if (response.ok && result.status === "ok") {
      showSuccess("Спасибо! Чек-лист отправлен в Telegram.");
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
