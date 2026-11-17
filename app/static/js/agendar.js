let escolhido = null, pets = [], servicos = [], requisicao = 0;
const $ = id => document.getElementById(id);

function botaoHorario(slot, alvo) {
  const b = el("button", { type: "button", class: "h", "aria-pressed": "false" });
  b.append(document.createTextNode(slot.inicio.slice(11, 16)), el("small", {}, "Livre"));
  b.addEventListener("click", () => {
    alvo.querySelectorAll(".h").forEach(x => { x.setAttribute("aria-pressed", "false"); x.lastChild.textContent = "Livre"; });
    b.setAttribute("aria-pressed", "true"); b.lastChild.textContent = "✓ Escolhido";
    escolhido = slot;
    const pet = pets.find(p => p.id_pet == $("pet").value), sv = servicos.find(s => s.id_servico == $("servico").value);
    $("resumo").textContent = pet.nome + " • " + sv.nome + " • " + fmtData(slot.inicio);
    $("resumo").classList.remove("oculto");
    $("confirmar").disabled = false;
  });
  return b;
}

async function carregarHorarios() {
  escolhido = null; $("confirmar").disabled = true; $("resumo").classList.add("oculto");
  const horas = $("horas"); horas.replaceChildren();
  if (!$("pet").value || !$("dia").value) return;
  const minha = ++requisicao;  // evita lista duplicada quando duas consultas terminam fora de ordem
  const slots = await API.req("GET", `/api/disponibilidade?id_pet=${$("pet").value}&id_servico=${$("servico").value}&dia=${$("dia").value}`);
  if (minha !== requisicao) return;
  horas.replaceChildren();
  const vistos = new Set();  // um botão por horário (o servidor escolhe um profissional livre)
  slots.filter(s => !vistos.has(s.inicio) && vistos.add(s.inicio)).forEach(s => horas.append(botaoHorario(s, horas)));
  $("sem-horario").classList.toggle("oculto", slots.length > 0);
}

async function confirmar(slot) {
  $("erro").classList.add("oculto");
  try {
    const ag = await API.req("POST", "/api/agendamentos", { id_pet: +$("pet").value, id_servico: +$("servico").value,
      id_profissional: slot.id_profissional, data_hora_inicio: slot.inicio });
    $("conflito").classList.add("oculto");
    $("passo-escolha").classList.add("oculto");
    $("detalhe").textContent = $("resumo").textContent || fmtData(ag.data_hora_inicio);
    $("passo-resultado").classList.remove("oculto");
    $("voltar-rodape").classList.add("oculto");  // a tela de confirmação já tem o botão de voltar
    listarMeus();
  } catch (e) {
    if (e.status === 409 && e.detail && e.detail.alternativas) {
      $("msg-conflito").textContent = e.detail.mensagem;
      const alt = $("alternativas"); alt.replaceChildren();
      e.detail.alternativas.forEach(a => {
        const b = botaoHorario({ inicio: a.inicio, id_profissional: a.id_profissional }, alt);
        b.addEventListener("click", () => confirmar({ inicio: a.inicio, id_profissional: a.id_profissional }));
        alt.append(b);
      });
      $("conflito").classList.remove("oculto"); $("conflito").focus();
      carregarHorarios();  // o horário que ficou ocupado sai da grade
    } else mostrarErro($("erro"), e);
  }
}

const CANCELAVEIS = new Set(["agendado", "confirmado"]);

function botaoCancelar(ag, li) {
  // Dois toques para cancelar (sem janela de confirmação do navegador): "Cancelar" -> "Confirmar cancelamento"
  const b = el("button", { type: "button", class: "btn", style: "min-height:48px;margin-top:6px" }, "Cancelar este agendamento");
  const manter = el("button", { type: "button", class: "btn oculto", style: "min-height:48px;margin-top:6px" }, "Manter agendamento");
  b.addEventListener("click", async () => {
    if (b.dataset.confirmar !== "1") {
      b.dataset.confirmar = "1"; b.textContent = "Confirmar cancelamento"; b.classList.add("prim");
      manter.classList.remove("oculto"); b.focus(); return;
    }
    b.disabled = true;
    try {
      await API.req("POST", `/api/agendamentos/${ag.id_agendamento}/cancelar`);
      $("aviso-meus").textContent = "Agendamento de " + fmtData(ag.data_hora_inicio) + " cancelado. O horário foi liberado.";
      $("aviso-meus").classList.remove("oculto");
      await listarMeus(); carregarHorarios().catch(() => {});
    } catch (e) { b.disabled = false; mostrarErro($("erro"), e); }
  });
  manter.addEventListener("click", () => {
    delete b.dataset.confirmar; b.textContent = "Cancelar este agendamento"; b.classList.remove("prim");
    manter.classList.add("oculto"); b.focus();
  });
  li.append(b, manter);
}

async function listarMeus() {
  const ul = $("lista-ags"); ul.replaceChildren();
  const ags = await API.req("GET", "/api/agendamentos");
  if (!ags.length) ul.append(el("li", { class: "muted" }, "Nenhum agendamento."));
  ags.forEach(a => {
    const li = el("li", { style: "margin-bottom:10px" }, fmtData(a.data_hora_inicio) + " – " + a.status);
    if (CANCELAVEIS.has(a.status) && new Date(a.data_hora_inicio) > new Date()) botaoCancelar(a, li);
    ul.append(li);
  });
}

(async () => {
  try {
    [pets, servicos] = await Promise.all([API.req("GET", "/api/pets"), API.req("GET", "/api/servicos")]);
  } catch (_) { location.href = "/"; return; }
  pets.forEach(p => $("pet").append(el("option", { value: p.id_pet }, p.nome + " – porte " + p.porte)));
  servicos.forEach(s => $("servico").append(el("option", { value: s.id_servico }, s.nome)));
  const amanha = new Date(Date.now() + 864e5); $("dia").value = amanha.toISOString().slice(0, 10);
  ["pet", "servico", "dia"].forEach(id => $(id).addEventListener("change", () => carregarHorarios().catch(e => mostrarErro($("erro"), e))));
  $("confirmar").addEventListener("click", () => escolhido && confirmar(escolhido));
  await carregarHorarios(); await listarMeus();
})();
