
document.addEventListener("DOMContentLoaded", () => {

    // =====================================
    // HTML ELEMENTS
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

    // Check required elements
    const requiredElements = [
        inputText, translatedText, sourceLanguage,
        targetLanguage, translateButton, swapButton,
        clearButton, copyButton, saveButton,
        characterCount, translationStatus, errorMessage,
        historyList, historySearch, clearHistoryButton, savedList
    ];

    if (requiredElements.some(element => !element)) {
        console.error("Some HTML elements are missing. Check index.html.");
        return;
    }

    // =====================================
    // STORAGE
    // =====================================

    const HISTORY_KEY = "lingua_translation_history";
    const SAVED_KEY = "lingua_saved_translations";

    const rtlLanguages = ["ur", "ar", "he", "fa"];

    let currentHistory = [];
    let savedTranslations = [];

    // =====================================
    // LANGUAGE NAME
    // =====================================

    function getLanguageName(code) {

        for (const select of [sourceLanguage, targetLanguage]) {

            const option = Array.from(select.options).find(
                item => item.value === code
            );

            if (option) {
                return option.textContent.trim();
            }
        }

        return code;
    }

    // =====================================
    // LOAD HISTORY
    // =====================================

    function loadHistory() {

        try {

            currentHistory =
                JSON.parse(localStorage.getItem(HISTORY_KEY)) || [];

            if (!Array.isArray(currentHistory)) {
                currentHistory = [];
            }

        } catch (error) {

            currentHistory = [];
        }

        renderHistory();
    }

    // =====================================
    // SAVE HISTORY
    // =====================================

    function saveHistory() {

        try {

            localStorage.setItem(
                HISTORY_KEY,
                JSON.stringify(currentHistory)
            );

        } catch (error) {

            errorMessage.textContent = "Unable to save history.";
        }
    }

    // =====================================
    // LOAD FAVORITES
    // =====================================

    function loadSaved() {

        try {

            savedTranslations =
                JSON.parse(localStorage.getItem(SAVED_KEY)) || [];

            if (!Array.isArray(savedTranslations)) {
                savedTranslations = [];
            }

        } catch (error) {

            savedTranslations = [];
        }

        renderSaved();
    }

    // =====================================
    // SAVE FAVORITES
    // =====================================

    function saveFavorites() {

        try {

            localStorage.setItem(
                SAVED_KEY,
                JSON.stringify(savedTranslations)
            );

        } catch (error) {

            errorMessage.textContent =
                "Unable to save favorite translations.";
        }
    }

    // =====================================
    // CREATE TEXT PANEL
    // =====================================

    function createTextPanel(label, value, className = "") {

        const panel = document.createElement("div");

        if (className) {
            panel.className = className;
        }

        const heading = document.createElement("span");
        heading.className = "history-label";
        heading.textContent = label;

        const text = document.createElement("div");
        text.textContent = value;

        panel.append(heading, text);

        return panel;
    }

    // =====================================
    // RENDER HISTORY WITH SEARCH
    // =====================================

    function renderHistory() {

        historyList.innerHTML = "";

        const searchTerm = historySearch.value
            .trim()
            .toLocaleLowerCase();

        // Filter history
        const filteredHistory = currentHistory.filter(item => {

            const searchableText = [
                item.original,
                item.translation,
                item.sourceName,
                item.targetName,
                item.source,
                item.target
            ].join(" ").toLocaleLowerCase();

            return searchableText.includes(searchTerm);
        });

        // Empty state
        if (filteredHistory.length === 0) {

            const empty = document.createElement("div");
            empty.className = "history-empty";

            const icon = document.createElement("span");
            icon.textContent = "◷";

            const message = document.createElement("p");

            message.textContent = searchTerm
                ? "No matching translations found."
                : "No translation history yet.";

            const description = document.createElement("small");

            description.textContent = searchTerm
                ? "Try another search."
                : "Your translations will appear here.";

            empty.append(icon, message, description);

            historyList.appendChild(empty);

            return;
        }

        // Display filtered history
        filteredHistory.forEach(item => {

            const card = document.createElement("div");
            card.className = "history-item";

            const top = document.createElement("div");
            top.className = "history-item-top";

            const languages = document.createElement("span");
            languages.className = "history-language";

            languages.textContent =
                `${item.sourceName} → ${item.targetName}`;

            const time = document.createElement("span");
            time.className = "history-time";

            time.textContent = new Date(item.date).toLocaleString();

            top.append(languages, time);

            const content = document.createElement("div");
            content.className = "history-content";

            const original = createTextPanel(
                "ORIGINAL TEXT",
                item.original,
                "history-original"
            );

            const translated = createTextPanel(
                "TRANSLATION",
                item.translation,
                "history-translated"
            );

            content.append(original, translated);

            const actions = document.createElement("div");
            actions.className = "history-actions";

            const copy = document.createElement("button");
            copy.className = "history-copy";
            copy.type = "button";
            copy.textContent = "Copy translation";

            copy.addEventListener("click", () => {
                copyText(item.translation, copy);
            });

            actions.appendChild(copy);

            card.append(top, content, actions);

            historyList.appendChild(card);
        });
    }

    // Search while typing
    historySearch.addEventListener("input", renderHistory);

    // =====================================
    // ADD TO HISTORY
    // =====================================

    function addToHistory(original, translation, source, target) {

        currentHistory.unshift({

            original,
            translation,
            source,
            target,

            sourceName: getLanguageName(source),
            targetName: getLanguageName(target),

            date: new Date().toISOString()
        });

        // Keep latest 50 translations
        currentHistory = currentHistory.slice(0, 50);

        saveHistory();
        renderHistory();
    }

    // =====================================
    // RENDER SAVED FAVORITES
    // =====================================

    function renderSaved() {

        savedList.innerHTML = "";

        if (savedTranslations.length === 0) {

            const empty = document.createElement("div");
            empty.className = "saved-empty";

            const icon = document.createElement("span");
            icon.textContent = "☆";

            const message = document.createElement("p");
            message.textContent = "No saved translations yet.";

            const description = document.createElement("small");
            description.textContent =
                "Save your favorite translations to find them here.";

            empty.append(icon, message, description);

            savedList.appendChild(empty);

            return;
        }

        savedTranslations.forEach(item => {

            const card = document.createElement("div");
            card.className = "saved-item";

            const header = document.createElement("div");
            header.className = "saved-item-header";

            const languages = document.createElement("span");
            languages.className = "saved-language";

            languages.textContent =
                `${item.sourceName} → ${item.targetName}`;

            const date = document.createElement("span");
            date.className = "saved-date";

            date.textContent = new Date(item.date).toLocaleString();

            header.append(languages, date);

            const content = document.createElement("div");
            content.className = "saved-content";

            const original = createTextPanel(
                "ORIGINAL TEXT",
                item.original,
                "saved-original"
            );

            const translated = createTextPanel(
                "TRANSLATION",
                item.translation,
                "saved-translated"
            );

            // Saved section uses its own label class
            original.querySelector("span").className = "saved-label";
            translated.querySelector("span").className = "saved-label";

            content.append(original, translated);

            const actions = document.createElement("div");
            actions.className = "saved-actions";

            const copy = document.createElement("button");
            copy.className = "saved-copy";
            copy.type = "button";
            copy.textContent = "Copy";

            copy.addEventListener("click", () => {
                copyText(item.translation, copy);
            });

            const remove = document.createElement("button");
            remove.className = "remove-saved";
            remove.type = "button";
            remove.textContent = "★ Remove";

            remove.addEventListener("click", () => {

                savedTranslations = savedTranslations.filter(
                    saved => saved.id !== item.id
                );

                saveFavorites();
                renderSaved();

                translationStatus.textContent =
                    "Favorite removed successfully.";
            });

            actions.append(copy, remove);

            card.append(header, content, actions);

            savedList.appendChild(card);
        });
    }

    // =====================================
    // COPY TEXT
    // =====================================

    async function copyText(text, button) {

        try {

            await navigator.clipboard.writeText(text);

            const previous = button.textContent;

            button.textContent = "Copied!";

            setTimeout(() => {
                button.textContent = previous;
            }, 1500);

            errorMessage.textContent = "";

        } catch (error) {

            errorMessage.textContent =
                "Unable to copy. Please copy manually.";
        }
    }

    // =====================================
    // SAVE CURRENT FAVORITE
    // =====================================

    saveButton.addEventListener("click", () => {

        if (translatedText.dataset.translated !== "true") {

            errorMessage.textContent =
                "Translate some text before saving it.";

            return;
        }

        const original = inputText.value.trim();
        const translation = translatedText.textContent.trim();

        const source = sourceLanguage.value;
        const target = targetLanguage.value;

        const alreadySaved = savedTranslations.some(item =>

            item.original === original &&
            item.translation === translation &&
            item.source === source &&
            item.target === target
        );

        if (alreadySaved) {

            translationStatus.textContent =
                "This translation is already saved.";

            return;
        }

        savedTranslations.unshift({

            id: Date.now().toString() +
                Math.random().toString(36).slice(2),

            original,
            translation,
            source,
            target,

            sourceName: getLanguageName(source),
            targetName: getLanguageName(target),

            date: new Date().toISOString()
        });

        saveFavorites();
        renderSaved();

        translationStatus.textContent =
            "★ Favorite saved successfully!";
    });

    // =====================================
    // CHARACTER COUNTER
    // =====================================

    inputText.addEventListener("input", () => {

        characterCount.textContent =
            `${inputText.value.length} / 500`;

        errorMessage.textContent = "";
    });

    // =====================================
    // SWAP LANGUAGES
    // =====================================

    swapButton.addEventListener("click", () => {

        const previousSource = sourceLanguage.value;

        sourceLanguage.value = targetLanguage.value;
        targetLanguage.value = previousSource;

        if (translatedText.dataset.translated === "true") {

            inputText.value = translatedText.textContent;

            characterCount.textContent =
                `${inputText.value.length} / 500`;

            translatedText.innerHTML =
                '<span class="placeholder-text">Your translation will appear here...</span>';

            translatedText.dataset.translated = "false";
        }

        errorMessage.textContent = "";

        translationStatus.textContent = "Languages swapped";

        updateTextDirection();
    });

    // =====================================
    // CLEAR INPUT
    // =====================================

    clearButton.addEventListener("click", () => {

        inputText.value = "";

        translatedText.innerHTML =
            '<span class="placeholder-text">Your translation will appear here...</span>';

        translatedText.dataset.translated = "false";

        characterCount.textContent = "0 / 500";

        translationStatus.textContent = "Waiting for text";

        errorMessage.textContent = "";

        updateTextDirection();
    });

    // =====================================
    // TEXT DIRECTION
    // =====================================

    function updateTextDirection() {

        translatedText.setAttribute(
            "dir",
            rtlLanguages.includes(targetLanguage.value)
                ? "rtl"
                : "ltr"
        );
    }

    targetLanguage.addEventListener("change", updateTextDirection);

    // =====================================
    // TRANSLATE
    // =====================================

    translateButton.addEventListener("click", async () => {

        const text = inputText.value.trim();

        const source = sourceLanguage.value;
        const target = targetLanguage.value;

        errorMessage.textContent = "";

        if (!text) {

            errorMessage.textContent =
                "Please enter some text to translate.";

            inputText.focus();

            return;
        }

        if (source === target) {

            errorMessage.textContent =
                "Please select two different languages.";

            return;
        }

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

            translatedText.textContent = data.translated_text;

            translatedText.dataset.translated = "true";

            translationStatus.textContent =
                "Translation successful";

            updateTextDirection();

            addToHistory(
                text,
                data.translated_text,
                source,
                target
            );

        } catch (error) {

            translatedText.innerHTML =
                '<span class="placeholder-text">Your translation will appear here...</span>';

            translatedText.dataset.translated = "false";

            errorMessage.textContent = error.message;

            translationStatus.textContent =
                "Translation failed";

        } finally {

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

            errorMessage.textContent =
                "There is no translation to copy.";

            return;
        }

        copyText(
            translatedText.textContent.trim(),
            copyButton
        );
    });

    // =====================================
    // CLEAR ALL HISTORY
    // =====================================

    clearHistoryButton.addEventListener("click", () => {

        if (currentHistory.length === 0) {
            return;
        }

        const confirmed = confirm(
            "Are you sure you want to delete all translation history?"
        );

        if (!confirmed) {
            return;
        }

        currentHistory = [];

        saveHistory();
        renderHistory();

        translationStatus.textContent =
            "History cleared successfully.";
    });

    // =====================================
    // INITIAL SETUP
    // =====================================

    translatedText.dataset.translated = "false";

    updateTextDirection();

    loadHistory();
    loadSaved();

    console.log(
        "Lingua Studio JavaScript loaded successfully!"
    );

});
