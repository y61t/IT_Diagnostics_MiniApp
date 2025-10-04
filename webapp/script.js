const scenarioButtons = document.querySelectorAll("#scenario-buttons button");
const screen1 = document.getElementById("screen1");
const screen2 = document.getElementById("screen2");
const insightText = document.getElementById("insight-text");

let selectedScenario = null;

const insights = {
  1: "80% кризисных проектов срывают сроки и бюджеты из-за подрядчиков. Средний перерасход = +30–50% к смете.",
  2: "70% проектов проваливаются ещё на ТЗ — подрядчик пишет его «под себя». Ошибки на старте = перерасход в миллионы.",
  3: "7 из 10 компаний выбирают софт «по рекламе» — и получают новые зависимости. Импортозамещение без ROI превращается в «галочку».",
  4: "Подрядчик считает часы, а не результат. Всё держится на одном ключевом человеке. Вы платите предоплату, но не видите прогресса.",
  5: "Конкуренты автоматизировали процессы, а у вас всё вручную. Отчётность формируется неделями, у конкурентов — на лету.",
  6: "ROI никто не считает, есть только «обещания эффективности». Бюджет вырос +30%, подрядчик получает деньги за часы, а не результат."
};

const screen3 = document.getElementById("screen3");
const contactForm = document.getElementById("contact-form");
const formMessage = document.getElementById("form-message");

// Переход к экрану формы контакта
document.getElementById("next-contact").addEventListener("click", () => {
  screen2.style.display = "none";
  screen3.style.display = "block";
});

// Отправка формы на сервер
contactForm.addEventListener("submit", async (e) => {
  e.preventDefault();

  const formData = new FormData(contactForm);
  const data = {
    name: formData.get("name"),
    email: formData.get("email"),
    telegram: formData.get("telegram"),
    scenario: selectedScenario
  };

  try {
    const response = await fetch("/submit", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data)
    });

    if(response.ok){
      formMessage.textContent = "Спасибо! Чек-лист уже летит к вам.";
      contactForm.reset();
    } else {
      formMessage.textContent = "Ошибка отправки. Попробуйте позже.";
    }
  } catch (err) {
    formMessage.textContent = "Ошибка сети. Попробуйте позже.";
    console.error(err);
  }
});

contactForm.addEventListener("submit", async (e) => {
  e.preventDefault();

  const formData = new FormData(contactForm);
  const data = {
    name: formData.get("name"),
    email: formData.get("email"),
    telegram: formData.get("telegram"),
    scenario: selectedScenario
  };

  try {
    // Отправляем контакт на сервер (для логирования / Bitrix24)
    const response = await fetch("/submit", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data)
    });

    if(response.ok){
      // Скачиваем PDF
      const link = document.createElement("a");
      link.href = "/download";
      link.download = "checklist.pdf";
      document.body.appendChild(link);
      link.click();
      link.remove();

      formMessage.textContent = "Спасибо! Чек-лист уже летит к вам.";
      contactForm.reset();
    } else {
      formMessage.textContent = "Ошибка отправки. Попробуйте позже.";
    }
  } catch (err) {
    formMessage.textContent = "Ошибка сети. Попробуйте позже.";
    console.error(err);
  }
});


scenarioButtons.forEach(btn => {
  btn.addEventListener("click", () => {
    selectedScenario = btn.dataset.scenario;
    insightText.textContent = insights[selectedScenario];
    screen1.style.display = "none";
    screen2.style.display = "block";
  });
});

document.getElementById("next-contact").addEventListener("click", () => {
  alert("Следующий шаг: форма контакта (будет реализована на следующем этапе)");
});
