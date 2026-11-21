"""
Dados 3D rolando na mesa (v0.32).

- geometria.py — os sólidos (d4, d6, d8, d10, d12, d20), faces e números.
- fisica.py    — a física (numpy, determinística: mesma semente = mesmo quique em todos os PCs).
- cena3d.py    — câmera, materiais por tema, preparação dos dados de uma rolagem.
- render_gl.py — desenho em OpenGL (placa de vídeo), com luz, brilho e sombra.
- render_2d.py — plano B sem OpenGL (QPainter): se o OpenGL falhar, ou nos testes sem tela.
- overlay.py   — o painel transparente por cima da mesa que mostra a rolagem e o resultado.

O RESULTADO é sempre o que o servidor do mestre sorteou: a física roda solta e, quando os dados
param, os números das faces são "renomeados" pra que a face de cima mostre o valor certo.
"""
