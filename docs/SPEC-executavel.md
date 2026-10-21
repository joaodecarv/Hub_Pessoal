# Hub Pessoal como executável para Ubuntu 24.04, com edição completa das finanças

## Problem Statement

Hoje as finanças do João vivem em dois programas. O Banco é um app desktop PySide6, cujo build mais recente está só em `packaging/AppDir`, sem AppImage na raiz nem atalho no menu. É nele que se importam extratos e se cadastram transações, contas, categorias, metas e orçamentos. O Hub Pessoal é a interface que ele de fato quer usar (dashboard monocromático, planilha, resumos de notícias pelo Gemini), mas só lê o `banco.db`, não consegue alterar nada e só roda em modo desenvolvimento: `./start.sh` sobe Uvicorn e Vite, e ele abre `localhost:5173` no navegador.

Resultado: para corrigir uma transação ou importar um extrato ele precisa sair do Hub, e o Hub não se comporta como um programa normal que se abre com um clique.

## Solution

O Hub Pessoal vira um app desktop comum para Ubuntu 24.04 e substitui o Banco por completo.

- Um único arquivo `HubPessoal-x86_64.AppImage` na pasta `Meus_Projetos/Banco/` abre com clique duplo. Um atalho "Hub Pessoal" no menu de aplicativos tem um ícone novo: cifrão preto em fundo branco.
- Abrir o app mostra a janela do Hub. Nenhum servidor, porta ou navegador fica visível. Abrir de novo foca a janela que já está aberta. Fechar a janela encerra o app.
- Tudo o que o Hub já faz continua funcionando: início, dashboard de finanças, planilha, notícias de IA e de Finanças.
- Novas capacidades de escrita: criar, editar e excluir transações; importar extratos OFX/CSV com prévia; gerir contas, categorias e regras de categorização; gerir metas (com aportes) e orçamentos mensais; configurar a chave do Gemini pela própria interface.
- A interface fica toda em português (R$, datas dd/mm/aaaa).
- Se não existir `banco.db`, o app cria um banco novo já com contas e categorias padrão. O `banco.db` é copiado automaticamente uma vez por dia.
- Uma versão nova é gerada com um único comando (`./release.sh`), que substitui o AppImage e o atalho.

## User Stories

### Abrir e usar como app

1. Como João, quero abrir o Hub com clique duplo num arquivo em `Meus_Projetos/Banco/`, para usá-lo como qualquer programa.
2. Como João, quero encontrar "Hub Pessoal" no menu de aplicativos do Ubuntu, para abrir sem procurar o arquivo.
3. Como João, quero que o ícone seja um cifrão preto em fundo branco, para reconhecer o app na dock e no menu.
4. Como João, quero que o app abra sem servidor local nem porta, para que ele se comporte como um bloco de notas e não como um site.
5. Como João, quero que clicar no ícone com o app já aberto traga a janela existente para a frente, para não ter duas instâncias gravando no mesmo banco.
6. Como João, quero que fechar a janela encerre o app por completo, para não deixar processos esquecidos.
7. Como João, quero que a janela lembre o tema claro/escuro escolhido entre aberturas, para não reconfigurar toda vez.
8. Como João, quero ver a versão do app em Configurações, para saber qual build estou usando.

### Dados e segurança

9. Como João, quero que o app continue usando meu `banco.db` atual em `~/.local/share/banco/`, para não perder nenhum dado do Banco.
10. Como João, quero que, se não houver `banco.db`, o app crie um banco novo com as contas e categorias padrão, para poder começar do zero numa máquina nova.
11. Como João, quero que meus digests já gerados (`hub.db`) sejam levados para a pasta de dados do app na primeira execução, para não perder o histórico de notícias.
12. Como João, quero uma cópia automática do `banco.db` uma vez por dia, ao abrir o app, para poder voltar atrás se uma edição ou importação der errado.
13. Como João, quero que só as 14 cópias mais recentes sejam mantidas, para o backup não encher o disco.
14. Como João, quero que a chave do Gemini nunca fique dentro do executável, para que uma cópia do AppImage não vaze meu segredo.

### Navegação e idioma

15. Como João, quero a navegação "Início · Finanças · Transações · Metas & Orçamentos · Notícias · Configurações", para achar cada coisa pelo que estou fazendo.
16. Como João, quero todas as telas em português, as novas e as existentes, para o app ficar consistente.
17. Como João, quero que dashboard, planilha e saldos reflitam na hora qualquer transação que eu criar, editar, excluir ou importar, para confiar nos números.

### Transações

18. Como João, quero filtrar a lista de transações por mês, para revisar um mês específico.
19. Como João, quero filtrar por conta e por categoria, para achar lançamentos de um cartão ou de um tipo de gasto.
20. Como João, quero buscar por descrição, para achar uma transação específica rapidamente.
21. Como João, quero clicar numa transação e ver um painel lateral com todos os campos, para editá-la sem sair da lista.
22. Como João, quero editar data, valor, tipo (receita, despesa, poupança), descrição, conta, categoria, notas e fixo/variável, para corrigir qualquer erro de lançamento ou de importação.
23. Como João, quero deixar o fixo/variável como "herdar da categoria" ou forçar um valor, para tratar exceções sem mudar a categoria.
24. Como João, quero que o seletor de categoria mostre só as categorias do tipo da transação, para não classificar uma despesa como receita.
25. Como João, quero criar uma transação manualmente pelo botão "+ Nova", para lançar gastos em dinheiro ou fora do extrato.
26. Como João, quero excluir uma transação com confirmação, para remover duplicatas sem medo de clicar errado.
27. Como João, quero mensagens de validação claras (valor maior que zero, data válida, conta obrigatória), para saber o que corrigir.
28. Como João, quero vincular uma transação de poupança a uma meta pelo painel ("Conta para a meta: …"), para registrar aportes onde eu já estou.

### Importação OFX/CSV

29. Como João, quero importar um arquivo OFX escolhendo a conta de destino, para trazer o extrato do banco sem digitar.
30. Como João, quero importar um CSV, para usar bancos que não exportam OFX.
31. Como João, quero mapear as colunas do CSV (data, descrição, valor, e como interpretar o sinal) na primeira importação de cada conta, para o app entender o formato.
32. Como João, quero que esse mapeamento fique salvo por conta, para não refazê-lo a cada mês.
33. Como João, quero ver uma prévia antes de importar, com cada linha, a categoria sugerida pelas regras e o tipo inferido, para conferir antes de gravar.
34. Como João, quero que as transações já importadas antes apareçam marcadas como duplicadas e desmarcadas, para não lançar duas vezes.
35. Como João, quero ajustar a categoria e desmarcar linhas na prévia, para importar só o que está certo.
36. Como João, quero um resumo ao confirmar (X importadas, Y ignoradas), para saber o que aconteceu.
37. Como João, quero um erro legível se o arquivo for inválido ou não bater com o mapeamento, para não ficar com uma importação pela metade.

### Contas, categorias e regras (Configurações)

38. Como João, quero criar, renomear e mudar o tipo de uma conta (corrente, poupança, cartão, dinheiro), para refletir meus bancos reais.
39. Como João, quero ser impedido de excluir uma conta que tem transações, com a explicação do porquê, para não corromper o histórico.
40. Como João, quero excluir uma conta vazia, para limpar contas criadas por engano.
41. Como João, quero criar e editar categorias com nome, tipo, cor e fixo/variável, para organizar meus gastos do meu jeito.
42. Como João, quero excluir uma categoria e ver antes quantas transações ficarão sem categoria e que regras e orçamentos dela serão apagados, para decidir com informação.
43. Como João, quero criar regras do tipo "descrição contém X → categoria Y" ou por regex, com prioridade, para que importações futuras já venham categorizadas.
44. Como João, quero editar, reordenar por prioridade e excluir regras, para ajustar a categorização automática.
45. Como João, quero colar a chave do Gemini numa aba de Configurações, para ativar os resumos de notícias sem editar arquivos.
46. Como João, quero que a página de Notícias, sem chave configurada, me leve até essa aba, para saber o que falta.

### Metas e orçamentos

47. Como João, quero criar uma meta com nome, valor alvo, prazo opcional e notas, para acompanhar objetivos de poupança.
48. Como João, quero editar, arquivar e excluir metas, para manter a lista atual.
49. Como João, quero ver o progresso de cada meta (aportado / alvo, ritmo até o prazo), para saber se estou no caminho.
50. Como João, quero ver as metas arquivadas separadas, para não poluir a lista principal.
51. Como João, quero uma tabela com as categorias de despesa do mês escolhido, mostrando limite, gasto e barra de progresso, para controlar o orçamento.
52. Como João, quero editar o limite de uma categoria e que ele valha do mês escolhido em diante, para mudar o orçamento sem reescrever os meses passados.
53. Como João, quero remover o orçamento de uma categoria a partir de um mês, para parar de controlá-la.

### Release

54. Como João, quero gerar e instalar uma versão nova com um único comando, para atualizar o app sem passos manuais.
55. Como João, quero que a pasta `Banco/` contenha só o executável, para não confundir o app novo com o código antigo.
56. Como João, quero continuar desenvolvendo com `./start.sh` (Vite + Uvicorn com reload), para iterar rápido sem gerar o executável.

## Implementation Decisions

### Código do domínio

- O pacote de domínio do Banco (models, db/schema, repositories, services, importers OFX/CSV) passa a fazer parte do backend do HubPessoal, sob git. A UI PySide6 do Banco, os temas, o `settings.py` dele e o caminho fixo `BANCO_SRC_PATH` saem. O adaptador `banco_view` passa a importar o pacote local.
- O schema não muda. As semânticas de exclusão já definidas são o contrato: conta com transações → `RESTRICT` (a API responde 409 com a mensagem); categoria → transações ficam sem categoria (`SET NULL`), regras e orçamentos dela são apagados (`CASCADE`); excluir uma transação apaga o aporte de meta ligado a ela.
- O acesso ao `banco.db` deixa de ser somente leitura. Cada requisição de escrita abre uma conexão com `PRAGMA foreign_keys = ON` e roda dentro de uma transação SQLite (o context manager `transaction` do domínio).

### API (FastAPI, prefixo `/api/banco`, contratos novos)

- Transações: listagem com filtros `year`, `month`, `account_id`, `category_id`, `q` (busca na descrição), paginação; `GET/POST/PUT/DELETE` por id. O payload espelha o modelo `Transaction` (valores em centavos, datas ISO, `is_fixed_override` nullable) e inclui `goal_id` opcional para o aporte.
- Contas, categorias e regras: CRUD completo. Excluir uma categoria tem um endpoint de pré-visualização do impacto (contagem de transações, regras e orçamentos afetados).
- Metas: CRUD + arquivar. O progresso vem do `GoalService` existente.
- Orçamentos: listagem efetiva por mês (gasto + limite), definir limite a partir de um mês (`set_for_month`), remover a partir de um mês (`delete_for_month`).
- Importação em duas etapas, sem estado no servidor entre elas:
  - `preview`: recebe o arquivo, a conta e (para CSV) o mapeamento; devolve as linhas parseadas com `import_hash`, categoria sugerida (`RuleService`) e flag de duplicada.
  - `commit`: recebe as linhas escolhidas (com as categorias ajustadas) e grava numa única transação SQLite, ignorando por `import_hash` qualquer duplicada que ainda reste; devolve as contagens.
  - O mapeamento CSV usado é salvo por conta (`CsvMappingRepository`).
- Configurações: ler e gravar a chave do Gemini (a leitura devolve só se está configurada, nunca o valor) e informar a versão do app.
- Os endpoints de leitura existentes (`summary`, `trends`, `category-history` etc.) mantêm os contratos atuais.

### Configuração e bootstrap de dados

- Os caminhos seguem XDG: `banco.db` em `~/.local/share/banco/` (respeitando `BANCO_DB_PATH`), `hub.db` em `~/.local/share/hubpessoal/`, segredos em `~/.config/hubpessoal/.env` com permissão 600.
- Um módulo de bootstrap roda ao iniciar o app (executável e modo dev). Ele cria os diretórios, roda `init_db` e `seed_if_empty` no `banco.db`, copia o `hub.db` legado de `backend/` se o novo ainda não existir, e faz o backup diário (`banco-AAAA-MM-DD.db` em `~/.local/share/banco/backups/`, no máximo um por dia, mantendo os 14 mais recentes). A data atual é injetável para testes.
- No modo dev, o `.env` de `backend/` continua valendo como fallback para a chave do Gemini.

### Shell desktop sem servidor

- A janela é PySide6 + QtWebEngine com um esquema de URL próprio, `hub://`. O build de produção do React é servido a partir de `hub://app/`. Como o frontend já usa caminhos relativos `/api/...`, as chamadas chegam ao mesmo esquema.
- Uma ponte em Python, sem Qt, converte uma requisição (método, caminho+query, headers, corpo) numa chamada ASGI ao app FastAPI em memória e devolve status, headers e corpo. Nenhum socket ou porta é aberto. O handler Qt do esquema só adapta `QWebEngineUrlRequestJob` para essa ponte e roda as chamadas fora da thread da UI (a geração de digest pelo Gemini é lenta).
- Instância única via `QLocalServer`/`QLocalSocket`: uma segunda execução avisa a primeira, que traz a janela para a frente, e então sai.
- O perfil do QtWebEngine é persistente (para o `localStorage` do tema) e fica em `~/.local/share/hubpessoal/`.
- O modo dev continua com Vite (proxy `/api` → Uvicorn :8000) e `./start.sh`.

### Frontend

- A navegação passa a ser: Início · Finanças · Transações · Metas & Orçamentos · Notícias (IA e Finanças) · Configurações (abas: Contas, Categorias, Regras, Gemini, Sobre).
- Transações: lista com filtros (`MonthSelector` reaproveitado, conta, categoria, busca), botão "+ Nova", botão "Importar", e um painel lateral com o formulário (criar/editar/excluir com confirmação).
- Importar: escolher arquivo e conta → mapear colunas (só CSV sem mapeamento salvo) → tabela de prévia editável → confirmar → resumo.
- Metas & Orçamentos: seção de metas (cartões com progresso, ações, arquivadas recolhidas) e seção de orçamentos (tabela mensal editável).
- Os componentes visuais seguem o `DESIGN.md` (monocromático) e os componentes existentes (`Money`, `DateBR`, `MonthSelector`). Toda a interface, inclusive as telas atuais, é traduzida para português.
- Depois de qualquer escrita, as telas de finanças recarregam os dados.

### Empacotamento e release

- Um único comando, `./release.sh`, faz o build do frontend, congela o app com PyInstaller (onedir, sem console, incluindo o `dist` do React), monta o AppDir, gera `HubPessoal-x86_64.AppImage` com appimagetool em `Meus_Projetos/Banco/`, e instala o `.desktop` "Hub Pessoal" e os ícones em `~/.local/share`. O processo é o mesmo do `build_appimage.sh` + `install_desktop.sh` do Banco.
- O ícone é gerado por script: cifrão preto em fundo branco, em 64/128/256/512 px.
- A versão do app (semver, começando em 1.0.0) fica num único lugar e é exibida em Configurações.

### Migração e limpeza (última fatia, só depois do executável validado)

- Apagar todo o conteúdo de `Meus_Projetos/Banco/` exceto o novo AppImage. Isso inclui código, UI, testes, docs, `.venv` e `packaging`. Não há git lá, então não tem volta.
- Apagar a cópia antiga em `HubPessoal/backend/Banco/`.
- `~/.local/share/banco/` (banco.db e settings) não é tocado.

### Entrega

- Branch `executavel`, um commit por fatia. O João revisa e faz o merge na `main`.

## Testing Decisions

- Um bom teste exercita comportamento observável por um seam público (respostas HTTP, arquivos no disco, bytes devolvidos pela ponte) e nunca detalhes internos como funções do adaptador ou SQL específico.
- Seam 1, API HTTP via `TestClient`: cobre transações (CRUD, filtros, validação, aporte em meta), contas (incluindo o 409 na exclusão com transações), categorias (impacto da exclusão), regras, metas, orçamentos (vigência "a partir do mês"), importação (prévia com sugestão e duplicadas, commit, idempotência por `import_hash`, mapeamento CSV salvo, arquivo inválido) e chave do Gemini (gravada com permissão 600, nunca devolvida). Prior art: `backend/tests/conftest.py` e os `test_banco_*.py`, que criam um `banco.db` temporário a partir do `SCHEMA` e chamam o app real. As fixtures passam a gravar e o conftest precisa isolar também `hub.db` e o diretório de config.
- Seam 2, ponte `hub://` → ASGI: testes chamam a função da ponte com requisições sintéticas e verificam status, headers e corpo de rotas reais (GET com query, POST com JSON, 404, upload multipart para a prévia de importação) e a entrega de arquivos estáticos do build. Sem Qt nos testes.
- Seam 3, bootstrap de dados: com diretórios temporários e data injetada, verifica criação do schema + seed num banco inexistente, cópia do `hub.db` legado sem sobrescrever, um único backup por dia e rotação mantendo 14.
- Não há testes automatizados de frontend novos. Cada fatia de UI é verificada no navegador (modo dev) e o executável final é verificado manualmente: abrir, instância única, editar, importar, fechar.
- Os testes existentes de leitura continuam passando sem mudança de contrato.

## Out of Scope

- Transações recorrentes (modelos e geração mensal), embora o schema e o repositório existam.
- Auto-update, pacote `.deb`, distribuição para outras máquinas ou arquiteturas além de x86_64.
- Ícone na bandeja ou execução em segundo plano.
- Testes automatizados de frontend.
- Migração ou mudança do schema do `banco.db`.
- Sincronização na nuvem, múltiplos usuários, senha no app.
- Novas fontes de notícias ou mudanças na geração de digests.

## Further Notes

- O código do Banco não tem git. Por isso a absorção do pacote de domínio no HubPessoal é o primeiro commit, e a limpeza da pasta `Banco/` é o último passo, depois do executável validado.
- Ordem sugerida das fatias: (1) absorver o domínio + bootstrap de dados; (2) CRUD de transações + painel; (3) contas, categorias e regras; (4) importação; (5) metas e orçamentos; (6) chave do Gemini + tradução para português; (7) ponte `hub://` + shell PySide6; (8) ícone + `release.sh`; (9) limpeza.
- O modo aprendizado (João digitando o código) continua pausado neste trabalho.
