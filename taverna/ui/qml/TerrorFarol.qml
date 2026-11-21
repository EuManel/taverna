// 🌊 Terror, tela 2 (v0.55, referência do Manel): tempestade no mar. Penhasco com o FAROL GIRANDO, ondas
// batendo nas pedras, chuva, BARCO BALANÇANDO e RAIOS de vez em quando. Às vezes, junto com o raio (NUNCA sem
// raio), aparece a silhueta do CTHULHU lá no fundo.
import QtQuick
import QtQuick.Particles

Item {
    id: raiz
    property int nivel: ponte.nivel
    readonly property bool anima: nivel >= 1
    readonly property real hz: height * 0.5          // linha do horizonte
    clip: true

    // ---------------------------------------------------------------- céu, clarão, Cthulhu, nuvens
    Image {
        anchors.fill: parent
        source: "image://taverna/farol/ceu/" + Math.round(width) + "/" + Math.round(height)
        smooth: false
    }
    Image {   // o Cthulhu (só aparece no clarão)
        id: cthulhu
        source: "image://taverna/farol/cthulhu"
        width: raiz.width * 0.5; height: width * 640 / 900
        x: raiz.width * 0.42; y: raiz.hz - height * 0.86
        opacity: 0
    }
    Rectangle {   // o clarão do raio no céu
        id: clarao
        width: parent.width; height: raiz.hz + 40
        gradient: Gradient {
            GradientStop { position: 0; color: Qt.rgba(0.6, 1, 0.75, 0.55) }
            GradientStop { position: 1; color: Qt.rgba(0.3, 0.6, 0.4, 0.05) }
        }
        opacity: 0
    }
    Repeater {   // nuvens passando (na frente do Cthulhu)
        model: [{y: 0.0, h: 0.32, v: 80000, o: 0.9, s: 0}, {y: 0.2, h: 0.3, v: 60000, o: 0.75, s: 1}]
        Item {
            width: raiz.width; height: raiz.height * modelData.h
            y: raiz.height * modelData.y
            clip: true
            Image {
                id: nv
                width: parent.width * 2; height: parent.height
                source: "image://taverna/farol/nuvem/" + modelData.s
                fillMode: Image.TileHorizontally
                opacity: modelData.o
                NumberAnimation on x { from: 0; to: -nv.width / 2; duration: modelData.v; loops: Animation.Infinite; running: raiz.anima }
            }
        }
    }
    Image {   // o raio
        id: raio
        property int v: 0
        source: "image://taverna/farol/raio/" + v
        width: raiz.height * 0.3; height: width * 700 / 360
        y: -height * 0.1
        opacity: 0
    }
    Timer {   // de vez em quando cai um raio; às vezes (só junto com um raio) o Cthulhu aparece
        running: raiz.anima; repeat: true; interval: 5000
        onTriggered: {
            interval = 4000 + Math.random() * 9000
            raio.v = Math.floor(Math.random() * 3)
            raio.x = raiz.width * (0.35 + Math.random() * 0.45)
            var comCthulhu = Math.random() < 0.4
            cthulhuAnim.stop()
            if (comCthulhu) cthulhuAnim.start()
            raioAnim.start()
        }
    }
    SequentialAnimation {
        id: raioAnim
        ParallelAnimation {
            NumberAnimation { target: raio; property: "opacity"; to: 1; duration: 30 }
            NumberAnimation { target: clarao; property: "opacity"; to: 1; duration: 30 }
        }
        PauseAnimation { duration: 70 }
        ParallelAnimation {
            NumberAnimation { target: raio; property: "opacity"; to: 0.2; duration: 60 }
            NumberAnimation { target: clarao; property: "opacity"; to: 0.2; duration: 60 }
        }
        ParallelAnimation {
            NumberAnimation { target: raio; property: "opacity"; to: 1; duration: 40 }
            NumberAnimation { target: clarao; property: "opacity"; to: 0.9; duration: 40 }
        }
        PauseAnimation { duration: 120 }
        ParallelAnimation {
            NumberAnimation { target: raio; property: "opacity"; to: 0; duration: 380 }
            NumberAnimation { target: clarao; property: "opacity"; to: 0; duration: 700 }
        }
    }
    SequentialAnimation {
        id: cthulhuAnim
        NumberAnimation { target: cthulhu; property: "opacity"; to: 0.9; duration: 30 }
        PauseAnimation { duration: 90 }
        NumberAnimation { target: cthulhu; property: "opacity"; to: 0.3; duration: 60 }
        NumberAnimation { target: cthulhu; property: "opacity"; to: 0.85; duration: 40 }
        PauseAnimation { duration: 260 }
        NumberAnimation { target: cthulhu; property: "opacity"; to: 0; duration: 900; easing.type: Easing.InQuad }
    }

    // ---------------------------------------------------------------- mar
    Image {
        y: raiz.hz; width: parent.width; height: parent.height - raiz.hz
        source: "image://taverna/farol/horizonte/" + Math.round(width) + "/" + Math.round(height)
        smooth: false
    }
    Repeater {   // faixas de ondas: as de trás pequenas e lentas, as da frente grandes e rápidas
        model: [{y: 0.52, h: 0.07, v: 26000, s: 0, b: 3, d: 2400}, {y: 0.58, h: 0.1, v: 19000, s: 1, b: 6, d: 2100},
                {y: 0.66, h: 0.14, v: 14000, s: 2, b: 10, d: 1800}, {y: 0.76, h: 0.19, v: 10000, s: 3, b: 16, d: 1600},
                {y: 0.86, h: 0.24, v: 7500, s: 4, b: 22, d: 1400}]
        Item {
            width: raiz.width; height: raiz.height * modelData.h
            y: raiz.height * modelData.y
            Image {
                id: onda
                width: parent.width * 2; height: parent.height
                source: "image://taverna/farol/onda/" + modelData.s
                fillMode: Image.TileHorizontally
                smooth: false
                NumberAnimation on x { from: -onda.width / 2; to: 0; duration: modelData.v; loops: Animation.Infinite; running: raiz.anima }
                SequentialAnimation on y {
                    running: raiz.anima; loops: Animation.Infinite
                    NumberAnimation { to: -modelData.b; duration: modelData.d; easing.type: Easing.InOutSine }
                    NumberAnimation { to: modelData.b * 0.6; duration: modelData.d; easing.type: Easing.InOutSine }
                }
            }
        }
    }

    // ---------------------------------------------------------------- penhasco e farol
    Item {
        id: penhasco
        height: raiz.height * 1.0; width: height * 900 / 1100
        x: -width * 0.12; y: raiz.height - height
        Image { anchors.fill: parent; source: "image://taverna/farol/penhasco"; smooth: false }
        // o feixe GIRANDO: visto de lado, encolhe e estica (e some quando aponta pra trás)
        Item {
            id: lampada
            x: parent.width * ponte.farolLampada.x; y: parent.height * ponte.farolLampada.y
            property real angulo: 0
            NumberAnimation on angulo { from: 0; to: 360; duration: 7000; loops: Animation.Infinite; running: raiz.anima }
            readonly property real frente: Math.cos(angulo * Math.PI / 180)      // 1 = apontando pra direita
            readonly property real pracamera: Math.max(0, Math.sin(angulo * Math.PI / 180))
            Image {
                source: "image://taverna/farol/feixe"
                width: raiz.width * 0.75 * Math.abs(lampada.frente); height: raiz.height * 0.22
                x: lampada.frente >= 0 ? 0 : -width
                y: -height / 2
                mirror: lampada.frente < 0
                opacity: 0.25 + 0.75 * Math.abs(lampada.frente)
            }
            Image {   // brilho da lâmpada (fica forte quando o feixe vira pra gente)
                source: "image://taverna/sprite/brilho"
                width: raiz.height * (0.1 + 0.25 * lampada.pracamera); height: width
                x: -width / 2; y: -height / 2
                opacity: 0.6 + 0.4 * lampada.pracamera
            }
        }
        ParticleSystem {   // espuma estourando nas pedras
            anchors.fill: parent
            running: raiz.anima
            ImageParticle {
                source: "image://taverna/sprite/fumaca"
                color: "#d8f0e4"
                alpha: 0.7
                colorVariation: 0.05
            }
            Emitter {
                id: estouro
                x: penhasco.width * 0.45; y: penhasco.height * 0.82
                width: penhasco.width * 0.5; height: 30
                enabled: false
                lifeSpan: 1300; lifeSpanVariation: 300
                size: 34; sizeVariation: 18; endSize: 70
                velocity: AngleDirection { angle: 270; angleVariation: 35; magnitude: 260; magnitudeVariation: 100 }
                acceleration: PointDirection { y: 380 }
            }
        }
        Timer {
            running: raiz.anima; repeat: true; interval: 1800
            onTriggered: { interval = 1300 + Math.random() * 1600; estouro.burst(60) }
        }
    }

    // ---------------------------------------------------------------- barco (balança)
    Image {
        id: barco
        source: "image://taverna/farol/barco"
        height: raiz.height * 0.58; width: height * 760 / 820
        x: raiz.width - width * 0.92; y: raiz.height - height * 0.92
        smooth: false
        transformOrigin: Item.Bottom
        SequentialAnimation on rotation {
            running: raiz.anima; loops: Animation.Infinite
            NumberAnimation { to: 3.5; duration: 2600; easing.type: Easing.InOutSine }
            NumberAnimation { to: -2.5; duration: 2800; easing.type: Easing.InOutSine }
        }
        SequentialAnimation on y {
            running: raiz.anima; loops: Animation.Infinite
            NumberAnimation { to: raiz.height - barco.height * 0.92 - 16; duration: 1900; easing.type: Easing.InOutSine }
            NumberAnimation { to: raiz.height - barco.height * 0.92 + 10; duration: 2100; easing.type: Easing.InOutSine }
        }
    }
    Item {   // uma onda passando na frente do pé do barco
        width: raiz.width; height: raiz.height * 0.16
        y: raiz.height * 0.9
        Image {
            id: ondaFrente
            width: parent.width * 2; height: parent.height
            source: "image://taverna/farol/onda/5"
            fillMode: Image.TileHorizontally
            smooth: false
            NumberAnimation on x { from: -ondaFrente.width / 2; to: 0; duration: 6000; loops: Animation.Infinite; running: raiz.anima }
        }
    }

    // ---------------------------------------------------------------- chuva
    ParticleSystem {
        anchors.fill: parent
        running: raiz.anima
        ImageParticle {
            source: "image://taverna/farol/gota"
            alpha: 0.6
            alphaVariation: 0.3
        }
        Emitter {
            x: -raiz.width * 0.2; y: -60
            width: raiz.width * 1.3; height: 10
            emitRate: raiz.nivel === 2 ? 700 : 350
            lifeSpan: 1400
            size: 34; sizeVariation: 14
            velocity: PointDirection { x: 220; xVariation: 30; y: 1100; yVariation: 200 }
        }
    }
}
