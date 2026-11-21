# Como lançar uma versão nova do Taverna

Passo a passo pra soltar uma versão (ex.: v1.1). Os comandos são do PowerShell, na pasta do projeto.

> Se o `git`/`gh` não forem achados, rode antes:
> `$env:PATH = "C:\Program Files\Git\cmd;C:\Program Files\GitHub CLI;" + $env:PATH`

## 1. Número da versão

- `taverna/config.py` → suba `APP_VERSAO` (ex.: `"1.1.0"`).
  - Correção pequena: último número (`1.0.1`). Coisa nova: o do meio (`1.1.0`). Mudança grande: o primeiro (`2.0.0`).
- Se alguma mensagem da rede mudou de formato, suba também `VERSAO_PROTOCOLO` em `taverna/rede/protocolo.py`
  (mestre e jogador vão precisar estar na mesma versão).

## 2. Textos em inglês

Todo texto novo da interface precisa estar em `taverna/idiomas/en.json`:
- `"textos"`: frase fixa (`"Salvar": "Save"`).
- `"modelos"`: frase com variável (`"Nova versão {0} disponível — baixar": "New version {0} available — download"`).

Abra o programa em inglês (bandeirinha na tela inicial) e procure texto que ficou em português.

## 3. Anotar o que mudou

- `ROADMAP.md`: entrada da versão (o que foi feito e o que ficou decidido).
- `CHANGELOG.md`: seção nova no topo, em inglês e em português.

## 4. Testes

```powershell
python testes/rodar_testes.py
```

Tem que dar "X de X passaram". Depois abra o `taverna.py` duas vezes (uma como Mestre, outra como Jogador) e olhe.

## 5. Gerar o zip

```powershell
python gerar_release.py
```

Sai em `release/Taverna-vX.Y-windows.zip` (versão terminada em `.0` vira curta: `1.1.0` → `v1.1`).
Descompacte numa pasta qualquer, abra o `Taverna.exe` como Mestre e como Jogador e confira que funciona.

## 6. Enviar o código pro GitHub

```powershell
git add -A
git commit -m "v1.1: resumo do que mudou"
git push
```

Os commits usam o e-mail noreply do GitHub (`139470716+EuManel@users.noreply.github.com`), nunca o e-mail pessoal.
Confira com `git config user.email` antes do primeiro commit numa máquina nova.

## 7. Criar a Release no GitHub

Escreva as notas num arquivo (inglês e português — dá pra copiar a seção do CHANGELOG) e rode:

```powershell
gh release create v1.1 release\Taverna-v1.1-windows.zip --title "Taverna v1.1" --notes-file notas.txt
```

**Importante:** a tag tem que ser `vX.Y` ou `vX.Y.Z` (ex.: `v1.1`, `v1.0.1`). É ela que o aviso de versão nova da
tela inicial lê. Não marque como "pre-release" nem deixe como rascunho, senão ninguém é avisado.

A partir daí, quem abrir uma versão antiga vê "Nova versão v1.1 disponível — baixar" (o programa consulta no
máximo uma vez por dia, então pode levar até 24 h pra aparecer).

## 8. itch.io

Em https://itch.io/dashboard → Taverna → Edit game → Uploads: suba o zip novo e apague (ou esconda) o antigo.
Se quiser, poste um devlog com as notas da versão. O link do aviso leva pra https://omanel.itch.io/taverna.

## Lista rápida

- [ ] `APP_VERSAO` (e `VERSAO_PROTOCOLO`, se precisar)
- [ ] Textos novos no `en.json`
- [ ] `ROADMAP.md` e `CHANGELOG.md`
- [ ] Testes passando + programa aberto como Mestre e Jogador
- [ ] `python gerar_release.py` + `.exe` testado
- [ ] `git commit` + `git push`
- [ ] `gh release create vX.Y ...`
- [ ] Zip no itch.io
