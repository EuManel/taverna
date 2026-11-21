"""
🧙 Biblioteca de tokens (v0.42) — "o mestre cria os próprios tokens e spawna na hora que quiser".

O mestre monta o token uma vez (nome, tipo, tamanho, cor, imagem, retrato, PV, deslocamento) e
SALVA. Depois é só escolher na aba Tokens da Biblioteca e "Colocar na mesa" — quantas vezes quiser,
como um objeto. Fica em Documentos/Taverna/Tokens salvos (um .json por token, com as imagens dentro).
Substitui o "colocar monstro do compêndio" (o compêndio de D&D saiu da biblioteca na v0.42).
"""

import base64
import json
import os
import re
import uuid
from types import SimpleNamespace

from PyQt6.QtCore import QSize, QStandardPaths, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPixmap
from PyQt6.QtWidgets import (QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem, QMessageBox,
                             QPushButton, QVBoxLayout, QWidget)


def pasta_tokens() -> str:
    docs = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DocumentsLocation) \
        or os.path.expanduser("~")
    pasta = os.path.join(docs, "Taverna", "Tokens salvos")
    os.makedirs(pasta, exist_ok=True)
    return pasta


def _b64(dados):
    return base64.b64encode(dados).decode("ascii") if dados else None


def _bytes(texto):
    try:
        return base64.b64decode(texto) if texto else None
    except (ValueError, TypeError):
        return None


def salvar(d: dict, ident: str | None = None) -> str:
    """Grava um token (dados do DialogoToken). Devolve o id."""
    ident = ident or uuid.uuid4().hex[:12]
    registro = {"id": ident, "nome": d.get("nome", "Token"), "tipo": d.get("tipo", "criatura"),
                "cor": d.get("cor", "#6e2a2f"), "tamanho": int(d.get("tamanho", 1)), "dono": d.get("dono", ""),
                "pv": int(d.get("pv") or 0), "desl": float(d.get("desl") or 0),
                "imagem": _b64(d.get("imagem")), "retrato": _b64(d.get("retrato")),
                "estilo": d.get("estilo") if d.get("estilo") in ("ficha", "standee") else "ficha",   # (v0.73)
                "sem_borda": bool(d.get("sem_borda", False)),
                "escala_standee": float(d.get("escala_standee", 1.0) or 1.0)}
    nome = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "", registro["nome"]).strip() or "Token"
    caminho = os.path.join(pasta_tokens(), f"{nome} [{ident}].json")
    for velho in os.listdir(pasta_tokens()):   # renomeou: tira o arquivo antigo do mesmo id
        if velho.endswith(f"[{ident}].json") and os.path.join(pasta_tokens(), velho) != caminho:
            os.remove(os.path.join(pasta_tokens(), velho))
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(registro, f, ensure_ascii=False)
    return ident


def listar() -> list[dict]:
    saida = []
    for a in os.listdir(pasta_tokens()):
        if not a.lower().endswith(".json"):
            continue
        try:
            with open(os.path.join(pasta_tokens(), a), encoding="utf-8") as f:
                d = json.load(f)
            d["imagem"], d["retrato"] = _bytes(d.get("imagem")), _bytes(d.get("retrato"))
            d["_arquivo"] = os.path.join(pasta_tokens(), a)
            saida.append(d)
        except (OSError, ValueError):
            continue
    return sorted(saida, key=lambda d: d.get("nome", "").casefold())


def apagar(ident: str):
    for a in os.listdir(pasta_tokens()):
        if a.endswith(f"[{ident}].json"):
            os.remove(os.path.join(pasta_tokens(), a))


def como_token(d: dict):
    """Os dados salvos com 'cara' de token (o DialogoToken edita a partir disso)."""
    return SimpleNamespace(nome=d.get("nome", ""), tipo=d.get("tipo", "criatura"), cor=d.get("cor", "#6e2a2f"),
                           tamanho=int(d.get("tamanho", 1)), dono=d.get("dono", ""), imagem=d.get("imagem"),
                           retrato=d.get("retrato"), pv=int(d.get("pv") or 0), desl=float(d.get("desl") or 0),
                           estilo=d.get("estilo", "ficha"), sem_borda=bool(d.get("sem_borda", False)),
                           escala_standee=float(d.get("escala_standee", 1.0) or 1.0))


def icone(d: dict, lado=64) -> QIcon:
    pm = QPixmap(lado, lado)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    caminho = QPainterPath()
    caminho.addEllipse(2, 2, lado - 4, lado - 4)
    p.setClipPath(caminho)
    img = QPixmap()
    if d.get("imagem") and img.loadFromData(d["imagem"]):
        img = img.scaled(lado, lado, Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                         Qt.TransformationMode.SmoothTransformation)
        p.drawPixmap((lado - img.width()) // 2, (lado - img.height()) // 2, img)
    else:
        p.fillPath(caminho, QColor(d.get("cor", "#6e2a2f")))
        p.setPen(QColor(245, 235, 215))
        f = p.font()
        f.setPixelSize(lado // 2)
        f.setBold(True)
        p.setFont(f)
        p.drawText(pm.rect(), Qt.AlignmentFlag.AlignCenter, (d.get("nome", "?").strip()[:1] or "?").upper())
    p.end()
    return QIcon(pm)


class AbaTokens(QWidget):
    """A aba 🧙 Tokens da Biblioteca (só o mestre)."""
    colocar = pyqtSignal(dict)   # o mestre quer esse token na mesa
    novo = pyqtSignal()          # abrir o "Novo token"

    def __init__(self, parent=None):
        super().__init__(parent)
        dica = QLabel("Seus tokens prontos. Monte uma vez (nome, imagem, PV…), salve, e coloque na mesa "
                      "quantas vezes quiser. Duplo clique = colocar na mesa.")
        dica.setWordWrap(True)
        dica.setObjectName("dica")
        self.filtro = QLineEdit()
        self.filtro.setPlaceholderText("Procurar token…")
        self.filtro.setClearButtonEnabled(True)
        self.filtro.textChanged.connect(self.recarregar)
        self.lista = QListWidget()
        self.lista.setViewMode(QListWidget.ViewMode.IconMode)
        self.lista.setIconSize(QSize(64, 64))
        self.lista.setGridSize(QSize(104, 100))
        self.lista.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.lista.setMovement(QListWidget.Movement.Static)
        self.lista.setWordWrap(True)
        self.lista.itemDoubleClicked.connect(lambda _it: self._colocar())
        botoes = QHBoxLayout()
        for texto, f, prim in (("＋ Novo token…", self.novo.emit, True), ("⬤ Colocar na mesa", self._colocar, True),
                               ("✏ Editar", self._editar, False), ("🗑 Apagar", self._apagar, False)):
            b = QPushButton(texto)
            if prim:
                b.setObjectName("primario")
            b.clicked.connect(f)
            botoes.addWidget(b)
        botoes.addStretch()
        lay = QVBoxLayout(self)
        lay.addWidget(dica)
        lay.addWidget(self.filtro)
        lay.addWidget(self.lista, 1)
        lay.addLayout(botoes)
        self.recarregar()
        from .acabamento import iconizar
        iconizar(self)

    def recarregar(self, *_):
        termo = self.filtro.text().strip().casefold()
        self.lista.clear()
        for d in listar():
            if termo and termo not in d.get("nome", "").casefold():
                continue
            it = QListWidgetItem(icone(d), d.get("nome", "?"))
            it.setData(Qt.ItemDataRole.UserRole, d)
            extra = [f"PV {d['pv']}"] if d.get("pv") else []
            if d.get("desl"):
                extra.append(f"{d['desl']:g} m")
            it.setToolTip(d.get("nome", "") + (f"\n{' · '.join(extra)}" if extra else ""))
            self.lista.addItem(it)

    def _atual(self):
        it = self.lista.currentItem()
        return it.data(Qt.ItemDataRole.UserRole) if it else None

    def _colocar(self):
        d = self._atual()
        if d:
            self.colocar.emit(d)

    def _editar(self):
        d = self._atual()
        if not d:
            return
        from .dialogos import DialogoToken
        dlg = DialogoToken(self, token=como_token(d), da_biblioteca=True)
        if dlg.exec():
            salvar(dlg.dados(), d["id"])
            self.recarregar()
            if dlg.acao == "mesa":
                self.colocar.emit(dict(dlg.dados(), id=d["id"]))

    def _apagar(self):
        d = self._atual()
        if d and QMessageBox.question(self, "Apagar token", f"Apagar “{d.get('nome')}” da biblioteca?\n"
                                      "(Os que já estão na mesa continuam lá.)") == QMessageBox.StandardButton.Yes:
            apagar(d["id"])
            self.recarregar()
