// (v0.56, ideia do Manel) Círculo riscado À MÃO em volta de uma opção, se desenhando na hora — como quem
// marca no papel a missão que vai pegar / o que vai assinar. Torto de propósito e passa um pouco do começo.
import QtQuick

Canvas {
    id: c
    property bool ligado: false
    property real progresso: 0
    property color cor: "#8a1a10"
    property int semente: 1
    Behavior on progresso { NumberAnimation { duration: c.ligado ? 320 : 160; easing.type: Easing.OutQuad } }
    onLigadoChanged: progresso = ligado ? 1 : 0
    onProgressoChanged: requestPaint()
    opacity: ligado ? 1 : progresso

    onPaint: {
        var ctx = getContext("2d")
        ctx.reset()
        if (progresso <= 0.001) return
        var cx = width / 2, cy = height / 2
        var rx = width / 2 - 6, ry = height / 2 - 5
        var a0 = -2.4 + (semente % 5) * 0.15
        var total = Math.PI * 2.25 * progresso
        ctx.strokeStyle = cor
        ctx.lineCap = "round"
        ctx.lineJoin = "round"
        ctx.beginPath()
        var passos = Math.max(6, Math.floor(70 * progresso))
        for (var i = 0; i <= passos; i++) {
            var t = i / passos
            var a = a0 + total * t
            // raio que "treme" e vai crescendo (a segunda volta passa por fora)
            var tremor = 1 + 0.035 * Math.sin(a * 3 + semente) + 0.02 * Math.sin(a * 7 + semente * 2) + 0.06 * t
            var x = cx + Math.cos(a) * rx * tremor
            var y = cy + Math.sin(a) * ry * tremor + (t * 4 - 2)
            if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y)
        }
        ctx.lineWidth = 3.2
        ctx.stroke()
    }
}
