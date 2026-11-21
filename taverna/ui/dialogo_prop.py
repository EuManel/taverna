"""
Editar um objeto (prop): nome, tamanho, giro, se é interativo, trancado, se bloqueia a visão,
se a luz está acesa — e o CONTEÚDO (itens guardados dentro, com imagem e descrição).
"""

import base64

from PyQt6.QtCore import QBuffer, QByteArray, QIODevice, QSize, Qt
from PyQt6.QtGui import QIcon, QImage, QPixmap
from PyQt6.QtWidgets import (QCheckBox, QComboBox, QDialog, QDialogButtonBox, QDoubleSpinBox, QFileDialog,
                             QFormLayout, QHBoxLayout, QLabel, QLineEdit, QListWidget,
                             QListWidgetItem, QPlainTextEdit, QPushButton, QSpinBox, QVBoxLayout,
                             QWidget)

from ..mesa.props import novo_id_item


def imagem_b64(caminho: str, lado: int = 256) -> str | None:
    """Abre uma imagem, diminui (no máximo 256 px) e devolve em PNG base64."""
    img = QImage(caminho)
    if img.isNull():
        return None
    if max(img.width(), img.height()) > lado:
        img = img.scaled(lado, lado, Qt.AspectRatioMode.KeepAspectRatio,
                         Qt.TransformationMode.SmoothTransformation)
    dados = QByteArray()
    buf = QBuffer(dados)
    buf.open(QIODevice.OpenModeFlag.WriteOnly)
    img.save(buf, "PNG")
    return base64.b64encode(bytes(dados)).decode("ascii")


def pixmap_b64(texto: str | None, lado: int = 48) -> QPixmap | None:
    if not texto:
        return None
    pm = QPixmap()
    if pm.loadFromData(base64.b64decode(texto)):
        return pm.scaled(lado, lado, Qt.AspectRatioMode.KeepAspectRatio,
                         Qt.TransformationMode.SmoothTransformation)
    return None


class DialogoItem(QDialog):
    """Um item do conteúdo: nome, quantidade, descrição e imagem."""

    def __init__(self, parent=None, item=None):
        super().__init__(parent)
        self.setWindowTitle("Item")
        self.item = dict(item or {"id": novo_id_item(), "nome": "", "qtd": 1, "desc": "", "img": None})
        self.nome = QLineEdit(self.item.get("nome", ""))
        self.nome.setPlaceholderText("ex.: Espada Lendária")
        self.qtd = QSpinBox()
        self.qtd.setRange(1, 99999)
        self.qtd.setValue(int(self.item.get("qtd", 1) or 1))
        self.desc = QPlainTextEdit(self.item.get("desc", ""))
        self.desc.setPlaceholderText("O que o jogador vê quando abre (descrição, efeito…)")
        self.desc.setMinimumHeight(100)
        self.img = QLabel()
        self.img.setFixedSize(72, 72)
        self.img.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.img.setStyleSheet("border: 1px dashed #5a4a32; border-radius: 6px;")
        escolher = QPushButton("Escolher imagem…")
        escolher.clicked.connect(self._imagem)
        tirar = QPushButton("Sem imagem")
        tirar.clicked.connect(lambda: self._definir_img(None))
        da_srd = QPushButton("📚 Do compêndio…")
        da_srd.setToolTip("Preenche com um item do SRD (equipamento ou item mágico)")
        da_srd.clicked.connect(self._do_compendio)
        linha_img = QHBoxLayout()
        linha_img.addWidget(self.img)
        col = QVBoxLayout()
        col.addWidget(escolher)
        col.addWidget(tirar)
        linha_img.addLayout(col)
        linha_img.addStretch()
        # Documento legível (bilhete, carta, mapa...): texto e/ou imagem que o jogador lê
        doc = self.item.get("doc") or {}
        self.eh_doc = QCheckBox("📜 É um documento que dá pra ler (bilhete, carta, mapa…)")
        self.eh_doc.setChecked(bool(self.item.get("doc")))
        self.doc_texto = QPlainTextEdit(doc.get("texto", ""))
        self.doc_texto.setPlaceholderText("O que está escrito. Dá pra usar **negrito**, *itálico* e # título.")
        self.doc_texto.setMinimumHeight(120)
        self.doc_img = QLabel()
        self.doc_img.setFixedSize(96, 96)
        self.doc_img.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.doc_img.setStyleSheet("border: 1px dashed #5a4a32; border-radius: 6px;")
        d_escolher = QPushButton("Imagem do documento…")
        d_escolher.setToolTip("Um desenho, mapa, carta escaneada… (até 1400 px)")
        d_escolher.clicked.connect(self._doc_imagem)
        d_tirar = QPushButton("Sem imagem")
        d_tirar.clicked.connect(lambda: self._definir_doc_img(None))
        ver = QPushButton("👁 Ver como o jogador")
        ver.clicked.connect(self._previa_doc)
        linha_doc = QHBoxLayout()
        linha_doc.addWidget(self.doc_img)
        cold = QVBoxLayout()
        for b in (d_escolher, d_tirar, ver):
            cold.addWidget(b)
        linha_doc.addLayout(cold)
        linha_doc.addStretch()
        self.caixa_doc = QWidget()
        ld = QVBoxLayout(self.caixa_doc)
        ld.setContentsMargins(0, 0, 0, 0)
        ld.addWidget(self.doc_texto)
        ld.addLayout(linha_doc)
        self.eh_doc.toggled.connect(self.caixa_doc.setVisible)
        self.caixa_doc.setVisible(self.eh_doc.isChecked())
        self._doc_img_b64 = None
        self._definir_doc_img(doc.get("img"))

        form = QFormLayout()
        form.addRow("Nome", self.nome)
        form.addRow("Quantidade", self.qtd)
        form.addRow("Descrição", self.desc)
        form.addRow("Imagem", linha_img)
        form.addRow(self.eh_doc)
        form.addRow(self.caixa_doc)
        botoes = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        botoes.accepted.connect(self.accept)
        botoes.rejected.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addWidget(da_srd)
        layout.addLayout(form)
        layout.addWidget(botoes)
        self.resize(520, 640 if self.eh_doc.isChecked() else 440)
        self._definir_img(self.item.get("img"))
        from .acabamento import iconizar
        iconizar(self)   # emoji → ícone do tema

    def _definir_doc_img(self, b64):
        self._doc_img_b64 = b64
        pm = pixmap_b64(b64, 92)
        self.doc_img.setPixmap(pm) if pm else self.doc_img.setText("—")

    def _doc_imagem(self):
        caminho, _ = QFileDialog.getOpenFileName(self, "Imagem do documento", "",
                                                 "Imagens (*.png *.jpg *.jpeg *.webp *.bmp)")
        if caminho:
            self._definir_doc_img(imagem_b64(caminho, 1400))

    def _previa_doc(self):
        from .janela_leitura import JanelaLeitura
        JanelaLeitura(self.resultado(), False, self).exec()

    def _definir_img(self, b64):
        self.item["img"] = b64
        pm = pixmap_b64(b64, 68)
        self.img.setPixmap(pm) if pm else self.img.setText("—")

    def _imagem(self):
        caminho, _ = QFileDialog.getOpenFileName(self, "Imagem do item", "",
                                                 "Imagens (*.png *.jpg *.jpeg *.webp *.bmp)")
        if caminho:
            self._definir_img(imagem_b64(caminho))

    def _do_compendio(self):
        from PyQt6.QtWidgets import QInputDialog
        from ..compendio.compendio import compendio
        c = compendio()
        entradas = c.entradas["itens_magicos"] + c.entradas["equipamento"]
        nomes = [e["nome"] for e in entradas]
        nome, ok = QInputDialog.getItem(self, "Do compêndio", "Item (digite pra buscar):", nomes, 0, True)
        if not ok:
            return
        entrada = next((e for e in entradas if e["nome"] == nome), None)
        if entrada is None:
            return
        import html
        import re
        texto = re.sub(r"<br\s*/?>|</p>|</h\d>", "\n", entrada["html"]())
        texto = html.unescape(re.sub(r"<[^>]+>", "", texto))
        linhas = [l.strip() for l in texto.split("\n") if l.strip()]
        self.nome.setText(nome)
        self.desc.setPlainText("\n".join(linhas[1:]))

    def resultado(self) -> dict:
        self.item.update(nome=self.nome.text().strip() or "Item", qtd=self.qtd.value(),
                         desc=self.desc.toPlainText().strip())
        if self.eh_doc.isChecked():
            self.item["doc"] = {"texto": self.doc_texto.toPlainText(), "img": self._doc_img_b64}
        else:
            self.item.pop("doc", None)
        return self.item


class DialogoProp(QDialog):
    def __init__(self, prop, parent=None):
        super().__init__(parent)
        self.prop = prop
        self.setWindowTitle(f"Objeto: {prop.nome}")
        self.itens = [dict(i) for i in prop.itens]

        self.nome = QLineEdit(prop.nome)
        self.w = QDoubleSpinBox()
        self.h = QDoubleSpinBox()
        for s, v in ((self.w, prop.w), (self.h, prop.h)):
            s.setRange(0.5, 50)
            s.setSingleStep(0.5)
            s.setDecimals(1)
            s.setSuffix(" m")
            s.setValue(v)
        self.angulo = QDoubleSpinBox()
        self.angulo.setRange(0, 359)
        self.angulo.setDecimals(0)
        self.angulo.setSingleStep(15)
        self.angulo.setWrapping(True)
        self.angulo.setSuffix("°")
        self.angulo.setValue(prop.angulo)
        tam = QHBoxLayout()
        tam.addWidget(self.w)
        tam.addWidget(QLabel("×"))
        tam.addWidget(self.h)

        self.interativo = QCheckBox("✦ Interativo (os jogadores podem abrir/mexer)")
        self.interativo.setChecked(prop.interativo)
        self.trancado = QCheckBox("🔒 Trancado (não abre até você destrancar)")
        self.trancado.setChecked(prop.trancado)
        self.perto = QCheckBox("Precisa estar perto (até 1,5 m) pra abrir")
        self.perto.setChecked(prop.perto)
        self.pegar = QCheckBox("🎒 Jogadores podem pegar os itens")
        self.pegar.setChecked(prop.pode_pegar)
        self.chave = QLineEdit(prop.chave)
        self.chave.setPlaceholderText("🗝 nome do item que destranca (opcional), ex.: Chave do baú")
        self.chave.setToolTip("Se o baú estiver trancado e o jogador tiver um item com esse nome\n"
                              "no inventário, ele destranca e abre.")
        try:
            from PyQt6.QtWidgets import QCompleter
            from .painel_propriedades import nomes_de_itens
            if prop.scene() is not None:
                self.chave.setCompleter(QCompleter(nomes_de_itens(prop.scene())))
        except Exception:
            pass
        self.gasta = QCheckBox("A chave some ao usar")
        self.gasta.setChecked(prop.gasta_chave)
        self.movel = QCheckBox("✋ Jogadores podem mover (empurrar, levar)")
        self.movel.setToolTip("O jogador arrasta se estiver perto; o objeto vai até onde ele alcança.\n"
                              "No combate, só na vez dele.")
        self.movel.setChecked(prop.movel)
        self.bloqueia = QCheckBox("🧱 Bloqueia a visão (e a luz)")
        self.bloqueia.setChecked(prop.bloqueia)
        self.luz = QCheckBox("💡 Luz acesa")
        self.luz.setChecked(prop.luz_acesa)
        self.luz.setVisible(bool(prop.luz))

        self.lista = QListWidget()
        self.lista.setIconSize(QSize(40, 40))
        self.lista.itemDoubleClicked.connect(lambda _: self._editar())
        add = QPushButton("＋ Item")
        add.setObjectName("primario")
        add.clicked.connect(self._adicionar)
        editar = QPushButton("Editar")
        editar.clicked.connect(self._editar)
        remover = QPushButton("Remover")
        remover.clicked.connect(self._remover)
        linha = QHBoxLayout()
        linha.addWidget(add)
        linha.addWidget(editar)
        linha.addWidget(remover)
        linha.addStretch()
        self._criar_sorteio(prop)
        self.caixa_conteudo = QWidget()
        lc = QVBoxLayout(self.caixa_conteudo)
        lc.setContentsMargins(0, 0, 0, 0)
        lc.addWidget(QLabel("<b>Conteúdo</b> (o que o jogador encontra quando abre)"))
        for w in (self.trancado, self.chave, self.gasta, self.perto, self.pegar):
            lc.addWidget(w)
        lc.addWidget(self.caixa_sorteio)
        lc.addWidget(self.lista, 1)
        lc.addLayout(linha)
        self.interativo.toggled.connect(self.caixa_conteudo.setEnabled)
        self.caixa_conteudo.setEnabled(prop.interativo)

        form = QFormLayout()
        form.addRow("Nome", self.nome)
        form.addRow("Tamanho", tam)
        form.addRow("Girado", self.angulo)
        botoes = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        botoes.accepted.connect(self._ok)
        botoes.rejected.connect(self.reject)
        from .tema import rolavel
        corpo = QWidget()
        layout = QVBoxLayout(corpo)
        externo = QVBoxLayout(self)
        externo.setContentsMargins(0, 0, 0, 8)
        externo.addWidget(rolavel(corpo), 1)
        layout.addLayout(form)
        layout.addWidget(self.movel)
        layout.addWidget(self.bloqueia)
        layout.addWidget(self.luz)
        layout.addWidget(self.interativo)
        layout.addWidget(self.caixa_conteudo, 1)
        # 🎒 (v0.48) qualquer objeto (ex.: uma imagem importada de espada) pode virar item coletável
        self.ck_coletavel = QCheckBox("🎒 Item coletável (o jogador pega e vai direto pro inventário)")
        self.ck_coletavel.setVisible(prop.tipo != "escada")
        layout.insertWidget(layout.indexOf(self.interativo), self.ck_coletavel)
        # 🏢 escada (v0.46.2): nada de baú (conteúdo, chave…); só a permissão do mestre
        self.escada_livre = QCheckBox("✅ Jogadores podem usar a escada (subir/descer)")
        self.escada_livre.setChecked(not prop.trancado)
        self.escada_livre.setVisible(prop.tipo == "escada")
        layout.addWidget(self.escada_livre)
        # (v0.48) pra onde a escada leva: andar de cima/baixo ou QUALQUER outro cenário (aba)
        self.cb_leva = QComboBox()
        self._destino_atual = None
        pai = self.parent()
        if prop.tipo == "escada" and hasattr(pai, "destinos_escada"):
            self.cb_leva.addItem("— nenhum lugar (o jogador não consegue usar)", None)
            cena_lig, _outra = pai._ponta_de(prop)
            for rot, dest in pai.destinos_escada(prop):
                self.cb_leva.addItem(rot, dest)
                if cena_lig is not None and dest is cena_lig:
                    self.cb_leva.setCurrentIndex(self.cb_leva.count() - 1)
            self._destino_atual = self.cb_leva.currentData()
            linha_leva = QHBoxLayout()
            linha_leva.addWidget(QLabel("🏢 Leva para"))
            linha_leva.addWidget(self.cb_leva, 1)
            layout.addLayout(linha_leva)
            dica = QLabel("Escolha a aba (cenário) onde a escada chega. Se lá tiver uma escada solta, ela vira a "
                          "outra ponta; se não, uma escada nova é posta no mesmo lugar. O jogador dá duplo "
                          "clique na escada (de perto) pra ir.")
            dica.setWordWrap(True)
            dica.setStyleSheet("font-size: 11px;")
            layout.addWidget(dica)
        if prop.tipo == "escada":
            self.interativo.setChecked(False)
            self.interativo.hide()
            self.caixa_conteudo.hide()
            self.movel.hide()
            layout.addStretch(1)
        externo.addWidget(botoes)
        self.lista.setMinimumHeight(110)
        self.resize(520, 720)
        self._recarregar()
        from .acabamento import iconizar
        iconizar(self)   # emoji → ícone do tema

    # ------------------------------------------------------------ recompensa aleatória
    def _criar_sorteio(self, prop):
        from PyQt6.QtWidgets import QComboBox, QGridLayout, QGroupBox, QSpinBox
        from ..jogo.sorteio import MOEDAS, RARIDADES, TIPOS, config_padrao
        cfg = dict(config_padrao(), **(prop.sorteio or {}))
        if not prop.sorteio:
            cfg["ativo"] = False
        self._sorteio_base = cfg
        caixa = QGroupBox("🎲 Recompensa aleatória")
        caixa.setCheckable(True)
        caixa.setChecked(bool(cfg.get("ativo")))
        caixa.setToolTip("Em vez de você escolher, o conteúdo é sorteado quando o PRIMEIRO jogador abrir.")
        miolo = QWidget()
        QVBoxLayout(caixa).addWidget(miolo)
        caixa.layout().setContentsMargins(6, 4, 6, 6)
        caixa.toggled.connect(miolo.setVisible)
        miolo.setVisible(caixa.isChecked())
        g = QGridLayout(miolo)
        g.setContentsMargins(0, 0, 0, 0)
        g.addWidget(QLabel("Itens de"), 0, 0, Qt.AlignmentFlag.AlignTop)
        linha_tab = QHBoxLayout()
        self.s_tabela = QComboBox()
        self.s_tabela.setToolTip("D&D 5e = itens do SRD. Ou uma tabela sua (Ordem Paranormal, Cyberpunk…).")
        self._tabela_salva = cfg.get("tabela")
        linha_tab.addWidget(self.s_tabela, 1)
        b_tab = QPushButton("📋 Tabelas…")
        b_tab.setToolTip("Criar/editar suas tabelas de sorteio")
        b_tab.clicked.connect(self._gerenciar_tabelas)
        linha_tab.addWidget(b_tab)
        g.addLayout(linha_tab, 0, 1)
        self.s_tabela.currentIndexChanged.connect(self._tabela_escolhida)
        g.addWidget(QLabel("Chance de vir vazio"), 1, 0)
        self.s_vazio = QSpinBox()
        self.s_vazio.setRange(0, 100)
        self.s_vazio.setSuffix(" %")
        self.s_vazio.setValue(int(cfg.get("vazio", 15)))
        g.addWidget(self.s_vazio, 1, 1)
        self.lbl_moedas = QLabel("Moedas")
        g.addWidget(self.lbl_moedas, 2, 0)
        self.s_moedas = QComboBox()
        for k, v in MOEDAS.items():
            self.s_moedas.addItem(v, k)
        self.s_moedas.setCurrentIndex(max(0, self.s_moedas.findData(cfg.get("moedas"))))
        g.addWidget(self.s_moedas, 2, 1)
        self.caixa_moedas = QWidget()
        lm = QHBoxLayout(self.caixa_moedas)
        lm.setContentsMargins(0, 0, 0, 0)
        self.s_dados_moeda = {}
        for sigla in ("PC", "PP", "PO", "PL"):
            ed = QLineEdit((cfg.get("moedas_dados") or {}).get(sigla, ""))
            ed.setPlaceholderText("—")
            ed.setToolTip(f"Dados pras moedas {sigla} (ex.: 2d6, 1d4+2, 10). Vazio = não vem.")
            ed.setMaximumWidth(64)
            lm.addWidget(QLabel(sigla))
            lm.addWidget(ed)
            self.s_dados_moeda[sigla] = ed
        lm.addStretch(1)
        g.addWidget(self.caixa_moedas, 3, 0, 1, 2)
        self.s_moedas.currentIndexChanged.connect(
            lambda _i: self.caixa_moedas.setVisible(self.s_moedas.currentData() == "personalizado"))
        self.caixa_moedas.setVisible(cfg.get("moedas") == "personalizado")
        g.addWidget(QLabel("Itens (fora as moedas)"), 20, 0)
        faixa = QHBoxLayout()
        self.s_min, self.s_max = QSpinBox(), QSpinBox()
        for s, v in ((self.s_min, cfg.get("itens_min", 0)), (self.s_max, cfg.get("itens_max", 2))):
            s.setRange(0, 10)
            s.setValue(int(v))
        faixa.addWidget(self.s_min)
        faixa.addWidget(QLabel("a"))
        faixa.addWidget(self.s_max)
        faixa.addStretch(1)
        g.addLayout(faixa, 20, 1)
        self.lbl_raridade = QLabel("Raridade máxima")
        g.addWidget(self.lbl_raridade, 21, 0)
        self.s_raridade = QComboBox()
        for r in RARIDADES:
            self.s_raridade.addItem(r.capitalize(), r)
        self.s_raridade.setCurrentIndex(max(0, self.s_raridade.findData(cfg.get("raridade_max"))))
        g.addWidget(self.s_raridade, 21, 1)
        self.lbl_pode = QLabel("Pode vir:")
        g.addWidget(self.lbl_pode, 22, 0, 1, 2)
        self.s_tipos = {}
        for k, (chave, (nome, _peso)) in enumerate(TIPOS.items()):
            ck = QCheckBox(nome)
            ck.setChecked(bool((cfg.get("tipos") or {}).get(chave)))
            self.s_tipos[chave] = ck
            g.addWidget(ck, 23 + k // 2, k % 2)
        linha_s = 23 + (len(TIPOS) + 1) // 2
        from PyQt6.QtWidgets import QPlainTextEdit
        self.s_proprios = QPlainTextEdit(cfg.get("proprios", ""))
        self.s_proprios.setPlaceholderText("Meus itens (um por linha):\nAmuleto do culto\nFlecha de prata ×5\n"
                                           "Carta do barão | Selada com cera vermelha")
        self.s_proprios.setFixedHeight(70)
        self.s_proprios.textChanged.connect(
            lambda: self.s_tipos["proprios"].setChecked(bool(self.s_proprios.toPlainText().strip())))
        g.addWidget(self.s_proprios, linha_s, 0, 1, 2)
        linha_s += 1
        self.s_status = QLabel()
        self.s_status.setWordWrap(True)
        g.addWidget(self.s_status, linha_s, 0, 1, 2)
        botoes = QHBoxLayout()
        testar = QPushButton("🎲 Testar um sorteio")
        testar.setToolTip("Mostra um exemplo do que poderia sair (não muda nada)")
        testar.clicked.connect(self._testar_sorteio)
        self.s_refazer = QPushButton("↺ Sortear de novo")
        self.s_refazer.setToolTip("Esvazia e volta a sortear quando alguém abrir de novo")
        self.s_refazer.clicked.connect(self._refazer_sorteio)
        botoes.addWidget(testar)
        botoes.addWidget(self.s_refazer)
        botoes.addStretch(1)
        g.addLayout(botoes, linha_s + 1, 0, 1, 2)
        self.caixa_sorteio = caixa
        self._carregar_tabelas()
        self._mostrar_status_sorteio()

    def _carregar_tabelas(self, selecionar: str | None = None):
        from ..jogo.tabelas import listar
        self._tabelas = {t["nome"]: t for t in listar()}
        salva = self._tabela_salva
        if salva and salva.get("nome") not in self._tabelas:
            self._tabelas[salva["nome"]] = salva   # veio de outro PC: usa a cópia que está no baú
        alvo = selecionar if selecionar is not None else (salva.get("nome") if salva else "")
        self.s_tabela.blockSignals(True)
        self.s_tabela.clear()
        from .acabamento import adicionar_item
        adicionar_item(self.s_tabela, "🐉 D&D 5e (padrão)", "")
        for nome in sorted(self._tabelas):
            adicionar_item(self.s_tabela, f"📋 {nome}", nome)
        self.s_tabela.setCurrentIndex(max(0, self.s_tabela.findData(alvo)))
        self.s_tabela.blockSignals(False)
        self._tabela_escolhida()

    def _tabela_escolhida(self, *_):
        dnd = not self.s_tabela.currentData()
        for w in (self.lbl_moedas, self.s_moedas, self.lbl_raridade, self.s_raridade, self.lbl_pode):
            w.setVisible(dnd)
        self.caixa_moedas.setVisible(dnd and self.s_moedas.currentData() == "personalizado")
        for k, ck in self.s_tipos.items():
            ck.setVisible(dnd)

    def _gerenciar_tabelas(self):
        from .dialogo_tabelas import DialogoTabelas
        d = DialogoTabelas(self, self.s_tabela.currentData() or "")
        d.exec()
        self._tabela_salva = None if not self.s_tabela.currentData() else self._tabela_salva
        self._carregar_tabelas(d.nome_atual() or self.s_tabela.currentData())

    def _config_sorteio(self):
        if not self.caixa_sorteio.isChecked():
            return None
        cfg = dict(self._sorteio_base)
        cfg.update({"ativo": True, "vazio": self.s_vazio.value(), "moedas": self.s_moedas.currentData(),
                    "itens_min": self.s_min.value(), "itens_max": self.s_max.value(),
                    "raridade_max": self.s_raridade.currentData(),
                    "moedas_dados": {k: ed.text().strip() for k, ed in self.s_dados_moeda.items()},
                    "tabela": self._tabelas.get(self.s_tabela.currentData()) if self.s_tabela.currentData() else None,
                    "proprios": self.s_proprios.toPlainText(),
                    "tipos": {k: ck.isChecked() for k, ck in self.s_tipos.items()}})
        return cfg

    def _mostrar_status_sorteio(self):
        if self._sorteio_base.get("sorteado"):
            self.s_status.setText(f"<b>Já sorteado:</b> {self._sorteio_base.get('resultado') or '—'}")
            self.s_refazer.setEnabled(True)
        else:
            self.s_status.setText("Ainda não sorteado — sai quando o primeiro jogador abrir.")
            self.s_refazer.setEnabled(False)

    def _testar_sorteio(self):
        from ..jogo.sorteio import config_padrao, sortear
        cfg = self._config_sorteio() or dict(config_padrao(), **{"vazio": self.s_vazio.value()})
        _itens, resumo = sortear(cfg)
        self.s_status.setText(f"<i>Exemplo:</i> {resumo}")

    def _refazer_sorteio(self):
        self._sorteio_base["sorteado"] = False
        self._sorteio_base["resultado"] = ""
        self.itens = []
        self._recarregar()
        self._mostrar_status_sorteio()

    def _recarregar(self):
        self.lista.clear()
        for it in self.itens:
            texto = ("📜 " if it.get("doc") else "") + it.get("nome", "?") + \
                (f"  ×{it['qtd']}" if it.get("qtd", 1) != 1 else "")
            item = QListWidgetItem(texto)
            pm = pixmap_b64(it.get("img"), 40)
            if pm:
                item.setIcon(QIcon(pm))
            item.setToolTip(it.get("desc", ""))
            self.lista.addItem(item)
        if not self.itens:
            vazio = QListWidgetItem("(vazio — clique em ＋ Item)")
            vazio.setFlags(Qt.ItemFlag.NoItemFlags)
            self.lista.addItem(vazio)

    def _adicionar(self):
        d = DialogoItem(self)
        if d.exec():
            self.itens.append(d.resultado())
            self._recarregar()

    def _editar(self):
        k = self.lista.currentRow()
        if 0 <= k < len(self.itens):
            d = DialogoItem(self, self.itens[k])
            if d.exec():
                self.itens[k] = d.resultado()
                self._recarregar()

    def _remover(self):
        k = self.lista.currentRow()
        if 0 <= k < len(self.itens):
            del self.itens[k]
            self._recarregar()

    def _ok(self):
        p = self.prop
        p.nome = self.nome.text().strip() or p.nome
        p.interativo = self.interativo.isChecked()
        p.trancado = self.trancado.isChecked()
        p.perto = self.perto.isChecked()
        p.pode_pegar = self.pegar.isChecked()
        p.chave = self.chave.text().strip()
        p.gasta_chave = self.gasta.isChecked()
        p.bloqueia = self.bloqueia.isChecked()
        p.movel = self.movel.isChecked()
        p.luz_acesa = self.luz.isChecked()
        p.itens = self.itens
        p.sorteio = self._config_sorteio()
        p.angulo = self.angulo.value()
        p.definir_tamanho(self.w.value(), self.h.value())
        if self.ck_coletavel.isChecked() and p.tipo != "escada":   # virou item coletável
            import base64
            from ..mesa.props import novo_id_item
            p.interativo, p.solto, p.trancado = True, True, False
            p.itens = [{"id": novo_id_item(), "nome": p.nome, "qtd": 1, "desc": "",
                        "img": base64.b64encode(p.imagem).decode() if p.imagem else None}]
        elif p.tipo == "escada":
            p.interativo, p.itens, p.sorteio = False, [], None
            pai = self.parent()
            novo = self.cb_leva.currentData() if self.cb_leva.count() else self._destino_atual
            if hasattr(pai, "aplicar_destino_escada") and self.cb_leva.count() and novo is not self._destino_atual:
                pai.aplicar_destino_escada(p, novo)
            if hasattr(pai, "liberar_escada"):   # vale pras duas pontas da escada
                pai.liberar_escada(p, self.escada_livre.isChecked())
            else:
                p.trancado = not self.escada_livre.isChecked()
        self.accept()
