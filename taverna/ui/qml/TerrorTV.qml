// 📺 Terror, tela 1 (v0.55, referência do Manel): sala abandonada em 3D com uma TV velha enferrujada e o
// MENU DENTRO DA TELA. A tela é branca/cinza com chiado (não verde), pisca de vez em quando e às vezes mostra
// um ROSTO. Luminária que FALHA de vez em quando, caneca rachada, fotos velhas, chaves, lanterna APAGADA,
// pano com sangue. `tela` = o retângulo da tela no 2D (o Lancador põe o menu ali).
import QtQuick
import QtQuick3D
import QtQuick3D.Helpers
import QtQuick.Shapes

Item {
    id: raiz
    property int nivel: ponte.nivel
    readonly property bool anima: nivel >= 1
    function tex(n) { return ponte.textura(n) }

    // ---- onde a tela da TV caiu no 2D (pro menu ficar dentro dela)
    component Ferrugem: PrincipledMaterial {
        baseColorMap: Texture { source: raiz.tex("ferrugem") }
        metalness: 0.3
        roughness: 0.6
    }
    property rect tela: Qt.rect(0, 0, 0, 0)
    function medirTela() {
        var a = vista.mapFrom3DScene(Qt.vector3d(-260, 495, 205))
        var b = vista.mapFrom3DScene(Qt.vector3d(260, 65, 205))
        tela = Qt.rect(a.x, a.y, b.x - a.x, b.y - a.y)
    }
    onWidthChanged: Qt.callLater(medirTela)
    onHeightChanged: Qt.callLater(medirTela)
    Component.onCompleted: Qt.callLater(medirTela)

    // ---- luz da luminária (1 = acesa); de vez em quando falha
    property real luz: 1
    SequentialAnimation {
        id: falha
        NumberAnimation { target: raiz; property: "luz"; to: 0.05; duration: 40 }
        NumberAnimation { target: raiz; property: "luz"; to: 0.9; duration: 60 }
        PauseAnimation { duration: 90 }
        NumberAnimation { target: raiz; property: "luz"; to: 0.0; duration: 30 }
        PauseAnimation { duration: 220 }
        NumberAnimation { target: raiz; property: "luz"; to: 0.7; duration: 40 }
        NumberAnimation { target: raiz; property: "luz"; to: 0.1; duration: 50 }
        PauseAnimation { duration: 140 }
        NumberAnimation { target: raiz; property: "luz"; to: 1; duration: 80 }
    }
    Timer {
        running: raiz.anima; repeat: true
        interval: 4500
        onTriggered: { interval = 3500 + Math.random() * 8000; falha.start() }
    }

    // ---- a imagem da tela (vira textura do vidro da TV): chiado, piscadas, rosto
    property real brilhoTela: 1
    Item {
        id: conteudo
        width: 512; height: 400   // (fica atrás do 3D; o View3D cobre)
        Rectangle { anchors.fill: parent; color: "#101010" }
        Image {
            id: chiado
            property int v: 0
            x: -Math.random() * 256; y: -Math.random() * 256
            width: parent.width + 256; height: parent.height + 256
            source: "image://taverna/tv/chiado/" + v
            fillMode: Image.Tile
            opacity: 0.42
            smooth: false
        }
        Timer {
            running: raiz.anima; repeat: true; interval: 45
            onTriggered: {
                chiado.v = (chiado.v + 1) % 3
                chiado.x = -Math.random() * 256; chiado.y = -Math.random() * 256
            }
        }
        Shape {   // meio da tela mais apagado (degradê redondo): o menu fica legível
            anchors.fill: parent
            ShapePath {
                strokeWidth: -1
                fillGradient: RadialGradient {
                    centerX: 256; centerY: 200; centerRadius: 300; focalX: 256; focalY: 200
                    GradientStop { position: 0; color: Qt.rgba(0, 0, 0, 0.6) }
                    GradientStop { position: 0.6; color: Qt.rgba(0, 0, 0, 0.35) }
                    GradientStop { position: 1; color: Qt.rgba(0, 0, 0, 0) }
                }
                PathRectangle { x: 0; y: 0; width: 512; height: 400 }
            }
        }
        Rectangle {   // faixa rolando (sinal ruim)
            id: rolo
            width: parent.width; height: 60
            gradient: Gradient {
                GradientStop { position: 0; color: "transparent" }
                GradientStop { position: 0.5; color: Qt.rgba(1, 1, 1, 0.18) }
                GradientStop { position: 1; color: "transparent" }
            }
            NumberAnimation on y { from: -60; to: 400; duration: 3800; loops: Animation.Infinite; running: raiz.anima }
        }
        Image {   // o ROSTO
            id: rosto
            property int v: 0
            width: 230; height: 230
            source: "image://taverna/tv/rosto/" + v
            opacity: 0
            smooth: true
        }
        SequentialAnimation {
            id: aparece
            NumberAnimation { target: rosto; property: "opacity"; to: 0.75; duration: 70 }
            NumberAnimation { target: rosto; property: "opacity"; to: 0.15; duration: 60 }
            NumberAnimation { target: rosto; property: "opacity"; to: 0.85; duration: 50 }
            PauseAnimation { duration: 380 }
            NumberAnimation { target: rosto; property: "opacity"; to: 0.3; duration: 80 }
            PauseAnimation { duration: 120 }
            NumberAnimation { target: rosto; property: "opacity"; to: 0; duration: 260 }
        }
        Timer {
            running: raiz.anima; repeat: true; interval: 7000
            onTriggered: {
                interval = 6000 + Math.random() * 10000
                rosto.v = Math.floor(Math.random() * 3)
                var cantos = [[10, 10], [272, 10], [10, 160], [272, 160], [141, 70]]
                var c = cantos[Math.floor(Math.random() * cantos.length)]
                rosto.x = c[0]; rosto.y = c[1]
                rosto.scale = c[0] === 141 ? 1.4 : 0.9
                aparece.start()
                piscaTela.start()
            }
        }
        Rectangle {   // escurece/clareia a tela inteira (a TV "pisca")
            anchors.fill: parent
            color: raiz.brilhoTela > 1 ? "white" : "black"
            opacity: raiz.brilhoTela > 1 ? (raiz.brilhoTela - 1) * 0.5 : 1 - raiz.brilhoTela
        }
    }
    SequentialAnimation {
        id: piscaTela
        NumberAnimation { target: raiz; property: "brilhoTela"; to: 0.15; duration: 40 }
        NumberAnimation { target: raiz; property: "brilhoTela"; to: 1.6; duration: 50 }
        NumberAnimation { target: raiz; property: "brilhoTela"; to: 0.4; duration: 60 }
        NumberAnimation { target: raiz; property: "brilhoTela"; to: 1; duration: 90 }
    }
    Timer {
        running: raiz.anima; repeat: true; interval: 3000
        onTriggered: { interval = 2500 + Math.random() * 5000; piscaTela.start() }
    }

    View3D {
        id: vista
        anchors.fill: parent
        camera: camera
        environment: SceneEnvironment {
            backgroundMode: SceneEnvironment.Color
            clearColor: "#050806"
            antialiasingMode: SceneEnvironment.MSAA
            antialiasingQuality: raiz.nivel === 2 ? SceneEnvironment.VeryHigh : SceneEnvironment.High
            aoEnabled: raiz.nivel === 2
            aoStrength: 70
            aoDistance: 14
            aoSoftness: 40
            tonemapMode: SceneEnvironment.TonemapModeFilmic
        }

        PerspectiveCamera {
            id: camera
            position: Qt.vector3d(0, 380, 1150)
            eulerRotation.x: -8
            fieldOfView: 40
            clipNear: 20
            clipFar: 5000
        }

        // ------------------------------------------------------------ luzes
        DirectionalLight {   // resto de luz verde-fria (da janela, da noite)
            eulerRotation: Qt.vector3d(-30, -40, 0)
            color: "#6a9a7a"
            brightness: 0.35
        }
        SpotLight {   // a luminária (falha de vez em quando)
            position: Qt.vector3d(-470, 300, 300)
            eulerRotation: Qt.vector3d(-75, -20, 0)
            color: "#ffd890"
            brightness: 14 * raiz.luz
            coneAngle: 75
            innerConeAngle: 30
            quadraticFade: 0.15
            castsShadow: true
            shadowMapQuality: Light.ShadowMapQualityHigh
            shadowFactor: 70
            shadowFilter: 10
        }
        PointLight {   // a lâmpada acende a cúpula por dentro e o canto da mesa
            position: Qt.vector3d(-430, 250, 300)
            color: "#ffcf70"
            brightness: 12 * raiz.luz
            quadraticFade: 0.8
        }
        PointLight {   // o brilho da tela na sala (pisca junto com a TV)
            position: Qt.vector3d(-85, 280, 420)
            color: "#d8e4ff"
            brightness: 14 * Math.max(0.1, raiz.brilhoTela)
            quadraticFade: 0.25
        }

        // ------------------------------------------------------------ parede, janela, mesa
        Model {
            source: "#Rectangle"
            position: Qt.vector3d(0, 600, -320)
            scale: Qt.vector3d(40, 18, 1)
            materials: PrincipledMaterial {
                baseColorMap: Texture { source: raiz.tex("parede_verde"); scaleU: 3; scaleV: 1.4; tilingModeHorizontal: Texture.Repeat; tilingModeVertical: Texture.Repeat }
                roughness: 0.9
            }
        }
        Node {   // janela (em cima, à esquerda) com o vidro quebrado
            position: Qt.vector3d(-860, 820, -300)
            Model {
                source: "#Rectangle"
                scale: Qt.vector3d(3.2, 2.6, 1)
                materials: PrincipledMaterial { baseColor: "#000000"; emissiveMap: Texture { source: raiz.tex("janela_noite") }
                    emissiveFactor: Qt.vector3d(0.8, 0.8, 0.8) }
            }
            Repeater3D {
                model: [{x: 0, y: 130, sx: 3.5, sy: 0.18}, {x: 0, y: -130, sx: 3.5, sy: 0.18}, {x: -165, y: 0, sx: 0.18, sy: 2.8},
                        {x: 165, y: 0, sx: 0.18, sy: 2.8}, {x: 0, y: 0, sx: 0.1, sy: 2.6}, {x: 0, y: 0, sx: 3.2, sy: 0.1}]
                Model {
                    source: "#Cube"
                    position: Qt.vector3d(modelData.x, modelData.y, 8)
                    scale: Qt.vector3d(modelData.sx, modelData.sy, 0.16)
                    materials: PrincipledMaterial { baseColor: "#1e1a14"; roughness: 0.9 }
                }
            }
        }
        Model {   // tampo da mesa
            source: "#Cube"
            position: Qt.vector3d(0, -20, 160)
            scale: Qt.vector3d(30, 0.4, 9.6)
            materials: PrincipledMaterial {
                baseColorMap: Texture { source: raiz.tex("mesa_suja"); scaleU: 4; scaleV: 1.3; tilingModeHorizontal: Texture.Repeat; tilingModeVertical: Texture.Repeat }
                roughness: 0.85
            }
        }
        Model {   // frente da mesa, com a gaveta
            source: "#Cube"
            position: Qt.vector3d(0, -260, 630)
            scale: Qt.vector3d(30, 4.4, 0.2)
            materials: PrincipledMaterial { baseColorMap: Texture { source: raiz.tex("mesa_suja"); scaleU: 3; scaleV: 0.6 }
                roughness: 0.85 }
        }
        Model {
            source: "#Cube"
            position: Qt.vector3d(0, -150, 645)
            scale: Qt.vector3d(5, 1.6, 0.1)
            materials: PrincipledMaterial { baseColorMap: Texture { source: raiz.tex("mesa_suja") }
                roughness: 0.85 }
        }
        Model {   // puxador
            source: "#Cube"
            position: Qt.vector3d(0, -140, 660)
            scale: Qt.vector3d(1.2, 0.12, 0.2)
            materials: PrincipledMaterial { baseColorMap: Texture { source: raiz.tex("ferrugem") }
                metalness: 0.6; roughness: 0.6 }
        }

        // ------------------------------------------------------------ a TV
        Node {
            id: tv
            position.x: 85   // (a tela fica no meio da janela)
            Model {   // caixa (atrás da moldura)
                source: "#Cube"
                position: Qt.vector3d(0, 280, -40)
                scale: Qt.vector3d(7.6, 5, 4.2)
                materials: Ferrugem {}
            }
            Model { source: "#Cube"; position: Qt.vector3d(-362, 280, 207); scale: Qt.vector3d(0.36, 5, 0.36); materials: Ferrugem {} }
            Model { source: "#Cube"; position: Qt.vector3d(-85, 512, 207); scale: Qt.vector3d(5.2, 0.36, 0.36); materials: Ferrugem {} }
            Model { source: "#Cube"; position: Qt.vector3d(-85, 48, 207); scale: Qt.vector3d(5.2, 0.36, 0.36); materials: Ferrugem {} }
            Model { source: "#Cube"; position: Qt.vector3d(277, 280, 207); scale: Qt.vector3d(2.06, 5, 0.36); materials: Ferrugem {} }
            Repeater3D {   // borda escura de borracha em volta do vidro
                model: [{x: -340, y: 280, sx: 0.12, sy: 4.3}, {x: 170, y: 280, sx: 0.12, sy: 4.3},
                        {x: -85, y: 490, sx: 5.2, sy: 0.12}, {x: -85, y: 70, sx: 5.2, sy: 0.12}]
                Model {
                    source: "#Cube"
                    position: Qt.vector3d(modelData.x, modelData.y, 200)
                    scale: Qt.vector3d(modelData.sx, modelData.sy, 0.3)
                    materials: PrincipledMaterial { baseColor: "#121210"; roughness: 0.8 }
                }
            }
            Model {   // o VIDRO (estufado), com o chiado de textura e brilhando sozinho
                geometry: Malha { pedido: "tela|0.05" }
                position: Qt.vector3d(-85, 280, 190)
                scale: Qt.vector3d(520, 430, 400)
                materials: PrincipledMaterial {
                    baseColor: "#000000"
                    emissiveMap: Texture { sourceItem: conteudo }
                    emissiveFactor: Qt.vector3d(1.1, 1.1, 1.1)
                    roughness: 0.08
                    specularAmount: 0
                    clearcoatAmount: 0.35
                    clearcoatRoughnessAmount: 0.25
                    cullMode: Material.NoCulling
                }
            }
            // painel da direita: botões e grade
            Model {
                source: "#Cube"
                position: Qt.vector3d(277, 380, 226)
                scale: Qt.vector3d(1.7, 2.3, 0.04)
                materials: PrincipledMaterial { baseColor: "#2a2622"; roughness: 0.6; metalness: 0.4 }
            }
            Repeater3D {
                model: [440, 320]
                Node {
                    position: Qt.vector3d(277, modelData, 228)
                    eulerRotation.z: modelData * 0.7
                    Model {
                        geometry: Malha { pedido: "torno|0,0; 40,0; 42,10; 40,34; 33,40; 0,40|0|8|plano" }
                        eulerRotation.x: 90
                        materials: Ferrugem {}
                    }
                    Model {   // risquinho do botão
                        source: "#Cube"
                        position: Qt.vector3d(0, 14, 41)
                        scale: Qt.vector3d(0.06, 0.4, 0.04)
                        materials: PrincipledMaterial { baseColor: "#c8c0a8"; roughness: 0.5 }
                    }
                }
            }
            Model {   // fundo da grade
                source: "#Cube"
                position: Qt.vector3d(277, 160, 224)
                scale: Qt.vector3d(1.6, 1.9, 0.04)
                materials: PrincipledMaterial { baseColor: "#080806"; roughness: 0.9 }
            }
            Repeater3D {
                model: 9
                Model {
                    source: "#Cube"
                    position: Qt.vector3d(277, 80 + index * 20, 228)
                    scale: Qt.vector3d(1.56, 0.1, 0.06)
                    materials: Ferrugem {}
                }
            }
            Repeater3D {   // grade de ventilação em cima
                model: 12
                Model {
                    source: "#Cube"
                    position: Qt.vector3d(-160 + index * 29, 532, 40)
                    scale: Qt.vector3d(0.14, 0.04, 1.6)
                    materials: PrincipledMaterial { baseColor: "#0a0a08"; roughness: 0.9 }
                }
            }
            Repeater3D {   // pés
                model: [-300, 220]
                Model {
                    source: "#Cube"
                    position: Qt.vector3d(modelData, 15, 150)
                    scale: Qt.vector3d(0.9, 0.3, 0.6)
                    materials: PrincipledMaterial { baseColor: "#1a1814"; roughness: 0.8 }
                }
            }
            Model {   // fio rasgado saindo de trás
                geometry: Malha { pedido: "toro|160|7|0.35|12|5|plano" }
                position: Qt.vector3d(380, 300, -40)
                eulerRotation: Qt.vector3d(90, 0, 10)
                materials: PrincipledMaterial { baseColor: "#141210"; roughness: 0.7 }
            }
        }

        // ------------------------------------------------------------ esquerda: luminária, caneca, fotos
        Node {   // luminária articulada
            position: Qt.vector3d(-610, 0, 260)
            Model {
                geometry: Malha { pedido: "torno|0,0; 80,0; 82,10; 70,24; 26,30; 0,30|0|8|plano" }
                materials: Ferrugem {}
            }
            Node {
                position.y: 30
                eulerRotation.z: -12
                Model {
                    source: "#Cube"
                    position.y: 130
                    scale: Qt.vector3d(0.14, 2.6, 0.14)
                    materials: Ferrugem {}
                }
                Node {
                    position.y: 260
                    eulerRotation.z: -78
                    Model {   // articulação
                        source: "#Cylinder"
                        eulerRotation.x: 90
                        scale: Qt.vector3d(0.3, 0.3, 0.3)
                        materials: Ferrugem {}
                    }
                    Model {
                        source: "#Cube"
                        position.y: 90
                        scale: Qt.vector3d(0.12, 1.8, 0.12)
                        materials: Ferrugem {}
                    }
                    Node {
                        position.y: 180
                        eulerRotation.z: -95
                        Model {   // cúpula (aberta pra baixo/direita)
                            geometry: Malha { pedido: "torno|10,-10; 20,-10; 22,0; 64,80; 70,92|0|10|plano" }
                            materials: PrincipledMaterial {
                                baseColorMap: Texture { source: raiz.tex("ferrugem") }
                                metalness: 0.45; roughness: 0.65
                                emissiveFactor: Qt.vector3d(0.25 * raiz.luz, 0.18 * raiz.luz, 0.06 * raiz.luz)
                                cullMode: Material.NoCulling
                            }
                        }
                        Model {   // lâmpada
                            source: "#Sphere"
                            position.y: 76
                            scale: Qt.vector3d(0.5, 0.55, 0.5)
                            materials: PrincipledMaterial {
                                baseColor: "#fff2c0"
                                emissiveFactor: Qt.vector3d(3 * raiz.luz, 2.5 * raiz.luz, 1.3 * raiz.luz)
                            }
                        }
                    }
                }
            }
        }
        Node {   // caneca rachada
            position: Qt.vector3d(-420, 0, 250)
            eulerRotation.y: 120
            Model {
                geometry: Malha { pedido: "torno|0,0; 52,0; 55,4; 56,120; 54,124; 50,124; 49,10; 0,8|0|10|plano" }
                materials: PrincipledMaterial { baseColorMap: Texture { source: raiz.tex("ceramica") }
                    roughness: 0.45; cullMode: Material.NoCulling }
            }
            Model {
                geometry: Malha { pedido: "toro|28|8|0.55|7|5|plano" }
                position: Qt.vector3d(54, 62, 0)
                eulerRotation: Qt.vector3d(90, 0, -100)
                materials: PrincipledMaterial { baseColor: "#b8b09a"; roughness: 0.5 }
            }
        }
        Model {   // fotos velhas
            source: "#Rectangle"
            position: Qt.vector3d(-470, 1, 400)
            eulerRotation: Qt.vector3d(-90, 0, 14)
            scale: Qt.vector3d(2.2, 1.8, 1)
            materials: PrincipledMaterial { baseColorMap: Texture { source: raiz.tex("foto_casa") }
                roughness: 0.6 }
        }
        Model {
            source: "#Rectangle"
            position: Qt.vector3d(-300, 1.5, 450)
            eulerRotation: Qt.vector3d(-90, 0, -22)
            scale: Qt.vector3d(2, 1.65, 1)
            materials: PrincipledMaterial { baseColorMap: Texture { source: raiz.tex("foto_arvore") }
                roughness: 0.6 }
        }
        Repeater3D {   // papeizinhos
            model: [{x: -700, z: 380, r: 30}, {x: -290, z: 440, r: 70}, {x: -640, z: 560, r: -20}, {x: 600, z: 560, r: 45}, {x: 300, z: 480, r: 10}]
            Model {
                source: "#Rectangle"
                position: Qt.vector3d(modelData.x, 0.8, modelData.z)
                eulerRotation: Qt.vector3d(-90, 0, modelData.r)
                scale: Qt.vector3d(0.45, 0.4, 1)
                materials: PrincipledMaterial { baseColorMap: Texture { source: raiz.tex("papel_velho") }
                    roughness: 0.9 }
            }
        }

        // ------------------------------------------------------------ direita: chaves, lanterna, pano
        Node {   // molho de chaves
            position: Qt.vector3d(300, 0, 340)
            eulerRotation.y: 20
            Model {
                geometry: Malha { pedido: "toro|24|3.5|1|12|5|plano" }
                position.y: 3.5
                materials: PrincipledMaterial { baseColorMap: Texture { source: raiz.tex("latao_velho") }
                    metalness: 0.8; roughness: 0.4 }
            }
            Repeater3D {
                model: [{a: -30, c: 110}, {a: 25, c: 95}]
                Node {
                    eulerRotation.y: modelData.a
                    Model {   // cabeça da chave
                        geometry: Malha { pedido: "toro|13|4|1|10|5|plano" }
                        position: Qt.vector3d(-38, 4, 0)
                        materials: PrincipledMaterial { baseColorMap: Texture { source: raiz.tex("latao_velho") }
                            metalness: 0.8; roughness: 0.4 }
                    }
                    Model {   // haste
                        source: "#Cube"
                        position: Qt.vector3d(-52 - modelData.c / 2, 4, 0)
                        scale: Qt.vector3d(modelData.c / 100, 0.06, 0.07)
                        materials: PrincipledMaterial { baseColorMap: Texture { source: raiz.tex("latao_velho") }
                            metalness: 0.8; roughness: 0.4 }
                    }
                    Repeater3D {   // dentes
                        model: 3
                        Model {
                            source: "#Cube"
                            position: Qt.vector3d(-52 - modelData.c + 6 + index * 11, 4, 9)
                            scale: Qt.vector3d(0.07, 0.06, 0.14 + (index % 2) * 0.06)
                            materials: PrincipledMaterial { baseColorMap: Texture { source: raiz.tex("latao_velho") }
                                metalness: 0.8; roughness: 0.4 }
                        }
                    }
                }
            }
        }
        Node {   // lanterna (APAGADA)
            position: Qt.vector3d(470, 34, 370)
            eulerRotation: Qt.vector3d(0, 25, 90)
            Model {
                geometry: Malha { pedido: "torno|0,0; 24,0; 26,10; 24,150; 30,166; 36,200; 36,214; 30,216; 0,216|0|10|plano" }
                materials: Ferrugem {}
            }
            Repeater3D {   // estrias da empunhadura
                model: 5
                Model {
                    geometry: Malha { pedido: "toro|25|2|1|10|4|plano" }
                    position.y: 30 + index * 24
                    materials: PrincipledMaterial { baseColor: "#1a1814"; roughness: 0.8 }
                }
            }
            Model {   // vidro da lente (apagado)
                source: "#Cylinder"
                position.y: 216
                scale: Qt.vector3d(0.6, 0.02, 0.6)
                materials: PrincipledMaterial { baseColor: "#2a2e28"; roughness: 0.05; metalness: 0.2 }
            }
        }
        Model {   // pano com sangue em cima da mesa
            geometry: Malha { pedido: "folha|1|1|0|0.06|9|plano" }
            position: Qt.vector3d(420, 1, 500)
            eulerRotation.y: -10
            scale: Qt.vector3d(300, 120, 200)
            materials: PrincipledMaterial { baseColorMap: Texture { source: raiz.tex("pano_sangue") }
                roughness: 0.95; cullMode: Material.NoCulling }
        }
        Model {   // e a ponta caindo pela frente da mesa
            geometry: Malha { pedido: "folha|1|1|0|0.08|5|plano" }
            position: Qt.vector3d(440, -100, 650)
            eulerRotation: Qt.vector3d(-88, -10, 0)
            scale: Qt.vector3d(260, 60, 200)
            materials: PrincipledMaterial { baseColorMap: Texture { source: raiz.tex("pano_sangue") }
                roughness: 0.95; cullMode: Material.NoCulling }
        }
    }

    // ---- teias nos cantos de cima e as folhas descascando (2D, por cima do 3D)
    Image {
        source: "image://taverna/tv/teia"
        width: Math.min(raiz.width, raiz.height) * 0.32; height: width
        opacity: 0.6
    }
    Image {
        source: "image://taverna/tv/teia"
        anchors.right: parent.right
        width: Math.min(raiz.width, raiz.height) * 0.3; height: width
        mirror: true
        opacity: 0.55
    }
    Image {
        source: "image://taverna/tv/hera"
        x: raiz.width * 0.86; y: raiz.height * 0.02
        width: raiz.width * 0.2; height: width
        opacity: 0.8
    }
}
