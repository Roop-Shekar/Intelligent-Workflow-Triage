document.querySelectorAll("[data-example]").forEach((button) => {
    button.addEventListener("click", () => {
        const textarea = document.querySelector("textarea[name='raw_request']");
        textarea.value = button.dataset.example;
        textarea.focus();
    });
});
