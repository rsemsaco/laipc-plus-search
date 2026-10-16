# LAIPC+ — landing de apresentação

## Escopo
Site estático em `docs/`, sem dependências, compilação, cookies ou analytics.
Nenhum arquivo do motor, providers, configuração, corpus ou workflow de busca foi alterado.
A busca existente continua em Actions > LAIPC+ Search Engine.

## Branding
- Slogan: Sua pesquisa é o ponto de partida.
- Assinatura: De pesquisador, para pesquisadores.
- Verde profundo #173e35; marfim #f6f4ed; cobre #9b5137.
- Logo: monograma L e +, com ponto de evidência, em docs/assets/symbol.svg.
- Tipografia: Georgia para títulos editoriais; Arial para interface, sem fontes externas.
- Referências de organização de produto: Elicit (fluxo guiado) e ResearchRabbit (pesquisa conectada). Não há afiliação.

## Funcionamento
O formulário inicial abre um roteiro local editável. Não executa IA, consulta ao motor nem upload.
O exemplo é preenchido explicitamente; perguntas livres não geram interpretação automática.
O usuário confirma o mapa e pode exportar TXT ou abrir sua pergunta na Europe PMC.
Somente esse clique explícito envia a pergunta à base externa. Nenhum dado é persistido pelo site.
Planos abrem detalhes em modal; preços e cotas são fictícios e não há contratação.
Todos os recursos futuros são apresentados como visão de produto.

## Publicar no GitHub Pages
1. Após merge, abrir Settings > Pages.
2. Em Build and deployment, selecionar Deploy from a branch.
3. Branch: main. Folder: /docs. Salvar.
4. Acompanhar Actions > pages build and deployment até concluir.
5. Abrir https://rsemsaco.github.io/laipc-plus-search/ e verificar Enforce HTTPS.

O repositório é privado. Se o plano da conta não oferecer Pages para repositórios privados,
não tornar o repositório público: ele contém corpus e código de pesquisa. Usar um plano
compatível ou um repositório público separado contendo somente docs/ mediante decisão do proprietário.
O site Pages pode ser público mesmo quando o repositório é privado; não publicar dados confidenciais.
A integração disponível não administra Settings > Pages.

## Validação
python3 site-tools/check_site.py
node --check docs/assets/site.js
CI isolado: .github/workflows/landing-ci.yml
Revisão estrutural em breakpoints 390, 700, 1000 e 1400 px; browser QA não executado
neste ambiente por indisponibilidade da capacidade de navegador exigida pela skill Sites.
Validar visualmente em 360/390/768/1024/1440 px antes de apresentação, incluindo formulário,
modal de planos, teclado, download, link externo e ausência de rolagem horizontal.

## Indexação e evolução
Noindex intencional: demonstração de conceito, não lançamento comercial. O sitemap fica
preparado, mas não deve ser enviado ao Search Console nesta etapa. O robots.txt de um
projeto Pages não controla o domínio inteiro; a diretiva meta noindex é a proteção principal
contra indexação, não um controle de acesso.
Quando houver produto público: revisar promessas, privacidade e planos; remover noindex;
configurar domínio e Search Console; então GA4/CTA e baseline de 7–14 dias; divulgação
orgânica; só depois avaliar campanha de 30 dias, orçamento e revisão semanal. Sem ads agora.

## Reversão
Reverter apenas o PR da landing ou desativar Pages. O motor original permanece independente.
