// 🌊 Terror, tela 2 em 3D (v0.56, o Manel pediu tudo em 3D): tempestade no mar. MAR de verdade (ondas no
// shader, espuma nas cristas), penhasco de rochas facetadas com a casinha e o FAROL — o feixe GIRA (cone de luz
// + holofote que varre o mar) —, barco balançando, chuva, espuma estourando nas pedras, RAIOS com clarão e,
// em parte dos raios (nunca sem raio), a silhueta do CTHULHU lá no fundo.
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

    property real tempo: 0
    NumberAnimation on tempo { from: 0; to: 1000; duration: 1000000; loops: Animation.Infinite; running: vista.anima }
    property real clarao: 0          // 0..1 durante o raio
    property real cthulhuVisivel: 0

    environment: SceneEnvironment {
        backgroundMode: SceneEnvironment.Color
        clearColor: "#0a1610"
        antialiasingMode: SceneEnvironment.MSAA
        antialiasingQuality: vista.nivel === 2 ? SceneEnvironment.VeryHigh : SceneEnvironment.High
        tonemapMode: SceneEnvironment.TonemapModeFilmic
        fog: Fog {
            enabled: true
            color: Qt.rgba(0.05 + vista.clarao * 0.25, 0.11 + vista.clarao * 0.35, 0.08 + vista.clarao * 0.28, 1)
            depthEnabled: true
            depthNear: 3200
            depthFar: 9000
            depthCurve: 1.2
        }
    }
    PerspectiveCamera {
        id: camera
        position: Qt.vector3d(0, 330, 1500)
        eulerRotation.x: -5
        fieldOfView: 46
        clipNear: 20
        clipFar: 12000
    }

    // ---------------------------------------------------------------- luzes
    DirectionalLight {   // a noite (e o clarão do raio)
        eulerRotation: Qt.vector3d(-35, 20, 0)
        color: "#9ad8b0"
        brightness: 0.4 + vista.clarao * 2.6
    }

    // ---------------------------------------------------------------- céu, nuvens, Cthulhu, raio
    Model {
        source: "#Rectangle"
        position: Qt.vector3d(0, 1600, -7600)
        scale: Qt.vector3d(190, 70, 1)
        materials: PrincipledMaterial {
            lighting: PrincipledMaterial.NoLighting
            baseColorMap: Texture { source: vista.tex("ceu_farol") }
            baseColor: Qt.rgba(1.1 + vista.clarao * 1.4, 1.1 + vista.clarao * 1.6, 1.1 + vista.clarao * 1.4, 1)
        }
    }
    // (v0.58) o CTHULHU em 3D, lá no fundão do mar: um polvo GIGANTE (cabeça alta e bulbosa, olhos acesos,
    // tentáculos grossos saindo da água em arco e enrolando na ponta). Escuro: no clarão do raio vira SILHUETA.
    component Pele: PrincipledMaterial {
        baseColor: "#050c0a"
        roughness: 0.55
        specularAmount: 0.3
    }
    Node {
        id: cthulhu
        visible: vista.cthulhuVisivel > 0.01
        opacity: vista.cthulhuVisivel
        position: Qt.vector3d(2300, 0, -5600)
        eulerRotation.y: -18
        scale: Qt.vector3d(1.3, 1.3, 1.3)
        // A CABEÇA afundada no mar: aparece só do meio dos olhos pra cima (o corpo todo está embaixo d'água)
        Model {
            source: "#Sphere"
            position: Qt.vector3d(-20, 160, -30)
            eulerRotation: Qt.vector3d(-10, 0, 7)
            scale: Qt.vector3d(4.8, 7.8, 4.8)
            materials: Pele {}
        }
        Model {   // a testa / arcada pesada em cima dos olhos
            source: "#Sphere"
            position: Qt.vector3d(0, 110, 150)
            scale: Qt.vector3d(4.2, 1.6, 2.2)
            materials: Pele {}
        }
        Repeater3D {   // olhos acesos, rentes à água
            model: [-1, 1]
            Model {
                source: "#Sphere"
                position: Qt.vector3d(modelData * 92, 66, 232)
                scale: Qt.vector3d(0.5, 0.24, 0.2)
                materials: PrincipledMaterial { lighting: PrincipledMaterial.NoLighting; baseColor: "#f4ffc0" }
            }
        }
        // os TENTÁCULOS saindo da água em volta, cada um de um jeito (nada igual, nada espelhado):
        // g = giro (+1 enrola pra cima/dentro, -1 enrola pra baixo/fora) · v = quanto enrola (0 = solto)
        // l = 1: arco que volta pra dentro d'água (só a "corcova") · tx/tz = inclinação
        Repeater3D {
            model: [
                {x: 520, z: 120, a: -12, tx: -6, tz: 6, alto: 1.4, largo: 0.5, enr: 0.28, g: 1, v: 1.9, l: 0, r: 72, s: 1.0},
                {x: 820, z: -80, a: 30, tx: 10, tz: -10, alto: 1.0, largo: 0.6, enr: 0.24, g: -1, v: 1.3, l: 0, r: 60, s: 0.95},
                {x: 360, z: 420, a: 8, tx: 4, tz: 0, alto: 0.38, largo: 1.0, enr: 0, g: 1, v: 0, l: 1, r: 64, s: 0.9},
                {x: 1050, z: 160, a: -40, tx: -10, tz: 14, alto: 0.7, largo: 0.3, enr: 0.2, g: 1, v: 0.6, l: 0, r: 46, s: 0.85},
                {x: -480, z: 60, a: 186, tx: 8, tz: -8, alto: 1.2, largo: 0.62, enr: 0.3, g: 1, v: 2.2, l: 0, r: 70, s: 1.05},
                {x: -760, z: 260, a: 160, tx: -14, tz: 6, alto: 0.85, largo: 0.4, enr: 0.24, g: -1, v: 1.6, l: 0, r: 54, s: 0.9},
                {x: -980, z: -120, a: 210, tx: 6, tz: -16, alto: 1.55, largo: 0.26, enr: 0.16, g: 1, v: 0.45, l: 0, r: 52, s: 0.85},
                {x: -340, z: 460, a: 150, tx: 0, tz: 0, alto: 0.32, largo: 0.85, enr: 0, g: 1, v: 0, l: 1, r: 58, s: 0.85},
                {x: -200, z: -300, a: 118, tx: -18, tz: 4, alto: 1.7, largo: 0.36, enr: 0.26, g: -1, v: 2.4, l: 0, r: 60, s: 0.95},
                {x: 260, z: -320, a: 70, tx: 8, tz: 10, alto: 1.25, largo: 0.5, enr: 0.2, g: 1, v: 1.1, l: 0, r: 56, s: 0.9},
                {x: 1250, z: -360, a: 12, tx: -8, tz: -6, alto: 0.9, largo: 0.24, enr: 0.18, g: -1, v: 0.9, l: 0, r: 40, s: 0.75},
                {x: -1250, z: 200, a: 230, tx: 16, tz: -2, alto: 0.6, largo: 0.5, enr: 0.3, g: 1, v: 1.4, l: 0, r: 42, s: 0.75},
                {x: 700, z: 380, a: -60, tx: 0, tz: 0, alto: 0.26, largo: 0.7, enr: 0, g: 1, v: 0, l: 1, r: 44, s: 0.8}
            ]
            Model {
                geometry: Malha { pedido: "tentaculo|1|" + modelData.largo + "|" + modelData.enr + "|" + (modelData.r / 1000) + "|0.011|"
                                          + modelData.g + "|" + modelData.v + "|" + modelData.l }
                position: Qt.vector3d(modelData.x, -20, modelData.z)
                eulerRotation: Qt.vector3d(modelData.tx, modelData.a, modelData.tz)
                // (v0.58, o Manel: "mais perto da água") a altura vai a 58%
                scale: Qt.vector3d(1000 * modelData.s, 580 * modelData.alto * modelData.s, 1000 * modelData.s)
                materials: Pele {}
            }
        }
    }    Repeater3D {   // nuvens passando (na frente do Cthulhu)
        model: [{y: 2600, z: -7000, s: 0, v: 140000, o: 0.95}, {y: 2000, z: -6800, s: 1, v: 100000, o: 0.8}]
        Model {
            source: "#Rectangle"
            position: Qt.vector3d(0, modelData.y, modelData.z)
            scale: Qt.vector3d(160, 28, 1)
            opacity: modelData.o
            materials: PrincipledMaterial {
                lighting: PrincipledMaterial.NoLighting
                baseColorMap: Texture { source: vista.tex("nuvem_farol" + modelData.s); tilingModeHorizontal: Texture.Repeat
                    scaleU: 2; positionU: vista.tempo * 1000 / modelData.v }
                baseColor: Qt.rgba(1 + vista.clarao * 2, 1 + vista.clarao * 2.4, 1 + vista.clarao * 2, 1)
                alphaMode: PrincipledMaterial.Blend
            }
        }
    }
    Model {   // o raio
        id: raio
        property int v: 0
        source: "#Rectangle"
        position: Qt.vector3d(600, 2100, -6500)
        scale: Qt.vector3d(14, 27, 1)
        opacity: 0
        materials: PrincipledMaterial {
            lighting: PrincipledMaterial.NoLighting
            baseColorMap: Texture { source: vista.tex("raio" + raio.v) }
            alphaMode: PrincipledMaterial.Blend
            blendMode: PrincipledMaterial.Screen
        }
    }
    Timer {   // de vez em quando cai um raio; às vezes (só junto com um raio) o Cthulhu aparece
        running: vista.anima; repeat: true; interval: 5000
        onTriggered: {
            interval = 4000 + Math.random() * 9000
            raio.v = Math.floor(Math.random() * 3)
            raio.x = -800 + Math.random() * 3200
            cthulhuAnim.stop()
            if (Math.random() < 0.4) cthulhuAnim.start()
            raioAnim.start()
        }
    }
    SequentialAnimation {
        id: raioAnim
        ParallelAnimation {
            NumberAnimation { target: raio; property: "opacity"; to: 1; duration: 30 }
            NumberAnimation { target: vista; property: "clarao"; to: 1; duration: 30 }
        }
        PauseAnimation { duration: 70 }
        ParallelAnimation {
            NumberAnimation { target: raio; property: "opacity"; to: 0.2; duration: 60 }
            NumberAnimation { target: vista; property: "clarao"; to: 0.2; duration: 60 }
        }
        ParallelAnimation {
            NumberAnimation { target: raio; property: "opacity"; to: 1; duration: 40 }
            NumberAnimation { target: vista; property: "clarao"; to: 0.85; duration: 40 }
        }
        PauseAnimation { duration: 120 }
        ParallelAnimation {
            NumberAnimation { target: raio; property: "opacity"; to: 0; duration: 380 }
            NumberAnimation { target: vista; property: "clarao"; to: 0; duration: 800 }
        }
    }
    SequentialAnimation {
        id: cthulhuAnim
        NumberAnimation { target: vista; property: "cthulhuVisivel"; to: 0.95; duration: 30 }
        PauseAnimation { duration: 90 }
        NumberAnimation { target: vista; property: "cthulhuVisivel"; to: 0.35; duration: 60 }
        NumberAnimation { target: vista; property: "cthulhuVisivel"; to: 0.9; duration: 40 }
        PauseAnimation { duration: 280 }
        NumberAnimation { target: vista; property: "cthulhuVisivel"; to: 0; duration: 1000; easing.type: Easing.InQuad }
    }

    // ---------------------------------------------------------------- o MAR
    Model {
        geometry: Malha { pedido: "grade|160" }
        position: Qt.vector3d(0, 0, -2200)
        scale: Qt.vector3d(14000, 1, 11000)
        materials: CustomMaterial {
            property real tempo: vista.tempo
            property real agito: 0.7
            vertexShader: "shaders/mar.vert"
            fragmentShader: "shaders/mar.frag"
        }
    }

    // ---------------------------------------------------------------- penhasco (rochas facetadas) + topo de grama
    readonly property var rochas: [
        {x: -950, z: -150, sx: 520, sy: 560, sz: 480, r: 10, tx: 4, tz: -3}, {x: -680, z: 80, sx: 260, sy: 520, sz: 240, r: 40, tx: -6, tz: 5},
        {x: -1250, z: 160, sx: 420, sy: 520, sz: 400, r: 70, tx: 3, tz: 6}, {x: -600, z: -360, sx: 220, sy: 470, sz: 230, r: 15, tx: 8, tz: -4},
        {x: -470, z: 280, sx: 170, sy: 230, sz: 160, r: 30, tx: -12, tz: 8}, {x: -380, z: 420, sx: 110, sy: 110, sz: 120, r: 80, tx: 15, tz: -10},
        {x: -1300, z: -420, sx: 460, sy: 580, sz: 420, r: 55, tx: -3, tz: 2}, {x: -540, z: -60, sx: 180, sy: 400, sz: 170, r: 120, tx: -5, tz: -8},
        {x: -800, z: 300, sx: 220, sy: 300, sz: 200, r: 200, tx: 10, tz: 6}, {x: -300, z: 560, sx: 80, sy: 60, sz: 90, r: 10, tx: 20, tz: 0}
    ]
    Node {   // tudo do penhasco (rochas, casa, farol, espuma) mais pro fundo
    position: Qt.vector3d(-380, 0, -950)
    Repeater3D {
        model: vista.rochas
        Model {
            geometry: Malha { pedido: "torno|0,-0.4; 1,-0.4; 0.96,0.25; 0.84,0.66; 0.6,0.93; 0.2,1; 0,1|0.22|7|plano" }
            position: Qt.vector3d(modelData.x, 0, modelData.z)
            eulerRotation: Qt.vector3d(modelData.tx, modelData.r, modelData.tz)
            scale: Qt.vector3d(modelData.sx, modelData.sy, modelData.sz)
            materials: PrincipledMaterial {
                baseColorMap: Texture { source: vista.tex("pedra_rocha") }
                roughness: 0.85
            }
        }
    }
    Model {   // topo plano com grama
        geometry: Malha { pedido: "torno|0,0; 1,0; 0.98,0.5; 0.85,0.95; 0,1|0.12|9|plano" }
        position: Qt.vector3d(-1000, 505, -150)
        scale: Qt.vector3d(470, 40, 400)
        materials: PrincipledMaterial { baseColorMap: Texture { source: vista.tex("grama") }
            roughness: 0.9 }
    }

    // ---------------------------------------------------------------- a casinha
    Node {
        position: Qt.vector3d(-1180, 560, -40)
        eulerRotation.y: 20
        Model {
            source: "#Cube"
            position.y: 55
            scale: Qt.vector3d(2.0, 1.1, 1.3)
            materials: PrincipledMaterial { baseColorMap: Texture { source: vista.tex("pedra_farol") }
                roughness: 0.8 }
        }
        Model {   // telhado (cubo girado 45° = prisma)
            source: "#Cube"
            position.y: 112
            eulerRotation.x: 45
            scale: Qt.vector3d(2.15, 0.95, 0.95)
            materials: PrincipledMaterial { baseColor: "#6a2a1e"; roughness: 0.7 }
        }
        Repeater3D {
            model: [-45, 40]
            Model {
                source: "#Cube"
                position: Qt.vector3d(modelData, 60, 66)
                scale: Qt.vector3d(0.24, 0.3, 0.02)
                materials: PrincipledMaterial { baseColor: "#e8d070"; emissiveFactor: Qt.vector3d(0.5, 0.4, 0.1) }
            }
        }
    }

    // ---------------------------------------------------------------- o FAROL
    Node {
        position: Qt.vector3d(-900, 560, -200)
        Model {   // torre
            geometry: Malha { pedido: "torno|0,0; 82,0; 82,14; 56,380; 62,392; 0,392|0|12|plano" }
            materials: PrincipledMaterial { baseColorMap: Texture { source: vista.tex("pedra_farol"); scaleU: 3; scaleV: 3 }
                roughness: 0.8 }
        }
        Model {   // galeria
            geometry: Malha { pedido: "torno|0,392; 92,392; 92,404; 0,404|0|12|plano" }
            materials: PrincipledMaterial { baseColor: "#2a302a"; metalness: 0.6; roughness: 0.5 }
        }
        Model {   // grade da galeria
            geometry: Malha { pedido: "toro|88|2.5|1|16|4|plano" }
            position.y: 432
            materials: PrincipledMaterial { baseColor: "#1a201a"; metalness: 0.6; roughness: 0.5 }
        }
        Repeater3D {
            model: 12
            Model {
                source: "#Cylinder"
                position: Qt.vector3d(Math.cos(index * Math.PI / 6) * 88, 418, Math.sin(index * Math.PI / 6) * 88)
                scale: Qt.vector3d(0.03, 0.28, 0.03)
                materials: PrincipledMaterial { baseColor: "#1a201a" }
            }
        }
        Model {   // sala da lâmpada (vidro aceso)
            geometry: Malha { pedido: "torno|40,404; 40,480|0|8|plano" }
            materials: PrincipledMaterial {
                baseColor: "#d8f080"
                emissiveFactor: Qt.vector3d(1.2, 1.4, 0.6)
                cullMode: Material.NoCulling
            }
        }
        Model {   // teto
            geometry: Malha { pedido: "torno|0,480; 56,480; 56,488; 0,548|0|8|plano" }
            materials: PrincipledMaterial { baseColor: "#5a2a1e"; roughness: 0.6 }
        }
        Node {   // a LUZ que gira
            position.y: 442
            NumberAnimation on eulerRotation.y { from: 0; to: 360; duration: 8000; loops: Animation.Infinite; running: vista.anima }
            Node {
                eulerRotation.z: -90       // o cone (eixo y) passa a apontar pra +x
                Model {   // halo largo e bem fraco em volta (a luz se espalhando na chuva)
                    geometry: Malha { pedido: "torno|16,0; 700,2900|0|16" }
                    materials: PrincipledMaterial {
                        lighting: PrincipledMaterial.NoLighting
                        baseColor: "#c8e070"
                        opacityMap: Texture { source: vista.tex("feixe_grad") }
                        opacity: 0.12
                        alphaMode: PrincipledMaterial.Blend
                        blendMode: PrincipledMaterial.Screen
                        cullMode: Material.NoCulling
                        depthDrawMode: Material.NeverDepthDraw
                    }
                }
                Model {
                    geometry: Malha { pedido: "torno|10,0; 380,2600|0|16" }
                    materials: PrincipledMaterial {
                        lighting: PrincipledMaterial.NoLighting
                        baseColor: "#d8f080"
                        opacityMap: Texture { source: vista.tex("feixe_grad") }
                        opacity: 0.32
                        alphaMode: PrincipledMaterial.Blend
                        blendMode: PrincipledMaterial.Screen
                        cullMode: Material.NoCulling
                        depthDrawMode: Material.NeverDepthDraw
                    }
                }
            }
            SpotLight {   // e um holofote de verdade junto, varrendo o mar e a chuva
                eulerRotation.y: -90
                eulerRotation.x: -6
                color: "#d8f080"
                brightness: 30
                coneAngle: 14
                innerConeAngle: 4
                quadraticFade: 0.02
                linearFade: 0.2
            }
            Model {   // brilho da lâmpada
                source: "#Sphere"
                scale: Qt.vector3d(0.5, 0.5, 0.5)
                materials: PrincipledMaterial { lighting: PrincipledMaterial.NoLighting; baseColor: "#f8ffd0" }
            }
        }
        PointLight {   // a luz em volta do farol
            position.y: 442
            color: "#c8e870"
            brightness: 5
            quadraticFade: 0.6
        }
    }

    // ---------------------------------------------------------------- espuma estourando nas pedras
    ParticleSystem3D {
        running: vista.anima
        position: Qt.vector3d(-430, 10, 330)
        SpriteParticle3D {
            id: espuma
            sprite: Texture { source: vista.tex("sprite_fumaca") }
            maxAmount: 300
            color: Qt.rgba(0.8, 0.9, 0.85, 0.45)
            fadeOutDuration: 600
            billboard: true
        }
        ParticleEmitter3D {
            id: estouro
            particle: espuma
            emitRate: 0
            lifeSpan: 1300
            lifeSpanVariation: 300
            particleScale: 10
            particleEndScale: 26
            particleScaleVariation: 5
            shape: ParticleShape3D { type: ParticleShape3D.Cube; extents: Qt.vector3d(260, 10, 120) }
            velocity: VectorDirection3D { direction: Qt.vector3d(40, 380, 60); directionVariation: Qt.vector3d(120, 140, 120) }
        }
        Gravity3D { magnitude: 520 }
    }
    Timer {
        running: vista.anima; repeat: true; interval: 1800
        onTriggered: { interval = 1300 + Math.random() * 1600; estouro.burst(90) }
    }

    }

    // ---------------------------------------------------------------- o BARCO (balança)
    Node {
        position: Qt.vector3d(640, 55, 820)
        eulerRotation.y: 160
        SequentialAnimation on eulerRotation.z {
            running: vista.anima; loops: Animation.Infinite
            NumberAnimation { to: 4; duration: 2700; easing.type: Easing.InOutSine }
            NumberAnimation { to: -3; duration: 2900; easing.type: Easing.InOutSine }
        }
        SequentialAnimation on eulerRotation.x {
            running: vista.anima; loops: Animation.Infinite
            NumberAnimation { to: 3; duration: 2100; easing.type: Easing.InOutSine }
            NumberAnimation { to: -4; duration: 2300; easing.type: Easing.InOutSine }
        }
        SequentialAnimation on y {
            running: vista.anima; loops: Animation.Infinite
            NumberAnimation { to: 75; duration: 1900; easing.type: Easing.InOutSine }
            NumberAnimation { to: 40; duration: 2100; easing.type: Easing.InOutSine }
        }
        Node {
            scale: Qt.vector3d(460, 460, 460)
            Model {
                geometry: Malha { pedido: "casco" }
                materials: PrincipledMaterial { baseColorMap: Texture { source: vista.tex("madeira_barco"); scaleU: 4; scaleV: 2 }
                    roughness: 0.6; cullMode: Material.NoCulling }
            }
            Model {
                geometry: Malha { pedido: "conves" }
                position.y: -0.02
                materials: PrincipledMaterial { baseColorMap: Texture { source: vista.tex("madeira_barco") }
                    roughness: 0.25; cullMode: Material.NoCulling }
            }
        }
        Repeater3D {   // amurada: postes e corrimão dos dois lados
            model: 16
            Model {
                readonly property int lado: index < 8 ? -1 : 1
                readonly property real t: (index % 8) / 7
                source: "#Cube"
                position: Qt.vector3d(-420 + t * 560, 22, lado * 158 * (1 - Math.pow(Math.max(0, (-420 + t * 560) / 460), 1.8)))
                scale: Qt.vector3d(0.08, 0.5, 0.08)
                materials: PrincipledMaterial { baseColor: "#2a1a10"; roughness: 0.7 }
            }
        }
        Repeater3D {
            model: [-1, 1]
            Model {
                source: "#Cube"
                position: Qt.vector3d(-100, 46, modelData * 150)
                eulerRotation.y: modelData * 5
                scale: Qt.vector3d(6.6, 0.08, 0.1)
                materials: PrincipledMaterial { baseColor: "#3a2414"; roughness: 0.6 }
            }
        }
        Model {   // cabeço de amarração
            source: "#Cylinder"
            position: Qt.vector3d(200, 22, 0)
            scale: Qt.vector3d(0.32, 0.45, 0.32)
            materials: PrincipledMaterial { baseColor: "#4a3626"; roughness: 0.6 }
        }
        Repeater3D {   // corda enrolada
            model: 4
            Model {
                geometry: Malha { pedido: "toro|20|4|1|12|5|plano" }
                position: Qt.vector3d(200, 8 + index * 8, 0)
                materials: PrincipledMaterial { baseColor: "#8a7a48"; roughness: 0.9 }
            }
        }
        Repeater3D {   // escada de corda subindo pro mastro
            model: [-1, 1]
            Model {
                source: "#Cylinder"
                position: Qt.vector3d(-250, 330, modelData * 60)
                eulerRotation.z: -28
                scale: Qt.vector3d(0.04, 7.2, 0.04)
                materials: PrincipledMaterial { baseColor: "#6a5a34"; roughness: 0.9 }
            }
        }
        Repeater3D {
            model: 9
            Model {
                source: "#Cylinder"
                position: Qt.vector3d(-250 + (index - 4) * 0.47 * 72, 330 + (index - 4) * 72 * 0.88, 0)
                eulerRotation.x: 90
                scale: Qt.vector3d(0.03, 1.2, 0.03)
                materials: PrincipledMaterial { baseColor: "#6a5a34"; roughness: 0.9 }
            }
        }
    }

    // ---------------------------------------------------------------- chuva
    ParticleSystem3D {
        running: vista.anima
        position: Qt.vector3d(0, 1200, 400)
        SpriteParticle3D {
            id: gota
            sprite: Texture { source: vista.tex("gota") }
            maxAmount: vista.nivel === 2 ? 2400 : 1200
            color: "#c8e8d8"
            billboard: true
            fadeInDuration: 50
        }
        ParticleEmitter3D {
            particle: gota
            emitRate: vista.nivel === 2 ? 1600 : 800
            lifeSpan: 1300
            particleScale: 12
            particleScaleVariation: 4
            shape: ParticleShape3D { type: ParticleShape3D.Cube; extents: Qt.vector3d(2000, 10, 1400) }
            velocity: VectorDirection3D { direction: Qt.vector3d(260, -1500, 0); directionVariation: Qt.vector3d(40, 200, 40) }
        }
    }
}
