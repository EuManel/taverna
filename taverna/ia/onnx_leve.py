"""
🧠 Leitor de ONNX em Python puro (v0.47) — sem onnx/protobuf/onnxruntime.

O ONNX é um arquivo protobuf. Aqui só lemos o que precisamos: os nós do grafo (operação, entradas,
saídas, atributos) e os pesos (initializers) como arrays numpy. O motor que roda o grafo fica em
`motor.py`.
"""

import numpy as np

# TensorProto.DataType → numpy
_TIPOS = {1: np.float32, 2: np.uint8, 3: np.int8, 5: np.int16, 6: np.int32, 7: np.int64,
          9: np.bool_, 10: np.float16, 11: np.float64}


def _varint(b, i):
    r = s = 0
    while True:
        c = b[i]
        i += 1
        r |= (c & 0x7F) << s
        if c < 0x80:
            return r, i
        s += 7


def _campos(b, ini=0, fim=None):
    """Itera (número do campo, tipo de fio, valor). Valor: int (varint/fixo) ou memoryview (bytes)."""
    i, fim = ini, len(b) if fim is None else fim
    while i < fim:
        chave, i = _varint(b, i)
        campo, fio = chave >> 3, chave & 7
        if fio == 0:
            v, i = _varint(b, i)
        elif fio == 1:
            v = b[i:i + 8]
            i += 8
        elif fio == 2:
            n, i = _varint(b, i)
            v = b[i:i + n]
            i += n
        elif fio == 5:
            v = b[i:i + 4]
            i += 4
        else:
            raise ValueError(f"protobuf: tipo de fio {fio} não suportado")
        yield campo, fio, v


def _int64(v):
    return v - (1 << 64) if v >= 1 << 63 else v


def _ints_empacotados(v):
    b, i, out = bytes(v), 0, []
    while i < len(b):
        x, i = _varint(b, i)
        out.append(_int64(x))
    return out


def _tensor(b) -> tuple:
    dims, tipo, nome, cru = [], 1, "", None
    floats, int64s, int32s = [], [], []
    for campo, fio, v in _campos(b):
        if campo == 1:
            dims.extend(_ints_empacotados(v) if fio == 2 else [_int64(v)])
        elif campo == 2:
            tipo = v
        elif campo == 4:
            floats.extend(np.frombuffer(bytes(v), "<f4") if fio == 2 else [np.frombuffer(bytes(v), "<f4")[0]])
        elif campo == 5:
            int32s.extend(_ints_empacotados(v) if fio == 2 else [_int64(v)])
        elif campo == 7:
            int64s.extend(_ints_empacotados(v) if fio == 2 else [_int64(v)])
        elif campo == 8:
            nome = bytes(v).decode()
        elif campo == 9:
            cru = bytes(v)
        elif campo == 13 or campo == 14:
            if campo == 14 and v == 1:
                raise ValueError("modelo com pesos em arquivo externo (não suportado)")
    dt = _TIPOS.get(tipo, np.float32)
    if cru is not None:
        arr = np.frombuffer(cru, dtype=np.dtype(dt).newbyteorder("<")).astype(dt)
    elif floats:
        arr = np.asarray(floats, np.float32)
    elif int64s:
        arr = np.asarray(int64s, np.int64)
    elif int32s:
        arr = np.asarray(int32s, dt)
    else:
        arr = np.zeros(0, dt)
    return nome, arr.reshape(dims) if dims else (arr.reshape(()) if arr.size == 1 else arr)


def _atributo(b):
    nome, valor = "", None
    floats, ints, strs = [], [], []
    for campo, fio, v in _campos(b):
        if campo == 1:
            nome = bytes(v).decode()
        elif campo == 2:
            valor = float(np.frombuffer(bytes(v), "<f4")[0])
        elif campo == 3:
            valor = _int64(v)
        elif campo == 4:
            valor = bytes(v).decode(errors="replace")
        elif campo == 5:
            valor = _tensor(v)[1]
        elif campo == 7:
            floats.extend(np.frombuffer(bytes(v), "<f4").tolist() if fio == 2 else
                          [float(np.frombuffer(bytes(v), "<f4")[0])])
        elif campo == 8:
            ints.extend(_ints_empacotados(v) if fio == 2 else [_int64(v)])
        elif campo == 9:
            strs.append(bytes(v).decode(errors="replace"))
    if valor is None:
        valor = floats or ints or strs or None
    return nome, valor


class No:
    __slots__ = ("op", "entradas", "saidas", "attr", "nome")

    def __init__(self):
        self.op, self.entradas, self.saidas, self.attr, self.nome = "", [], [], {}, ""


def _no(b) -> No:
    n = No()
    for campo, _fio, v in _campos(b):
        if campo == 1:
            n.entradas.append(bytes(v).decode())
        elif campo == 2:
            n.saidas.append(bytes(v).decode())
        elif campo == 3:
            n.nome = bytes(v).decode()
        elif campo == 4:
            n.op = bytes(v).decode()
        elif campo == 5:
            k, val = _atributo(v)
            n.attr[k] = val
    return n


def _nome_valueinfo(b) -> str:
    for campo, _fio, v in _campos(b):
        if campo == 1:
            return bytes(v).decode()
    return ""


class Modelo:
    """nos: lista de No (em ordem) · pesos: {nome: array} · entradas/saidas: nomes."""

    def __init__(self, caminho: str):
        with open(caminho, "rb") as f:
            dados = memoryview(f.read())
        grafo = next((v for c, _f, v in _campos(dados) if c == 7), None)
        if grafo is None:
            raise ValueError("arquivo sem grafo ONNX")
        self.nos, self.pesos, entradas, self.saidas = [], {}, [], []
        for campo, _fio, v in _campos(grafo):
            if campo == 1:
                self.nos.append(_no(v))
            elif campo == 5:
                k, arr = _tensor(v)
                self.pesos[k] = arr
            elif campo == 11:
                entradas.append(_nome_valueinfo(v))
            elif campo == 12:
                self.saidas.append(_nome_valueinfo(v))
        self.entradas = [e for e in entradas if e not in self.pesos]
