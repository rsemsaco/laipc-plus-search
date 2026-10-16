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
