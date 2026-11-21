// Cenário do Terror (v0.52.1): céu frio, LUA bem trabalhada (crateras, fase, halo pulsando, nuvens passando
// na frente), árvores mortas BALANÇANDO no vento, NÉVOA em várias camadas (alturas e velocidades diferentes =
// sensação de volume) e os morros escuros na frente. Tudo animado pela placa de vídeo.
import QtQuick

Item {
    id: raiz
    property int nivel: ponte.nivel
    readonly property bool anima: nivel >= 1

    // a lua desta vez (sorteada quando o programa abre: lugar, fase, se é vermelha)
    readonly property var lua0: ponte.luaTerror
    Image {   // céu
        anchors.fill: parent
        source: "image://taverna/terror/ceu/" + Math.round(width) + "/" + Math.round(height) + "/"
                + raiz.lua0.x + "/" + raiz.lua0.y + "/" + (raiz.lua0.vermelha ? 1 : 0)
        smooth: true
    }
    // ---- lua
    Item {
        id: lua
        width: Math.min(raiz.width, raiz.height) * raiz.lua0.tamanho; height: width
        x: raiz.width * raiz.lua0.x - width / 2; y: raiz.height * raiz.lua0.y - height / 2
        Image {   // halo
            anchors.centerIn: parent
            width: parent.width * 2.6; height: width
            source: raiz.lua0.vermelha ? "image://taverna/sprite/brilho" : "image://taverna/sprite/fumaca"
            opacity: 0.85
            SequentialAnimation on opacity {
                running: raiz.anima; loops: Animation.Infinite
                NumberAnimation { to: 0.7; duration: 3200; easing.type: Easing.InOutSine }
                NumberAnimation { to: 0.9; duration: 3200; easing.type: Easing.InOutSine }
            }
        }
        Image {
            anchors.fill: parent
            source: "image://taverna/terror/lua/" + raiz.lua0.fase + "/" + (raiz.lua0.vermelha ? 1 : 0)
            smooth: true
        }
    }
    // nuvens finas passando na frente da lua
    Repeater {
        model: raiz.anima ? 2 : 0
        Image {
            source: "image://taverna/terror/nevoa/" + (5 + index)
            width: raiz.width * 0.9; height: raiz.height * 0.16
            y: raiz.height * (raiz.lua0.y - 0.07 + index * 0.06)
            opacity: 0.5
            NumberAnimation on x {
                from: raiz.width; to: -raiz.width * 0.9
                duration: 52000 + index * 17000; loops: Animation.Infinite
                running: raiz.anima
            }
        }
    }
    // ---- névoa do fundo (atrás das árvores)
    Repeater {
        model: [{y: 0.56, h: 0.22, v: 90000, o: 0.45, s: 1}, {y: 0.62, h: 0.2, v: 70000, o: 0.5, s: 2}]
        Item {
            width: raiz.width; height: raiz.height * modelData.h
            y: raiz.height * modelData.y
            clip: true
            Image {
                id: nv
                width: parent.width * 2; height: parent.height
                source: "image://taverna/terror/nevoa/" + modelData.s
                fillMode: Image.TileHorizontally
                opacity: modelData.o
                NumberAnimation on x {
                    from: 0; to: -nv.width / 2; duration: modelData.v; loops: Animation.Infinite
                    running: raiz.anima
                }
            }
        }
    }
    // ---- árvores mortas balançando (a base fica parada, a copa vai e volta)
    Repeater {
        model: [{x: 0.06, s: 1.15, v: 0, d: 3900}, {x: 0.2, s: 0.7, v: 1, d: 3100}, {x: 0.63, s: 0.55, v: 2, d: 3500},
                {x: 0.9, s: 1.25, v: 3, d: 4300}, {x: 0.76, s: 0.8, v: 4, d: 3300}]
        Image {
            source: "image://taverna/terror/arvore/" + modelData.v + "/" + modelData.s
            width: 360 * modelData.s; height: 420 * modelData.s
            x: raiz.width * modelData.x - width / 2
            y: raiz.height * 0.86 - height
            smooth: true
            transformOrigin: Item.Bottom
            SequentialAnimation on rotation {
                running: raiz.anima; loops: Animation.Infinite
                NumberAnimation { to: 1.6; duration: modelData.d; easing.type: Easing.InOutSine }
                NumberAnimation { to: -0.8; duration: modelData.d * 1.1; easing.type: Easing.InOutSine }
            }
        }
    }
    // ---- morros da frente
    Image {
        anchors.fill: parent
        source: "image://taverna/terror/morros/" + Math.round(width) + "/" + Math.round(height)
        smooth: true
    }
    // ---- névoa da frente (rasteira, mais rápida e mais densa)
    Repeater {
        model: [{y: 0.74, h: 0.26, v: 46000, o: 0.6, s: 3}, {y: 0.82, h: 0.22, v: 34000, o: 0.7, s: 4}]
        Item {
            width: raiz.width; height: raiz.height * modelData.h
            y: raiz.height * modelData.y
            clip: true
            Image {
                id: nf
                width: parent.width * 2; height: parent.height
                source: "image://taverna/terror/nevoa/" + modelData.s
                fillMode: Image.TileHorizontally
                opacity: modelData.o
                NumberAnimation on x {
                    from: -nf.width / 2; to: 0; duration: modelData.v; loops: Animation.Infinite
                    running: raiz.anima
                }
            }
        }
    }
}
