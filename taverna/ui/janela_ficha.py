"""
Janela da ficha D&D 5e (a mesma pro mestre e pro jogador).

"Pacote" = tudo o que a janela edita:
  {"ficha": {...}, "pv": [atual, máx] | None, "desl": metros, "raca": str, "classe": str,
   "inventario": [itens]}
Os 5 últimos ficam no token.info (são os mesmos do painel INFORMAÇÕES).
"""

import html
import time

from PyQt6.QtCore import QMarginsF, QRectF, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QPageLayout, QPageSize, QPainter, QPdfWriter, QPen
from PyQt6.QtWidgets import (QAbstractItemView, QCheckBox, QComboBox, QDoubleSpinBox, QFileDialog,
                             QFormLayout, QGridLayout, QGroupBox, QHBoxLayout, QHeaderView,
                             QInputDialog, QLabel, QLineEdit, QListWidget, QMainWindow,
                             QMessageBox, QPlainTextEdit, QPushButton, QScrollArea, QSpinBox,
                             QTableWidget, QTableWidgetItem, QTabWidget, QVBoxLayout, QWidget)

from ..jogo import ficha as F

TENDENCIAS = ["", "Leal e Bom", "Neutro e Bom", "Caótico e Bom", "Leal e Neutro", "Neutro",
              "Caótico e Neutro", "Leal e Mau", "Neutro e Mau", "Caótico e Mau"]


# ====================================================================== pacote <-> token
def pacote_do_token(token) -> dict:
    info = token.info
    classe = info.get("classe", {}).get("v") or ""
    f = F.completar(getattr(token, "ficha", None))
    if not f.get("nome"):
        f["nome"] = token.nome
    if not f.get("jogador"):
        f["jogador"] = token.dono
    if not f.get("classe") and classe:
        partes = classe.rsplit(" ", 1)
        f["classe"] = partes[0]
        if len(partes) == 2 and partes[1].isdigit():
            f["nivel"] = int(partes[1])
    return {"ficha": f, "pv": info.get("pv", {}).get("v"), "desl": token.deslocamento or 9.0,
            "raca": info.get("raca", {}).get("v") or "", "classe": classe,
            "inventario": list(info.get("inventario", {}).get("v") or [])}


def aplicar_pacote(token, pacote: dict):
    """Grava o pacote no token (mantendo quem vê cada campo)."""
    f = F.completar(pacote.get("ficha"))
    token.ficha = f
    if pacote.get("pv") is not None:
        token.definir_info("pv", pacote["pv"])
    token.definir_info("desl", float(pacote.get("desl") or 0))
    token.definir_info("raca", pacote.get("raca", ""))
    classe = f"{f.get('classe', '')} {f.get('nivel', 1)}".strip() if f.get("classe") else pacote.get("classe", "")
    token.definir_info("classe", classe)
    token.definir_info("inventario", list(pacote.get("inventario") or []))


# ====================================================================== janela
class JanelaFicha(QMainWindow):
    salvar = pyqtSignal(dict)   # pacote

    def __init__(self, pacote: dict, titulo: str = "", parent=None, fonte=None, app_nome: str = "Mestre"):
        super().__init__(parent)
        self.fonte = fonte   # função que devolve o pacote atualizado (do token)
        from PyQt6.QtCore import QSettings, QTimer
        self.config = QSettings("Taverna", app_nome)
        self._timer_previa = QTimer(self)
        self._timer_previa.setSingleShot(True)
        self._timer_previa.setInterval(700)
        self._timer_previa.timeout.connect(self._atualizar_previa)
        self.setWindowTitle(f"📜 Ficha — {titulo or pacote['ficha'].get('nome') or 'personagem'}")
        self.resize(980, 760)
        self._carregando = False
        self.sujo = False
        self.pacote = pacote

        abas = QTabWidget()
        self.abas = abas
        self.aba_oficial = self._aba_oficial()
        abas.addTab(self.aba_oficial, "📄 Ficha do D&&D")
        abas.addTab(self._aba_principal(), "Principal")
        abas.addTab(self._aba_combate(), "Ataques e magias")
        abas.addTab(self._aba_inventario(), "Inventário")
        abas.addTab(self._aba_personagem(), "Personagem")
        abas.currentChanged.connect(lambda _: self._atualizar_previa() if abas.currentWidget() is self.aba_oficial else None)

        self.status = QLabel()
        self.status.setObjectName("dica")
        b_salvar = QPushButton("💾 Salvar ficha")
        b_salvar.setObjectName("primario")
        b_salvar.clicked.connect(self._salvar)
        b_importar = QPushButton("📥 Importar PDF…")
        b_importar.setToolTip("Lê uma ficha em PDF preenchível (a oficial do D&D 5e ou parecida)")
        b_importar.clicked.connect(self._importar_pdf)
        b_oficial = QPushButton("📤 Exportar ficha do D&&D…")
        b_oficial.setToolTip("Salva um PDF da ficha oficial preenchido com este personagem\n"
                             "(usa o PDF da ficha oficial que você indicou como modelo).")
        b_oficial.clicked.connect(self._preencher_oficial)
        b_exportar = QPushButton("Exportar no modelo do Taverna…")
        b_exportar.setToolTip("Gera um PDF com o modelo próprio do Taverna")
        b_exportar.clicked.connect(self._exportar_pdf)
        baixo = QHBoxLayout()
        for b in (b_importar, b_oficial, b_exportar):
            baixo.addWidget(b)
        baixo.addStretch()
        baixo.addWidget(self.status)
        baixo.addWidget(b_salvar)

        central = QWidget()
        lay = QVBoxLayout(central)
        lay.addWidget(abas, 1)
        lay.addLayout(baixo)
        self.setCentralWidget(central)
        self.carregar(pacote)
        if self._modelo():
            self._atualizar_previa()
        else:
            abas.setCurrentIndex(1)   # sem modelo ainda: abre na aba Principal
        from .acabamento import iconizar
        iconizar(self)   # emoji → ícone do tema

    def ir_para(self, aba: str):
        """(v0.48) "magias" → Ataques e magias · "inventario" → Inventário (atalhos do botão direito)."""
        procura = {"magias": "magia", "inventario": "invent"}.get(aba, aba)
        for k in range(self.abas.count()):
            if procura in self.abas.tabText(k).lower():
                self.abas.setCurrentIndex(k)
                return

    def changeEvent(self, event):
        from PyQt6.QtCore import QEvent
        if event.type() == QEvent.Type.ActivationChange and self.isActiveWindow():
            self.atualizar_de_fora()
        super().changeEvent(event)

    def atualizar_de_fora(self):
        # mudou fora da janela (dano, item pego...): recarrega se não tem nada sem salvar
        if self.fonte and not self.sujo:
            try:
                self.carregar(self.fonte())
            except RuntimeError:
                pass

    def closeEvent(self, event):
        if self.sujo:
            r = QMessageBox.question(self, "Ficha", "Salvar as alterações da ficha?",
                                     QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard
                                     | QMessageBox.StandardButton.Cancel)
            if r == QMessageBox.StandardButton.Cancel:
                event.ignore()
                return
            if r == QMessageBox.StandardButton.Save:
                self._salvar()
        super().closeEvent(event)

    # ------------------------------------------------------------ helpers de campos
    def _mudou(self, *_):
        if self._carregando:
            return
        self.sujo = True
        self.status.setText("● alterações não salvas")
        self._recalcular()
        if self.abas.currentWidget() is self.aba_oficial:
            self._timer_previa.start()

    # ------------------------------------------------------------ ficha oficial (modelo da pessoa)
    def _aba_oficial(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        self.lbl_modelo = QLabel()
        self.lbl_modelo.setWordWrap(True)
        self.lbl_modelo.setObjectName("dica")
        escolher = QPushButton("Escolher o PDF da ficha oficial…")
        escolher.setToolTip("Use a ficha oficial preenchível que você baixou (PDF com campos).\n"
                            "Fica guardado só no seu computador.")
        escolher.clicked.connect(self._escolher_modelo)
        topo = QHBoxLayout()
        topo.addWidget(self.lbl_modelo, 1)
        topo.addWidget(escolher)
        self.previa = QVBoxLayout()
        self.previa.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        conteudo = QWidget()
        conteudo.setLayout(self.previa)
        area = QScrollArea()
        area.setWidgetResizable(True)
        area.setWidget(conteudo)
        area.setStyleSheet("QScrollArea { background: #3a3026; }")
        lay.addLayout(topo)
        lay.addWidget(area, 1)
        return w

    def _modelo(self) -> str:
        import os
        caminho = self.config.value("modelo_ficha_pdf", "") or ""
        return caminho if caminho and os.path.exists(caminho) else ""

    def _escolher_modelo(self):
        caminho, _ = QFileDialog.getOpenFileName(self, "Ficha oficial do D&D (PDF preenchível)", "", "PDF (*.pdf)")
        if not caminho:
            return
        try:
            campos = F.ler_campos_pdf(caminho)
        except Exception as erro:
            QMessageBox.warning(self, "Não deu", f"Não consegui ler esse PDF:\n{erro}")
            return
        conhecidos = {F._norm(n) for n in campos} & (set(F.CAMPOS_PDF) | set(F.PERICIAS_PDF))
        if len(conhecidos) < 5:
            QMessageBox.warning(self, "Não parece a ficha",
                                "Esse PDF não tem os campos da ficha oficial (preenchível) do D&D 5e.\n"
                                "Escolha a versão com campos editáveis.")
            return
        self.config.setValue("modelo_ficha_pdf", caminho)
        self._atualizar_previa()

    def _pdf_oficial(self) -> tuple[bytes, int] | None:
        modelo = self._modelo()
        if not modelo:
            return None
        pacote = self.ler()
        pv = pacote.get("pv") or [0, 0]
        extras = {"raca": pacote.get("raca", ""), "desl": pacote.get("desl", 9), "pv": pv[0], "pv_max": pv[1],
                  "equipamento": "\n".join(f"{i.get('nome')}{' x' + str(i['qtd']) if i.get('qtd', 1) != 1 else ''}"
                                           for i in pacote.get("inventario") or [])}
        return F.preencher_pdf_bytes(modelo, pacote["ficha"], extras)

    def _atualizar_previa(self):
        import os
        while self.previa.count():
            w = self.previa.takeAt(0).widget()
            if w:
                w.deleteLater()
        modelo = self._modelo()
        if not modelo:
            self.lbl_modelo.setText(
                "Pra ver a ficha no visual oficial do D&D, escolha o PDF da ficha oficial preenchível que você "
                "baixou (só uma vez). O Taverna preenche ele com os dados deste personagem.\n"
                "Edite nas abas Principal, Ataques e magias, Inventário e Personagem.")
            return
        self.lbl_modelo.setText(f"Modelo: {os.path.basename(modelo)} · a prévia acompanha o que você edita "
                                f"nas outras abas.")
        try:
            dados, _n = self._pdf_oficial()
            import pypdfium2 as pdfium
            from PyQt6.QtGui import QImage, QPixmap
            doc = pdfium.PdfDocument(dados)
            doc.init_forms()
            largura = max(500, self.width() - 120)
            for k in range(len(doc)):
                pag = doc[k]
                escala = largura / pag.get_width()
                bm = pag.render(scale=escala, may_draw_forms=True)
                img = QImage(bm.buffer, bm.width, bm.height, bm.stride, QImage.Format.Format_BGR888).copy()
                rotulo = QLabel()
                rotulo.setPixmap(QPixmap.fromImage(img))
                self.previa.addWidget(rotulo)
        except Exception as erro:
            self.lbl_modelo.setText(f"Não consegui mostrar a ficha oficial: {erro}")

    def _linha(self, texto=""):
        e = QLineEdit(texto)
        e.textChanged.connect(self._mudou)
        return e

    def _spin(self, minimo, maximo, valor=0):
        s = QSpinBox()
        s.setRange(minimo, maximo)
        s.setValue(valor)
        s.valueChanged.connect(self._mudou)
        return s

    def _texto(self, dica=""):
        t = QPlainTextEdit()
        t.setPlaceholderText(dica)
        t.textChanged.connect(self._mudou)
        return t

    def _combo(self, itens, editavel=True):
        c = QComboBox()
        c.setEditable(editavel)
        c.addItems(itens)
        c.currentTextChanged.connect(self._mudou)
        return c

    @staticmethod
    def _rolar(widget):
        area = QScrollArea()
        area.setWidgetResizable(True)
        area.setWidget(widget)
        return area

    # ------------------------------------------------------------ abas
    def _aba_principal(self):
        from ..compendio.compendio import compendio
        try:
            c = compendio()
            racas = [""] + [e["nome"] for e in c.entradas["racas"]]
            classes = [""] + [e["nome"] for e in c.entradas["classes"]]
            antecedentes = [""] + [e["nome"] for e in c.entradas["antecedentes"]]
        except Exception:
            racas, classes, antecedentes = [""], [""], [""]
        self.nome = self._linha()
        self.jogador = self._linha()
        self.classe = self._combo(classes)
        self.nivel = self._spin(1, 20, 1)
        self.subclasse = self._linha()
        self.raca = self._combo(racas)
        self.antecedente = self._combo(antecedentes)
        self.tendencia = self._combo(TENDENCIAS)
        self.xp = self._spin(0, 999999)
        self.inspiracao = QCheckBox("Inspiração")
        self.inspiracao.toggled.connect(self._mudou)
        cab = QGridLayout()
        for k, (rot, w) in enumerate((("Nome", self.nome), ("Jogador", self.jogador),
                                      ("Classe", self.classe), ("Nível", self.nivel),
                                      ("Subclasse", self.subclasse), ("Raça", self.raca),
                                      ("Antecedente", self.antecedente), ("Tendência", self.tendencia),
                                      ("XP", self.xp))):
            cab.addWidget(QLabel(rot), k // 3, (k % 3) * 2)
            cab.addWidget(w, k // 3, (k % 3) * 2 + 1)
        cab.addWidget(self.inspiracao, 3, 0, 1, 2)
        caixa_cab = QGroupBox("Personagem")
        caixa_cab.setLayout(cab)

        # atributos
        self.atrib = {}
        self.atrib_mod = {}
        grade = QGridLayout()
        for k, (chave, nome, ab) in enumerate(F.ATRIBUTOS):
            s = self._spin(1, 30, 10)
            s.setToolTip(nome)
            m = QLabel("+0")
            m.setAlignment(Qt.AlignmentFlag.AlignCenter)
            m.setStyleSheet("font-size: 16pt; font-weight: bold; color: palette(highlight);")
            rot = QLabel(f"<b>{ab}</b>")
            rot.setAlignment(Qt.AlignmentFlag.AlignCenter)
            grade.addWidget(rot, 0, k)
            grade.addWidget(m, 1, k)
            grade.addWidget(s, 2, k)
            self.atrib[chave], self.atrib_mod[chave] = s, m
        caixa_atrib = QGroupBox("Atributos")
        caixa_atrib.setLayout(grade)

        # combate rápido
        self.ca = self._spin(0, 40, 10)
        self.desl = QDoubleSpinBox()
        self.desl.setRange(0, 999)
        self.desl.setSingleStep(1.5)
        self.desl.setDecimals(1)
        self.desl.setSuffix(" m")
        self.desl.valueChanged.connect(self._mudou)
        self.pv = self._spin(-999, 9999)
        self.pv_max = self._spin(0, 9999)
        self.pv_temp = self._spin(0, 999)
        self.dados_vida = self._linha()
        self.morte_s = self._spin(0, 3)
        self.morte_f = self._spin(0, 3)
        self.lbl_ini = QLabel()
        self.lbl_prof = QLabel()
        self.lbl_passiva = QLabel()
        for l in (self.lbl_ini, self.lbl_prof, self.lbl_passiva):
            l.setStyleSheet("font-size: 13pt; font-weight: bold; color: palette(highlight);")
        fc = QFormLayout()
        fc.addRow("Classe de Armadura", self.ca)
        fc.addRow("Iniciativa", self.lbl_ini)
        fc.addRow("Deslocamento", self.desl)
        fc.addRow("Bônus de proficiência", self.lbl_prof)
        linha_pv = QHBoxLayout()
        linha_pv.addWidget(self.pv)
        linha_pv.addWidget(QLabel("/"))
        linha_pv.addWidget(self.pv_max)
        fc.addRow("Pontos de vida", linha_pv)
        fc.addRow("PV temporários", self.pv_temp)
        fc.addRow("Dados de vida", self.dados_vida)
        linha_m = QHBoxLayout()
        linha_m.addWidget(QLabel("✔"))
        linha_m.addWidget(self.morte_s)
        linha_m.addWidget(QLabel("✖"))
        linha_m.addWidget(self.morte_f)
        fc.addRow("Testes contra a morte", linha_m)
        fc.addRow("Percepção passiva", self.lbl_passiva)
        caixa_combate = QGroupBox("Combate")
        caixa_combate.setLayout(fc)

        # salvaguardas
        self.salv = {}
        self.salv_val = {}
        gs = QGridLayout()
        for k, (chave, nome, _ab) in enumerate(F.ATRIBUTOS):
            cb = QCheckBox(nome)
            cb.toggled.connect(self._mudou)
            v = QLabel("+0")
            gs.addWidget(cb, k, 0)
            gs.addWidget(v, k, 1)
            self.salv[chave], self.salv_val[chave] = cb, v
        caixa_salv = QGroupBox("Testes de resistência")
        caixa_salv.setLayout(gs)

        # perícias
        self.per = {}
        self.per_esp = {}
        self.per_val = {}
        gp = QGridLayout()
        gp.addWidget(QLabel("<small>prof.</small>"), 0, 0)
        gp.addWidget(QLabel("<small>espec.</small>"), 0, 1)
        for k, (chave, nome, atrib) in enumerate(F.PERICIAS, start=1):
            cb = QCheckBox(f"{nome} ({next(a for c, _, a in F.ATRIBUTOS if c == atrib)})")
            cb.toggled.connect(self._mudou)
            esp = QCheckBox()
            esp.setToolTip("Especialização (dobra a proficiência)")
            esp.toggled.connect(self._mudou)
            v = QLabel("+0")
            v.setMinimumWidth(30)
            gp.addWidget(cb, k, 0)
            gp.addWidget(esp, k, 1)
            gp.addWidget(v, k, 2)
            self.per[chave], self.per_esp[chave], self.per_val[chave] = cb, esp, v
        gp.setRowStretch(len(F.PERICIAS) + 1, 1)
        caixa_per = QGroupBox("Perícias")
        caixa_per.setLayout(gp)

        esq = QVBoxLayout()
        esq.addWidget(caixa_atrib)
        esq.addWidget(caixa_salv)
        esq.addWidget(caixa_combate)
        esq.addStretch()
        meio = QHBoxLayout()
        meio.addLayout(esq, 3)
        meio.addWidget(caixa_per, 2)
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.addWidget(caixa_cab)
        lay.addLayout(meio)
        return self._rolar(w)

    def _aba_combate(self):
        self.ataques = QTableWidget(0, 3)
        self.ataques.setHorizontalHeaderLabels(["Ataque", "Bônus", "Dano / tipo"])
        self.ataques.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.ataques.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.ataques.verticalHeader().hide()
        self.ataques.itemChanged.connect(self._mudou)
        add = QPushButton("＋ Ataque")
        add.clicked.connect(lambda: (self.ataques.insertRow(self.ataques.rowCount()), self._mudou()))
        rem = QPushButton("Remover")
        rem.clicked.connect(lambda: (self.ataques.removeRow(self.ataques.currentRow()), self._mudou())
                            if self.ataques.currentRow() >= 0 else None)
        la = QHBoxLayout()
        la.addWidget(add)
        la.addWidget(rem)
        la.addStretch()
        caixa_at = QGroupBox("Ataques")
        v = QVBoxLayout(caixa_at)
        v.addWidget(self.ataques)
        v.addLayout(la)

        self.conj = QComboBox()
        self.conj.addItem("(automático pela classe)", "")
        for chave, nome, _ in F.ATRIBUTOS:
            self.conj.addItem(nome, chave)
        self.conj.currentIndexChanged.connect(self._mudou)
        self.lbl_cd = QLabel()
        self.lbl_atq = QLabel()
        for l in (self.lbl_cd, self.lbl_atq):
            l.setStyleSheet("font-size: 13pt; font-weight: bold; color: palette(highlight);")
        self.magias = QListWidget()
        self.magias.setToolTip("Duplo clique: ver a magia no compêndio")
        self.magias.itemDoubleClicked.connect(self._ver_magia)
        addm = QPushButton("＋ Magia do compêndio…")
        addm.clicked.connect(self._add_magia)
        addl = QPushButton("＋ Outra…")
        addl.clicked.connect(self._add_magia_livre)
        remm = QPushButton("Remover")
        remm.clicked.connect(self._rem_magia)
        lm = QHBoxLayout()
        for b in (addm, addl, remm):
            lm.addWidget(b)
        lm.addStretch()
        self.espacos = {}
        ge = QGridLayout()
        ge.addWidget(QLabel("<b>Espaços de magia</b> (usados / total)"), 0, 0, 1, 6)
        for n in range(1, 10):
            u = self._spin(0, 9)
            t = self._spin(0, 9)
            ge.addWidget(QLabel(f"{n}º"), 1 + (n - 1) // 3, ((n - 1) % 3) * 3)
            ge.addWidget(u, 1 + (n - 1) // 3, ((n - 1) % 3) * 3 + 1)
            ge.addWidget(t, 1 + (n - 1) // 3, ((n - 1) % 3) * 3 + 2)
            self.espacos[str(n)] = (u, t)
        fm = QFormLayout()
        fm.addRow("Atributo de conjuração", self.conj)
        fm.addRow("CD das magias", self.lbl_cd)
        fm.addRow("Ataque mágico", self.lbl_atq)
        caixa_mag = QGroupBox("Magias")
        vm = QVBoxLayout(caixa_mag)
        vm.addLayout(fm)
        vm.addWidget(self.magias, 1)
        vm.addLayout(lm)
        vm.addLayout(ge)
        w = QWidget()
        lay = QHBoxLayout(w)
        lay.addWidget(caixa_at, 1)
        lay.addWidget(caixa_mag, 1)
        return w

    def _aba_inventario(self):
        self.inv = QTableWidget(0, 3)
        self.inv.setHorizontalHeaderLabels(["Item", "Qtd", "Descrição"])
        self.inv.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.inv.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.inv.verticalHeader().hide()
        self.inv.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.inv.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.inv.itemDoubleClicked.connect(lambda _: self._ler_item() if self._item_atual_doc() else self._editar_item())
        add = QPushButton("＋ Item…")
        add.setObjectName("primario")
        add.clicked.connect(self._add_item)
        ed = QPushButton("Editar")
        ed.clicked.connect(self._editar_item)
        rem = QPushButton("Remover")
        rem.clicked.connect(self._rem_item)
        ler = QPushButton("📖 Ler")
        ler.setToolTip("Ler um documento (bilhete, carta, mapa…)")
        ler.clicked.connect(self._ler_item)
        li = QHBoxLayout()
        for b in (add, ed, rem, ler):
            li.addWidget(b)
        li.addStretch()
        self.moedas = {}
        lmo = QHBoxLayout()
        for chave, rot in (("pc", "PC"), ("pp", "PP"), ("pe", "PE"), ("po", "PO"), ("pl", "PL")):
            s = self._spin(0, 9999999)
            lmo.addWidget(QLabel(f"<b>{rot}</b>"))
            lmo.addWidget(s)
            self.moedas[chave] = s
        lmo.addStretch()
        dica = QLabel("Os itens pegos de baús e criaturas aparecem aqui sozinhos. "
                      "Duplo clique pra ver/editar.")
        dica.setObjectName("dica")
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.addWidget(QLabel("<b>Moedas</b>"))
        lay.addLayout(lmo)
        lay.addWidget(self.inv, 1)
        lay.addLayout(li)
        lay.addWidget(dica)
        self.itens = []
        return w

    def _aba_personagem(self):
        self.idiomas = self._texto("Idiomas, armas, armaduras e ferramentas que domina…")
        self.caract = self._texto("Características e traços (de raça, classe, talentos…)")
        self.personalidade = self._texto()
        self.ideais = self._texto()
        self.vinculos = self._texto()
        self.defeitos = self._texto()
        self.aparencia = self._texto("Idade, altura, olhos, cabelo…")
        self.historia = self._texto("A história do personagem")
        self.notas_f = self._texto("Anotações livres")
        g = QGridLayout()
        for k, (rot, w) in enumerate((("Idiomas e proficiências", self.idiomas),
                                      ("Características e traços", self.caract),
                                      ("Traços de personalidade", self.personalidade),
                                      ("Ideais", self.ideais), ("Vínculos", self.vinculos),
                                      ("Defeitos", self.defeitos), ("Aparência", self.aparencia),
                                      ("História", self.historia), ("Anotações", self.notas_f))):
            caixa = QGroupBox(rot)
            v = QVBoxLayout(caixa)
            w.setMinimumHeight(90)
            v.addWidget(w)
            g.addWidget(caixa, k // 2, k % 2)
        w = QWidget()
        w.setLayout(g)
        return self._rolar(w)

    # ------------------------------------------------------------ carregar / ler
    def carregar(self, pacote: dict):
        self._carregando = True
        self.pacote = pacote
        f = F.completar(pacote.get("ficha"))
        self.nome.setText(f["nome"])
        self.jogador.setText(f["jogador"])
        self.classe.setCurrentText(f["classe"])
        self.nivel.setValue(int(f["nivel"] or 1))
        self.subclasse.setText(f.get("subclasse", ""))
        self.raca.setCurrentText(pacote.get("raca") or f.get("raca", ""))
        self.antecedente.setCurrentText(f["antecedente"])
        self.tendencia.setCurrentText(f["tendencia"])
        self.xp.setValue(int(f["xp"] or 0))
        self.inspiracao.setChecked(bool(f["inspiracao"]))
        for chave, s in self.atrib.items():
            s.setValue(int(f["atributos"].get(chave, 10)))
        for chave, cb in self.salv.items():
            cb.setChecked(chave in f["salvaguardas"])
        for chave in self.per:
            self.per[chave].setChecked(chave in f["pericias"])
            self.per_esp[chave].setChecked(chave in f["especialista"])
        self.ca.setValue(int(f["ca"] or 10))
        self.desl.setValue(float(pacote.get("desl") or 0))
        pv = pacote.get("pv") or [0, 0]
        self.pv_max.setValue(int(pv[1]))
        self.pv.setValue(int(pv[0]))
        self.pv_temp.setValue(int(f["pv_temp"] or 0))
        self.dados_vida.setText(f["dados_vida"])
        self.morte_s.setValue(int(f["morte_sucessos"] or 0))
        self.morte_f.setValue(int(f["morte_falhas"] or 0))
        self.ataques.setRowCount(0)
        for a in f["ataques"]:
            r = self.ataques.rowCount()
            self.ataques.insertRow(r)
            for k, campo in enumerate(("nome", "bonus", "dano")):
                self.ataques.setItem(r, k, QTableWidgetItem(str(a.get(campo, ""))))
        self.conj.setCurrentIndex(max(0, self.conj.findData(f.get("conjuracao_atrib", ""))))
        self._magias = [dict(m) for m in f["magias"]]
        self._mostrar_magias()
        for n, (u, t) in self.espacos.items():
            us, tot = f["espacos"].get(n, [0, 0])
            u.setValue(int(us))
            t.setValue(int(tot))
        for chave, s in self.moedas.items():
            s.setValue(int(f["moedas"].get(chave, 0) or 0))
        self.itens = [dict(i) for i in pacote.get("inventario") or []]
        self._mostrar_itens()
        for w, chave in ((self.idiomas, "idiomas_prof"), (self.caract, "caracteristicas"),
                         (self.personalidade, "personalidade"), (self.ideais, "ideais"),
                         (self.vinculos, "vinculos"), (self.defeitos, "defeitos"),
                         (self.aparencia, "aparencia"), (self.historia, "historia"),
                         (self.notas_f, "notas")):
            w.setPlainText(f.get(chave, ""))
        self._carregando = False
        self.sujo = False
        self.status.setText("")
        self._recalcular()

    def ler(self) -> dict:
        f = F.ficha_vazia()
        f.update(nome=self.nome.text().strip(), jogador=self.jogador.text().strip(),
                 classe=self.classe.currentText().strip(), nivel=self.nivel.value(),
                 subclasse=self.subclasse.text().strip(), raca=self.raca.currentText().strip(),
                 antecedente=self.antecedente.currentText().strip(),
                 tendencia=self.tendencia.currentText().strip(), xp=self.xp.value(),
                 inspiracao=self.inspiracao.isChecked(), ca=self.ca.value(),
                 pv_temp=self.pv_temp.value(), dados_vida=self.dados_vida.text().strip(),
                 morte_sucessos=self.morte_s.value(), morte_falhas=self.morte_f.value(),
                 conjuracao_atrib=self.conj.currentData() or "", magias=self._magias,
                 idiomas_prof=self.idiomas.toPlainText(), caracteristicas=self.caract.toPlainText(),
                 personalidade=self.personalidade.toPlainText(), ideais=self.ideais.toPlainText(),
                 vinculos=self.vinculos.toPlainText(), defeitos=self.defeitos.toPlainText(),
                 aparencia=self.aparencia.toPlainText(), historia=self.historia.toPlainText(),
                 notas=self.notas_f.toPlainText())
        f["atributos"] = {k: s.value() for k, s in self.atrib.items()}
        f["salvaguardas"] = [k for k, cb in self.salv.items() if cb.isChecked()]
        f["pericias"] = [k for k, cb in self.per.items() if cb.isChecked()]
        f["especialista"] = [k for k, cb in self.per_esp.items() if cb.isChecked()]
        f["ataques"] = []
        for r in range(self.ataques.rowCount()):
            linha = [(self.ataques.item(r, k).text() if self.ataques.item(r, k) else "") for k in range(3)]
            if any(linha):
                f["ataques"].append({"nome": linha[0], "bonus": linha[1], "dano": linha[2]})
        f["espacos"] = {n: [u.value(), t.value()] for n, (u, t) in self.espacos.items()}
        f["moedas"] = {k: s.value() for k, s in self.moedas.items()}
        maximo = self.pv_max.value()
        return {"ficha": f, "pv": [self.pv.value(), maximo] if maximo > 0 else None,
                "desl": self.desl.value(), "raca": f["raca"],
                "classe": f"{f['classe']} {f['nivel']}".strip() if f["classe"] else "",
                "inventario": self.itens}

    # ------------------------------------------------------------ contas automáticas
    def _recalcular(self):
        f = self.ler()["ficha"]
        for chave, m in self.atrib_mod.items():
            m.setText(F.sinal(F.mod(f["atributos"][chave])))
        for chave, v in self.salv_val.items():
            v.setText(F.sinal(F.bonus_salvaguarda(f, chave)))
        for chave, v in self.per_val.items():
            v.setText(F.sinal(F.bonus_pericia(f, chave)))
            self.per_esp[chave].setEnabled(self.per[chave].isChecked())
        self.lbl_ini.setText(F.sinal(F.iniciativa(f)))
        self.lbl_prof.setText(F.sinal(F.bonus_prof(f["nivel"])))
        self.lbl_passiva.setText(str(F.percepcao_passiva(f)))
        cd, atq = F.cd_magia(f), F.ataque_magia(f)
        self.lbl_cd.setText(str(cd) if cd is not None else "—")
        self.lbl_atq.setText(F.sinal(atq) if atq is not None else "—")

    # ------------------------------------------------------------ magias
    def _mostrar_magias(self):
        self.magias.clear()
        for m in sorted(self._magias, key=lambda m: (m.get("nivel", 0), m.get("nome", ""))):
            nv = "Truque" if m.get("nivel", 0) == 0 else f"{m.get('nivel')}º"
            self.magias.addItem(f"[{nv}]  {m.get('nome', '')}")

    def _magias_srd(self):
        from ..compendio.compendio import compendio
        return compendio().entradas["magias"]

    def _add_magia(self):
        entradas = self._magias_srd()
        nomes = [e["nome"] for e in entradas]
        nome, ok = QInputDialog.getItem(self, "Magia", "Magia (digite pra buscar):", nomes, 0, True)
        if not ok or not nome:
            return
        e = next((x for x in entradas if x["nome"] == nome), None)
        nivel = e["dados"].get("level", 0) if e and e.get("dados") else 0
        self._magias.append({"nome": nome, "nivel": nivel})
        self._mostrar_magias()
        self._mudou()

    def _add_magia_livre(self):
        nome, ok = QInputDialog.getText(self, "Magia", "Nome da magia:")
        if not ok or not nome.strip():
            return
        nivel, ok = QInputDialog.getInt(self, "Magia", "Nível (0 = truque):", 1, 0, 9)
        if ok:
            self._magias.append({"nome": nome.strip(), "nivel": nivel})
            self._mostrar_magias()
            self._mudou()

    def _rem_magia(self):
        k = self.magias.currentRow()
        if k < 0:
            return
        ordem = sorted(self._magias, key=lambda m: (m.get("nivel", 0), m.get("nome", "")))
        self._magias.remove(ordem[k])
        self._mostrar_magias()
        self._mudou()

    def _ver_magia(self, item):
        nome = item.text().split("]  ", 1)[-1]
        e = next((x for x in self._magias_srd() if x["nome"] == nome), None)
        if e is None:
            return
        from PyQt6.QtWidgets import QDialog, QTextBrowser
        from .biblioteca import ESTILO_FICHA
        d = QDialog(self)
        d.setWindowTitle(nome)
        t = QTextBrowser()
        t.setHtml(ESTILO_FICHA + e["html"]())
        v = QVBoxLayout(d)
        v.addWidget(t)
        d.resize(560, 600)
        d.exec()

    # ------------------------------------------------------------ inventário
    def _mostrar_itens(self):
        self.inv.setRowCount(len(self.itens))
        for r, it in enumerate(self.itens):
            self.inv.setItem(r, 0, QTableWidgetItem(("📜 " if it.get("doc") else "") + it.get("nome", "?")))
            self.inv.setItem(r, 1, QTableWidgetItem(str(it.get("qtd", 1))))
            desc = (it.get("desc") or "").replace("\n", " ")
            if it.get("origem"):
                desc = f"[de {it['origem']}] " + desc
            self.inv.setItem(r, 2, QTableWidgetItem(desc[:200]))

    def _add_item(self):
        from .dialogo_prop import DialogoItem
        d = DialogoItem(self)
        if d.exec():
            self.itens.append(d.resultado())
            self._mostrar_itens()
            self._mudou()

    def _editar_item(self):
        r = self.inv.currentRow()
        if not 0 <= r < len(self.itens):
            return
        from .dialogo_prop import DialogoItem
        d = DialogoItem(self, self.itens[r])
        if d.exec():
            self.itens[r] = d.resultado()
            self._mostrar_itens()
            self._mudou()

    def _item_atual_doc(self):
        r = self.inv.currentRow()
        return 0 <= r < len(self.itens) and bool(self.itens[r].get("doc"))

    def _ler_item(self):
        r = self.inv.currentRow()
        if not 0 <= r < len(self.itens) or not self.itens[r].get("doc"):
            return
        from .janela_leitura import JanelaLeitura
        JanelaLeitura(self.itens[r], False, self).exec()

    def _rem_item(self):
        r = self.inv.currentRow()
        if 0 <= r < len(self.itens):
            del self.itens[r]
            self._mostrar_itens()
            self._mudou()

    # ------------------------------------------------------------ salvar / PDF
    def _salvar(self):
        pacote = self.ler()
        self.salvar.emit(pacote)
        self.sujo = False
        self.status.setText(f"✔ salva às {time.strftime('%H:%M')}")

    def _importar_pdf(self):
        caminho, _ = QFileDialog.getOpenFileName(self, "Importar ficha em PDF", "", "PDF (*.pdf)")
        if not caminho:
            return
        try:
            campos = F.ler_campos_pdf(caminho)
        except Exception as erro:
            QMessageBox.warning(self, "Não deu", f"Não consegui ler esse PDF:\n{erro}")
            return
        if not campos:
            QMessageBox.information(self, "Sem campos",
                                    "Esse PDF não tem campos preenchíveis (pode ser uma ficha escaneada\n"
                                    "ou impressa em PDF). Só dá pra importar ficha preenchível.")
            return
        f, extras = F.de_campos(campos)
        pacote = self.ler()
        pacote["ficha"] = f
        if "pv" in extras or "pv_max" in extras:
            pacote["pv"] = [extras.get("pv", extras.get("pv_max", 0)), extras.get("pv_max", extras.get("pv", 0))]
        if "desl" in extras:
            pacote["desl"] = extras["desl"]
        if extras.get("raca"):
            pacote["raca"] = extras["raca"]
        if extras.get("equipamento"):
            # cada linha/vírgula do campo "Equipamento" vira um item (os que já estavam continuam)
            from ..mesa.props import novo_id_item
            nomes = [n.strip() for n in extras["equipamento"].replace("\n", ",").split(",") if n.strip()]
            existentes = {i.get("nome", "").lower() for i in pacote["inventario"]}
            for n in nomes:
                if n.lower() not in existentes:
                    pacote["inventario"].append({"id": novo_id_item(), "nome": n, "qtd": 1, "desc": "", "img": None})
        self.carregar(pacote)
        self._mudou()
        lidos = len([v for v in campos.values() if str(v).strip()])
        QMessageBox.information(self, "Importado",
                                f"Li {lidos} campos preenchidos. Confira a ficha e clique em 💾 Salvar.")

    def _exportar_pdf(self):
        pacote = self.ler()
        nome = pacote["ficha"].get("nome") or "ficha"
        caminho, _ = QFileDialog.getSaveFileName(self, "Exportar ficha", f"{nome}.pdf", "PDF (*.pdf)")
        if caminho:
            exportar_pdf_taverna(pacote, caminho)
            self.status.setText("✔ PDF exportado")

    def _preencher_oficial(self):
        modelo = self._modelo()
        if not modelo:
            self._escolher_modelo()
            modelo = self._modelo()
            if not modelo:
                return
        pacote = self.ler()
        nome = pacote["ficha"].get("nome") or "ficha"
        destino, _ = QFileDialog.getSaveFileName(self, "Salvar ficha preenchida", f"{nome} (preenchida).pdf",
                                                 "PDF (*.pdf)")
        if not destino:
            return
        pv = pacote.get("pv") or [0, 0]
        extras = {"raca": pacote.get("raca", ""), "desl": pacote.get("desl", 9), "pv": pv[0], "pv_max": pv[1],
                  "equipamento": "\n".join(f"{i.get('nome')}{' x' + str(i['qtd']) if i.get('qtd', 1) != 1 else ''}"
                                           for i in pacote.get("inventario") or [])}
        try:
            n = F.preencher_pdf_oficial(modelo, destino, pacote["ficha"], extras)
        except Exception as erro:
            QMessageBox.warning(self, "Não deu", f"Não consegui preencher:\n{erro}")
            return
        if n == 0:
            QMessageBox.information(self, "Nenhum campo",
                                    "Não achei campos conhecidos nesse PDF. Ele é a ficha oficial preenchível?")
        else:
            QMessageBox.information(self, "Pronto", f"Preenchi {n} campos e salvei em:\n{destino}")


# ====================================================================== PDF do Taverna
def exportar_pdf_taverna(pacote: dict, caminho: str):
    """Ficha num PDF A4 com o visual do Taverna (não usa o modelo da Wizards)."""
    f = F.completar(pacote["ficha"])
    pv = pacote.get("pv") or [0, 0]
    pdf = QPdfWriter(caminho)
    pdf.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
    pdf.setPageMargins(QMarginsF(12, 12, 12, 12), QPageLayout.Unit.Millimeter)
    pdf.setResolution(150)
    p = QPainter(pdf)
    L = pdf.width()
    tinta = QColor("#2a2018")
    dourado = QColor("#8a6420")

    def fonte(tam, negrito=False, serif=False):
        ft = QFont("Georgia" if serif else "Arial")
        ft.setPointSizeF(tam)
        ft.setBold(negrito)
        p.setFont(ft)

    def caixa(x, y, w, h, titulo=None):
        p.setPen(QPen(dourado, 2))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(QRectF(x, y, w, h), 10, 10)
        if titulo:
            fonte(7, True)
            p.setPen(dourado)
            p.drawText(QRectF(x + 10, y + 4, w - 20, 20), Qt.AlignmentFlag.AlignLeft, titulo.upper())

    def texto(x, y, w, h, t, tam=9, negrito=False, alin=Qt.AlignmentFlag.AlignLeft, cor=tinta):
        fonte(tam, negrito)
        p.setPen(cor)
        p.drawText(QRectF(x, y, w, h), alin | Qt.TextFlag.TextWordWrap, str(t))

    # cabeçalho
    fonte(22, True, True)
    p.setPen(tinta)
    p.drawText(QRectF(0, 0, L * 0.5, 60), Qt.AlignmentFlag.AlignVCenter, f["nome"] or "Personagem")
    cab = [("Classe e nível", f"{f['classe']} {f['nivel']}" + (f" ({f['subclasse']})" if f.get("subclasse") else "")),
           ("Raça", pacote.get("raca", "")), ("Antecedente", f["antecedente"]),
           ("Tendência", f["tendencia"]), ("Jogador", f["jogador"]), ("XP", f["xp"])]
    for k, (rot, val) in enumerate(cab):
        x = L * 0.5 + (k % 3) * L * 0.1667
        y = (k // 3) * 34
        texto(x, y, L * 0.16, 18, val, 9, True)
        texto(x, y + 16, L * 0.16, 14, rot.upper(), 6, cor=dourado)
    y0 = 80
    # atributos
    for k, (chave, nome, ab) in enumerate(F.ATRIBUTOS):
        y = y0 + k * 110
        caixa(0, y, 120, 100)
        texto(0, y + 6, 120, 16, ab, 8, True, Qt.AlignmentFlag.AlignHCenter, dourado)
        texto(0, y + 22, 120, 40, F.sinal(F.mod(f["atributos"][chave])), 22, True, Qt.AlignmentFlag.AlignHCenter)
        texto(0, y + 66, 120, 24, f["atributos"][chave], 11, False, Qt.AlignmentFlag.AlignHCenter)
    # salvaguardas e perícias
    x1 = 140
    caixa(x1, y0, 330, 170, "Testes de resistência")
    for k, (chave, nome, _) in enumerate(F.ATRIBUTOS):
        marca = "●" if chave in f["salvaguardas"] else "○"
        texto(x1 + 12, y0 + 26 + k * 23, 310, 20, f"{marca}  {F.sinal(F.bonus_salvaguarda(f, chave))}   {nome}", 8.5)
    caixa(x1, y0 + 180, 330, 470, "Perícias")
    for k, (chave, nome, atrib) in enumerate(F.PERICIAS):
        marca = "◉" if chave in f["especialista"] else ("●" if chave in f["pericias"] else "○")
        ab = next(a for c, _, a in F.ATRIBUTOS if c == atrib)
        texto(x1 + 12, y0 + 206 + k * 24.5, 310, 20, f"{marca}  {F.sinal(F.bonus_pericia(f, chave))}   {nome} ({ab})", 8.5)
    # combate
    x2 = 490
    w2 = L * 0.32
    rapidos = [("CA", f["ca"]), ("Inic.", F.sinal(F.iniciativa(f))),
               ("Desloc.", f"{pacote.get('desl', 9):g}m".replace(".", ",")),
               ("Prof.", F.sinal(F.bonus_prof(f['nivel']))), ("Passiva", F.percepcao_passiva(f))]
    larg = (w2 - 4 * 8) / 5
    for k, (rot, val) in enumerate(rapidos):
        x = x2 + k * (larg + 8)
        caixa(x, y0, larg, 80)
        texto(x, y0 + 8, larg, 36, val, 15, True, Qt.AlignmentFlag.AlignHCenter)
        texto(x, y0 + 52, larg, 20, rot.upper(), 6, False, Qt.AlignmentFlag.AlignHCenter, dourado)
    caixa(x2, y0 + 92, w2, 90, "Pontos de vida")
    texto(x2, y0 + 118, w2, 40, f"{pv[0]} / {pv[1]}" + (f"   (+{f['pv_temp']} temp.)" if f.get("pv_temp") else ""),
          18, True, Qt.AlignmentFlag.AlignHCenter)
    texto(x2 + 10, y0 + 158, w2 - 20, 20, f"Dados de vida: {f['dados_vida'] or '—'}", 8)
    caixa(x2, y0 + 194, w2, 200, "Ataques")
    for k, a in enumerate(f["ataques"][:7]):
        texto(x2 + 12, y0 + 220 + k * 24, w2 - 24, 20, f"{a.get('nome', '')}   {a.get('bonus', '')}   {a.get('dano', '')}", 8.5)
    caixa(x2, y0 + 404, w2, 246, "Magias")
    cd = F.cd_magia(f)
    linhas = []
    if cd is not None:
        linhas.append(f"CD {cd} · ataque {F.sinal(F.ataque_magia(f))}")
    for m in sorted(f["magias"], key=lambda m: (m.get("nivel", 0), m.get("nome", ""))):
        linhas.append(f"[{'T' if m.get('nivel', 0) == 0 else m.get('nivel')}] {m.get('nome')}")
    texto(x2 + 12, y0 + 428, w2 - 24, 214, "\n".join(linhas[:12]) + (" …" if len(linhas) > 12 else ""), 8)
    # coluna direita: equipamento
    x3 = x2 + w2 + 16
    w3 = L - x3
    caixa(x3, y0, w3, 300, "Equipamento")
    moedas = "  ".join(f"{k.upper()} {v}" for k, v in f["moedas"].items() if v)
    itens = "\n".join(f"• {i.get('nome')}{' ×' + str(i['qtd']) if i.get('qtd', 1) != 1 else ''}"
                      for i in pacote.get("inventario") or [])
    texto(x3 + 12, y0 + 26, w3 - 24, 268, (moedas + "\n" if moedas else "") + itens, 8)
    caixa(x3, y0 + 310, w3, 340, "Idiomas e proficiências")
    texto(x3 + 12, y0 + 336, w3 - 24, 306, f["idiomas_prof"], 8)
    # parte de baixo
    yb = y0 + 670
    blocos = [("Características e traços", f["caracteristicas"]),
              ("Personalidade · ideais · vínculos · defeitos",
               "\n".join(t for t in (f["personalidade"], f["ideais"], f["vinculos"], f["defeitos"]) if t)),
              ("História", f["historia"])]
    wb = (L - 2 * 16) / 3
    for k, (rot, t) in enumerate(blocos):
        x = k * (wb + 16)
        caixa(x, yb, wb, pdf.height() - yb - 30, rot)
        texto(x + 12, yb + 26, wb - 24, pdf.height() - yb - 64, t, 8)
    texto(0, pdf.height() - 22, L, 20, "Gerado pelo Taverna · regras do SRD 5.1 (CC BY 4.0)", 6,
          alin=Qt.AlignmentFlag.AlignRight, cor=dourado)
    p.end()
