const screen1 = document.getElementById("screen1");
const screen2 = document.getElementById("screen2");
const screen3 = document.getElementById("screen3");
const screen4 = document.getElementById("screen4");
const insightText = document.getElementById("insight-text");
const contactForm = document.getElementById("contact-form");
const formMessage = document.getElementById("form-message");

let selectedScenario = null;

// Инициализация Telegram WebApp
if (window.Telegram && window.Telegram.WebApp) {
  const tg = window.Telegram.WebApp;
  tg.ready();
  tg.expand(); // Полноэкранный режим
  console.log("Telegram WebApp initialized. initData:", tg.initData); // Отладка
} else {
  console.log("Telegram WebApp not detected. Testing outside Telegram?");
}

// Тексты инсайтов и чек-листов
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
  2: {
    text: `
      <ul>
        <li>70% проектов проваливаются ещё на ТЗ — подрядчик пишет его «под себя».</li>
        <li>Ошибки на старте = перерасход в миллионы через 6–12 месяцев.</li>
        <li>Каждый месяц задержки внедрения = минус 5–10% бизнес-эффекта.</li>
      </ul>`,
    button: 'Получить чек-лист «5 ошибок при запуске»'
  },
  3: {
    text: `
      <ul>
        <li>7 из 10 компаний выбирают софт «по рекламе» — и получают новые зависимости.</li>
        <li>Импортозамещение без ROI превращается в «галочку ради отчёта».</li>
        <li>Интегратор всегда продаёт «своё», а не то, что реально нужно бизнесу.</li>
      </ul>`,
    button: 'Получить чек-лист «7 ошибок импортозамещения»'
  },
  4: {
    text: `
      <ul>
        <li>Подрядчик считает часы, а не результат.</li>
        <li>В проекте всё держится на одном «ключевом человеке».</li>
        <li>Вы платите предоплату, но не видите реального прогресса.</li>
      </ul>`,
    button: 'Получить чек-лист «5 сигналов, что подрядчик вас подведёт»'
  },
  5: {
    text: `
      <ul>
        <li>Конкуренты уже автоматизировали ключевые процессы, а у вас всё вручную.</li>
        <li>Управленческая отчётность у вас формируется неделями, у конкурентов — «на лету».</li>
        <li>Конкуренты запускают цифровые сервисы, а вы работаете «как 5 лет назад».</li>
      </ul>`,
    button: 'Получить чек-лист «5 признаков, что конкуренты обгоняют вас»'
  },
  6: {
    text: `
      <ul>
        <li>ROI никто не считает, есть только «обещания эффективности».</li>
        <li>Бюджет уже вырос на +30%, но оснований нет.</li>
        <li>Подрядчик получает деньги за «часы», а не за результат.</li>
      </ul>`,
    button: 'Получить чек-лист «7 признаков, что проект сжигает деньги»'
  }
};

// Валидация email и имени
function validateEmail(email) {
  return /^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$/.test(email);
}

function validateName(name) {
  return /^[А-Яа-яA-Za-zЁё\s-]+$/.test(name);
}

function validateNameLength(name) {
  return name.length >= 2;
}

// Сообщения
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

// Выбор сценария
document.querySelectorAll("#scenario-buttons button").forEach(btn => {
  btn.addEventListener("click", () => {
    selectedScenario = btn.dataset.scenario;
    insightText.innerHTML = insights[selectedScenario].text;
    document.getElementById("next-contact").textContent = insights[selectedScenario].button;
    screen1.classList.add("hidden");
    screen2.classList.remove("hidden");
  });
});

// Переход к форме контакта
document.getElementById("next-contact").addEventListener("click", () => {
  screen2.classList.add("hidden");
  screen3.classList.remove("hidden");
});

// Отправка формы с валидацией
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
  if (window.Telegram && window.Telegram.WebApp) {
    data.init_data = window.Telegram.WebApp.initData;
    console.log("Отправляем init_data:", data.init_data); // Отладка
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

      // Через 2 секунды показываем экран успеха
      setTimeout(() => {
        screen3.classList.add("hidden");
        screen4.classList.remove("hidden");
      }, 2000);
    } else {
      showError(result.message || "Ошибка отправки. Попробуйте позже.");
    }
  } catch (err) {
    console.error(err);
    showError("Ошибка сети. Попробуйте позже.");
  }
});

