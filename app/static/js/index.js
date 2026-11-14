async function carregarInicio() {
  const eu = await API.req("GET", "/api/auth/eu");
  if (eu.perfil !== "tutor") { location.href = "/equipe.html"; return; }
  document.getElementById("tela-login").classList.add("oculto");
  document.getElementById("tela-inicio").classList.remove("oculto");
  document.getElementById("saudacao").textContent = "Olá, " + eu.nome.split(" ")[0] + "!";
  const [ags, pets] = await Promise.all([API.req("GET", "/api/agendamentos"), API.req("GET", "/api/pets")]);
  const futuros = ags.filter(a => ["agendado", "confirmado"].includes(a.status) && new Date(a.data_hora_inicio) > new Date())
    .sort((a, b) => a.data_hora_inicio.localeCompare(b.data_hora_inicio));
  if (futuros.length) {
    const a = futuros[0], pet = pets.find(p => p.id_pet === a.id_pet);
    document.getElementById("proximo").textContent = (pet ? pet.nome : "Pet") + " • " + fmtData(a.data_hora_inicio);
  }
}
document.getElementById("form-login").addEventListener("submit", async (ev) => {
  ev.preventDefault();
  const erro = document.getElementById("erro-login");
  erro.classList.add("oculto");
  try {
    const t = await API.req("POST", "/api/auth/login", {
      email: document.getElementById("email").value, senha: document.getElementById("senha").value });
    sessionStorage.setItem("token", t.access_token);
    await carregarInicio();
  } catch (e) { mostrarErro(erro, e); }
});
document.getElementById("sair").addEventListener("click", async () => {
  try { await API.req("POST", "/api/auth/logout"); } catch (_) {}
  sessionStorage.removeItem("token"); location.reload();
});
if (API.token()) carregarInicio().catch(() => sessionStorage.removeItem("token"));
