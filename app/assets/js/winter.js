const numFlakes = 100; // Nombre de flocons
const snowContainer = document.body;

// Crée les flocons de neige
for (let i = 0; i < numFlakes; i++) {
    const snowFlake = document.createElement('div');
    snowFlake.classList.add('snow', 'text-white');
    snowFlake.textContent = '*';  // Caractère représentant la neige
    snowFlake.style.left = `${Math.random() * 100}vw`;  // Position aléatoire sur l'axe X
    snowFlake.style.animationDuration = `${Math.random() * 3 + 7.5}s`;  // Durée aléatoire de la chute
    snowFlake.style.animationDelay = `${Math.random() * 5}s`;  // Retard aléatoire avant de commencer la chute
    snowContainer.appendChild(snowFlake);
}