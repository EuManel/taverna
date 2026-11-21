// 🍺 Tela inicial do Taverna (v0.52): cada tema com a sua personalidade (botões, título, cenário), menu no
// MEIO. Medieval: muro de pedra 3D com tochas de fogo de verdade. Claro/Escuro: neutros, "de programa".
import QtQuick
import QtQuick.Effects
import Taverna 1.0

Item {
    id: raiz
    property var cores: ponte.cores
    property int nivel: ponte.nivel
    readonly property real dpr: Screen.devicePixelRatio

    // ---------------------------------------------------------------- cenário
    FundoTema {
        id: fundoCena
        anchors.fill: parent
        tema: ponte.tema
        coberto: mesa3d.active   // (a cena 3D cobre tudo: não pinta a mesa 2D à toa)
    }
    // Medieval (v0.56): sorteia a MESA DA TAVERNA (com o contrato) ou o QUADRO DE MISSÕES, os dois em 3D
    // (com placa de vídeo; sem ela, fica a imagem 2D da mesa)
    Loader {
        id: mesa3d
        anchors.fill: parent
        // (v0.57) o Mágico também: CÍRCULO MÁGICO ou TORRE DE MAGO
        // (v0.58) e o Moderno: CELULAR NA MESA ou TERRAÇO com o outdoor de LED
        // (v0.59) Steampunk (OFICINA / DIRIGÍVEL) e Pós-apocalíptico (CIDADE / ABRIGO)
        active: (ponte.tema === "medieval" || ponte.tema === "magico" || ponte.tema === "moderno" || ponte.tema === "futurista"
                 || ponte.tema === "steampunk" || ponte.tema === "posapoc")
                && nivel >= 1 && GraphicsInfo.api !== GraphicsInfo.Software
        source: ponte.tema === "steampunk" ? (ponte.cenaSteampunk === "dirigivel" ? "SteampunkDirigivel.qml" : "SteampunkOficina.qml")
                : ponte.tema === "posapoc" ? (ponte.cenaPosApocaliptico === "abrigo" ? "PosApocAbrigo.qml" : "PosApocCidade.qml")
                : ponte.tema === "futurista" ? (ponte.cenaFuturista === "nave" ? "FuturistaNave.qml" : "FuturistaBeco.qml")
                : ponte.tema === "moderno" ? (ponte.cenaModerno === "terraco" ? "ModernoTerraco.qml" : "ModernoCelular.qml")
                : ponte.tema === "magico" ? (ponte.cenaMagico === "torre" ? "MagicoTorre.qml" : "MagicoCirculo.qml")
                : (ponte.cenaMedieval === "quadro" ? "MedievalQuadro.qml" : "MesaTaverna3D.qml")
    }
    // Terror (v0.55): duas telas sorteadas toda vez que abre — a TV (3D, precisa da placa) ou o farol
    readonly property bool terrorTV: ponte.tema === "terror" && ponte.cenaTerror === "tv"
                                     && nivel >= 1 && GraphicsInfo.api !== GraphicsInfo.Software
    Loader {
        id: cenaTerror
        anchors.fill: parent
        active: ponte.tema === "terror"
        // (v0.56) com placa de vídeo, tudo em 3D; sem placa (ou no Baixo), o farol desenhado em 2D
        readonly property bool gpu: nivel >= 1 && GraphicsInfo.api !== GraphicsInfo.Software
        source: raiz.terrorTV ? "TerrorTV.qml" : (gpu ? "TerrorFarol3D.qml" : "TerrorFarol.qml")
    }
    // o menu entra DENTRO de algo da cena: a tela da TV, o contrato da mesa, o cartaz do quadro de missões
    readonly property var cenaComTela: mesa3d.status === Loader.Ready ? mesa3d.item
                                     : (terrorTV && cenaTerror.status === Loader.Ready ? cenaTerror.item : null)
    readonly property rect telaTV: cenaComTela && cenaComTela.tela ? cenaComTela.tela : Qt.rect(0, 0, 0, 0)
    readonly property bool dentroTV: telaTV.width > 10
    // Medieval com papel: o menu é escrito A TINTA (e o mouse risca um círculo)
    readonly property bool menuTinta: ponte.tema === "medieval" && dentroTV
    // (v0.58) o mouse entrou num botão: a cena pode reagir (o celular vibra)
    function botaoEntrou() {
        if (cenaComTela && typeof cenaComTela.vibrar === "function") cenaComTela.vibrar()
    }
    Repeater {   // a chama da vela da mesa 2D (quando não tem a mesa 3D)
        model: mesa3d.status === Loader.Ready ? [] : ponte.tochas
        Tocha {
            soChama: modelData.vela === true
            transformOrigin: Item.TopLeft
            scale: soChama ? 0.55 * raiz.height / 800 : 1
            x: modelData.x * raiz.width - fogoX * scale
            y: modelData.y * raiz.height - fogoY * scale
        }
    }
    Image {   // vinheta de cinema (bordas escuras) — os neutros não têm
        visible: !ponte.neutro
        anchors.fill: parent
        source: "image://taverna/vinheta/" + Math.round(raiz.width) + "/" + Math.round(raiz.height)
        smooth: true
        opacity: nivel === 0 ? 0.6 : 1.0
    }
    Rectangle {   // faixa mais escura no meio, atrás do menu, pra ler bem
        visible: !ponte.neutro && !raiz.dentroTV
        anchors.horizontalCenter: parent.horizontalCenter
        width: Math.min(parent.width, 760); height: parent.height
        gradient: Gradient {
            orientation: Gradient.Horizontal
            GradientStop { position: 0.0; color: "transparent" }
            GradientStop { position: 0.5; color: cores.claro ? Qt.rgba(1, 0.97, 0.9, 0.4) : Qt.rgba(0, 0, 0, 0.5) }
            GradientStop { position: 1.0; color: "transparent" }
        }
    }

    // Moderno: um painel de VIDRO FOSCO atrás do menu (desfoca a cidade de trás) — cara de app de hoje
    Item {
        id: vidro
        visible: ponte.tema === "moderno" && nivel >= 1 && !raiz.dentroTV && !mesa3d.active   // (só no cenário 2D)
        x: (raiz.width - width) / 2; y: coluna.y + logo.height + espaco.height - 34
        width: 420; height: menu.height + 68
        ShaderEffectSource {
            id: fonteVidro
            anchors.fill: parent
            sourceItem: fundoCena
            sourceRect: Qt.rect(vidro.x, vidro.y, vidro.width, vidro.height)
            visible: false
            live: true
        }
        MultiEffect {
            anchors.fill: parent
            source: fonteVidro
            blurEnabled: true
            blur: 1.0
            blurMax: 48
            brightness: -0.08
            maskEnabled: true
            maskSource: mascaraVidro
        }
        Rectangle {
            id: mascaraVidro
            anchors.fill: parent
            radius: 18
            visible: false
            layer.enabled: true
        }
        Rectangle {   // véu claro e borda fininha do vidro
            anchors.fill: parent
            radius: 18
            color: Qt.rgba(1, 1, 1, 0.06)
            border.color: Qt.rgba(1, 1, 1, 0.16)
        }
    }

    // ---------------------------------------------------------------- título + menu (no meio)
    Column {
        id: coluna
        // (v0.58) a cena pode escrever o título E o menu nela mesma (o círculo mágico): aí some tudo daqui
        visible: !(raiz.cenaComTela && raiz.cenaComTela.tituloProprio)
        // normal: no meio, em cima. Terror/TV: encolhido pra caber dentro da tela da TV
        readonly property real cabe: raiz.dentroTV ? Math.min(1, raiz.telaTV.height * 0.9 / Math.max(1, height),
                                                               raiz.telaTV.width * 0.9 / Math.max(1, width)) : 1
        scale: cabe
        transformOrigin: Item.Top
        x: raiz.dentroTV ? raiz.telaTV.x + raiz.telaTV.width / 2 - width / 2 : (raiz.width - width) / 2
        y: raiz.dentroTV ? raiz.telaTV.y + (raiz.telaTV.height - height * cabe) / 2 : Math.max(24, raiz.height * 0.06)
        spacing: 0

        Text {   // título escrito a tinta no papel
            visible: raiz.menuTinta
            anchors.horizontalCenter: parent.horizontalCenter
            text: "Taverna"
            font.family: cores.fonte
            font.pixelSize: 76
            color: "#2e1806"
        }
        Image {
            id: logo
            visible: !raiz.menuTinta
            anchors.horizontalCenter: parent.horizontalCenter
            source: "image://taverna/logo/" + ponte.tema + "/" + nivel + "/" + raiz.dpr
            // (dentro de um objeto da cena o título fica menor: sobra mais espaço pros botões)
            width: raiz.dentroTV ? 340 : Math.min(ponte.neutro ? 360 : 540, raiz.width * 0.42)
            height: width * (sourceSize.height / Math.max(1, sourceSize.width))
            smooth: true
            // Terror: a luz falha de vez em quando
            SequentialAnimation on opacity {
                running: ponte.tema === "terror" && nivel >= 1
                loops: Animation.Infinite
                PauseAnimation { duration: 2600 }
                NumberAnimation { to: 0.25; duration: 60 }
                NumberAnimation { to: 1.0; duration: 50 }
                PauseAnimation { duration: 120 }
                NumberAnimation { to: 0.5; duration: 40 }
                NumberAnimation { to: 1.0; duration: 80 }
                PauseAnimation { duration: 4200 }
            }
        }
        Item { id: espaco; width: 1; height: raiz.menuTinta ? 6 : Math.max(20, raiz.height * (ponte.neutro ? 0.05 : 0.06)) }

        Column {
            id: menu
            // (v0.57) a cena pode ter o menu DELA (os cristais da torre do Mágico)
            visible: !(raiz.cenaComTela && raiz.cenaComTela.menuProprio)
            anchors.horizontalCenter: parent.horizontalCenter
            spacing: ponte.neutro ? 8 : 12
            Rotulo { tinta: raiz.menuTinta; texto: "Mestre" }
            BotaoOrnado { tinta: raiz.menuTinta; width: 320; texto: "Nova sessão"; onEntrou: raiz.botaoEntrou(); onClicado: ponte.escolher("mestre_nova") }
            BotaoOrnado {
                tinta: raiz.menuTinta
                width: 320; texto: "Continuar sessão"
                detalhe: ponte.temUltima ? ponte.ultimaAventura : ""
                habilitado: ponte.temUltima
                onEntrou: raiz.botaoEntrou()
                onClicado: ponte.escolher("mestre_continuar")
            }
            BotaoOrnado { tinta: raiz.menuTinta; width: 320; texto: "Abrir sessão…"; onEntrou: raiz.botaoEntrou(); onClicado: ponte.escolher("mestre_abrir") }
            Item { width: 1; height: 8 }
            Rotulo { tinta: raiz.menuTinta; texto: "Jogador" }
            BotaoOrnado {
                tinta: raiz.menuTinta
                width: 320; texto: "Entrar na sessão"
                detalhe: ponte.servidor !== "" ? "da última vez: " + ponte.servidor : ""
                onEntrou: raiz.botaoEntrou()
                onClicado: ponte.escolher("jogador_entrar")
            }
            Item { width: 1; height: 8 }
            BotaoOrnado { tinta: raiz.menuTinta; width: 320; texto: "Sair"; onEntrou: raiz.botaoEntrou(); onClicado: ponte.escolher("sair") }
            Text {
                visible: ponte.info !== ""
                width: 320
                horizontalAlignment: Text.AlignHCenter
                wrapMode: Text.WordWrap
                text: ponte.info
                color: cores.sub
                font.pixelSize: 14
            }
        }
    }

    // Terror: granulado de filme mexendo por cima de tudo
    Image {
        id: grao
        visible: ponte.tema === "terror" && nivel >= 1
        x: -128; y: -128
        width: raiz.width + 256; height: raiz.height + 256
        source: visible ? "image://taverna/grao" : ""
        fillMode: Image.Tile
        opacity: 0.55
        Timer {
            running: grao.visible
            interval: 70; repeat: true
            onTriggered: { grao.x = -Math.random() * 128; grao.y = -Math.random() * 128 }
        }
    }
    // Terror: cara de CÂMERA filmando — linhas de varredura bem fracas + uma faixa de interferência passando
    Item {
        anchors.fill: parent
        visible: ponte.tema === "terror" && nivel >= 1
        Image {
            anchors.fill: parent
            source: parent.visible ? "image://taverna/varredura" : ""
            fillMode: Image.Tile
            opacity: 0.35
        }
        Rectangle {
            id: faixa
            width: parent.width; height: 26
            y: -40
            gradient: Gradient {
                GradientStop { position: 0; color: "transparent" }
                GradientStop { position: 0.5; color: Qt.rgba(1, 1, 1, 0.05) }
                GradientStop { position: 1; color: "transparent" }
            }
            SequentialAnimation on y {
                running: faixa.parent.visible; loops: Animation.Infinite
                PauseAnimation { duration: 3000 }
                NumberAnimation { from: -40; to: raiz.height + 40; duration: 2200 }
            }
        }
    }

    // (v0.58) outdoor de LED (Moderno): a grade de pixels POR CIMA do menu, só dentro da tela do outdoor
    Item {
        visible: raiz.dentroTV && raiz.cenaComTela && raiz.cenaComTela.gradeLed === true
        x: raiz.telaTV.x; y: raiz.telaTV.y; width: raiz.telaTV.width; height: raiz.telaTV.height
        clip: true
        Image {
            anchors.fill: parent
            source: parent.visible ? "image://taverna/led/grade" : ""
            fillMode: Image.Tile
            opacity: 0.32
        }
    }

    // ---------------------------------------------------------------- rodapé
    Row {
        anchors.left: parent.left; anchors.bottom: parent.bottom
        anchors.margins: 18
        spacing: 10
        Escolha {
            rotulo: "Tema"
            opcoes: ponte.temas
            atual: ponte.tema
            onEscolhido: (chave) => ponte.definirTema(chave)
        }
        Escolha {
            rotulo: "Gráficos"
            opcoes: ponte.niveis
            atual: ponte.nivelChave
            onEscolhido: (chave) => ponte.definirNivel(chave)
        }
        // (v1.0) idioma: as bandeirinhas (a escolhida acesa, a outra apagadinha)
        Row {
            anchors.verticalCenter: parent.verticalCenter
            spacing: 6
            Repeater {
                model: ponte.idiomas
                Item {
                    width: 30; height: 20
                    readonly property bool escolhida: modelData.chave === ponte.idioma
                    Rectangle {   // marquinha da escolhida
                        anchors.fill: parent; anchors.margins: -3
                        radius: 4
                        color: "transparent"
                        border.color: cores.destaque
                        border.width: 1.5
                        visible: parent.escolhida
                    }
                    Image {
                        anchors.fill: parent
                        source: "image://taverna/bandeira/" + modelData.chave + "/" + Screen.devicePixelRatio
                        smooth: true
                        opacity: parent.escolhida ? 1.0 : (mb.containsMouse ? 0.85 : 0.45)
                    }
                    MouseArea {
                        id: mb
                        anchors.fill: parent; anchors.margins: -4
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: ponte.definirIdioma(modelData.chave)
                    }
                }
            }
        }
    }
    Text {
        id: textoVersao
        anchors.right: parent.right; anchors.bottom: parent.bottom
        anchors.margins: 20
        text: "v" + ponte.versao
        color: cores.fraco
        font.pixelSize: 12
    }
    // (v1.0.1) versão nova no GitHub: aviso pequeno com link pro itch.io (nada é baixado sozinho)
    Rectangle {
        id: avisoVersao
        visible: ponte.avisoVersao !== ""
        anchors.right: parent.right; anchors.bottom: textoVersao.top
        anchors.rightMargin: 16; anchors.bottomMargin: 6
        width: rotuloAviso.implicitWidth + 22; height: rotuloAviso.implicitHeight + 10
        radius: 5
        color: Qt.rgba(0, 0, 0, maVersao.containsMouse ? 0.7 : 0.55)
        border.color: cores.destaque
        border.width: 1
        Text {
            id: rotuloAviso
            anchors.centerIn: parent
            text: "✨ " + ponte.avisoVersao
            color: maVersao.containsMouse ? "#ffffff" : cores.destaque
            font.pixelSize: 13
            font.underline: maVersao.containsMouse
        }
        MouseArea {
            id: maVersao
            anchors.fill: parent
            hoverEnabled: true
            cursorShape: Qt.PointingHandCursor
            onClicked: ponte.abrirNovaVersao()
        }
    }
}
