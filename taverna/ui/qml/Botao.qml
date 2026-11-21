// Botão do Taverna (v0.51). O detalhe segue o nível de Gráficos:
//   0 (Baixo)  = simples: cor lisa e borda
//   1 (Médio)  = peça esculpida com luz (bisel), material discreto
//   2 (Alto)   = peça esculpida no material do tema (couro, latão, metal, ônix…) com brilho especular,
//                afunda de verdade ao apertar, e um halo ao passar o mouse
import QtQuick

Item {
    id: raiz
    property string texto: ""
    property string detalhe: ""          // linha pequena embaixo (ex.: a última aventura)
    property bool principal: false       // botão de destaque (material "principal" do tema)
    property bool habilitado: true
    property var cores: ponte.cores
    property int nivel: ponte.nivel
    signal clicado()

    implicitWidth: 360
    implicitHeight: detalhe ? 66 : 54
    opacity: habilitado ? 1.0 : 0.45

    readonly property real raio: Math.max(3, cores.raio + 1)
    readonly property bool sobre: area.containsMouse && habilitado
    readonly property bool apertado: area.pressed && habilitado
    readonly property string estado: apertado ? "apertado" : (sobre ? "sobre" : "normal")
    readonly property real dpr: Screen.devicePixelRatio
    function peca(est) {
        return "image://taverna/peca/" + ponte.tema + "/" + (principal ? "principal" : "botao") + "/"
               + Math.round(width) + "/" + Math.round(height) + "/" + est + "/" + nivel + "/" + raio + "/" + dpr
    }

    // sombra no chão (o botão "flutua" um pouco; afundado, quase encosta)
    Rectangle {
        visible: nivel >= 1
        x: 2; y: apertado ? 2 : 5
        width: parent.width - 2; height: parent.height
        radius: raio + 2
        color: "#000000"
        opacity: apertado ? 0.25 : 0.45
    }
    // halo ao passar o mouse (alto)
    Rectangle {
        id: halo
        visible: nivel === 2 && raiz.sobre
        anchors.fill: parent
        anchors.margins: -4
        radius: raio + 4
        color: "transparent"
        border.width: 2
        border.color: cores.destaque
        SequentialAnimation on opacity {
            running: halo.visible
            loops: Animation.Infinite
            NumberAnimation { from: 0.2; to: 0.7; duration: 800; easing.type: Easing.InOutSine }
            NumberAnimation { from: 0.7; to: 0.2; duration: 800; easing.type: Easing.InOutSine }
        }
    }
    // baixo: retângulo liso
    Rectangle {
        visible: nivel === 0
        anchors.fill: parent
        radius: raio
        color: principal ? Qt.darker(cores.destaque, cores.claro ? 1.0 : 2.4) : cores.painel2
        border.color: raiz.sobre ? cores.destaque : cores.borda
    }
    // médio/alto: a peça esculpida (as 3 poses ficam prontas e só troca)
    Image {
        visible: nivel >= 1
        anchors.fill: parent
        source: nivel >= 1 && width > 0 ? raiz.peca(raiz.estado) : ""
        smooth: true
        cache: true
    }

    Column {
        anchors.centerIn: parent
        anchors.verticalCenterOffset: apertado && nivel >= 1 ? 2 : 0
        spacing: 2
        Item {
            anchors.horizontalCenter: parent.horizontalCenter
            width: rotulo.width; height: rotulo.height
            Text {   // sombra suave (no lugar do contorno chapado)
                visible: nivel >= 1
                x: 1; y: 2
                text: rotulo.text; font: rotulo.font
                color: "#000000"
                opacity: cores.claro && !principal ? 0.18 : 0.6
            }
            Text {
                id: rotulo
                text: raiz.texto.toUpperCase()
                font.family: cores.fonte
                font.pixelSize: nivel === 2 ? 20 : 18
                font.letterSpacing: 2.5
                color: principal ? (cores.claro ? "#fff8ec" : "#fffaf0")
                       : raiz.sobre ? (cores.claro ? cores.destaque : "#ffffff") : cores.texto
            }
        }
        Text {
            visible: raiz.detalhe !== ""
            anchors.horizontalCenter: parent.horizontalCenter
            text: raiz.detalhe
            font.pixelSize: 12
            color: principal ? "#fff4e0" : cores.fraco
            opacity: principal ? 0.85 : 1.0
            elide: Text.ElideRight
            width: Math.min(implicitWidth, raiz.width - 24)
            horizontalAlignment: Text.AlignHCenter
        }
    }

    MouseArea {
        id: area
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: raiz.habilitado ? Qt.PointingHandCursor : Qt.ArrowCursor
        onClicked: if (raiz.habilitado) raiz.clicado()
    }
}
