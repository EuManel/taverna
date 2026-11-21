// ⚙ Steampunk, tela 2 (v0.59, pedido do Manel): PONTE DE COMANDO DE UM DIRIGÍVEL. Janelão pras nuvens do fim
// de tarde, cidade de chaminés lá embaixo soltando fumaça, outros dirigíveis passando ao longe. O MENU É O
// TELÉGRAFO DE ORDENS (mostrador redondo com alavanca): cada fatia do mostrador é uma opção; no hover a alavanca
// vai até ela; no clique toca a campainha "plim-plim" (e aí escolhe).
import QtQuick
import QtQuick3D
import QtQuick3D.Particles3D

View3D {
    id: vista
    property int nivel: ponte.nivel
    readonly property bool anima: nivel >= 1
    function tex(n) { return ponte.textura(n) }
    camera: camera
    readonly property bool menuProprio: true
    readonly property bool tituloProprio: true
    property int sobre: -1
    property int tocou: -1

    property real tempo: 0
    NumberAnimation on tempo { from: 0; to: 1000; duration: 1000000; loops: Animation.Infinite; running: vista.anima }

    readonly property string fonte: "IM FELL English SC"
    // as 5 fatias do mostrador, da esquerda (180°) pra direita (0°)
    readonly property var opcoes: [
        {texto: "Nova\nsessão", acao: "mestre_nova"},
        {texto: "Continuar", acao: "mestre_continuar", ok: ponte.temUltima},
        {texto: "Abrir\nsessão", acao: "mestre_abrir"},
        {texto: "Entrar na\nsessão", acao: "jogador_entrar"},
        {texto: "Sair", acao: "sair"}
    ]
    readonly property vector3d centro: Qt.vector3d(0, 330, 640)   // o centro do mostrador
    readonly property real raio: 190
    function anguloDe(i) { return 180 - (i + 0.5) * 36 }        // meio da fatia, em graus

    environment: SceneEnvironment {
        backgroundMode: SceneEnvironment.Color
        clearColor: "#f0b070"
        antialiasingMode: SceneEnvironment.MSAA
        antialiasingQuality: vista.nivel === 2 ? SceneEnvironment.VeryHigh : SceneEnvironment.High
        tonemapMode: SceneEnvironment.TonemapModeNone
    }
    PerspectiveCamera {
        id: camera
        position: Qt.vector3d(0, 470, 1500)
        eulerRotation.x: -5
        fieldOfView: 52
        clipNear: 10
        clipFar: 30000
    }
    DirectionalLight { eulerRotation: Qt.vector3d(-15, -160, 0); color: "#ffc890"; brightness: 1.6 }   // o sol de fora
    PointLight { position: Qt.vector3d(0, 600, 600); color: "#ffd8a0"; brightness: 6; quadraticFade: 0.2 }   // lampião da cabine

    // ---------------------------------------------------------------- LÁ FORA: céu, nuvens, cidade, outros dirigíveis
    Model {
        source: "#Rectangle"; position: Qt.vector3d(0, 1200, -12000); scale: Qt.vector3d(420, 160, 1)
        materials: PrincipledMaterial { lighting: PrincipledMaterial.NoLighting; baseColorMap: Texture { source: vista.tex("ceu_nuvens"); positionU: vista.tempo * 0.0008 } }
    }
    Model {   // a cidade de chaminés lá embaixo
        source: "#Rectangle"; position: Qt.vector3d(0, -1600, -7000); scale: Qt.vector3d(220, 40, 1)
        materials: PrincipledMaterial {
            lighting: PrincipledMaterial.NoLighting
            alphaMode: PrincipledMaterial.Blend
            baseColorMap: Texture { source: vista.tex("cidade_chamines"); scaleU: 2; tilingModeHorizontal: Texture.Repeat; positionU: vista.tempo * 0.004 }
        }
    }
    ParticleSystem3D {   // fumaça das chaminés
        running: vista.anima
        position: Qt.vector3d(0, -1500, -6900)
        SpriteParticle3D {
            id: fumaca
            sprite: Texture { source: vista.tex("sprite_fumaca") }
            maxAmount: 120
            color: Qt.rgba(0.45, 0.38, 0.4, 0.25)
            fadeInDuration: 600; fadeOutDuration: 3000
            billboard: true
        }
        ParticleEmitter3D {
            particle: fumaca
            emitRate: 14
            lifeSpan: 7000
            particleScale: 60; particleEndScale: 260
            shape: ParticleShape3D { type: ParticleShape3D.Cube; extents: Qt.vector3d(9000, 10, 10) }
            velocity: VectorDirection3D { direction: Qt.vector3d(-120, 260, 0); directionVariation: Qt.vector3d(40, 60, 20) }
        }
    }
    Repeater3D {   // nuvens passando (perto e longe)
        model: 9
        Model {
            readonly property real dist: 2500 + (index % 3) * 1800
            readonly property real vel: 40 + (index % 4) * 15
            source: "#Rectangle"
            position: Qt.vector3d(((index * 1700 - vista.tempo * vel) % 9000 + 9000) % 9000 - 4500, -300 + (index * 397) % 900, -dist)
            scale: Qt.vector3d(14 + (index % 3) * 6, 5 + (index % 2) * 2, 1)
            materials: PrincipledMaterial {
                lighting: PrincipledMaterial.NoLighting
                alphaMode: PrincipledMaterial.Blend
                depthDrawMode: Material.NeverDepthDraw
                baseColorMap: Texture { source: vista.tex("nuvem") }
                opacity: 0.85
            }
        }
    }
    component Dirigivel: Node {
        id: dg
        property real vel: 30
        property real fase: 0
        property real largo: 9000
        Model { source: "#Sphere"; scale: Qt.vector3d(6, 1.7, 1.7)
            materials: PrincipledMaterial { baseColorMap: Texture { source: vista.tex("lona_dirigivel") }
                roughness: 0.8 } }
        Model { source: "#Cube"; position.y: -110; scale: Qt.vector3d(1.6, 0.4, 0.5); materials: PrincipledMaterial { baseColor: "#4a2e18"; roughness: 0.6 } }
        Repeater3D { model: [-1, 1]
            Model { source: "#Cube"; position: Qt.vector3d(-290, modelData * 60, 0); scale: Qt.vector3d(0.6, 0.05, 0.9)
                materials: PrincipledMaterial { baseColor: "#6a4a2a" } } }
        Node {   // hélice girando
            position.x: -330
            eulerRotation.x: vista.tempo * 600
            Model { source: "#Cube"; scale: Qt.vector3d(0.04, 1.2, 0.12); materials: PrincipledMaterial { baseColor: "#3a2a1a" } }
        }
    }
    Dirigivel { position: Qt.vector3d(((vista.tempo * 60) % 12000) - 6000, 600, -5200); scale: Qt.vector3d(1, 1, 1) }
    Dirigivel { position: Qt.vector3d(5000 - ((vista.tempo * 35 + 4000) % 12000), 1300, -8500); eulerRotation.y: 180; scale: Qt.vector3d(0.8, 0.8, 0.8) }

    // ---------------------------------------------------------------- A CABINE: moldura da janela e o painel
    component Latao: PrincipledMaterial { baseColorMap: Texture { source: vista.tex("latao") }
                metalness: 0.3; roughness: 0.38 }
    component Madeira: PrincipledMaterial { baseColorMap: Texture { source: vista.tex("madeira_oficina") }
                roughness: 0.6 }
    Latao { id: lataoMat }
    Madeira { id: madeiraMat }
    Repeater3D {   // os montantes da janela (latão), inclinados
        model: [-900, -460, 460, 900]
        Model { source: "#Cube"; position: Qt.vector3d(modelData, 700, -100); eulerRotation.z: modelData * 0.008
            scale: Qt.vector3d(0.3, 14, 0.3); materials: lataoMat }
    }
    Model { source: "#Cube"; position: Qt.vector3d(0, 1340, -100); scale: Qt.vector3d(22, 1.2, 0.8); materials: madeiraMat }   // viga de cima
    Model { source: "#Cube"; position: Qt.vector3d(0, 40, 0); scale: Qt.vector3d(24, 2.4, 3.4); materials: madeiraMat }
    Model { source: "#Rectangle"; eulerRotation.x: -90; position: Qt.vector3d(0, -80, 800); scale: Qt.vector3d(30, 18, 1); materials: madeiraMat }   // o assoalho da cabine
    PointLight { position: Qt.vector3d(0, 380, 1100); color: "#ffcf90"; brightness: 7; quadraticFade: 0.2 }        // o painel embaixo da janela
    Model { source: "#Cube"; position: Qt.vector3d(0, 160, -60); scale: Qt.vector3d(24, 0.12, 0.3); materials: lataoMat }      // friso
    Repeater3D {   // relógios/instrumentos no painel
        model: [-700, -520, 520, 700]
        Node {
            position: Qt.vector3d(modelData, 90, 172)
            Model { source: "#Cylinder"; eulerRotation.x: 90; scale: Qt.vector3d(0.8, 0.1, 0.8); materials: lataoMat }
            Model { source: "#Rectangle"; position.z: 6; scale: Qt.vector3d(1.4, 1.4, 1)
                materials: PrincipledMaterial { lighting: PrincipledMaterial.NoLighting; alphaMode: PrincipledMaterial.Mask
                    baseColorMap: Texture { source: vista.tex("mostrador") } } }
            Node { position.z: 8; eulerRotation.z: 60 * Math.sin(vista.tempo * (0.4 + Math.abs(modelData) * 0.0004) + modelData)
                Model { source: "#Cube"; position.y: 24; scale: Qt.vector3d(0.03, 0.5, 0.01); materials: PrincipledMaterial { baseColor: "#1a0e06" } } }
        }
    }
    Node {   // o TIMÃO (roda do leme) à direita
        position: Qt.vector3d(760, 330, 180)
        eulerRotation: Qt.vector3d(-10, -20, 12 * Math.sin(vista.tempo * 0.3))
        Model { geometry: Malha { pedido: "toro|1|0.06|1|40|8" }
                eulerRotation.x: 90; scale: Qt.vector3d(140, 140, 140); materials: madeiraMat }
        Repeater3D { model: 8
            Model { source: "#Cylinder"; eulerRotation.z: index * 22.5; scale: Qt.vector3d(0.08, 3.5, 0.08); materials: madeiraMat } }
        Model { source: "#Cylinder"; eulerRotation.x: 90; scale: Qt.vector3d(0.4, 0.3, 0.4); materials: lataoMat }
    }

    // ---------------------------------------------------------------- O TELÉGRAFO DE ORDENS (o menu)
    Node {
        id: telegrafo
        position: vista.centro
        Model { source: "#Cylinder"; position: Qt.vector3d(0, -260, -70); scale: Qt.vector3d(0.9, 3.0, 0.9); materials: lataoMat }   // coluna
        Model { source: "#Cylinder"; eulerRotation.x: 90; position.z: -18; scale: Qt.vector3d(4.3, 0.3, 4.3); materials: lataoMat }   // o aro
        Model {   // o mostrador (pickable: o ângulo do clique diz a fatia)
            id: mostrador
            property int opcao: -2
            pickable: true
            source: "#Rectangle"
            scale: Qt.vector3d(4.0, 4.0, 1)
            materials: PrincipledMaterial {
                lighting: PrincipledMaterial.NoLighting
                alphaMode: PrincipledMaterial.Mask
                baseColorMap: Texture { source: vista.tex("telegrafo") }
            }
        }
        Repeater3D {   // os nomes das fatias + o destaque da fatia do mouse
            model: vista.opcoes
            Node {
                id: fatia
                readonly property real a: vista.anguloDe(index) * Math.PI / 180
                readonly property bool acesa: vista.sobre === index
                readonly property bool habilitado: modelData.ok === undefined || modelData.ok
                position: Qt.vector3d(Math.cos(a) * vista.raio * 0.66, Math.sin(a) * vista.raio * 0.66, 3)
                Model {
                    source: "#Rectangle"
                    scale: Qt.vector3d(1.1, 0.7, 1)
                    materials: PrincipledMaterial {
                        lighting: PrincipledMaterial.NoLighting
                        alphaMode: PrincipledMaterial.Blend
                        baseColorMap: Texture {
                            sourceItem: Item {
                                width: 220; height: 140
                                Rectangle {   // o brilho da fatia escolhida
                                    anchors.fill: parent; radius: 20
                                    color: fatia.acesa ? "#55e8a020" : "transparent"
                                }
                                Text {
                                    anchors.centerIn: parent
                                    text: modelData.texto
                                    horizontalAlignment: Text.AlignHCenter
                                    lineHeight: 0.85
                                    font.family: vista.fonte; font.pixelSize: 38; font.bold: true
                                    color: !fatia.habilitado ? "#9a8a6a" : (fatia.acesa ? "#8a1408" : "#2a1806")
                                }
                            }
                        }
                    }
                }
            }
        }
        Repeater3D {   // MESTRE / JOGADOR em cima das fatias
            model: [{t: "MESTRE", a: 126}, {t: "JOGADOR", a: 36}]
            Model {
                source: "#Rectangle"
                readonly property real r: modelData.a * Math.PI / 180
                position: Qt.vector3d(Math.cos(r) * vista.raio * 1.13, Math.sin(r) * vista.raio * 1.13, 4)
                eulerRotation.z: modelData.a - 90
                scale: Qt.vector3d(1.3, 0.3, 1)
                materials: PrincipledMaterial {
                    lighting: PrincipledMaterial.NoLighting
                    alphaMode: PrincipledMaterial.Blend
                    baseColorMap: Texture { sourceItem: Text { width: 260; height: 60; horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter; text: modelData.t; font.family: vista.fonte; font.pixelSize: 40
                        font.letterSpacing: 8; color: "#f4e0a8"; style: Text.Outline; styleColor: "#3a2008" } }
                }
            }
        }
        Node {   // a ALAVANCA: vai até a fatia do mouse (mola)
            id: alavanca
            property real alvo: vista.sobre >= 0 ? vista.anguloDe(vista.sobre) : 90
            eulerRotation.z: alavanca.alvo - 90
            Behavior on eulerRotation.z { SpringAnimation { spring: 2.5; damping: 0.22 } }
            position.z: 14
            Model { source: "#Cube"; position.y: vista.raio * 0.45; scale: Qt.vector3d(0.12, vista.raio * 0.009, 0.06); materials: lataoMat }
            Model { source: "#Cube"; position.y: vista.raio * 0.9; scale: Qt.vector3d(0.34, 0.16, 0.12)
                materials: PrincipledMaterial { baseColor: "#6a1a10"; roughness: 0.4 } }   // a ponta (seta)
            Model { source: "#Cylinder"; position: Qt.vector3d(0, vista.raio * 1.15, 30); eulerRotation.x: 90; scale: Qt.vector3d(0.14, 0.7, 0.14)
                materials: PrincipledMaterial { baseColor: "#2a1a0e"; roughness: 0.5 } }   // o punho
        }
        Model { source: "#Cylinder"; eulerRotation.x: 90; position.z: 20; scale: Qt.vector3d(0.4, 0.12, 0.4); materials: lataoMat }   // o eixo
        Node {   // a CAMPAINHA: treme quando toca
            position: Qt.vector3d(-vista.raio * 1.2, vista.raio * 0.95, -10)
            eulerRotation.z: sino.running ? 18 * Math.sin(vista.tempo * 120) : 0
            Model { source: "#Sphere"; scale: Qt.vector3d(0.6, 0.5, 0.6); materials: lataoMat }
            NumberAnimation { id: sino; duration: 600 }
        }
    }
    // a PLACA DO TÍTULO em cima do telégrafo
    Node {
        position: Qt.vector3d(0, 700, 120)
        Model { source: "#Cube"; scale: Qt.vector3d(5.2, 1.0, 0.1); materials: lataoMat }
        Model {
            source: "#Rectangle"; position.z: 6; scale: Qt.vector3d(5.0, 0.95, 1)
            materials: PrincipledMaterial {
                alphaMode: PrincipledMaterial.Blend
                roughness: 0.5
                baseColorMap: Texture { sourceItem: Item { width: 1000; height: 190
                    Text { anchors.centerIn: parent; text: "TAVERNA"; font.family: vista.fonte; font.pixelSize: 150
                        font.letterSpacing: 18; color: "#2a1806"; style: Text.Raised; styleColor: "#f8e0a0" } } }
            }
        }
    }

    // ---------------------------------------------------------------- mouse: o ângulo no mostrador diz a fatia
    Timer { id: escolhe; interval: 700; property string acao: ""; onTriggered: ponte.escolher(acao) }
    MouseArea {
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: vista.sobre >= 0 ? Qt.PointingHandCursor : Qt.ArrowCursor
        function qual(x, y) {
            var r = vista.pick(x, y)
            if (!r.objectHit || r.objectHit.opcao !== -2) return -1
            var p = r.scenePosition
            var dx = p.x - vista.centro.x, dy = p.y - vista.centro.y
            var dist = Math.sqrt(dx * dx + dy * dy)
            if (dy < 0 || dist < vista.raio * 0.25 || dist > vista.raio * 1.05) return -1
            var ang = Math.atan2(dy, dx) * 180 / Math.PI
            var i = Math.min(4, Math.max(0, Math.floor((180 - ang) / 36)))
            if (vista.opcoes[i].ok !== undefined && !vista.opcoes[i].ok) return -1
            return i
        }
        onPositionChanged: (m) => vista.sobre = qual(m.x, m.y)
        onExited: vista.sobre = -1
        onClicked: (m) => {
            var i = qual(m.x, m.y)
            if (i >= 0 && !escolhe.running) {
                ponte.plim()          // "plim-plim"
                sino.restart()
                escolhe.acao = vista.opcoes[i].acao
                escolhe.start()
            }
        }
    }
}
