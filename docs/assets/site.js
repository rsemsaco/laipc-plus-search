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

// User-paced journey. Without JavaScript all four scenes remain readable.
const journeyTabs = Array.from(document.querySelectorAll('.journey-tabs [role="tab"]'));
const journeyPanels = journeyTabs.map(tab => $(tab.getAttribute('aria-controls')));
const journeyNames = ['Seu projeto', 'A leitura', 'A busca', 'Sua análise'];
const nextLabels = ['Ver a leitura →', 'Explorar a busca →', 'Comparar estudos →', 'Recomeçar ↺'];
let journeyIndex = 0;
function showJourney(index, focusTab = false) {
  journeyIndex = Math.max(0, Math.min(index, journeyTabs.length - 1));
  journeyTabs.forEach((tab, i) => {
    const active = i === journeyIndex;
    tab.setAttribute('aria-selected', String(active));
    tab.tabIndex = active ? 0 : -1;
    journeyPanels[i].hidden = !active;
  });
  $('research-journey').dataset.stage = String(journeyIndex);
  $('journey-prev').disabled = journeyIndex === 0;
  $('journey-next').textContent = nextLabels[journeyIndex];
  $('journey-status').textContent = `${journeyNames[journeyIndex]} · ${journeyIndex + 1} de 4`;
  if (focusTab) journeyTabs[journeyIndex].focus({preventScroll:true});
}
journeyTabs.forEach((tab, index) => {
  const panel = journeyPanels[index];
  panel.setAttribute('role', 'tabpanel');
  panel.setAttribute('aria-labelledby', tab.id);
  tab.addEventListener('click', () => showJourney(index));
  tab.addEventListener('keydown', event => {
    let target = index;
    if (event.key === 'ArrowRight') target = (index + 1) % journeyTabs.length;
    else if (event.key === 'ArrowLeft') target = (index + journeyTabs.length - 1) % journeyTabs.length;
    else if (event.key === 'Home') target = 0;
    else if (event.key === 'End') target = journeyTabs.length - 1;
    else return;
    event.preventDefault();
    showJourney(target, true);
  });
});
$('journey-prev').addEventListener('click', () => showJourney(journeyIndex - 1));
$('journey-next').addEventListener('click', () => showJourney((journeyIndex + 1) % journeyTabs.length));
$('research-journey').classList.add('enhanced');
$('journey-navigation').hidden = false;
$('journey-controls').hidden = false;
showJourney(0);

const excerptNotes = [
  'A pergunta orienta quais relações procurar entre os estudos.',
  'Os participantes ajudam a perceber se um estudo se aplica ao público que você investiga.',
  'As medidas mostram o que foi observado. Atenção e memória, por exemplo, não são a mesma coisa.'
];
const sourceNotes = [
  'Europe PMC: explorar artigos de ciências da vida e saúde.',
  'OpenAlex: ampliar a descoberta de literatura em diferentes áreas.',
  'DataCite: localizar registros de dados e outros materiais de pesquisa.'
];
function bindExplainers(selector, key, outputId, notes) {
  const buttons = Array.from(document.querySelectorAll(selector));
  buttons.forEach(button => button.addEventListener('click', () => {
    buttons.forEach(item => item.setAttribute('aria-pressed', String(item === button)));
    $(outputId).textContent = notes[Number(button.dataset[key])];
  }));
}
bindExplainers('[data-excerpt]', 'excerpt', 'excerpt-explanation', excerptNotes);
bindExplainers('[data-source]', 'source', 'source-explanation', sourceNotes);

// One brief entrance per section; never auto-advance or loop animations.
if ('IntersectionObserver' in window && !window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
  const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('is-visible');
        observer.unobserve(entry.target);
      }
    });
  }, {threshold:0.08});
  document.querySelectorAll('.origin-story, .values-connected article, .plan, .oversight-path').forEach(element => {
    element.classList.add('reveal-ready');
    observer.observe(element);
  });
}
