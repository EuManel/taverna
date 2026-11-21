"""
Combate por turnos (vive no computador do mestre).

- participantes: tokens que estão no combate (pelo id).
- cada um tem iniciativa (None = ainda não rolou) e um modificador.
- ordem: da maior iniciativa pra menor (empate: maior modificador).
- vez: id do token que está jogando agora (None = rodada ainda não começou).
"""


class Combate:
    def __init__(self):
        self.ativo = False
        self.rodada = 0
        self.vez: str | None = None
        self.participantes: list[dict] = []   # {"id","nome","dono","tipo","ini","mod","extra"}
        self.limitar = True                   # limitar o movimento ao deslocamento de cada um

    # ------------------------------------------------------------ montar
    def iniciar(self, tokens):
        self.ativo = True
        self.rodada = 0
        self.vez = None
        self.participantes = []
        for t in tokens:
            self.adicionar(t)

    def adicionar(self, token):
        if any(p["id"] == token.uid for p in self.participantes):
            return
        self.participantes.append({"id": token.uid, "nome": token.nome, "dono": token.dono,
                                   "tipo": token.tipo, "ini": None, "mod": 0, "extra": 0.0})

    def remover(self, uid):
        if self.vez == uid:
            self.proximo()
            if self.vez == uid:
                self.vez = None
        self.participantes = [p for p in self.participantes if p["id"] != uid]

    def encerrar(self):
        limitar = self.limitar
        self.__init__()
        self.limitar = limitar

    def participante(self, uid) -> dict | None:
        return next((p for p in self.participantes if p["id"] == uid), None)

    def definir_iniciativa(self, uid, valor, mod=None):
        p = self.participante(uid)
        if p is not None:
            p["ini"] = None if valor is None else int(valor)
            if mod is not None:
                p["mod"] = int(mod)

    def atualizar_nomes(self, tokens_por_id):
        for p in self.participantes:
            t = tokens_por_id.get(p["id"])
            if t is not None:
                p["nome"], p["dono"], p["tipo"] = t.nome, t.dono, t.tipo

    # ------------------------------------------------------------ ordem e turnos
    def ordem(self) -> list[dict]:
        com = [p for p in self.participantes if p["ini"] is not None]
        sem = [p for p in self.participantes if p["ini"] is None]
        com.sort(key=lambda p: (p["ini"], p["mod"]), reverse=True)
        return com + sem

    def faltando(self) -> list[dict]:
        return [p for p in self.participantes if p["ini"] is None]

    def comecar(self):
        ordem = self.ordem()
        if not ordem:
            return
        self.rodada = 1
        self.vez = ordem[0]["id"]

    def proximo(self):
        ordem = self.ordem()
        if not ordem:
            self.vez = None
            return
        if self.vez is None:
            self.comecar()
            return
        ids = [p["id"] for p in ordem]
        k = ids.index(self.vez) if self.vez in ids else -1
        if k + 1 >= len(ids):
            self.rodada += 1
            self.vez = ids[0]
        else:
            self.vez = ids[k + 1]

    def anterior(self):
        ordem = self.ordem()
        if not ordem or self.vez is None:
            return
        ids = [p["id"] for p in ordem]
        k = ids.index(self.vez) if self.vez in ids else 0
        if k == 0:
            if self.rodada > 1:
                self.rodada -= 1
                self.vez = ids[-1]
        else:
            self.vez = ids[k - 1]

    # ------------------------------------------------------------ rede
    def para_dict(self) -> dict:
        return {"ativo": self.ativo, "rodada": self.rodada, "vez": self.vez,
                "limitar": self.limitar, "ordem": [dict(p) for p in self.ordem()]}
