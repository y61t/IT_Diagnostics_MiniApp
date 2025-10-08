// === Экраны ===
const screen1 = document.getElementById("screen1");
const screen2 = document.getElementById("screen2");
const screen3 = document.getElementById("screen3");
const screen4 = document.getElementById("screen4");

// === Элементы формы ===
const insightText = document.getElementById("insight-text");
const contactForm = document.getElementById("contact-form");
const formMessage = document.getElementById("form-message");

window.Telegram.WebApp.ready();

let telegramUserId = null;
if (window.Telegram.WebApp.initDataUnsafe && window.Telegram.WebApp.initDataUnsafe.user) {
    telegramUserId = window.Telegram.WebApp.initDataUnsafe.user.id;
    console.log("Telegram user_id через WebApp API:", telegramUserId);
}

if (!telegramUserId) {
    console.warn("Telegram user_id не определён! Фото не придёт.");
}

// === Сценарии и тексты инсайтов ===
let selectedScenario = null;
const insights = {
    1: { text: `<ul><li>80% кризисных проектов...</li></ul>`, button: 'Получить чек-лист «10 признаков...»' },
    2: { text: `<ul><li>70% проектов...</li></ul>`, button: 'Получить чек-лист «5 ошибок...»' },
    3: { text: `<ul><li>7 из 10 компаний...</li></ul>`, button: 'Получить чек-лист «7 ошибок...»' },
    4: { text: `<ul><li>Подрядчик считает часы...</li></ul>`, button: 'Получить чек-лист «5 сигналов...»' },
    5: { text: `<ul><li>Конкуренты уже автоматизировали...</li></ul>`, button: 'Получить чек-лист «5 признаков...»' },
    6: { text: `<ul><li>ROI никто не считает...</li></ul>`, button: 'Получить чек-лист «7 признаков...»' }
};

// === Валидация ===
function validateEmail(email) { return /^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$/.test(email); }
function validateName(name) { return /^[А-Яа-яA-Za-zЁё\s-]+$/.test(name); }
function validateNameLength(name) { return name.length >= 2; }

// === Сообщения ===
function showError(message, field = null) {
    formMessage.innerText = message; formMessage.style.color = "red"; formMessage.style.display = "block";
    if (field) field.classList.add("error");
}
function clearError(field = null) {
    formMessage.innerText = ""; formMessage.style.display = "none";
    if (field) field.classList.remove("error");
}
function showSuccess(message) {
    formMessage.innerText = message; formMessage.style.color = "green"; formMessage.style.display = "block";
}

// === Выбор сценария ===
document.querySelectorAll("#scenario-buttons button").forEach(btn => {
    btn.addEventListener("click", () => {
        selectedScenario = btn.dataset.scenario;
        insightText.innerHTML = insights[selectedScenario].text;
        document.getElementById("next-contact").textContent = insights[selectedScenario].button;
        screen1.classList.add("hidden");
        screen2.classList.remove("hidden");
    });
});

// === Переход к форме контакта ===
document.getElementById("next-contact").addEventListener("click", () => {
    if (!selectedScenario) return showError("Выберите сценарий");
    screen2.classList.add("hidden");
    screen3.classList.remove("hidden");
});

// === Отправка формы ===
contactForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    const name = contactForm.name.value.trim();
    const email = contactForm.email.value.trim();
    const telegram = contactForm.telegram.value.trim();

    clearError(contactForm.name);
    clearError(contactForm.email);

    if (!name) return showError("Введите имя.", contactForm.name);
    if (!validateName(name)) return showError("Имя должно содержать только буквы, пробелы или дефисы.", contactForm.name);
    if (!validateNameLength(name)) return showError("Имя должно быть минимум 2 символа.", contactForm.name);
    if (!email) return showError("Введите email.", contactForm.email);
    if (!validateEmail(email)) return showError("Введите корректный email.", contactForm.email);

    if (!telegramUserId) {
        showError("Не удалось определить Telegram ID. Фото не будет отправлено.");
        return;
    }

    const data = { name, email, telegram, scenario: selectedScenario, user_id: telegramUserId };
    console.log("Отправка данных:", data);

    try {
        const response = await fetch(`${window.location.origin}/submit`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (response.ok && result.status === "ok") {
            showSuccess("Спасибо! Чек-лист уже летит к вам.");
            contactForm.reset();
            setTimeout(() => {
                screen3.classList.add("hidden");
                screen4.classList.remove("hidden");
            }, 1500);
        } else {
            showError(result.message || "Ошибка отправки. Попробуйте позже.");
        }
    } catch (err) {
        console.error(err);
        showError("Ошибка сети. Попробуйте позже.");
    }
});
