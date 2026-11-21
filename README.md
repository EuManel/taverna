# 🍺 Taverna

**English** · [Português](#português)

A desktop virtual tabletop (VTT) to play RPGs with your friends — one program for everyone: on the start screen
the **Game Master** opens the table and the **Players** join it over the internet. System-neutral, with
D&D 5e (SRD 5.1) built in.

**⬇ Download (Windows): <https://omanel.itch.io/taverna>** — unzip and run `Taverna.exe`, no install needed.

## Features

- **One app, two roles** — the GM hosts, players join with a room code (automatic UPnP) or through Radmin VPN.
  The GM's server is in charge: each player only receives what they're allowed to see.
- **3D table** — top-down camera that can rotate and tilt; walls, doors, objects and tokens with height.
- **Building tools** — floor painted like paint, free-angle walls, 8 door types, rooms, stairs and **floors**
  (each player sees the floor their token is on), Universal VTT map import.
- **Vision and light** — vision cones, fog of war, dynamic lights with shadows that stop at walls.
- **Combat** — initiative, turn order, movement limited by speed, conditions, HP, 3D dice.
- **Atmosphere** — weather (rain, snow, fog), areas of effect (fire, ice, acid…) that react to each other,
  gas and liquids that spread and respect walls, quick effects (explosions, lightning), sound board and
  **YouTube music** through the official, visible player.
- **Interactive objects** — chests with loot tables, traps and triggers, documents, keys, a projector to show
  images to the players.
- **Library** — your own PDFs (stay on your computer), fillable PDF character sheets for any system, D&D 5e
  sheet, token library, image bank with an **AI background remover**.
- **World and city maps** with travel and fog, campaign journal, chat with whispers and NPC voices.
- **9 visual themes** (Medieval, Horror, Futuristic, Modern, Magical, Steampunk, Post-apocalyptic, Light, Dark),
  graphics quality Low / Medium / High.
- **Portuguese and English** — pick it with the little flags on the start screen.

## Run from source

1. Install **Python 3.11 or newer** (<https://www.python.org/downloads/>) — tick **"Add python.exe to PATH"**.
2. In the project folder:

   ```
   python -m pip install -r requirements.txt
   python taverna.py
   ```

   (or double-click `iniciar_taverna.bat`, which installs what's missing on the first run)
3. Optional — YouTube music: `python -m pip install PyQt6-WebEngine` (or `instalar_musica.bat`).
4. To test a player on the same PC: open Taverna again, pick **Player** and join `127.0.0.1`, port `7777`.

Tests: `python testes/rodar_testes.py` (they run the GM and the Player headless over the local network).
Release build: `python gerar_release.py` (needs `pyinstaller` and `PyQt6-WebEngine`) → `release/`.

How to connect over the internet: [`HOW_TO_CONNECT.txt`](HOW_TO_CONNECT.txt).

## Suggestions and bugs

- Open an **[issue](../../issues)** here on GitHub, or leave a comment on the
  [itch.io page](https://omanel.itch.io/taverna).
- Inside the app: **Help → Report a problem** builds a `.zip` on your Desktop with the error log and system
  info (nothing is sent automatically) — attach it to the issue.

## License and credits

Copyright (C) 2026 Manel. Taverna is free software under the **GNU General Public License v3.0** — see
[`LICENSE`](LICENSE) (Qt is used under the LGPL v3: [`LICENSE-LGPL-3.0.txt`](LICENSE-LGPL-3.0.txt)). Third-party credits (PyQt6, Qt, SRD 5.1 under CC-BY 4.0, OFL fonts, CC0 textures,
AI models) are in [`LICENCAS.md`](LICENCAS.md). Only the free SRD 5.1 is included — no content from
copyrighted books. Dungeons & Dragons is a trademark of Wizards of the Coast; Taverna is not affiliated with it.

---

## Português

Uma mesa virtual de RPG (VTT) pra desktop, pra jogar com os amigos — um programa só pra todo mundo: na tela
inicial o **Mestre** abre a mesa e os **Jogadores** entram nela pela internet. Neutro de sistema, com D&D 5e
(SRD 5.1) embutido.

**⬇ Baixar (Windows): <https://omanel.itch.io/taverna>** — descompacte e abra o `Taverna.exe`, não precisa
instalar.

## Recursos

- **Um programa, dois papéis** — o mestre abre a taverna, os jogadores entram com o código da sala (UPnP
  automático) ou pelo Radmin VPN. Quem manda é o servidor do mestre: cada jogador recebe só o que pode ver.
- **Mesa em 3D** — câmera de cima que gira e inclina; paredes, portas, objetos e fichas com altura.
- **Construção** — chão pintado como tinta, paredes em qualquer ângulo, 8 tipos de porta, salas, escadas e
  **andares** (cada jogador vê o andar do próprio token), importação de mapa Universal VTT.
- **Visão e luz** — cone de visão, névoa de guerra, luzes dinâmicas com sombra que param nas paredes.
- **Combate** — iniciativa, ordem dos turnos, movimento limitado pelo deslocamento, condições, PV, dados 3D.
- **Atmosfera** — clima (chuva, neve, neblina), áreas de efeito (fogo, gelo, ácido…) que reagem entre si, gás e
  líquidos que se espalham e respeitam paredes, efeitos rápidos (explosão, raio), mesa de sons e **música do
  YouTube** pelo player oficial e visível.
- **Objetos interativos** — baús com tabelas de loot, armadilhas e gatilhos, documentos, chaves e um projetor
  pra mostrar imagens aos jogadores.
- **Biblioteca** — seus PDFs (ficam no seu computador), fichas em PDF preenchível de qualquer sistema, ficha de
  D&D 5e, biblioteca de tokens e banco de imagens com **removedor de fundo com IA**.
- **Mapas de mundo e cidade** com viagem e névoa, diário da campanha, chat com sussurro e fala de NPC.
- **9 temas visuais** (Medieval, Terror, Futurista, Moderno, Mágico, Steampunk, Pós-apocalíptico, Claro,
  Escuro) e qualidade gráfica Baixo / Médio / Alto.
- **Português e inglês** — escolha pelas bandeirinhas da tela inicial.

## Rodar pelo código

1. Instale o **Python 3.11 ou mais novo** (<https://www.python.org/downloads/>) — marque **"Add python.exe to
   PATH"**.
2. Na pasta do projeto:

   ```
   python -m pip install -r requirements.txt
   python taverna.py
   ```

   (ou dê dois cliques no `iniciar_taverna.bat`, que instala o que faltar na primeira vez)
3. Opcional — música do YouTube: `python -m pip install PyQt6-WebEngine` (ou `instalar_musica.bat`).
4. Pra testar um jogador no mesmo PC: abra o Taverna de novo, escolha **Jogador** e entre em `127.0.0.1`,
   porta `7777`.

Testes: `python testes/rodar_testes.py` (rodam o Mestre e o Jogador sem tela, pela rede local).
Build de release: `python gerar_release.py` (precisa do `pyinstaller` e do `PyQt6-WebEngine`) → `release/`.

Como conectar pela internet: [`HOW_TO_CONNECT.txt`](HOW_TO_CONNECT.txt).

## Sugestões e problemas

- Abra uma **[issue](../../issues)** aqui no GitHub, ou deixe um comentário na
  [página do itch.io](https://omanel.itch.io/taverna).
- Dentro do programa: **Ajuda → Reportar problema** monta um `.zip` na sua Área de Trabalho com o registro de
  erros e as informações do sistema (nada é enviado sozinho) — anexe na issue.

## Licença e créditos

Copyright (C) 2026 Manel. O Taverna é software livre sob a **GNU General Public License v3.0** — veja o
[`LICENSE`](LICENSE) (o Qt é usado sob a LGPL v3: [`LICENSE-LGPL-3.0.txt`](LICENSE-LGPL-3.0.txt)). Os créditos de terceiros (PyQt6, Qt, SRD 5.1 sob CC-BY 4.0, fontes OFL, texturas
CC0, modelos de IA) estão no [`LICENCAS.md`](LICENCAS.md). Só o SRD 5.1 livre vem embutido — nenhum conteúdo de
livro protegido. Dungeons & Dragons é marca da Wizards of the Coast; o Taverna não é afiliado a ela.
