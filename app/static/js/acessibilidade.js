// Recurso de acessibilidade (RNF04): "A+ Alto contraste" aumenta a letra em 25% e reforça o contraste.
// Carregado no <head> de todas as telas, antes da renderização, para não "piscar" ao abrir a página.
// A escolha fica salva no aparelho (localStorage) e vale para todas as telas do app.
(function () {
  const CHAVE = "village-a11y-alto-contraste";
  const raiz = document.documentElement;
  let ativo = false;
  try { ativo = localStorage.getItem(CHAVE) === "1"; } catch (e) { /* navegação privada: usa o padrão */ }
  raiz.classList.toggle("a11y", ativo);

  document.addEventListener("DOMContentLoaded", function () {
    const header = document.querySelector("header");
    if (!header) return;
    const textos = document.createElement("div");
    while (header.firstChild) textos.appendChild(header.firstChild);
    header.appendChild(textos);

    const botao = document.createElement("button");
    botao.type = "button";
    botao.className = "btn-a11y";
    botao.textContent = "A+ Alto contraste";
    botao.title = "Aumenta a letra e reforça o contraste das cores";
    botao.setAttribute("aria-pressed", String(ativo));
    botao.addEventListener("click", function () {
      ativo = !ativo;
      raiz.classList.toggle("a11y", ativo);
      botao.setAttribute("aria-pressed", String(ativo));
      try { localStorage.setItem(CHAVE, ativo ? "1" : "0"); } catch (e) { /* sem persistência */ }
    });
    header.appendChild(botao);
  });
})();
