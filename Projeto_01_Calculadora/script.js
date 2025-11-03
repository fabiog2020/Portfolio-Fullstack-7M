console.log("Calculadora JS iniciada.");

// 1. CONFIGURAÇÃO (Roda uma única vez)
// Encontra os elementos de que precisaremos.
let botaoSomar = document.getElementById("BotaoSomar");
let botaoSubtrair = document.getElementById("BotaoSubtrair");
let botaoMultiplicar = document.getElementById("BotaoMultiplicar");
let botaoDividir = document.getElementById("BotaoDividir");

// Encontrando o elemento de exibição
let areaResultado = document.getElementById("resultado");

// 2. AÇÃO (Roda toda vez que o botãoSomar for clicado) 
botaoSomar.addEventListener('click', function() {
    // 1. CAPTURAR OS NÚMEROS AQUI DENTRO
    let numero1 = parseInt(document.getElementById("num1").value);
    let numero2 = parseInt(document.getElementById("num2").value);
    // 2. CALCULAR
    let resultado = numero1 + numero2;
    // 3. EXIBIR
    areaResultado.innerText = "O resultado é: " + resultado;
});
// 3. AÇÃO (Roda toda vez que o botãoSubtrair  for clicado) 
botaoSubtrair.addEventListener('click', function() {
    // 1. CAPTURAR OS NÚMEROS AQUI DENTRO
    let numero1 = parseInt(document.getElementById("num1").value);
    let numero2 = parseInt(document.getElementById("num2").value);
    // 2. CALCULAR
    let resultado = numero1 - numero2;
    // 3. EXIBIR
    areaResultado.innerText = "O resultado é: " + resultado;
});
// 4. AÇÃO (Roda toda vez que o botãoMultiplicar  for clicado) 
botaoMultiplicar.addEventListener('click', function() {
    // 1. CAPTURAR OS NÚMEROS AQUI DENTRO
    let numero1 = parseInt(document.getElementById("num1").value);
    let numero2 = parseInt(document.getElementById("num2").value);
    // 2. CALCULAR
    let resultado = numero1 * numero2;
    // 3. EXIBIR
    areaResultado.innerText = "O resultado é: " + resultado;
});
// 5. AÇÃO (Roda toda vez que o botãoDividir for clicado) 
botaoDividir.addEventListener('click', function() {
    // 1. CAPTURAR OS NÚMEROS AQUI DENTRO
    let numero1 = parseInt(document.getElementById("num1").value);
    let numero2 = parseInt(document.getElementById("num2").value);
    // 2. CALCULAR
    let resultado = numero1 / numero2;
    // 3. EXIBIR
    areaResultado.innerText = "O resultado é: " + resultado;
});