"""Janelinhas de diálogo (criar/editar token)."""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPixmap
from PyQt6.QtWidgets import (QColorDialog, QComboBox, QDialog, QFileDialog,
                             QFormLayout, QHBoxLayout, QLabel, QLineEdit,
                             QPushButton, QVBoxLayout)

from ..config import TAMANHOS_TOKEN, TIPOS_TOKEN

CORES_SUGERIDAS = {
    "jogador": "#3f6b4a",
    "criatura": "#6e2a2f",
    "npc": "#3b5470",
}


def reduzir_imagem(dados: bytes, lado: int) -> bytes:
    """Reduz pra no máx. `lado` px e regrava (PNG se tiver transparência, senão JPEG). Falhou: devolve igual."""
    from PyQt6.QtCore import QBuffer, QIODevice
    from PyQt6.QtGui import QImage
    img = QImage.fromData(dados)
    if img.isNull() or max(img.width(), img.height()) <= lado:
        return dados
    img = img.scaled(lado, lado, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
    buf = QBuffer()
    buf.open(QIODevice.OpenModeFlag.WriteOnly)
    img.save(buf, "PNG" if img.hasAlphaChannel() else "JPG", 90)
    return bytes(buf.data())


class DialogoToken(QDialog):
    """Cria um token novo ou edita um existente (passe `token` para editar)."""

    def __init__(self, parent=None, token=None, tipo_inicial="criatura", jogadores=None, da_biblioteca=False,
                 do_jogador=False):
        super().__init__(parent)
        self.do_jogador = do_jogador   # (v0.48) o jogador editando o PRÓPRIO token: nome, cor, imagem, retrato
        # novo token ou token da biblioteca: botões Cancelar / Salvar na biblioteca / Colocar na mesa (v0.42)
        self.modelo = token is None or da_biblioteca
        self.acao = "salvar"
        self.setWindowTitle(("Meu token" if do_jogador else "Editar token") if token else "Novo token")
        self.setMinimumWidth(380)
        self.imagem = token.imagem if token else None
        self.cor = QColor(token.cor if token else CORES_SUGERIDAS.get(tipo_inicial, "#6e2a2f"))

        titulo = QLabel("Editar token" if token else "Novo token")
        titulo.setObjectName("titulo")

        self.nome = QLineEdit(token.nome if token else "")
        self.nome.setPlaceholderText("Ex.: Goblin, Aelar, Taverneiro...")

        self.tipo = QComboBox()
        for chave, (rotulo, _, _) in TIPOS_TOKEN.items():
            self.tipo.addItem(rotulo, chave)
        self.tipo.setCurrentIndex(self.tipo.findData(token.tipo if token else tipo_inicial))
        self.tipo.currentIndexChanged.connect(self._tipo_mudou)

        self.tamanho = QComboBox()
        for rotulo, n in TAMANHOS_TOKEN.items():
            self.tamanho.addItem(rotulo, n)
        self.tamanho.setCurrentIndex(max(0, self.tamanho.findData(token.tamanho if token else 1)))

        self.botao_cor = QPushButton()
        self.botao_cor.clicked.connect(self._escolher_cor)
        self._pintar_botao_cor()

        self.preview = QLabel()
        self.preview.setFixedSize(56, 56)
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview.setStyleSheet("border: 1px solid #3b2f24; border-radius: 28px;")
        botao_img = QPushButton("Escolher imagem…")
        botao_img.clicked.connect(self._escolher_imagem)
        self.botao_tirar = QPushButton("Remover")
        self.botao_tirar.clicked.connect(self._tirar_imagem)
        linha_img = QHBoxLayout()
        linha_img.addWidget(self.preview)
        linha_img.addWidget(botao_img)
        self.botao_cortar = QPushButton("✂")
        self.botao_cortar.setToolTip("Remover o fundo da imagem (com IA ou na mão)")
        self.botao_cortar.clicked.connect(lambda: self._cortar_fundo("imagem"))
        linha_img.addWidget(self.botao_cortar)
        linha_img.addWidget(self.botao_tirar)
        linha_img.addStretch()
        self._atualizar_preview()

        # Retrato (opcional): imagem em pé pros retratos do grupo e do combate. Sem ele, usa a de cima.
        self.retrato = getattr(token, "retrato", None) if token else None
        self.preview_retrato = QLabel()
        self.preview_retrato.setFixedSize(44, 56)
        self.preview_retrato.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_retrato.setStyleSheet("border: 1px solid palette(mid); border-radius: 4px;")
        botao_ret = QPushButton("Escolher retrato…")
        botao_ret.setToolTip("Imagem em pé (tipo pintura) que aparece nos retratos do grupo, à esquerda da mesa,\n"
                             "e na ordem do combate. Sem retrato, usa a imagem do token.")
        botao_ret.clicked.connect(self._escolher_retrato)
        self.botao_tirar_ret = QPushButton("Remover")
        self.botao_tirar_ret.clicked.connect(self._tirar_retrato)
        linha_ret = QHBoxLayout()
        linha_ret.addWidget(self.preview_retrato)
        linha_ret.addWidget(botao_ret)
        self.botao_cortar_ret = QPushButton("✂")
        self.botao_cortar_ret.setToolTip("Remover o fundo do retrato (com IA ou na mão)")
        self.botao_cortar_ret.clicked.connect(lambda: self._cortar_fundo("retrato"))
        linha_ret.addWidget(self.botao_cortar_ret)
        linha_ret.addWidget(self.botao_tirar_ret)
        linha_ret.addStretch()
        self._atualizar_preview_retrato()

        # Lista de jogadores conectados, mas dá pra digitar qualquer nome
        # (o vínculo vale quando alguém entrar com esse nome)
        self.dono = QComboBox()
        self.dono.setEditable(True)
        self.dono.addItem("")
        for nome in (jogadores or []):
            self.dono.addItem(nome)
        atual = token.dono if token else ""
        if atual and self.dono.findText(atual) < 0:
            self.dono.addItem(atual)
        self.dono.setCurrentText(atual)
        self.dono.lineEdit().setPlaceholderText("Quem controla este token")

        form = QFormLayout()
        form.setSpacing(10)
        form.addRow("Nome", self.nome)
        form.addRow("Tipo", self.tipo)
        form.addRow("Tamanho", self.tamanho)
        form.addRow("Cor", self.botao_cor)
        form.addRow("Imagem", linha_img)
        form.addRow("Retrato", linha_ret)
        form.addRow("Jogador", self.dono)
        # (v0.73) peça na Mesa 3D: ficha redonda ou standee (a imagem em pé, virada pra câmera)
        self.estilo = QComboBox()
        self.estilo.addItem("Ficha redonda", "ficha")
        self.estilo.addItem("Standee (imagem em pé)", "standee")
        self.estilo.setCurrentIndex(max(0, self.estilo.findData(getattr(token, "estilo", "ficha") if token else "ficha")))
        self.estilo.setToolTip("Como o token aparece na Mesa 3D: ficha redonda, ou a imagem em pé num suporte\n"
                               "(standee), sempre virada pra câmera. Dá pra trocar todos em Mesa → Peças dos tokens.")
        form.addRow("Peça (3D)", self.estilo)
        # (v0.77) standee sem moldura/base: pra PNG recortado (o personagem em pé no cenário)
        from PyQt6.QtWidgets import QCheckBox
        self.sem_borda = QCheckBox("Sem bordas")
        self.sem_borda.setChecked(bool(getattr(token, "sem_borda", False)) if token else False)
        self.sem_borda.setToolTip("Só a imagem, sem moldura, fundo e base — pra PNG recortado")
        form.addRow("", self.sem_borda)
        # (v0.78) tamanho da imagem do standee
        from PyQt6.QtWidgets import QSpinBox
        self.escala_standee = QSpinBox()
        self.escala_standee.setRange(30, 300)
        self.escala_standee.setSingleStep(10)
        self.escala_standee.setSuffix(" %")
        self.escala_standee.setValue(int(round(float(getattr(token, "escala_standee", 1.0) if token else 1.0) * 100)))
        form.addRow("Escala da imagem", self.escala_standee)

        def _mostrar_standee(_i=None):
            eh = self.estilo.currentData() == "standee"
            form.setRowVisible(self.sem_borda, eh)
            form.setRowVisible(self.escala_standee, eh)
        self.estilo.currentIndexChanged.connect(_mostrar_standee)
        _mostrar_standee()
        if do_jogador:   # tipo, tamanho e dono quem decide é o mestre
            for w in (self.tipo, self.tamanho, self.dono, self.estilo, self.sem_borda, self.escala_standee):
                form.setRowVisible(w, False)
            self.botao_cor.setToolTip("A cor do seu token. Também vira a cor da sua luvinha (o mouse que os outros veem).")
        self._tipo_mudou()
        if self.modelo:   # já sai pronto pra jogo (vai pro painel de informações do token)
            from PyQt6.QtWidgets import QDoubleSpinBox, QSpinBox
            self.pv = QSpinBox()
            self.pv.setRange(0, 9999)
            self.pv.setSpecialValueText("—")
            self.pv.setValue(int(getattr(token, "pv", 0) or 0))
            self.desl = QDoubleSpinBox()
            self.desl.setRange(0, 60)
            self.desl.setSingleStep(1.5)
            self.desl.setDecimals(1)
            self.desl.setSuffix(" m")
            self.desl.setSpecialValueText("—")
            self.desl.setValue(float(getattr(token, "desl", 0) or 0))
            form.addRow("PV", self.pv)
            form.addRow("Deslocamento", self.desl)

        cancelar = QPushButton("Cancelar")
        cancelar.clicked.connect(self.reject)
        botoes = QHBoxLayout()
        botoes.addStretch()
        botoes.addWidget(cancelar)
        if self.modelo:
            salvar = QPushButton("💾 Salvar na biblioteca")
            salvar.setToolTip("Guarda este token pronto na Biblioteca → Tokens, pra colocar na mesa quando quiser.")
            salvar.clicked.connect(lambda: self._confirmar("salvar"))
            botoes.addWidget(salvar)
            ok = QPushButton("⬤ Colocar na mesa")
            ok.clicked.connect(lambda: self._confirmar("mesa"))
        else:
            ok = QPushButton("Salvar")
            ok.clicked.connect(lambda: self._confirmar("salvar"))
        ok.setObjectName("primario")
        ok.setDefault(True)
        botoes.addWidget(ok)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(14)
        layout.addWidget(titulo)
        layout.addLayout(form)
        layout.addLayout(botoes)
        from .acabamento import iconizar
        iconizar(self)   # emoji → ícone do tema

    def _tipo_mudou(self):
        e_jogador = self.tipo.currentData() == "jogador"
        self.dono.setEnabled(e_jogador)

    def _pintar_botao_cor(self):
        self.botao_cor.setText(self.cor.name().upper())
        texto = "#111" if self.cor.lightness() > 140 else "#eee"
        self.botao_cor.setStyleSheet(
            f"background: {self.cor.name()}; color: {texto}; border: 1px solid #3b2f24;")

    def _escolher_cor(self):
        cor = QColorDialog.getColor(self.cor, self, "Cor do token")
        if cor.isValid():
            self.cor = cor
            self._pintar_botao_cor()

    def _escolher_imagem(self):
        caminho, _ = QFileDialog.getOpenFileName(
            self, "Imagem do token", "", "Imagens (*.png *.jpg *.jpeg *.webp *.bmp *.gif)")
        if caminho:
            with open(caminho, "rb") as f:
                self.imagem = f.read()
            self._atualizar_preview()

    def _tirar_imagem(self):
        self.imagem = None
        self._atualizar_preview()

    def _cortar_fundo(self, qual):
        """✂ (v0.47) abre o removedor de fundo (com IA) na imagem ou no retrato do token."""
        dados = getattr(self, qual, None)
        if not dados:
            return
        from .remover_fundo import DialogoRemoverFundo
        d = DialogoRemoverFundo(dados, self.nome.text().strip(), self)
        if d.exec():
            setattr(self, qual, d.resultado())
            if qual == "imagem":
                self._atualizar_preview()
            else:
                self._atualizar_preview_retrato()

    def _atualizar_preview(self):
        self.botao_tirar.setEnabled(bool(self.imagem))
        self.botao_cortar.setEnabled(bool(self.imagem))
        if self.imagem:
            pm = QPixmap()
            pm.loadFromData(self.imagem)
            self.preview.setPixmap(pm.scaled(
                52, 52, Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation))
        else:
            self.preview.setPixmap(QPixmap())
            self.preview.setText("—")

    def _escolher_retrato(self):
        caminho, _ = QFileDialog.getOpenFileName(
            self, "Retrato do personagem", "", "Imagens (*.png *.jpg *.jpeg *.webp *.bmp *.gif)")
        if caminho:
            with open(caminho, "rb") as f:
                self.retrato = reduzir_imagem(f.read(), 512)   # retrato não precisa ser enorme (vai pela rede)
            self._atualizar_preview_retrato()

    def _tirar_retrato(self):
        self.retrato = None
        self._atualizar_preview_retrato()

    def _atualizar_preview_retrato(self):
        self.botao_tirar_ret.setEnabled(bool(self.retrato))
        self.botao_cortar_ret.setEnabled(bool(self.retrato))
        if self.retrato:
            pm = QPixmap()
            pm.loadFromData(self.retrato)
            pm = pm.scaled(42, 54, Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                           Qt.TransformationMode.SmoothTransformation)
            self.preview_retrato.setPixmap(pm.copy((pm.width() - 42) // 2, 0, 42, 54))
        else:
            self.preview_retrato.setPixmap(QPixmap())
            self.preview_retrato.setText("—")

    def _confirmar(self, acao="salvar"):
        if not self.nome.text().strip():
            self.nome.setFocus()
            self.nome.setPlaceholderText("Dá um nome pro token 🙂")
            return
        self.acao = acao
        self.accept()

    def dados(self) -> dict:
        tipo = self.tipo.currentData()
        d = {
            "nome": self.nome.text().strip(),
            "tipo": tipo,
            "cor": self.cor.name(),
            "tamanho": self.tamanho.currentData(),
            "imagem": self.imagem,
            "retrato": self.retrato,
            "dono": self.dono.currentText().strip() if tipo == "jogador" else "",
            "estilo": self.estilo.currentData() or "ficha",
            "sem_borda": self.sem_borda.isChecked(),
            "escala_standee": self.escala_standee.value() / 100,
        }
        if self.modelo:
            d["pv"] = self.pv.value()
            d["desl"] = self.desl.value()
        return d


def caminho_como_conectar():
    """(v0.81) O guia de conexão: do lado do .exe, dentro do .exe (PyInstaller) ou na raiz do projeto.
    (v1.0) Virou HOW_TO_CONNECT.txt (inglês primeiro, português depois); o nome antigo ainda vale."""
    import os
    import sys
    lugares = []
    if getattr(sys, "frozen", False):
        lugares.append(os.path.dirname(sys.executable))
        lugares.append(getattr(sys, "_MEIPASS", ""))
    lugares.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    for nome in ("HOW_TO_CONNECT.txt", "COMO_CONECTAR.txt"):
        for pasta in lugares:
            arq = os.path.join(pasta, nome)
            if pasta and os.path.isfile(arq):
                return arq
    return None


def _rotulo_porta():
    """"Porta" aqui é a porta de REDE (no inglês "Port", não "Door")."""
    from ..idioma import ingles
    return "Port" if ingles() else "Porta"


def abrir_como_conectar(parent=None) -> bool:
    from PyQt6.QtCore import QUrl
    from PyQt6.QtGui import QDesktopServices
    arq = caminho_como_conectar()
    if arq and QDesktopServices.openUrl(QUrl.fromLocalFile(arq)):
        return True
    from PyQt6.QtWidgets import QMessageBox
    QMessageBox.information(parent, "Como conectar", "Não achei o HOW_TO_CONNECT.txt.")
    return False


def botao_como_conectar(parent):
    b = QPushButton("❓ Como conectar")
    b.setAutoDefault(False)
    b.clicked.connect(lambda: abrir_como_conectar(parent))
    return b


class DialogoAbrirTaverna(QDialog):
    """Mestre: escolher a porta e ver qual IP passar pros amigos."""

    def __init__(self, parent, enderecos, porta_padrao):
        super().__init__(parent)
        self.setWindowTitle("Abrir a taverna")
        self.setMinimumWidth(440)
        titulo = QLabel("Abrir a taverna")
        titulo.setObjectName("titulo")

        from PyQt6.QtWidgets import QSpinBox
        self.porta = QSpinBox()
        self.porta.setRange(1024, 65535)
        self.porta.setValue(porta_padrao)

        if enderecos:
            linhas = []
            for ip, nome in enderecos:
                destaque = ip.startswith("26.")
                cor = "#c9a24a" if destaque else "#9c8d76"
                peso = "bold" if destaque else "normal"
                linhas.append(f"<span style='color:{cor}; font-weight:{peso}'>{ip}</span>"
                              f"<span style='color:#9c8d76'> — {nome}</span>")
            texto_ips = "<br>".join(linhas)
            if not any(ip.startswith("26.") for ip, _ in enderecos):
                texto_ips += ("<br><br><span style='color:#a8323e'>Não achei o Radmin VPN. "
                              "Abra o Radmin e entre na rede antes.</span>")
        else:
            texto_ips = "Nenhuma rede encontrada."
        ips = QLabel(texto_ips)
        ips.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        ips.setWordWrap(True)

        dica = QLabel("O Taverna também tenta abrir <b>pela internet</b> sozinho (pede pro roteador): se der "
                      "certo, aparece um <b>código da sala</b> embaixo, na barra — é só mandar pros amigos. Se não "
                      "der, eles entram pelo IP do Radmin, como sempre. Na primeira vez, o Windows vai perguntar sobre "
                      "o firewall: marque <b>as duas</b> caixinhas (privada e pública) e permita.")
        dica.setObjectName("dica")
        dica.setWordWrap(True)

        form = QFormLayout()
        form.addRow(_rotulo_porta(), self.porta)
        form.addRow("Seus IPs", ips)

        ok = QPushButton("Abrir")
        ok.setObjectName("primario")
        ok.setDefault(True)
        ok.clicked.connect(self.accept)
        cancelar = QPushButton("Cancelar")
        cancelar.clicked.connect(self.reject)
        botoes = QHBoxLayout()
        botoes.addWidget(botao_como_conectar(self))
        botoes.addStretch()
        botoes.addWidget(cancelar)
        botoes.addWidget(ok)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(14)
        layout.addWidget(titulo)
        layout.addLayout(form)
        layout.addWidget(dica)
        layout.addLayout(botoes)
        from .acabamento import iconizar
        iconizar(self)   # emoji → ícone do tema


class DialogoConectar(QDialog):
    """Player: nome, IP e porta do mestre."""

    def __init__(self, parent, nome="", ip="", porta=7777, erro=""):
        super().__init__(parent)
        self.setWindowTitle("Entrar na taverna")
        self.setMinimumWidth(400)
        titulo = QLabel("Entrar na taverna")
        titulo.setObjectName("titulo")

        from PyQt6.QtWidgets import QSpinBox
        self.nome = QLineEdit(nome)
        self.nome.setPlaceholderText("Seu nome (o mestre vincula seu token a ele)")
        self.nome.setMaxLength(30)
        self.ip = QLineEdit(ip)
        self.ip.setPlaceholderText("Código da sala (TAV-…) ou IP do mestre, ex.: 26.12.34.56")
        self.porta = QSpinBox()
        self.porta.setRange(1024, 65535)
        self.porta.setValue(porta)

        form = QFormLayout()
        form.setSpacing(10)
        form.addRow("Nome", self.nome)
        form.addRow("Código ou IP", self.ip)
        form.addRow(_rotulo_porta(), self.porta)

        self.erro = QLabel(erro)
        self.erro.setStyleSheet("color: #d0606b;")
        self.erro.setWordWrap(True)
        self.erro.setVisible(bool(erro))

        ok = QPushButton("Entrar")
        ok.setObjectName("primario")
        ok.setDefault(True)
        ok.clicked.connect(self._confirmar)
        sair = QPushButton("Sair")
        sair.clicked.connect(self.reject)
        botoes = QHBoxLayout()
        botoes.addWidget(botao_como_conectar(self))
        botoes.addStretch()
        botoes.addWidget(sair)
        botoes.addWidget(ok)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(14)
        layout.addWidget(titulo)
        layout.addLayout(form)
        layout.addWidget(self.erro)
        layout.addLayout(botoes)
        from .acabamento import iconizar
        iconizar(self)   # emoji → ícone do tema

    def _confirmar(self):
        if not self.nome.text().strip():
            self.nome.setFocus()
            return
        if not self.ip.text().strip():
            self.ip.setFocus()
            return
        self.accept()


class DialogoNovaAventura(QDialog):
    """Mestre: nome da aventura e tema, antes de abrir a mesa."""

    def __init__(self, parent, pasta: str, existe):
        super().__init__(parent)
        from ..temas import TEMAS, TEMA_PADRAO
        self.pasta = pasta
        self.existe = existe  # função(nome) -> bool
        self.setWindowTitle("Nova sessão")
        self.setMinimumWidth(440)
        titulo = QLabel("Nova aventura")
        titulo.setObjectName("titulo")

        self.nome = QLineEdit()
        self.nome.setPlaceholderText("Ex.: Cromocópia")
        self.nome.setMaxLength(60)
        self.nome.textChanged.connect(self._validar)

        self.tema = QComboBox()
        for chave, t in TEMAS.items():
            self.tema.addItem(f"{t['nome']}  —  {t['descricao']}", chave)
        self.tema.setCurrentIndex(self.tema.findData(TEMA_PADRAO))

        self.aviso = QLabel()
        self.aviso.setObjectName("dica")
        self.aviso.setWordWrap(True)

        form = QFormLayout()
        form.setSpacing(10)
        form.addRow("Nome", self.nome)
        form.addRow("Tema", self.tema)

        self.ok = QPushButton("Começar")
        self.ok.setObjectName("primario")
        self.ok.setDefault(True)
        self.ok.clicked.connect(self.accept)
        cancelar = QPushButton("Cancelar")
        cancelar.clicked.connect(self.reject)
        botoes = QHBoxLayout()
        botoes.addStretch()
        botoes.addWidget(cancelar)
        botoes.addWidget(self.ok)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(14)
        layout.addWidget(titulo)
        layout.addLayout(form)
        layout.addWidget(self.aviso)
        layout.addLayout(botoes)
        self._validar()
        from .acabamento import iconizar
        iconizar(self)   # emoji → ícone do tema

    def _validar(self):
        nome = self.nome.text().strip()
        if not nome:
            self.ok.setEnabled(False)
            self.aviso.setText(f"Ela vai ser salva em:\n{self.pasta}")
        elif self.existe(nome):
            self.ok.setEnabled(False)
            self.aviso.setText("Já existe uma aventura com esse nome. "
                               "Use “Continuar” ou “Abrir sessão” pra abrir ela.")
        else:
            self.ok.setEnabled(True)
            self.aviso.setText(f"Ela vai ser salva em:\n{self.pasta}")

    def dados(self) -> tuple[str, str]:
        return self.nome.text().strip(), self.tema.currentData()
