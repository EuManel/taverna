// ☢ Pós-apocalíptico, tela 2 (v0.59, pedido do Manel): ABRIGO À NOITE. Cerca de arame, fogo dentro de um tambor,
// rádio velho chiando, latas, lanterna, mapa com marcações. CADA OPÇÃO É UMA PLACA DE MADEIRA PINTADA À MÃO
// pregada na cerca; no hover o facho da LANTERNA vai até a placa e ela balança. O rádio solta umas frases
// picotadas de vez em quando (legenda perto dele).
import QtQuick
import QtQuick3D
import QtQuick3D.Particles3D

View3D {
    id: vista
    property int nivel: ponte.nivel
    readonly property bool anima: nivel >= 1
    function tex(n) { return ponte.textura(n) }
    function acaso(i, k) { var s = Math.sin(i * 12.9898 + k * 78.233) * 43758.5453; return s - Math.floor(s) }
    camera: camera
    readonly property bool menuProprio: true
    readonly property bool tituloProprio: true
    property int sobre: -1

    property real tempo: 0
    NumberAnimation on tempo { from: 0; to: 1000; duration: 1000000; loops: Animation.Infinite; running: vista.anima }

    readonly property string pincel: "Black Ops One"
    readonly property real cercaZ: -120
    readonly property var opcoes: [
        {titulo: "TAVERNA", x: 0, y: 720, w: 620, h: 150, rot: -2, cor: "#e8e0d0", px: 110},
        {rotulo: "MESTRE", x: -360, y: 560, w: 260, h: 70, rot: 3, cor: "#e8c040", px: 40},
        {texto: "Nova sessão", acao: "mestre_nova", x: -360, y: 460, w: 400, h: 90, rot: -3, cor: "#f0ece0", px: 46},
        {texto: "Continuar", acao: "mestre_continuar", x: -380, y: 350, w: 360, h: 90, rot: 2, cor: "#f0ece0", px: 46, ok: ponte.temUltima},
        {texto: "Abrir sessão", acao: "mestre_abrir", x: -350, y: 240, w: 400, h: 90, rot: -1, cor: "#f0ece0", px: 46},
        {rotulo: "JOGADOR", x: 360, y: 560, w: 260, h: 70, rot: -2, cor: "#e8c040", px: 40},
        {texto: "Entrar na sessão", acao: "jogador_entrar", x: 360, y: 450, w: 460, h: 90, rot: 3, cor: "#f0ece0", px: 44},
        {texto: "SAIR", acao: "sair", x: 380, y: 320, w: 260, h: 90, rot: -4, cor: "#e84a3a", px: 56}
    ]

    environment: SceneEnvironment {
        backgroundMode: SceneEnvironment.Color
        clearColor: "#070910"
        antialiasingMode: SceneEnvironment.MSAA
        antialiasingQuality: vista.nivel === 2 ? SceneEnvironment.VeryHigh : SceneEnvironment.High
        tonemapMode: SceneEnvironment.TonemapModeNone
        fog: Fog { enabled: true; color: "#0a0c14"; depthEnabled: true; depthNear: 1800; depthFar: 6000 }
    }
    PerspectiveCamera {
        id: camera
        position: Qt.vector3d(0, 380, 1250)
        eulerRotation.x: -2
        fieldOfView: 50
        clipNear: 10
        clipFar: 20000
    }
    DirectionalLight { eulerRotation: Qt.vector3d(-35, 25, 0); color: "#6a7aa8"; brightness: 0.8 }   // a lua
    // o FOGO do tambor ilumina tudo de laranja (tremendo)
    readonly property real fogo: 1 + 0.18 * Math.sin(tempo * 11) + 0.1 * Math.sin(tempo * 23 + 2)
    PointLight { position: Qt.vector3d(-560, 260, 380); color: "#ff8a3a"; brightness: 10 * vista.fogo; quadraticFade: 0.3 }

    // ---------------------------------------------------------------- céu, lua, chão
    Model {
        source: "#Rectangle"; position: Qt.vector3d(900, 1600, -8000); scale: Qt.vector3d(14, 14, 1)
        materials: PrincipledMaterial { lighting: PrincipledMaterial.NoLighting; alphaMode: PrincipledMaterial.Blend
            blendMode: PrincipledMaterial.Screen; baseColor: "#c8d4ff"
            baseColorMap: Texture { source: vista.tex("sprite_brilho") } }
    }
    Repeater3D {   // estrelas
        model: 90
        Model {
            source: "#Sphere"
            position: Qt.vector3d((vista.acaso(index, 1) - 0.5) * 16000, 900 + vista.acaso(index, 2) * 4000, -9000)
            scale: Qt.vector3d(0.12, 0.12, 0.12)
            materials: PrincipledMaterial { lighting: PrincipledMaterial.NoLighting; baseColor: "#dfe6ff" }
        }
    }
    Model {
        source: "#Rectangle"; eulerRotation.x: -90; position: Qt.vector3d(0, 0, 0); scale: Qt.vector3d(80, 80, 1)
        materials: PrincipledMaterial {
            baseColorMap: Texture { source: vista.tex("terra_noite"); scaleU: 12; scaleV: 12; tilingModeHorizontal: Texture.Repeat; tilingModeVertical: Texture.Repeat }
            roughness: 0.95
        }
    }
    Repeater3D {   // silhuetas de ruínas lá longe
        model: 8
        Model {
            source: "#Cube"
            readonly property real alto: 600 + vista.acaso(index, 4) * 1600
            position: Qt.vector3d(-3500 + index * 1000, alto / 2, -4500 - vista.acaso(index, 5) * 1500)
            scale: Qt.vector3d(6 + vista.acaso(index, 6) * 6, alto / 100, 4)
            materials: PrincipledMaterial { baseColor: "#121420"; roughness: 1 }
        }
    }

    // ---------------------------------------------------------------- a CERCA de arame
    Model {   // a tela (alambrado)
        source: "#Rectangle"; position: Qt.vector3d(0, 420, vista.cercaZ); scale: Qt.vector3d(30, 8.4, 1)
        materials: PrincipledMaterial {
            alphaMode: PrincipledMaterial.Mask
            cullMode: Material.NoCulling
            baseColorMap: Texture { source: vista.tex("cerca_arame"); scaleU: 30; scaleV: 8.4; tilingModeHorizontal: Texture.Repeat; tilingModeVertical: Texture.Repeat }
            metalness: 0.5; roughness: 0.5
        }
    }
    Repeater3D {   // postes
        model: 9
        Model { source: "#Cylinder"; position: Qt.vector3d(-1500 + index * 375, 430, vista.cercaZ - 6); scale: Qt.vector3d(0.14, 8.6, 0.14)
            materials: PrincipledMaterial { baseColorMap: Texture { source: vista.tex("ferrugem") }
                roughness: 0.8 } }
    }
    Repeater3D {   // arame farpado em cima
        model: 3
        Model { source: "#Cylinder"; position: Qt.vector3d(0, 860 + index * 22, vista.cercaZ - 10); eulerRotation.z: 90
            scale: Qt.vector3d(0.02, 30, 0.02); materials: PrincipledMaterial { baseColor: "#5a5a54"; metalness: 0.6 } }
    }

    // ---------------------------------------------------------------- as PLACAS de madeira pintadas à mão
    component Placa: Node {
        id: pl
        property var d
        property int i: 0
        readonly property bool ehBotao: d.texto !== undefined
        readonly property bool habilitado: d.ok === undefined || d.ok
        readonly property bool acesa: vista.sobre === i && habilitado
        property real balanco: 0
        onAcesaChanged: if (acesa) chacoalha.restart()
        SequentialAnimation {   // a placa balança (presa por um prego só em cima)
            id: chacoalha
            NumberAnimation { target: pl; property: "balanco"; to: 7; duration: 140; easing.type: Easing.OutQuad }
            NumberAnimation { target: pl; property: "balanco"; to: -5; duration: 260; easing.type: Easing.InOutQuad }
            NumberAnimation { target: pl; property: "balanco"; to: 3; duration: 240; easing.type: Easing.InOutQuad }
            NumberAnimation { target: pl; property: "balanco"; to: -1.5; duration: 220 }
            NumberAnimation { target: pl; property: "balanco"; to: 0; duration: 200 }
        }
        position: Qt.vector3d(d.x, d.y + d.h / 2, vista.cercaZ + 12)   // o pivô é o prego de cima
        eulerRotation.z: d.rot + pl.balanco
        Model {   // a tábua
            property int opcao: pl.i
            pickable: pl.ehBotao
            source: "#Cube"
            position.y: -pl.d.h / 2
            scale: Qt.vector3d(pl.d.w / 100, pl.d.h / 100, 0.08)
            materials: PrincipledMaterial {
                baseColorMap: Texture { source: vista.tex("madeira_placa") }
                baseColor: pl.habilitado ? "#ffffff" : "#8a8a8a"
                roughness: 0.9
            }
        }
        Model {   // a tinta (pincel)
            source: "#Rectangle"
            position: Qt.vector3d(0, -pl.d.h / 2, 5)
            scale: Qt.vector3d(pl.d.w / 100, pl.d.h / 100, 1)
            materials: PrincipledMaterial {
                alphaMode: PrincipledMaterial.Blend
                roughness: 0.85
                baseColorMap: Texture {
                    sourceItem: Item {
                        width: pl.d.w * 2; height: pl.d.h * 2
                        Text {
                            anchors.centerIn: parent
                            anchors.verticalCenterOffset: pl.d.det ? -8 : 0
                            text: pl.d.titulo || pl.d.rotulo || pl.d.texto
                            font.family: vista.pincel; font.pixelSize: pl.d.px * 2
                            color: pl.habilitado ? pl.d.cor : "#8a8478"
                            opacity: 0.92
                        }
                    }
                }
            }
        }
        Repeater3D {   // pregos
            model: pl.d.titulo ? 4 : 2
            Model { source: "#Sphere"; position: Qt.vector3d((index % 2 ? 1 : -1) * (pl.d.w / 2 - 18), index < 2 ? -14 : -pl.d.h + 14, 7)
                scale: Qt.vector3d(0.07, 0.07, 0.05); materials: PrincipledMaterial { baseColor: "#5a5048"; metalness: 0.7 } }
        }
    }
    Repeater3D { model: vista.opcoes; Placa { d: modelData; i: index } }

    // ---------------------------------------------------------------- o acampamento: tambor com fogo, caixotes, rádio, latas, mapa, lanterna
    Node {   // TAMBOR com fogo
        position: Qt.vector3d(-560, 0, 380)
        Model { source: "#Cylinder"; position.y: 90; scale: Qt.vector3d(1.2, 1.8, 1.2)
            materials: PrincipledMaterial { baseColorMap: Texture { source: vista.tex("ferrugem") }
                roughness: 0.8 } }
        ParticleSystem3D {
            running: vista.anima
            position.y: 180
            SpriteParticle3D { id: chama; sprite: Texture { source: vista.tex("sprite_chama") }
                maxAmount: 140; color: "#ff9a40"
                blendMode: SpriteParticle3D.Screen; fadeInDuration: 60; fadeOutDuration: 300; billboard: true }
            ParticleEmitter3D { particle: chama; emitRate: 90; lifeSpan: 650; particleScale: 22; particleEndScale: 5; particleScaleVariation: 6
                shape: ParticleShape3D { type: ParticleShape3D.Sphere; extents: Qt.vector3d(40, 4, 40) }
                velocity: VectorDirection3D { direction: Qt.vector3d(0, 140, 0); directionVariation: Qt.vector3d(20, 40, 20) } }
            SpriteParticle3D { id: faisca; sprite: Texture { source: vista.tex("sprite_faisca") }
                maxAmount: 40; color: "#ffc070"
                blendMode: SpriteParticle3D.Screen; billboard: true; fadeOutDuration: 400 }
            ParticleEmitter3D { particle: faisca; emitRate: 8; lifeSpan: 1800; particleScale: 2
                velocity: VectorDirection3D { direction: Qt.vector3d(0, 220, 0); directionVariation: Qt.vector3d(60, 60, 60) } }
        }
    }
    Repeater3D {   // caixotes
        model: [{x: 520, z: 420, r: 10, s: 1.4}, {x: 640, z: 300, r: -20, s: 1.1}, {x: -300, z: 560, r: 30, s: 1.0}]
        Model { source: "#Cube"; position: Qt.vector3d(modelData.x, modelData.s * 50, modelData.z); eulerRotation.y: modelData.r
            scale: Qt.vector3d(modelData.s * 1.2, modelData.s, modelData.s); materials: PrincipledMaterial { baseColorMap: Texture { source: vista.tex("madeira_placa") }
                roughness: 0.9 } }
    }
    Node {   // o RÁDIO velho em cima do caixote (dial aceso, antena)
        position: Qt.vector3d(520, 140, 420)
        eulerRotation.y: -15
        Model { source: "#Cube"; position.y: 30; scale: Qt.vector3d(1.1, 0.6, 0.4); materials: PrincipledMaterial { baseColor: "#4a3a2a"; roughness: 0.6 } }
        Model { source: "#Cylinder"; eulerRotation.x: 90; position: Qt.vector3d(-24, 30, 21); scale: Qt.vector3d(0.38, 0.02, 0.38); materials: PrincipledMaterial { baseColor: "#1a1410" } }
        Model { source: "#Cube"; position: Qt.vector3d(30, 38, 21); scale: Qt.vector3d(0.3, 0.12, 0.01)
            materials: PrincipledMaterial { lighting: PrincipledMaterial.NoLighting; baseColor: radio.falando ? "#ffd070" : "#a07030" } }
        Model { source: "#Cylinder"; position: Qt.vector3d(40, 120, 0); eulerRotation.z: -20; scale: Qt.vector3d(0.02, 1.6, 0.02); materials: PrincipledMaterial { baseColor: "#8a8a84"; metalness: 0.8 } }
        PointLight { position: Qt.vector3d(30, 40, 60); color: "#ffb050"; brightness: radio.falando ? 2.5 : 0.8; quadraticFade: 1.5 }
    }
    Repeater3D {   // latas
        model: [{x: 470, z: 520}, {x: 560, z: 560}, {x: -420, z: 620}, {x: -200, z: 480}]
        Model { source: "#Cylinder"; position: Qt.vector3d(modelData.x, 20, modelData.z); scale: Qt.vector3d(0.22, 0.4, 0.22)
            materials: PrincipledMaterial { baseColor: index % 2 ? "#8a8a80" : "#a85a2a"; metalness: 0.7; roughness: 0.4 } }
    }
    Model {   // o MAPA com marcações em cima do caixote da esquerda
        source: "#Rectangle"; position: Qt.vector3d(-300, 101, 560); eulerRotation: Qt.vector3d(-90, 0, 25); scale: Qt.vector3d(1.1, 0.82, 1)
        materials: PrincipledMaterial { baseColorMap: Texture { source: vista.tex("mapa_marcado") }
                roughness: 0.9 }
    }

    // ---------------------------------------------------------------- a LANTERNA: o facho vai até a placa do mouse
    readonly property vector3d lanternaPos: Qt.vector3d(640, 130, 300)
    property vector3d alvo: Qt.vector3d(0, 0, vista.cercaZ - 600)          // apontada pro chão quando ninguém escolhe
    property vector3d mira: alvo
    Connections {   // a mão de quem segura: vai até o alvo aos poucos
        target: vista
        function onTempoChanged() {
            var a = vista.sobre >= 0 ? Qt.vector3d(vista.opcoes[vista.sobre].x, vista.opcoes[vista.sobre].y, vista.cercaZ)
                                     : Qt.vector3d(150, 40, vista.cercaZ + 200)
            vista.mira = vista.mira.plus(a.minus(vista.mira).times(0.12))
        }
    }
    readonly property vector3d dir: mira.minus(lanternaPos)
    readonly property real guinada: Math.atan2(-dir.x, -dir.z) * 180 / Math.PI
    readonly property real arfagem: Math.atan2(dir.y, Math.sqrt(dir.x * dir.x + dir.z * dir.z)) * 180 / Math.PI
    Node {
        position: vista.lanternaPos
        eulerRotation: Qt.vector3d(vista.arfagem, vista.guinada, 0)
        Model { source: "#Cylinder"; eulerRotation.x: 90; scale: Qt.vector3d(0.16, 0.5, 0.16); materials: PrincipledMaterial { baseColor: "#2a2a2c"; metalness: 0.6; roughness: 0.4 } }
        Model { source: "#Cylinder"; eulerRotation.x: 90; position.z: -28; scale: Qt.vector3d(0.2, 0.06, 0.2); materials: PrincipledMaterial { lighting: PrincipledMaterial.NoLighting; baseColor: "#fff8e0" } }
        SpotLight { position.z: -30; color: "#fff2d0"; brightness: vista.sobre >= 0 ? 9 : 4; coneAngle: 20; innerConeAngle: 9; quadraticFade: 0.05 }
        Model {   // o facho visível (poeira no ar)
            source: "#Cone"
            readonly property real comp: vista.dir.length()
            eulerRotation.x: 90   // (o #Cone nasce na base, com a ponta pra cima: base na placa, ponta na lanterna)
            position.z: -comp - 30
            scale: Qt.vector3d(comp * 0.0024, comp / 100, comp * 0.0024)
            opacity: vista.sobre >= 0 ? 0.08 : 0.035
            materials: PrincipledMaterial { lighting: PrincipledMaterial.NoLighting; baseColor: "#fff4d8"; alphaMode: PrincipledMaterial.Blend
                blendMode: PrincipledMaterial.Screen; depthDrawMode: Material.NeverDepthDraw; cullMode: Material.NoCulling }
        }
    }

    // ---------------------------------------------------------------- o RÁDIO falando (frases picotadas, legenda)
    Item {
        id: radio
        readonly property int ciclo: 14
        readonly property int volta: Math.floor(vista.tempo / ciclo)
        readonly property real fase: (vista.tempo % ciclo) / ciclo
        readonly property bool falando: vista.anima && fase < 0.42
        readonly property string frase: ponte.frasesRadio.length ? ponte.frasesRadio[volta % ponte.frasesRadio.length] : ""
        // vai aparecendo letra por letra, com falhas (chiado)
        readonly property int letras: Math.floor(Math.min(1, fase / 0.3) * frase.length)
        readonly property bool chiado: vista.acaso(Math.floor(vista.tempo * 6), 9) > 0.8
        visible: falando
        x: parent.width * 0.62; y: parent.height * 0.82
        width: parent.width * 0.34; height: 40
        Text {
            anchors.fill: parent
            wrapMode: Text.WordWrap
            text: "📻 " + (radio.chiado ? radio.frase.substring(0, radio.letras).replace(/[aeiou]/g, "·") : radio.frase.substring(0, radio.letras))
            font.family: "Courier New"; font.pixelSize: 15; font.italic: true
            color: "#e8c890"; style: Text.Outline; styleColor: "#000000"
        }
    }

    // ---------------------------------------------------------------- mouse
    MouseArea {
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: vista.sobre >= 0 ? Qt.PointingHandCursor : Qt.ArrowCursor
        function qual(x, y) {
            var r = vista.pick(x, y)
            var i = r.objectHit && r.objectHit.opcao !== undefined ? r.objectHit.opcao : -1
            if (i >= 0 && (!vista.opcoes[i].acao || (vista.opcoes[i].ok !== undefined && !vista.opcoes[i].ok))) return -1
            return i
        }
        onPositionChanged: (m) => vista.sobre = qual(m.x, m.y)
        onExited: vista.sobre = -1
        onClicked: (m) => {
            var i = qual(m.x, m.y)
            if (i >= 0) ponte.escolher(vista.opcoes[i].acao)
        }
    }
}
