
document.addEventListener("DOMContentLoaded", () => {

    "use strict";

    // =====================================
    // ELEMENTS
    // =====================================

    const inputText = document.getElementById("inputText");
    const translatedText = document.getElementById("translatedText");

    const sourceLanguage = document.getElementById("sourceLanguage");
    const targetLanguage = document.getElementById("targetLanguage");

    const translateButton = document.getElementById("translateButton");
    const swapButton = document.getElementById("swapLanguages");

    const clearButton = document.getElementById("clearText");
    const copyButton = document.getElementById("copyTranslation");
    const saveButton = document.getElementById("saveTranslation");

    const characterCount = document.getElementById("characterCount");
    const translationStatus = document.getElementById("translationStatus");
    const errorMessage = document.getElementById("errorMessage");

    const historyList = document.getElementById("historyList");
    const historySearch = document.getElementById("historySearch");
    const clearHistoryButton = document.getElementById("clearHistory");

    const savedList = document.getElementById("savedList");

    const requiredElements = [
        inputText, translatedText,
        sourceLanguage, targetLanguage,
        translateButton, swapButton,
        clearButton, copyButton, saveButton,
        characterCount, translationStatus,
        errorMessage, historyList, historySearch,
        clearHistoryButton, savedList
    ];

    if (requiredElements.some(element => !element)) {
        console.error("Lingua Studio: HTML elements are missing.");
        return;
    }

    // =====================================
    // CONFIGURATION
    // =====================================

    const HISTORY_KEY = "lingua_translation_history";
    const SAVED_KEY = "lingua_saved_translations";
    const MAX_HISTORY = 50;
    const MAX_CHARACTERS = 500;

    const rtlLanguages = ["ur", "ar", "he", "fa", "ps"];

    let currentHistory = [];
    let savedTranslations = [];
    let isTranslating = false;

    // =====================================
    // STORAGE
    // =====================================

    function readStorage(key) {
        try {
            const data = JSON.parse(localStorage.getItem(key) || "[]");
            return Array.isArray(data) ? data : [];
        } catch (error) {
            console.error("Storage error:", error);
            return [];
        }
    }

    function writeStorage(key, data) {
        try {
            localStorage.setItem(key, JSON.stringify(data));
            return true;
        } catch (error) {
            console.error("Unable to save:", error);
            showError("Unable to save data in browser storage.");
            return false;
        }
    }

    // =====================================
    // MESSAGES
    // =====================================

    function showError(message) {
        errorMessage.textContent = message;
        errorMessage.style.display = "block";
    }

    function clearError() {
        errorMessage.textContent = "";
        errorMessage.style.display = "none";
    }

    // =====================================
    // LANGUAGE HELPERS
    // =====================================

    function getLanguageName(code) {
        const selects = [sourceLanguage, targetLanguage];

        for (const select of selects) {
            const option = Array.from(select.options).find(
                item => item.value === code
            );

            if (option) return option.textContent.trim();
        }

        return code;
    }

    function updateTextDirection() {
        inputText.dir = rtlLanguages.includes(sourceLanguage.value)
            ? "rtl" : "ltr";

        translatedText.dir = rtlLanguages.includes(targetLanguage.value)
            ? "rtl" : "ltr";
    }

    function updateCharacterCount() {
        characterCount.textContent =
            `${inputText.value.length} / ${MAX_CHARACTERS}`;
    }

    // =====================================
    // EMPTY STATES
    // =====================================

    function createEmptyState(container, icon, message, description) {
        const empty = document.createElement("div");
        empty.className = container === savedList
            ? "saved-empty"
            : "history-empty";

        const symbol = document.createElement("span");
        symbol.textContent = icon;

        const title = document.createElement("p");
        title.textContent = message;

        const detail = document.createElement("small");
        detail.textContent = description;

        empty.append(symbol, title, detail);
        container.appendChild(empty);
    }

    // =====================================
    // SAFE TEXT PANEL
    // =====================================

    function createTextPanel(label, value, className) {
        const panel = document.createElement("div");
        panel.className = className;

        const heading = document.createElement("span");
        heading.className = "history-label";
        heading.textContent = label;

        const text = document.createElement("div");
        text.textContent = value;

        panel.append(heading, text);
        return panel;
    }

    // =====================================
    // COPY FUNCTION
    // =====================================

    async function copyText(text, button) {
        if (!text) {
            showError("There is no text to copy.");
            return;
        }

        try {
            if (navigator.clipboard && window.isSecureContext) {
                await navigator.clipboard.writeText(text);
            } else {
                const temporary = document.createElement("textarea");
                temporary.value = text;
                temporary.style.position = "fixed";
                temporary.style.opacity = "0";
                document.body.appendChild(temporary);
                temporary.select();

                const success = document.execCommand("copy");
                temporary.remove();

                if (!success) throw new Error("Copy failed");
            }

            clearError();

            if (button) {
                const previous = button.textContent;
                button.textContent = "Copied!";

                setTimeout(() => {
                    button.textContent = previous;
                }, 1500);
            }

        } catch (error) {
            showError("Unable to copy. Please copy manually.");
        }
    }

    // =====================================
    // HISTORY
    // =====================================

    function loadHistory() {
        currentHistory = readStorage(HISTORY_KEY);
        renderHistory();
    }

    function saveHistory() {
        return writeStorage(HISTORY_KEY, currentHistory);
    }

    function addToHistory(original, translation, source, target) {
        const item = {
            id: createID(),
            original,
            translation,
            source,
            target,
            sourceName: getLanguageName(source),
            targetName: getLanguageName(target),
            date: new Date().toISOString()
        };

        currentHistory.unshift(item);
        currentHistory = currentHistory.slice(0, MAX_HISTORY);

        if (saveHistory()) renderHistory();
    }

    function createID() {
        return window.crypto &&
            typeof window.crypto.randomUUID === "function"
            ? window.crypto.randomUUID()
            : Date.now().toString(36) +
              Math.random().toString(36).slice(2);
    }

    function renderHistory() {
        historyList.innerHTML = "";

        const term = historySearch.value.trim().toLowerCase();

        const filtered = currentHistory.filter(item => {
            const searchable = [
                item.original,
                item.translation,
                item.sourceName,
                item.targetName
            ].join(" ").toLowerCase();

            return searchable.includes(term);
        });

        if (filtered.length === 0) {
            createEmptyState(
                historyList,
                "◷",
                term ? "No matching translations found." : "No translation history yet.",
                term ? "Try another search." : "Your translations will appear here."
            );
            return;
        }

        filtered.forEach(item => {
            const card = document.createElement("article");
            card.className = "history-item";

            const top = document.createElement("div");
            top.className = "history-item-top";

            const languages = document.createElement("span");
            languages.className = "history-language";
            languages.textContent =
                `${item.sourceName} → ${item.targetName}`;

            const date = document.createElement("span");
            date.className = "history-time";
            date.textContent = new Date(item.date).toLocaleString();

            top.append(languages, date);

            const content = document.createElement("div");
            content.className = "history-content";

            content.append(
                createTextPanel("ORIGINAL TEXT", item.original, "history-original"),
                createTextPanel("TRANSLATION", item.translation, "history-translated")
            );

            const actions = document.createElement("div");
            actions.className = "history-actions";

            const copy = document.createElement("button");
            copy.type = "button";
            copy.className = "history-copy";
            copy.textContent = "Copy translation";

            copy.addEventListener("click", () => {
                copyText(item.translation, copy);
            });

            actions.appendChild(copy);
            card.append(top, content, actions);
            historyList.appendChild(card);
        });
    }

    // =====================================
    // FAVORITES
    // =====================================

    function loadSaved() {
        savedTranslations = readStorage(SAVED_KEY);
        renderSaved();
    }

    function saveFavorites() {
        return writeStorage(SAVED_KEY, savedTranslations);
    }

    function renderSaved() {
        savedList.innerHTML = "";

        if (savedTranslations.length === 0) {
            createEmptyState(
                savedList,
                "☆",
                "No saved translations yet.",
                "Save your favorite translations to find them here."
            );
            return;
        }

        savedTranslations.forEach(item => {
            const card = document.createElement("article");
            card.className = "saved-item";

            const heading = document.createElement("h4");
            heading.textContent =
                `${item.sourceName} → ${item.targetName}`;

            const original = createTextPanel(
                "ORIGINAL TEXT",
                item.original,
                "saved-original"
            );

            const translation = createTextPanel(
                "TRANSLATION",
                item.translation,
                "saved-translated"
            );

            const date = document.createElement("small");
            date.textContent = new Date(item.date).toLocaleString();

            const copy = document.createElement("button");
            copy.type = "button";
            copy.textContent = "Copy";

            copy.addEventListener("click", () => {
                copyText(item.translation, copy);
            });

            const remove = document.createElement("button");
            remove.type = "button";
            remove.textContent = "★ Remove";

            remove.addEventListener("click", () => {
                savedTranslations = savedTranslations.filter(
                    saved => saved.id !== item.id
                );

                if (saveFavorites()) {
                    renderSaved();
                    translationStatus.textContent = "Favorite removed.";
                }
            });

            card.append(
                heading, original, translation, date, copy, remove
            );

            savedList.appendChild(card);
        });
    }

    // =====================================
    // SAVE CURRENT FAVORITE
    // =====================================

    saveButton.addEventListener("click", () => {
        if (translatedText.dataset.translated !== "true") {
            showError("Translate some text before saving it.");
            return;
        }

        const original = inputText.value.trim();
        const translation = translatedText.textContent.trim();
        const source = sourceLanguage.value;
        const target = targetLanguage.value;

        const duplicate = savedTranslations.some(item =>
            item.original === original &&
            item.translation === translation &&
            item.source === source &&
            item.target === target
        );

        if (duplicate) {
            translationStatus.textContent =
                "This translation is already saved.";
            return;
        }

        savedTranslations.unshift({
            id: createID(),
            original,
            translation,
            source,
            target,
            sourceName: getLanguageName(source),
            targetName: getLanguageName(target),
            date: new Date().toISOString()
        });

        if (saveFavorites()) {
            renderSaved();
            translationStatus.textContent =
                "★ Favorite saved successfully!";
            clearError();
        }
    });

    // =====================================
    // CHARACTER COUNTER
    // =====================================

    inputText.addEventListener("input", () => {
        updateCharacterCount();
        clearError();
    });

    // =====================================
    // LANGUAGE SWAP
    // =====================================

    
function findMatchingLanguage(select, languageCode) {

    const options = Array.from(select.options);

    // Exact language code match
    let match = options.find(
        option => option.value === languageCode
    );

    if (match) return match.value;

    // Match regional variants using the base language code
    const baseCode = languageCode.split("-")[0];

    const matches = options.filter(
        option => option.value.split("-")[0] === baseCode
    );

    if (matches.length === 0) return null;

    // Prefer American English when available
    if (baseCode === "EN") {
        const americanEnglish = matches.find(
            option => option.value === "EN-US"
        );

        if (americanEnglish) return americanEnglish.value;
    }

    return matches[0].value;
}


swapButton.addEventListener("click", () => {

    const previousSource = sourceLanguage.value;
    const previousTarget = targetLanguage.value;

    // Clear both language searches and restore full lists
    const sourceSearch = document.getElementById(
        "sourceLanguageSearch"
    );

    const targetSearch = document.getElementById(
        "targetLanguageSearch"
    );

    if (sourceSearch) {
        sourceSearch.value = "";
        sourceSearch.dispatchEvent(new Event("input"));
    }

    if (targetSearch) {
        targetSearch.value = "";
        targetSearch.dispatchEvent(new Event("input"));
    }

    // Find equivalent codes in opposite dropdowns
    const newSource = findMatchingLanguage(
        sourceLanguage,
        previousTarget
    );

    const newTarget = findMatchingLanguage(
        targetLanguage,
        previousSource
    );

    if (!newSource || !newTarget) {
        showError(
            "These languages cannot be swapped. Please select another language pair."
        );
        return;
    }

    // Update dropdowns
    sourceLanguage.value = newSource;
    targetLanguage.value = newTarget;

    // Move translated text back into the input
    if (translatedText.dataset.translated === "true") {

        inputText.value = translatedText.textContent.trim();

        translatedText.innerHTML =
            '<span class="placeholder-text">Your translation will appear here...</span>';

        translatedText.dataset.translated = "false";
    }

    updateCharacterCount();
    updateTextDirection();
    clearError();

    translationStatus.textContent = "Languages swapped";
});


    // =====================================
    // CLEAR INPUT
    // =====================================

    clearButton.addEventListener("click", () => {
        inputText.value = "";

        translatedText.textContent =
            "Your translation will appear here...";

        translatedText.dataset.translated = "false";

        updateCharacterCount();
        updateTextDirection();

        translationStatus.textContent = "Waiting for text";
        clearError();

        inputText.focus();
    });

    sourceLanguage.addEventListener("change", updateTextDirection);
    targetLanguage.addEventListener("change", updateTextDirection);

    // =====================================
    // TRANSLATE
    // =====================================

    translateButton.addEventListener("click", async () => {
        if (isTranslating) return;

        const text = inputText.value.trim();
        const source = sourceLanguage.value;
        const target = targetLanguage.value;

        clearError();

        if (!text) {
            showError("Please enter some text to translate.");
            inputText.focus();
            return;
        }

        if (text.length > MAX_CHARACTERS) {
            showError(`Maximum ${MAX_CHARACTERS} characters allowed.`);
            return;
        }

        if (!source || !target) {
            showError("Please select both languages.");
            return;
        }

        if (source === target) {
            showError("Please select two different languages.");
            return;
        }

        isTranslating = true;
        translateButton.disabled = true;
        translateButton.textContent = "Translating...";
        translationStatus.textContent = "Processing...";

        translatedText.textContent = "Please wait...";
        translatedText.dataset.translated = "false";

        try {
            const response = await fetch("/api/translate", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    text: text,
                    source_language: source,
                    target_language: target
                })
            });

            const data = await response.json();

            if (!response.ok || data.status !== "success") {
                throw new Error(
                    data.error || "Translation failed."
                );
            }

            if (!data.translated_text ||
                typeof data.translated_text !== "string") {
                throw new Error("The translation service returned no text.");
            }

            translatedText.textContent = data.translated_text;
            translatedText.dataset.translated = "true";

            translationStatus.textContent = "Translation successful";

            updateTextDirection();

            addToHistory(
                text,
                data.translated_text,
                source,
                target
            );

        } catch (error) {
            translatedText.textContent =
                "Your translation will appear here...";

            translatedText.dataset.translated = "false";

            showError(error.message || "Unable to translate text.");

            translationStatus.textContent = "Translation failed";

        } finally {
            isTranslating = false;
            translateButton.disabled = false;
            translateButton.innerHTML =
                '<span>✦</span> Translate now <span class="button-arrow">→</span>';
        }
    });

    // =====================================
    // COPY CURRENT TRANSLATION
    // =====================================

    copyButton.addEventListener("click", () => {
        if (translatedText.dataset.translated !== "true") {
            showError("There is no translation to copy.");
            return;
        }

        copyText(translatedText.textContent.trim(), copyButton);
    });

    // =====================================
    // SEARCH HISTORY
    // =====================================

    historySearch.addEventListener("input", renderHistory);

    // =====================================
    // CLEAR HISTORY
    // =====================================

    clearHistoryButton.addEventListener("click", () => {
        if (currentHistory.length === 0) return;

        if (!confirm("Are you sure you want to delete all translation history?")) {
            return;
        }

        currentHistory = [];

        if (saveHistory()) {
            renderHistory();
            translationStatus.textContent = "History cleared successfully.";
        }
    });

    // =====================================
    // INITIALIZATION
    // =====================================

    translatedText.dataset.translated = "false";

    updateCharacterCount();
    updateTextDirection();

    loadHistory();
    loadSaved();

    console.log("Lingua Studio JavaScript loaded successfully.");

});
