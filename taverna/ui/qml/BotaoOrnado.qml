// Botão de tela de título (v0.52, referência: menus de RPG): cápsula escura com borda de METAL de verdade
// (reflexo, pontas em losango, gemas), texto serifado e um brilho quente ao passar o mouse.
import QtQuick

Item {
    id: raiz
    property string texto: ""
    property string detalhe: ""
    property bool habilitado: true
    property var cores: ponte.cores
    property int nivel: ponte.nivel
    // (v0.56) Medieval: escrito A TINTA no papel (contrato / cartaz de missões); o mouse risca um círculo
    property bool tinta: false
    readonly property color corTinta: "#2e1806"
    signal clicado()
    signal entrou()      // (v0.58) o mouse entrou (a cena pode reagir: o celular vibra)
    onSobreChanged: if (sobre) entrou()
    implicitWidth: 300
    implicitHeight: detalhe ? 52 : 44
    opacity: habilitado ? 1.0 : 0.4

    readonly property bool sobre: area.containsMouse && habilitado
    readonly property bool apertado: area.pressed && habilitado
    readonly property string estado: apertado ? "apertado" : (sobre ? "sobre" : "normal")
    readonly property int margem: 10   // = MARGEM_BRILHO no Python
    readonly property real dpr: Screen.devicePixelRatio

    Image {
        visible: !raiz.tinta
        x: -raiz.margem; y: -raiz.margem
        width: raiz.width + 2 * raiz.margem; height: raiz.height + 2 * raiz.margem
        source: raiz.width > 0 && !raiz.tinta ? "image://taverna/ornado/" + ponte.tema + "/" + Math.round(raiz.width) + "/"
                                 + Math.round(raiz.height) + "/" + raiz.estado + "/" + nivel + "/" + raiz.dpr
                                 + (ponte.textoNaImagem ? "/" + encodeURIComponent(raiz.texto) : "") : ""
        smooth: true
    }
    CirculoTinta {
        visible: raiz.tinta
        ligado: raiz.tinta && raiz.sobre
        semente: raiz.texto.length
        anchors.centerIn: parent
        width: Math.min(raiz.width + 30, rot.width + 90); height: raiz.height + 14
    }
    Column {
        anchors.centerIn: parent
        anchors.verticalCenterOffset: raiz.apertado ? 1 : 0
        spacing: 0
        Item {
            opacity: ponte.textoNaImagem ? 0 : 1   // (o espaço continua, pra linha de baixo não subir)
            anchors.horizontalCenter: parent.horizontalCenter
            width: rot.width; height: ponte.textoNaImagem ? 22 : rot.height
            Text { visible: !ponte.neutro && !raiz.tinta; x: 1; y: 1.5; text: rot.text; font: rot.font; color: "#000000"; opacity: cores.claro ? 0.15 : 0.7 }
            Text {
                id: rot
                text: raiz.texto
                font.family: cores.fonte
                font.pixelSize: raiz.tinta ? 27 : 18
                font.letterSpacing: 1
                color: raiz.tinta ? (raiz.sobre ? "#5a1208" : raiz.corTinta)
                       : raiz.sobre ? (cores.claro ? cores.destaque : "#fff6e0") : cores.texto
                Behavior on color { ColorAnimation { duration: 120 } }
            }
        }
        Text {
            visible: raiz.detalhe !== ""
            anchors.horizontalCenter: parent.horizontalCenter
            text: raiz.detalhe
            font.pixelSize: raiz.tinta ? 14 : 11
            color: raiz.tinta ? "#5a3a1c" : cores.fraco
            elide: Text.ElideRight
            width: Math.min(implicitWidth, raiz.width - 50)
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
