// Título pequeno de seção do menu ("MESTRE", "JOGADOR"): letras espaçadas entre dois filetes.
import QtQuick

Item {
    id: raiz
    property string texto: ""
    property var cores: ponte.cores
    property bool tinta: false
    readonly property color cor: tinta ? "#6a2a10" : cores.destaque
    width: 320; height: 24
    Rectangle {
        anchors.verticalCenter: parent.verticalCenter
        anchors.left: parent.left; anchors.right: nome.left; anchors.rightMargin: 12
        height: 1
        gradient: Gradient {
            orientation: Gradient.Horizontal
            GradientStop { position: 0; color: "transparent" }
            GradientStop { position: 1; color: raiz.cor }
        }
    }
    Text {
        id: nome
        anchors.centerIn: parent
        text: raiz.texto.toUpperCase()
        font.family: ponte.tema === "terror" ? "Courier New" : cores.fonte
        font.bold: ponte.tema === "terror"
        font.pixelSize: 13
        font.letterSpacing: 5
        color: raiz.cor
    }
    Rectangle {
        anchors.verticalCenter: parent.verticalCenter
        anchors.right: parent.right; anchors.left: nome.right; anchors.leftMargin: 12
        height: 1
        gradient: Gradient {
            orientation: Gradient.Horizontal
            GradientStop { position: 0; color: raiz.cor }
            GradientStop { position: 1; color: "transparent" }
        }
    }
}
