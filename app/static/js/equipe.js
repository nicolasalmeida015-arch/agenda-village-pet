const ROTULOS = { agendado: "🕒 Agendado", confirmado: "✔️ Confirmado", em_atendimento: "🛁 Em atendimento",
  concluido: "✅ Concluído", faltou: "❌ Faltou", cancelado: "🚫 Cancelado" };
const PROXIMOS = { agendado: ["confirmado", "em_atendimento", "faltou", "cancelado"], confirmado: ["em_atendimento", "faltou", "cancelado"],
  em_atendimento: ["concluido"] };
const dia = document.getElementById("dia");
dia.value = new Date().toISOString().slice(0, 10);

let requisicao = 0;

async function carregar() {
  const tbody = document.getElementById("linhas");
  const minha = ++requisicao;  // duas cargas simultâneas (troca de data + carga inicial) não duplicam linhas
  const itens = await API.req("GET", "/api/equipe/agenda?dia=" + dia.value);
  if (minha !== requisicao) return;
  tbody.replaceChildren();
  document.getElementById("vazio").classList.toggle("oculto", itens.length > 0);
  // Ajuste da validação (rodada 1): resumo do que está pendente e de quantos pets pedem cuidado especial
  const ativos = itens.filter(a => a.status !== "cancelado");
  const aConfirmar = ativos.filter(a => a.status === "agendado").length;
  const cuidados = ativos.filter(a => a.pet_alergias).length;
  const resumo = document.getElementById("resumo-dia");
  resumo.textContent = ativos.length + " atendimento(s) · " + aConfirmar + " aguardando confirmação · "
    + cuidados + " com cuidado especial";
  resumo.classList.toggle("oculto", itens.length === 0);
  itens.forEach(a => {
    const tr = el("tr");
    tr.append(el("td", {}, a.data_hora_inicio.slice(11, 16) + "–" + a.data_hora_fim.slice(11, 16)));
    const ficha = el("td"); ficha.append(el("strong", {}, a.pet_nome), el("div", { class: "muted" }, "Porte " + a.pet_porte));
    if (a.pet_alergias) {
      tr.classList.add("linha-cuidado");
      const aviso = el("div", { class: "cuidado" });
      aviso.append(el("strong", {}, "⚠️ Cuidado especial"), el("div", {}, a.pet_alergias));
      ficha.append(aviso);
    }
    tr.append(ficha, el("td", {}, a.servico_nome + " / " + a.profissional_nome));
    const st = el("td"); st.append(el("span", { class: "status" }, ROTULOS[a.status] || a.status));
    const jaPassou = new Date(a.data_hora_inicio) <= new Date();
    if ((PROXIMOS[a.status] || []).length) st.append(el("div", { class: "muted", style: "margin-top:6px" }, "Próximo passo:"));
    (PROXIMOS[a.status] || []).filter(n => n !== "faltou" || jaPassou).forEach(n => {
      const b = el("button", { type: "button", class: "btn", style: "min-height:48px;margin-top:6px;font-size:.9rem" }, ROTULOS[n]);
      b.addEventListener("click", async () => {
        try { await API.req("PATCH", `/api/equipe/agendamentos/${a.id_agendamento}/status`, { status: n }); await carregar(); }
        catch (e) { mostrarErro(document.getElementById("erro"), e); }
      });
      st.append(b);
    });
    tr.append(st); tbody.append(tr);
  });
}
dia.addEventListener("change", () => carregar().catch(e => mostrarErro(document.getElementById("erro"), e)));
document.getElementById("sair").addEventListener("click", () => { sessionStorage.removeItem("token"); location.href = "/"; });
carregar().catch(() => (location.href = "/"));
API.req("GET", "/api/auth/eu").then(eu => {  // só a gerência vê o atalho para o painel
  if (eu.perfil === "gerente") document.getElementById("link-painel").classList.remove("oculto");
}).catch(() => {});
