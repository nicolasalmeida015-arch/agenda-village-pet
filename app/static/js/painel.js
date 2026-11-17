// Painel da gerência (RF08) e disparo dos lembretes da véspera (RF06). Apenas perfil "gerente".
const $ = id => document.getElementById(id);
const iso = d => d.toISOString().slice(0, 10);

async function carregar() {
  $("erro").classList.add("oculto");
  const d = await API.req("GET", `/api/equipe/indicadores?inicio=${$("inicio").value}&fim=${$("fim").value}`);
  $("i-total").textContent = d.total_agendamentos;
  $("i-faltas").textContent = d.taxa_faltas.toLocaleString("pt-BR") + "%";
  $("i-faltas-n").textContent = d.faltas + " falta(s) entre os atendimentos encerrados";
  $("i-ocupacao").textContent = d.ocupacao.toLocaleString("pt-BR") + "%";
  $("i-retorno").textContent = d.pets_sem_retorno;
  const ol = $("i-servicos"); ol.replaceChildren();
  if (!d.servicos_mais_procurados.length) ol.append(el("li", { class: "muted" }, "Sem atendimentos no período."));
  d.servicos_mais_procurados.forEach(s => ol.append(el("li", {}, s.servico + " – " + s.quantidade)));
}

$("form-periodo").addEventListener("submit", ev => {
  ev.preventDefault();
  if ($("fim").value < $("inicio").value) {
    mostrarErro($("erro"), { detail: "A data final deve ser igual ou posterior à inicial." }); return;
  }
  carregar().catch(e => mostrarErro($("erro"), e));
});

$("gerar").addEventListener("click", async () => {
  $("gerar").disabled = true;
  try {
    const itens = await API.req("POST", "/api/equipe/lembretes/vespera");
    const ul = $("lembretes"); ul.replaceChildren();
    $("lemb-vazio").classList.toggle("oculto", itens.length > 0);
    itens.forEach(i => {
      const li = el("li", { style: "margin-bottom:8px" });
      li.append(el("a", { href: i.link_whatsapp, target: "_blank", rel: "noopener" },
        "Enviar lembrete pelo WhatsApp (atendimento nº " + i.id_agendamento + ")"));
      ul.append(li);
    });
  } catch (e) { mostrarErro($("erro"), e); } finally { $("gerar").disabled = false; }
});

(async () => {
  try {
    const eu = await API.req("GET", "/api/auth/eu");
    if (eu.perfil !== "gerente") { location.href = "/equipe.html"; return; }
  } catch (_) { location.href = "/"; return; }
  const hoje = new Date();
  $("fim").value = iso(hoje);
  $("inicio").value = iso(new Date(hoje.getTime() - 29 * 864e5));
  carregar().catch(e => mostrarErro($("erro"), e));
})();
