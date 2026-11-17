async function listar() {
  const lista = document.getElementById("lista");
  lista.replaceChildren();
  const pets = await API.req("GET", "/api/pets");
  if (!pets.length) lista.append(el("li", { class: "muted" }, "Nenhum pet cadastrado ainda."));
  pets.forEach(p => lista.append(el("li", {}, "🐶 " + p.nome + " – porte " + p.porte)));
}
document.getElementById("form").addEventListener("submit", async (ev) => {
  ev.preventDefault();
  const v = id => document.getElementById(id).value;
  try {
    await API.req("POST", "/api/pets", { nome: v("nome"), especie: v("especie"), porte: v("porte"),
      pelagem: v("pelagem"), alergias_observacoes: v("obs") || null });
    ev.target.reset(); await listar();
  } catch (e) { mostrarErro(document.getElementById("erro"), e); }
});
listar().catch(() => (location.href = "/"));
