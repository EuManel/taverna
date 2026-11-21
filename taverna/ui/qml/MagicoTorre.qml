// 🏰 Mágico, tela 2 (v0.57, referência do Manel): céu roxo de noite com lua, redemoinho de galáxia e um mar de
// nuvens com o pôr do sol no horizonte. À direita, a TORRE DE MAGO numa ilha flutuante: janelas roxas acesas,
// torrinhas, arcos, estrela brilhando no topo e ANÉIS DE RUNAS girando em volta. Ilhotas com cristais
// flutuando e cristais grandes nos cantos. O menu fica no céu livre (meio).
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

    property real tempo: 0
    NumberAnimation on tempo { from: 0; to: 1000; duration: 1000000; loops: Animation.Infinite; running: vista.anima }

    environment: SceneEnvironment {
        backgroundMode: SceneEnvironment.Color
        clearColor: "#140a3a"
        antialiasingMode: SceneEnvironment.MSAA
        antialiasingQuality: vista.nivel === 2 ? SceneEnvironment.VeryHigh : SceneEnvironment.High
        tonemapMode: SceneEnvironment.TonemapModeNone   // (o filmic deixava o texto dos cristais cinza)
    }
    PerspectiveCamera {
        id: camera
        position: Qt.vector3d(0, 150, 1700)
        eulerRotation.x: 3
        fieldOfView: 44
        clipNear: 50
        clipFar: 20000
    }

    // ---------------------------------------------------------------- luzes
    DirectionalLight {   // luar lilás
        eulerRotation: Qt.vector3d(-25, -50, 0)
        color: "#c8b8ff"
        brightness: 2.5
        castsShadow: true
        shadowFactor: 50
    }
    DirectionalLight {   // o resto do pôr do sol, de baixo/longe
        eulerRotation: Qt.vector3d(15, 170, 0)
        color: "#ff9060"
        brightness: 0.5
    }

    // ---------------------------------------------------------------- céu, lua, nuvens
    Model {
        source: "#Rectangle"
        position: Qt.vector3d(0, 1700, -9000)
        scale: Qt.vector3d(200, 112, 1)
        materials: PrincipledMaterial { lighting: PrincipledMaterial.NoLighting
            baseColorMap: Texture { source: vista.tex("ceu_magico") }
            baseColor: Qt.rgba(1.6, 1.55, 1.6, 1) }
    }
    Model {   // lua
        source: "#Rectangle"
        position: Qt.vector3d(-3800, 3500, -8800)
        scale: Qt.vector3d(12, 12, 1)
        materials: PrincipledMaterial { lighting: PrincipledMaterial.NoLighting
            baseColorMap: Texture { source: vista.tex("lua_magica") }
            alphaMode: PrincipledMaterial.Blend }
    }
    // nuvens: as do céu (passando) e o MAR de nuvens embaixo (várias camadas)
    readonly property var nuvens: [
        {x: -2600, y: 3000, z: -8500, sx: 90, sy: 18, v: 0.004, o: 0.8},
        {x: 0, y: 900, z: -8000, sx: 220, sy: 22, v: 0.002, o: 0.85},
        {x: 0, y: 200, z: -6000, sx: 200, sy: 22, v: 0.003, o: 0.95},
        {x: 0, y: -380, z: -3500, sx: 140, sy: 18, v: 0.005, o: 1},
        {x: 0, y: -620, z: -1500, sx: 90, sy: 13, v: 0.008, o: 1},
        {x: 0, y: -720, z: 200, sx: 60, sy: 9, v: 0.012, o: 1}
    ]
    Repeater3D {
        model: vista.nuvens
        Model {
            source: "#Rectangle"
            position: Qt.vector3d(modelData.x, modelData.y, modelData.z)
            scale: Qt.vector3d(modelData.sx, modelData.sy, 1)
            opacity: modelData.o
            materials: PrincipledMaterial {
                lighting: PrincipledMaterial.NoLighting
                baseColorMap: Texture { source: vista.tex("nuvem_magica"); tilingModeHorizontal: Texture.Repeat
                    scaleU: 2; positionU: vista.tempo * modelData.v }
                baseColor: Qt.rgba(1.45, 1.4, 1.45, 1)
                alphaMode: PrincipledMaterial.Blend
                cullMode: Material.NoCulling
            }
        }
    }

    // ---------------------------------------------------------------- a ilha da torre
    component Rocha: PrincipledMaterial {
        baseColorMap: Texture { source: vista.tex("rocha_magica"); scaleU: 2; scaleV: 2; tilingModeHorizontal: Texture.Repeat; tilingModeVertical: Texture.Repeat }
        roughness: 0.9
    }
    component Pedra: PrincipledMaterial {
        baseColorMap: Texture { source: vista.tex("pedra_torre"); scaleU: 3; scaleV: 3; tilingModeHorizontal: Texture.Repeat; tilingModeVertical: Texture.Repeat }
        roughness: 0.8
    }
    component Janela: Model {
        source: "#Cube"
        materials: PrincipledMaterial { baseColor: "#c070ff"; emissiveFactor: Qt.vector3d(1.2, 0.5, 2.0) }
    }
    component Pinaculo: Node {
        property real alto: 120
        Model {
            geometry: Malha { pedido: "torno|0,0; 1,0; 1,0.4; 0,1|0|6|plano" }
            scale: Qt.vector3d(alto * 0.22, alto, alto * 0.22)
            materials: PrincipledMaterial { baseColor: "#8a8486"; roughness: 0.8 }
        }
        Model {   // ponta de cristal
            geometry: Malha { pedido: "torno|0,-1; 0.5,0; 0,1|0|6|plano" }
            position.y: alto + 20
            scale: Qt.vector3d(12, 26, 12)
            materials: PrincipledMaterial { baseColor: "#c080ff"; emissiveFactor: Qt.vector3d(0.8, 0.3, 1.3) }
        }
    }
    Node {
        id: ilha
        position: Qt.vector3d(820, -330 + Math.sin(vista.tempo * 0.5) * 14, -700)
        eulerRotation.y: -18
        Model {   // a rocha (cone de cabeça pra baixo, facetado)
            geometry: Malha { pedido: "torno|0,-1.2; 0.2,-0.95; 0.45,-0.6; 0.8,-0.25; 0.97,-0.06; 1,0; 0,0|0.22|9|plano" }
            scale: Qt.vector3d(560, 620, 440)
            materials: Rocha {}
        }
        Model {   // grama/musgo por cima
            geometry: Malha { pedido: "torno|0,0; 1,0; 0.96,0.04; 0,0.05|0.22|9|plano" }
            scale: Qt.vector3d(560, 300, 440)
            materials: PrincipledMaterial { baseColorMap: Texture { source: vista.tex("grama_magica") }
                roughness: 0.9 }
        }
        Repeater3D {   // cristais pendurados embaixo
            model: 5
            Model {
                geometry: Malha { pedido: "torno|0,-1; 0.5,0; 0,1|0|6|plano" }
                position: Qt.vector3d(-200 + index * 100, -300 - vista.acaso(index, 1) * 260, (vista.acaso(index, 2) - 0.5) * 200)
                scale: Qt.vector3d(22, 60 + vista.acaso(index, 3) * 40, 22)
                materials: PrincipledMaterial { baseColor: "#b070ff"; emissiveFactor: Qt.vector3d(0.6, 0.2, 1.0); roughness: 0.15 }
            }
        }
        // ---- a torre (andares afinando)
        Node {
            position: Qt.vector3d(40, 14, -40)
            Model {
                geometry: Malha { pedido: "torno|0,0; 190,0; 190,20; 172,30; 168,240; 180,250; 180,262; 0,262|0|8|plano" }
                materials: Pedra {}
            }
            Model {
                geometry: Malha { pedido: "torno|0,262; 135,262; 128,520; 142,530; 142,544; 0,544|0|8|plano" }
                materials: Pedra {}
            }
            Model {
                geometry: Malha { pedido: "torno|0,544; 98,544; 92,780; 104,790; 104,802; 0,802|0|8|plano" }
                materials: Pedra {}
            }
            Model {
                geometry: Malha { pedido: "torno|0,802; 70,802; 66,960; 0,960|0|8|plano" }
                materials: Pedra {}
            }
            Pinaculo { position.y: 960; alto: 260 }
            Repeater3D {   // janelas acesas nas faces de cada andar
                model: 18
                Janela {
                    readonly property int andar: Math.floor(index / 6)
                    readonly property real a: (index % 6) * 60 + andar * 30 + 22.5
                    readonly property real r: [170, 130, 94][andar]
                    position: Qt.vector3d(Math.cos(a * Math.PI / 180) * r, 110 + andar * 270, Math.sin(a * Math.PI / 180) * r)
                    eulerRotation.y: -a + 90
                    scale: Qt.vector3d(0.26, 0.6, 0.06)
                }
            }
            Repeater3D {   // torrinhas em volta da base e do meio
                model: [{a: 20, r: 205, y: 262, h: 110}, {a: 120, r: 205, y: 262, h: 90}, {a: 220, r: 205, y: 262, h: 110},
                        {a: 300, r: 205, y: 262, h: 80}, {a: 60, r: 150, y: 544, h: 90}, {a: 200, r: 150, y: 544, h: 90},
                        {a: 330, r: 112, y: 802, h: 70}]
                Pinaculo {
                    position: Qt.vector3d(Math.cos(modelData.a * Math.PI / 180) * modelData.r, modelData.y, Math.sin(modelData.a * Math.PI / 180) * modelData.r)
                    alto: modelData.h
                }
            }
        }
        // ---- arcos (aqueduto) saindo pra esquerda e a escada
        Repeater3D {
            model: 4
            Node {
                position: Qt.vector3d(-150 - index * 95, 14, 120)
                Model { source: "#Cube"; position.y: 70; scale: Qt.vector3d(0.22, 1.4, 0.3); materials: Pedra {} }
                Model { source: "#Cube"; position: Qt.vector3d(-47, 150, 0); scale: Qt.vector3d(1.16, 0.22, 0.32); materials: Pedra {} }
                Model {
                    geometry: Malha { pedido: "toro|38|8|0.5|10|4|plano" }
                    position: Qt.vector3d(-47, 118, 0)
                    eulerRotation.x: 90
                    materials: Pedra {}
                }
            }
        }
        Repeater3D {   // escada
            model: 6
            Model {
                source: "#Cube"
                position: Qt.vector3d(-60, 14 + index * 16, 230 - index * 22)
                scale: Qt.vector3d(1.3, 0.16, 0.24)
                materials: Pedra {}
            }
        }
        // ---- a ESTRELA no topo
        Node {
            position: Qt.vector3d(40, 1290, -40)
            Model {
                geometry: Malha { pedido: "torno|0,-1; 0.4,0; 0,1|0|4|plano" }
                eulerRotation.y: vista.tempo * 50
                scale: Qt.vector3d(40, 70, 40)
                materials: PrincipledMaterial { lighting: PrincipledMaterial.NoLighting; baseColor: "#f0d8ff" }
            }
            PointLight { color: "#d080ff"; brightness: 8; quadraticFade: 0.8 }
            ParticleSystem3D {
                running: true
                SpriteParticle3D {
                    id: halo
                    sprite: Texture { source: vista.tex("sprite_brilho") }
                    maxAmount: 3
                    color: "#e0a0ff"
                    blendMode: SpriteParticle3D.Screen
                    billboard: true
                }
                ParticleEmitter3D {
                    particle: halo
                    emitRate: 4
                    lifeSpan: 800
                    particleScale: 60
                    particleEndScale: 70
                }
            }
        }
        // ---- os ANÉIS DE RUNAS girando em volta da torre
        Repeater3D {
            model: [{y: 760, r: 330, tx: 8, tz: -6, v: 25}, {y: 980, r: 250, tx: -10, tz: 8, v: -35}, {y: 560, r: 400, tx: 4, tz: 10, v: 18}]
            Node {
                position: Qt.vector3d(40, modelData.y, -40)
                eulerRotation: Qt.vector3d(modelData.tx, vista.tempo * modelData.v, modelData.tz)
                Model {
                    geometry: Malha { pedido: "torno|1,-0.06; 1,0.06|0|48" }
                    scale: Qt.vector3d(modelData.r, modelData.r, modelData.r)
                    materials: PrincipledMaterial {
                        lighting: PrincipledMaterial.NoLighting
                        baseColorMap: Texture { source: vista.tex("runas_anel"); scaleU: 3; tilingModeHorizontal: Texture.Repeat }
                        alphaMode: PrincipledMaterial.Blend
                        blendMode: PrincipledMaterial.Screen
                        cullMode: Material.NoCulling
                    }
                }
            }
        }
    }

    // ---------------------------------------------------------------- ilhotas com cristal flutuando
    readonly property var ilhotas: [{x: -1100, y: 400, z: -1400, s: 90}, {x: -500, y: -150, z: -2600, s: 70},
                                     {x: 300, y: 700, z: -2200, s: 60}, {x: 1700, y: 700, z: -1800, s: 100},
                                     {x: 1450, y: -260, z: -900, s: 70}, {x: -1500, y: -80, z: -600, s: 80}]
    Repeater3D {
        model: vista.ilhotas
        Node {
            position: Qt.vector3d(modelData.x, modelData.y + Math.sin(vista.tempo * 0.7 + index * 1.7) * 20, modelData.z)
            eulerRotation.y: index * 50
            scale: Qt.vector3d(modelData.s / 100, modelData.s / 100, modelData.s / 100)
            Model {
                geometry: Malha { pedido: "torno|0,-1.3; 0.35,-0.8; 0.8,-0.25; 1,0; 0,0|0.25|7|plano" }
                scale: Qt.vector3d(160, 180, 140)
                materials: Rocha {}
            }
            Model {
                geometry: Malha { pedido: "torno|0,0; 1,0; 1,3; 0,4|0|6|plano" }
                eulerRotation.z: 8
                scale: Qt.vector3d(24, 30, 24)
                materials: PrincipledMaterial { baseColor: "#b070ff"; emissiveFactor: Qt.vector3d(0.7, 0.25, 1.2); roughness: 0.1 }
            }
        }
    }

    // ---------------------------------------------------------------- cristais grandes nos cantos (perto da câmera)
    component CristalGrande: Model {
        geometry: Malha { pedido: "torno|0,0; 1,0; 1,3; 0,4|0|6|plano" }
        materials: PrincipledMaterial {
            baseColor: "#a060ff"
            emissiveFactor: Qt.vector3d(0.45, 0.18, 0.85)
            roughness: 0.12
            clearcoatAmount: 1
            specularAmount: 1
        }
    }
    Node {
        position: Qt.vector3d(-860, -560, 600)
        Model {
            geometry: Malha { pedido: "torno|0,-1; 1,-0.6; 1,0; 0.6,0.5; 0,0.6|0.2|7|plano" }
            scale: Qt.vector3d(260, 200, 220)
            materials: Rocha {}
        }
        CristalGrande { position: Qt.vector3d(-40, 60, 0); eulerRotation.z: 18; scale: Qt.vector3d(60, 110, 60) }
        CristalGrande { position: Qt.vector3d(60, 60, 30); eulerRotation.z: -12; scale: Qt.vector3d(36, 60, 36) }
    }
    Node {
        position: Qt.vector3d(880, -520, 620)
        CristalGrande { eulerRotation.z: -14; scale: Qt.vector3d(62, 120, 62) }
        CristalGrande { position: Qt.vector3d(-90, -20, 40); eulerRotation.z: 22; scale: Qt.vector3d(40, 70, 40) }
        PointLight { position.y: 300; color: "#b060ff"; brightness: 4; quadraticFade: 1.4 }
    }
    PointLight {   // luz lilás batendo na frente da torre
        position: Qt.vector3d(300, 600, 200)
        color: "#d8c0ff"
        brightness: 13
        quadraticFade: 0.3
    }
    Node {
        position: Qt.vector3d(-900, 620, 400)
        eulerRotation.z: 160
        CristalGrande { scale: Qt.vector3d(48, 80, 48) }
    }

    // ---------------------------------------------------------------- o MENU: cristais flutuando no céu
    // (v0.57, pedido do Manel) os botões são CRISTAIS DE VERDADE do cenário, com o nome brilhando dentro.
    // O Lancador esconde o menu 2D quando a cena tem `menuProprio`.
    readonly property bool menuProprio: true
    property int sobre: -1                    // qual cristal está debaixo do mouse
    readonly property var opcoes: [
        {rotulo: "Mestre", y: 430},
        {texto: "Nova sessão", acao: "mestre_nova", y: 352},
        {texto: "Continuar sessão", acao: "mestre_continuar", y: 262, det: ponte.temUltima ? ponte.ultimaAventura : "",
         ok: ponte.temUltima},
        {texto: "Abrir sessão…", acao: "mestre_abrir", y: 172},
        {rotulo: "Jogador", y: 92},
        {texto: "Entrar na sessão", acao: "jogador_entrar", y: 14, det: ponte.servidor !== "" ? "da última vez: " + ponte.servidor : ""},
        {texto: "Sair", acao: "sair", y: -86}
    ]
    Repeater3D {
        model: vista.opcoes
        Node {
            id: cristalNo
            readonly property bool ehBotao: modelData.texto !== undefined
            readonly property bool habilitado: modelData.ok === undefined || modelData.ok
            readonly property bool aceso: vista.sobre === index && habilitado
            property real brilho: aceso ? 1 : 0
            Behavior on brilho { NumberAnimation { duration: 180 } }
            position: Qt.vector3d((index % 2 ? 16 : -16), modelData.y + Math.sin(vista.tempo * 0.9 + index * 1.3) * 5, 300)
            eulerRotation: Qt.vector3d(0, Math.sin(vista.tempo * 0.5 + index) * 6 + (aceso ? 0 : 0), Math.sin(vista.tempo * 0.7 + index * 2) * 1.5)
            scale: Qt.vector3d(1 + brilho * 0.12, 1 + brilho * 0.12, 1 + brilho * 0.12)
            Model {   // o cristal (losango comprido, facetado), deitado
                visible: cristalNo.ehBotao
                property int opcao: index
                pickable: cristalNo.ehBotao
                geometry: Malha { pedido: "torno|0,-1; 0.5,-0.8; 0.5,0.8; 0,1|0|6|plano" }
                eulerRotation: Qt.vector3d(0, 0, 90)
                scale: Qt.vector3d(80, 215, 56)
                materials: PrincipledMaterial {
                    baseColor: cristalNo.habilitado ? "#3a0a80" : "#2a1a40"
                    emissiveFactor: cristalNo.habilitado ? Qt.vector3d(0.42 + cristalNo.brilho * 0.9, 0.08 + cristalNo.brilho * 0.2, 0.95 + cristalNo.brilho * 0.9)
                                                         : Qt.vector3d(0.08, 0.05, 0.14)
                    roughness: 0.25
                    clearcoatAmount: 0.4
                    specularAmount: 0.5
                }
            }
            Model {   // o nome, brilhando por dentro (na frente do cristal)
                source: "#Rectangle"
                position.z: 33
                scale: Qt.vector3d(3.4, 0.85, 1)
                materials: PrincipledMaterial {
                    lighting: PrincipledMaterial.NoLighting
                    alphaMode: PrincipledMaterial.Blend
                    baseColor: Qt.rgba(5, 5, 5, 1)
                    baseColorMap: Texture {
                        sourceItem: Item {
                            width: 720; height: 180
                            Text {
                                anchors.centerIn: parent
                                anchors.verticalCenterOffset: modelData.det ? -16 : 0
                                text: cristalNo.ehBotao ? modelData.texto : modelData.rotulo.toUpperCase()
                                font.family: ponte.cores.fonte
                                font.pixelSize: cristalNo.ehBotao ? 62 : 40
                                font.letterSpacing: cristalNo.ehBotao ? 2 : 14
                                color: cristalNo.ehBotao ? (cristalNo.habilitado ? "#fff4ff" : "#9a8aaa") : "#d8b0ff"
                                style: Text.Outline
                                styleColor: "#5a1a9a"
                            }
                            Text {
                                visible: !!modelData.det
                                anchors.horizontalCenter: parent.horizontalCenter
                                anchors.bottom: parent.bottom
                                anchors.bottomMargin: 14
                                text: modelData.det || ""
                                font.pixelSize: 26
                                color: "#e0c8ff"
                                elide: Text.ElideRight
                                width: 640
                                horizontalAlignment: Text.AlignHCenter
                            }
                        }
                    }
                }
            }
            PointLight {   // o cristal aceso ilumina em volta
                position.z: 80
                color: "#d080ff"
                brightness: cristalNo.brilho * 10
                quadraticFade: 1.2
            }
            Model {   // halo de luz em volta do cristal aceso
                visible: cristalNo.ehBotao && cristalNo.brilho > 0.01
                source: "#Rectangle"
                position.z: -10
                scale: Qt.vector3d(6.2, 2.4, 1)
                opacity: cristalNo.brilho
                materials: PrincipledMaterial {
                    lighting: PrincipledMaterial.NoLighting
                    baseColorMap: Texture { source: vista.tex("sprite_brilho") }
                    baseColor: "#e090ff"
                    alphaMode: PrincipledMaterial.Blend
                    blendMode: PrincipledMaterial.Screen
                }
            }
        }
    }

    MouseArea {   // mouse nos cristais: acende e escolhe
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: vista.sobre >= 0 ? Qt.PointingHandCursor : Qt.ArrowCursor
        function qual(x, y) {
            var r = vista.pick(x, y)
            return r.objectHit && r.objectHit.opcao !== undefined ? r.objectHit.opcao : -1
        }
        onPositionChanged: (m) => vista.sobre = qual(m.x, m.y)
        onExited: vista.sobre = -1
        onClicked: (m) => {
            var i = qual(m.x, m.y)
            if (i < 0) return
            var o = vista.opcoes[i]
            if (o.acao && (o.ok === undefined || o.ok)) ponte.escolher(o.acao)
        }
    }

    // ---------------------------------------------------------------- brilhinhos no ar
    ParticleSystem3D {
        running: vista.anima
        position: Qt.vector3d(0, 300, -500)
        SpriteParticle3D {
            id: brilhinho
            sprite: Texture { source: vista.tex("sprite_faisca") }
            maxAmount: 120
            color: "#e0b0ff"
            blendMode: SpriteParticle3D.Screen
            fadeInDuration: 800
            fadeOutDuration: 800
            billboard: true
        }
        ParticleEmitter3D {
            particle: brilhinho
            emitRate: 20
            lifeSpan: 4000
            particleScale: 1.5
            shape: ParticleShape3D { type: ParticleShape3D.Cube; extents: Qt.vector3d(2000, 900, 800) }
            velocity: VectorDirection3D { direction: Qt.vector3d(0, 10, 0); directionVariation: Qt.vector3d(10, 10, 10) }
        }
    }
}
