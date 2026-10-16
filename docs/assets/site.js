'use strict';
const $ = id => document.getElementById(id);
const example = {question:'Como o estresse crônico afeta a flexibilidade cognitiva em modelos animais?',population:'Roedores expostos a protocolos de estresse crônico',method:'Estudo experimental com avaliação comportamental'};
let confirmedMap = null;
function openDemo(useExample = false) {
  const question = $('research-query').value.trim();
  if (!question) { $('research-query').setCustomValidity('Digite uma pergunta ou use o exemplo.'); $('research-query').reportValidity(); return; }
  $('map-question').value = question;
  $('map-population').value = useExample ? example.population : '';
  $('map-method').value = useExample ? example.method : '';
  $('map-result').hidden = true;
  confirmedMap = null;
  $('demo').hidden = false;
  $('demo-title').focus({preventScroll:true});
  $('demo').scrollIntoView({block:'start'});
}
$('research-query').addEventListener('input', () => $('research-query').setCustomValidity(''));
$('search-form').addEventListener('submit', event => {event.preventDefault();openDemo();});
$('example').addEventListener('click', () => { $('research-query').setCustomValidity('');$('research-query').value = example.question;openDemo(true); });
$('close-demo').addEventListener('click', () => { $('demo').hidden = true;$('research-query').focus(); });
$('map-form').addEventListener('input', () => {$('map-result').hidden = true;confirmedMap = null;});
$('map-form').addEventListener('submit', event => {
  event.preventDefault();
  const fields = ['map-question','map-population','map-method'];
  for (const id of fields) { if (!$(id).value.trim()) { $(id).focus();return; } }
  confirmedMap = {question:$('map-question').value.trim(),population:$('map-population').value.trim(),method:$('map-method').value.trim(),goal:$('map-goal').value};
  $('map-summary').textContent = `${confirmedMap.goal} · Objeto: ${confirmedMap.population} · Método: ${confirmedMap.method}.`;
  $('external-search').href = 'https://europepmc.org/search?query=' + encodeURIComponent(confirmedMap.question);
  $('map-result').hidden = false;
  $('map-result').scrollIntoView({block:'nearest'});
});
$('download-map').addEventListener('click', () => {
  if (!confirmedMap) return;
  const text = `LAIPC+ — Roteiro de pesquisa\nDemonstração: conteúdo informado pelo usuário, sem análise por IA.\n\nPergunta: ${confirmedMap.question}\nPopulação/objeto: ${confirmedMap.population}\nMétodo: ${confirmedMap.method}\nObjetivo: ${confirmedMap.goal}\n\nPróximo passo: definir bases, critérios de elegibilidade e estratégia de busca.\nEste roteiro não constitui um levantamento executado.\n`;
  const url = URL.createObjectURL(new Blob([text], {type:'text/plain;charset=utf-8'}));
  const a = document.createElement('a');a.href=url;a.download='LAIPC-roteiro-de-pesquisa.txt';document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);
});
const dialog = $('plan-dialog');
document.querySelectorAll('.plan-button').forEach(button => button.addEventListener('click', () => {
  const team = button.dataset.plan === 'Teams';
  $('plan-title').textContent = `Plano ${button.dataset.plan}`;
  $('plan-description').textContent = team ? 'Simulação de R$ 249,90/mês para até 5 pesquisadores, com 25 levantamentos ampliados e 10 análises profundas compartilhados por mês.' : 'Simulação de R$ 59,90/mês para 1 pesquisador, com 5 levantamentos ampliados e 2 análises profundas por mês.';
  dialog.showModal();
}));
$('close-plan').addEventListener('click', () => dialog.close());
$('plan-demo').addEventListener('click', () => {dialog.close();$('research-query').focus();});

// Illustrative comparison: curated examples only, no scientific analysis or requests.
const comparisonViews = {
  participants: {
    project:'Estudantes universitários', a:'Adultos de diferentes idades', b:'Estudantes universitários',
    insight:'O Estudo B se aproxima do seu público. Isso, por si só, não diz se ele tem melhor qualidade.',
    source:'Estudo A: “Participaram adultos de diferentes idades.”\nEstudo B: “Participaram estudantes universitários.”'
  },
  method: {
    project:'Acompanhar os mesmos estudantes ao longo do semestre', a:'Uma avaliação em um único dia', b:'Avaliações ao longo de seis meses',
    insight:'O Estudo B também acompanha mudanças ao longo do tempo. O Estudo A oferece um retrato de um momento. Você decide qual comparação é útil.',
    source:'Estudo A: “A coleta ocorreu em uma única sessão.”\nEstudo B: “Os participantes foram avaliados mensalmente durante seis meses.”'
  },
  findings: {
    project:'Qualidade do sono e desempenho em testes de memória', a:'Horas de sono e atenção', b:'Qualidade do sono e memória',
    insight:'O Estudo A mede atenção; o B, memória. Medidas diferentes respondem a perguntas diferentes — não devem ser tratadas como equivalentes.',
    source:'Estudo A: “Registramos as horas de sono e aplicamos um teste de atenção.”\nEstudo B: “Avaliamos a qualidade do sono e o desempenho em tarefas de memória.”'
  }
};
$('compare-view').addEventListener('change', event => {
  const view = comparisonViews[event.target.value];
  if (!view) return;
  for (const key of ['project','a','b','insight','source']) $('compare-' + key).textContent = view[key];
});
