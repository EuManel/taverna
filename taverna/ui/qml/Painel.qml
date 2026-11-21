// Painel com moldura do tema (v0.51): uma placa ESCULPIDA no material do tema (madeira com moldura
// entalhada, metal rebitado, ônix, papel…) com luz de verdade. Baixo = caixa lisa · Médio = placa com bisel
// · Alto = moldura entalhada dupla, material forte, cantoneiras e sombra funda.
import QtQuick

Item {
    id: raiz
    property string titulo: ""
    property bool aceso: false            // destaque (ex.: o papel usado da última vez)
    property var cores: ponte.cores
    property int nivel: ponte.nivel
    default property alias conteudo: miolo.data
    readonly property real raio: Math.max(4, cores.raio + 4)
    readonly property real dpr: Screen.devicePixelRatio

    // sombra funda
    Rectangle {
        visible: nivel >= 1
        x: nivel === 2 ? 10 : 5; y: nivel === 2 ? 14 : 7
        width: parent.width; height: parent.height
        radius: raio
        color: "#000000"
        opacity: nivel === 2 ? 0.55 : 0.4
    }
    // brilho de destaque em volta (o papel da última vez)
    Rectangle {
        visible: raiz.aceso && nivel >= 1
        anchors.fill: parent
        anchors.margins: -5
        radius: raio + 5
        color: "transparent"
        border.width: 3
        border.color: cores.destaque
        opacity: 0.5
        SequentialAnimation on opacity {
            running: raiz.aceso && nivel === 2
            loops: Animation.Infinite
            NumberAnimation { from: 0.25; to: 0.65; duration: 1400; easing.type: Easing.InOutSine }
            NumberAnimation { from: 0.65; to: 0.25; duration: 1400; easing.type: Easing.InOutSine }
        }
    }
    // baixo: caixa lisa
    Rectangle {
        visible: nivel === 0
        anchors.fill: parent
        radius: raio
        color: cores.painel
        opacity: 0.95
        border.color: raiz.aceso ? cores.destaque : cores.borda
    }
    // médio/alto: a placa esculpida
    Image {
        visible: nivel >= 1
        anchors.fill: parent
        source: nivel >= 1 && width > 0
                ? "image://taverna/peca/" + ponte.tema + "/placa/" + Math.round(width) + "/" + Math.round(height)
                  + "/normal/" + nivel + "/" + raio + "/" + dpr
                : ""
        smooth: true
    }
    // cantoneiras de metal (alto)
    Repeater {
        model: nivel === 2 ? 4 : 0
        Image {
            source: "image://taverna/canto/" + ponte.tema
            width: 54; height: 54
            smooth: true
            x: (index === 1 || index === 2) ? raiz.width - width + 3 : -3
            y: (index >= 2) ? raiz.height - height + 3 : -3
            rotation: [0, 90, 180, 270][index]
        }
    }
    // título (com sombra suave, como gravado na placa)
    Column {
        id: cabeca
        anchors.top: parent.top
        anchors.topMargin: nivel === 2 ? 34 : 22
        anchors.horizontalCenter: parent.horizontalCenter
        spacing: 8
        Item {
            anchors.horizontalCenter: parent.horizontalCenter
            width: tit.width; height: tit.height
            Text {
                visible: nivel >= 1
                x: 0; y: 2
                text: tit.text; font: tit.font
                color: cores.claro ? "#ffffff" : "#000000"
                opacity: cores.claro ? 0.6 : 0.75
            }
            Text {
                id: tit
                text: raiz.titulo
                font.family: cores.fonte
                font.pixelSize: nivel === 2 ? 34 : 28
                font.letterSpacing: 6
                color: raiz.aceso ? cores.titulo : cores.texto
            }
        }
        Rectangle {   // filete embaixo do título
            anchors.horizontalCenter: parent.horizontalCenter
            width: raiz.width * 0.5; height: 2
            gradient: Gradient {
                orientation: Gradient.Horizontal
                GradientStop { position: 0.0; color: "transparent" }
                GradientStop { position: 0.5; color: cores.destaque }
                GradientStop { position: 1.0; color: "transparent" }
            }
        }
    }
    Item {
        id: miolo
        anchors.top: cabeca.bottom
        anchors.topMargin: 20
        anchors.left: parent.left; anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.margins: nivel === 2 ? 36 : 24
    }
}
