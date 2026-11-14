document.getElementById("form").addEventListener("submit", async (ev) => {
  ev.preventDefault();
  const erro = document.getElementById("erro");
  const v = id => document.getElementById(id).value;
  try {
    await API.req("POST", "/api/auth/cadastro", { nome: v("nome"), email: v("email"), telefone_whatsapp: v("tel"),
      senha: v("senha"), consentimento_lgpd: document.getElementById("lgpd").checked });
    const t = await API.req("POST", "/api/auth/login", { email: v("email"), senha: v("senha") });
    sessionStorage.setItem("token", t.access_token);
    location.href = "/pets.html";
  } catch (e) { mostrarErro(erro, e); }
});
