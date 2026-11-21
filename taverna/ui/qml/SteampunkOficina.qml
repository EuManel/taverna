// ⚙ Steampunk, tela 1 (v0.59, pedido do Manel): OFICINA DO INVENTOR. Engrenagens girando na parede, canos de
// cobre, vapor escapando, autômato pela metade na bancada, luz de lampião a gás. AS OPÇÕES SÃO PLAQUINHAS DE
// LATÃO num painel de controle, cada uma com um mostrador: no hover o ponteiro sobe e a válvula solta vapor;
// no clique a alavanca desce (e aí escolhe).
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
    property int puxada: -1          // a alavanca que desceu (clique)

    property real tempo: 0
    NumberAnimation on tempo { from: 0; to: 1000; duration: 1000000; loops: Animation.Infinite; running: vista.anima }

    readonly property string fonte: "IM FELL English SC"
    readonly property real painelZ: -180
    readonly property var opcoes: [
        {rotulo: "MESTRE", y: 545},
        {texto: "Nova sessão", acao: "mestre_nova", y: 480},
        {texto: "Continuar sessão", acao: "mestre_continuar", y: 400, det: ponte.temUltima ? ponte.ultimaAventura : "", ok: ponte.temUltima},
        {texto: "Abrir sessão…", acao: "mestre_abrir", y: 320},
        {rotulo: "JOGADOR", y: 255},
        {texto: "Entrar na sessão", acao: "jogador_entrar", y: 190, det: ponte.servidor !== "" ? "da última vez: " + ponte.servidor : ""},
        {texto: "Sair", acao: "sair", y: 110}
    ]

    environment: SceneEnvironment {
        backgroundMode: SceneEnvironment.Color
        clearColor: "#0e0906"
        antialiasingMode: SceneEnvironment.MSAA
        antialiasingQuality: vista.nivel === 2 ? SceneEnvironment.VeryHigh : SceneEnvironment.High
        tonemapMode: SceneEnvironment.TonemapModeNone
    }
    PerspectiveCamera {
        id: camera
        position: Qt.vector3d(0, 380, 1180)
        eulerRotation.x: -2
        fieldOfView: 50
        clipNear: 10
        clipFar: 8000
    }
    DirectionalLight { eulerRotation: Qt.vector3d(-30, 15, 0); color: "#ffd8a8"; brightness: 1.6 }
    // o LAMPIÃO A GÁS (tremula de leve)
    readonly property real chama: 1 + 0.08 * Math.sin(tempo * 13) + 0.05 * Math.sin(tempo * 29 + 1)
    PointLight { position: Qt.vector3d(-520, 620, 0); color: "#ffb860"; brightness: 9 * vista.chama; quadraticFade: 0.35 }
    PointLight { position: Qt.vector3d(0, 420, 250); color: "#ffcf90"; brightness: 9; quadraticFade: 0.25 }

    // ---------------------------------------------------------------- a parede e o chão
    Model {
        source: "#Rectangle"; position: Qt.vector3d(0, 500, -300); scale: Qt.vector3d(30, 14, 1)
        materials: PrincipledMaterial {
            baseColorMap: Texture { source: vista.tex("parede_oficina"); scaleU: 3; scaleV: 1.4; tilingModeHorizontal: Texture.Repeat; tilingModeVertical: Texture.Repeat }
            roughness: 0.7
        }
    }
    Model {
        source: "#Rectangle"; eulerRotation.x: -90; position: Qt.vector3d(0, -40, 200); scale: Qt.vector3d(30, 14, 1)
        materials: PrincipledMaterial {
            baseColorMap: Texture { source: vista.tex("madeira_oficina"); scaleU: 6; scaleV: 3; tilingModeHorizontal: Texture.Repeat; tilingModeVertical: Texture.Repeat }
            roughness: 0.6
        }
    }
    component Latao: PrincipledMaterial {
        baseColorMap: Texture { source: vista.tex("latao") }
        metalness: 0.3; roughness: 0.38
    }
    component Cobre: PrincipledMaterial {
        baseColorMap: Texture { source: vista.tex("cobre") }
        metalness: 0.3; roughness: 0.4
    }

    // ---------------------------------------------------------------- ENGRENAGENS girando na parede
    component Engrenagem: Node {
        id: eng
        property real raio: 100
        property int dentes: 14
        property real vel: 20
        property bool cobre: false
        eulerRotation.z: vista.tempo * eng.vel
        Model {   // o disco
            source: "#Cylinder"; eulerRotation.x: 90
            scale: Qt.vector3d(eng.raio / 50, 0.18, eng.raio / 50)
            materials: eng.cobre ? cobreMat : lataoMat
        }
        Repeater3D {   // os dentes
            model: eng.dentes
            Model {
                source: "#Cube"
                readonly property real a: index * 2 * Math.PI / eng.dentes
                position: Qt.vector3d(Math.cos(a) * eng.raio * 1.04, Math.sin(a) * eng.raio * 1.04, 0)
                eulerRotation.z: a * 180 / Math.PI
                scale: Qt.vector3d(eng.raio * 0.0026 + 0.1, eng.raio * 0.0035 + 0.12, 0.16)
                materials: eng.cobre ? cobreMat : lataoMat
            }
        }
        Model {   // o eixo
            source: "#Cylinder"; eulerRotation.x: 90; position.z: 12
            scale: Qt.vector3d(eng.raio / 250, 0.3, eng.raio / 250)
            materials: PrincipledMaterial { baseColor: "#2a2420"; metalness: 0.8; roughness: 0.4 }
        }
        Repeater3D {   // furos (raios do disco)
            model: 5
            Model {
                source: "#Cylinder"; eulerRotation.x: 90
                readonly property real a: index * 2 * Math.PI / 5
                position: Qt.vector3d(Math.cos(a) * eng.raio * 0.58, Math.sin(a) * eng.raio * 0.58, 10)
                scale: Qt.vector3d(eng.raio / 520, 0.02, eng.raio / 520)
                materials: PrincipledMaterial { baseColor: "#140c06"; roughness: 0.9 }
            }
        }
    }
    Latao { id: lataoMat }
    Cobre { id: cobreMat }
    Engrenagem { position: Qt.vector3d(-600, 640, -280); raio: 150; dentes: 20; vel: 12 }
    Engrenagem { position: Qt.vector3d(-420, 760, -276); raio: 80; dentes: 12; vel: -22.5; cobre: true }
    Engrenagem { position: Qt.vector3d(600, 700, -280); raio: 130; dentes: 18; vel: -14 }
    Engrenagem { position: Qt.vector3d(470, 520, -276); raio: 70; dentes: 10; vel: 25; cobre: true }
    Engrenagem { position: Qt.vector3d(720, 420, -282); raio: 95; dentes: 14; vel: -18 }

    // ---------------------------------------------------------------- CANOS de cobre (com cotovelo e válvula)
    Repeater3D {
        model: [{x: -700, y: 300, z: -250, l: 6, h: true}, {x: 700, y: 250, z: -250, l: 6, h: true},
                {x: -380, y: 450, z: -250, l: 7, h: false}, {x: 380, y: 860, z: -250, l: 4, h: false},
                {x: 0, y: 900, z: -240, l: 12, h: true}]
        Model {
            source: "#Cylinder"
            position: Qt.vector3d(modelData.x, modelData.y, modelData.z)
            eulerRotation.z: modelData.h ? 90 : 0
            scale: Qt.vector3d(0.28, modelData.l, 0.28)
            materials: cobreMat
        }
    }
    Repeater3D {   // anéis/braçadeiras nos canos
        model: [{x: -560, y: 300}, {x: -840, y: 300}, {x: 560, y: 250}, {x: 840, y: 250}, {x: -300, y: 900}, {x: 300, y: 900}]
        Model {
            source: "#Cylinder"; position: Qt.vector3d(modelData.x, modelData.y, -250); eulerRotation.z: 90
            scale: Qt.vector3d(0.36, 0.12, 0.36)
            materials: lataoMat
        }
    }

    // ---------------------------------------------------------------- o LAMPIÃO a gás na parede
    Node {
        position: Qt.vector3d(-520, 600, -270)
        Model { source: "#Cube"; position: Qt.vector3d(0, 0, 20); scale: Qt.vector3d(0.12, 0.12, 0.5); materials: lataoMat }
        Model { source: "#Cylinder"; position: Qt.vector3d(0, -30, 50); scale: Qt.vector3d(0.3, 0.2, 0.3); materials: lataoMat }
        Model {   // o vidro com a chama
            source: "#Sphere"; position: Qt.vector3d(0, 10, 50); scale: Qt.vector3d(0.6, 0.8, 0.6)
            materials: PrincipledMaterial { lighting: PrincipledMaterial.NoLighting; baseColor: Qt.rgba(1, 0.75 * vista.chama, 0.4, 1); opacity: 0.9 }
        }
        Model { source: "#Cone"; position: Qt.vector3d(0, 55, 50); scale: Qt.vector3d(0.5, 0.3, 0.5); materials: lataoMat }
    }

    // ---------------------------------------------------------------- O PAINEL DE CONTROLE (o menu)
    Model {   // a chapa de fundo do painel (madeira escura com moldura de latão)
        source: "#Cube"; position: Qt.vector3d(0, 380, vista.painelZ - 20); scale: Qt.vector3d(8.4, 6.6, 0.3)
        materials: PrincipledMaterial {
            baseColorMap: Texture { source: vista.tex("madeira_oficina") }
            roughness: 0.6
        }
    }
    Repeater3D {   // moldura de latão
        model: [{x: 0, y: 712, sx: 8.6, sy: 0.14}, {x: 0, y: 48, sx: 8.6, sy: 0.14}, {x: -421, y: 380, sx: 0.14, sy: 6.8}, {x: 421, y: 380, sx: 0.14, sy: 6.8}]
        Model {
            source: "#Cube"; position: Qt.vector3d(modelData.x, modelData.y, vista.painelZ - 2)
            scale: Qt.vector3d(modelData.sx, modelData.sy, 0.12)
            materials: lataoMat
        }
    }
    // a PLACA DO TÍTULO
    Node {
        position: Qt.vector3d(0, 640, vista.painelZ)
        Model { source: "#Cube"; scale: Qt.vector3d(5.6, 1.0, 0.08); materials: lataoMat }
        Repeater3D {   // rebites
            model: 4
            Model {
                source: "#Sphere"
                position: Qt.vector3d(index % 2 ? 265 : -265, index < 2 ? 36 : -36, 4)
                scale: Qt.vector3d(0.08, 0.08, 0.05)
                materials: lataoMat
            }
        }
        Model {
            source: "#Rectangle"; position.z: 5; scale: Qt.vector3d(5.4, 0.95, 1)
            materials: PrincipledMaterial {
                alphaMode: PrincipledMaterial.Blend
                metalness: 0.4; roughness: 0.5
                baseColorMap: Texture {
                    sourceItem: Item {
                        width: 1080; height: 190
                        Text {
                            anchors.centerIn: parent
                            text: "TAVERNA"
                            font.family: vista.fonte; font.pixelSize: 150; font.letterSpacing: 18
                            color: "#2a1806"
                            style: Text.Raised; styleColor: "#f8e0a0"   // gravado no latão
                        }
                    }
                }
            }
        }
    }
    component Plaquinha: Node {
        id: pq
        property var d
        property int i: 0
        readonly property bool ehBotao: d.texto !== undefined
        readonly property bool habilitado: d.ok === undefined || d.ok
        readonly property bool acesa: vista.sobre === i && habilitado
        property real pressao: acesa ? 1 : 0          // o ponteiro do mostrador
        Behavior on pressao { SpringAnimation { spring: 3; damping: 0.18 } }
        readonly property real largura: pq.ehBotao ? 420 : 220
        position: Qt.vector3d(pq.ehBotao ? -40 : -140, d.y, vista.painelZ)
        Model {   // a plaquinha de latão (pickable)
            property int opcao: pq.i
            pickable: pq.ehBotao
            source: "#Cube"
            scale: Qt.vector3d(pq.largura / 100, pq.ehBotao ? 0.6 : 0.38, 0.06)
            materials: PrincipledMaterial {
                baseColorMap: Texture { source: vista.tex("latao") }
                baseColor: pq.acesa ? "#ffffff" : (pq.habilitado ? "#b8a888" : "#5a5040")
                emissiveFactor: pq.acesa ? Qt.vector3d(0.3, 0.22, 0.08) : (pq.habilitado ? Qt.vector3d(0.16, 0.12, 0.05) : Qt.vector3d(0.05, 0.04, 0.02))
                metalness: 0.3; roughness: 0.35
            }
        }
        Model {   // o texto gravado
            source: "#Rectangle"; position.z: 4
            scale: Qt.vector3d(pq.largura / 100, pq.ehBotao ? 0.6 : 0.38, 1)
            materials: PrincipledMaterial {
                alphaMode: PrincipledMaterial.Blend
                roughness: 0.6
                baseColorMap: Texture {
                    sourceItem: Item {
                        width: pq.largura * 2; height: pq.ehBotao ? 120 : 76
                        Text {
                            anchors.centerIn: parent
                            anchors.verticalCenterOffset: pq.d.det ? -10 : 0
                            text: pq.d.texto || pq.d.rotulo
                            font.family: vista.fonte; font.pixelSize: pq.ehBotao ? 64 : 44
                            font.letterSpacing: pq.ehBotao ? 2 : 10
                            color: "#2a1806"; style: Text.Raised; styleColor: "#f8e0a0"
                        }
                        Text {
                            visible: !!pq.d.det
                            anchors.horizontalCenter: parent.horizontalCenter; anchors.bottom: parent.bottom; anchors.bottomMargin: 6
                            text: pq.d.det || ""; font.pixelSize: 20; color: "#3a2410"
                        }
                    }
                }
            }
        }
        Node {   // o MOSTRADOR à esquerda da plaquinha
            visible: pq.ehBotao
            position: Qt.vector3d(-pq.largura / 2 - 50, 0, 6)
            Model { source: "#Cylinder"; eulerRotation.x: 90; position.z: -4; scale: Qt.vector3d(0.44, 0.08, 0.44); materials: lataoMat }
            Model {
                source: "#Rectangle"; position.z: 1; scale: Qt.vector3d(0.78, 0.78, 1)
                materials: PrincipledMaterial {
                    lighting: PrincipledMaterial.NoLighting
                    alphaMode: PrincipledMaterial.Mask
                    baseColorMap: Texture { source: vista.tex("mostrador") }
                    baseColor: "#e8dcc0"
                }
            }
            Node {   // o ponteiro: parado no começo da escala; no hover sobe até o vermelho
                position.z: 3
                eulerRotation.z: 135 - pq.pressao * 220 + (pq.acesa ? Math.sin(vista.tempo * 23) * 3 : 0)
                Model { source: "#Cube"; position.y: 14; scale: Qt.vector3d(0.03, 0.3, 0.01); materials: PrincipledMaterial { baseColor: "#1a0e06"; metalness: 0.5 } }
                Model { source: "#Cylinder"; eulerRotation.x: 90; scale: Qt.vector3d(0.07, 0.03, 0.07); materials: lataoMat }
            }
        }
        Node {   // a ALAVANCA à direita: desce quando clica
            visible: pq.ehBotao
            position: Qt.vector3d(pq.largura / 2 + 40, 0, 10)
            Model { source: "#Cylinder"; eulerRotation.x: 90; scale: Qt.vector3d(0.22, 0.12, 0.22); materials: lataoMat }
            Node {
                eulerRotation.z: vista.puxada === pq.i ? -150 : -20
                Behavior on eulerRotation.z { NumberAnimation { duration: 260; easing.type: Easing.OutBack } }
                Model { source: "#Cylinder"; position.y: 34; scale: Qt.vector3d(0.06, 0.6, 0.06); materials: PrincipledMaterial { baseColor: "#2a2420"; metalness: 0.8; roughness: 0.4 } }
                Model { source: "#Sphere"; position.y: 70; scale: Qt.vector3d(0.2, 0.2, 0.2); materials: PrincipledMaterial { baseColor: "#5a0e0a"; roughness: 0.3 } }
            }
        }
        Node {   // a VÁLVULA em cima: solta vapor no hover
            visible: pq.ehBotao
            position: Qt.vector3d(pq.largura / 2 - 30, 34, 14)
            Model { source: "#Cylinder"; scale: Qt.vector3d(0.08, 0.2, 0.08); materials: cobreMat }
            Model { source: "#Cylinder"; position.y: 12; scale: Qt.vector3d(0.2, 0.03, 0.2); materials: PrincipledMaterial { baseColor: "#8a1a10"; roughness: 0.4 } }
            ParticleSystem3D {
                running: vista.anima && pq.ehBotao
                position.y: 16
                SpriteParticle3D {
                    id: vaporPq
                    sprite: Texture { source: vista.tex("sprite_fumaca") }
                    maxAmount: 40
                    color: Qt.rgba(0.95, 0.93, 0.9, 0.35)
                    fadeInDuration: 80; fadeOutDuration: 700
                    billboard: true
                }
                ParticleEmitter3D {
                    particle: vaporPq
                    emitRate: pq.acesa ? 34 : 0
                    lifeSpan: 900
                    particleScale: 1.5; particleEndScale: 7
                    velocity: VectorDirection3D { direction: Qt.vector3d(30, 160, 20); directionVariation: Qt.vector3d(30, 30, 20) }
                }
            }
        }
    }
    Repeater3D { model: vista.opcoes; Plaquinha { d: modelData; i: index } }

    // ---------------------------------------------------------------- a BANCADA com o AUTÔMATO pela metade
    Node {
        position: Qt.vector3d(560, 0, 160)
        Model { source: "#Cube"; position.y: 80; scale: Qt.vector3d(4.2, 0.24, 2.4)
            materials: PrincipledMaterial {
                baseColorMap: Texture { source: vista.tex("madeira_oficina") }
                roughness: 0.6
            } }
        Repeater3D { model: [-1, 1]
            Model { source: "#Cube"; position: Qt.vector3d(modelData * 190, 0, 0); scale: Qt.vector3d(0.2, 1.6, 2.2)
                materials: PrincipledMaterial { baseColor: "#2a1a0e"; roughness: 0.7 } } }
        Node {   // o autômato (tronco, cabeça, um braço, engrenagens à mostra)
            position: Qt.vector3d(-40, 92, -20)
            eulerRotation.y: -25
            Model { source: "#Cylinder"; position.y: 70; scale: Qt.vector3d(0.9, 1.4, 0.7); materials: lataoMat }
            Model { source: "#Cylinder"; position.y: 140; scale: Qt.vector3d(0.3, 0.3, 0.3); materials: cobreMat }
            Node {   // cabeça meio inclinada, com olhos de lente
                position.y: 195
                eulerRotation.z: 12 + 3 * Math.sin(vista.tempo * 0.7)
                Model { source: "#Sphere"; scale: Qt.vector3d(0.9, 0.85, 0.85); materials: lataoMat }
                Repeater3D { model: [-1, 1]
                    Model { source: "#Cylinder"; eulerRotation.x: 90; position: Qt.vector3d(modelData * 16, 4, 38); scale: Qt.vector3d(0.12, 0.1, 0.12)
                        materials: PrincipledMaterial { lighting: PrincipledMaterial.NoLighting
                            baseColor: Math.sin(vista.tempo * 0.9) > 0.95 ? "#ffd070" : "#ff9a30" } } }
            }
            Model { source: "#Cylinder"; position: Qt.vector3d(60, 110, 0); eulerRotation.z: 50; scale: Qt.vector3d(0.16, 1.1, 0.16); materials: cobreMat }   // braço
            Engrenagem { position: Qt.vector3d(0, 80, 36); raio: 22; dentes: 8; vel: 40; scale: Qt.vector3d(1, 1, 0.5) }   // peito aberto
        }
        Repeater3D {   // ferramentas e peças soltas
            model: [{x: 120, z: 40, r: 30}, {x: 150, z: -40, r: 70}, {x: -150, z: 60, r: -20}]
            Model { source: "#Cube"; position: Qt.vector3d(modelData.x, 96, modelData.z); eulerRotation.y: modelData.r
                scale: Qt.vector3d(0.8, 0.06, 0.12); materials: PrincipledMaterial { baseColor: "#4a4440"; metalness: 0.8; roughness: 0.4 } }
        }
    }

    // ---------------------------------------------------------------- vapor escapando de um cano
    ParticleSystem3D {
        running: vista.anima
        position: Qt.vector3d(-380, 820, -230)
        SpriteParticle3D {
            id: vapor
            sprite: Texture { source: vista.tex("sprite_fumaca") }
            maxAmount: 60
            color: Qt.rgba(0.95, 0.92, 0.88, 0.18)
            fadeInDuration: 200; fadeOutDuration: 1400
            billboard: true
        }
        ParticleEmitter3D {
            particle: vapor
            emitRate: 12
            lifeSpan: 2600
            particleScale: 4; particleEndScale: 20
            velocity: VectorDirection3D { direction: Qt.vector3d(60, 70, 30); directionVariation: Qt.vector3d(20, 20, 20) }
        }
    }

    // ---------------------------------------------------------------- mouse
    Timer { id: escolhe; interval: 380; property string acao: ""; onTriggered: { ponte.escolher(acao); vista.puxada = -1 } }
    MouseArea {
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: vista.sobre >= 0 ? Qt.PointingHandCursor : Qt.ArrowCursor
        function qual(x, y) {
            var r = vista.pick(x, y)
            var i = r.objectHit && r.objectHit.opcao !== undefined ? r.objectHit.opcao : -1
            if (i >= 0 && vista.opcoes[i].ok !== undefined && !vista.opcoes[i].ok) return -1
            return i
        }
        onPositionChanged: (m) => vista.sobre = qual(m.x, m.y)
        onExited: vista.sobre = -1
        onClicked: (m) => {
            var i = qual(m.x, m.y)
            if (i >= 0 && vista.opcoes[i].acao && !escolhe.running) {
                vista.puxada = i            // a alavanca desce e aí escolhe
                escolhe.acao = vista.opcoes[i].acao
                escolhe.start()
            }
        }
    }
}
