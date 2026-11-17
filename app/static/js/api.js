// Cliente da API. Dados do usuário são inseridos com textContent (nunca innerHTML) - prevenção de XSS.
const API = {
  token: () => sessionStorage.getItem("token"),
  async req(metodo, url, corpo) {
    const headers = { "Content-Type": "application/json" };
    if (API.token()) headers.Authorization = "Bearer " + API.token();
    const r = await fetch(url, { method: metodo, headers, body: corpo ? JSON.stringify(corpo) : undefined });
    const dados = r.status === 204 ? null : await r.json().catch(() => null);
    if (!r.ok) throw { status: r.status, detail: dados && dados.detail };
    return dados;
  },
};
function el(tag, attrs = {}, texto) {
  const e = document.createElement(tag);
  Object.entries(attrs).forEach(([k, v]) => e.setAttribute(k, v));
  if (texto !== undefined) e.textContent = texto;
  return e;
}
function mensagemErro(err) {
  if (!err || !err.detail) return "Não foi possível concluir. Tente novamente.";
  if (typeof err.detail === "string") return err.detail;
  if (err.detail.mensagem) return err.detail.mensagem;
  if (Array.isArray(err.detail)) return "Confira os campos destacados e tente novamente.";
  return "Não foi possível concluir. Tente novamente.";
}
function mostrarErro(alvo, err) {
  alvo.textContent = "⚠️ " + mensagemErro(err);
  alvo.classList.remove("oculto");
  alvo.focus();
}
function fmtData(iso) {
  const d = new Date(iso);
  return d.toLocaleDateString("pt-BR", { weekday: "long", day: "2-digit", month: "2-digit" }) +
    " às " + d.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" });
}
