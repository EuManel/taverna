// Caixinha de escolha (Tema, Gráficos) NO ESTILO do tema atual (v0.52.1): usa o mesmo desenho dos botões
// do tema (borda de ouro, cristal, tábua de relatório, vidro, liso…) e a lista abre no mesmo jeito.
import QtQuick

Item {
    id: raiz
    property string rotulo: ""
    property var opcoes: []             // [{chave, nome}]
    property string atual: ""
    property var cores: ponte.cores
    property int nivel: ponte.nivel
    signal escolhido(string chave)
    implicitWidth: 230
    implicitHeight: 38

    function nomeDe(chave) {
        for (var i = 0; i < opcoes.length; i++) if (opcoes[i].chave === chave) return opcoes[i].nome
        return chave
    }
    readonly property bool sobre: area.containsMouse || lista.visible
    readonly property string texto: raiz.rotulo + ": " + raiz.nomeDe(raiz.atual)

    Image {   // o desenho do botão do tema (mesmo dos botões do menu)
        x: -10; y: -10
        width: raiz.width + 20; height: raiz.height + 20
        source: "image://taverna/ornado/" + ponte.tema + "/" + Math.round(raiz.width) + "/" + Math.round(raiz.height)
                + "/" + (raiz.sobre ? "sobre" : "normal") + "/" + nivel + "/" + Screen.devicePixelRatio
                + (ponte.textoNaImagem ? "/" + encodeURIComponent(raiz.texto) : "")
        smooth: true
    }
    Text {
        visible: !ponte.textoNaImagem
        anchors.verticalCenter: parent.verticalCenter
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.horizontalCenterOffset: -6
        text: raiz.texto
        color: raiz.sobre ? (cores.claro ? cores.destaque : "#ffffff") : cores.texto
        font.family: ponte.neutro ? "Segoe UI" : cores.fonte
        font.pixelSize: 13
    }
    Item {   // setinha
        visible: !ponte.textoNaImagem
        width: 10; height: 10
        anchors.verticalCenter: parent.verticalCenter
        anchors.right: parent.right; anchors.rightMargin: ponte.tema === "medieval" || ponte.tema === "magico" ? 26 : 14
        rotation: lista.visible ? 180 : 0
        Rectangle { width: 7; height: 2; color: cores.fraco; rotation: 45; x: -1; y: 4 }
        Rectangle { width: 7; height: 2; color: cores.fraco; rotation: -45; x: 3.4; y: 4 }
    }
    MouseArea {
        id: area
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        onClicked: lista.visible = !lista.visible
    }
    // a lista abre pra cima, numa placa do tema
    Rectangle {
        id: lista
        visible: false
        z: 10
        width: parent.width
        height: col.height + 12
        y: -height - 8
        radius: ponte.neutro ? 6 : Math.max(2, cores.raio)
        color: ponte.tema === "moderno" ? Qt.rgba(0.08, 0.1, 0.12, 0.92) : cores.painel
        border.color: ponte.neutro ? cores.borda : cores.destaque
        border.width: ponte.neutro ? 1 : 1.5
        Column {
            id: col
            x: 6; y: 6
            width: parent.width - 12
            spacing: 2
            Repeater {
                model: raiz.opcoes
                Rectangle {
                    width: col.width; height: 30
                    radius: 4
                    color: m.containsMouse ? Qt.rgba(Qt.color(cores.destaque).r, Qt.color(cores.destaque).g,
                                                     Qt.color(cores.destaque).b, 0.22) : "transparent"
                    Text {
                        anchors.verticalCenter: parent.verticalCenter
                        x: 10
                        text: modelData.nome
                        color: modelData.chave === raiz.atual ? cores.destaque : cores.texto
                        font.family: ponte.neutro ? "Segoe UI" : cores.fonte
                        font.pixelSize: 13
                    }
                    MouseArea {
                        id: m
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: { lista.visible = false; raiz.escolhido(modelData.chave) }
                    }
                }
            }
        }
    }
}
