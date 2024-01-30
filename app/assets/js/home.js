document.addEventListener("DOMContentLoaded", function() {
    let panel = document.querySelector("#main-panel");
    panel.style.height = (window.innerHeight - document.querySelector("#title").clientHeight) + 'px'
});