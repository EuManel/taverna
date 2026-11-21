// 📜 Medieval, tela 2 (v0.56, referência do Manel): o QUADRO DE MISSÕES em 3D, num muro de tijolos de pedra.
// Moldura de vigas com chapas de ferro, cartazes de papel presos com pregos e ligados por fios vermelhos, um mapa,
// selos de cera, estandarte com brasão, flâmulas, espadas cruzadas, cordas com brasões (lobo e torre), hera e a
// LAMPARINA acesa (chama de partículas, luz tremendo que faz sombra). O menu é escrito no cartaz grande do meio.
import QtQuick
import QtQuick3D
import QtQuick3D.Particles3D
import QtQuick3D.Helpers

View3D {
    id: vista
    property int nivel: ponte.nivel
    readonly property bool anima: nivel >= 1
    function tex(n) { return ponte.textura(n) }
    function acaso(i, k) { var s = Math.sin(i * 12.9898 + k * 78.233) * 43758.5453; return s - Math.floor(s) }
    camera: camera

    // onde o cartaz grande caiu no 2D (o menu é escrito nele)
    property rect tela: Qt.rect(0, 0, 0, 0)
    function medirTela() {
        var a = mapFrom3DScene(Qt.vector3d(-285, 262, 30))
        var b = mapFrom3DScene(Qt.vector3d(285, -340, 30))
        tela = Qt.rect(a.x, a.y, b.x - a.x, b.y - a.y)
    }
    onWidthChanged: Qt.callLater(medirTela)
    onHeightChanged: Qt.callLater(medirTela)
    Component.onCompleted: Qt.callLater(medirTela)

    environment: SceneEnvironment {
        backgroundMode: SceneEnvironment.Color
        clearColor: "#0c0a0a"
        antialiasingMode: SceneEnvironment.MSAA
        antialiasingQuality: vista.nivel === 2 ? SceneEnvironment.VeryHigh : SceneEnvironment.High
        aoEnabled: vista.nivel === 2
        aoStrength: 80
        aoDistance: 16
        aoSoftness: 40
        tonemapMode: SceneEnvironment.TonemapModeFilmic
    }
    PerspectiveCamera {
        id: camera
        position: Qt.vector3d(0, -40, 1640)
        fieldOfView: 40
        clipNear: 50
        clipFar: 5000
    }

    // ---------------------------------------------------------------- luzes
    DirectionalLight {   // luz geral quente vinda da frente/esquerda (sombras dos cartazes no quadro)
        eulerRotation: Qt.vector3d(-28, -32, 0)
        color: "#ffe0b8"
        brightness: 0.55
        castsShadow: true
        shadowMapQuality: Light.ShadowMapQualityHigh
        shadowFactor: 60
        shadowFilter: 8
        shadowBias: 3
    }
    PointLight {   // a lamparina (tremendo)
        id: luzLamparina
        position: Qt.vector3d(690, 320, 170)
        color: "#ffa850"
        brightness: 6
        quadraticFade: 0.45
        castsShadow: vista.nivel === 2
        shadowFactor: 60
        SequentialAnimation on brightness {
            running: vista.anima
            loops: Animation.Infinite
            NumberAnimation { to: 5; duration: 120; easing.type: Easing.InOutQuad }
            NumberAnimation { to: 6.6; duration: 90 }
            NumberAnimation { to: 5.6; duration: 150 }
            NumberAnimation { to: 6.9; duration: 100 }
            NumberAnimation { to: 6; duration: 130 }
        }
    }

    // ---------------------------------------------------------------- muro de tijolos de pedra
    readonly property int colunas: 19
    Repeater3D {
        model: vista.colunas * 22
        Model {
            readonly property int lin: Math.floor(index / vista.colunas)
            readonly property int col: index % vista.colunas
            source: "#Cube"
            position: Qt.vector3d(-1180 + col * 128 + (lin % 2) * 64, -700 + lin * 64, -90 + vista.acaso(index, 1) * 8)
            eulerRotation: Qt.vector3d((vista.acaso(index, 2) - 0.5) * 3, (vista.acaso(index, 3) - 0.5) * 4, (vista.acaso(index, 4) - 0.5) * 2)
            scale: Qt.vector3d(1.2, 0.56, 0.4)
            materials: PrincipledMaterial {
                baseColorMap: Texture { source: vista.tex("pedra_tijolo"); scaleU: 1 + vista.acaso(index, 5); scaleV: 0.6 }
                baseColor: Qt.rgba(0.75 + vista.acaso(index, 6) * 0.35, 0.72 + vista.acaso(index, 6) * 0.35, 0.78 + vista.acaso(index, 6) * 0.3, 1)
                roughness: 0.9
            }
        }
    }
    Model {   // reboco escuro atrás dos tijolos
        source: "#Rectangle"
        position.z: -112
        scale: Qt.vector3d(30, 18, 1)
        materials: PrincipledMaterial { baseColor: "#141214"; roughness: 1 }
    }

    // ---------------------------------------------------------------- o quadro: tábuas, vigas, chapas
    Repeater3D {
        model: 9
        Model {
            source: "#Cube"
            position: Qt.vector3d(-656 + index * 164, 0, -25)
            scale: Qt.vector3d(1.6, 9.3, 0.3)
            materials: PrincipledMaterial {
                baseColorMap: Texture { source: vista.tex("madeira_escura"); scaleU: 0.5; scaleV: 2; tilingModeVertical: Texture.Repeat }
                baseColor: Qt.rgba(0.85 + vista.acaso(index, 9) * 0.3, 0.85 + vista.acaso(index, 9) * 0.3, 0.85 + vista.acaso(index, 9) * 0.3, 1)
                roughness: 0.85
            }
        }
    }
    component Viga: Model {
        source: "#Cube"
        materials: PrincipledMaterial {
            baseColorMap: Texture { source: vista.tex("viga"); scaleU: 3; tilingModeHorizontal: Texture.Repeat }
            roughness: 0.8
        }
    }
    Viga { position: Qt.vector3d(0, 478, 10); scale: Qt.vector3d(16.4, 0.72, 0.6) }
    Viga { position: Qt.vector3d(0, -478, 10); scale: Qt.vector3d(16.4, 0.76, 0.6) }
    Viga { position: Qt.vector3d(-790, -80, 14); scale: Qt.vector3d(13.6, 0.72, 0.66); eulerRotation.z: 90 }
    Viga { position: Qt.vector3d(790, -80, 14); scale: Qt.vector3d(13.6, 0.72, 0.66); eulerRotation.z: 90 }
    component Prego: Model {
        geometry: Malha { pedido: "icosaedro" }
        scale: Qt.vector3d(7, 7, 4)
        materials: PrincipledMaterial { baseColor: "#5a5a64"; metalness: 1; roughness: 0.35 }
    }
    Repeater3D {   // chapas de ferro nos cantos da moldura (com 4 pregos)
        model: [Qt.point(-790, 478), Qt.point(790, 478), Qt.point(-790, -478), Qt.point(790, -478)]
        Node {
            position: Qt.vector3d(modelData.x, modelData.y, 46)
            Model {
                source: "#Cube"
                scale: Qt.vector3d(1.0, 0.9, 0.06)
                materials: PrincipledMaterial { baseColorMap: Texture { source: vista.tex("ferro_preto") }
                    metalness: 0.7; roughness: 0.5 }
            }
            Repeater3D {
                model: [Qt.point(-32, -28), Qt.point(32, -28), Qt.point(-32, 28), Qt.point(32, 28)]
                Prego { position: Qt.vector3d(modelData.x, modelData.y, 4) }
            }
        }
    }

    // ---------------------------------------------------------------- cartazes
    component Papel: Model {
        property string img: "cartaz_texto"
        property int semente: 1
        geometry: Malha { pedido: "folha|1|1|0|0.02|" + semente + "|plano" }
        eulerRotation.x: 90
        materials: PrincipledMaterial {
            baseColorMap: Texture { source: vista.tex(img) }
            alphaMode: PrincipledMaterial.Mask
            alphaCutoff: 0.5
            roughness: 0.9
            cullMode: Material.NoCulling
        }
    }
    readonly property var papeis: [
        {img: "cartaz_texto", x: -560, y: 300, w: 300, h: 220, r: -3},
        {img: "cartaz_texto", x: -575, y: 50, w: 300, h: 220, r: 2},
        {img: "cartaz_mapa", x: -545, y: -215, w: 380, h: 250, r: -1},
        {img: "cartaz_texto", x: 560, y: 245, w: 290, h: 270, r: 2},
        {img: "cartaz_texto", x: 575, y: -250, w: 270, h: 240, r: -2},
        {img: "bilhete", x: 405, y: 10, w: 120, h: 110, r: 8}
    ]
    Repeater3D {
        model: vista.papeis
        Node {
            id: cartazNo
            readonly property real w: modelData.w
            readonly property real h: modelData.h
            position: Qt.vector3d(modelData.x, modelData.y, 6)
            eulerRotation.z: modelData.r
            Papel { img: modelData.img; semente: index + 3; scale: Qt.vector3d(modelData.w, 20, modelData.h) }
            Repeater3D {
                model: modelData.img === "bilhete" ? [Qt.point(0, 0.38)] : [Qt.point(-0.44, 0.42), Qt.point(0.44, 0.42), Qt.point(-0.44, -0.42), Qt.point(0.44, -0.42)]
                Prego { position: Qt.vector3d(modelData.x * cartazNo.w, modelData.y * cartazNo.h, 6) }
            }
        }
    }
    Node {   // o cartaz GRANDE do meio
        position: Qt.vector3d(0, -38, 22)
        Papel { img: "cartaz_grande"; semente: 2; scale: Qt.vector3d(620, 30, 660) }
        Repeater3D {
            model: [Qt.point(-285, 305), Qt.point(285, 305), Qt.point(-285, -305), Qt.point(285, -305)]
            Prego { position: Qt.vector3d(modelData.x, modelData.y, 8); scale: Qt.vector3d(9, 9, 5) }
        }
    }
    component Selo: Node {
        Model {
            geometry: Malha { pedido: "torno|0,0; 22,0; 25,3; 22,7; 14,8; 0,8|0.18|10|plano" }
            eulerRotation.x: 90
            materials: PrincipledMaterial { baseColor: "#9a1a14"; roughness: 0.35; clearcoatAmount: 0.6 }
        }
        Repeater3D {   // fitinhas
            model: [-1, 1]
            Model {
                source: "#Cube"
                position: Qt.vector3d(modelData * 9, -30, -2)
                eulerRotation.z: modelData * 12
                scale: Qt.vector3d(0.12, 0.42, 0.02)
                materials: PrincipledMaterial { baseColor: "#7a1410"; roughness: 0.6 }
            }
        }
    }
    Selo { position: Qt.vector3d(-475, -10, 14) }
    Selo { position: Qt.vector3d(650, 150, 14) }

    // fios vermelhos ligando os cartazes
    component Fio: Node {
        property vector3d a
        property vector3d b
        readonly property real comp: Math.sqrt((b.x - a.x) * (b.x - a.x) + (b.y - a.y) * (b.y - a.y))
        position: Qt.vector3d((a.x + b.x) / 2, (a.y + b.y) / 2, 30)
        eulerRotation.z: Math.atan2(b.y - a.y, b.x - a.x) * 180 / Math.PI - 90
        Model {
            source: "#Cylinder"
            scale: Qt.vector3d(0.03, parent.comp / 100, 0.03)
            materials: PrincipledMaterial { baseColor: "#9a1a14"; roughness: 0.7 }
        }
    }
    readonly property var fios: [
        [-420, 250, -300, 180], [-430, 60, -300, -40], [-360, -200, -300, -230],
        [420, 220, 300, 160], [430, 20, 300, -10], [460, -10, 480, -140], [370, 40, 470, 200]
    ]
    Repeater3D {
        model: vista.fios
        Node {
            Fio { a: Qt.vector3d(modelData[0], modelData[1], 0); b: Qt.vector3d(modelData[2], modelData[3], 0) }
            Prego { position: Qt.vector3d(modelData[0], modelData[1], 32) }
            Prego { position: Qt.vector3d(modelData[2], modelData[3], 34) }
        }
    }

    // ---------------------------------------------------------------- estandarte e flâmulas (em cima)
    Model {   // vara
        source: "#Cylinder"
        position: Qt.vector3d(0, 520, 60)
        eulerRotation.z: 90
        scale: Qt.vector3d(0.09, 7, 0.09)
        materials: PrincipledMaterial { baseColor: "#3a2414"; roughness: 0.7 }
    }
    Repeater3D {
        model: [-1, 1]
        Model {
            geometry: Malha { pedido: "icosaedro" }
            position: Qt.vector3d(modelData * 355, 520, 60)
            scale: Qt.vector3d(12, 12, 12)
            materials: PrincipledMaterial { baseColor: "#b08a3a"; metalness: 1; roughness: 0.3 }
        }
    }
    Papel { img: "estandarte"; semente: 5; position: Qt.vector3d(0, 385, 64); scale: Qt.vector3d(340, 60, 280) }
    Repeater3D {
        model: [-1, 1]
        Papel { img: "flamula"; semente: 6 + index; position: Qt.vector3d(modelData * 245, 420, 58); scale: Qt.vector3d(64, 30, 200) }
    }

    // ---------------------------------------------------------------- embaixo: espadas cruzadas, cordas, brasões
    component Espada: Node {
        Model {   // lâmina
            geometry: Malha { pedido: "torno|0,-150; 1,-120; 1,110; 0,112|0|4|plano" }
            scale: Qt.vector3d(13, 1, 3)
            materials: PrincipledMaterial { baseColor: "#d0d4dc"; metalness: 0.85; roughness: 0.25 }
        }
        Model {
            source: "#Cube"
            position.y: 116
            scale: Qt.vector3d(0.9, 0.1, 0.16)
            materials: PrincipledMaterial { baseColor: "#8a6a3a"; metalness: 1; roughness: 0.35 }
        }
        Model {
            geometry: Malha { pedido: "torno|0,120; 7,120; 8,140; 7,170; 0,170|0|8|plano" }
            materials: PrincipledMaterial { baseColor: "#6a1a12"; roughness: 0.8 }
        }
        Model {
            geometry: Malha { pedido: "icosaedro" }
            position.y: 178
            scale: Qt.vector3d(11, 11, 11)
            materials: PrincipledMaterial { baseColor: "#9a7a44"; metalness: 1; roughness: 0.3 }
        }
    }
    Espada { position: Qt.vector3d(0, -470, 70); eulerRotation.z: 40 }
    Espada { position: Qt.vector3d(0, -470, 76); eulerRotation.z: -40 }
    Repeater3D {   // cordas caídas (meia argola achatada)
        model: [-1, 1]
        Model {
            geometry: Malha { pedido: "toro|1|0.06|0.5|16|6|plano" }
            position: Qt.vector3d(modelData * 265, -470, 60)
            eulerRotation.x: 90
            scale: Qt.vector3d(165, 165, 70)
            materials: PrincipledMaterial { baseColor: "#a08850"; roughness: 0.9 }
        }
    }
    Model {   // brasão do lobo (moeda de 8 lados de pé)
        geometry: Malha { pedido: "moeda|8" }
        position: Qt.vector3d(-430, -545, 64)
        eulerRotation: Qt.vector3d(90, 0, 0)
        scale: Qt.vector3d(52, 52, 52)
        materials: PrincipledMaterial { baseColorMap: Texture { source: vista.tex("brasao_lobo") }
            roughness: 0.6; metalness: 0.2; cullMode: Material.NoCulling }
    }
    Model {   // brasão da torre (escudo)
        source: "#Rectangle"
        position: Qt.vector3d(430, -560, 66)
        scale: Qt.vector3d(1.1, 1.1, 1)
        materials: PrincipledMaterial { baseColorMap: Texture { source: vista.tex("brasao_torre") }
            alphaMode: PrincipledMaterial.Mask; roughness: 0.6 }
    }
    Model {
        source: "#Rectangle"
        position: Qt.vector3d(434, -565, 60)
        scale: Qt.vector3d(1.1, 1.1, 1)
        materials: PrincipledMaterial { baseColorMap: Texture { source: vista.tex("brasao_torre") }
            baseColor: "#201008"; alphaMode: PrincipledMaterial.Mask; roughness: 0.8 }
    }

    // ---------------------------------------------------------------- hera (folhas 3D penduradas)
    Repeater3D {
        model: 46
        Model {
            readonly property bool esquerda: index < 26
            readonly property real t: esquerda ? index / 25 : (index - 26) / 19
            source: "#Rectangle"
            position: esquerda ? Qt.vector3d(-900 + t * 260 + Math.sin(t * 9) * 40 + (vista.acaso(index, 1) - 0.5) * 70,
                                             560 - t * 380 + (vista.acaso(index, 2) - 0.5) * 50, 40 + vista.acaso(index, 3) * 40)
                               : Qt.vector3d(880 + Math.sin(t * 7) * 30 + (vista.acaso(index, 1) - 0.5) * 60,
                                             -40 - t * 420 + (vista.acaso(index, 2) - 0.5) * 50, 40 + vista.acaso(index, 3) * 40)
            eulerRotation: Qt.vector3d((vista.acaso(index, 4) - 0.5) * 50, (vista.acaso(index, 5) - 0.5) * 50, (vista.acaso(index, 6) - 0.5) * 120)
            scale: Qt.vector3d(0.5 + vista.acaso(index, 7) * 0.35, 0.5 + vista.acaso(index, 7) * 0.35, 1)
            materials: PrincipledMaterial { baseColorMap: Texture { source: vista.tex("folha_hera") }
                baseColor: Qt.rgba(0.8 + vista.acaso(index, 8) * 0.4, 0.8 + vista.acaso(index, 8) * 0.4, 0.8, 1)
                alphaMode: PrincipledMaterial.Mask; roughness: 0.6; cullMode: Material.NoCulling }
        }
    }

    // ---------------------------------------------------------------- a LAMPARINA (presa na viga da direita)
    Node {
        position: Qt.vector3d(690, 330, 170)
        Model {   // braço de ferro saindo da viga
            source: "#Cube"
            position: Qt.vector3d(50, 130, -40)
            scale: Qt.vector3d(1.1, 0.1, 0.1)
            materials: PrincipledMaterial { baseColor: "#1e1e22"; metalness: 0.8; roughness: 0.5 }
        }
        Model {
            source: "#Cube"
            position: Qt.vector3d(100, 130, -120)
            scale: Qt.vector3d(0.1, 0.1, 1.7)
            materials: PrincipledMaterial { baseColor: "#1e1e22"; metalness: 0.8; roughness: 0.5 }
        }
        Model {   // argola
            geometry: Malha { pedido: "toro|12|3|1|10|5|plano" }
            position: Qt.vector3d(0, 112, -40)
            eulerRotation.x: 90
            materials: PrincipledMaterial { baseColor: "#1e1e22"; metalness: 0.8; roughness: 0.5 }
        }
        Model {   // tampa
            geometry: Malha { pedido: "torno|0,60; 46,60; 46,70; 18,96; 6,104; 0,104|0|6|plano" }
            position.z: -40
            materials: PrincipledMaterial { baseColor: "#24242a"; metalness: 0.7; roughness: 0.5 }
        }
        Model {   // vidro (aceso por dentro)
            geometry: Malha { pedido: "torno|36,-60; 38,-50; 38,60|0|6|plano" }
            position.z: -40
            materials: PrincipledMaterial {
                baseColor: "#ffd890"
                emissiveFactor: Qt.vector3d(0.9, 0.55, 0.2)
                opacity: 0.55
                alphaMode: PrincipledMaterial.Blend
                roughness: 0.1
                cullMode: Material.NoCulling
            }
        }
        Repeater3D {   // grade de ferro (6 barras)
            model: 6
            Model {
                source: "#Cube"
                position: Qt.vector3d(Math.cos(index * Math.PI / 3) * 39, 0, -40 + Math.sin(index * Math.PI / 3) * 39)
                scale: Qt.vector3d(0.07, 1.25, 0.07)
                materials: PrincipledMaterial { baseColor: "#1e1e22"; metalness: 0.8; roughness: 0.5 }
            }
        }
        Model {   // base
            geometry: Malha { pedido: "torno|0,-90; 10,-90; 30,-72; 46,-62; 46,-56; 0,-56|0|6|plano" }
            position.z: -40
            materials: PrincipledMaterial { baseColor: "#24242a"; metalness: 0.7; roughness: 0.5 }
        }
        ParticleSystem3D {   // a chama
            running: vista.anima
            position: Qt.vector3d(0, -40, -40)
            SpriteParticle3D {
                id: chama
                sprite: Texture { source: vista.tex("sprite_chama") }
                maxAmount: 120
                color: "#ff9a40"
                blendMode: SpriteParticle3D.Screen
                fadeInDuration: 60
                fadeOutDuration: 260
                billboard: true
            }
            ParticleEmitter3D {
                particle: chama
                emitRate: 80
                lifeSpan: 460
                particleScale: 7
                particleEndScale: 1.5
                particleScaleVariation: 1.5
                shape: ParticleShape3D { type: ParticleShape3D.Sphere; extents: Qt.vector3d(5, 2, 5) }
                velocity: VectorDirection3D { direction: Qt.vector3d(0, 70, 0); directionVariation: Qt.vector3d(8, 16, 8) }
            }
            SpriteParticle3D {
                id: brilho
                sprite: Texture { source: vista.tex("sprite_brilho") }
                maxAmount: 2
                color: "#ff9040"
                blendMode: SpriteParticle3D.Screen
                billboard: true
            }
            ParticleEmitter3D {
                particle: brilho
                emitRate: 3
                lifeSpan: 700
                particleScale: 60
                particleEndScale: 60
            }
        }
    }
}
