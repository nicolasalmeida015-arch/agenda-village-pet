const ROTULOS = { agendado: "🕒 Agendado", confirmado: "✔️ Confirmado", em_atendimento: "🛁 Em atendimento",
  concluido: "✅ Concluído", faltou: "❌ Faltou", cancelado: "🚫 Cancelado" };
const PROXIMOS = { agendado: ["confirmado", "em_atendimento", "faltou", "cancelado"], confirmado: ["em_atendimento", "faltou", "cancelado"],
  em_atendimento: ["concluido"] };
const dia = document.getElementById("dia");
dia.value = new Date().toISOString().slice(0, 10);

async function carregar() {
  const tbody = document.getElementById("linhas"); tbody.replaceChildren();
  const itens = await API.req("GET", "/api/equipe/agenda?dia=" + dia.value);
  document.getElementById("vazio").classList.toggle("oculto", itens.length > 0);
  itens.forEach(a => {
    const tr = el("tr");
    tr.append(el("td", {}, a.data_hora_inicio.slice(11, 16) + "–" + a.data_hora_fim.slice(11, 16)));
    const ficha = el("td"); ficha.append(el("strong", {}, a.pet_nome), el("div", { class: "muted" }, "Porte " + a.pet_porte));
    if (a.pet_alergias) ficha.append(el("div", {}, "⚠️ " + a.pet_alergias));
    tr.append(ficha, el("td", {}, a.servico_nome + " / " + a.profissional_nome));
    const st = el("td"); st.append(el("span", { class: "status" }, ROTULOS[a.status] || a.status));
    const jaPassou = new Date(a.data_hora_inicio) <= new Date();
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
