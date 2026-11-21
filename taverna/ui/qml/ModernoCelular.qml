// 📱 Moderno, tela 1 (v0.58, pacote do Manel): vista de cima de uma mesa à noite — chuva na janela do lado, café
// soltando fumaça, chaves, carteira, papéis. O MENU É A TELA DO CELULAR (como um app; `tela` = o pedaço da tela
// onde o Lancador põe os botões). A luz da tela ilumina a mesa. Mouse num botão = o celular vibra de leve
// (`vibrar()`, chamado pelo Lancador). Notificações inventadas descem de vez em quando.
import QtQuick
import QtQuick3D
import QtQuick3D.Particles3D
import QtQuick3D.Helpers

View3D {
    id: vista
    property int nivel: ponte.nivel
    readonly property bool anima: nivel >= 1
    function tex(n) { return ponte.textura(n) }
    camera: camera
    readonly property color destaque: ponte.cores.destaque

    // tamanho do celular (unidades da cena) e o pedaço da tela onde mora o menu
    readonly property real largCel: 300
    readonly property real altCel: 620
    property rect tela: Qt.rect(0, 0, 0, 0)
    function medirTela() {
        var w = largCel * 0.9 / 2, topo = -altCel * 0.94 / 2, z0 = topo + altCel * 0.94 * 0.17, z1 = topo + altCel * 0.94 * 0.93
        var a = mapFrom3DScene(Qt.vector3d(-w * 0.88, 18, z0))
        var b = mapFrom3DScene(Qt.vector3d(w * 0.88, 18, z1))
        tela = Qt.rect(a.x, a.y, b.x - a.x, b.y - a.y)
    }
    onWidthChanged: Qt.callLater(medirTela)
    onHeightChanged: Qt.callLater(medirTela)
    Component.onCompleted: Qt.callLater(medirTela)

    // ---- vibrar (o Lancador chama quando o mouse entra num botão)
    property real tremor: 0
    function vibrar() { if (vista.anima) { vibra.restart() } }
    SequentialAnimation {
        id: vibra
        NumberAnimation { target: vista; property: "tremor"; to: 1; duration: 25 }
        NumberAnimation { target: vista; property: "tremor"; to: -1; duration: 35 }
        NumberAnimation { target: vista; property: "tremor"; to: 0.8; duration: 35 }
        NumberAnimation { target: vista; property: "tremor"; to: -0.6; duration: 35 }
        NumberAnimation { target: vista; property: "tremor"; to: 0.3; duration: 35 }
        NumberAnimation { target: vista; property: "tremor"; to: 0; duration: 40 }
    }

    environment: SceneEnvironment {
        backgroundMode: SceneEnvironment.Color
        clearColor: "#06070a"
        antialiasingMode: SceneEnvironment.MSAA
        antialiasingQuality: vista.nivel === 2 ? SceneEnvironment.VeryHigh : SceneEnvironment.High
        aoEnabled: vista.nivel === 2
        aoStrength: 60
        aoDistance: 10
        tonemapMode: SceneEnvironment.TonemapModeFilmic
    }
    PerspectiveCamera {
        id: camera
        position: Qt.vector3d(0, 1060, 210)
        eulerRotation.x: -79
        fieldOfView: 36
        clipNear: 20
        clipFar: 5000
    }

    // ---------------------------------------------------------------- luzes
    DirectionalLight {   // abajur quente, de longe
        eulerRotation: Qt.vector3d(-60, 40, 0)
        color: "#ffc890"
        brightness: 0.5
        castsShadow: true
        shadowFactor: 45
        shadowMapQuality: Light.ShadowMapQualityHigh
    }
    PointLight {   // a luz da TELA do celular na mesa
        position: Qt.vector3d(0, 130, 0)
        color: "#a8c4ff"
        brightness: 3.2
        quadraticFade: 0.9
    }
    PointLight {   // a luz fria da janela (cidade + chuva)
        position: Qt.vector3d(-700, 260, 0)
        color: "#5a7ab8"
        brightness: 2.2
        quadraticFade: 0.4
    }

    // ---------------------------------------------------------------- mesa e janela com chuva
    Model {
        source: "#Rectangle"
        eulerRotation.x: -90
        scale: Qt.vector3d(24, 16, 1)
        materials: PrincipledMaterial {
            baseColorMap: Texture { source: vista.tex("mesa_moderna"); scaleU: 2; scaleV: 1.4; tilingModeHorizontal: Texture.Repeat; tilingModeVertical: Texture.Repeat }
            roughness: 0.5
            clearcoatAmount: 0.4
            clearcoatRoughnessAmount: 0.25
        }
    }
    Model {   // parapeito da janela
        source: "#Cube"
        position: Qt.vector3d(-560, 6, 0)
        scale: Qt.vector3d(0.3, 0.14, 16)
        materials: PrincipledMaterial { baseColor: "#1a1c22"; roughness: 0.6; metalness: 0.4 }
    }
    Model {   // o vidro, com a chuva escorrendo e a cidade borrada lá fora
        source: "#Rectangle"
        position: Qt.vector3d(-690, 2, 0)
        eulerRotation.x: -90
        scale: Qt.vector3d(2.4, 16, 1)
        materials: PrincipledMaterial {
            lighting: PrincipledMaterial.NoLighting
            baseColorMap: Texture {
                sourceItem: Item {
                    width: 240; height: 1600
                    Rectangle {
                        anchors.fill: parent
                        gradient: Gradient {
                            GradientStop { position: 0; color: "#1a2a44" }
                            GradientStop { position: 1; color: "#24304e" }
                        }
                    }
                    Repeater {   // luzes da cidade, borradas
                        model: 26
                        Rectangle {
                            readonly property real s: Math.sin(index * 12.9898) * 43758.5453
                            readonly property real r1: s - Math.floor(s)
                            readonly property real s2: Math.sin(index * 78.233) * 43758.5453
                            readonly property real r2: s2 - Math.floor(s2)
                            x: r1 * 220 - 30; y: r2 * 1600
                            width: 30 + r1 * 50; height: width; radius: width / 2
                            color: ["#ffb060", "#ffd890", "#80b0ff", "#ff7050"][index % 4]
                            opacity: 0.3 + r2 * 0.25
                        }
                    }
                    Repeater {   // gotas escorrendo
                        model: 34
                        Rectangle {
                            id: gota
                            readonly property real s: Math.sin(index * 3.7 + 1.3) * 43758.5453
                            readonly property real r: s - Math.floor(s)
                            x: r * 230
                            width: 3 + r * 4; height: width * 2.4; radius: width / 2
                            color: "#cfe0ff"
                            opacity: 0.45
                            NumberAnimation on y {
                                from: -40 - gota.r * 1600; to: 1640
                                duration: 3500 + gota.r * 7000
                                loops: Animation.Infinite
                                running: vista.anima
                            }
                        }
                    }
                }
            }
        }
    }

    // ---------------------------------------------------------------- o CELULAR
    Node {
        id: celular
        x: vista.tremor * 2.5
        eulerRotation.y: vista.tremor * 0.6
        Model {   // corpo
            source: "#Cube"
            position.y: 8
            scale: Qt.vector3d(vista.largCel / 100, 0.16, vista.altCel / 100)
            materials: PrincipledMaterial { baseColor: "#16181d"; metalness: 0.6; roughness: 0.35 }
        }
        Model {   // aro de metal
            source: "#Cube"
            position.y: 8
            scale: Qt.vector3d(vista.largCel / 100 + 0.06, 0.12, vista.altCel / 100 + 0.06)
            materials: PrincipledMaterial { baseColor: "#5a5e68"; metalness: 1; roughness: 0.25 }
        }
        Repeater3D {   // botões laterais
            model: [{z: -140, l: 70}, {z: -40, l: 50}]
            Model {
                source: "#Cube"
                position: Qt.vector3d(vista.largCel / 2 + 4, 8, modelData.z)
                scale: Qt.vector3d(0.06, 0.08, modelData.l / 100)
                materials: PrincipledMaterial { baseColor: "#4a4e58"; metalness: 1; roughness: 0.3 }
            }
        }
        Model {   // a TELA (o app do Taverna)
            source: "#Rectangle"
            position.y: 17
            eulerRotation.x: -90
            scale: Qt.vector3d(vista.largCel * 0.9 / 100, vista.altCel * 0.94 / 100, 1)
            materials: PrincipledMaterial {
                lighting: PrincipledMaterial.NoLighting
                baseColorMap: Texture {
                    sourceItem: Item {
                        id: app
                        width: 540; height: 1160
                        Rectangle {
                            anchors.fill: parent
                            radius: 40
                            gradient: Gradient {
                                GradientStop { position: 0; color: "#14182a" }
                                GradientStop { position: 0.5; color: "#1c1a36" }
                                GradientStop { position: 1; color: "#0e1424" }
                            }
                        }
                        Rectangle {   // brilho de fundo
                            x: -120; y: 300; width: 520; height: 520; radius: 260
                            color: vista.destaque
                            opacity: 0.12
                        }
                        Rectangle {
                            x: 260; y: 720; width: 420; height: 420; radius: 210
                            color: "#6a4aff"
                            opacity: 0.1
                        }
                        Text {   // barra de status
                            x: 40; y: 20
                            text: "21:47"
                            color: "white"
                            font.pixelSize: 30
                            font.bold: true
                        }
                        Row {
                            x: 400; y: 30
                            spacing: 8
                            Repeater {
                                model: 4
                                Rectangle { width: 7; height: 8 + index * 5; y: 20 - height; color: "white"; radius: 2 }
                            }
                            Rectangle { width: 46; height: 22; radius: 5; color: "transparent"; border.color: "white"; border.width: 2
                                Rectangle { x: 4; y: 4; width: 30; height: 14; radius: 2; color: "white" } }
                        }
                        Rectangle {   // a "ilha" da câmera
                            x: 200; y: 18; width: 140; height: 40; radius: 20; color: "black"
                        }
                        Rectangle {   // a barrinha de baixo
                            x: 190; y: 1130; width: 160; height: 8; radius: 4; color: "white"; opacity: 0.6
                        }
                        // notificação descendo de vez em quando (texto inventado)
                        Rectangle {
                            id: notif
                            property int qual: 0
                            x: 24; y: -160
                            width: 492; height: 120; radius: 28
                            color: Qt.rgba(0.16, 0.17, 0.24, 0.96)
                            border.color: Qt.rgba(1, 1, 1, 0.12)
                            Rectangle { x: 22; y: 30; width: 60; height: 60; radius: 16; color: vista.destaque
                                Text { anchors.centerIn: parent; text: "T"; color: "#10121a"; font.pixelSize: 36; font.bold: true } }
                            Text { x: 100; y: 24; text: ponte.notificacoes[notif.qual][0]; color: "white"; font.pixelSize: 26; font.bold: true }
                            Text { x: 100; y: 62; width: 370; elide: Text.ElideRight
                                text: ponte.notificacoes[notif.qual][1]; color: "#c8cce0"; font.pixelSize: 24 }
                            Text { x: 430; y: 26; text: "agora"; color: "#8a90a8"; font.pixelSize: 20 }
                        }
                        SequentialAnimation {
                            id: desce
                            NumberAnimation { target: notif; property: "y"; to: 70; duration: 380; easing.type: Easing.OutBack }
                            PauseAnimation { duration: 3200 }
                            NumberAnimation { target: notif; property: "y"; to: -160; duration: 300; easing.type: Easing.InQuad }
                        }
                        Timer {
                            running: vista.anima; repeat: true; interval: 6000
                            onTriggered: {
                                interval = 9000 + Math.random() * 9000
                                notif.qual = Math.floor(Math.random() * ponte.notificacoes.length)
                                desce.start()
                                vista.vibrar()
                            }
                        }
                    }
                }
            }
        }
    }

    // ---------------------------------------------------------------- café (soltando fumaça)
    Node {
        position: Qt.vector3d(330, 0, -190)
        Model {   // pires
            geometry: Malha { pedido: "torno|0,0; 100,0; 108,6; 104,10; 60,12; 0,10|0|24" }
            materials: PrincipledMaterial { baseColor: "#e8e6e2"; roughness: 0.25; clearcoatAmount: 0.6 }
        }
        Model {   // xícara
            geometry: Malha { pedido: "torno|0,10; 46,10; 60,30; 66,80; 68,88; 64,90; 60,86; 55,32; 0,28|0|28" }
            materials: PrincipledMaterial { baseColor: "#f2f0ec"; roughness: 0.2; clearcoatAmount: 0.7; cullMode: Material.NoCulling }
        }
        Model {   // café
            source: "#Cylinder"
            position.y: 76
            scale: Qt.vector3d(1.16, 0.01, 1.16)
            materials: PrincipledMaterial { baseColor: "#2a160c"; roughness: 0.1 }
        }
        Model {   // asa
            geometry: Malha { pedido: "toro|22|6|0.6|16|8" }
            position: Qt.vector3d(64, 55, 0)
            eulerRotation: Qt.vector3d(90, 0, -100)
            materials: PrincipledMaterial { baseColor: "#f2f0ec"; roughness: 0.2 }
        }
        ParticleSystem3D {
            running: vista.anima
            position.y: 90
            SpriteParticle3D {
                id: vapor
                sprite: Texture { source: vista.tex("sprite_fumaca") }
                maxAmount: 40
                color: Qt.rgba(1, 1, 1, 0.22)
                fadeInDuration: 500
                fadeOutDuration: 1400
                billboard: true
            }
            ParticleEmitter3D {
                particle: vapor
                emitRate: 6
                lifeSpan: 3200
                particleScale: 8
                particleEndScale: 22
                shape: ParticleShape3D { type: ParticleShape3D.Cylinder; extents: Qt.vector3d(30, 2, 30) }
                velocity: VectorDirection3D { direction: Qt.vector3d(10, 50, -10); directionVariation: Qt.vector3d(10, 10, 10) }
            }
            Wander3D { particles: [vapor]; globalAmount: Qt.vector3d(20, 4, 20); globalPace: Qt.vector3d(0.4, 0.2, 0.4) }
        }
    }

    // ---------------------------------------------------------------- carteira, chaves, papéis e caneta
    Model {
        source: "#Cube"
        position: Qt.vector3d(360, 9, 240)
        eulerRotation.y: 18
        scale: Qt.vector3d(2.2, 0.18, 1.6)
        materials: PrincipledMaterial { baseColorMap: Texture { source: vista.tex("couro_preto") }
            roughness: 0.7 }
    }
    Node {   // chaves
        position: Qt.vector3d(-300, 0, 250)
        eulerRotation.y: -30
        Model {
            geometry: Malha { pedido: "toro|20|3|1|16|6" }
            position.y: 3
            materials: PrincipledMaterial { baseColor: "#b8bcc4"; metalness: 1; roughness: 0.25 }
        }
        Repeater3D {
            model: [{a: -20, c: 85}, {a: 35, c: 70}]
            Node {
                eulerRotation.y: modelData.a
                Model {
                    geometry: Malha { pedido: "toro|11|4|1|14|6" }
                    position: Qt.vector3d(-32, 4, 0)
                    materials: PrincipledMaterial { baseColor: "#c8ccd4"; metalness: 1; roughness: 0.25 }
                }
                Model {
                    source: "#Cube"
                    position: Qt.vector3d(-44 - modelData.c / 2, 4, 0)
                    scale: Qt.vector3d(modelData.c / 100, 0.05, 0.12)
                    materials: PrincipledMaterial { baseColor: "#c8ccd4"; metalness: 1; roughness: 0.25 }
                }
            }
        }
    }
    Model {   // papéis
        source: "#Rectangle"
        position: Qt.vector3d(-320, 1, -170)
        eulerRotation: Qt.vector3d(-90, 0, 12)
        scale: Qt.vector3d(2.2, 2.9, 1)
        materials: PrincipledMaterial { baseColorMap: Texture { source: vista.tex("documento") }
            roughness: 0.8 }
    }
    Model {
        source: "#Rectangle"
        position: Qt.vector3d(-290, 1.5, -130)
        eulerRotation: Qt.vector3d(-90, 0, -6)
        scale: Qt.vector3d(2.2, 2.9, 1)
        materials: PrincipledMaterial { baseColorMap: Texture { source: vista.tex("documento") }
            roughness: 0.8 }
    }
    Model {   // caneta
        source: "#Cylinder"
        position: Qt.vector3d(-210, 6, -60)
        eulerRotation: Qt.vector3d(90, 0, 60)
        scale: Qt.vector3d(0.08, 1.5, 0.08)
        materials: PrincipledMaterial { baseColor: "#1a2a5a"; metalness: 0.5; roughness: 0.3 }
    }
}
