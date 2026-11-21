# 🗺 Roadmap do Taverna

> Este arquivo é a "memória" do projeto: o que já foi feito, o que vem agora e as ideias guardadas.
> Atualizado a cada versão.

**Versão atual: 1.0.0**

---

## ✅ Já feito

### Etapa 1 · A mesa (Mestre)
- Grid fixo: 1 quadrado = 1 metro. Mapa (imagem) redimensionável por cima.
- Tokens (jogador / criatura / NPC), tamanhos 1×1 até 4×4, snap liga/desliga.
- Camadas estilo Photoshop, com setinha pra ver o que tem dentro de cada uma.
- Salvar/abrir aventura (`.taverna`).

### Etapa 2 · Rede
- Mestre abre a taverna (porta **7777**), players entram pelo **Radmin VPN** (IP 26.x.x.x).
- Cada player só move o próprio token. O que está escondido não é enviado pros players.
- Reconexão automática. Script pra gerar `.exe`.

### Etapa 3 · Construir o mundo
- Telas iniciais com muro de pedra e tochas (Mestre e Player).
- Nova sessão pede **nome da aventura** e **tema** (medieval, moderno, futurista, mágico).
- **Terreno como tinta**: pincel redondo livre ou quadrado por quadrado, borracha, tamanhos `[` `]`.
- **Paredes em qualquer ângulo** (gruda no grid, Alt solta, Shift trava 15°). Ferramenta Sala.
- **Portas livres**: madeira, pedra, metal, mágica, mecânica · largura, espessura, dupla, abre pra dentro/fora.
- **Botão direito = menu** (parede, porta, terreno, token).
- Barra de construção vertical. Ícone próprio (T dourado) na janela, na barra de tarefas e no .exe.
- **36 chãos** (inclui lava/magma, gelo, neve, lama, pântano, cascalho, paralelepípedo, tapete, obsidiana,
  piso xadrez, piso hexagonal, ácido, pilha de ouro, concreto com sangue…), **17 paredes** (rocha de caverna,
  paliçada, gelo, obsidiana, metal enferrujado, ossos, sebe…) e **8 tipos de porta**
  (madeira, pedra, metal, mecânica, mágica, grade levadiça, **secreta** — parece parede pros players —, cortina).

### Etapa 4 · Mesa viva
- **Ctrl+Z / Ctrl+Y** (desfazer/refazer) em toda a construção: pinceladas, paredes, salas, portas
  (inclusive mudar e arrastar porta). Guarda as últimas 80 ações.
- **Portas animadas**: madeira/pedra/metal giram · mágica some e aparece · mecânica desliza pra dentro
  da parede · grade sobe · cortina se recolhe · secreta desliza pro lado. Animam pra todo mundo.
- **Movimento suave**: token arrastado por um player desliza na tela do mestre e dos outros.
- **Mouse dos outros**: setinha colorida com o nome de cada player e do Mestre.
  Dá pra esconder (Mestre: menu Exibir · Player: botão "Mouse dos outros").
- O mestre pode **esconder o próprio mouse** dos players (botão "Meu mouse visível" na barra de cima).

### Extras (v0.6)
- **Abas de cenário**: uma aventura pode ter vários cenários (caverna, floresta, castelo…), cada um numa aba.
  Só o mestre vê as abas. Ele escolhe qual está **ao vivo** (🔴) pros players com
  "📡 Mostrar esta aba pros jogadores". Dá pra editar uma aba enquanto os players estão em outra.
  Botão direito na aba: mostrar pros jogadores, renomear, duplicar, excluir. Arrastar reordena.
- **Zoom** sempre centrado no mouse e suave.
- **Portas sempre grudam**: na parede mais perto ou, sem parede, num dos 4 lados do quadrado do grid.
  Vale ao colocar e ao arrastar (Alt solta).
- **Seleção por arrasto** (modo Selecionar): pega tokens, portas, **paredes e pinceladas** de uma vez.
  Portas entram encostando na caixa. **Delete** apaga tudo. Ctrl+arrastar soma.
  Botão direito: "apagar só o terreno dentro da área".
- **Duas borrachas separadas**: borracha de terreno (`E`) e **borracha de paredes** (`Shift+E`),
  que apaga só o pedaço de parede por onde passa. As duas usam o tamanho do Pincel.

> ✅ **Etapa 4 concluída.**

### Etapa 5 · Visão
- **Cone de visão** em cada token de jogador: alcance (m), abertura (°) e pra onde está olhando
  (setinha na borda do token).
- **Paredes e portas fechadas bloqueiam** a visão. Vidro, campo de energia, gelo e grade levadiça deixam ver.
  Paredes duplas (duas salas encostadas) também abrem o vão certinho quando se coloca porta.
- **Névoa de guerra** (liga/desliga por aba, botão "🌫 Névoa de guerra"): o player só vê o que os tokens
  dele enxergam. O que já foi visto fica na **penumbra** (chão e paredes, sem criaturas).
- **Criaturas fora da visão nem são enviadas** pro player (não tem como espiar).
- **Mestre edita a visão** em Propriedades: alcance, abertura, direção e atalhos
  (Normal, Visão no escuro, Visão total 360°, Escuridão, Cegueira).
- **Girar**: o mestre libera/trava por token (ou "Liberar/Travar giro de todos" no menu Mesa).
  Player: `Q`/`E` giram 15°, `F` olha pro mouse. Mestre: `,` e `.` giram, `F` olha pro mouse.
- **Mostrar a visão dos jogadores** (menu Mesa): o mestre vê os cones de todo mundo na tela dele.

> ✅ **Etapa 5 concluída.**

### Etapa 5½ · Luzes
- **Fontes de luz** (ferramenta `L` na barra da esquerda): tocha, lampião, vela, fogueira, lâmpada,
  cristal brilhante e luz neon. Cada uma com luz forte, penumbra, cor e tremulação (chamas).
  Selecionada: edita em Propriedades. Duplo clique acende/apaga. Ficam na camada **Luzes**.
- A luz **para nas paredes** e **passa pelas portas abertas** (mesmo motor da visão):
  sala A com tocha clara, sala B escura; abriu a porta, a luz vaza pela passagem.
- **Luz ambiente por aba** (menu Mesa → 💡 Luz ambiente): ☀ Dia, 🌗 Penumbra, 🌑 Escuro total.
- **No escuro**, com névoa ligada, o player só vê o que está **no cone E iluminado**.
  **Visão no escuro** (campo novo no token) deixa enxergar alguns metros mesmo sem luz.
  Criaturas no escuro nem são enviadas pro player.
- Na tela do mestre a escuridão é só uma **prévia** (ele continua vendo tudo); dá pra desligar
  em Mesa → Luz ambiente → "Prévia da iluminação".

### Biblioteca (v0.9)
- **📚 Biblioteca** (botão na barra, `Ctrl+B`), no Mestre e no Player.
- **Compêndio (SRD 5.1, conteúdo livre)**: 334 monstros (só o mestre vê), 319 magias, condições, raças,
  classes, 407 habilidades de classe, equipamento, 362 itens mágicos, regras, perícias, atributos, idiomas,
  tipos de dano, escolas de magia, tendências. Busca por nome/tipo/escola/ND.
  Rótulos em português e distâncias em metros. Partes em pt-BR onde o projeto tem tradução
  (condições, raças, perícias, atributos, idiomas…); monstros, magias e itens no texto original em inglês.
  O mestre joga um monstro direto na mesa ("Colocar este monstro na mesa", já no tamanho certo).
- **Meus PDFs**: cada pessoa importa os **próprios** PDFs e lê dentro do Taverna (páginas, zoom, busca).
  Ficam **só no computador dela** — o Taverna **não envia** esses arquivos pela rede.
- Créditos e licenças em `LICENCAS.md`.
- v0.9.1: raças 100% em português (traços, sub-raças e tabela da ancestralidade dracônica com tradução
  própria). Busca no PDF estilo Ctrl+F: todas as ocorrências em amarelo, a atual em laranja,
  contador "3 de 12", Enter/F3 = próxima, Shift+Enter/Shift+F3 = anterior, Esc limpa.
- v0.9.2: **tradução do compêndio, parte 1**: nomes de TUDO em português (magias, monstros, itens,
  equipamento, habilidades, classes, subclasses, regras); campos das fichas traduzidos (tempo de conjuração,
  duração, escola, perícias, imunidades, idiomas, propriedades, peso em kg); 24 truques com texto completo.
  A busca aceita o nome em português ou em inglês, e a ficha mostra o nome original.
- v0.9.3: **Meus PDFs** com "📁 Adicionar pasta" (mostra todos os PDFs da pasta e subpastas; PDFs novos
  aparecem sozinhos; ⟳ atualiza), filtro por nome e arquivos avulsos separados.
  Corrigido: o destaque da busca caía no lugar errado em PDFs com página recortada/girada (livros diagramados).

### Tradução do compêndio — ❌ DESCARTADA (o compêndio saiu na v0.42; o que já foi traduzido fica)
Arquivos em `taverna/compendio/dados/pt-taverna/` (tradução própria do Taverna, a partir do SRD).
- [x] Nomes de tudo · campos curtos · raças · traços · truques (24)
- [ ] Magias 1º–9º nível (295)
- [ ] Condições já vieram em pt-BR · Habilidades de classe (407) · Classes/subclasses
- [ ] Equipamento (descrições) · Itens mágicos (362)
- [ ] Monstros (ações e traços dos 334)
- [ ] Regras (33 seções longas)

---

## 🔜 Próximas etapas (ordem combinada)

### Etapa 6 · Turnos, dados e painel de informações ✅ (v0.10)
**Combate** (painel COMBATE, à esquerda no Mestre):
- "⚔ Iniciar combate" → com os **selecionados**, com **selecionados + quem está na mesma área**
  (o que eles enxergam; paredes e portas fechadas separam) ou com **todos os visíveis**.
- Cada **jogador rola a própria iniciativa** (aparece um botão pra ele, com o modificador que ele guarda).
  "🎲 Rolar pras criaturas" rola as do mestre (escondido ou não). O mestre pode editar qualquer valor
  (duplo clique na tabela), colocar/tirar gente no meio do combate.
- "Começar ▶" / "Próximo turno ▶" (atalho **N**) e "◀" pra voltar. Contagem de rodadas.
- Token da vez ganha um **anel dourado**. No combate **só o token da vez se mexe/gira**;
  o servidor recusa o resto. O mestre sempre mexe em tudo. Jogador recebe "⚔ Sua vez!".
- Fora do combate: "jogadores podem mover" e "podem girar a visão" (liga/desliga).
- Criatura que o jogador não está vendo aparece como "???" na ordem dele.

**Dados** (painel DADOS, no Mestre e no Player):
- Expressões: `2d6+3`, `1d20+5-1d4`, `4d6kh3` (3 maiores), `2d20kh1` (vantagem), `2d20kl1`, `d%`.
- Botões d4…d100, Vantagem/Desvantagem (escreva só `+5` e clique no dado).
- Rolagem de **jogador é sempre pública**; do **mestre** pode ser **🔒 privada**.
- Quem rola de verdade é o computador do mestre (ninguém trapaceia). Histórico com 20/1 natural.

**Informações** (painel INFORMAÇÕES, ao lado de Propriedades no Mestre):
- PV atual/máximo (com dano/cura rápidos), condições (envenenado, sangrando, ferido, caído,
  queimando, molhado…), raça, classe, anotações.
- Cada campo tem um botão: 🔒 só mestre e dono · 👁 todos · 👤 só os jogadores escolhidos.
- Na mesa: **barra de PV** e **ícones das condições** em cima do token (pro mestre, o que está
  escondido aparece apagadinho). Passar o mouse mostra um resumo.
- Monstro colocado pela Biblioteca já vem com PV, tipo e CA/ND (tudo escondido).
- Player tem o painel INFORMAÇÕES com tudo do personagem dele + o que o mestre revelou dos outros.
- Salvo no arquivo da aventura.

v0.10.1:
- Painéis **COMBATE** e **DADOS** agora são **retráteis**: começam fechados e abrem pelos botões
  "⚔ Combate" (Ctrl+K) e "🎲 Dados" (Ctrl+D) na barra. No Player também "📋 Informações" (Ctrl+I).
- **Faixa de turnos** flutuando em cima da mesa durante o combate (ordem, de quem é a vez;
  o mestre passa a vez por ela; o jogador tem o botão "🎲 Rolar iniciativa" ali).
- Com o painel de dados fechado, as rolagens aparecem num **aviso no canto** que some sozinho.
- Duas anotações: **Anotações** (com cadeado 🔒/👁/👤) e **🔒 Notas secretas do mestre**
  (nunca saem do computador do mestre, nem pro dono). Monstro da Biblioteca guarda CA/ND nas secretas.

### Pacote de melhorias ✅ (v0.11)
- **Régua**: segure **M** e arraste (mestre e player). Mostra a distância em metros.
- **Distância ao arrastar** um token: linha tracejada com "X m" desde onde ele estava.
- **Quanto andou no turno**: no combate, o token da vez mostra uma linha amarela
  "andou X m" desde onde começou o turno (todo mundo vê).
- **Ping**: tecla **P** marca o ponto onde está o mouse, com ondas e o nome de quem pingou,
  pra todo mundo. Some em ~3 s.
- **Condições com duração**: clique direito numa condição no painel INFORMAÇÕES → 1, 2, 3, 5, 10
  rodadas ou outro valor. Aparece um numerozinho no ícone; quando acaba o turno daquele token,
  conta 1; chegou a zero, a condição sai sozinha (aviso na barra de status).
- **Salvamento automático** a cada 3 minutos (se mudou algo). Antes de salvar, guarda a versão
  anterior em "Nome (cópia de segurança).taverna". O arquivo é gravado num temporário e só depois
  trocado, então se a luz cair no meio o antigo fica inteiro. Aventura nunca salva vai pra
  "Nome (automático).taverna" na pasta de aventuras, e o "Continuar sessão" abre ela.
- Ainda pendente: **teste de verdade com os amigos** (Radmin).

### Histórico + limite de movimento ✅ (v0.12)
- **📜 Histórico** (Ctrl+H, só o mestre vê): entrou/saiu, moveu (quantos metros e quanto já andou
  no turno), rolou dados, pingou, e **tentativas recusadas** (fora da vez, além do deslocamento,
  com movimento travado). "[ver]" leva a câmera até o lugar. Filtro, "só ⚠" e salvar em .txt.
  O que o mestre faz não aparece pros jogadores.
- **Deslocamento** de cada token (painel INFORMAÇÕES → "Deslocam.", padrão 9 m; monstro da
  Biblioteca já vem com o do SRD). No combate, o jogador só anda até o deslocamento, contado
  **a partir de onde começou o turno** (círculo amarelo na mesa + "andou X de Y m").
  O arrasto não sai do círculo e o servidor confere.
- O mestre muda o deslocamento a qualquer hora (coluna "Desl." no COMBATE ou no INFORMAÇÕES),
  ex.: ferido → 4,5 m. "🏃 Disparada" dobra só no turno atual. Dá pra desligar o limite.
- O mestre não tem limite (mexe em tudo).

### Etapa 7 · Props (objetos de cenário) ✅ (v0.13)
- **📦 Objetos** (Ctrl+J): biblioteca com **49 objetos** desenhados pelo programa (vista de cima),
  em 5 categorias: Móveis (mesas, cadeira, banco, camas, penteadeira, guarda-roupa, estante, armário,
  sofá, tapete, balcão), Recipientes (baú, baú grande, caixote, barril, cacifo, saco, urna, cofre,
  caixão), Cenário (fogueira, poço, estátua, altar, pilar, árvore, pedra, rochedo, arbusto,
  escombros, túmulo, lápide), Luzes (lareira, lustre, poste, braseiro, candelabro, fogueira de
  acampamento) e Temáticos (computador, terminal, rack de servidor, carro, cápsula, cristal arcano,
  círculo mágico, caixa de suprimentos). Busca e filtro por categoria.
- Arraste pra mesa ou duplo clique. **"🖼 Importar imagem como objeto"** pra usar um PNG seu.
- Nova camada **Objetos** (entre Paredes e Luzes).
- Objeto pode **bloquear a visão** (pilar, estátua, estante, rochedo, rack…) — a névoa e a luz
  respeitam, igual parede. Objeto pode **iluminar** (lareira, lustre, poste…), acende/apaga.
- **Token carrega luz** (tocha, lanterna, vela, cristal, lâmpada): Propriedades do token →
  "Carrega luz". A luz anda junto.
- **Interativos** (✦): o mestre dá duplo clique → nome, tamanho, giro e o **conteúdo**
  (itens com nome, quantidade, descrição e imagem; ou "📚 Do compêndio" pra puxar um item do SRD).
  Opções: 🔒 trancado, precisa estar perto (1,5 m), jogadores podem pegar.
- **Jogador**: duplo clique no objeto ✦ → se estiver perto e destrancado, abre uma janela com o que
  tem dentro; "🎒 Pegar" leva o item pro **inventário** do personagem (aparece no INFORMAÇÕES).
  O conteúdo **nunca** vai pro jogador antes de ele abrir. Trancado/longe → aviso na tela.
- **Mestre mostra o conteúdo** (clique direito → "👁 Mostrar conteúdo para…" todos ou alguém).
- Tudo entra no **histórico** (abriu, pegou, tentou abrir trancado/longe). Salvo na aventura.
- Ideias pra depois: girar com atalho, mais objetos (por tema), árvore bloqueando só o tronco,
  objetos com estados (porta de armário aberta), armadilhas nos baús (etapa 9).

### Interações extras ✅ (v0.14)
- **Jogador move objetos** (empurrar a cama até a porta, levar um caixote…): objeto com
  "✋ Jogadores podem mover" (cama, mesa, cadeira, banco, sofá, baú, caixote, barril, saco, urna,
  caixa de suprimentos já vêm assim; o mestre liga/desliga). Precisa estar perto (1,5 m);
  cada empurrão leva até 1,5 m (ou mais, se continuar ao alcance). No combate, só na vez dele.
  O servidor confere e tudo vai pro histórico. (Subir em cima: é só pôr o token em cima do objeto.)
- **💀 Morto / ✚ Caído**: PV chega a 0 → criatura/NPC fica 💀 (token escurecido com caveira),
  jogador fica ✚ (cruz de ajuda). Curou → o caído levanta. O mestre muda pelo INFORMAÇÕES
  ("Estado") ou clique direito → Estado. Todo mundo vê. Morto é pulado no combate.
- **Saquear criaturas**: o inventário do token (mestre coloca itens com "＋ Item" no INFORMAÇÕES)
  pode ser revistado por um jogador perto quando a criatura está caída ou morta (duplo clique):
  abre a mesma janela do baú e "🎒 Pegar" leva pro inventário dele. Vai pro histórico.

### Etapa 8 · Fichas e inventário (D&D 5e) ✅ (v0.15)
- **📜 Ficha D&D 5e dentro do programa** (abas Principal · Ataques e magias · Inventário · Personagem):
  atributos, salvaguardas, 18 perícias (proficiência e especialização), CA, iniciativa, deslocamento,
  PV/temporários, dados de vida, testes contra a morte, ataques, magias (do compêndio ou livres) com
  CD/ataque mágico e espaços por nível, moedas, inventário, idiomas, características, personalidade,
  aparência, história e anotações. Raça, classe e antecedente com a lista do compêndio.
- **Contas automáticas**: modificadores, bônus de proficiência pelo nível, perícias, salvaguardas,
  percepção passiva, iniciativa, CD e ataque de magia (atributo de conjuração pela classe).
- **Integrada ao token**: PV, deslocamento, raça, classe e inventário são os mesmos do INFORMAÇÕES
  (dano do mestre, item pego do baú/criatura aparecem na ficha, e vice-versa).
- **Quem vê**: o jogador vê/edita a dele ("📜 Minha ficha", Ctrl+P); o mestre vê/edita todas
  (clique direito no token → "📜 Ficha…" ou botão no INFORMAÇÕES). Os outros jogadores não recebem
  nada da ficha. Só é enviada quando muda. Salvar vai pro histórico do mestre.
- **PDF**: 📥 importar uma ficha preenchível (lê os campos da ficha oficial: nome, classe/nível,
  raça, atributos, CA, PV, deslocamento em pés→m, perícias proficientes, ataques, equipamento→inventário,
  moedas…); 📤 exportar no modelo do Taverna; 📄 preencher a ficha oficial (a pessoa escolhe o PDF
  em branco que já tem; o Taverna não distribui o arquivo da Wizards).
- **Monstros**: token vindo da Biblioteca → clique direito "📖 Ficha do SRD"; qualquer criatura
  também pode ter a ficha completa (monstros criados pelo mestre).
- v0.15.1: **aba "📄 Ficha do D&D"**: cada pessoa escolhe uma vez o PDF da ficha oficial preenchível
  que ELA baixou (fica guardado só no computador dela, nunca vai pela rede); a aba mostra a ficha
  oficial preenchida e acompanha a edição. "📤 Exportar ficha do D&D" salva o PDF oficial preenchido.
  O modelo do Taverna continua como opção. (A ficha oficial não faz parte do SRD, então o Taverna
  não vem com ela embutida.)
  Ideia pra depois: clicar num campo da ficha oficial e editar ali mesmo.
- Obs.: testado com campos no padrão da ficha oficial; se a sua ficha tiver nomes de campo diferentes,
  me mande o nome dos campos que eu ajusto.

### Etapa 9 · Gatilhos e armadilhas ✅ (v0.16)
- **Armadilha num objeto**: clique direito → "⚡ Armadilha / gatilho…". Dispara quando um jogador
  ABRE/mexe (mesmo trancado, se estiver perto) ou quando ele MOVE o objeto.
- **Área no chão** (placa de pressão, alçapão, runa): clique direito no chão → "⚡ Criar área de
  armadilha aqui". Dispara quando o token de um jogador ENTRA. Tracejado vermelho que **só o mestre vê**.
  Clique direito → Tamanho…, Desarmar/Rearmar, Disparar agora.
- **Ações** (em ordem): 💬 mensagem (pra quem disparou ou pra todos), 🩸 dano rolado (ex.: 1d4+1,
  rolagem pública) + condição com duração no token de quem disparou (PV 0 → ✚), 🚪 abrir/fechar
  portas, 💡 apagar/acender luzes (escolhidas ou todas), 👁 fazer aparecer monstros/objetos
  escondidos, 🙈 esconder, 🌑 mudar a luz ambiente, 📍 ping no lugar.
- Uma vez só ou sempre · armada/desarmada · "Rearmar". O mestre é avisado (aviso no canto + barra +
  janela piscando) e fica no histórico. Os jogadores **não recebem nada** das armadilhas.
- Ideias pra depois: teste de resistência (CD) antes do dano, "Percepção revela a armadilha",
  tocar som (quando tiver a mesa de áudio), porta que tranca (quando jogador abrir porta).

### Documentos legíveis ✅ (v0.16)
- Item pode ser **📜 documento** (bilhete, carta, mapa, página de diário): texto (com **negrito**,
  *itálico*, # título) e/ou **imagem** (até 1400 px). "👁 Ver como o jogador".
- **Solto no cenário**: categoria "Documentos" nos Objetos (pergaminho, carta, livro aberto, bilhete).
  O jogador perto dá duplo clique → abre direto pra ler, num papel; "🎒 Pegar" tira do chão e leva
  pro inventário.
- **Dentro de baús/criaturas**: botão "📖 Ler" no item. **No inventário** (ficha): "📖 Ler" pra reler.

### Portas e janelas pelos jogadores ✅ (v0.16.1)
- O **jogador abre/fecha portas e janelas** com duplo clique, se estiver perto (1,5 m); no combate,
  só na vez dele. Vai pro histórico (abriu/fechou, ⚠ trancada, longe…).
- O mestre decide em cada porta: **"Jogadores podem abrir/fechar"** (porta secreta já vem desligada)
  e **🔒 Trancada** (o jogador recebe "Está trancada" — ele não sabe antes de tentar). Painel de
  propriedades ou clique direito na porta.
- **Janelas** (novos tipos de porta): **janela de vidro** (dá pra ver através mesmo fechada) e
  **janela com persiana** (fechada bloqueia a visão). Abrem igual porta.

### Itens-chave ✅ (v0.16.2)
- Porta, janela, baú ou cofre podem ter uma **🗝 Chave**: o nome de um item. Se o jogador tiver um
  item com esse nome no inventário (sem diferença de maiúscula/acento), a coisa **destranca e abre**
  na hora: "🗝 Você destrancou … com …". Vai pro histórico.
- **"A chave some ao usar"**: opcional, a chave é gasta.
- Porta pode ter **nome** ("Porta armadilha") pra aparecer no histórico e nas armadilhas.
- Atalho: clique direito na porta/baú → **"🗝 Criar chave pra esta porta…"**: liga a chave, tranca
  e já coloca o item no chão ao lado, pro mestre arrastar e esconder.
- Nova categoria **Itens soltos** nos Objetos (chave, poção, moedas, saquinho): o jogador perto dá
  duplo clique e pega.
- Armadilha ganhou a ação **"Fechar e TRANCAR"** (e "Destrancar"): mexeu no baú → a porta bate e tranca.
- O nome da chave **não vai** pro computador do jogador (não dá pra "colar").

### Etapa 10 · Atmosfera ✅ (v0.17.0)
Tudo fica no painel **🌦 Atmosfera** (Ctrl+T), com duas abas.

**✨ Efeitos e clima**
- **Áreas de efeito / templates**: círculo (raio), quadrado, cone e linha, **animados**: 🔥 fogo, ❄ gelo,
  ☠ veneno, 🧪 ácido, 💧 água, ⚡ elétrico, 🌑 escuridão mágica, 💨 fumaça, ✨ luz mágica, ☀ radiante,
  🕸 teia, 🌿 vinhas, 🔮 só a área. Clique = tamanho do painel; clicar e arrastar = direção e tamanho
  (de 1,5 em 1,5 m). Shift = ângulo livre, Alt = mantém o tamanho, Esc sai.
- **Escuridão e fumaça bloqueiam a visão** dos jogadores; **fogo, luz, radiante e raio iluminam**.
- Mestre: duplo clique edita, botão direito troca/gira/apaga; "✨ Área de efeito aqui" no clique direito do mapa.
- **Jogadores colocam o template da magia deles** (vai pro histórico, com o nome de quem pôs; máx. 12 cada)
  e apagam os seus. O mestre pode desligar.
- **Efeito em token e objeto** (clique direito → ✨ Efeito): em chamas (ilumina!), molhado, congelado,
  envenenado, ácido, eletrizado, brilhando, preso na teia, enroscado.
- **Clima** por cenário: chuva, tempestade (com relâmpagos), neve, neblina, cinzas e brasas,
  tempestade de areia, folhas ao vento — força 1 a 3. Botão **⚡ Raio** = clarão na tela de todos.
  Cada um pode esconder o clima da própria tela.
- **✏ Lápis**: mestre e jogadores rabiscam por cima do mapa (8 cores, 3 espessuras). "Some sozinho
  (10 s)" pra apontar coisas, ou fixo (salvo na aventura). O mestre pode desligar o lápis dos jogadores.

**🎵 Som e música**
- **Efeitos sonoros**: o mestre importa os sons DELE (mp3, ogg, wav…), toca **pra todos** ou **só pra ele**,
  com volume por som. **🔁 Ambiente** = repete até parar (e quem entra depois também ouve).
  O arquivo vai uma vez pra cada jogador.
- **Música do YouTube**: o mestre cola links numa **fila** e controla tocar/pausar/próxima/parar
  (repete a fila se quiser). Todo mundo vê o **player oficial do YouTube**, seguindo o do mestre.
  Vídeo que o dono não deixa tocar fora do YouTube é pulado sozinho.
- Jogador: painel **🎵 Som** (Ctrl+M) com o player e volumes separados (música / efeitos / silenciar).
- A música precisa do componente **PyQt6-WebEngine**: rode `instalar_musica.bat` uma vez
  (sem ele o resto funciona, e aparece um botão pra abrir a música no navegador).

### Ajustes ✅ (v0.17.1)
- Os **divisores entre os painéis** (os pontinhos "……") agora redimensionam de verdade: os painéis
  ganharam rolagem própria, então dá pra deixar Camadas maior e Propriedades menor (e vice-versa).
- Decidido: **música continua pelo player do YouTube + mesa de áudio** (sem playlist de arquivos).
- Os avisos internos do player do YouTube ("web-share", "postMessage", "WebGPU") não aparecem mais
  na janela preta — não eram erros do Taverna.

### Mini player ✅ (v0.17.2)
- No jogador, o vídeo da música não ocupa mais a lateral: vira um **mini player no canto da mesa**
  (aparece quando o mestre dá play e some quando ele para). Botões: ⇲ trocar de canto · ⤢ maior/menor.
  Não dá pra esconder de vez: o YouTube exige o player oficial visível (mín. ~200 px de altura).
- O painel 🎵 Som (Ctrl+M) do jogador ficou só com os volumes.

### Etapa 11 · Projetor ✅ (v0.18.0)
- Painel **📽 Projetor** (Ctrl+P no mestre): galeria de imagens da aventura (**fica salva no .taverna** —
  dá pra preparar antes da sessão). ➕ Imagem do PC, 📋 Colar (imagem copiada), legenda, 🗑.
- **Pra quem**: todos ou só alguns jogadores (ex.: a carta que só um personagem recebeu).
- **📽 Projetar** (ou duplo clique) e **⏹ Recolher**. Fica no histórico.
- Botão direito num **token com imagem** → "Projetar o retrato"; num **objeto com documento com imagem**
  → "Projetar a imagem de …".
- Imagem grande é reduzida (máx. 1920 px) antes de mandar.
- **Jogador**: a imagem aparece no meio da mesa (com legenda e efeito de surgir), **🔍 Ampliar** abre
  com zoom, **✕** fecha. Tudo que recebeu fica em **📽 Imagens** pra rever depois.

### Etapa 12 · Baú com recompensa aleatória ✅ (v0.19.0)
- Em qualquer objeto interativo (baú, cofre, barril…): **Editar objeto → 🎲 Recompensa aleatória**.
- **Tudo configurável**: chance de vir vazio (%), moedas (nenhuma · poucas · médias · muitas · tesouro ·
  **personalizado** com dados por moeda, ex.: PO 2d6), **quantidade de itens (de X a Y)**,
  raridade máxima (comum → lendária) e o que pode vir: comida, bugigangas, equipamento, armas,
  armaduras, poções, itens mágicos e **📝 meus itens** (lista própria: `Amuleto`, `Flecha ×5`,
  `Carta | Selada com cera`).
- **O primeiro jogador que abrir** dispara o sorteio; depois o baú fica com aquilo (os outros veem o que
  sobrou). Se vier nada, aparece uma frase ("Só poeira e teias de aranha.").
- Histórico do mestre mostra quem abriu e o que saiu. 🎲 no canto do baú (só o mestre vê; ✓ depois de sorteado).
- **🎲 Testar um sorteio** (exemplo sem mudar nada) e **↺ Sortear de novo** (reseta).
- Itens do SRD 5.1 (equipamentos e itens mágicos, nomes em português) + comidas e bugigangas do Taverna.
  "Arma +1" vira uma arma de verdade (ex.: "Espada Longa +1").

### Tabelas de sorteio personalizadas ✅ (v0.19.1) — pra qualquer sistema
- No baú: **"Itens de"** → 🐉 D&D 5e (padrão) **ou uma tabela sua** (ex.: "Ordem Paranormal — Armas").
- **📋 Tabelas…** abre o gerenciador: ＋ Nova, ⧉ Duplicar, 🗑, e o editor com **Item · Quantidade ·
  Chance · Descrição**. Quantidade aceita dados (`2d10`); chance: comum · incomum · raro · muito raro.
- **Dinheiro com nome livre** (R$, Créditos… ou nenhum) e quantia em dados (`2d6+10`).
- **📋 Colar lista…**: cola a tabela do livro (copiada no leitor de PDF do Taverna), um item por linha:
  `Munição ×2d10`, `Fuzil de assalto [raro]`, `Kit médico | Recupera 2d8 PV`. **🎲 Testar** mostra exemplos.
- Cada tabela é um arquivo em **Documentos/Taverna/Tabelas de sorteio** — vale pra todas as aventuras e dá
  pra mandar pros amigos. O baú guarda **uma cópia** da tabela (a aventura abre igual em outro PC).

### Etapa 13 · Banco de imagens + removedor de fundo básico ✅ (v0.20.0)
- **🖼 Banco de imagens** (aba no painel 📦 Objetos, Ctrl+J · ou Exibir → Banco de imagens): vale pra
  **todas as aventuras**. Fica em **Documentos/Taverna/Banco de imagens**, com pastas Mapas, Tokens,
  Objetos, Projetor, Outros (e as que você criar).
- ➕ Importar várias de uma vez, ou **arrastar do Windows** (até uma pasta inteira). Busca por nome.
- **Duplo clique ou arrastar pra mesa**: na pasta Mapas vira mapa, Tokens vira token, Objetos vira objeto,
  Projetor vai pra galeria do projetor (pastas novas perguntam). Botão direito: pôr como qualquer um,
  ✂ remover fundo, renomear, mover de pasta, apagar.
- Botão direito na mesa: **"🖼 Guardar a imagem no banco"** (token, objeto, mapa).
- **✂ Removedor de fundo básico**: 🪄 Automático (cor das bordas) · 🎯 clicar numa cor (só a parte ligada
  ao clique, ou a cor na imagem toda) · 🧽 borracha · tolerância · suavizar borda · desfazer · original.
  No banco salva uma cópia "(sem fundo)"; num objeto da mesa troca a imagem dele.
  (O **removedor com IA** fica pro acabamento, com o Fable.)
- Novo componente: **numpy** (o `iniciar_*.bat` instala sozinho). Corrigido o `iniciar_player.bat`.

### Etapa 14 · Ficha em PDF de qualquer sistema ✅ (v0.21.0)
- Jogador: botão **📄 Ficha PDF** na barra · Mestre: **Biblioteca → 📄 Fichas em PDF**.
- **➕ Importar ficha**: copia o PDF pra **Documentos/Taverna/Fichas** (o original fica intacto) e abre.
- O editor mostra as páginas e põe os **campos por cima**: clicar e digitar, marcar caixinhas,
  escolher opção/lista. Campo repetido (mesmo nome em várias páginas) atualiza junto.
- **Salva sozinho** (a cada 30 s e ao fechar) · 💾 Ctrl+S · **📤 Exportar cópia** · zoom.
- O PDF salvo abre preenchido em qualquer leitor (Acrobat, navegador…).
- PDF sem campos (não editável) abre só pra leitura, com aviso.
- O Taverna **não interpreta** a ficha (é neutro) — só deixa preencher. Fica só no PC de quem preencheu.

- (v0.21.1) **Versão do protocolo de rede atualizada (3)**: Player de versão antiga é recusado com aviso
  claro ("peça pro mestre o Taverna Player 0.21.1"). **Mande o .exe novo pros amigos.**

### Chat, rolagens prontas e diário ✅ (v0.22.0)
- **💬 Chat** (aba no painel "💬 Chat", Ctrl+D — junto dos dados): mensagem pra todos ou **🤫 sussurro**
  pra uma pessoa (o mestre vê todos os sussurros). O mestre pode **falar como um NPC** ("como: Duquesa").
  Rolagens aparecem no chat; `/r 1d20+5` rola pelo chat. Quem entra depois recebe as últimas mensagens
  que podia ver. Com o painel fechado, aparece um aviso no canto da mesa. `**negrito**` e `*itálico*`.
- **⚡ Rolagens prontas** (aba 🎲 Dados): **cada um cria as suas** — "＋ Salvar rolagem" (nome + dados,
  ex.: "Ataque com espada" = 1d20+5). Vira botão; clicou, rolou (com o nome no chat). Botão direito:
  editar, mover, apagar. Ficam salvas no PC de cada um. (Não lê a ficha — decisão do Manel.)
- **📓 Diário da campanha** (mestre: Sessão → Diário, Ctrl+Shift+D · jogador: 📓 Diário):
  entradas por tipo (📅 Sessão com modelo pronto, 👤 NPC, 🏰 Lugar, 📜 Missão, 📝 Nota), busca e filtro,
  formatação simples, aba "Ver como fica". Cada entrada é 🔒 só do mestre ou 👁 compartilhada.
  Fica salvo na aventura. **Jogador** lê o que foi compartilhado (com aviso quando muda) e tem
  **"Minhas anotações"**, só dele.
- Jogador: botão **📜 Ficha** com setinha (D&D / Ficha em PDF). Protocolo de rede 4 (mande o .exe novo).

### Etapa 15 · ACABAMENTO (com o Fable) — plano combinado em 16/11
Ordem: **1) temas + tela inicial ✅ · 2) retratos estilo Baldur's Gate · 3) efeitos refeitos + lava +
clima melhor + efeitos de impacto (explosão, raio, tremor…) + otimização · 4) dados 3D ·
5) removedor de fundo com IA (opcional, instalar_ia.bat) · 6) tradução do compêndio (em lotes)**

#### Bloco 1 · Temas, tela inicial e opção de gráficos ✅ (v0.23.0)
- **7 temas**: Medieval, Moderno, Futurista, Mágico + os novos **Terror**, **Claro** e **Escuro**.
  Cada um com paleta, fonte de título, cantos (reto no futurista, redondo no mágico…), segunda cor,
  degradês nos painéis/botões e detalhes próprios. Painéis flutuantes, compêndio, chat e listas
  acompanham o tema (inclusive no claro).
- **Tela inicial com um cenário animado por tema**: muro com tochas e brasas (medieval), cidade na chuva
  (moderno), grade de neon e sol de faixas (futurista), círculo arcano girando (mágico), lua, árvores
  mortas, névoa, olhos no escuro e luz falhando (terror), pergaminho com rosa dos ventos (claro),
  ardósia com luzes lentas (escuro). Seletor de **🎨 tema** na própria tela (preferência do PC;
  dentro da aventura vale o tema que o mestre escolheu pra ela).
- **✨ Gráficos: Baixo / Médio / Alto** — cada pessoa escolhe (tela inicial; Mestre: Exibir → Gráficos;
  Player: botão ⚙). Baixo = cenário parado e efeitos simples; Alto = tudo. Também ali: desligar
  "tela tremer" e "tela clarear" (vão ser usados nos efeitos de impacto do bloco 3).

#### Gráficos da mesa, parte 1 ✅ (v0.24.0) — pedido do Manel: "mais detalhado, com cara de 3D"
- **Corrigido o crash** ao clicar numa área de efeito (o painel Propriedades não conhecia esse item).
- **Rede de segurança**: erro inesperado não fecha mais o programa — avisa na barra de status e grava em
  `Documentos/Taverna/erros.log`.
- **Chão com relevo**: todas as texturas ganham volume (juntas afundam, pedras/tábuas saltam, luz de
  cima-esquerda) + manchas grandes de claro/escuro que quebram a repetição.
- **Paredes com altura**: face lateral aparente, quina iluminada/sombreada, sombra projetada macia e o
  chão escurecendo perto da parede.
- **Luz**: queda suave, cor quente somando no chão e nas paredes, miolo claro perto da fonte e penumbra
  na borda das sombras (Alto).
- Tudo obedece **Gráficos Baixo/Médio/Alto** (Baixo = como era antes, leve). Trocar a opção atualiza na hora.
- FALTA (pedido): áreas de efeito refeitas + lava, atmosfera/clima, efeitos de impacto (explosão, raio,
  tremor), objetos e tokens com volume, tela inicial e interface ainda mais ricas.

#### Gráficos da mesa, parte 2 ✅ (v0.25.0) — efeitos, clima e impactos
- **Todas as áreas de efeito refeitas**, em camadas: fogo (labaredas com miolo, brasas, fumaça), gelo
  (rachaduras com profundidade, cristais, geada na borda, reflexo), água (reflexos ondulando, espuma),
  veneno/ácido (gás girando, bolhas que estouram, chiado), elétrico (raios com galhos), escuridão (véus
  girando), fumaça, luz/radiante (feixes girando, anéis), teia (com gotinhas), vinhas (com folhas e capim),
  magia (círculo rúnico). **Nova: 🌋 Lava** (crosta boiando, veios quentes, bolhas; ilumina).
- **Clima**: chuva com profundidade (pingos de longe/perto), respingos no chão e névoa; tempestade com o
  **raio desenhado** no céu; neve com flocos grandes na frente.
- **💥 Efeitos rápidos do mestre** (aba Atmosfera, ou botão direito no mapa → "Efeito rápido aqui"):
  no mapa — explosão, raio, onda de choque, clarão arcano, desabamento; na tela — tremor, clarão, apagão.
  **Explosão treme a tela, raio clareia.** Independentes do clima. Tamanho ajustável.
  Também é **ação de armadilha** ("💥 Efeito de impacto").
- Tudo com **Baixo/Médio/Alto** (menos partículas e animação "aos pulinhos" no Baixo). Cada pessoa pode
  desligar "tela tremer" e "tela clarear" em Gráficos.
- Protocolo de rede 5 (mande o .exe novo).
- (v0.25.1) **🔊 Sons dos efeitos…** (aba Atmosfera → Efeitos rápidos): um som pra cada efeito rápido
  (da lista de Efeitos sonoros ou um arquivo novo), com volume e ▶ pra ouvir. Toca pra todo mundo quando o
  efeito dispara — botão, botão direito no mapa ou armadilha. Fica salvo no PC do mestre.
- FALTA: objetos e tokens com volume; interface/tela inicial mais ricas; retratos; dados 3D; removedor IA;
  otimização medida; tradução.

#### Gráficos, parte 3 ✅ (v0.26.0) — objetos, tokens e tela inicial com volume
- **Objetos**: cada objeto ganha relevo, quina clara/escura no contorno e **sombra macia projetada** (cai
  sempre pro mesmo lado, mesmo girado). Vale pros do catálogo e pros de imagem. Calculado uma vez e
  guardado (cache) — colar a imagem pronta é mais leve que redesenhar.
- **Tokens** viram "peças": sombra no chão, espessura da ficha, anel de metal com luz/sombra, miolo
  abaulado e reflexo de vidro (Alto).
- **Tela inicial**: título TAVERNA em relevo (metal com espessura e sombra; neon com halo nos temas
  futurista/mágico/terror; brilho que passa pelas letras), **moldura com cantoneiras** atrás do menu,
  enfeite ——◆—— e **tochas de parede com chama viva** no medieval.
- Tudo respeita Baixo/Médio/Alto (Baixo = desenho antigo, leve).
- (v0.26.1) **Fonte própria por tema** (embutidas, licença aberta OFL — ver LICENCAS.md): Medieval =
  MedievalSharp · Terror = Pirata One (gótica) · Futurista = Orbitron (cyberpunk) · Moderno = Bebas Neue
  (industrial) · Mágico = Cinzel Decorative · Claro e Escuro = fontes padrão do sistema. Vale no título,
  nos botões da tela inicial e nos títulos dos painéis.
- PEDIDO (16/11, "vamos mexendo com o tempo"): **interface de dentro do programa** mais bonita, detalhada
  e bem distribuída; **trocar os emojis por ícones próprios** desenhados pelo programa.
- FALTA: retratos estilo Baldur's Gate; dados 3D; removedor de fundo com IA; otimização medida; tradução.

#### Pacote de desenvolvimento (sem mudar o programa)
- Pasta `testes/` agora vem junto: 25 testes automáticos + `rodar_testes.py` (roda todos de uma vez).
- `CLAUDE.md` na raiz: regras do projeto, decisões e o que falta, para qualquer sessão nova começar sabendo.

#### Interface, 1ª passada ✅ (v0.27.0)
- **Ícones próprios** (40 desenhados pelo programa, `ui/icones.py`), na cor do tema: texto no normal,
  destaque quando ligado/com o mouse. Trocam de cor junto com o tema.
- **Barras de ferramentas** (Mestre e Player): ícone em cima + nome embaixo, sem emoji, em grupos;
  no Mestre "Meu mouse" e **Abrir taverna** (em destaque) ficam à direita; no Player, Gráficos e Sair.
- **Cabeçalho dos painéis**: faixa de destaque, ícone, nome na fonte do tema, filete com losango e
  botão de fechar. Abas (Chat/Dados, Objetos/Banco, Efeitos/Som) com ícone.
- AINDA COM EMOJI (próximas passadas): títulos de seção dentro dos painéis, lista de camadas, botões
  internos, menus de botão direito, diálogos. Também falta redistribuir o conteúdo de cada painel.

#### Interface, 2ª passada ✅ (v0.28.0) — emojis → ícones
- **Fonte do Terror** (decisão do Manel): a gótica (Pirata One) fica só nos títulos grandes (tela inicial);
  cabeçalhos de painel e títulos de seção usam Constantia. Cada tema tem agora `fonte_painel` em `temas.py`.
- **57 ícones novos** em `ui/icones.py` (88 no total): cadeado, lixeira, salvar, chave, mochila, caveira,
  aviso, lápis, tesoura, pasta, alto-falante, lupa, exportar/importar, explosão, ao vivo, sussurro, monstro,
  escudo, calendário, castelo, frasco, teia, lua, cone, pedra, tremor…
- **Conversor automático** (`ui/acabamento.py`): o código continua escrito com emoji ("🔒 Trancar"), e na
  hora de mostrar o emoji do começo vira o ícone do tema (tabela `EMOJI_ICONE`). Vale para botões, menus
  (inclusive os de botão direito), abas, caixas de opção, lista de camadas, listas da biblioteca, do diário
  e das fichas em PDF. Títulos de seção e de janela só perdem o emoji. Os ícones trocam de cor com o tema.
  Pra usar em código novo: `iconizar(self)` no fim do `__init__` de janela/painel, `iconizar_menu(menu)`
  antes do `exec()`, e `com_icone` / `item_com_icone` / `adicionar_item` quando o texto muda depois.
- Lista de camadas com ícone por tipo (mapa, terreno, paredes, luzes, criaturas, jogadores…); marcas de
  objeto viraram texto ("· interativo, trancado, armadilha"). Lista de jogadores com bolinha verde/vazia.
  Aba ao vivo com o ícone de transmissão na cor de perigo do tema. Botão de "quem vê" (🔒/👁/👤) no
  INFORMAÇÕES agora segue o tema (antes era marrom fixo).
- CONTINUAM com emoji (de propósito): mensagens do chat, histórico, barra de status e avisos na mesa,
  ícones das condições em cima dos tokens, tela inicial. Símbolos de texto (▶ ◀ ● ✔ →) ficam.
- FALTA (3ª passada): redistribuir Atmosfera, Informações e Combate; algumas janelas ainda têm cores
  fixas marrons (janela do baú/conteúdo) que não seguem o tema claro.

#### Interface, 3ª passada ✅ (v0.29.0) — painéis redistribuídos
- Decisão do Manel: **seções que abrem/fecham** (clique no título) em vez de sub-abas. Cada seção tem
  setinha, ícone, nome na fonte do tema e um resumo apagado no fim (ex.: "Chuva", "2 ativas", "9 m").
  O Taverna lembra, por PC, quais ficaram abertas. Peça reaproveitável: `Secao` em `ui/acabamento.py`.
- **Atmosfera**: Clima · Efeitos rápidos · Área de efeito (ou Template de magia, no jogador) · Lápis
  (fechada) · Jogadores podem… (fechada, só mestre). A aba **Som e música não fecha** de propósito: o
  player do YouTube tem que ficar visível.
- **Combate** (decisão do Manel: passar a vez em cima): Iniciar/Encerrar → situação ("Rodada 2 · vez
  de…") → ◀ / Próximo turno ▶ → ordem → rolar pras criaturas → ＋ Selecionados / Tirar / Disparada →
  seção fechada "Regras de movimento" (limitar ao deslocamento, mover fora do combate, girar a visão).
- **Informações**: sempre à vista nome, ficha, PV, dano/cura e estado; depois as seções Condições ·
  Deslocamento, raça e classe · Anotações · Inventário · Notas secretas (fechada). O botão "quem vê" de
  cada bloco fica dentro da seção. O botão de condição marcado agora usa a cor do tema (era marrom fixo).
- Os botões de **condição continuam com emoji** (iguais ao ícone em cima do token) até ganharem desenho.
- IDEIAS: desenhar ícones próprios das 22 condições (painel + token); tirar as cores fixas da janela do
  baú/conteúdo e do aviso de rolagem.

#### Interface, fechamento ✅ (v0.29.1)
- **22 ícones de condição** desenhados (`cond_<chave>` em `ui/icones.py`): frasco borbulhando
  (envenenado), gotas (sangrando), curativo, "Zz", seta pro chão, punho, corrente, espiral, raio no
  círculo, proibido, pedra, rosto assustado, coração, olho riscado, orelha riscada, fantasma tracejado,
  bateria fraca, chama, gota, floco, foco e auréola. Usados **em cima do token** (nítidos com zoom), nos
  botões do INFORMAÇÕES e na lista de condições da armadilha. A **caveira do token morto** também virou
  desenho. As dicas do token e o cartão do jogador mostram só o nome da condição.
- **Cores do tema** onde ainda era marrom fixo: cartões da janela do baú/criatura, faixa de iniciativa
  em cima da mesa, linha da vez no combate do jogador, textos apagados do INFORMAÇÕES e do aviso de
  rolagem. Faixa de iniciativa e tabela do combate se redesenham quando o tema muda.
- Lista de iniciativa (mestre e jogador) com ícone por tipo: escudo (jogador), monstro (criatura),
  pessoa (NPC).
- Ficam de propósito com visual próprio: o "papel" dos documentos (janela de leitura) e o aviso
  "Sua vez" em cima da mesa.
- ✅ Item 1 da fase de acabamento (interface) concluído.

#### Objetos de cada tema ✅ (v0.30.0) — sugestão do Manel
- **50 objetos novos**, 10 por ambientação (Claro e Escuro são só estilo, usam todos), em
  `mesa/props_temas.py`. Catálogo agora com **107 objetos**.
  - **Medieval**: trono, forja (ilumina), bigorna, carroça, tenda (bloqueia), mesa de banquete,
    estandarte, suporte de armas, fardo de feno, tocheiro (ilumina).
  - **Moderno**: geladeira, fogão, pia, vaso sanitário, banheira, TV (brilho de tela), escrivaninha, moto,
    caçamba de lixo, máquina de lanches.
  - **Futurista**: mesa holográfica, robô, drone, console de controle, reator, tubo de estase, nave
    pequena, contêiner, plataforma de teleporte, torreta.
  - **Mágico**: caldeirão, mesa de alquimia, pedestal com orbe, estante de grimórios, portal, pedra rúnica,
    cogumelos brilhantes, esfera armilar, telescópio, fonte mágica.
  - **Terror**: forca, jaula, mesa de tortura, cadáver (dá pra revistar), teia gigante, espelho quebrado,
    boneca velha (o jogador pega), pilha de ossos, círculo de velas, poça de sangue.
- Os que fazem sentido são **interativos** (guardam itens), **iluminam** (cristal, neon, tela, braseiro,
  vela, tocha) ou podem ser **empurrados**. Objeto que ilumina não bloqueia a visão (a luz ficaria presa).
- **Painel Objetos** (decisão do Manel): o filtro tem "Tema: Medieval / Moderno / Futurista / Mágico /
  Terror" e **abre no tema da aventura** (troca sozinho quando o tema muda). Mostra primeiro os feitos pro
  tema, depois os antigos que combinam (ex.: caixão no Terror) e por fim os comuns. Buscar pelo nome
  procura em todos. As categorias de sempre continuam no filtro.
- A categoria "Temáticos" virou **Tecnologia** e **Magia** (o carro foi pra Cenário, a caixa de
  suprimentos pra Recipientes). Aventuras salvas abrem igual (o tipo do objeto não mudou).
- ⚠ **Mande o .exe novo pros amigos**: Player antigo não conhece os objetos novos e desenha um baú.

#### Bloco 2 · Retratos estilo Baldur's Gate ✅ (v0.31.0)
Decisões do Manel: imagem do token + retrato opcional · retrato com PV e condições · PV/condições
respeitam o cadeado "quem vê" (igual ao token).
- **Grupo na lateral esquerda da mesa** (mestre e jogadores): um retrato em pé por token de jogador, com
  nome, **barra de PV**, até 4 **ícones de condição** (+n), **moldura dourada** em quem está na vez e
  moldura dupla no seu personagem. **Caído** fica cinza com a cruz; **morto** escurece com a caveira.
  Clique = câmera no token · duplo clique = ficha (mestre: qualquer uma; jogador: a dele).
  Grupo grande encolhe pra caber na altura da mesa.
- O grupo vai do servidor numa **lista à parte**: o retrato do companheiro **não some** quando ele sai da
  visão (névoa/escuro). PV e condições de cada um vão filtrados por jogador; o dono vê tudo do dele.
  O mestre vê tudo, e o que está escondido dos jogadores aparece apagadinho.
- **Retrato opcional** no "Editar token" (linha Retrato): imagem em pé tipo pintura, reduzida pra 512 px.
  Sem ele, usa a imagem do token; sem imagem, a inicial na cor do token. Salvo na aventura.
- **Ordem do combate em retratos**: a faixa de cima mostra retratos pequenos na ordem, com a iniciativa
  num selo, a vez com moldura dourada; clique leva a câmera. Criatura que o jogador não vê = silhueta
  "???". **Companheiro de grupo nunca vira "???"** (antes virava, quando estava fora da visão).
- Liga/desliga: Mestre em Exibir → "Retratos do grupo"; jogador no menu ⚙ Gráficos. Fica salvo no PC.
- Teste novo: `teste_retratos.py` (26 testes no total).
- ⚠ **Protocolo de rede 6**: mande o .exe novo pros amigos (Player antigo é recusado com aviso).

#### Chat e Dados separados ✅ (v0.31.1) — pedido do Manel
- Antes era um painel só ("Chat e dados", com abas). Agora são **dois painéis**, cada um com seu botão
  na barra (Mestre e Player): **Dados** (Ctrl+D) — rolar e rolagens prontas — e **Chat** (Ctrl+E).
- O contador de não lidas fica no botão Chat. Rolagens só viram aviso no canto da mesa se Dados e Chat
  estiverem os dois fechados (o chat também mostra as rolagens); mensagens, se o Chat estiver fechado.
- Mestre: os dois também no menu Exibir.

#### Bloco 3 · Dados 3D rolando na mesa ✅ (v0.32.0) — em OpenGL (decisão do Manel)
- Pasta nova `taverna/dados3d/`. **Sem instalar nada**: OpenGL do próprio PyQt6 + numpy (o `pybullet` não
  existe pro Python 3.15, então a física é do Taverna).
- **Dados de verdade**: d4, d6, d8, d10 (trapezoedro), d12, d20 e d% (dois d10: dezenas "00–90" + unidades).
  Faces opostas somam lados+1; 6 e 9 com risquinho; d4 com os números nas quinas (vale o de cima).
- **Física real**: caem de um lado da mesa, quicam, batem um no outro e nas bordas, rolam e param retos.
  **Determinística**: o servidor manda uma "semente" e a área da física é fixa, então **todo mundo vê o
  mesmo quique**, em qualquer tamanho de janela. Calculada em segundo plano (a tela não trava).
- **O resultado é sempre o do mestre**: a física roda solta e, quando o dado para, os números das faces
  são renomeados pra face de cima mostrar o valor sorteado (sem dado "forçado").
- **OpenGL** (placa de vídeo): luz principal + luz de preenchimento, reflexo, números gravados, borda
  brilhante e leve transparência nos temas "gema", sombra macia que cresce com a altura, antisserrilhado.
  **Material por tema**: osso (medieval), plástico branco (moderno), vidro ciano (futurista), ametista com
  ouro (mágico), vermelho-sangue com números de osso (terror), marfim (claro), grafite (escuro).
  Dado descartado (vantagem/desvantagem) aparece escurecido.
- **Placar** no fim: quem rolou, motivo, total grande, "20 NATURAL!" em dourado / "1 natural…" em vermelho,
  e a conta (1d20[17] + 5). Some sozinho. Rolagens seguidas entram na fila.
- Até **10 dados** na tela (o total vale pra tudo). Rolagem privada do mestre: só na tela dele.
- Liga/desliga por pessoa: Gráficos → "Dados 3D rolando na mesa" (desligado = o aviso de sempre).
- **Plano B**: se o OpenGL falhar no PC, desenha os mesmos dados sem placa de vídeo e anota o motivo no
  `erros.log` (função nova `seguranca.registrar_erro`). Os testes usam o plano B (não há tela aqui).
- ⚠ **O visual em OpenGL nunca foi visto rodando** (não dá pra testar aqui): conferir com `mestre.py`.
- Teste novo: `teste_dados3d.py` (27 testes). Protocolo de rede igual (6): campos novos na rolagem
  ("fisicos", "semente") — Player 0.31 ignora e mostra o aviso de sempre.
- PRÓXIMOS (combinado): levar o OpenGL pras áreas de efeito → luz → clima → mesa inteira.
- (v0.32.1) Manel conferiu: "ficou muito bom", mas **travado** (não ia a 60 FPS) e pediu **borda suave**.
  - Animação lisa: posições **interpoladas** entre os quadros da física (antes pulava de 1/60 em 1/60 s),
    o próximo quadro é pedido quando o monitor mostra o anterior (**vsync**, `frameSwapped`), e o timer
    do plano B virou o preciso (o comum do Windows tem ~15,6 ms e dava trancos). Câmera em cache.
  - **Quinas e arestas arredondadas** (malha chanfrada em `geometria.malha_chanfrada`; a física segue o
    sólido original) + antisserrilhado 8× ligado explicitamente.
  - ⚠ De novo não visto rodando em OpenGL: conferir se ficou liso e bonito. → Manel: "tá perfeito".

### 🧊 MESA EM 3D — plano combinado em 17/11 (ideia do Manel e do amigo)
Tudo na mesa pode ser 3D (piso, paredes, tokens, objetos, efeitos), mas a **câmera é sempre de cima**
e ninguém gira (como aqueles mapas de jogo). Decisão: **câmera de cima COM perspectiva** (não isométrica):
o chão fica idêntico ao 2D (grid, cliques, régua, visão e névoa não mudam) e o que tem altura "vem pra
câmera". Ordem combinada:
1. ✅ Câmera 3D + paredes e portas com altura (v0.33.0)
2. ✅ Mesa desenhada pela placa de vídeo (viewport OpenGL) + piso com relevo + luz nas paredes (v0.34.0)
3. ✅ (v0.36.0) Áreas de efeito em 3D com partículas (lava com pedras boiando e respingos, fogo subindo pra câmera,
   bolhas de veneno, cristais/neve no gelo…) + **efeitos que iluminam em volta na cor deles** (lava
   laranja, ácido verde, magia roxa…) + **várias cores de magia** (pedido do Manel)
4. ✅ (v0.37.0) Tokens e objetos com volume · 5. ✅ (v0.38.0) Clima e impactos em 3D
Sempre com plano B: o desenho 2D de hoje (Gráficos → desligar "Mesa em 3D", Gráficos Baixo, PC sem OpenGL).

#### Mesa 3D, parte 1 · Paredes e portas com altura ✅ (v0.33.0)
- `mesa/camera3d.py`: câmera acima do centro da tela, altura = 1,8 tela. O truque: um plano inteiro numa
  mesma altura é só o desenho 2D **ampliado a partir do centro da tela** — então o TOPO de uma parede é o
  próprio desenho da parede (texturas de sempre) lá em cima, e as LATERAIS ligam o pé ao topo.
- **Paredes com 2 m de altura**: faces de dentro aparecem conforme a posição na tela (parede à esquerda
  mostra a face da direita, etc.), com a **textura do material** (pedra, tijolo, madeira…), mais escuras no
  pé e conforme estão de costas pra luz (que vem de cima-esquerda). Sombra no chão continua.
- **Portas e janelas com volume**: batentes até a altura da parede; folhas de 1,85 m que giram de pé;
  mecânica desliza pra dentro da parede; **secreta com a altura e a textura da parede** (se disfarça);
  grade levadiça vai baixando enquanto "sobe"; cortina; barreira mágica translúcida; janela com peitoril
  baixo e o vidro em cima.
- Funciona em qualquer PC (é QPainter, não precisa de OpenGL) e nos testes. Gráficos Baixo = 2D.
- Opção nova: Gráficos → **"Mesa em 3D (paredes e portas com altura)"**, liga/desliga na hora.
- Limite conhecido: um token do outro lado de uma parede alta pode aparecer por cima da lateral dela
  (a névoa normalmente esconde esse lado). Resolve quando a mesa toda for desenhada em 3D (parte 2). → resolvido na v0.34.

#### Mesa 3D, parte 2 · Placa de vídeo, piso com relevo e luz nas paredes ✅ (v0.34.0)
- **A mesa é desenhada pela placa de vídeo** (viewport OpenGL do QGraphicsView, antisserrilhado 4×):
  o desenho é o mesmo, mas sai do processador — arrastar e dar zoom em mapa grande fica mais leve.
  Decidido ao abrir o programa (Gráficos → Mesa em 3D); sem OpenGL, plano B (como antes) + aviso no erros.log.
- **Piso com relevo que reage à luz** (`mesa/relevo_gl.py`): o terreno é desenhado por um shader com um
  mapa de relevo calculado da própria textura (claro = alto: pedras saltam, juntas afundam). A tocha
  passando revela os sulcos; a luz realça o lado virado pra ela e sombreia o outro. Médio = suave,
  Alto = forte. Sem luz por perto, o chão fica igual. Se o shader falhar, volta pro desenho de sempre.
- **Paredes e portas por cima dos tokens**: camada própria (`mesa/altura3d.py`, z 700.000) — um token do
  outro lado de uma parede alta fica ESCONDIDO atrás dela; luz e névoa continuam por cima.
- **A luz "lambe" as paredes**: tocha, lampião, cristal… pintam com a cor deles a face da parede (e da
  porta) virada pra eles, mais forte de perto, e só se a luz chega ali (parede no caminho bloqueia).
- Corrigido no caminho: reabrir a aventura com portas no modo 3D derrubava o programa nos testes (porta
  já apagada sendo desenhada) — agora é ignorada.
- Teste novo: `teste_mesa3d.py` (28 testes). ⚠ Piso com relevo e viewport OpenGL NÃO vistos rodando:
  conferir no PC (tocha perto de chão de pedra/madeira, no Escuro/Penumbra).
- ~~Limite conhecido~~ (o Manel confirmou em 18/11 que não acontece mais): o relevo do chão ainda não sabe de parede no caminho (a luz de uma sala pode realçar
  de leve o relevo do outro lado da parede, perto dela). Fica pra quando a luz inteira for pro shader.
- (v0.34.1) Manel viu o piso com relevo funcionando no PC dele. Pediu pra tirar as **faixas escuras nas
  paredes**: as faces de costas pra luz geral (viradas pra baixo/direita) ficavam quase pretas e o pé da
  parede tinha um degradê forte. Agora as faces vão de ~60% (de costas) a ~95% (de frente) da cor da
  textura, e o pé só escurece um pouco. (As manchas do chão continuam como estavam — eram de propósito.)
- (v0.34.2) Manel: "a pedra está parecendo plástico". Três causas e as correções:
  - **Textura da pedra** (`materiais._laje`) refeita: lajotas com cantos tortos e lados irregulares,
    manchadas em várias escalas, com grão, lascas na borda e rachaduras finas; argamassa com grão. E a
    textura agora é de **2×2 m (16 lajes diferentes)** em vez de 1×1 m (4) — repete bem menos
    (`TAM_TEXTURA`). Antes: retângulo perfeito com degradê liso = azulejo de plástico.
  - **Relevo embutido** (`materiais._relevo`, vale pra todos os chãos e paredes): usa também o grão (não
    só a forma suavizada, que deixava "acolchoado") e **não clareia dentro dos vãos** — as juntas eram
    linhas claras em alto-relevo (cara de grade de plástico); agora são vãos escuros afundados.
  - **Shader do piso** (`relevo_gl`): luz FOSCA (Lambert, sem o brilho somado que parecia reflexo),
    relevo em duas escalas (forma + grão), **sujeira/sombra nas juntas** (cavidade, canal azul do mapa) e
    a luz não "brilha" dentro do vão. Conferido simulando o shader em numpy (não dá pra ver OpenGL aqui).

#### Materiais novos ✅ (v0.35.0) — Manel: "o brilho ainda tá estranho, parece plástico; deixa as texturas mais bonitas, tudo"
- O que ainda dava cara de plástico era a **luz pintada dentro das texturas** (sempre de cima-esquerda):
  um fio claro em toda junta, no chão inteiro. **Saiu de vez** (`materiais._relevo` removido). As texturas
  agora têm só a cor e a sujeira/sombra nos vãos; o relevo e o brilho vêm SÓ das luzes de verdade (shader).
- **Gerador novo** (`mesa/texturas.py`, numpy, sem imagem de fora): ruído de Perlin em várias escalas,
  pedras de formato orgânico (Voronoi), rachaduras de verdade, veio de madeira, ondas de areia,
  cáusticas da água… tudo **emenda sem costura** e os chãos naturais têm **4×4 m** antes de repetir.
- **Refeitos (26 chãos)**: pedra (lajes irregulares assentadas à mão), paralelepípedo, cascalho, rocha de
  caverna, obsidiana, mármore branco (veios + placas), cerâmica, ouro (moedas), terra (com pedrinhas),
  lama (poças), areia, grama (fios e florzinhas), neve (cintilando), gelo (rachaduras), água (cáusticas),
  pântano (algas e lentilha-d'água), lava (fendas incandescentes), ácido (bolhas), madeira e tábuas velhas
  (comprimentos variados, veio, nós, emendas desencontradas), concreto, asfalto, concreto com sangue,
  placa de metal (escovado, rebites) e metal enferrujado, carpete (trama).
- **Paredes ganharam FACE própria** (a lateral vista de frente, antes repetia o topo empilhado): fiadas de
  pedra de alturas diferentes, tijolos assentados, tábuas, troncos roliços (paliçada), rocha com fissuras,
  concreto com marca de fôrma, gesso, metal, enferrujado, sebe (folhagem), gelo, obsidiana. E topos novos.
- Os "desenhados" (runas, neon, grade, xadrez, hexágono, tapete, cristal, vidro, energia, osso…) mantêm o
  desenho, sem a luz pintada, com grão e sombra nos vãos (`texturas.acabamento`).
- **Guardadas no disco** (`Documentos/Taverna/cache/texturas_v2`): a 1ª vez gera tudo em ~6 s (só se abrir
  a paleta inteira); depois carrega em <1 s. Subir `VERSAO_TEXTURAS` quando o gerador mudar.
- Shader do piso com menos "bisel" na borda e mais grão (`relevo_gl.mapas`).

#### Mesa 3D, parte 3 · Efeitos em 3D, luz colorida e cores de magia ✅ (v0.36.0)
Decisões do Manel: cor livre pra **magia, luz, radiante e escuridão**; a luz do efeito **revela no escuro
como uma tocha**.
- **Efeitos que iluminam na cor deles** (`efeitos.LUZ_EFEITO`): fogo laranja (tremendo), lava laranja forte,
  raio azulado, luz, radiante dourado, ácido verde, veneno verde fraco, gelo azul fraco, magia roxa (ou a
  cor escolhida). A luz entra na iluminação de verdade: revela no escuro, pinta as paredes, a parede bloqueia.
  Escuridão não ilumina.
- **Cor livre**: no painel Atmosfera (linha de cores, só aparece pros 4 efeitos) e no duplo clique da área
  ("Cor": 8 cores prontas + "Outra…"). Vai pela rede no campo "cor" (opcional — cliente velho ignora, por
  isso o protocolo continua 6). Muda o desenho 2D, as partículas e a luz.
- **Partículas 3D** (`mesa/efeitos3d.py`), com altura, vindo pra câmera: fogo (labaredas + brasas subindo,
  fumaça no Alto), lava (respingos em arco e bolhas estourando), veneno/ácido (nuvem subindo + bolhinhas),
  gelo (neve caindo + cristais de pé), água (gotinhas), raio (faíscas do chão), escuridão/fumaça (véus
  subindo), luz (poeira de luz), radiante (colunas de luz), magia (anel de runas flutuando + fagulhas em
  espiral), vinhas (talos balançando). Sem estado (função do tempo), Médio = metade das partículas, Baixo
  ou "Mesa em 3D" desligado = só o 2D. Desenhadas pela camada alta: por cima dos tokens, atrás das paredes.
- Teste: `teste_mesa3d.py` desenha todos os efeitos em 2 níveis e 3 instantes. ⚠ Não visto rodando de
  verdade (animação e desempenho com placa de vídeo): conferir no PC.
- Manel viu no PC e aprovou ("ficou bom").

#### Mesa 3D, parte 4 · Tokens e objetos com volume ✅ (v0.37.0)
Decisão do Manel: token como **ficha grossa** (entre ficha grossa, miniatura em pé e pedestal).
- **Token = ficha de 30 cm** (`token.ESPESSURA_3D`): sombra no chão, lateral de cilindro (na cor do anel,
  clara do lado da luz da mesa) e TUDO do token (imagem, anel, barra de vida, nome, condições) desenhado
  no topo. A lateral aparece mais na borda da tela (perspectiva de verdade; no centro, visto de cima, quase
  não aparece). Clique e arrasto continuam no chão, como sempre.
- **Objetos com altura por tipo** (`props.ALTURA_3D`, em metros; o que não está na tabela usa a altura da
  categoria): o contorno do desenho é **empilhado** do chão até a altura (laterais escurecidas, mais
  escuras no pé) e o desenho de sempre fica no topo. Ex.: estante 1,9 m, guarda-roupa 2 m, pilar 3 m,
  árvore 2,6 m, barril 1 m, mesa 0,8 m, contêiner 2,4 m. Rente ao chão (tapete, papéis, moedas, círculo
  mágico, poça de sangue, teia) = 0, fica 2D. Folhagem/pano (`ORGANICOS`) escurece menos a lateral.
  Imagem própria (objeto com foto) ganha 0,6 m. Camadas: ~1 a cada 1,5 px de deslocamento (máx. 28 no
  Alto, 16 no Médio).
- Paredes continuam por cima (um objeto atrás de uma parede alta fica escondido).
- Teste em `teste_mesa3d.py` (estante no canto da tela se desloca no 3D e não no 2D; token desenha).
  ⚠ Não visto no PC: conferir desempenho com muitos objetos e se as alturas estão boas.
- Limite conhecido: o objeto é um "bloco" do contorno — a árvore vira uma coluna de copa (a lateral é
  verde escurecida), a mesa não tem pernas. Pra pernas/copa de verdade precisaria de modelo próprio por tipo.
- Manel viu no PC e aprovou ("ficou bom").

#### Mesa 3D, parte 5 · Clima e impactos em 3D ✅ (v0.38.0) — fecha o plano da Mesa 3D
- **Clima com altura** (`ui/clima.py`, `_passo3d`/`_pintar3d`): cada partícula tem um ponto no chão e uma
  altura; na tela ela se afasta do centro conforme sobe. Chuva = riscos curtos apontando pro centro, que
  **respingam onde batem no chão**; neve desce encolhendo (flocos perto da câmera grandes e desfocados no
  Alto); cinzas e brasas sobem crescendo; folhas planam descendo; areia rente ao chão; neblina em camadas
  de alturas diferentes. **Preso ao mundo**: ao arrastar/dar zoom no mapa, as partículas acompanham, e o que
  está mais alto anda mais (paralaxe). Raio da tempestade desce do alto até um ponto do chão.
- **Impactos com altura** (`mesa/impactos.py`): bola de fogo e coluna de fumaça da explosão SOBEM pra
  câmera, estilhaços voam em arco; o raio desce do alto até o alvo; pedras do desabamento caem de cima (com
  a sombra no chão crescendo) e a poeira sobe; anéis de runas do clarão arcano flutuam e as fagulhas sobem
  em espiral. Onda de choque continua no chão.
- `camera3d.Camera.z_max()`: nada passa de ~2,2× de ampliação (não "estoura" na câmera).
- Plano B: Mesa 3D desligada / Baixo = clima e impactos como antes. Erro no desenho vai pro erros.log.
- Teste em `teste_mesa3d.py` (os 7 climas com o mapa sendo arrastado + os 5 impactos do mapa em 4 instantes).
  ⚠ Não visto no PC: conferir se a chuva/neve ficaram naturais e o desempenho na tempestade forte.
- Manel viu no PC: "tá ficando muito bom".

### 🧊 MESA 3D, segunda rodada — pedidos do Manel (17/11, depois da v0.38)
"As áreas de efeito ainda estão no estilo 2D, quero 3D e que interajam com o cenário (sala de madeira +
fogo = chão com cara de queimado, sem o fogo se espalhar)". Decisões:
- **Marcas no chão ficam até o mestre limpar.**
- **Neblina volumétrica rasteira** (até ~1,5 m), que **reage aos objetos** (contorna, não atravessa).
- **Gás como área de efeito** (gás tóxico…) que **é bloqueado por paredes, portas** etc.
- **Andares**: cada andar com seu chão/paredes/objetos (camadas viram andares); **cada jogador vê só o
  andar do token dele** (jogador 1 no andar 2 vê o 2, jogador 2 no andar 1 vê o 1); **escada: o jogador
  clica pra subir/descer**. O grid importado é só a base; o mestre também constrói o próprio chão.
Ordem: 1) áreas 3D + marcas (v0.39) · 1b) reações entre áreas (v0.40, pedido no meio) · 2) neblina
volumétrica + gás bloqueado por paredes · 3) andares.

#### Áreas de efeito em 3D e o chão reagindo ✅ (v0.39.0)
- **Superfície pela placa de vídeo** (`mesa/efeitos_gl.py`, shader animado, borda irregular que se mistura
  ao chão): lava escorrendo com placas de crosta e rachaduras incandescentes; fogo em brasa tremendo
  (o chão queimado aparece embaixo); gelo rachado em células com brilhinhos; ácido com bolhas estourando;
  veneno/fumaça enrolando; água com cáusticas; raio com arcos que trocam de lugar; escuridão; luz com
  pontinhos; radiante com feixes girando; magia em espiral na cor escolhida. Teia e vinhas ficam no
  desenho de sempre. **Conferido de verdade na placa de vídeo deste PC** (contexto OpenGL sem janela,
  `testes/saida/areas_shader.png`). Plano B: o desenho 2D (sem OpenGL, 3D desligado, Baixo, ou erro).
- **Marcas no chão** (`mesa/marcas.py`): a área PARADA no lugar faz o chão "pegar" aos poucos (~3 s, a
  própria área desenha); arrastar pra posicionar não deixa rastro. Ao apagar a área (ou movê-la depois de
  ter pegado), vira uma pincelada do terreno `{"t": "marca"}` — salva, vai pros jogadores, tem relevo com a
  luz, entra no Ctrl+Z. Fogo = **madeira/pedra torrada mostrando as tábuas**, cinza e rachaduras, borda
  marrom; lava = rocha vulcânica rachada; raio = marca ramificada (Lichtenberg); ácido = corroído com furos;
  veneno = mancha; gelo = geada; água = chão molhado mais escuro; vinhas = musgo; magia = resíduo na cor
  dela; radiante = descorado; escuridão = veios de corrupção. Luz, fumaça e teia não marcam.
  Cada marca tem duas partes: uma que ESCURECE/TINGE o chão que já está lá (Multiply) e uma que COBRE.
- **Atmosfera → 🧽 Limpar marcas do chão** (só o mestre); pra tirar uma só, selecionar como pincelada e apagar.
- Protocolo 7 (o terreno ganhou o tipo "marca"; Player antigo não entende).
- Teste em `teste_mesa3d.py` (marca só depois de parada, fica ao mover/apagar, luz não marca, as 11 geram
  imagem, limpar + Ctrl+Z; o shader é testado quando dá pra abrir OpenGL).
  ⚠ Não visto rodando dentro do programa (animação dentro da mesa, desempenho com várias áreas).

#### Reações entre áreas ✅ (v0.40.0) — Manel: "água em cima do fogo, o fogo apaga; fogo no gás explode"
Decisões: **o mestre confirma** cada reação (aviso não-bloqueante "Aplicar / Agora não"); **todas** da
tabela. Reage quando uma área cobre ≥ 30% da menor. Nada dá dano sozinho (continua com o mestre).
- `mesa/reacoes.py`: água+fogo (apaga, vapor 8 s) · água+lava (vira rocha = marca de basalto, onda de
  vapor, a água evapora) · fogo+gás e raio+gás (EXPLOSÃO do tamanho da nuvem, chão queimado) · fogo+ácido
  (estalo, vira vapor tóxico) · fogo+gelo (derrete → água) · água+gelo (congela) · raio+água (a poça fica
  eletrificada) · fogo+vinhas/teia (pegam fogo) · luz/radiante+escuridão (dissipa).
- A cena espera soltar o mouse (600 ms) e procura; "Agora não" só pergunta de novo se uma das duas mudar;
  um par que já reagiu não reage de novo. Explosões/ondas vão pra todo mundo (`servidor.impacto`) se for a
  aba ao vivo. Vapor é uma área de fumaça que some sozinha.
- Teste em `teste_mesa3d.py` (as 12 reações, sem encostar não reage, recusar, o aviso não trava a mesa).
- Corrigido no caminho: import local de QTimer em `MesaCena.__init__` (escondia o import do módulo).

#### Reações com física + lançar efeitos ✅ (v0.41.0)
Manel testou: "botei água em cima do fogo e ele apagou TODO, não só onde encostou". E: "uma explosão é
reação em cadeia; a água pegar a energia também".
- **Reação de CONTATO = só onde encosta** (água×fogo, água×lava, fogo×ácido, fogo×gelo, água×gelo,
  luz×escuridão): a área ganha **recortes** (`EfeitoItem.recortes`, polígonos tirados da forma) e o
  pedaço que vira outra coisa é uma área de **forma livre** (`forma "livre"` + `pontos`). Ex.: o fogo
  perde só o pedaço coberto pela água; o gelo derrete só a beirada onde o fogo encosta e ali vira água.
- **Reação em CADEIA = a área toda** (gás + fogo/raio explode a nuvem inteira; raio na água eletrifica a
  poça inteira; fogo se espalha pelas vinhas/teia inteiras).
- Aviso agora dispara com ≥ 8% de sobreposição. Vapor de reação não bloqueia visão/luz (`NOME_VAPOR`).
- **🎯 Lançar** (Atmosfera, mestre e jogador; `mesa/lancamentos.py`): elemento (fogo, gelo, ácido, veneno,
  raio, água, magia, escuridão, luz, radiante, magma) × jeito: **projétil** (bola de fogo, cristal de gelo
  girando, bolha de ácido/veneno com reflexo, orbe… voa em arco com rastro e estoura no alvo), **jato em
  cone** (as labaredas/lascas/gás saem de quem lança e VÃO PRA FRENTE, abrindo) e **jato em linha / raio**.
  Arrasta de quem lança até o alvo (começando num token, sai do centro dele); ajusta abertura, largura,
  velocidade; opcional "deixar a área no chão quando chegar" (raio da área no alvo). Na Mesa 3D, a bola
  sobe em arco e vem pra câmera.
- Rede: jogador manda `lancar` (servidor confere tudo: `lancamentos.conferir`, distância máx. 60 m) →
  todos recebem `lancamento`; a área deixada vira template do jogador. Protocolo **8**.
- Teste em `teste_mesa3d.py` (recorte parcial vai pela rede, forma livre, 11 elementos × 3 jeitos em 2D
  e 3D, bolha de ácido deixando a poça do jogador). ⚠ Não visto rodando no PC (animação de verdade).

### 📚 Pedido do Manel (17/11, depois da v0.41) — biblioteca sem D&D
"Vou lançar em plataformas: tira o setor da biblioteca com as coisas de D&D. Deixa só a biblioteca própria
do jogador (importar os documentos que ele usa), uma aba de Fichas na biblioteca, e o jogador também tem
biblioteca." Decisões (perguntado): tira o que der problema de direito autoral → o SRD 5.1 é CC-BY 4.0
(livre, com atribuição), então loot/magias da ficha D&D/condições **continuam**; sai a **aba do compêndio**.
Livros que o mestre libera **vão pela rede** pro jogador (muda a regra antiga "PDF nunca passa pela rede";
com aviso de só enviar o que se tem direito). Aba Fichas = **modelos + fichas salvas**.

#### Biblioteca nova, reações automáticas, projéteis e cores ✅ (v0.42.0)
- **Biblioteca**: saiu o Compêndio (SRD). Abas: **📕 PDFs** (os seus), **📄 Fichas** (modelos em branco em
  `Documentos/Taverna/Fichas - modelos` → "Nova ficha deste modelo"; embaixo as fichas preenchidas) e
  **🧙 Tokens** (só o mestre; `ui/biblioteca_tokens.py`, `Documentos/Taverna/Tokens salvos`). O jogador
  tem PDFs e Fichas. Saiu também o "📖 Ficha do SRD" do botão direito do token.
- **Tokens prontos**: o botão **Token** da barra abre a Biblioteca na aba Tokens. "Novo token" tem
  **Cancelar / 💾 Salvar na biblioteca / ⬤ Colocar na mesa**, com PV e deslocamento. Da biblioteca,
  "Colocar na mesa" (ou duplo clique) spawna quantas vezes quiser, já com PV/deslocamento. Botão direito num
  token da mesa → "💾 Salvar na biblioteca de tokens".
- **Reações automáticas** (o Manel tirou o aviso): encostou, reage; só avisa na barra de status. A própria
  cena aplica (`MesaCena._procurar_reacoes`); explosões vão pra todo mundo via `janela.impacto_de_reacao`.
- **Lançar**: escolher o **formato do projétil** (bola, orbe com faíscas, **míssil mágico = 3 setinhas
  serpenteando**, cristal, bolha, lança, raio) e a **cor** de magia, **fogo** (azul, verde, negro, roxo,
  branco, outra…), **raio** (vermelho, roxo, verde, dourado, negro…), luz, radiante e escuridão.
  Cor escura (fogo negro) desenha por cima em vez de "somar luz".
- Pendente (v0.43): o mestre libera livros pros jogadores (o PDF vai pela rede) e vê a biblioteca deles.

#### Livros entre mestre e jogadores ✅ (v0.43.0)
- **Mestre → jogador** (`rede/livros.py`): Biblioteca → PDFs → **👥 Liberar pros jogadores…** (marca quem
  pode ver, ou "Todos", que vale até pra quem entrar depois; aviso de só compartilhar o que se tem direito).
  O PDF vai pela rede **em partes de 384 KB** (fila com timer, não trava a mesa; até 400 MB) e aparece na
  aba **📗 Do mestre** do jogador (com "chegando… %"). Tirou a liberação → a cópia do jogador é **apagada**.
  Liberações guardadas nas preferências do mestre (`livros_liberados`); a lista na aba mostra "👥 pra quem".
  O jogador guarda em `Documentos/Taverna/Livros do mestre` (com `indice.json`; não baixa de novo o que já tem).
- **Mestre vê a biblioteca do jogador**: ao entrar (e quando importa/tira PDF), o jogador manda a LISTA dos
  PDFs dele; aba **👥 Dos jogadores** do mestre. **📥 Pegar uma cópia** → o jogador envia o arquivo (e é
  avisado na barra) → fica em `Documentos/Taverna/Livros dos jogadores/<nome>`.
- Regra do CLAUDE.md atualizada (antes: "PDF nunca passa pela rede"). Protocolo **9**.
- Teste novo `teste_livros.py` (29 testes): mestre libera ~1 MB → chega idêntico; tira → some; "Todos";
  mestre vê a lista da jogadora e pega a cópia (idêntica). Usa e devolve as preferências reais.

#### Neblina volumétrica + gás que respeita paredes ✅ (v0.44.0)
Decisões do Manel: neblina **rasteira** que **reage aos objetos**; gás (área) **bloqueado por paredes e portas**.
- **Neblina volumétrica** (`mesa/neblina.py`, Clima → Neblina com a Mesa 3D): uma camada de verdade dentro
  da mesa (z 690.000: por cima de tokens/objetos, por baixo das paredes altas, da luz e da névoa de guerra),
  do chão até ~1,1–1,9 m (força). No **shader**, cada pixel atravessa a camada em **6 (Médio) / 10 (Alto)
  fatias de altura** com a perspectiva da câmera, somando um **ruído 3D** que anda com o tempo — mais grossa
  embaixo, topo dos "rolos" mais claro (sombreamento por densidade acima). **Contorna** objetos (com altura),
  tokens e paredes: máscara de ocupação (borrada) zera a densidade ali e **desvia o fluxo** (gradiente da
  máscara). As luzes da cena acendem a neblina em volta (halo). Conferido na placa deste PC
  (`testes/saida/neblina_volumetrica.png`). **Plano B** (sem OpenGL): 3–4 camadas de ruído em alturas
  diferentes com os mesmos buracos (desenha numa imagem e recorta com a máscara). Mesa 3D desligada/Baixo =
  a neblina antiga da tela. A neblina "de PNG" na tela saiu do modo 3D.
- **Gás** (`mesa/gas.py`; veneno e fumaça): a nuvem não atravessa **parede, porta fechada e objeto que
  bloqueia**; espalha do centro (ou da boca no cone/linha) e **contorna** cantos em duas etapas (anéis de
  sementes a 40% e 70% do raio). Abriu a porta → passa. Refaz no máx. ~3×/s e só se algo mudou. A forma
  recortada vale pra tudo: desenho, shader, partículas, marcas e **reações** (fogo do outro lado da parede
  não acende o gás). `MesaCena/CenaPlayer.obstaculos_gas()`.
- Teste em `teste_mesa3d.py` (gás não passa da parede; fogo do outro lado não reage; máscara da neblina no
  barril; plano B pinta). ⚠ Não visto rodando no programa (animação/desempenho da neblina com GPU).
- Manel testou: "a neblina ficou legal, reagindo aos players".

#### Gás e líquidos de cenário, iluminação dinâmica, efeito fora do mapa ✅ (v0.45.0)
Conversa com o Manel (decisões): a ÁREA de veneno/fumaça é **gás mágico** (não espalha, não some); o gás
de **CENÁRIO** é outro — a estátua que solta gás, que se espalha e, sem fonte, **dilui até sumir**; fonte
**sem parar ou por um tempo**; mesma coisa pra **líquidos** (água, lava, ácido). Iluminação **o mais fiel
possível**: luz que se mexe e **para na parede**. **Efeito no vazio (fora do mapa) não existe**; tokens e
objetos podem ficar fora (o mestre "estaciona").
- **Simulação** (`mesa/fluidos.py`): grade de 0,5 m cobrindo o cenário (cresce até 200 m), 10×/s no
  mestre. Gás = difusão (4 passos por quadro) que não atravessa parede/porta fechada/objeto que bloqueia
  (arestas fechadas entre células, calculadas dos segmentos), se dilui (0,25%/passo + fiapo ralo some).
  Líquido = escorre do mais alto pro mais baixo até a película de 6 cm e para (lava devagar, água rápido).
  Só onde tem chão. Fontes: vazão fraca/média/forte, duração (0 = sem parar), liga/desliga.
- **Reações**: água + lava → vapor (fumaça) e a lava vira **rocha** (marca de basalto no chão); gás tóxico
  concentrado + área de fogo/raio/lava, lava de cenário ou **bola de fogo chegando** → **explosão em cadeia**
  só na nuvem que está ligada (sem passar parede), pra todo mundo; água alagando uma área de fogo → apaga ali
  (recorte). A **lava de cenário brilha** (luzes com sombra a cada ~3 m de lava).
- **Desenho** (`mesa/fluidos_desenho.py`): gás **volumétrico** (fatias de altura, como a neblina) na cor,
  mais grosso onde concentra, tóxico rasteiro e fumaça subindo; líquidos com o shader animado das áreas
  (`efeitos_gl.desenhar_campo`) na forma exata do alagamento, z 3,5 (depois do chão/grid/paredes, antes de
  objetos e tokens); plano B em 2D. Marcadores das fontes só pro mestre.
- **Mestre**: Atmosfera → **🏞 Cenário: gás e líquidos** (tipo, vazão, por quanto tempo, tamanho; 📍 Pôr
  fonte, 💨 Soltar/derramar, 🧽 Limpar, Tirar fontes). Botão direito num objeto → **"Soltar gás/líquido
  daqui"** (a boca da estátua). Botão direito na fonte → ligar/desligar, vazão, tirar.
- **Rede**: o mestre calcula; os jogadores recebem o retrato (bytes comprimidos, só a parte com fluido,
  até 4×/s) — mensagem `fluidos`, protocolo **10**. Fontes e o que está espalhado vão no arquivo (`"fluidos"`).
- **Iluminação dinâmica** (`mesa/luz_dinamica.py`): luzes passageiras recalculadas enquanto se mexem
  (~30×/s), sempre com sombra: bola de fogo voando + clarão do estouro apagando; jato de fogo (a luz anda
  com as labaredas); raio piscando; explosão, clarão arcano. Na cor do poder (fogo negro quase não ilumina).
  Iluminam chão com relevo, faces das paredes, tokens, neblina e gás. `gradiente_luz` ganhou "brilho".
- **Fora do mapa** (`mesa/chao.py`): `chao_caminho()` = chão pintado (menos borracha) + mapas importados.
  Área de efeito, marca, gás e líquido são cortados no vazio. Mesa sem chão nenhum = não corta.
- Corrigido no caminho: o overlay de luz pedia uma imagem do tamanho do mundo quando a cena era desenhada
  inteira de uma vez (fotos) — agora limita à tela.
- Testes em `teste_mesa3d.py` (fonte enche o lado dela sem passar parede, bola de fogo explode, nuvem some,
  poça para, retrato/arquivo, água apaga área de fogo, corte fora do mapa, luz para na parede). Conferido na
  placa deste PC (`testes/saida/gas_liquidos_luz.png`, `so_agua.png`, `so_lava.png`).
  ⚠ Não visto no programa: desempenho com muitas fontes; nas fotos montadas "de uma vez" aparece um
  quadrado mais claro em volta de uma área de fogo/lava (acredito ser do jeito da foto — conferir na mesa).
- **(v0.45.1) "Sala fantasma"** — Manel: fogo clicado no limbo aparecia com o FORMATO da sala. Causa: a área
  nascia no (0,0), o corte "fora do mapa" era calculado ali (pegando o pedaço da sala) e, com o intervalo de
  0,3 s, não era refeito quando ela ia pro lugar do clique. Agora: a área nasce já no lugar; o corte é refeito
  NA HORA quando muda lugar/forma/giro (só a conta das paredes do gás espera); área toda no vazio **não é
  criada** (aviso pro mestre/jogador); arrastada toda pro vazio fica só o contorno pontilhado (dá pra clicar e
  apagar). Marcas no chão que já tinham "fantasma" saem com Atmosfera → Limpar marcas do chão.
- **(v0.45.2) Animação de crítico no d20** (pedido do Manel): 20 natural → o dado dá um pulinho, onda
  dourada, faíscas, brilho pulsando com raios girando e "ACERTO CRÍTICO!" com pop; 1 natural → o dado treme,
  bordas da tela piscam vermelho, rachaduras, fumaça escura e "FALHA CRÍTICA" caindo e tremendo. Só o d20 que
  VALEU (o descartado na vantagem/desvantagem não anima). Placa de vídeo e plano B (`dados3d/overlay.py`
  `desenhar_critico`; o pulo/tremor em `cena3d.Rolagem.quadro`). Teste em `teste_dados3d.py`.
- **(v0.45.3) Rolar de novo cancela a anterior** (pedido do Manel): sem fila; cada rolagem ganha um número
  e a física que terminar "velha" é descartada — a nova entra por cima na hora. (A fila de até 3 saiu.)

#### 🏢 Andares ✅ (v0.46.0) — fecha a segunda rodada da Mesa 3D
Decisões (lá de trás): cada andar com o próprio chão/paredes/objetos; **cada jogador vê só o andar do token
dele**; escada que o jogador usa clicando.
- **Cada andar é uma aba** (`mesa/andares.py`): abas do mesmo **prédio** (`cena.predio`, `cena.andar`: 0 térreo,
  1, 2… / -1 subsolo). Aba → botão direito → **🏢 Novo andar acima/abaixo**. O nome da aba mostra o andar.
- **Ao vivo é o prédio inteiro**: `servidor.andares`; `_cena_de(conexão)` = o andar onde está o token do jogador
  → o estado é montado por andar e cada um recebe o seu (mudou de andar → recebe o gás/líquido de lá também).
  Tudo que o jogador faz é tratado no andar dele (o servidor troca `self.cena` durante a mensagem). Impactos
  com lugar, lançamentos e gás vão só pra quem está naquele andar; tremor/clarão/apagão, pra todos. O combate
  junta os tokens de todos os andares.
- **Escada** (Objetos → Escada; `props.CATALOGO["escada"]`): botão direito → **Ligar ao andar de cima/de
  baixo** (cria o andar se não existir e põe a escada correspondente no mesmo lugar; `prop.ligacao`). O jogador
  dá **duplo clique na escada** (até 1,5 m) e o token vai pro outro andar, chegando junto da outra escada.
- **Mestre**: troca de andar pelas abas; botão direito no token → **🏢 Levar pro andar**.
- Jogador: aviso "Você está no 1º andar" quando muda. Salvo na aventura (`predio`, `andar`). Protocolo **11**.
- Teste novo `teste_andares.py` (30 testes): prédio criado pela escada, dois jogadores em andares diferentes
  vendo só o seu (com o barril só lá em cima), subir pela escada, salvar.
- ~~Ver o andar de baixo "apagadinho" por baixo do atual~~ — descartado pelo Manel (18/11).

#### 🐛 Correções ✅ (v0.46.1) — 4 bugs que o Manel achou
- **Luz laranja da lava da sessão passada** aparecia na sessão nova: `cena.limpar_restos()` (chamado em
  `criar_camadas_padrao` e ao carregar aventura) zera fluidos e fontes, luzes temporárias, caches de sombra e o
  prédio/andar; `fluidos.limpar()` também apaga as luzes da lava.
- **Botão direito dava `UnboundLocalError: iconizar_menu`**: um import local no ramo da fonte de fluido
  "sombreava" o nome no método inteiro (`janela_mestre._menu_contexto`). Tirado.
- **A mesa pulava ao abrir painéis**: a visão agora segura o ponto do centro quando muda de tamanho
  (`visao.resizeEvent`, `NoAnchor`), então abrir/fechar dock não mexe no que se está olhando.
- **Resultado do dado aparecia antes da animação**: o histórico e o chat só recebem quando o dado PARA
  (`PainelDados3D.revelar`; nas janelas, `_mostrar_rolagem`). Rolagem cancelada por outra por cima é revelada na
  hora, pra não sumir do histórico. Sem animação (gráficos baixos/tela inicial), entra direto como antes.

#### 🏢 Escada e andar clonado ✅ (v0.46.2) — pedido do Manel
- **Escada não é mais "baú"**: saiu do catálogo como interativa (sem conteúdo, chave, trancar, sorteio,
  estrelinha). O duplo clique do jogador só sobe/desce (`cena_player.prop_duplo_clique`). Aventuras da v0.46.0
  são corrigidas ao abrir (`PropItem.aplicar_dict`).
- **Permissão do mestre**: botão direito na escada → **✅ Liberar / 🚫 Bloquear pros jogadores**, ou "Editar
  escada…" (caixinha "Jogadores podem usar"). Vale pras duas pontas (`janela_mestre.liberar_escada`; guardado em
  `trancado`). Bloqueada: o jogador recebe "O mestre não liberou essa escada" e o mestre vê no registro.
- **Andar novo clona paredes e chão**: "Novo andar acima/abaixo" (e o "Ligar ao andar…" que cria andar) copia
  só o terreno e as paredes com portas/janelas do andar de base (`_copiar_estrutura`). Mapa (imagem), objetos,
  tokens, luzes e áreas não vêm.

#### ✂🧠 Removedor de fundo com IA + otimização medida ✅ (v0.47.0)
**Removedor com IA** (`taverna/ia/`): o Python 3.15 não tem onnxruntime, então o Taverna tem o PRÓPRIO
motor em numpy: `onnx_leve.py` lê o arquivo .onnx (protobuf na mão) e `motor.py` roda o grafo (Conv com
dilatação/passo como 9 multiplicações de matriz, MaxPool, Resize bilinear, Concat, Sigmoid…). Conferido
contra a conta na mão (`teste_ia.py`). Funciona no .exe, sem instalar nada.
- Dois modelos, **baixados só quando o usuário clica** (ficam em Documentos/Taverna/IA, depois funciona sem
  internet): **Rápido** U²-Netp (~4,6 MB, ~2 s, acerto 97–99%) e **Caprichado** IS-Net (~170 MB, ~10 s).
  Apache-2.0, créditos no LICENCAS.md (arquivos .onnx do rembg, MIT).
- Na janela do ✂ Remover fundo: "✨ Remover fundo com IA" (roda em segundo plano, com barra e Cancelar),
  régua "borda suave/seca" depois do recorte; borracha, 🎯 e desfazer continuam pra limpar o resto.
- Novo: botão **✂** ao lado da imagem e do **retrato** do token (janela de editar token).

**Otimização medida** (mesa pesada: sala com paredes, 14 tokens, 8 tochas, 6 áreas, lava e gás com fonte,
neblina — medido com a placa de vídeo de verdade, só o mestre):
- 🐛 **Travamento corrigido**: com Mestre + Players abertos no mesmo PC, os shaders (áreas, gás, neblina,
  relevo) guardavam o "kit" de cada janela pelo `id()` do contexto OpenGL, que o Python reaproveita →
  shader de uma janela usado na outra → programa fechava (access violation). Agora `mesa/gl_contexto.py`.
- Partículas das áreas: cor arredondada (o cache de bolinhas estourava e redesenhava tudo), desenho em LOTE
  (`drawPixmapFragments`) e contas em numpy → ~7,5 ms → ~4 ms por quadro.
- Luz: pinta o polígono da luz direto (sem recorte), pula luz fora da tela e reaproveita a imagem de
  luz/sombra quando nada mudou → ~4,8 ms → ~2 ms.
- Polígono de luz/visão: todos os raios de uma vez (numpy) + guardado enquanto luz e paredes não mudam.
- Paredes 3D: o "lado de fora" de cada aresta é guardado por contorno e faces fora da tela são puladas
  → ~5 ms → ~2 ms.
- Resultado: ~30 → ~36 quadros/s com tudo ligado e token andando (antes caía bem mais com jogadores
  abertos). Parada, a mesa vazia não redesenha nada; com tochas, só ~11×/s (a tremulação).

#### 🧤 Teste com o amigo: ajustes ✅ (v0.48.0) — protocolo 12
- **Atmosfera**: clicar no efeito (fogo, gelo…) já arma o "Colocar na mesa"; clicar DE NOVO tira a seleção
  (e desarma). Cores da magia e do lápis também desmarcam. Mestre e jogador (`painel_atmosfera._desmarcavel`).
- **Escada**: a janela da escada (duplo clique) tem **"🏢 Leva para"**: andar de cima/baixo ou **qualquer outra
  aba (cenário)**. A aba escolhida entra no prédio (num andar livre) e vai pro ar junto; se lá tiver uma escada
  solta, ela vira a outra ponta. Botão direito → "Esta escada leva para…" / "Desligar".
- **Ponto de luz**: o jogador vê a LUZ, mas não o desenho do ponto (`LuzItem.icone_oculto`).
- **Tocha de parede** (Objetos → Luzes): presa na parede (gire pra virar), acende luz de tocha; no 3D fica lá
  em cima, sem bloco embaixo (`props.SUSPENSOS`).
- **Jogador edita o próprio token**: botão direito no token → "Editar meu token" (nome, cor, imagem, retrato,
  com ✂ remover fundo). Tipo/tamanho/dono continuam do mestre; o servidor confere o dono (`editar_token`).
- **🧤 Luvinha**: o mouse na mesa é uma luvinha de desenho na COR DO TOKEN (mestre: dourada), com contorno
  preto (cor clara) ou branco (cor escura) e sombra; a "luvinha dos outros" também (`mesa/luva.py`).
- **Itens coletáveis**: chave, poção, moedas, saquinho e as armas novas (espada, adaga, lança, machado,
  martelo, arco, escudo) vão DIRETO pro inventário no duplo clique (de perto) e somem do chão. Janela do mestre
  enxuta (`ui/dialogo_coletavel.py`): nome, quantidade, descrição, **imagem importada**; na chave, **"Esta chave
  abre: [porta/baú]"** (tranca o escolhido). Qualquer objeto vira coletável pela caixinha "🎒 Item coletável".
- **Botão direito do jogador** (acesso rápido): no próprio token → Usar magia (abre a ficha em "Ataques e
  magias"), Inventário, Ficha, Rolar d20, Lançar daqui, Editar meu token; em objetos → Pegar / Abrir / Subir a
  escada; em criatura caída → Revistar; em qualquer lugar → Marcar o ponto, Ir pro meu token.
- **🎒 Meu inventário** na barra do jogador (atalho I).
- Teste novo `teste_jogador_v048.py`; `teste_chaves.py` atualizado pro "direto pro inventário".

#### 🍺 Launcher único + tela inicial nova ✅ (v0.49.0) — 1º passo da interface nova
- **Um programa só**: `python taverna.py` (ou `iniciar_taverna.bat`; o `gerar_exe.bat` agora gera só o
  **Taverna.exe**). Na abertura: painel **MESTRE** (nova sessão, continuar — mostra qual —, abrir) e painel
  **JOGADOR** (entrar na sessão — lembra o último nome/IP). O papel usado da última vez fica aceso.
  Saiu da mesa (fechar sessão / caiu a conexão) → volta pro launcher. `mestre.py`/`player.py` continuam.
- **Feito em Qt Quick (QML)** (`ui/lancador.py`, `ui/qml/`): por trás o cenário animado de cada tema (o mesmo
  de antes), na frente peças com material do tema (`ui/materiais_ui.py`: madeira com ferro e rebites, metal
  com LED, pedra rúnica com cristal, madeira podre com ferrugem, pergaminho com latão…).
- **O exagero segue os Gráficos** (decisão do Manel): Baixo = caixas lisas · Médio = relevo, sombra e
  cantoneiras pequenas · Alto = material do tema, moldura dupla, cantoneiras grandes, brilho pulsando.
- Conferido na placa de vídeo de verdade (Direct3D 11) e nos testes (`teste_lancador.py`, com capturas em
  `testes/saida/lancador_*.png`).
- 🐛 **Névoa: a memória do que já foi visto** agora guarda o formato exato do cone (imagem em ladrilhos de
  32 m, 8 px/m) — a borda na diagonal não fica mais em "quadradinhos" (`mesa/nevoa.py`).
- **Cone de visão padrão = pessoa comum: 180° e 24 m** (era 120° e 12 m). Tokens já salvos mantêm o deles.
- Próximo da interface: moldura da janela e botões do programa todo (painéis depois).

#### 👁 Visão dos jogadores + só o launcher ✅ (v0.50.0)
- **👁 Visão dos jogadores** (botão ao lado de "Ao vivo"): o mestre vê a mesa EXATAMENTE como a tela de um
  jogador — o mesmo filtro do servidor (névoa, andar do token, o que ele pode ver/ler), desenhado pela mesma
  cena do jogador. Escolhe quem (conectados e donos de token, mesmo quem ainda não entrou), acompanha ~3×/s,
  "Centralizar no token dele", "Voltar pra minha mesa". Só olhar (`ui/visao_jogador.py`,
  `servidor.estado_do_jogador`). Teste `teste_visao_jogador.py`.
- **Saíram `mestre.py`, `player.py`, `iniciar_mestre.bat`, `iniciar_player.bat`** e os .exe/builds antigos
  (foram pra Lixeira). Só `taverna.py` / `iniciar_taverna.bat` / `Taverna.exe`. README atualizado.

#### 🪵 Peças esculpidas com luz + luvinha em todo lugar ✅ (v0.51.0)
- **Sai a cara de "jogo de Flash"**: painéis e botões da tela inicial agora são "esculpidos" pelo
  `ui/relevo_ui.py` — altura da peça (bisel, moldura entalhada dupla no Alto, botão AFUNDA ao apertar) + o
  relevo do material, iluminados (luz de cima-esquerda, brilho especular no metal, sombra nas quinas).
  Imagem pronta em cache (não pesa).
- **Materiais CC0 do ambientCG** (`ui/materiais/`, 1,4 MB, crédito no LICENCAS.md): madeira (Medieval),
  tábuas velhas + ferrugem (Terror), placas de metal + alumínio (Futurista), couro preto + alumínio
  (Moderno/Escuro), ônix tingido (Mágico), papel kraft (Claro), latão (botão principal do Medieval).
  **"Não precisa ser tão realista"** (Manel): a textura entra suave, meio "pintada" (`ESTILIZADO = 0.5`).
- Texto sem o contorno chapado (era o que mais parecia Flash): sombra suave.
- **🧤 Luvinha no programa inteiro** (`ui/cursor_global.py`): botões, listas, menus, janelinhas, tela inicial
  — trocam seta/mãozinha/mão de arrastar pela luva na cor do jogador. Ficam o cursor de texto, os de
  redimensionar e a cruz das ferramentas.
- `gerar_exe.bat` leva a pasta de materiais.

#### 🎬 Tela inicial "de RPG" ✅ (v0.52.0) — referência do Manel: tela de título do Baldur's Gate 3
- **O Manel não quer realismo de foto** ("é uma VTT fantasiosa, não um jogo realista"): saíram as placas com
  textura de foto (as texturas CC0 ficam guardadas em `ui/materiais/`, mas a tela não usa).
- **Estilo tela de título**: cenário escuro com vinheta de cinema, **logo TAVERNA de metal** com filigrana,
  ponta e gemas no alto à esquerda, **coluna de botões finos** ("MESTRE" / "JOGADOR") — cápsula escura
  translúcida com **borda de metal com reflexo de verdade**, pontas em losango, gemas, brilho ao passar o mouse.
  Sem placas e sem a borda dourada de "último papel" (o Manel achou estranha).
- **Metal de verdade** (`estilizado.metal`): em vez de degradê (parecia plástico), cada pixel reflete um
  "ambiente" — céu claro, horizonte escuro, chão quente — pela inclinação do bisel, + brilho estourado e riscos
  de polimento. Cada tema com o seu metal (ouro velho, ferro avermelhado, aço azulado, prata arcana, bronze…).
- **Medieval**: muro de **pedra cinza 3D** (blocos irregulares, lascados, inclinados, argamassa funda) iluminado
  DE VERDADE pelas tochas (a luz vem da direção de cada uma); **tochas** com suporte de ferro batido e **fogo de
  partículas na placa de vídeo** (Qt Quick Particles): chama em camadas, miolo amarelo, faíscas que dançam,
  fumaça (Alto) e a luz tremendo na parede. Baixo = chama parada.
- Arquivos: `ui/estilizado.py`, `ui/qml/{Lancador,BotaoOrnado,Tocha,Rotulo}.qml`.
- **Cada tema com personalidade própria** (pedido do Manel: "não o mesmo botão pra todos"; menu **no meio**):
  | Tema | Botões | Título |
  |---|---|---|
  | Medieval | cápsula com borda de ouro e pontas em losango | metal + filigrana entalhada (só ele tem) |
  | Terror | tábua velha QUEBRADA (lascas, rachadura, pregos, mancha de sangue) | sangue seco escorrendo, arranhado |
  | Futurista | só o nome; o mouse acende um contorno tecnológico | tubos de neon + traço magenta |
  | Mágico | cristal lapidado apagadinho que ACENDE com o mouse | linha mágica brilhando, com faíscas |
  | Moderno | plaqueta industrial de aço com parafusos; faixa de alerta no mouse | placa de aço industrial |
  | Claro/Escuro | **neutros "de programa"** (tipo editor de imagem): liso e limpo | só a palavra, objetiva |
  O **Claro** virou neutro no programa todo (cinzas/branco e Segoe UI, não mais pergaminho).
- **(v0.53.0) Terror e Moderno refeitos** (o amigo achou o Terror "cringe"):
  - **Terror** (vibe de jogo de terror atual, tipo Phasmophobia — sem copiar): letra de **máquina de escrever
    corroída** (Courier New + corrosão feita pelo programa), cor de osso com um "fantasma" vermelho deslocado;
    botões só com o texto e, no mouse, **contorno rabiscado à mão** + luz de lanterna; título que **pisca**
    (luz falhando); **chiado/granulado de câmera** + linhas de varredura + faixa de interferência (o Manel curtiu).
    Cenário novo (`CenaTerror.qml`): **lua** com mares, crateras, fase e halo pulsando, nuvens passando na
    frente, **árvores mortas balançando**, **névoa em 4 camadas** (alturas/velocidades diferentes = volume).
  - **Moderno** (como os apps/jogos de hoje): título limpo em Bebas branco com traço de destaque, **cartão de
    vidro fosco** desfocando a cidade (MultiEffect), botões translúcidos arredondados com barrinha de destaque.
  - As caixinhas **Tema/Gráficos** do rodapé usam o desenho dos botões do tema.
- **Tocha que se encaixa no cenário**: o fogo ilumina o próprio suporte (laranja em cima, escuro embaixo) e o
  suporte joga **sombra comprida na parede** (+ sombra de contato).
- **(v0.54.0) Fundo do Medieval = MESA DE TAVERNA EM 3D** (ideia do Manel + Gemini, imagem de referência dele):
  Qt Quick 3D na placa de vídeo (`ui/qml/MesaTaverna3D.qml`), **vista de cima**, objetos **low-poly facetados**
  nas bordas e o meio livre pro menu: pano listrado + livro vermelho com cruz dourada e cantoneiras, vela no
  castiçal de latão com alça (chama de partículas, luz que tremula), **mapa dobrado preso na mesa por uma
  adaga enfiada** (pedido do Manel) + selo de cera, moedas de ouro e cobre com a cruz (pilha e uma escorada),
  saquinho de couro, caneca de aduelas com aros, rebites, espuma escorrendo e bolhas, pão com cortes e
  farelos, dois d6, riscos de faca e marcas de caneca. Formas em `ui/geometria3d.py` (torno, toro, moeda,
  folha dobrada, dado chanfrado; `|plano` = faces chapadas) entregues pelo `ponte.malha`; texturas desenhadas
  pelo programa e gravadas em arquivo (`estilizado.caminho_textura_3d`, o Quick 3D não lê do provedor).
  Só aparece em Médio/Alto com placa de vídeo; no Baixo/sem placa fica a mesa 2D pintada.
- **(v0.55.0) Terror com DUAS telas, sorteadas toda vez que o programa abre** (`ponte.cenaTerror`; dá pra
  forçar com a variável `TAVERNA_CENA_TERROR=tv|farol`). Desenhos em `ui/terror_cenas.py`.
  - **TV** (`qml/TerrorTV.qml`, 3D, Médio/Alto com placa): TV enferrujada low-poly (botões, grade, fio rasgado)
    com o **menu DENTRO da tela** (o Lancador mede a tela com `mapFrom3DScene` e encolhe o menu pra caber);
    tela cinza com **chiado** de verdade (textura viva via `Texture.sourceItem`), faixa rolando, **pisca** de
    vez em quando e às vezes mostra um **ROSTO** num canto ou no meio; **luminária que falha** (luz + cúpula),
    caneca rachada, fotos velhas, papeizinhos, chaves, **lanterna apagada**, pano com sangue caindo da mesa,
    janela, teias e hera. Sem placa/Baixo: cai no farol.
  - **FAROL** (`qml/TerrorFarol.qml`, 2D, jeitão "pixel pintado"): céu de tempestade, penhasco facetado com casa
    e **farol com o feixe GIRANDO** (encolhe/estica, brilha quando vira pra gente), **ondas** em 5 camadas,
    **espuma estourando nas pedras**, **barco balançando**, **chuva**, **raios** de vez em quando com clarão
    e, em ~40% dos raios (só junto com raio), a **silhueta do Cthulhu** no fundo.
  - A cena antiga da lua (`CenaTerror.qml`) ficou guardada, sem uso.
- **(v0.56.0) TUDO EM 3D (o Manel pediu) + Medieval com duas telas** (`ponte.cenaMedieval`, forçar com
  `TAVERNA_CENA_MEDIEVAL=mesa|quadro`):
  - **Mesa da taverna**: agora tem um **CONTRATO** no meio, com o menu escrito nele **a tinta**; o livro foi
    pra cima do pano (o pano atravessava o livro).
  - **Quadro de missões** (`qml/MedievalQuadro.qml`, 3D): muro de tijolos de pedra (cada tijolo é uma peça),
    tábuas e vigas com chapas de ferro e pregos, cartazes de papel rasgado (folhas 3D com dobrinha), mapa,
    bilhete da bússola, selos de cera, fios vermelhos, estandarte com brasão, flâmulas, espadas cruzadas,
    cordas com brasões (lobo e torre), hera de folhas 3D e a **LAMPARINA** (chama de partículas + luz tremendo).
    O menu fica no cartaz grande do meio.
  - **Botões a tinta** (`BotaoOrnado.tinta`, `Rotulo.tinta`): nos papéis do Medieval o texto é tinta marrom e
    o mouse **risca um círculo vermelho à mão** em volta da opção (`CirculoTinta.qml`, se desenhando na hora).
  - **Farol em 3D** (`qml/TerrorFarol3D.qml`): MAR com ondas de verdade (shader `qml/shaders/mar.vert/.frag`,
    espuma nas cristas), penhasco de rochas facetadas, casinha, farol com **feixe girando** (cone de luz +
    holofote que varre o mar), barco balançando no canto, chuva 3D, espuma nas pedras, raios com clarão e o
    Cthulhu no clarão. O farol 2D (`TerrorFarol.qml`) ficou só pra quem não tem placa de vídeo.
  - O menu cabe DENTRO de algo da cena (TV, contrato, cartaz): a cena expõe `tela` (retângulo medido com
    `mapFrom3DScene`) e o Lancador encolhe o menu pra caber.
  - Formas novas em `geometria3d.py`: `tela` (vidro estufado), `grade` (mar), `casco` e `conves` (barco).
  - Cuidado (aprendido aqui): animar `position.y` de um Node zera x/z — anime `y` direto.
  - Texturas 3D em cache no temp com sufixo `_v4` (suba quando mudar um desenho).
### 📦 Pacote v0.58 (pedidos combinados em 18/11 — `PEDIDOS_v0.58.md`)
Ordem combinada com o Manel: 1 → 10 do documento; depois detalhar o 3D da mesa, HUD/painéis, CÂMERA LIVRE
(360°, por etapas: girar/inclinar com o GRID como limite → névoa e luz → efeitos e clima; travada = reto de
cima como hoje), TIPOS DE TOKEN (ficha redonda ou STANDEE com a foto em pé no suporte; na visão de cima a foto
vira pra câmera; mestre escolhe um por um ou todos); depois o TUTORIAL (aventura de exemplo + dicas, botão
Tutorial pro mestre e pro jogador); testes com os amigos; publicação POR ÚLTIMO. Estética: a das telas
iniciais 3D (low-poly facetado com textura desenhada, inspirado no PS1). Desempenho: medir a cada mudança.
- **(v0.58.0) 1 · ⌨ Tela de atalhos (F1)** — `ui/atalhos.py`: F1 (mestre e jogador) e menu **Ajuda** (no
  jogador, botão "Ajuda" na barra). Grupos (Arquivo, Edição, Construção, Mesa e câmera, Tokens e visão,
  Combate, Painéis, Biblioteca, Ficha PDF, Mouse), busca, e só os atalhos do papel de quem abriu.
  Levantamento feito: **nenhuma tecla repetida dentro do mesmo papel**; as que mudam entre mestre e jogador
  (Ctrl+P projetor/ficha, E borracha/girar, Ctrl+I importar/informações, Ctrl+T atmosfera/templates; girar
  `,` `.` no mestre e Q/E no jogador) **ficam como estão** (decisão do Manel). Ctrl+D = Dados e Ctrl+E = Chat
  nos dois. O F1 do mestre funciona até na tela inicial dele. Ícone novo: teclado (⌨).
  Teste `teste_atalhos.py`: confere que cada atalho da lista existe mesmo na janela (se mudar um atalho no
  código, mude em `atalhos.py`), que não há repetidos e que a busca filtra.
- **(v0.58.9) 6 · 🌆 Futurista com 2 telas 3D** (`ui/futurista_cenas.py`, sorteio 50/50, `TAVERNA_CENA_FUTURISTA=beco|nave`):
  - **Beco de neon** (`FuturistaBeco.qml`): você está EM PÉ no beco (olho a 400 ≈ 1,70 m; 1 m ≈ 235), e o beco
    **sai numa rua de verdade** (duas mãos, faixa, calçadas, postes) por onde passam **carros em tamanho real**
    de vez em quando (faróis, lanterna, neon embaixo). Do outro lado, um **prédio de lojas**: vitrines acesas
    com prateleiras, gente, balcão, porta, caixilho de metal, tubo de neon, nome inventado e porta de enrolar
    pichada em algumas. Paredes de **concreto liso bruto** (`concreto_cyber`: placas de fôrma, furos de
    tirante, chuva escorrendo, rachaduras; o Manel: "nada de tijolinho"). **Cada opção é uma placa diferente**
    (fonte, moldura, inclinação: Bebas em tubo, terminal Consolas, script redondo, Impact com cantoneiras,
    EXIT em Courier); apagada fica fraca, o mouse LIGA piscando ("tz-tz") e a luz pinta a fachada. As placas
    são espelhadas por baixo do chão e aparecem só na **poça** (reflexo). Letreiros das paredes do beco também
    todos diferentes (vertical, lâmpadas correndo, círculo, telinha de pixel, seta, duas linhas), com
    palavras inventadas. Vapor do bueiro, fios, chuva.
  - **Cabine de nave** (`FuturistaNave.qml`): console com botõezinhos piscando e 2 radares, janela pro espaço
    com planeta com anel girando e uma **estação espacial passando devagar**; as opções são **hologramas** que
    sobem dos projetores: parados têm interferência (tremem, falham, linhas de varredura), o mouse firma.
  - Cache das texturas 3D foi pra `_v9` (texturas mudaram). Teste `teste_futurista.py`.
- **(v1.0.1) 🔔 Aviso de versão nova + projeto pronto pra manutenção** (pedido do Manel):
  - **Auditoria de segurança** do repositório e do histórico: nada sensível (só IPs de exemplo, e-mails de autores
    de fonte exigidos pela OFL, mapa de teste). Commits já usam o e-mail noreply. Nomes de teste ("Bia", "Lucia
    Andrade") — o Manel confirma se são pessoas reais; histórico NÃO foi reescrito.
  - **Aviso na tela inicial** (`taverna/atualizacao.py`): ao abrir, consulta em segundo plano a última Release do
    GitHub (`api.github.com/repos/EuManel/taverna/releases/latest`, 5 s de limite, no máximo 1 vez por dia, guarda
    em `QSettings` `atualizacao/tag` e `atualizacao/quando`). Se a tag for mais nova que `APP_VERSAO`, aparece
    "✨ Nova versão vX.Y disponível — baixar" acima da versão; o clique abre o itch.io. NUNCA baixa nada; sem
    internet fica quieto. Ignora rascunho e pre-release. Tag precisa ser `vX.Y` ou `vX.Y.Z`.
    `TAVERNA_SEM_ATUALIZACAO=1` desliga (os testes usam). Teste `teste_atualizacao.py`.
  - `CHANGELOG.md` bilíngue, modelos de issue (`.github/ISSUE_TEMPLATE/`: bug e ideia, pedindo versão, Windows,
    placa de vídeo e o .zip do "Reportar problema") e `COMO_LANCAR_VERSAO.md` (passo a passo de lançamento).
- **(v1.0.0) 🌐 Inglês + versão de release pro itch.io** (pedido do Manel):
  - **Seletor de idioma**: bandeirinhas 🇧🇷 🇺🇸 no rodapé da tela inicial, ao lado de Tema/Gráficos (desenhadas no
    Python, `lancador.bandeira`). Fica salvo (`QSettings("Taverna","Geral")["idioma"]`; `TAVERNA_IDIOMA` força).
  - **Como funciona** (`taverna/idioma.py`): o código CONTINUA em português. No inglês, `idioma.instalar(app)`
    embrulha os pontos do Qt que mostram texto (setText, tooltips, menus, combos, abas, caixas de aviso, drawText…)
    + um filtro de eventos (texto do construtor e ações). O dicionário é `taverna/idiomas/en.json`: "textos"
    (frase inteira; emoji do começo e pontuação do fim mantidos; também acha o texto sem o emoji, em MAIÚSCULAS e
    pedaço por pedaço separado por " · ") e "modelos" (f-strings: "Rodada {0}" → "Round {0}"). HTML: traduz
    entre as marcas. O que não está no dicionário (nome de token, chat, o que o usuário escreveu) fica igual.
    Texto NOVO na interface: precisa entrar no `en.json` (senão aparece em português no inglês).
  - Tela inicial (QML): `idioma.pasta_qml` faz uma cópia traduzida do QML na pasta temporária; trocar a bandeira
    recarrega a tela. Janela de mesa já aberta nesta execução só muda por inteiro reabrindo (aparece um aviso).
  - Compêndio SRD: no inglês usa os dados originais em inglês (`compendio._em_ingles`).
  - Piso "Grade" virou "Grade de metal" (pra não confundir com a grade do mapa no inglês).
  - Os testes rodam sempre em português (`rodar_testes.py` põe `TAVERNA_IDIOMA=pt`). Teste `teste_idioma.py`.
  - **Release**: `python gerar_release.py` → `release/Taverna-v1.0-windows.zip` (PASTA com Taverna.exe — onedir,
    sem console, com ícone, sem precisar de Python — + README.txt e HOW_TO_CONNECT.txt, os dois com INGLÊS
    PRIMEIRO e português depois (pedido do Manel; o COMO_CONECTAR.txt virou o HOW_TO_CONNECT.txt), LICENCAS.md).
    `gerar_exe.bat` agora chama esse script. Publicar no itch.io é com o Manel.
  - **Licença (decisão do Manel): GPL-3.0** (por causa do PyQt6, que é GPL v3), não MIT. `LICENSE` na raiz =
    texto oficial da GPL v3; `LICENSE-LGPL-3.0.txt` = LGPL v3 do Qt; créditos do PyQt6 (Riverbank) e do Qt
    (The Qt Company) no `LICENCAS.md`. Os três vão no zip.
  - **Código público no GitHub**: https://github.com/EuManel/taverna (GPL-3.0, branch `main`, commits com o
    e-mail noreply do GitHub), Release v1.0 com o zip. `.gitignore` deixa fora builds/zips, saves, saídas dos
    testes, `referencias/`, `CLAUDE.md` e `PEDIDOS_*.md`. README.md bilíngue (inglês primeiro). Git e gh
    instalados pelo winget; o gh está logado na conta EuManel.
  - No inglês, a "Porta" de rede dos diálogos de conexão sai "Port" (não "Door": `dialogos._rotulo_porta`).
  - Limites conhecidos: mensagem do servidor é montada no idioma do mestre (boa parte é traduzida em quem recebe,
    pelos modelos); fichas D&D antigas guardam o texto que estava no campo (ex.: tendência em português).
- **(v0.84.0) ⚡ Otimização sem mexer no visual + objetos na ordem certa na câmera inclinada**:
  medido na placa de vídeo (mesa com 3 salas, 14 fichas, 8 objetos, 3 tochas; script de medição fora do projeto).
  A tocha tremendo redesenha a mesa ~10×/s mesmo parada — então o que não muda entre quadros agora é guardado:
  o contorno projetado da lateral da ficha (`token._geometria_lateral`, chave = câmera + posição) e as paredes
  da frente de cada token (`altura3d._ParedesDoQuadro`: silhueta de cada parede feita UMA vez por quadro, e o
  recorte reaproveitado por quem está atrás das mesmas paredes; antes era por token × parede). O casco convexo
  (`token._casco_xy`) ficou ~2× mais rápido. Tudo conferido pixel a pixel contra o desenho antigo.
  Resultado: parado 40% → 29% de CPU (inclinado 57% → 26%); arrastando ficha 50 → 59 quadros/s; com efeitos
  134% → 100% de CPU. **Bug (Manel):** com a câmera inclinada, fichas e paredes passavam por cima dos OBJETOS
  (eles ficavam numa camada por baixo). Agora o corpo do objeto entra na mesma fila de profundidade das fichas
  (`altura3d.OBJETOS`, `PropItem.pintar_corpo_3d`) e é recortado pelas paredes da frente; no chão fica só a
  sombra. Pendurados na parede (SUSPENSOS) e o 2D/Baixo continuam como antes. Teste `teste_ordem_3d.py`.
- **(v0.83.0) 🌫 Névoa DESENHADA na cidade/mundo do jogador** (`ui/nevoa_atlas.py`; era o "pra depois" da v0.64):
  a parte coberta deixou de ser o escuro liso. Por cima do que não chegou (a imagem continua vindo só com o revelado
  — nada muda na rede nem no que o jogador pode ver) vai uma névoa no estilo do tema: **pergaminho** (medieval),
  **estática de radar** com linhas (futurista), nuvens **arroxeadas com brilhinhos** (mágico), **breu** com borda
  vermelha (terror), **fumaça** (steampunk), **poeira** (pós-apocalíptico), nuvens (moderno, claro, escuro). A beirada
  do revelado é **irregular** (desfiada/queimada) com uma faixa escura e um fio de brilho (brasa, neon, latão…).
  Gráficos: **Baixo** = como antes · **Médio** = parada · **Alto** = anda devagar (~10 quadros/s só com o atlas na
  tela; ~25 ms por quadro numa grade de até 512 px). Textura feita por FFT (repete sem emenda), sem pacote novo.
  Teste `teste_nevoa_atlas.py` (prancha dos 9 temas em `testes/saida/nevoa_atlas_temas.png`) e `teste_atlas_rede.py`.
- **(v0.82.0) 👥 Preparação do teste com os amigos**:
  - **Ensaio com 5 jogadores** (`teste_cinco_jogadores.py`): mestre + 5 jogadores pela rede local numa mesa com mapa,
    2 salas, 30 goblins. Todos veem os 5 se mexendo ao mesmo tempo, ninguém mexe no dos outros. Mandar a mesa pros 5
    custa ~3 ms pro mestre.
  - **A mesa vai COMPRIMIDA** (**protocolo 21**): medido arrastando um goblin por 2 s com 5 jogadores, o mestre
    mandava ~950 KB (~3,5 Mbps no teste; num PC rápido, o dobro — pesado pra upload de casa e pro Radmin). Agora
    mensagem grande (estado da mesa, histórico do chat, diário, fluidos, atlas) vai em binário zlib
    (`protocolo.enviar_grande`/`abrir_binaria`, com limite de 64 MB): **136 KB (7× menos, ~0,5 Mbps)**. Mensagem
    pequena continua texto. Imagens (assets) continuam iguais.
  - **`TESTE_COM_AMIGOS.md`**: roteiro do Manel pro teste (antes, o que marcar durante, e "Reportar problema" pra
    mandar os .zip).
- **(v0.81.1) 📦 .exe conferido de verdade** (no PC do Manel, 20/11/2026): o `gerar_exe.bat` gera o `Taverna.exe`
  (~240 MB, ~1,5 min) com Python 3.15 + PyInstaller 6.22. Aberto 2 vezes: tela inicial 3D ok (~9 s pra abrir, é o
  onefile se descompactando), **Mestre** (nova sessão → mesa → Abrir taverna; o UPnP disse "Só pela rede
  local/Radmin" na rede do Manel) e **Jogador** (Entrar na sessão → conectou, mesa e dicas apareceram); o botão
  **❓ Como conectar** abriu o `COMO_CONECTAR.txt` no Bloco de Notas; nada no `erros.log`.
  - 🐛 Achado no teste: "Nova sessão" e "Entrar na sessão" abriam no MONITOR PRINCIPAL (o pai delas é a janela do
    Mestre/Jogador, ainda escondida). Agora toda janelinha de pai escondido abre centrada na janela do Taverna que
    está aparecendo (`lancador._CentrarDialogos`). Conferido com 2 monitores; teste em `teste_lancador.py`.
  - Ainda não conferido: o .exe num PC SEM Python (de um amigo) e música do YouTube/som dentro do .exe.
- **(v0.81.0) 📄 Documento de conexão** (pedido do Manel: UPnP → Radmin "MUITO claro" no programa e na pasta do
  jogo): **`COMO_CONECTAR.txt`** na raiz — abrir a taverna, o código TAV- (deu certo) ou "Só pela rede local/Radmin"
  (não deu), entrar como jogador, por que falha (CGNAT, UPnP desligado), Radmin passo a passo, mesma casa, e "não
  conectou?". O `gerar_exe.bat` põe ele dentro do .exe E do lado dele na `dist`. Botão **❓ Como conectar** no "Abrir
  taverna", no "Entrar na sessão" e no aviso de que a internet não abriu (`dialogos.abrir_como_conectar`: procura do
  lado do .exe, dentro do .exe, ou na raiz). README seção 3 atualizada. Teste `teste_como_conectar.py`.
- **(v0.80.0) Pendências pequenas da câmera livre**:
  - **Letra do token em pé**: a inicial (token sem imagem) girava junto com a câmera; agora sai da imagem guardada do
    topo e é desenhada desvirada (`_pintar_letra`), sempre legível — de cima, girada ou inclinada.
  - **Fogo da explosão preso no chão**: no 3D a bola de fogo subia ~1,4 R e parecia solta no ar. Agora é mais baixa
    e cada bolha é desenhada em camadas do chão até o alto (parece uma coluna saindo do chão); fagulhas e fumaça
    também mais baixas (ponto mais alto 0,88 R; antes ~2,7 R com a fumaça).
  - **Entrar em "Ver pelos olhos"**: a câmera DESLIZA até a posição em ~0,3 s em vez de pular (os quadros do meio vão
    no modo leve "em movimento"). Engasgo medido na placa de vídeo: ~0,6 s → ~0,2 s (a 1ª vez depois de abrir o
    programa ainda pode demorar mais, montando as texturas do relevo).
  - Testes `teste_pendencias_080.py` e `teste_pelos_olhos.py` (desliza, não pula).
- **(v0.79.0) 🔥 Status com partículas** (pedido do Manel): token com status solta partículas em volta, além do
  simbolozinho em cima. Vale o **Efeito em cima** do token (fogo, veneno, ácido, gelo, elétrico, água = molhado, luz,
  planta) e as **condições** em Informações (queimando, envenenado, congelado, molhado, sangrando, abençoado,
  paralisado). Usa as mesmas partículas das áreas (`efeitos3d.desenhar_status`, chamado em `altura3d._cartoes` logo
  depois do corpo do token, então respeita a ordem de profundidade e as paredes na frente). Sangrando = gotas
  vermelhas caindo + manchinhas no chão; molhado = pingos azuis. Respeita Gráficos (Baixo não tem, Médio metade) e a
  condição escondida do jogador não aparece pra ele. O token fica animando enquanto tiver status. Teste
  `teste_status_particulas.py`.
- **(v0.78.0) ♟ Escala da imagem do standee** (pedido do Manel): **Editar token → Escala da imagem** (30% a 300%,
  aparece quando a peça é standee) — muda o tamanho da foto em pé (câmera livre) e deitada (travada). Vai pela rede
  (**protocolo 20**, campo `se`), fica salva e na biblioteca de tokens. Teste em `teste_standee.py`.
- **(v0.77.1) ♟ Standee do jeito do Manel**:
  - **Câmera TRAVADA** (de cima): a foto fica DEITADA, virada pra cima (pra câmera), centrada no token.
  - **Câmera LIVRE**: a foto fica EM PÉ de verdade num suporte, parada no mundo, virada pra onde o token olha
    (`pintar_cartao_no_mundo`: a face pronta numa imagem e colada num retângulo 3D com perspectiva). De lado fica
    fininha; de costas aparece o verso (a imagem espelhada, um pouco mais escura). A ficha é igual nas duas câmeras.
  - **"Sem bordas"** (Editar token, aparece quando a peça é standee): só a imagem — sem moldura, fundo, verniz,
    suporte e base —, na proporção do PNG, em pé direto no chão: pra usar PNG recortado como personagem no cenário.
    Vai pela rede (**protocolo 19**, campo `sb`), fica salvo e na biblioteca de tokens.
- **(v0.77.0) Pedidos do Manel em cima da v0.76**:
  - 🐛 **Textura da parede "dando zoom"** com a câmera inclinada: a textura era colada em cada face com uma conta
    afim (boa pra paralelogramo), e a parede comprida vira TRAPÉZIO em perspectiva — a escala da ponta perto valia
    pra face toda. Agora, inclinada, a textura vai com perspectiva de verdade, canto a canto (`QTransform.quadToQuad`).
  - **Barra de menu** (Arquivo, Editar…): cada item é uma plaquinha escura com aro de metal (losangos no Alto), na fonte
    dos títulos do tema; acende com o mouse.
  - **Títulos dos painéis**: viraram uma PLACA inteira no tamanho do painel (`hud.placa_titulo`) — moldura de metal,
    MEDALHÃO com o ícone, nome GRAVADO (sombra + metal na letra), filete de metal afinando até a divisória antes do
    fechar, rebites/losangos no Alto (gemas no Mágico, neon no Futurista).
- **(v0.76.1) 🐛 Token de trás aparecendo por cima do da frente** (achado pelo Manel, câmera inclinada): cada token era
  desenhado na ordem fixa da camada. Agora o CORPO 3D da ficha (lateral, topo, nome) vai pra camada das coisas altas
  junto com os standees, desenhado do mais LONGE pro mais PERTO da câmera e recortado só pelas paredes entre a câmera e
  ele (`TokenItem.pintar_corpo_3d`, `altura3d._cartoes`); no chão fica só a sombra. A placa do nome agora fica sempre
  EMBAIXO na tela (girada 180° ela ia pra cima). Teste em `teste_standee.py` (ordem de desenho).
- **(v0.76.0) ⚡ OTIMIZAÇÃO MEDIDA (câmera livre)** — medido na placa de vídeo do Manel (2º monitor), cena pesada (3 salas,
  12 tokens com standees, 8 objetos, 3 tochas, penumbra, área de fogo), câmera inclinada GIRANDO sem parar:
  | | antes | depois |
  |---|---|---|
  | inclinada | 20,5 fps, engasgos ~300 ms | **31 fps**, engasgos 90–130 ms |
  | com chuva | 16 fps | **22 fps** (engasgos 330 → ~120 ms) |
  | pelos olhos | 16 fps (engasgo de 1,2 s) | **22–28 fps** (engasgo ao entrar ~0,6 s) |
  - **Bug**: os títulos dos painéis se redesenhavam em CICLO (o ícone de fechar era trocado dentro do próprio desenho
    e pedia outro) — pesava até com a mesa parada.
  - Luz/sombra em **meia resolução** (é macia); lateral dos tokens e das paredes/portas com as quinas projetadas **de uma
    vez** (numpy); topo das fichas e retratos do grupo **guardados prontos** (só refaz quando mudam); chuva em **lotes**.
  - **Qualidade adaptativa** (`camera3d.em_movimento`): com a câmera mexendo, objetos com metade das camadas, luz em 1/3
    da resolução sem penumbra extra, maçaneta/dobradiças puladas; 0,18 s depois de parar redesenha com tudo.
  - Piso com a câmera inclinada: resolução **por pedaço** (longe em baixa), em vez de uma só pra tela toda.
  - **60 fps não chegou**: com a câmera mexendo, a mesa inteira é redesenhada em Python a cada quadro. Pra 60 de verdade,
    só com o renderizador 3D próprio (ModernGL) — fica anotado. Parada, a mesa só redesenha o que anima.
    Teste `teste_otimizacao.py`.
- **(v0.75.0) 👁 "PELOS OLHOS DE…" — câmera por cima do ombro** (o caminho 1 combinado com o Manel; a primeira pessoa
  de verdade fica pra quando a mesa tiver um renderizador 3D próprio, se este não bastar):
  - **Botão direito no token → 👁 Ver pelos olhos** (jogador no dele, mestre em qualquer um): a câmera vai pra TRÁS do
    token, mais baixa (`camera3d.ALTURA_OLHOS_TELAS`) e bem deitada (72°), virada pra onde ele olha, e ACOMPANHA
    suave quando ele anda ou gira (Q/E). Sai com **Esc**, arrastando a visão, Alt+arrastar ou o clique duplo na
    bússola — e a câmera volta exatamente como estava.
  - **Horizonte na tela**: céu em cima (dia azulado, penumbra azul-escura, escuro quase preto — `drawBackground`) e
    uma faixa fina de névoa ao longe (`_nevoa_horizonte`). O chão "visível" corta logo abaixo do horizonte
    (`linha_horizonte`), e o que fica atrás da câmera não é desenhado (`Camera.na_frente`).
  - **CORTE** (como nos jogos): pedaço de parede (~1 m), topo de parede e tronco de paliçada com o pé ENTRE a câmera e
    o token não aparecem (`corte_y`) — a parede de trás não tapa mais a tela.
  - Conferido na placa de vídeo (2º monitor), de dia e no escuro com tocha. Teste `teste_pelos_olhos.py` (pegou: o
    Esc era pego por um atalho da janela antes de chegar na mesa).
- **(v0.74.0) 🎨 MEUS DADOS — cada um personaliza os seus dados 3D** (`dados3d/visual.py`, `ui/dialogo_meus_dados.py`):
  - Botão 🎨 no painel de **Dados** (mestre e jogador): **material** — do tema da mesa (o de sempre), osso, plástico,
    fosco (borracha), **pedra**, **mármore**, **madeira**, **ferro (com ferrugem)**, latão, **ouro**, **prata**, vidro,
    **cristal**, gema, **obsidiana** (cada um com a sua textura por cima: grão, veios, anéis da madeira, ferrugem,
    polimento…; ouro/prata/ferro/latão com brilho COLORIDO de metal) —, **cor do corpo**, **cor dos números**,
    **Translúcido** (em qualquer material — o Manel pediu) e **Brilho** (fosco ↔ polido), com PRÉVIA de um d20 e
    um d6 de verdade (o desenho simples dos dados agora também mostra a textura do material). Fica salvo no PC.
  - ⚠ Achado: os testes que "isolavam" as preferências com `QSettings.setDefaultFormat` NÃO isolavam no Windows (as
    preferências com nome continuam no registro). O teste dos dados agora usa um arquivo de verdade (`visual._config`).
  - A escolha vai JUNTO com cada rolagem (`dv` — **protocolo 18**): todo mundo vê os seus dados do seu jeito e os dos
    outros do jeito deles (o servidor confere material e cores; o mestre usa a dele). Sem escolha, os dados seguem o
    tema de quem está olhando, como antes. Material = brilho + translúcido + a textura de desgaste de um tema
    (osso = a do medieval, metal = pátina do steampunk, gema = veios do mágico…).
  - Conferido na placa de vídeo (gema verde translúcida, metal prateado). Teste `teste_meus_dados.py`.
- **(v0.73.0) ♟ TIPOS DE TOKEN — ficha redonda ou STANDEE** (item da ordem combinada, depois da câmera livre):
  - **Standee**: base escura no chão com o anel da cor do tipo e a IMAGEM do token num cartão em pé num suporte,
    sempre virado pra câmera (de cima ou inclinada); altura ~1,75 m pra médio, crescendo com o tamanho; sem imagem,
    o cartão mostra a cor e a inicial. Selecionado: moldura dourada.
  - **Quem escolhe**: o mestre — **Editar token → Peça (3D)** (um por um; também na biblioteca de tokens) ou **Mesa →
    Peças dos tokens** → todos como ficha/standee. Vai pela rede (**protocolo 17**, campo `es`) e fica salvo.
  - **Profundidade**: as paredes são desenhadas por cima dos tokens, então a parede do FUNDO cortava o cartão. Agora o
    cartão é desenhado pela camada das coisas altas (`altura3d._cartoes`), depois das paredes, do mais longe pro mais
    perto, e recortado SÓ pelas paredes que estão entre a câmera e o token (`_na_frente`) — a da frente continua
    escondendo quem está atrás dela.
  - **Nome de pé**: com a câmera inclinada, a placa do nome (ficha e standee) fica de pé na tela, legível (antes
    ficava deitada no chão).
  - Conferido na placa de vídeo (2º monitor). Teste `teste_standee.py` (pegou um bug: com duas cenas no mesmo
    programa — mestre e jogador — uma tirava da lista os standees da outra).
- **(v0.72.0) 🎥 CÂMERA LIVRE — etapa 3 de 3: efeitos e clima** (fecha a câmera livre):
  - **Clima** (`ui/clima.py`): tinha a sua própria câmera "de cima" e acompanhava o mapa só por posição e zoom.
    Agora usa a mesma câmera da mesa (`_camera`: zoom, giro, posição e inclinação da visão): as partículas
    acompanham o mapa também no GIRO, nascem no chão que aparece na tela (inclinada vai bem mais longe — e vem mais
    chuva/neve pra cobrir), e a projeção tem a perspectiva (a chuva cai reta em 3D; o raio desce do alto). O
    respingo fica deitado no chão, em perspectiva. De cima, a conta é idêntica à de antes.
  - **Impactos, lançamentos e partículas das áreas** já usavam a `camera3d` (v0.70): conferidos inclinados — a
    explosão com a onda de choque no chão e o fogo/fumaça subindo, a bola de fogo voando até o alvo.
  - Conferido na placa de vídeo de verdade (2º monitor). Teste `teste_camera_clima.py`.
- **(v0.71.0) 🎥 CÂMERA LIVRE — etapa 2 de 3: névoa e luz inclinadas**:
  - **Névoa de guerra no 3D** (tela do jogador): a névoa é "tinta no chão" e, inclinada, o alto das paredes caía em
    cima do chão de TRÁS delas — pegava a névoa errada e o topo de parede de sala NÃO explorada aparecia (entregava o
    mapa). Agora o corpo 3D consulta a névoa (`NevoaItem.amostrar`, `camera3d.nevoa_da_cena`/`nevoa_da_parede`):
    uma parede é conhecida se o chão de QUALQUER lado dela já foi visto (a face de fora da parede da frente também
    aparece); cada face em pedaços de ~1 m (pedaço nunca visto nem é desenhado, já explorado fica escurecido); o topo
    de cada parede pega a névoa dos lados dela; paliçada, porta e objeto num lugar nunca visto não aparecem. O escuro
    (penumbra/escuro com tocha) vem junto, porque a névoa do jogador já leva a luz em conta.
  - **Neblina e gás volumétricos inclinados**: o raio de cada pixel agora sai do PÉ da câmera (`pe_cena`) até a altura
    dela (D·cos θ) — antes supunha a câmera em cima do centro da tela. Voltaram a ser volumétricos com a câmera
    inclinada (na v0.70 caíam no desenho em camadas).
  - Luz: o chão iluminado e as tochas "lambendo" as paredes já funcionavam inclinados (conferido na placa).
  - Conferido na placa de vídeo de verdade (2º monitor), na tela do jogador. Teste `teste_camera_nevoa.py`.
  - Falta (etapa 3): efeitos e clima (chuva, partículas, impactos, lançamentos) com a câmera inclinada.
  - **Visão padrão do token = CONE DE 60° pra frente, 24 m** (o Manel: "360 não faz sentido, senão eu não faria a
    mesa"; era 180°). Atalhos no painel: Normal (60°), Visão no escuro (60° + 18 m), Amplo (180°), Visão total (360°).
    Token salvo com o padrão antigo (180° e 24 m) passa pro novo ao abrir; quem o mestre mudou fica como está.
- **(v0.70.0) 🎥 CÂMERA LIVRE — etapa 1 de 3: girar e inclinar** (`mesa/visao.py`, `mesa/camera3d.py`, `mesa/bussola.py`):
  - **🧭 Bússola** no canto de baixo à direita da mesa (mestre e jogador, cada um mexe na sua câmera): **cadeado** =
    TRAVADA (reto de cima, exatamente como antes — o padrão) ou LIVRE; arrastar nela gira (pro lado) e inclina (pra
    cima/baixo); rodinha inclina; ◀ ▶ giram 45°; clique duplo volta pro reto de cima. Na mesa: **Alt+arrastar**.
    A agulha aponta pro norte da mesa e o anel mostra a inclinação. (No F1.)
  - **Como funciona**: a visão guarda centro, zoom, giro e inclinação e monta uma transformação em PERSPECTIVA
    (homografia — `camera3d.homografia`); o chão (piso, grid, mapas, névoa, luz) fica em perspectiva sozinho e os
    cliques caem no ponto certo do chão. A `camera3d` ganhou a projeção 3D de verdade (câmera atrás e acima do centro):
    paredes com textura, portas, paliçada, objetos com pernas e tokens ficam **em pé** do jeito certo; as faces que
    aparecem são as viradas pra onde a câmera ESTÁ (`pe_cena`). Com inclinação 0 as contas são idênticas às de antes.
  - **O grid é o limite**: inclinação até 55° (o horizonte nunca entra na tela). **Afastando muito** (cidade/mundo do
    atlas) a câmera volta a ficar de cima sozinha.
  - Itens "infinitos" (grid, paredes 3D, névoa, luz, desenhos, gás) e mapas grandes: inclinada, o Qt não desenhava
    o que passava por trás da câmera — agora eles ocupam só o chão visível (`camera3d.limitar`).
  - Placa de vídeo: piso com relevo e áreas de efeito com a matriz em perspectiva (`camera3d.mvp`) — conferido na
    placa de verdade (2º monitor). Neblina volumétrica e gás volumétrico usam o desenho em camadas quando a câmera
    está inclinada (o volumétrico inclinado é a **etapa 2: névoa e luz**). **Etapa 3: efeitos e clima.**
  - Escala com a mesa girada: grid, terreno, atlas e clima liam o zoom do `m11` (girada dava 0 ou negativo).
  - Teste `teste_camera_livre.py` (capturas `testes/saida/camera_*.png`).
  - 🐛 (achado pelo Manel) **Token virava um "balde"** com a câmera inclinada: a lateral da ficha era desenhada com
    círculos na tela (de cima dava certo). Agora a base e o topo são PROJETADOS e o corpo é o contorno dos dois
    (`token._casco`); o filete de cima segue a elipse em perspectiva.
- **(v0.69.1) 🐛 Área de efeito vazando pra fora da sala (só na placa de vídeo)** — a máscara que diz ao shader onde a
  área existe era guardada só por forma/tamanho (`efeitos_gl.mascara`): duas áreas do mesmo tamanho (ou uma apagada
  e outra nova) pegavam a máscara uma da outra, com o recorte de OUTRO lugar, e o fogo aparecia fora da sala. Agora
  a chave é a área + onde ela está. Teste `teste_area_mascara.py` (com a chave antiga ele falha).
- **(v0.69.0) 🛡 HUD de METAL** (a "última passada nos gráficos": HUD/painéis; `ui/hud.py`):
  - A interface da mesa ganhou as peças de **metal de verdade** da tela inicial (`estilizado.metal`, reflexo, não
    degradê): barra de ferramentas e menu com **trilho de metal** (rebites/losango no Alto; a barra da esquerda tem o
    trilho do lado), barra de status, **botões** com aro de metal (normal, mouse em cima com brilho, apertado,
    marcado, desligado), botão principal mais grosso (losangos/gemas no Alto), botões da barra só ganham o aro com o
    mouse ou marcados, **abas**, **molduras dos painéis e dos menus** (cantoneiras em L no Alto), **título dos
    painéis** numa placa com trilho e ornamento (`acabamento.TituloPainel` desenha a peça), **slider** com pino de
    metal e gema, **caixinhas de marcar** de metal (também nas listas, ex.: Camadas), barra de rolagem de metal.
  - **Cada tema com o seu jeito** (`hud.JEITO`): forma do canto (ponta/chanfro/redondo), ornamento (losango,
    prego, neon, parafuso, gema, rebite) e **ferrugem** no Terror e no Pós-apocalíptico; linha de **neon** no
    Futurista, **gemas acesas** no Mágico.
  - **Segue os Gráficos**: Baixo = liso como antes · Médio = aro fino discreto · Alto = metal grosso + ornamentos +
    brilho. Trocar o nível muda na hora (`tema._ligar_graficos`). **Claro e Escuro** continuam lisos ("de programa").
  - Campos de texto ficaram lisos (com cantoneira em todo campo ficou poluído).
  - Imagens pequenas feitas uma vez (no dobro, nítidas com zoom do Windows) em `Documentos/Taverna/cache/hud_v1`.
    Teste `teste_hud.py` (capturas `testes/saida/hud_terror_*.png`).
- **(v0.68.0) 🧱 Piso detalhado** (fecha a frente "detalhar o 3D": portas, grade, paliçada, objetos e piso):
  - **Texturas de chão no dobro da resolução** (`mesa/texturas.py`: `ESCALA_CHAO = 2`, `ESC` durante a geração): os
    ~26 chãos do gerador (pedra, paralelepípedo, madeira, tábuas velhas, mármore, cerâmica, metal, terra, grama…) saem
    com 2 px por unidade e o MESMO desenho — as medidas (células do ruído, pedras, juntas, tábuas, rebites) crescem
    junto e o Voronoi devolve a distância "em medida de 1×"; só o grão fininho não cresce, e vira o detalhe a mais.
    O Voronoi agora é calculado em faixas (no dobro, de uma vez, passava de meio giga). Gerar todos leva ~13 s
    uma vez só (cache no disco foi pra `texturas_v3`). Chãos "desenhados" (runas, xadrez…) seguem em 1×.
  - **Pincel na medida certa** (`materiais.pincel_chao`/`escala_chao`): 1 quadrado da textura = 1 quadrado da mesa.
  - **Zoom perto = azulejo detalhado** (`construcao.TerrenoItem`, nível 2 = 2 px por unidade): com zoom ≥ 1,2 e
    Gráficos Médio/Alto o piso é montado em alta, então a pedra e a madeira ficam nítidas em vez de borrar. No
    Baixo continua como antes.
  - Teste `teste_piso.py` (capturas `testes/saida/piso_zoom*.png`).
- **(v0.67.1) 🪑 Objetos na Mesa 3D mais detalhados** (`mesa/props.py`):
  - **Móveis com pernas**: mesa, mesa grande, de banquete, escrivaninha, banco, cadeira, mesa de alquimia, de tortura,
    bancada de engrenagens = TAMPO (só a parte de cima é "maciça") + **quatro pés** embaixo, na cor do móvel; mesa
    redonda, holomesa e pedestal do orbe = **um pé no centro** (`PERNAS`, `_pes`). Antes era um bloco até o chão.
  - **Faixas de material nas laterais** (`FAIXAS`): aros de ferro no barril e no tambor, ferragem e a fresta da tampa
    no baú, frestas no caixote, fiadas de pedra no pilar/lareira/forja/altar, prateleiras na estante, faixas de luz
    azul no servidor/terminal/reator, etc.
  - **Piso**: ficou pra depois (precisa refazer os ~35 geradores de chão no dobro da resolução + azulejos em alta no
    zoom perto — só aí ganha detalhe de verdade). Teste `teste_objetos3d.py`.- **(v0.67.0) 🚪 Mesa 3D detalhada — portas, grade e paliçada** (pedido do Manel: "porta com textura e maçaneta
  certa, grade vazada, paliçada de troncos cilíndricos"):
  - **Textura nas folhas** (`mesa/texturas_porta.py`, 4 px por unidade, bem nítida): madeira = tábuas com veio e
    duas faixas de ferro rebitadas · pedra = laje com moldura entalhada e símbolo · metal = chapas de aço escovado
    com costuras, rebites e ferrugem · mecânica = painéis de nave, costura no meio, faixa amarela e preta e luzinha ·
    cortina = dobras e franja dourada · persiana = lâminas. (`camera3d.desenhar_laterais` ganhou `escala_tex`.)
  - **Maçaneta** (latão; ferro na de pedra) no lado LIVRE da folha a ~1 m do chão, com o espelho embaixo, e **duas
    dobradiças** no lado da dobradiça — só na face virada pra câmera (a de trás "atravessava" a folha). Giram junto.
  - **Grade levadiça vazada**: barras de verdade (uma a cada ~14 cm) + 3 travessas, subindo juntas ao abrir.
  - **Paliçada**: no 3D vira uma fileira de **troncos redondos** (octógono com luz, casca com musgo embaixo),
    alturas um pouco diferentes (sempre as mesmas) e **ponta afiada** (madeira lascada), desenhados do mais longe
    pro mais perto. O "topo chato" de parede não é desenhado nela. (`ParedesItem.troncos`, `construcao.TRONCOS`.)
  - Prevenção: o piso com relevo também volta pra `GL_TEXTURE0` (o mesmo bug da tela preta da v0.65.1).
  - Teste `teste_portas3d.py` (captura em `testes/saida/portas3d.png`). **Falta** dessa frente: piso e objetos.- **(v0.66.0) 💡 Dicas de primeiro acesso** (item 11 dos PEDIDOS_v0.58 — **só as dicas: o Manel decidiu NÃO ter
  aventura de exemplo**; `ui/dicas.py`):
  - Na primeira vez que a mesa aparece (mestre e jogador, cada um com as suas, 8 passos), a janela escurece, a coisa
    explicada fica DESTACADA (recorte com borda dourada) e um balão explica, com **Anterior / Próxima / Pular**
    (Esc pula, Enter/→ avança, ← volta; as teclas do tour vêm antes dos atalhos da janela). Uma vez só (guardado nas
    preferências); **Ajuda → "Dicas de primeiro acesso"** reabre.
  - Mestre: barra de ferramentas, botão direito na mesa, zoom/arrastar/régua/ping/"todos olhem", construir (porta
    presa, Excluir porta), Abrir taverna + código da sala, cidade e mundo, F1. Jogador: criar/editar o próprio token,
    andar (Q/E/F/C), botão direito no token, régua e ping, combate (iniciativa, Encerrar meu turno), zoom out pra
    cidade/mundo, F1.
  - O botão "Criar meu token" do jogador ganhou ícone e nome curto como os outros (aparecia um ☒).
  - Nos testes sem tela as dicas não abrem sozinhas. Teste `teste_dicas.py` (preferências temporárias).- **(v0.65.1) Correções e pedidos do Manel**
  - **Erro ao fechar o .exe** ("'NoneType' object has no attribute 'flush'"): no .exe sem console não existe
    stdout/stderr. `taverna.py` e a rede de segurança (`seguranca.py`) agora conferem antes — a rede de segurança
    caía junto com qualquer erro no .exe, e o programa fechava em vez de anotar o erro.
  - **Jogador encerra o próprio turno**: no painel de combate dele aparece "Encerrar meu turno ▶" quando é a vez de
    um token DELE (o mestre confere; fora da vez dele não passa nada). Protocolo **16** ("encerrar_turno").
  - **Iniciativa só aparece depois do dado**: a rolagem agora sai ANTES do estado novo do combate, e enquanto o
    dado de iniciativa está rolando a lista (jogador e mestre) e a faixa de retratos mostram "…"; o número aparece
    quando o dado para (`painel_combate.INI_ROLANDO`).
  - **Falha crítica sem tela preta**: era a placa de vídeo — o desgaste dos dados (v0.59) deixava a unidade de
    textura 1 ativa, e TODA imagem/degradê que o QPainter desenhava depois saía preta (a borda vermelha virava a
    tela inteira preta, a fumaça virava bolotas pretas; o 20 natural também perdia o brilho). `render_gl` volta
    pra `GL_TEXTURE0`. Conferido na placa de vídeo, quadro a quadro.
  - **Fumaça com volume** (`dados3d/efeitos_critico.py`): bolotas geradas com ruído fractal, iluminadas de cima
    (topo claro, barriga escura), girando, crescendo e subindo por trás do dado. **Rachado com profundidade**: fendas
    que afinam até a ponta, fundo escuro com um fio de brasa, borda iluminada de um lado e sombreada do outro,
    galhinhos e lascas pulando; começam na borda do dado (o rachado é no chão). Tudo desenhado numa imagem comum e
    colado depois. Testes `teste_turno_jogador.py`, `teste_critico.py` (prancha em `testes/saida/falha_critica.png`).- **(v0.65.0) 🌐 Entrar sem Radmin** (item 10 dos PEDIDOS_v0.58; `rede/upnp.py`, feito à mão com socket/urllib):
  - Ao **Abrir taverna**, o Taverna pede pro ROTEADOR abrir a porta sozinho (UPnP: SSDP acha o roteador, SOAP
    pergunta o IP de fora e abre a porta), numa thread (não trava a tela). A porta abre por 12 h e **fecha** ao
    fechar a taverna, ao voltar pro início e ao fechar o programa.
  - Deu certo → na barra de baixo aparece **"Aberta pela internet · TAV-XXXXX-XXXXX"**: o **código da sala** (IP de
    fora + porta em 10 letras/números, sem I/L/O/U). Clicando: explica e **copia o código**. O jogador cola o código
    no "Entrar na sessão" (campo "Código ou IP"; aceita também IP e "IP:porta").
  - Não deu → **"Só pela rede local/Radmin (clique)"**, com o motivo e o passo a passo do Radmin. **CGNAT**
    (o roteador diz um IP 100.64.x/privado — comum nas operadoras do Brasil): avisa claro que a internet da pessoa
    não recebe conexões e que o caminho é o Radmin. Botão "Tentar de novo". O Radmin continua funcionando igual.
  - Teste `teste_upnp.py` com um **roteador falso** (SSDP + HTTP/SOAP em 127.0.0.1). ⚠ **Falta testar de verdade
    com um amigo FORA da rede do Manel** (e ver se o roteador dele tem UPnP ligado).- **(v0.64.1) Pedidos do Manel: token do jogador e ponteiro por tema**
  - **Jogador cria o PRÓPRIO token** (botão "✏ Criar meu token" na barra dele): um só, sempre tipo jogador, tamanho
    1, dono = ele; nasce onde ele está olhando (dentro do cenário). Se ele já tem token em QUALQUER aba, o mestre
    recusa — nem forçando a mensagem dá pra criar outro, nem de outro tipo/dono (protocolo **15**, "criar_token").
  - **Jogador edita o dele**: o botão vira "✏ Editar meu token", e o **duplo clique no próprio token** também abre
    (antes só tinha o botão direito exatamente em cima do token). O mestre agora acha o token em qualquer andar/aba.
  - **Mestre**: botão direito num token de jogador → "🧙 Dar este token pra…" (os jogadores conectados) — se o token
    foi criado sem o campo Jogador (dono), o jogador não conseguia mexer nele.
  - **Ponteiro do mouse por tema** (`mesa/luva.py`), sempre na cor do jogador (e é o mesmo que os outros veem andando
    na mesa): medieval = luvinha · futurista = seta holográfica neon · steampunk = ponteiro de latão com engrenagem ·
    terror = punhal ritual com sangue · mágico = varinha com cristal e faíscas · moderno = seta lisa · pós-apocalíptico
    = seta de chapa enferrujada com fita adesiva · claro = seta com contorno escuro · escuro = seta grafite com
    contorno brilhando. Trocar o tema troca o ponteiro na hora (`tema.gerar_qss` → `cursor_global.atualizar_tema`).
    Prancha em `testes/saida/cursores_temas.png`. Testes `teste_token_jogador.py` e `teste_cursores.py`.- **(v0.64.0) 🌍 Mesa → Cidade → Mundo — etapa 3 de 3: névoa e jogadores pela rede** (item 9 CONCLUÍDO):
  - **Névoa na cidade E no mundo** (decisão do Manel): máscara por mapa (`mesa/atlas.py`, até 1024 px no lado
    maior, salva na aventura como PNG cinza). Começa tudo coberto. **O grupo revela em volta de onde está** (os
    tokens andaram/mudaram de aba → 0,4 s depois) **e por onde viaja** (arrastando o alfinete). Raio configurável
    ("Raio que o grupo revela…", em m/km se a escala estiver calibrada). O mestre vê através (escurecido).
  - **Pincel do mestre** (botão direito no mapa → "Pincel: revelar" / "Pincel: cobrir"), "Revelar o mapa todo",
    "Cobrir o mapa todo", "Névoa ligada" (desligada = os jogadores veem o mapa inteiro).
  - **Jogadores** (`rede/atlas_rede.py` no mestre, `ui/atlas_jogador.py` no jogador): cada um recebe só a cidade da
    aba onde está o token dele (e o mundo, se a cidade estiver nele), o lugar dele, o chão da aba (o encaixe fica
    igual ao do mestre) e os marcadores que estão em parte revelada. A imagem vai em **pedaços de 256 px, só os que
    têm algo revelado, com a parte coberta APAGADA** — o que está na névoa nunca sai do PC do mestre; quando a névoa
    muda, só vão os pedaços que mudaram. Eles sobem dando zoom out (e pelos botões Mesa · Cidade · Mundo) e **só
    olham**: não arrastam o alfinete, não pintam, não trocam de aba. Régua (M) funciona pra eles também.
  - Protocolo **14** (`"atlas"`, `"atlas_pedaco"`). O servidor manda quando o jogador entra e quando algo muda.
    Teste `teste_atlas_rede.py` (mestre + jogador pela rede local).
  - Pra depois (se o Manel quiser): a névoa do jogador é só escuro liso — dá pra fazer uma névoa desenhada
    (nuvens/pergaminho) no tema.- **(v0.63.0) 🌍 Mesa → Cidade → Mundo — etapa 2 de 3: marcador do grupo e viagem** (`ui/atlas_visao.py`):
  - **Marcador automático**: com todos os tokens de JOGADOR na mesma aba (ou prédio) aparece UM alfinete dourado
    "Grupo"; separados, um alfinete por jogador **na cor do token**. Na cidade ele fica no lugar exato do token
    (o encaixe da aba ao contrário); no mundo, em cima da cidade. Criaturas/NPCs não contam.
  - **Viagem**: o mestre ARRASTA o alfinete na cidade ou no mundo; aparece a linha de onde saiu e a distância
    (m/km pela escala calibrada). Fica o **rastro** do caminho (tracejado dourado, só o mestre vê) — a névoa da
    etapa 3 vai revelar por ele. Se o grupo mudar de aba, o alfinete volta pro automático. Botão direito:
    "Voltar pro lugar dos tokens", "Apagar o rastro deste mapa", "Montar cidade e mundo…".
  - **Régua (segure M)** na cidade e no mundo, na unidade do nível ("350 m", "1,5 km", "40 km"); sem escala
    calibrada, avisa.
  - Viagem e rastro salvos na aventura (`atlas.viagem`, `atlas.rastros`). Teste `teste_atlas_viagem.py`.
  - **Falta**: etapa 3 (névoa da cidade e do mundo + jogadores vendo pela rede).- **(v0.62.0) 🌍 Mesa → Cidade → Mundo — etapa 1 de 3: montagem e navegação do mestre** (item 9 dos PEDIDOS_v0.58;
  o Manel decidiu: **a cidade TEM névoa**, igual ao mundo — fica pra etapa 3).
  - **Montar** (Mesa → Cidade e mundo, `ui/janela_atlas.py`): importa a imagem do mundo e de cada cidade; ferramenta
    **Marcar lugar** (retângulo → qual ABA fica ali; as abas de um prédio contam como um lugar só) e no mundo
    (retângulo → qual CIDADE); **Calibrar escala** (linha → quantos m/km ela mede). Lista dos lugares, remover.
  - **Modelo e contas** em `mesa/atlas.py`: o retângulo do lugar é ENCAIXADO no chão da aba (e o da cidade na
    imagem da cidade inteira), então trocar de nível é só trocar de referencial — a imagem não pula.
  - **Zoom contínuo** (`ui/atlas_visao.py`, camada por cima da mesa): afastando, o cenário encolhe e a cidade
    aparece em volta (mistura); a mistura começa quando o cenário ocupa **metade** da tela e termina em **1/3**
    (o "cabe na tela" da especificação deixava a cidade aparecendo já no "enquadrar tudo", que deixa a sala em
    ~57% por causa da folga do 3D). Daí a câmera passa pra cidade; mais zoom out = mundo (mesma regra), e o
    mundo para quando cabe inteiro na tela (centralizado). Zoom in num lugar desce pra AQUELA aba (troca de aba
    sozinho) e o zoom continua na mesa. Histerese de 12%. Duplo clique num lugar/cidade também desce.
  - **Botões Mesa · Cidade · Mundo** no canto de cima da mesa (animação rápida de zoom).
  - Salvo na aventura (`"atlas"`) e no pacote (imagens em `imagens/Mapas`). Teste `teste_atlas.py`.
  - **Falta**: etapa 2 (marcador do grupo automático + viagem com distância em m/km, régua por nível) e etapa 3
    (névoa da cidade e do mundo com pincel + jogadores vendo pela rede, protocolo novo).- **(v0.61.0) 📦 Pacote de aventura (.tavernapack)** (item 8 dos PEDIDOS_v0.58; `mesa/pacote.py`). Arquivo →
  **Exportar pacote de aventura…** / **Importar pacote de aventura…**:
  - é um .zip: `aventura.json` (a aventura com as imagens trocadas por referências), `imagens/<Pasta>/…` (mapas,
    tokens, objetos, projetor — cada imagem UMA vez só, mesmo usada em vários lugares), `tabelas/` (as tabelas de
    sorteio dos baús), `manifesto.json` e um LEIA-ME;
  - **não vão**: PDFs e as **fichas dos jogadores** (o token vai, a ficha não; as fichas das criaturas do mestre
    vão). O **diário da campanha** só vai se o mestre marcar. Música do YouTube não fica salva na aventura;
  - aviso na exportação: só compartilhe o que você tem direito de compartilhar;
  - importar **não sobrescreve nada**: a aventura ganha "(2)" se o nome já existir, as imagens vão pro banco
    (Mapas/Tokens/Objetos/Projetor, "Aventura - nome") e as que você já tinha não são copiadas de novo; tabela
    com o mesmo nome e conteúdo diferente vira "Nome (2)". Depois abre a aventura;
  - `arquivo.dados_aventura()` separado do `salvar_aventura` (exportar não marca a aventura como salva).
    Teste `teste_pacote.py` (em pastas temporárias). "Excluir porta" no menu ficou sem o "(a parede fecha)".- **(v0.60.1) 🧱 Paredes e portas (pedidos do Manel)**:
  - **Sala encostada em sala**: antes ficavam DUAS paredes uma em cima da outra e o 3D não desenhava nenhuma
    ("a parede some"). Agora `construcao.pedacos_livres` não repete o trecho que já tem parede; aventuras antigas
    e mapas importados são consertados ao abrir (`sem_sobreposicao`).
  - **Encontro em T** (parede de um lado ao outro da sala): a ponta para no eixo da outra parede em vez de ir
    até a face de fora dela (era o que abria a frestinha no canto). `ParedesItem._pontas`.
  - **Porta presa**: clicar e arrastar não move mais a porta (fica onde foi colocada até ser excluída).
  - **Botão direito na porta**: acha a porta mais perto (ela é fininha e no 3D aparece mais alta que o chão) e
    o menu tem **🗑 Excluir porta** logo em cima.
  - **Excluir a porta fecha a parede**: o vão vira parede de novo, do mesmo material, numa peça só. Ctrl+Z traz
    a porta de volta. Teste `teste_paredes_portas.py`.- **(v0.60.0) 🗺 Importar mapa Universal VTT** (`.dd2vtt` do Dungeondraft, `.uvtt`, `.df2vtt` do DungeonFog —
  item 7 dos PEDIDOS_v0.58). Arquivo → **Importar mapa Universal VTT…** (`mesa/uvtt.py`, diálogo em
  `ui/dialogo_uvtt.py`):
  - a imagem vira o **mapa** no tamanho certo; **1 quadrado do mapa = 1,5 m** por padrão (5 pés do D&D), ou 1 m,
    ou outro valor; o canto do mapa gruda no grid do Taverna;
  - `line_of_sight` + `objects_line_of_sight` viram **paredes** — material escolhido na hora, **pedra** por
    padrão (decisão do Manel);
  - `portals` viram **portas de madeira** do tamanho do vão, **abertas/fechadas como no arquivo**; se a parede
    do arquivo passa por cima da porta, o vão é aberto;
  - `lights` viram **luzes** (alcance, cor e intensidade do arquivo);
  - por padrão cria **uma aba nova** com o nome do arquivo (dá pra pôr na aba atual).
  - Nada novo na rede (usa mapa/paredes/portas/luzes de sempre). Teste `teste_uvtt.py` com arquivo gerado no teste.
- **(v0.60.0) 🚪 Porta FÍSICA pra luz** (pedido do Manel): antes a luz só sabia "aberta/fechada" (pulava de uma vez
  no clique) e a folha aberta não fazia sombra. Agora `PortaItem.segmentos_bloqueio()` diz onde a porta está
  NAQUELE momento: a folha girando na dobradiça (simples, dupla, persiana), deslizando pra dentro da parede
  (mecânica, secreta), a cortina recolhendo, a barreira mágica sumindo. A luz **vai entrando junto com a porta**
  (recalcula a cada passo da animação, no mestre e no jogador) e a **folha aberta faz sombra**. Vale também pra
  visão dos tokens e pro gás. Grade e janela de vidro continuam deixando a luz passar. Teste `teste_porta_fisica.py`.- **(v0.59.1) ☢ Cidade pós-apocalíptica REFEITA** (o Manel: "ficou muito zoado", o ônibus nem parecia amarelo):
  - **Dia cinza nublado** em vez do entardecer: o céu (`pa_ceu`, equiretangular) é fundo E luz ambiente
    (`lightProbe`), sol fraco atrás das nuvens com sombra suave, névoa clara sumindo com os prédios lá longe.
  - **Ônibus escolar amarelo de verdade**, de pé, atravessado na rua como **barricada**: lateral com pintura
    gasta, sujeira subindo, ferrugem escorrendo dos rebites, caixas de roda, porta de vidro trincada com tábuas
    em X, janelas tapadas com chapa de compensado / tábuas / vidro sujo, frisos, rodas com calota, retrovisor,
    sacos de areia, pneus e caixote no teto, hera subindo na traseira. Do lado: carro empurrado, sacos de areia,
    tambores e pneus fechando a rua.
  - **Pichação com letra de pichação** (fonte **Sedgwick Ave Display**, OFL; a Rubik Wet Paint parecia terror),
    com contorno de tag e borrifo em volta. **Corrigido**: o escorrido do hover nunca aparecia (pegava a cor
    errada e cortava embaixo) — agora escorre de verdade.
  - **Árvores e moitas de folha** (galhos cheios de folha instanciados, `RandomInstancing`), capim nas rachaduras
    e no meio-fio, **prédios com janelas** (vidro refletindo o céu, quebradas, tapadas, cortina, ar-condicionado,
    4 fachadas: reboco caindo, tijolo, concreto, verde) e **lojas fechadas no térreo** (placa desbotada, porta de
    enrolar pichada, vitrine quebrada; nomes genéricos), calçadas, postes (um torto), semáforos, entulho.
  - **Uma rua cruzando lá no fundo** com carros e a fileira de prédios do outro lado ("SOBREVIVENTES →" pichado),
    prédios altos sumindo na névoa, **corvos** rodando. Cervo atravessa a rua; o zumbi raro anda na rua do fundo.
  - Texturas novas `pa_*` em `posapoc_cenas.py` (as antigas da cidade saíram).- **(v0.59.0) ⚙ STEAMPUNK e ☢ PÓS-APOCALÍPTICO — dois temas novos completos** (pedido do Manel; paleta, fonte e
  dados aprovados antes). Agora são **9 temas**.
  - **Tema do programa todo**: paleta (Steampunk: couro, latão, cobre, pergaminho, pátina · Pós: fuligem,
    ferrugem, musgo, papel velho, amarelo de alerta), estilo das janelas (`tema.py`), botões e título em metal
    (`estilizado.py`: latão polido / lata enferrujada), textura das placas e cantoneiras (`materiais_ui.py`,
    `relevo_ui.py`), ícones na cor do tema (automático), filtro "Tema:" no painel Objetos.
  - **Fontes OFL** (em `taverna/fontes`, com a licença e crédito no `LICENCAS.md`): **IM FELL English SC**
    (Steampunk), **Black Ops One** (Pós) e **Sedgwick Ave Display** (o spray do ônibus; era Rubik Wet Paint, trocada na v0.59.1).
  - **Dados com desgaste em TODOS os temas** (`dados3d/cena3d.textura_desgaste`, multiplica a cor no shader):
    osso amarelado com poros e trincas (Medieval), plástico marmorizado (Moderno), trilhas de circuito acesas
    (Futurista), nuvens e veios (Mágico), sangue seco respingado (Terror), **latão com pátina e número gravado
    (Steampunk)**, **plástico desbotado, sujo e com fita isolante (Pós)**, grão discreto (Claro/Escuro).
    Personalização de dados pelo jogador: combinada pra depois (ver lista do que falta).
  - **Telas iniciais 3D** (sorteio 50/50, `TAVERNA_CENA_STEAMPUNK=oficina|dirigivel`, `TAVERNA_CENA_POSAPOC=cidade|abrigo`):
    - **Oficina do inventor** (`SteampunkOficina.qml`): engrenagens girando na parede, canos de cobre, vapor,
      lampião a gás tremendo, autômato pela metade na bancada. Opções = **plaquinhas de latão** num painel:
      no hover o **ponteiro do mostrador sobe** e a **válvula solta vapor**; no clique a **alavanca desce**.
    - **Ponte de comando do dirigível** (`SteampunkDirigivel.qml`): janelão pras nuvens do fim de tarde,
      cidade de chaminés lá embaixo soltando fumaça, outros dirigíveis passando, timão e instrumentos. O menu é
      o **telégrafo de ordens**: 5 fatias; no hover a **alavanca vai até a fatia**; no clique toca a campainha
      **"plim-plim"** (som sintetizado no próprio Taverna, `Ponte.plim`).
    - **Cidade tomada pelas plantas** (`PosApocCidade.qml`): rua rachada com mato, prédios com hera, carros
      enferrujados (uma árvore saindo de um), semáforo caído, pólen na luz do sol, **cervo** passando de vez
      em quando. O menu é **pichado com spray na lateral do ônibus tombado**; no hover a **tinta escorre
      fresca** (brilha). **Raramente um zumbi cambaleia lá no fundo.**
    - **Abrigo à noite** (`PosApocAbrigo.qml`): cerca de arame com arame farpado, fogo no tambor, rádio velho
      com o dial aceso, latas, caixotes, mapa marcado. Cada opção é uma **placa de madeira pintada à mão**
      pregada na cerca; no hover o **facho da lanterna** vai até a placa e ela **balança**. O rádio solta
      **frases picotadas** (legenda letra por letra com chiado; frases inventadas em `posapoc_cenas.FRASES_RADIO`).
  - **Plano B 2D** (sem placa de vídeo ou Gráficos Baixo, `tela_inicial.py`): engrenagens girando e vapor;
    cidade em ruínas no entardecer com hera e pólen.
  - **20 objetos de cenário** (`mesa/props_temas.py`, com altura na Mesa 3D). Steampunk: caldeira (ilumina),
    bancada com engrenagens, autômato, cano com válvula, relógio de pêndulo, lampião a gás (ilumina), baú com
    rebites, globo mapa-múndi, telescópio de latão, balão de carga. Pós: carro enferrujado, barricada, tambor
    com fogo (ilumina), sacos de areia, placa de PERIGO, prateleira saqueada, galão, pneu, cerca de arame,
    zumbi caído (dá pra revistar). Alguns aparecem também em outros temas (zumbi no Terror etc.).
  - Texturas novas em `ui/steampunk_cenas.py` e `ui/posapoc_cenas.py`. Teste `teste_temas_novos.py`.
- **(v0.58.8) Cthulhu do jeito certo** (o Manel: "parece só uma lula"): a **cabeça fica AFUNDADA no mar**,
  aparecendo só do meio dos olhos pra cima (o corpo todo está embaixo d'água), com a arcada pesada em cima dos
  olhos acesos rentes à água. **Tentáculos variados**: a forma `tentaculo` ganhou `giro` (+1 enrola pra
  cima/dentro, -1 pra baixo/fora), `voltas` (quanto enrola; 0 = solto) e `laco` (arco que volta pra dentro
  d'água, só a "corcova"); 13 tentáculos, cada um de um jeito, **baixos, perto da água** (altura a 58%).
- **(v0.58.7) Ajustes pedidos pelo Manel**:
  - **Cthulhu 3D com tentáculos ALEATÓRIOS** (nada espelhado): 11 tentáculos, cada um com altura, grossura,
    arco, espiral e inclinação próprios, uns colados no corpo e outros longe; barba com comprimentos diferentes;
    cabeça torta.
  - **Gente na janela caprichada** (`moderno_cenas._pessoa`): 5 poses (em pé; de lado tomando café; sentado no
    notebook com a tela acesa; duas pessoas conversando; olhando o celular), com cabelo, nariz de perfil,
    pescoço, ombros, braços grossos e contorno de luz.
  - **Helicóptero detalhado**: fuselagem com bico, cabine de vidro, cauda comprida, aleta, estabilizador, rotor
    de cauda girando, esquis com pernas, mastro e 4 pás + o borrão do giro, luzes de navegação (verde/vermelha,
    pisca branco e vermelho no rabo) e o holofote embaixo do bico. Agora passa NA FRENTE dos prédios.
  - **Bug corrigido (era da otimização v0.56.1)**: os testes rodam "sem tela" e lá o Windows não entrega as
    fontes do sistema (ex.: Courier New do Terror) — o desenho saía com a fonte errada e ia pro CACHE de
    desenhos, e o programa de verdade reaproveitava. Agora sem tela não grava no cache (e as texturas 3D dos
    testes vão pra `taverna_3d_teste`); o cache contaminado foi apagado.
- **(v0.58.6) Prédios caprichados + Cthulhu em 3D** (pedido do Manel: "dá pra melhorar"):
  - Fachadas ÚNICAS por prédio (`predio_<semente>_<colunas>_<andares>` em `moderno_cenas._predio`; a textura
    cobre o prédio inteiro, nada se repete): **janelas grandes**, cada uma do seu jeito — acesa quente/fria ou
    apagada (vidro com reflexo), cortina meio fechada, persiana, gente na janela, luminária, TV azul no escuro —,
    moldura, peitoril e faixa de laje entre os andares.
  - **Prédio da frente detalhado**: escada de incêndio de ferro (plataformas, guarda-corpo, escadas em
    zigue-zague), **jardineiras com plantas e flor** embaixo de algumas janelas, ar-condicionado, laje com caixas
    d'água, e a luz de um **poste da rua** (sódio) batendo na fachada.
  - **Cthulhu em 3D** (`TerrorFarol3D.qml`, forma nova `tentaculo` em `geometria3d.py`): polvo gigante lá no
    fundão (cabeça alta, "rosto", olhos acesos, barba de tentáculos e 8 tentáculos em arco enrolando na ponta,
    espalhados em volta). Escuro + a neblina: no clarão do raio aparece como SILHUETA. (A imagem 2D do Cthulhu
    também foi redesenhada e continua no farol 2D, sem placa de vídeo.)
- **(v0.58.5) Terraço refeito pelo desenho do Manel + Cthulhu novo**:
  - `qml/ModernoTerraco.qml`: **outdoor de PAPEL colado** na ESQUERDA (folhas emendadas, rugas, sujeira de
    chuva, canto rasgado — textura `papel_outdoor`), em pernas de ferro com passarela; prédio alto atrás, outro
    alto na direita e um baixo na frente (com laje e caixas d'água). O **menu é impresso no cartaz** (título,
    MESTRE/JOGADOR, opções; `menuProprio` + `tituloProprio`), arte com um **d20** de verdade num "sol" laranja.
    **Dois refletores, um de cada lado, giram e apontam a luz pra opção do mouse** (a luz bate no cartaz de
    verdade; a mira escorrega suave a cada quadro). Sem nada no mouse, um ilumina o título e o outro a arte.
    A grade de LED saiu (o Lancador ainda sabe desenhar, `gradeLed`, se alguma cena quiser).
  - Cthulhu do farol (`terror_cenas._cthulhu`): agora um **polvo gigante saindo do mar** (pela imagem do Manel):
    cabeça alta e bulbosa, sobrancelhas pesadas, olhos acesos, tentáculos grossos em ARCO pros dois lados com a
    ponta ENROLADA e ventosas, barba de tentáculos e espuma onde sai da água.
  - Cuidado aprendido: no Qt Quick 3D `lookAt` só existe na câmera (o refletor calcula o ângulo na mão); e um
    Model com opacidade 0 some do `View3D.pick` (as linhas clicáveis usam 0.01).
- **(v0.58.4) 5 · 🏙 Moderno com 2 telas em 3D** (`ponte.cenaModerno`, `TAVERNA_CENA_MODERNO=celular|terraco`;
  sorteia de novo ao escolher o tema; sem placa/Baixo = o cenário antigo com o vidro fosco). Desenhos em
  `ui/moderno_cenas.py` (nada de marca/app de verdade).
  - **Celular na mesa** (`qml/ModernoCelular.qml`): vista de cima, mesa de madeira escura à noite. **O menu é
    a tela do celular** (o app: barra de status, ilha da câmera, brilho de fundo, barrinha embaixo) — a cena
    expõe `tela` e o Lancador encaixa os botões. A luz da tela ilumina a mesa. **Mouse num botão = o celular
    vibra** (`BotaoOrnado.entrou` → `Lancador.botaoEntrou` → `cena.vibrar()`). **Notificações inventadas**
    (`ponte.notificacoes`) descem de tempos em tempos (e o celular vibra). Chuva escorrendo na janela com a
    cidade borrada, café com fumaça, chaves, carteira, papéis e caneta.
  - **Terraço** (`qml/ModernoTerraco.qml`): noite, **outdoor de LED** em cima do prédio da frente com o menu
    (`gradeLed: true` → o Lancador desenha a grade de pixels por cima dos botões), luz e brilho no ar úmido
    (névoa), prédios com janelas acesas, luzinhas vermelhas piscando nos topos, rua com **carros** (faróis e
    lanternas), **helicóptero com holofote** (cone de luz + luz de verdade) cruzando de vez em quando,
    mureta/corrimão/antena do nosso terraço.
  - Dentro de um objeto da cena, o título fica menor (340) pra sobrar espaço pros botões (vale pra TV também).
  Teste `teste_moderno.py`. ⚠ A vibração, as notificações e o helicóptero não foram vistos rodando.
- **(v0.58.3) 4 · 🔮 Mágico: menu do círculo ESCRITO COM LUZ NA PEDRA** (resolve o "falta decidir" da v0.57) —
  `qml/MagicoCirculo.qml`: sem cápsulas; título "Taverna" (na cor de destaque) e as opções gravadas no chão,
  brilhando fraco; separadores MESTRE/JOGADOR no mesmo estilo. A cena tem `menuProprio` + `tituloProprio` (o
  Lancador esconde o título e o menu 2D). **Disco escuro e liso** no miolo (sólido: esconde o pentagrama atrás
  das letras). **Hover** (`View3D.pick`): a palavra acende na cor de destaque, um **traço de luz** corre por
  baixo e **uma runa do anel de fora acende** (cada opção tem a sua). **Clique**: 5 bolinhas de luz correm do
  centro até as pontas do pentagrama, o círculo inteiro (e as fendas) dá um **clarão** e entra a transição.
  **Fendas de verdade**: textura nova `pedra_rachada` + `fendas_normal` (sulco afundado) + `fendas_luz` (a luz
  só no fundo da fenda); tampo da plataforma mapeado reto (as lajes não entortam). **Poções**: mais pra
  dentro da tela, contorno escuro no vidro (casco invertido), reflexo, aro no gargalo e o **nível do líquido**.
  **Cor de destaque: DOURADO** (escolha do Manel; `ponte.destaqueMagico`, o ciano ficou só pra comparar com
  `TAVERNA_DESTAQUE=ciano`). Teste `teste_magico_menu.py`. ⚠ O clarão do clique não foi visto rodando.
  Cuidado aprendido: objeto transparente grande (disco com borda suave) é desenhado POR CIMA das palavras de
  trás (ordem por distância) — por isso o disco é sólido e as palavras não gravam profundidade.
- **(v0.58.2) 3 · 🐞 Reportar problema** — `ui/reportar.py`, menu **Ajuda → Reportar problema…** (mestre e
  jogador). A pessoa escreve "o que aconteceu" e o Taverna monta `Taverna_problema_<data>.zip` na **Área de
  Trabalho** com `o_que_aconteceu.txt`, `sistema.txt` (versão, protocolo, Windows, Python/PyQt/Qt, **placa de
  vídeo e versão do OpenGL**, Gráficos, Mesa 3D/Dados 3D/tremor/clarão) e o `erros.log` (só o fim, se passar de
  2 MB). Abre a pasta no fim. **Nada vai pela internet.** Caixinha "incluir a aventura aberta" (só o mestre,
  **desligada** por padrão, só o `.taverna`, precisa estar salva); **nunca** PDFs nem fichas.
  Teste `teste_reportar.py` (gera numa pasta temporária, não mexe na Área de Trabalho).
- **(v0.58.1) 2 · 📣 "Todos olhem pra cá"** — **protocolo 13** (mande o .exe novo pros amigos). Mestre: botão
  direito no mapa → "📣 Levar a câmera de todos aqui" (ou **Shift+P** no ponto do mouse) e "… e travar 5 s".
  A câmera de cada jogador **desliza** (0,9 s, suave) até o ponto, no **zoom do mestre**, e aparece um ping lá.
  Jogador em **outro andar/aba** só recebe o aviso "📣 O mestre chamou a atenção pro 2º andar". A névoa continua
  valendo (a câmera vai, mas só se vê o que já se veria). **Travar**: por uns segundos o jogador não consegue dar
  zoom, arrastar, "ver tudo" nem centralizar no token. Vai pro histórico ("chamou a atenção de todos pra cá").
  Só funciona com a taverna aberta e a aba ao vivo (senão o menu explica por quê).
  `servidor.olhar_aqui`, `JanelaMestre.chamar_atencao`, `JanelaPlayer.olhar_aqui`, `visao.voar_para` /
  `travar_camera` / `camera_travada`. Teste `teste_olhar_aqui.py` (mestre + jogador pela rede).
  ⚠ Não visto rodando com amigos de verdade (a animação foi conferida só no teste).
  Lição: teste que mexe na mesa NÃO pode chamar `M.close()` no fim (abre o "quer salvar?" e trava): saia com
  `os._exit`.
- **(v0.57.0) MÁGICO com duas telas em 3D** (`ponte.cenaMagico`, forçar com `TAVERNA_CENA_MAGICO=circulo|torre`;
  desenhos em `ui/magico_cenas.py`):
  - **Círculo mágico** (`qml/MagicoCirculo.qml`): plataforma octogonal de pedra rachada (rachaduras acesas,
    pulsando) flutuando no espaço (skybox de nebulosa), o **círculo mágico em 2 anéis girando em sentidos
    contrários** (pentagrama, lua, elementos, runas do futhark desenhadas por traços) com o **menu dentro**;
    cristais, cristal flutuando girando com anel de runas, 4 poções coloridas, alambique de latão com
    serpentina de vidro (forma `helice` nova) e fumaça roxa, pilão com pó brilhando, lascas de cristal voando.
  - **Torre de mago** (`qml/MagicoTorre.qml`): céu roxo com redemoinho de galáxia e pôr do sol, lua, mar de
    nuvens em camadas passando, ilha flutuante de rocha com a torre (andares, janelas acesas, torrinhas com
    ponta de cristal, arcos, escada), **estrela no topo** e **3 anéis de runas girando**; ilhotas com
    cristais boiando, cristais grandes nos cantos, brilhinhos no ar.
    **Os botões são CRISTAIS 3D do cenário** (pedido do Manel): cada opção é um cristal flutuando com o nome
    brilhando dentro (`Texture.sourceItem`); o mouse é testado com `View3D.pick` e o cristal **ACENDE** (rosa-
    magenta forte, luz em volta e cresce um pouco); clicou, escolhe. A cena avisa `menuProprio: true` e o
    Lancador esconde o menu 2D (fica só o título). (Sem tonemap nessa cena: o filmic deixava tudo cinza.)
  - **Sorteio das telas**: 50/50, e agora sorteia de novo **toda vez que a pessoa escolhe o tema** no rodapé
    (antes era só uma vez por abertura; o Manel trocava de tema e via sempre a mesma tela).
  - Torre um pouco mais clara (céu e nuvens redesenhados mais claros, luzes mais fortes; mesmas cores).
  - **Falta decidir com o Manel**: como o menu do CÍRCULO se mistura com o cenário. Ideias passadas: (1) as
    5 pontas do pentagrama = as 5 opções (acende a ponta no mouse, o círculo dá um clarão no clique) — a
    favorita; (2) rótulos nas poções; (3) grimório aberto; (4) cristais orbitando.
- **(v0.56.1) Abertura mais rápida (pedido do Manel, sem tirar nada)** — medido: tela Medieval de **8,6 s → 2,9 s**
  até aparecer (da 2ª vez em diante):
  - A tela inicial em 3D agora desenha com **OpenGL** (`taverna.py`, `QQuickWindow.setGraphicsApi`): o driver da
    placa guarda os shaders compilados. No Direct3D eles eram refeitos a cada abertura (~2 s) e o cache do Qt
    nunca era gravado (o programa sai com `os._exit`). Visual conferido igual nas 4 cenas.
  - O fundo 2D da mesa (2,3 s de numpy) não é mais pintado quando a cena 3D cobre a tela (`FundoTema.coberto`).
  - Desenhos caros da tela inicial (botões de metal, títulos, peças das cenas) ficam guardados em arquivo
    (`AppData/Local/Taverna/cache/imagens/<assinatura>`); a assinatura muda sozinha com a versão
    ou quando um arquivo de desenho muda, e as pastas velhas são apagadas.
  - Montagem das formas 3D mais rápida (`geometria3d.malha` com `tolist`).
  - Farol: o feixe agora **some aos poucos com a distância** (antes o degradê estava invertido e ficava um
    círculo forte na ponta) + um halo largo e fraco em volta (luz espalhando na chuva).
  - Sorteio das telas: 50% / 50% (já era `random.choice`).
- **PEDIDO DO MANEL (18/11) — cada tema com 2 VARIANTES de tela inicial, sorteadas toda vez que abre**
  (referências em `referencias/`; as do Mágico não vieram como arquivo, estão descritas aqui):
  - **Terror** (v0.55): (1) TV velha enferrujada com o MENU DENTRO DA TELA — tela branca/cinza com chiado,
    pisca e às vezes aparece um ROSTO; luminária que pisca de vez em quando, caneca rachada, fotos, chaves,
    lanterna APAGADA, pano com sangue, teias. (2) Tempestade: penhasco com FAROL GIRANDO à esquerda, mar
    violento batendo nas pedras, chuva, BARCO BALANÇANDO à direita, raios de vez em quando e às vezes (sempre
    junto com um raio, nunca sem) a SILHUETA DO CTHULHU no fundo.
  - **Mágico** (depois do Terror): (1) plataforma de pedra rachada flutuando no espaço roxo, com um CÍRCULO
    MÁGICO enorme no meio (pentagrama, runas, símbolos de lua/sol/elementos — o menu fica dentro dele);
    cristais roxos (cluster em cima/esquerda, um cristal flutuando girando com anel de runas), poções coloridas
    (vermelha, azul-esverdeada, roxa, amarela), alambique de latão com serpentina e fumaça roxa, pilão com pó
    roxo brilhando; rachaduras com luz roxa; cristais soltos flutuando em volta. (2) Céu roxo de noite com lua,
    nuvens e redemoinho de galáxia; TORRE DE MAGO em ilha flutuante (janelas roxas acesas, estrela brilhando
    no topo, ANÉIS DE RUNAS girando em volta), ilhotas com cristais flutuando, cristais grandes nos cantos,
    mar de nuvens embaixo com pôr do sol laranja no horizonte.
  - **Medieval**: (1) a mesa da taverna 3D (v0.54). (2) QUADRO DE MISSÕES de madeira num muro de pedra: papel
    grande no meio (o menu fica nele), cartazes menores nos lados com fio vermelho ligando, mapa, selos de cera,
    estandarte vermelho com brasão e espadas no topo, duas espadas cruzadas e cordas com brasões (lobo, torre)
    embaixo, LAMPARINA de ferro acesa à direita (chama tremendo), hera nos cantos.
- Falta: cenário próprio com efeitos pros outros temas (hoje: o cenário antigo + vinheta), e as caixinhas de
  Tema/Gráficos do rodapé no mesmo estilo; depois, levar o visual pra dentro da mesa.

### (acabamento em andamento — próximos blocos acima) (candidatas: banco de imagens + remover fundo; ficha PDF de qualquer sistema)

### 💬 Sugestões do teste com o amigo (16/11)
**Funcionalidade (entram como etapas):**
- 🧪 Teste com 4–5 jogadores ao mesmo tempo (quando der) — ver se a rede aguenta som/projetor.
- ~~Baú com recompensa aleatória~~ → feito na Etapa 12.
- ~~Banco de imagens + remover fundo~~ → feito na Etapa 13 (o removedor com IA fica pro acabamento).

**Parte visual (fica pro acabamento, no fim):**
- **✂ Removedor de fundo avançado (IA)** — fazer com o Fable.
- **Animação de dados** rolando (e outras animações).
- **Retratos do grupo na lateral esquerda**, estilo Baldur's Gate (conversar melhor depois).
- **Retratos na ordem do combate**, estilo Baldur's Gate: em cima da tela, em sequência
  (Jogador A → Monstro → Jogador B…). Hoje a faixa de turnos mostra os nomes; vira retratos.

### 🧭 Decisões (16/11)
- **O Taverna é um VTT neutro**: vem com o **D&D 5e embutido** (o padrão), mas não vai ter outros
  sistemas prontos. Quem joga outro sistema usa **a própria ficha em PDF** no leitor do programa.
  → feito na Etapa 14 (preencher qualquer ficha PDF editável dentro do Taverna).
- **Área perigosa não dá dano sozinha**: quem decide é o mestre (o personagem pode ser imune a fogo etc.).
- **Acabamento visual + otimização** ficam por último, juntos.

---

## 💡 Ideias guardadas (sem etapa ainda)
- ~~Tradução do resto do compêndio~~ — descartada (não tem mais compêndio).

### 🏁 Reta final (combinado em 18/11)
1. ~~Removedor de fundo com IA~~ ✅ v0.47. 2. ~~Otimização medida~~ ✅ v0.47. 3. O Manel testa com o amigo (Radmin).
4. **Detalhar tudo que é 3D** (pedido do Manel, 18/11 — logo depois da otimização): paredes, piso, objetos
   e portas bem acabados. Já anotado: a porta não tem textura (toda marrom) e a maçaneta aparece como
   uma bola dourada POR CIMA da textura; porta de grade com as grades realmente vazadas; parede de
   madeira/paliçada com troncos cilíndricos de verdade.
5. Última passada nos gráficos com o Manel: **HUD mais bonito e detalhado, tela inicial** etc.
6. (ideias do Manel, 18/11 — ainda em conversa) **Launcher único**: um programa só pra mestre e jogador; na
   abertura escolhe Mestre (criar sessão / continuar) ou Jogador (entrar na sessão). **Interface toda mais
   detalhada e "sólida", com texturas em 3D em TODOS os temas**: botões, bordas da janela, botões das seções…
   Caminho conversado: mesa num renderizador próprio na placa de vídeo (ModernGL) + HUD/telas em Qt Quick
   (QML), sem trocar de linguagem; texturas/modelos CC0 com crédito.
   **Decidido (18/11):** ordem = 1) launcher + tela inicial nova (vitrine do estilo de cada tema),
   2) moldura da janela e botões, 3) painéis. Referências: escolha do Claude. **O "exagero" da interface segue
   o nível de Gráficos**: Baixo = simples · Médio = equilibrado · Alto = exagerado (moldura pesada, relevo,
   brilho, animação).
7. (ideias do Manel, 18/11) **Câmera em perspectiva do jogador**: ver a mesa "pelos olhos" do token (fica pra
   quando a mesa estiver no renderizador da placa de vídeo). **Cone de visão padrão = visão comum de uma
   pessoa.** 🐛 **A borda do cone revela o "quadradinho" inteiro** em vez de cortar na diagonal (corrigir).
   **Vários tipos de token** — o Manel vai detalhar.

---

## Como as coisas se ligam
```
Paredes ──► Visão (bloqueiam)  ──► Gatilhos (apagar luzes)
   │
   └──────► Turnos (quem está na mesma sala entra no combate)
Props ────► Interação (baú) ───► Inventário da ficha
                     └─────────► Armadilhas (eventos)
```

**Áudio (anotado em 16/11):**
- **Efeitos sonoros**: o mestre importa arquivos de áudio (mp3/ogg/wav) baixados por ele;
  o Taverna manda pros players uma vez (como as imagens) e toca na hora que o mestre clicar.
  Fontes que o Manel usa: Pixabay, Freesound, MyInstants. (Freesound: ver a licença de cada som;
  MyInstants: muitos são trechos de filme/meme enviados por usuários, não necessariamente livres.)
- **Música pelo YouTube**: **só o mestre** cola o link. Os players não fazem nada: o programa deles
  abre o mesmo vídeo sozinho, no mesmo ponto, pelo **player oficial do YouTube**. Quando o mestre
  troca pra música de combate, pausa, pula ou volta, **muda pra todo mundo na hora**.
  O mestre controla o volume geral; cada player só pode baixar o próprio volume. **Fila** de links.
- Alternativa sem YouTube: o mestre importa a música como arquivo (igual aos efeitos) e controla
  igual. Sem anúncio e sem janelinha, mas só com músicas que ele pode usar (ex.: trilhas livres).
- Efeitos: Pixabay e Freesound (atenção à licença de cada som: CC0 livre, CC-BY pede crédito,
  "NC" só uso não comercial). MyInstants tem muito som enviado por usuários e tirado de filmes/jogos,
  então nem tudo lá é liberado.
  Regras do YouTube a seguir: player oficial **visível** (mínimo 200×200 px; pode ficar num cantinho
  ou numa janelinha), sem esconder o player/logo e **sem baixar ou extrair o áudio**.
  Vídeos com incorporação desativada pelo dono não tocam. Pode aparecer anúncio.
  Tecnicamente precisa do QtWebEngine (aumenta bastante o tamanho do .exe).
