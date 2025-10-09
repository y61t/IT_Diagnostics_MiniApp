const screen1 = document.getElementById("screen1");
const screen2 = document.getElementById("screen2");
const screen3 = document.getElementById("screen3");
const screen4 = document.getElementById("screen4");
const insightText = document.getElementById("insight-text");
const contactForm = document.getElementById("contact-form");
const formMessage = document.getElementById("form-message");

let selectedScenario = null;

const insights = {
  1: { text: "80% кризисных проектов...", button: "Получить чек-лист «10 признаков»" },
  2: { text: "70% проектов проваливаются...", button: "Получить чек-лист «5 ошибок»" },
  3: { text: "7 из 10 компаний выбирают софт...", button: "Получить чек-лист «7 ошибок импортозамещения»" },
  4: { text: "Подрядчик считает часы...", button: "Получить чек-лист «5 сигналов»" },
  5: { text: "Конкуренты уже автоматизировали...", button: "Получить чек-лист «5 признаков»" },
  6: { text: "ROI никто не считает...", button: "Получить чек-лист «7 признаков»" },
};

function showMessage(text, color = "black") {
  formMessage.style.display = "block";
  formMessage.style.color = color;
  formMessage.innerText = text;
}

// === Сценарии ===
document.querySelectorAll("#scenario-buttons button").forEach(btn => {
  btn.addEventListener("click", () => {
    selectedScenario = btn.dataset.scenario;
    insightText.innerText = insights[selectedScenario].text;
    document.getElementById("next-contact").innerText = insights[selectedScenario].button;
    screen1.classList.add("hidden");
    screen2.classList.remove("hidden");
  });
});

document.getElementById("next-contact").addEventListener("click", () => {
  screen2.classList.add("hidden");
  screen3.classList.remove("hidden");
});

// === Отправка формы ===
contactForm.addEventListener("submit", async e => {
  e.preventDefault();

  const name = contactForm.querySelector("input[name='name']").value.trim();
  const email = contactForm.querySelector("input[name='email']").value.trim();

  if (!name || !email) return showMessage("Заполните все поля.", "red");

  // Получаем user.id из Telegram WebApp
  const webappUserId = window.Telegram?.WebApp?.initDataUnsafe?.user?.id || null;
  console.log("webappUserId:", webappUserId);

  const payload = {
    name,
    email,
    scenario: selectedScenario,
    telegram_user_id: webappUserId,
  };

  console.log("📤 Отправляем:", payload);

  try {
    const resp = await fetch("/submit", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const result = await resp.json();
    console.log("📥 Ответ сервера:", result);

    if (resp.ok && result.status === "ok") {
      showMessage("✅ Чек-лист отправлен в Telegram!", "green");
      setTimeout(() => {
        screen3.classList.add("hidden");
        screen4.classList.remove("hidden");
      }, 1200);
    } else {
      showMessage(result.message || "Ошибка при отправке.", "red");
    }
  } catch (err) {
    console.error("Ошибка:", err);
    showMessage("Ошибка сети. Попробуйте позже.", "red");
  }
});
