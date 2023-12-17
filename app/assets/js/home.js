document.addEventListener('DOMContentLoaded', function() {
    let titleDiv = document.querySelector('#title');
    titleDiv.classList.add('loaded');

    let logos = document.querySelectorAll('.img-fluid');
    logos.forEach(logo => {
        logo.classList.add('loaded')
    });
})