// Tocha de parede (v0.52): suporte de ferro com volume + FOGO de partículas desenhado pela placa de vídeo
// (chama em camadas, miolo amarelo, faíscas subindo e dançando, fumaça fininha) + a luz tremendo na parede.
// Baixo = chama parada · Médio = fogo e faíscas · Alto = tudo, mais denso, com fumaça.
import QtQuick
import QtQuick.Particles

Item {
    id: raiz
    property int nivel: ponte.nivel
    property bool soChama: false     // vela: só o fogo (o castiçal já está desenhado na mesa)
    width: 70; height: 170
    // o "ponto" da tocha (onde fica o fogo) é o topo do cabo
    readonly property real fogoX: width / 2
    readonly property real fogoY: 10

    // luz quente na parede, tremendo
    Image {
        id: brilho
        source: "image://taverna/sprite/brilho"
        width: 420; height: 380
        x: raiz.fogoX - width / 2; y: raiz.fogoY - height / 2 - 10
        opacity: 0.5
        smooth: true
        SequentialAnimation on opacity {
            running: nivel >= 1
            loops: Animation.Infinite
            NumberAnimation { to: 0.30; duration: 130; easing.type: Easing.InOutQuad }
            NumberAnimation { to: 0.48; duration: 90 }
            NumberAnimation { to: 0.36; duration: 160 }
            NumberAnimation { to: 0.50; duration: 110 }
        }
    }

    Image {   // o suporte de ferro e o cabo (iluminados pelo fogo) + a sombra que ele joga na parede
        visible: !raiz.soChama
        x: 0; y: 0
        width: parent.width; height: parent.height * 1.7
        source: "image://taverna/suporte/" + Screen.devicePixelRatio
        smooth: true
    }

    // chama parada (Baixo)
    Image {
        visible: nivel === 0
        source: "image://taverna/sprite/chama_parada"
        width: 34; height: 52
        x: raiz.fogoX - width / 2; y: raiz.fogoY - 44
    }

    ParticleSystem {
        id: sistema
        anchors.fill: parent
        running: nivel >= 1 && raiz.visible
    }
    // camadas da chama: fora laranja/vermelha, miolo amarelo-branco
    ImageParticle {
        system: sistema
        groups: ["chama"]
        source: "image://taverna/sprite/chama"
        color: "#ff6a18"
        colorVariation: 0.08
        alpha: 0.75
        entryEffect: ImageParticle.Scale
    }
    ImageParticle {
        system: sistema
        groups: ["miolo"]
        source: "image://taverna/sprite/chama"
        color: "#ffe08a"
        alpha: 0.9
        entryEffect: ImageParticle.Scale
    }
    ImageParticle {
        system: sistema
        groups: ["faisca"]
        source: "image://taverna/sprite/faisca"
        color: "#ffc860"
        colorVariation: 0.15
        alpha: 1.0
    }
    ImageParticle {
        system: sistema
        groups: ["fumaca"]
        source: "image://taverna/sprite/fumaca"
        color: "#9a948c"
        alpha: 0.35
    }
    Emitter {
        system: sistema
        group: "chama"
        x: raiz.fogoX - 9; y: raiz.fogoY - 2
        width: 18; height: 6
        emitRate: nivel === 2 ? 70 : 40
        lifeSpan: 620; lifeSpanVariation: 180
        size: 44; sizeVariation: 10; endSize: 8
        velocity: AngleDirection { angle: 270; angleVariation: 10; magnitude: 80; magnitudeVariation: 22 }
        acceleration: PointDirection { y: -30; xVariation: 12 }
    }
    Emitter {
        system: sistema
        group: "miolo"
        x: raiz.fogoX - 5; y: raiz.fogoY
        width: 10; height: 4
        emitRate: nivel === 2 ? 50 : 28
        lifeSpan: 380; lifeSpanVariation: 100
        size: 26; sizeVariation: 5; endSize: 4
        velocity: AngleDirection { angle: 270; angleVariation: 6; magnitude: 60; magnitudeVariation: 15 }
    }
    Emitter {
        system: sistema
        group: "faisca"
        x: raiz.fogoX - 6; y: raiz.fogoY - 10
        width: 12; height: 8
        emitRate: nivel === 2 ? 9 : 4
        lifeSpan: 1700; lifeSpanVariation: 600
        size: 4; sizeVariation: 2; endSize: 1
        velocity: AngleDirection { angle: 270; angleVariation: 30; magnitude: 85; magnitudeVariation: 40 }
        acceleration: PointDirection { y: 20; xVariation: 10 }
    }
    Emitter {
        system: sistema
        group: "fumaca"
        enabled: nivel === 2
        x: raiz.fogoX - 6; y: raiz.fogoY - 40
        width: 12; height: 6
        emitRate: 6
        lifeSpan: 2600; lifeSpanVariation: 600
        size: 22; sizeVariation: 6; endSize: 70
        velocity: AngleDirection { angle: 270; angleVariation: 12; magnitude: 30; magnitudeVariation: 10 }
    }
    Wander {   // as faíscas dançam no ar quente
        system: sistema
        groups: ["faisca"]
        xVariance: 60
        pace: 90
    }
    Wander {
        system: sistema
        groups: ["fumaca"]
        xVariance: 40
        pace: 20
    }
}
