# Licenças e créditos

## O Taverna
Copyright (C) 2026 Manel.
O Taverna é software livre, distribuído sob a **GNU General Public License versão 3** (GPL-3.0).
O texto completo está no arquivo `LICENSE`. Você pode usar, estudar, modificar e redistribuir o programa,
desde que as versões redistribuídas continuem sob a GPL-3.0 com o código-fonte disponível.
O programa é fornecido SEM GARANTIA, nos termos da licença.

## Bibliotecas incluídas no programa
- **PyQt6** (e PyQt6-WebEngine) — © Riverbank Computing Limited (https://www.riverbankcomputing.com),
  licença **GNU GPL v3** (texto no arquivo `LICENSE`).
- **Qt 6** (incluindo Qt Quick, Qt Multimedia e Qt WebEngine) — © The Qt Company Ltd. e outros
  colaboradores (https://www.qt.io), usado sob a licença **GNU LGPL v3** (texto no arquivo
  `LICENSE-LGPL-3.0.txt`; a LGPL v3 complementa a GPL v3 do arquivo `LICENSE`). As bibliotecas do Qt vão
  como arquivos separados (DLLs na pasta `_internal`) e podem ser trocadas por outra versão compatível.
  O Qt WebEngine inclui o Chromium, com as licenças dos seus próprios componentes.
- **NumPy** (BSD-3-Clause), **pypdf** (BSD-3-Clause), **Python** (PSF License).

## Conteúdo do Compêndio (SRD 5.1)
Este trabalho inclui material do System Reference Document 5.1 ("SRD 5.1") da Wizards of the Coast LLC,
disponível em https://dnd.wizards.com/resources/systems-reference-document.
O SRD 5.1 é licenciado sob a Creative Commons Attribution 4.0 International License,
disponível em https://creativecommons.org/licenses/by/4.0/legalcode.

Dungeons & Dragons é marca registrada da Wizards of the Coast LLC. O Taverna não é afiliado,
patrocinado nem endossado pela Wizards of the Coast.

## Dados organizados por 5e-database
Os arquivos em `taverna/compendio/dados` vêm do projeto 5e-database
(https://github.com/5e-bits/5e-database), licença MIT:

    Copyright (c) 2018-2020 Adrian Padua, Christopher Ward
    Permission is hereby granted, free of charge, to any person obtaining a copy of this software
    and associated documentation files (the "Software"), to deal in the Software without restriction,
    including without limitation the rights to use, copy, modify, merge, publish, distribute,
    sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions: The above copyright notice and this
    permission notice shall be included in all copies or substantial portions of the Software.
    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND.

## Leitor de PDF
pypdfium2 (Apache-2.0 / BSD-3-Clause) e PDFium (Google, BSD-3-Clause).

## Seus PDFs
Os PDFs que cada pessoa importa ficam só no computador dela. O Taverna só os envia pela rede quando o
mestre libera um livro pra um jogador ou pega uma cópia da biblioteca de um jogador (compartilhe só o que
você tem direito de compartilhar).

## Materiais da interface (pasta `taverna/ui/materiais`)
Texturas de **ambientCG** (<https://ambientcg.com>), licença **CC0 1.0 Universal** (domínio público — uso e
redistribuição livres; o crédito é cortesia): WoodFloor043, Leather037, Leather026, MetalPlates013,
MetalPlates006, Metal049A, Metal041B, Planks037A, Onyx015, Paper006. Reduzidas pra 512 px (cor, normal e
rugosidade) e "pintadas" com luz pelo próprio Taverna (`ui/relevo_ui.py`).

## Removedor de fundo com IA
Os modelos NÃO vêm dentro do Taverna: são baixados quando você pede (ficam em Documentos/Taverna/IA).
O Taverna os roda com um motor próprio em numpy (`taverna/ia/`).
- **U²-Net / U²-Netp** — Xuebin Qin, Zichen Zhang, Chenyang Huang, Masood Dehghan, Osmar R. Zaiane,
  Martin Jagersand. https://github.com/xuebinqin/U-2-Net — licença Apache-2.0.
- **IS-Net (DIS, "isnet-general-use")** — Xuebin Qin, Hang Dai, Xiaobin Hu, Deng-Ping Fan, Ling Shao,
  Luc Van Gool. https://github.com/xuebinqin/DIS — licença Apache-2.0.
- Arquivos `.onnx` convertidos e publicados pelo projeto **rembg** (Daniel Gatis,
  https://github.com/danielgatis/rembg, licença MIT), de onde o Taverna os baixa.


## Fontes (pasta `taverna/fontes`)

Fontes de título dos temas, todas sob a **SIL Open Font License 1.1** (uso e redistribuição livres;
o texto completo de cada licença está na mesma pasta, nos arquivos `OFL-*.txt`):

| Tema | Fonte | Autor |
|---|---|---|
| Medieval | MedievalSharp | wmk69 |
| Terror | Pirata One | Rodrigo Fuenzalida, Nicolas Massi |
| Futurista | Orbitron | The Orbitron Project Authors (Matt McInerney) |
| Moderno | Bebas Neue | The Bebas Neue Project Authors (Ryoichi Tsunekawa) |
| Mágico | Cinzel Decorative | Natanael Gama |
| Steampunk | IM FELL English SC | Igino Marini |
| Pós-apocalíptico | Black Ops One | The Black-Ops Project Authors (James Grieshaber) |
| Pós-apocalíptico (menu pichado) | Sedgwick Ave Display | The Sedgwick Ave Project Authors (Kevin Burke, Luke Prowse) |

Os temas Claro e Escuro usam as fontes do próprio sistema.
