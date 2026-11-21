// 🍺 A MESA DA TAVERNA em 3D (v0.54, referência que o Manel mandou): fundo do tema Medieval.
// Vista DE CIMA, objetos low-poly facetados nas bordas e o meio livre pro menu: pano e livro vermelho,
// vela no castiçal de latão (luz que tremula e faz sombra), MAPA DOBRADO PRESO NA MESA POR UMA ADAGA,
// moedas de ouro e cobre, saquinho de moedas, caneca de madeira com aros, rebites e espuma escorrendo
// (com bolhas), pão com farelos, dois d6, risco de faca e marca de caneca no tampo.
// Formas: ui/geometria3d.py (via Malha.qml). Texturas: arquivos, via ponte.textura().
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

    // (v0.56) onde o CONTRATO caiu no 2D: o menu é escrito nele (ver Lancador)
    property rect tela: Qt.rect(0, 0, 0, 0)
    function medirTela() {
        var a = mapFrom3DScene(Qt.vector3d(-235, 2, -330))
        var b = mapFrom3DScene(Qt.vector3d(235, 2, 330))
        tela = Qt.rect(a.x, a.y, b.x - a.x, b.y - a.y)
    }
    onWidthChanged: Qt.callLater(medirTela)
    onHeightChanged: Qt.callLater(medirTela)
    Component.onCompleted: Qt.callLater(medirTela)

    environment: SceneEnvironment {
        backgroundMode: SceneEnvironment.Color
        clearColor: "#0b0704"
        antialiasingMode: SceneEnvironment.MSAA
        antialiasingQuality: vista.nivel === 2 ? SceneEnvironment.VeryHigh : SceneEnvironment.High
        aoEnabled: vista.nivel === 2
        aoStrength: 60
        aoDistance: 12
        aoSoftness: 40
        tonemapMode: SceneEnvironment.TonemapModeFilmic
        lightProbe: Texture { source: vista.tex("ambiente"); mappingMode: Texture.LightProbe }
        probeExposure: 0.7
        probeHorizon: 0.4
    }

    PerspectiveCamera {
        id: camera
        position: Qt.vector3d(0, 1420, 300)
        eulerRotation.x: -78
        fieldOfView: 36
        clipNear: 50
        clipFar: 4000
    }

    // ---------------------------------------------------------------- luzes
    DirectionalLight {   // luz geral quente vinda de cima/esquerda: faz as sombras curtas dos objetos
        eulerRotation: Qt.vector3d(-62, -35, 0)
        color: "#ffd9a8"
        brightness: 0.75
        castsShadow: true
        shadowMapQuality: Light.ShadowMapQualityHigh
        shadowFactor: 55
        shadowFilter: 8
        shadowBias: 2
    }
    PointLight {   // a vela: tremula e esquenta o canto esquerdo
        position: Qt.vector3d(-560, 230, -20)
        color: "#ffa850"
        brightness: 9
        quadraticFade: 0.35
        castsShadow: vista.nivel === 2
        shadowFactor: 50
        SequentialAnimation on brightness {
            running: vista.anima
            loops: Animation.Infinite
            NumberAnimation { to: 7.5; duration: 110; easing.type: Easing.InOutQuad }
            NumberAnimation { to: 10; duration: 80 }
            NumberAnimation { to: 8.5; duration: 140 }
            NumberAnimation { to: 10.5; duration: 95 }
            NumberAnimation { to: 9; duration: 120 }
        }
    }

    // ---------------------------------------------------------------- tampo, risco de faca, marca de caneca
    Model {
        source: "#Rectangle"
        eulerRotation.x: -90
        scale: Qt.vector3d(30, 20, 1)
        materials: PrincipledMaterial {
            baseColorMap: Texture { source: vista.tex("tampo"); scaleU: 3; scaleV: 1; tilingModeHorizontal: Texture.Repeat; tilingModeVertical: Texture.Repeat }
            normalMap: Texture { source: vista.tex("tampo_normal"); scaleU: 3; scaleV: 1; tilingModeHorizontal: Texture.Repeat; tilingModeVertical: Texture.Repeat }
            normalStrength: 0.9
            roughness: 0.75
        }
    }
    component Decalque: Model {
        property string img
        source: "#Rectangle"
        eulerRotation.x: -90
        materials: PrincipledMaterial {
            baseColorMap: Texture { source: vista.tex(img) }
            alphaMode: PrincipledMaterial.Blend
            roughness: 0.8
        }
    }
    Decalque { img: "riscos"; position: Qt.vector3d(80, 0.4, -300); scale: Qt.vector3d(3.4, 1.6, 1); eulerRotation.z: 8 }
    Decalque { img: "riscos"; position: Qt.vector3d(-90, 0.4, 330); scale: Qt.vector3d(3, 1.4, 1); eulerRotation.z: -14 }
    Decalque { img: "mancha"; position: Qt.vector3d(300, 0.5, -170); scale: Qt.vector3d(1.7, 1.7, 1) }
    Decalque { img: "mancha"; position: Qt.vector3d(-230, 0.5, -60); scale: Qt.vector3d(1.4, 1.4, 1); eulerRotation.z: 60 }

    // ---------------------------------------------------------------- o CONTRATO no meio (o menu vai escrito nele)
    Model {
        geometry: Malha { pedido: "folha|1|1|0|0.012|7|plano" }
        position: Qt.vector3d(0, 1.2, 0)
        eulerRotation.y: 1.5
        scale: Qt.vector3d(540, 60, 720)
        materials: PrincipledMaterial {
            baseColorMap: Texture { source: vista.tex("contrato") }
            roughness: 0.9
            cullMode: Material.NoCulling
        }
    }
    Model {   // selo de cera do contrato
        geometry: Malha { pedido: "torno|0,0; 22,0; 25,3; 22,7; 14,8; 0,8|0.18|10|plano" }
        position: Qt.vector3d(-185, 3, 300)
        materials: PrincipledMaterial { baseColor: "#9a1a14"; roughness: 0.35; clearcoatAmount: 0.6 }
    }

    // ---------------------------------------------------------------- pano e livro (canto de cima, esquerda)
    Model {
        geometry: Malha { pedido: "folha|1|1|0|0.025|4|plano" }
        position: Qt.vector3d(-520, 0.6, -300)
        eulerRotation.y: 14
        scale: Qt.vector3d(380, 150, 270)
        materials: PrincipledMaterial { baseColorMap: Texture { source: vista.tex("pano") }
                roughness: 0.95; cullMode: Material.NoCulling }
    }
    Node {   // livro vermelho com a cruz dourada
        position: Qt.vector3d(-490, 12, -295)
        eulerRotation.y: -22
        Model {   // miolo (folhas)
            source: "#Cube"
            position.y: 22
            scale: Qt.vector3d(2.1, 0.36, 1.6)
            materials: PrincipledMaterial { baseColor: "#e8d8b0"; roughness: 0.9 }
        }
        Model {   // capa de baixo
            source: "#Cube"
            position.y: 2
            scale: Qt.vector3d(2.24, 0.06, 1.72)
            materials: PrincipledMaterial { baseColor: "#6e1c1a"; roughness: 0.7 }
        }
        Model {   // capa de cima
            source: "#Cube"
            position.y: 43
            scale: Qt.vector3d(2.24, 0.06, 1.72)
            materials: PrincipledMaterial { baseColor: "#6e1c1a"; roughness: 0.7 }
        }
        Model {   // lombada
            source: "#Cube"
            position: Qt.vector3d(-111, 22, 0)
            scale: Qt.vector3d(0.06, 0.44, 1.72)
            materials: PrincipledMaterial { baseColor: "#5a1412"; roughness: 0.7 }
        }
        Model {   // a arte da capa (cruz e moldura em ouro)
            source: "#Rectangle"
            position.y: 46.2
            eulerRotation.x: -90
            scale: Qt.vector3d(2.2, 1.68, 1)
            materials: PrincipledMaterial { baseColorMap: Texture { source: vista.tex("livro") }
                roughness: 0.55; metalness: 0.15 }
        }
        Repeater3D {   // cantoneiras de metal
            model: [Qt.point(-1, -1), Qt.point(1, -1), Qt.point(1, 1), Qt.point(-1, 1)]
            Model {
                source: "#Cube"
                position: Qt.vector3d(modelData.x * 102, 46, modelData.y * 78)
                scale: Qt.vector3d(0.2, 0.04, 0.2)
                materials: PrincipledMaterial { baseColor: "#d8a85a"; metalness: 1; roughness: 0.35 }
            }
        }
    }

    // ---------------------------------------------------------------- vela no castiçal de latão (com alça)
    Node {
        id: vela
        position: Qt.vector3d(-560, 0, -20)
        Model {   // prato
            geometry: Malha { pedido: "torno|0,0; 70,0; 74,4; 72,9; 62,10; 20,12; 16,22; 15,32; 23,35; 24,42; 19,44; 0,44|0|12|plano" }
            materials: PrincipledMaterial { baseColor: "#d8a24e"; metalness: 1; roughness: 0.3; cullMode: Material.NoCulling }
        }
        Model {   // alça (argola presa na borda do prato)
            geometry: Malha { pedido: "toro|22|5|1|12|6|plano" }
            position: Qt.vector3d(86, 8, 0)
            eulerRotation.x: 90
            scale: Qt.vector3d(1, 1, 0.8)
            materials: PrincipledMaterial { baseColor: "#c8923e"; metalness: 1; roughness: 0.32 }
        }
        Model {   // a vela (cera torta)
            geometry: Malha { pedido: "torno|0,42; 18,42; 18.5,118; 17,128; 12,132; 0,131|0.1|10|plano" }
            materials: PrincipledMaterial { baseColor: "#efe2c2"; roughness: 0.6; emissiveFactor: Qt.vector3d(0.12, 0.07, 0.02) }
        }
        Repeater3D {   // cera escorrida (e uma poça no prato)
            model: [{a: 30, h: 100, s: 0.08}, {a: 150, h: 110, s: 0.07}, {a: 260, h: 92, s: 0.09}]
            Model {
                geometry: Malha { pedido: "icosaedro" }
                position: Qt.vector3d(Math.cos(modelData.a * Math.PI / 180) * 18, modelData.h, Math.sin(modelData.a * Math.PI / 180) * 18)
                scale: Qt.vector3d(modelData.s * 50, modelData.s * 150, modelData.s * 50)
                materials: PrincipledMaterial { baseColor: "#f2e6c8"; roughness: 0.55 }
            }
        }
        Model {
            geometry: Malha { pedido: "torno|0,0; 30,0; 32,2; 26,4; 0,5|0.25|9|plano" }
            position: Qt.vector3d(-6, 42, 8)
            materials: PrincipledMaterial { baseColor: "#f2e6c8"; roughness: 0.55 }
        }
        Model {   // pavio
            source: "#Cylinder"
            position.y: 138
            scale: Qt.vector3d(0.025, 0.12, 0.025)
            materials: PrincipledMaterial { baseColor: "#1a1008"; roughness: 0.9 }
        }
    }
    ParticleSystem3D {   // chama: partículas viradas pra câmera, somando luz
        running: vista.anima
        position: Qt.vector3d(-560, 146, -20)
        SpriteParticle3D {
            id: chama
            sprite: Texture { source: vista.tex("sprite_chama") }
            maxAmount: 160
            color: "#ff9a40"
            colorVariation: Qt.vector4d(0.1, 0.15, 0.05, 0.1)
            blendMode: SpriteParticle3D.Screen
            fadeInDuration: 60
            fadeOutDuration: 300
            billboard: true
        }
        ParticleEmitter3D {
            particle: chama
            emitRate: 90
            lifeSpan: 520
            lifeSpanVariation: 120
            particleScale: 6
            particleEndScale: 1.4
            particleScaleVariation: 1.2
            shape: ParticleShape3D { type: ParticleShape3D.Sphere; extents: Qt.vector3d(4, 2, 4) }
            velocity: VectorDirection3D { direction: Qt.vector3d(0, 60, 6); directionVariation: Qt.vector3d(6, 15, 6) }
        }
        SpriteParticle3D {
            id: miolo
            sprite: Texture { source: vista.tex("sprite_chama") }
            maxAmount: 80
            color: "#fff2b0"
            blendMode: SpriteParticle3D.Screen
            fadeOutDuration: 200
            billboard: true
        }
        ParticleEmitter3D {
            particle: miolo
            emitRate: 60
            lifeSpan: 300
            particleScale: 3.4
            particleEndScale: 0.9
            shape: ParticleShape3D { type: ParticleShape3D.Sphere; extents: Qt.vector3d(2, 1, 2) }
            velocity: VectorDirection3D { direction: Qt.vector3d(0, 45, 4); directionVariation: Qt.vector3d(3, 8, 3) }
        }
        SpriteParticle3D {
            id: brilho
            sprite: Texture { source: vista.tex("sprite_brilho") }
            maxAmount: 2
            color: "#ff9040"
            blendMode: SpriteParticle3D.Screen
            billboard: true
        }
        ParticleEmitter3D {   // halo quente parado em volta da chama
            particle: brilho
            emitRate: 3
            lifeSpan: 700
            particleScale: 40
            particleEndScale: 40
            velocity: VectorDirection3D { direction: Qt.vector3d(0, 0, 0) }
        }
        SpriteParticle3D {
            id: fagulha
            sprite: Texture { source: vista.tex("sprite_faisca") }
            maxAmount: 30
            color: "#ffc860"
            blendMode: SpriteParticle3D.Screen
            fadeOutDuration: 400
            billboard: true
        }
        ParticleEmitter3D {
            particle: fagulha
            emitRate: vista.nivel === 2 ? 4 : 0
            lifeSpan: 1500
            particleScale: 0.8
            particleEndScale: 0.2
            velocity: VectorDirection3D { direction: Qt.vector3d(0, 70, 0); directionVariation: Qt.vector3d(25, 25, 25) }
        }
        Wander3D { particles: [fagulha]; globalAmount: Qt.vector3d(14, 6, 14); globalPace: Qt.vector3d(1.4, 1.2, 1.4) }
    }

    // ---------------------------------------------------------------- o MAPA preso na mesa pela ADAGA
    Model {
        geometry: Malha { pedido: "folha|3|2|0.07|0.008|2|plano" }
        position: Qt.vector3d(-440, 0.8, 250)
        eulerRotation.y: 9
        scale: Qt.vector3d(380, 120, 300)
        materials: PrincipledMaterial { baseColorMap: Texture { source: vista.tex("mapa") }
                roughness: 0.9; cullMode: Material.NoCulling }
    }
    Model {   // selo de cera vermelha no canto do mapa
        geometry: Malha { pedido: "torno|0,0; 22,0; 25,3; 22,7; 14,8; 0,8|0.18|10|plano" }
        position: Qt.vector3d(-285, 4, 345)
        materials: PrincipledMaterial { baseColor: "#9a1a14"; roughness: 0.35; clearcoatAmount: 0.6 }
    }
    Node {   // a adaga: lâmina enfiada no mapa, inclinada, o cabo pra cima
        position: Qt.vector3d(-470, 0, 215)
        eulerRotation: Qt.vector3d(38, 35, 0)
        scale: Qt.vector3d(1.5, 1.5, 1.5)
        Model {   // lâmina (losango, faces chapadas); a ponta fica enterrada
            geometry: Malha { pedido: "torno|0,-40; 1,10; 1,120; 0.6,124; 0,125|0|4|plano" }
            scale: Qt.vector3d(11, 1, 2.6)
            materials: PrincipledMaterial { baseColor: "#d8dce4"; metalness: 0.75; roughness: 0.28; emissiveFactor: Qt.vector3d(0.06, 0.06, 0.07) }
        }
        Model {   // guarda (cruzeta)
            source: "#Cube"
            position.y: 128
            scale: Qt.vector3d(0.78, 0.09, 0.14)
            materials: PrincipledMaterial { baseColor: "#8a6a3a"; metalness: 1; roughness: 0.35 }
        }
        Repeater3D {   // pontas da guarda
            model: [-1, 1]
            Model {
                geometry: Malha { pedido: "icosaedro" }
                position: Qt.vector3d(modelData * 42, 128, 0)
                scale: Qt.vector3d(7, 7, 7)
                materials: PrincipledMaterial { baseColor: "#8a6a3a"; metalness: 1; roughness: 0.35 }
            }
        }
        Model {   // cabo de couro
            geometry: Malha { pedido: "torno|0,132; 6.5,132; 7.5,150; 7,170; 6.5,190; 0,190|0|8|plano" }
            materials: PrincipledMaterial { baseColor: "#3a2214"; roughness: 0.85 }
        }
        Repeater3D {   // tiras de couro enroladas
            model: 4
            Model {
                geometry: Malha { pedido: "toro|7.4|1.6|1|10|5|plano" }
                position.y: 140 + index * 13
                materials: PrincipledMaterial { baseColor: "#2a180c"; roughness: 0.9 }
            }
        }
        Model {   // pomo
            geometry: Malha { pedido: "icosaedro" }
            position.y: 198
            scale: Qt.vector3d(11, 11, 11)
            materials: PrincipledMaterial { baseColor: "#9a7a44"; metalness: 1; roughness: 0.3 }
        }
    }

    // ---------------------------------------------------------------- moedas (ouro e cobre, com a cruz)
    component Moeda: Model {
        property bool ouro: true
        geometry: Malha { pedido: "moeda|12" }
        scale: Qt.vector3d(21, 21, 21)
        materials: PrincipledMaterial {
            baseColorMap: Texture { source: vista.tex(ouro ? "moeda_ouro" : "moeda_cobre") }
            metalness: 0.65
            roughness: 0.38
            cullMode: Material.NoCulling
        }
    }
    readonly property var moedas: [
        {x: -340, z: 20, r: 10, o: true}, {x: -330, z: 150, r: 40, o: true}, {x: -380, z: 110, r: 0, o: false},
        {x: -300, z: 190, r: 20, o: true}, {x: -280, z: 420, r: 0, o: true}, {x: -240, z: 450, r: 70, o: false},
        {x: 300, z: 440, r: 15, o: true}, {x: 420, z: -230, r: 0, o: true}, {x: 380, z: -200, r: 30, o: true},
        {x: 440, z: -170, r: 50, o: false}, {x: 350, z: -265, r: 0, o: true}, {x: 340, z: -340, r: 25, o: false},
        {x: 640, z: 60, r: 10, o: true}, {x: -640, z: 160, r: 0, o: false}
    ]
    Repeater3D {
        model: vista.moedas
        Moeda {
            ouro: modelData.o
            position: Qt.vector3d(modelData.x, 0.5, modelData.z)
            eulerRotation.y: modelData.r
        }
    }
    Repeater3D {   // pilhinha
        model: 6
        Moeda {
            position: Qt.vector3d(-390 + Math.sin(index * 1.7) * 2.5, 0.5 + index * 3.4, 60 + Math.cos(index * 2.3) * 2.5)
            eulerRotation.y: index * 37
        }
    }
    Moeda {   // uma escorada na outra, meio inclinada
        position: Qt.vector3d(-330, 9, 80)
        eulerRotation: Qt.vector3d(0, 20, 22)
    }

    // ---------------------------------------------------------------- saquinho de moedas (canto de cima, direita)
    Node {
        position: Qt.vector3d(500, 0, -290)
        eulerRotation: Qt.vector3d(0, 30, 0)
        scale: Qt.vector3d(1.35, 1.35, 1.35)
        Node {
            eulerRotation.z: -62   // tombado, com a boca pro lado das moedas
            position.y: 45
            Model {
                geometry: Malha { pedido: "torno|0,-55; 30,-52; 52,-35; 58,-10; 50,15; 28,32; 18,40|0.12|9|plano" }
                materials: PrincipledMaterial { baseColorMap: Texture { source: vista.tex("couro") }
                roughness: 0.85; cullMode: Material.NoCulling }
            }
            Model {   // a boca franzida
                geometry: Malha { pedido: "torno|18,40; 22,50; 30,62; 26,64; 16,52; 12,44|0.3|9|plano" }
                materials: PrincipledMaterial { baseColorMap: Texture { source: vista.tex("couro") }
                roughness: 0.85; cullMode: Material.NoCulling }
            }
            Model {   // cordão
                geometry: Malha { pedido: "toro|19|3|1|10|5|plano" }
                position.y: 42
                materials: PrincipledMaterial { baseColor: "#c8a46a"; roughness: 0.9 }
            }
        }
    }

    // ---------------------------------------------------------------- caneca (direita)
    Node {
        position: Qt.vector3d(470, 0, -40)
        eulerRotation.y: -30
        Model {   // corpo de aduelas (10 lados, chapado)
            geometry: Malha { pedido: "torno|0,0; 68,0; 72,4; 74,10; 75,150; 76,158; 73,163; 66,164; 64,160; 63,16; 0,14|0|10|plano" }
            materials: PrincipledMaterial { baseColorMap: Texture { source: vista.tex("caneca"); scaleU: 2 }
                roughness: 0.65; cullMode: Material.NoCulling }
        }
        Model {   // a cerveja
            source: "#Cylinder"
            position.y: 140
            scale: Qt.vector3d(1.26, 0.02, 1.26)
            materials: PrincipledMaterial { baseColor: "#c8841a"; roughness: 0.15; emissiveFactor: Qt.vector3d(0.08, 0.04, 0) }
        }
        Repeater3D {   // aros de ferro
            model: [26, 138]
            Node {
                position.y: modelData
                Model {
                    geometry: Malha { pedido: "toro|76|4|1|10|4|plano" }
                    materials: PrincipledMaterial { baseColor: "#4a4a52"; metalness: 1; roughness: 0.4 }
                }
                Repeater3D {   // rebites
                    model: 10
                    Model {
                        geometry: Malha { pedido: "icosaedro" }
                        position: Qt.vector3d(Math.cos((index + 0.5) * Math.PI / 5) * 80, 0, Math.sin((index + 0.5) * Math.PI / 5) * 80)
                        scale: Qt.vector3d(3.2, 3.2, 3.2)
                        materials: PrincipledMaterial { baseColor: "#6a6a72"; metalness: 1; roughness: 0.35 }
                    }
                }
            }
        }
        Model {   // asa quadradona (meia argola de poucos lados)
            geometry: Malha { pedido: "toro|42|10|0.56|7|5|plano" }
            position: Qt.vector3d(74, 92, 0)
            eulerRotation: Qt.vector3d(90, 0, -100)
            materials: PrincipledMaterial { baseColorMap: Texture { source: vista.tex("caneca") }
                roughness: 0.6 }
        }
        Model {   // espuma transbordando
            geometry: Malha { pedido: "espuma|20|8|plano" }
            position.y: 156
            scale: Qt.vector3d(72, 72, 72)
            materials: PrincipledMaterial { baseColor: "#f2e4c4"; roughness: 0.85; emissiveFactor: Qt.vector3d(0.02, 0.015, 0.01); cullMode: Material.NoCulling }
        }
        Repeater3D {   // espuma escorrendo pela parede
            model: [{a: 200, h: 138, s: 0.09}, {a: 235, h: 126, s: 0.07}, {a: 320, h: 140, s: 0.08}, {a: 90, h: 132, s: 0.06}]
            Model {
                geometry: Malha { pedido: "icosaedro" }
                position: Qt.vector3d(Math.cos(modelData.a * Math.PI / 180) * 76, modelData.h, Math.sin(modelData.a * Math.PI / 180) * 76)
                scale: Qt.vector3d(modelData.s * 60, modelData.s * 200, modelData.s * 60)
                materials: PrincipledMaterial { baseColor: "#f6ecd2"; roughness: 0.9 }
            }
        }
        ParticleSystem3D {   // bolhas: nascem na espuma, sobem um pouquinho e estouram
            running: vista.anima
            position.y: 180
            ModelParticle3D {
                id: bolha
                delegate: Model {
                    source: "#Sphere"
                    scale: Qt.vector3d(0.03, 0.03, 0.03)
                    materials: PrincipledMaterial { baseColor: "#ffffff"; roughness: 0.05; opacity: 0.7; alphaMode: PrincipledMaterial.Blend }
                }
                maxAmount: 60
                fadeInEffect: Particle3D.FadeScale
                fadeOutEffect: Particle3D.FadeScale
                fadeOutDuration: 120
            }
            ParticleEmitter3D {
                particle: bolha
                emitRate: vista.nivel === 2 ? 22 : 10
                lifeSpan: 900
                lifeSpanVariation: 400
                particleScale: 1
                particleScaleVariation: 0.6
                shape: ParticleShape3D { type: ParticleShape3D.Cylinder; extents: Qt.vector3d(60, 6, 60) }
                velocity: VectorDirection3D { direction: Qt.vector3d(0, 12, 0); directionVariation: Qt.vector3d(4, 6, 4) }
            }
        }
    }

    // ---------------------------------------------------------------- pão com farelos (canto de baixo, direita)
    Node {
        position: Qt.vector3d(540, 0, 270)
        eulerRotation.y: 25
        Model {
            geometry: Malha { pedido: "torno|0,0; 0.85,0; 1,0.2; 0.97,0.45; 0.85,0.68; 0.62,0.86; 0.32,0.97; 0,1|0.06|12|plano" }
            scale: Qt.vector3d(150, 95, 78)
            materials: PrincipledMaterial { baseColorMap: Texture { source: vista.tex("pao") }
                roughness: 0.8; cullMode: Material.NoCulling }
        }
        Repeater3D {   // cortes na casca
            model: [-50, -10, 30]
            Model {
                source: "#Cube"
                position: Qt.vector3d(modelData, 90 - Math.abs(modelData) * 0.5, 0)
                eulerRotation: Qt.vector3d(0, 70, -modelData * 0.4)
                scale: Qt.vector3d(0.9, 0.06, 0.12)
                materials: PrincipledMaterial { baseColor: "#e8b870"; roughness: 0.9 }
            }
        }
    }
    readonly property var farelos: [
        {x: 420, z: 240, s: 5}, {x: 440, z: 300, s: 4}, {x: 400, z: 330, s: 6}, {x: 460, z: 360, s: 3.5},
        {x: 380, z: 270, s: 3}, {x: 650, z: 330, s: 4}, {x: 610, z: 190, s: 3.5}, {x: 470, z: 200, s: 4.5}
    ]
    Repeater3D {
        model: vista.farelos
        Model {
            geometry: Malha { pedido: "icosaedro" }
            position: Qt.vector3d(modelData.x, modelData.s * 0.6, modelData.z)
            eulerRotation: Qt.vector3d(index * 40, index * 70, 0)
            scale: Qt.vector3d(modelData.s, modelData.s * 0.7, modelData.s)
            materials: PrincipledMaterial { baseColor: index % 2 ? "#c07a3a" : "#e8c48a"; roughness: 0.9 }
        }
    }

    // ---------------------------------------------------------------- dois d6
    Repeater3D {
        model: [{x: 310, z: 300, ry: 20, rx: 0}, {x: 380, z: 345, ry: -35, rx: 90}]
        Model {
            geometry: Malha { pedido: "dado" }
            position: Qt.vector3d(modelData.x, 22, modelData.z)
            eulerRotation: Qt.vector3d(modelData.rx, modelData.ry, 0)
            scale: Qt.vector3d(22, 22, 22)
            materials: PrincipledMaterial {
                baseColorMap: Texture { source: vista.tex("dados") }
                roughness: 0.3
                clearcoatAmount: 0.5
                cullMode: Material.NoCulling
            }
        }
    }
}
