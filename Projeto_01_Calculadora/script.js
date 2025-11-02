console.log("Calculadora JS iniciada.");

// 1. CONFIGURAÇÃO (Roda uma única vez)
// Encontra os elementos de que precisaremos.
let botao = document.getElementById("meuBotao");

// Encontrando o elemento de exibição
let areaResultado = document.getElementById("resultado");

// 2. AÇÃO (Roda toda vez que o botão for clicado) 
botao.addEventListener('click', function() {
    // 1. CAPTURAR OS NÚMEROS AQUI DENTRO
    let numero1 = parseInt(document.getElementById("num1").value);
    let numero2 = parseInt(document.getElementById("num2").value);
    // 2. CALCULAR
    let resultado = numero1 + numero2;
    // 3. EXIBIR
    let areaResultado = document.getElementById("resultado");
    areaResultado.innerText = "O resultado é: " + resultado;
});