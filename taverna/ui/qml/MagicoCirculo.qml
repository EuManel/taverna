// 🔮 Mágico, tela 1 (v0.57, referência do Manel): plataforma de pedra rachada FLUTUANDO no espaço roxo, com o
// CÍRCULO MÁGICO enorme no meio (dois anéis girando em sentidos contrários e pulsando) — o menu fica dentro
// dele. Cristais, cristal flutuando com anel de runas, poções, alambique com fumaça roxa, pilão com pó
// brilhando, rachaduras acesas e lascas de cristal voando em volta.
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
    readonly property real raio: 620      // raio do círculo mágico

    // onde o miolo do círculo caiu no 2D (o menu fica ali)
    property rect tela: Qt.rect(0, 0, 0, 0)
    function medirTela() {
        var cima = mapFrom3DScene(Qt.vector3d(0, 2, -raio * 0.74))
        var baixo = mapFrom3DScene(Qt.vector3d(0, 2, raio * 0.7))
        var esq = mapFrom3DScene(Qt.vector3d(-raio * 0.62, 2, 0))
        var dir = mapFrom3DScene(Qt.vector3d(raio * 0.62, 2, 0))
        tela = Qt.rect(esq.x, cima.y, dir.x - esq.x, baixo.y - cima.y)
    }
    onWidthChanged: Qt.callLater(medirTela)
    onHeightChanged: Qt.callLater(medirTela)
    Component.onCompleted: Qt.callLater(medirTela)

    property real tempo: 0
    NumberAnimation on tempo { from: 0; to: 1000; duration: 1000000; loops: Animation.Infinite; running: vista.anima }
    readonly property real pulso: 0.85 + 0.15 * Math.sin(tempo * 1.6)
    property real clarao: 0          // (v0.58) o clarão do clique (0..1)

    environment: SceneEnvironment {
        backgroundMode: SceneEnvironment.SkyBox
        lightProbe: Texture { source: vista.tex("espaco"); mappingMode: Texture.LightProbe }
        probeExposure: 0.9
        probeOrientation: Qt.vector3d(0, 40, 0)
        antialiasingMode: SceneEnvironment.MSAA
        antialiasingQuality: vista.nivel === 2 ? SceneEnvironment.VeryHigh : SceneEnvironment.High
        aoEnabled: vista.nivel === 2
        aoStrength: 60
        aoDistance: 14
        tonemapMode: SceneEnvironment.TonemapModeFilmic
    }
    PerspectiveCamera {
        id: camera
        position: Qt.vector3d(0, 1640, 1240)
        eulerRotation.x: -53
        fieldOfView: 40
        clipNear: 50
        clipFar: 20000
    }

    // ---------------------------------------------------------------- luzes
    DirectionalLight {
        eulerRotation: Qt.vector3d(-55, -30, 0)
        color: "#b8a8ff"
        brightness: 0.55
        castsShadow: true
        shadowMapQuality: Light.ShadowMapQualityHigh
        shadowFactor: 55
        shadowFilter: 8
    }
    PointLight {   // o círculo acende o chão
        position: Qt.vector3d(0, 160, 0)
        color: "#c070ff"
        brightness: 6 * vista.pulso + vista.clarao * 40
        quadraticFade: 0.5
    }

    // ---------------------------------------------------------------- a plataforma (pedra com rachaduras acesas)
    // (v0.58) FENDAS de verdade: sulco escuro com relevo (normal) e a luz só no fundo da fenda
    component Pedra: PrincipledMaterial {
        property real ladrilho: 1.5
        baseColorMap: Texture { source: vista.tex("pedra_rachada"); scaleU: ladrilho; scaleV: ladrilho; tilingModeHorizontal: Texture.Repeat; tilingModeVertical: Texture.Repeat }
        normalMap: Texture { source: vista.tex("fendas_normal"); scaleU: ladrilho; scaleV: ladrilho; tilingModeHorizontal: Texture.Repeat; tilingModeVertical: Texture.Repeat }
        normalStrength: 1.2
        emissiveMap: Texture { source: vista.tex("fendas_luz"); scaleU: ladrilho; scaleV: ladrilho; tilingModeHorizontal: Texture.Repeat; tilingModeVertical: Texture.Repeat }
        emissiveFactor: Qt.vector3d(1.1 * vista.pulso * (1 + vista.clarao * 2), 1.1 * vista.pulso * (1 + vista.clarao * 2), 1.1 * vista.pulso * (1 + vista.clarao * 2))
        roughness: 0.85
    }
    Model {   // o corpo da plataforma (lados e o fundo pendurado)
        geometry: Malha { pedido: "torno|0,-0.55; 0.5,-0.55; 0.8,-0.4; 0.95,-0.12; 1,0; 0,0|0.07|8|plano" }
        eulerRotation.y: 22.5
        scale: Qt.vector3d(1150, 560, 950)
        materials: Pedra {}
    }
    Model {   // o TAMPO (mapeado reto: as lajes e as fendas não entortam)
        geometry: Malha { pedido: "moeda|8" }
        position.y: -3
        eulerRotation.y: 22.5
        scale: Qt.vector3d(1150, 20, 950)
        materials: Pedra { ladrilho: 2.6 }
    }
    Repeater3D {   // pedaços de pedra soltos pendurados embaixo / em volta
        model: 9
        Model {
            readonly property real a: index * 40 + vista.acaso(index, 1) * 20
            geometry: Malha { pedido: "torno|0,-1; 0.6,-0.6; 1,0; 0,0.15|0.2|6|plano" }
            position: Qt.vector3d(Math.cos(a * Math.PI / 180) * 1050, -180 - vista.acaso(index, 2) * 260 + Math.sin(vista.tempo * 0.6 + index) * 18,
                                  Math.sin(a * Math.PI / 180) * 880)
            eulerRotation.y: a
            scale: Qt.vector3d(70 + vista.acaso(index, 3) * 70, 90 + vista.acaso(index, 4) * 90, 70 + vista.acaso(index, 3) * 60)
            materials: Pedra {}
        }
    }

    // ---------------------------------------------------------------- o CÍRCULO MÁGICO (2 anéis girando)
    Node {
        position.y: 2
        eulerRotation.y: vista.tempo * 3
        Model {
            source: "#Rectangle"
            eulerRotation.x: -90
            scale: Qt.vector3d(vista.raio * 2 / 100, vista.raio * 2 / 100, 1)
            materials: PrincipledMaterial {
                lighting: PrincipledMaterial.NoLighting
                baseColorMap: Texture { source: vista.tex("circulo_runas") }
                baseColor: Qt.rgba(vista.pulso * (1 + vista.clarao * 2.5), vista.pulso * (1 + vista.clarao * 2.5), vista.pulso * (1 + vista.clarao * 2.5), 1)
                alphaMode: PrincipledMaterial.Blend
                blendMode: PrincipledMaterial.Screen
            }
        }
    }
    Node {
        position.y: 3
        eulerRotation.y: -vista.tempo * 5
        Model {
            source: "#Rectangle"
            eulerRotation.x: -90
            scale: Qt.vector3d(vista.raio * 1.66 / 100, vista.raio * 1.66 / 100, 1)
            materials: PrincipledMaterial {
                lighting: PrincipledMaterial.NoLighting
                baseColorMap: Texture { source: vista.tex("circulo_magico") }
                baseColor: Qt.rgba(vista.pulso * (1 + vista.clarao * 2.5), vista.pulso * (1 + vista.clarao * 2.5), vista.pulso * (1 + vista.clarao * 2.5), 1)
                alphaMode: PrincipledMaterial.Blend
                blendMode: PrincipledMaterial.Screen
            }
        }
    }
    ParticleSystem3D {   // faíscas subindo do círculo
        running: vista.anima
        SpriteParticle3D {
            id: faisca
            sprite: Texture { source: vista.tex("sprite_brilho") }
            maxAmount: 160
            color: "#d090ff"
            blendMode: SpriteParticle3D.Screen
            fadeInDuration: 300
            fadeOutDuration: 800
            billboard: true
        }
        ParticleEmitter3D {
            particle: faisca
            emitRate: vista.nivel === 2 ? 40 : 18
            lifeSpan: 2600
            particleScale: 3
            particleEndScale: 0.5
            shape: ParticleShape3D { type: ParticleShape3D.Cylinder; extents: Qt.vector3d(vista.raio, 2, vista.raio) }
            velocity: VectorDirection3D { direction: Qt.vector3d(0, 60, 0); directionVariation: Qt.vector3d(10, 30, 10) }
        }
    }

    // ================================================================ (v0.58) o MENU escrito com LUZ na pedra
    // Sem cápsulas: as opções ficam gravadas no chão, brilhando fraco como as runas do anel. O miolo do círculo
    // ganha um disco escuro e liso (apaga o pentagrama atrás das letras). Hover: a palavra acende forte na cor
    // de destaque, um traço de luz corre por baixo e UMA runa do anel de fora acende junto. Clique: a luz corre
    // pelas linhas do pentagrama até as pontas, o círculo inteiro dá um clarão e entra a transição.
    readonly property bool menuProprio: true
    readonly property bool tituloProprio: true      // (o título "Taverna" também é escrito no chão)
    readonly property color destaque: ponte.destaqueMagico
    property int sobre: -1
    property int escolhido: -1
    readonly property var opcoes: [
        {titulo: "Taverna", z: -322},
        {rotulo: "Mestre", z: -226},
        {texto: "Nova sessão", acao: "mestre_nova", z: -164, runa: 0},
        {texto: "Continuar sessão", acao: "mestre_continuar", z: -84, runa: 1,
         det: ponte.temUltima ? ponte.ultimaAventura : "", ok: ponte.temUltima},
        {texto: "Abrir sessão…", acao: "mestre_abrir", z: 4, runa: 2},
        {rotulo: "Jogador", z: 72},
        {texto: "Entrar na sessão", acao: "jogador_entrar", z: 132, runa: 3,
         det: ponte.servidor !== "" ? "da última vez: " + ponte.servidor : ""},
        {texto: "Sair", acao: "sair", z: 212, runa: 4}
    ]
    Model {   // disco escuro e liso no miolo (sólido: fica por baixo das letras e esconde o pentagrama)
        geometry: Malha { pedido: "moeda|64" }
        position.y: 3.4
        scale: Qt.vector3d(vista.raio * 0.585, 1, vista.raio * 0.585)
        materials: PrincipledMaterial {
            lighting: PrincipledMaterial.NoLighting
            baseColor: Qt.rgba(0.04 + vista.clarao * 0.3, 0.022 + vista.clarao * 0.15, 0.08 + vista.clarao * 0.4, 1)
        }
    }
    Repeater3D {   // as palavras de luz
        model: vista.opcoes
        Node {
            id: palavra
            readonly property bool ehBotao: modelData.texto !== undefined
            readonly property bool habilitado: modelData.ok === undefined || modelData.ok
            readonly property bool acesa: (vista.sobre === index || vista.escolhido === index) && habilitado
            property real brilho: acesa ? 1 : 0
            Behavior on brilho { NumberAnimation { duration: 220; easing.type: Easing.OutQuad } }
            position: Qt.vector3d(0, 4.2, modelData.z)
            Model {
                property int opcao: index
                pickable: palavra.ehBotao
                source: "#Rectangle"
                eulerRotation.x: -90
                scale: modelData.titulo ? Qt.vector3d(6.2, 1.55, 1) : Qt.vector3d(5.6, 1.1, 1)
                materials: PrincipledMaterial {
                    lighting: PrincipledMaterial.NoLighting
                    alphaMode: PrincipledMaterial.Blend
                    blendMode: PrincipledMaterial.Screen
                    depthDrawMode: Material.NeverDepthDraw   // (senão uma palavra apaga a outra)
                    baseColor: Qt.rgba(1 + palavra.brilho * 1.2, 1 + palavra.brilho * 1.2, 1 + palavra.brilho * 1.2, 1)
                    baseColorMap: Texture {
                        sourceItem: Item {
                            width: 720
                            height: modelData.titulo ? 180 : 140
                            Text {   // o brilho em volta (texto mais grosso e transparente atrás)
                                anchors.centerIn: rot
                                text: rot.text
                                font: rot.font
                                color: "transparent"
                                style: Text.Outline
                                styleColor: palavra.acesa || modelData.titulo ? Qt.rgba(vista.destaque.r, vista.destaque.g, vista.destaque.b, 0.45)
                                                                            : Qt.rgba(0.75, 0.4, 1, 0.35)
                            }
                            Text {
                                id: rot
                                anchors.horizontalCenter: parent.horizontalCenter
                                anchors.verticalCenter: parent.verticalCenter
                                anchors.verticalCenterOffset: modelData.det ? -14 : 0
                                text: modelData.titulo ? modelData.titulo
                                      : (palavra.ehBotao ? modelData.texto : modelData.rotulo.toUpperCase())
                                font.family: ponte.cores.fonte
                                font.pixelSize: modelData.titulo ? 118 : (palavra.ehBotao ? 60 : 30)
                                font.letterSpacing: palavra.ehBotao || modelData.titulo ? 3 : 16
                                color: modelData.titulo ? vista.destaque
                                       : !palavra.habilitado ? Qt.rgba(0.45, 0.35, 0.55, 1)
                                       : palavra.acesa ? Qt.lighter(vista.destaque, 1.25)
                                       : palavra.ehBotao ? Qt.rgba(0.78, 0.6, 1, 0.82) : Qt.rgba(0.7, 0.5, 0.95, 0.7)
                                style: Text.Outline
                                styleColor: palavra.acesa ? Qt.rgba(1, 1, 1, 0.5) : Qt.rgba(0.35, 0.1, 0.6, 0.6)
                            }
                            Rectangle {   // o traço de luz correndo por baixo da palavra
                                visible: palavra.ehBotao
                                anchors.horizontalCenter: parent.horizontalCenter
                                y: rot.y + rot.height - 4 + (modelData.det ? 0 : 0)
                                height: 4
                                radius: 2
                                width: rot.width * palavra.brilho
                                color: vista.destaque
                                opacity: palavra.brilho
                            }
                            Text {
                                visible: !!modelData.det
                                anchors.horizontalCenter: parent.horizontalCenter
                                anchors.bottom: parent.bottom
                                anchors.bottomMargin: 6
                                text: modelData.det || ""
                                font.pixelSize: 24
                                color: Qt.rgba(0.8, 0.65, 1, 0.75)
                                elide: Text.ElideRight
                                width: 660
                                horizontalAlignment: Text.AlignHCenter
                            }
                        }
                    }
                }
            }
        }
    }
    // as 5 runas do anel de fora que acendem junto com cada opção (giram com o anel)
    Node {
        position.y: 5
        eulerRotation.y: vista.tempo * 3
        Repeater3D {
            model: 5
            Model {
                readonly property int qual: index
                readonly property real a: -90 + index * 72 + 18
                readonly property bool acesa: vista.opcoes.some(function (o, i) { return o.runa === qual && (vista.sobre === i || vista.escolhido === i) })
                property real luz: acesa ? 1 : 0
                Behavior on luz { NumberAnimation { duration: 220 } }
                source: "#Rectangle"
                position: Qt.vector3d(Math.cos(a * Math.PI / 180) * vista.raio * 0.922, 0, Math.sin(a * Math.PI / 180) * vista.raio * 0.922)
                eulerRotation: Qt.vector3d(-90, 0, -a - 90)
                scale: Qt.vector3d(0.7 + luz * 0.5, 0.7 + luz * 0.5, 1)
                opacity: 0.1 + luz * 0.9
                materials: PrincipledMaterial {
                    lighting: PrincipledMaterial.NoLighting
                    baseColorMap: Texture { source: vista.tex("runa_" + [3, 7, 11, 13, 15][qual]) }
                    baseColor: Qt.rgba(vista.destaque.r * 2.2, vista.destaque.g * 2.2, vista.destaque.b * 2.2, 1)
                    alphaMode: PrincipledMaterial.Blend
                    blendMode: PrincipledMaterial.Screen
                }
            }
        }
    }
    // o clique: a luz corre do centro até as 5 pontas do pentagrama (giram junto com o anel de dentro)
    property real corrida: 0
    Node {
        position.y: 6
        eulerRotation.y: -vista.tempo * 5
        Repeater3D {
            model: 5
            Model {
                readonly property real a: (-90 + index * 72) * Math.PI / 180
                readonly property real r: vista.raio * 0.585 * vista.corrida
                visible: vista.corrida > 0.001
                source: "#Sphere"
                position: Qt.vector3d(Math.cos(a) * r, 0, Math.sin(a) * r)
                scale: Qt.vector3d(0.32, 0.32, 0.32)
                materials: PrincipledMaterial {
                    lighting: PrincipledMaterial.NoLighting
                    baseColor: Qt.rgba(vista.destaque.r * 3, vista.destaque.g * 3, vista.destaque.b * 3, 1)
                }
            }
        }
    }
    SequentialAnimation {
        id: ritual
        property string acao: ""
        NumberAnimation { target: vista; property: "corrida"; from: 0; to: 1; duration: 420; easing.type: Easing.InQuad }
        ParallelAnimation {
            NumberAnimation { target: vista; property: "clarao"; from: 0; to: 1; duration: 120 }
            NumberAnimation { target: vista; property: "corrida"; to: 0; duration: 10 }
        }
        PauseAnimation { duration: 160 }
        ScriptAction { script: ponte.escolher(ritual.acao) }
        NumberAnimation { target: vista; property: "clarao"; to: 0; duration: 500 }
        ScriptAction { script: vista.escolhido = -1 }
    }
    MouseArea {   // mouse nas palavras: acende; clique: o ritual e escolhe
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: vista.sobre >= 0 ? Qt.PointingHandCursor : Qt.ArrowCursor
        function qual(x, y) {
            var r = vista.pick(x, y)
            return r.objectHit && r.objectHit.opcao !== undefined ? r.objectHit.opcao : -1
        }
        onPositionChanged: (m) => vista.sobre = ritual.running ? vista.sobre : qual(m.x, m.y)
        onExited: if (!ritual.running) vista.sobre = -1
        onClicked: (m) => {
            if (ritual.running) return
            var i = qual(m.x, m.y)
            if (i < 0) return
            var o = vista.opcoes[i]
            if (!o.acao || (o.ok !== undefined && !o.ok)) return
            vista.escolhido = i
            ritual.acao = o.acao
            if (vista.anima) ritual.start(); else ponte.escolher(o.acao)
        }
    }

    // ---------------------------------------------------------------- cristais (cima, esquerda)
    component Cristal: Model {
        geometry: Malha { pedido: "torno|0,0; 1,0; 1,3; 0,4|0|6|plano" }
        materials: PrincipledMaterial {
            baseColor: "#b070ff"
            emissiveFactor: Qt.vector3d(0.45, 0.18, 0.85)
            roughness: 0.12
            clearcoatAmount: 1
            specularAmount: 1
        }
    }
    Node {
        position: Qt.vector3d(-800, 0, -330)
        Model {
            geometry: Malha { pedido: "torno|0,0; 1,0; 0.9,0.6; 0.6,1; 0,1|0.15|7|plano" }
            scale: Qt.vector3d(210, 90, 190)
            materials: Pedra {}
        }
        Cristal { position: Qt.vector3d(-20, 80, -10); scale: Qt.vector3d(46, 85, 46); eulerRotation: Qt.vector3d(-6, 10, 8) }
        Cristal { position: Qt.vector3d(70, 80, 30); scale: Qt.vector3d(34, 60, 34); eulerRotation: Qt.vector3d(10, 30, -14) }
        Cristal { position: Qt.vector3d(-90, 80, 60); scale: Qt.vector3d(28, 46, 28); eulerRotation: Qt.vector3d(14, 0, 20) }
        Cristal { position: Qt.vector3d(40, 80, -80); scale: Qt.vector3d(24, 38, 24); eulerRotation: Qt.vector3d(-18, 50, -6) }
        PointLight { position.y: 260; color: "#b060ff"; brightness: 4 * vista.pulso; quadraticFade: 1.4 }
    }

    // ---------------------------------------------------------------- cristal flutuando com anel de runas (esquerda)
    Node {
        position: Qt.vector3d(-880, 220 + Math.sin(vista.tempo * 1.3) * 22, 160)
        Model {
            geometry: Malha { pedido: "torno|0,-1; 0.5,0; 0,1|0|6|plano" }
            eulerRotation.y: vista.tempo * 40
            scale: Qt.vector3d(70, 140, 70)
            materials: PrincipledMaterial {
                baseColor: "#c080ff"
                emissiveFactor: Qt.vector3d(0.7, 0.3, 1.1)
                roughness: 0.1
                clearcoatAmount: 1
            }
        }
        Node {
            eulerRotation.x: 72
            Node {
                eulerRotation.y: -vista.tempo * 30
                Model {
                    geometry: Malha { pedido: "torno|1,-0.07; 1,0.07|0|40" }
                    scale: Qt.vector3d(190, 190, 190)
                    materials: PrincipledMaterial {
                        lighting: PrincipledMaterial.NoLighting
                        baseColorMap: Texture { source: vista.tex("runas_anel"); scaleU: 2; tilingModeHorizontal: Texture.Repeat }
                        alphaMode: PrincipledMaterial.Blend
                        blendMode: PrincipledMaterial.Screen
                        cullMode: Material.NoCulling
                    }
                }
            }
        }
        PointLight { color: "#c070ff"; brightness: 5 * vista.pulso; quadraticFade: 1.6 }
    }

    // ---------------------------------------------------------------- poções (embaixo, esquerda)
    // (v0.58) vidro mais legível: contorno escuro (casco invertido), reflexo, aro no gargalo e o NÍVEL do líquido
    component Pocao: Node {
        property color liquido: "#c01830"
        property real tam: 1
        property real nivelLiq: 0.62
        scale: Qt.vector3d(tam, tam, tam)
        Model {   // contorno (o mesmo vidro um pouco maior, só as costas: vira uma borda escura)
            geometry: Malha { pedido: "torno|0,0; 40,0; 58,20; 62,46; 50,74; 20,90; 18,124; 22,128; 22,134; 0,134|0|8|plano" }
            scale: Qt.vector3d(1.07, 1.03, 1.07)
            position.y: -2
            materials: PrincipledMaterial { lighting: PrincipledMaterial.NoLighting; baseColor: "#140820"; cullMode: Material.FrontFaceCulling }
        }
        Model {   // líquido (com a superfície reta no nível)
            geometry: Malha { pedido: "torno|0,4; 36,4; 53,22; 57,46; 50,66; 40,74; 0,74|0|8|plano" }
            scale: Qt.vector3d(1, nivelLiq / 0.62, 1)
            materials: PrincipledMaterial {
                baseColor: liquido
                emissiveFactor: Qt.vector3d(liquido.r * 0.65, liquido.g * 0.65, liquido.b * 0.65)
                roughness: 0.1
            }
        }
        Model {   // a superfície do líquido, mais clara (dá pra ver o nível)
            source: "#Cylinder"
            position.y: 74 * nivelLiq / 0.62
            scale: Qt.vector3d(0.92, 0.01, 0.92)
            materials: PrincipledMaterial { lighting: PrincipledMaterial.NoLighting
                baseColor: Qt.lighter(liquido, 1.7) }
        }
        Model {   // vidro
            geometry: Malha { pedido: "torno|0,0; 40,0; 58,20; 62,46; 50,74; 20,90; 18,124; 22,128; 22,134; 0,134|0|8|plano" }
            materials: PrincipledMaterial {
                baseColor: "#e8e0ff"
                roughness: 0.04
                opacity: 0.28
                alphaMode: PrincipledMaterial.Blend
                specularAmount: 1
                clearcoatAmount: 1
            }
        }
        Model {   // reflexo (risco de luz no vidro)
            source: "#Sphere"
            position: Qt.vector3d(-34, 52, 34)
            eulerRotation.z: 12
            scale: Qt.vector3d(0.05, 0.3, 0.05)
            materials: PrincipledMaterial { lighting: PrincipledMaterial.NoLighting; baseColor: "#ffffff"; opacity: 0.8
                alphaMode: PrincipledMaterial.Blend }
        }
        Model {   // aro do gargalo
            geometry: Malha { pedido: "toro|21|3.5|1|12|5|plano" }
            position.y: 126
            materials: PrincipledMaterial { baseColorMap: Texture { source: vista.tex("latao_velho") }
                metalness: 0.8; roughness: 0.35 }
        }
        Model {   // rolha
            source: "#Cylinder"
            position.y: 142
            scale: Qt.vector3d(0.38, 0.2, 0.38)
            materials: PrincipledMaterial { baseColorMap: Texture { source: vista.tex("latao_velho") }
                metalness: 0.8; roughness: 0.35 }
        }
    }
    Pocao { position: Qt.vector3d(-690, 0, 330); liquido: "#d0102a"; tam: 1.45; nivelLiq: 0.66 }
    Pocao { position: Qt.vector3d(-545, 0, 405); liquido: "#18b8a0"; tam: 1.25; nivelLiq: 0.5 }
    Pocao { position: Qt.vector3d(-425, 0, 460); liquido: "#a040f0"; tam: 0.95; nivelLiq: 0.7 }
    Pocao { position: Qt.vector3d(-330, 0, 505); liquido: "#d8e020"; tam: 0.8; nivelLiq: 0.4 }
    // ---------------------------------------------------------------- alambique (cima, direita)
    Node {
        position: Qt.vector3d(640, 0, -420)
        Repeater3D {   // pés
            model: 3
            Model {
                source: "#Cylinder"
                position: Qt.vector3d(Math.cos(index * 2.094) * 60, 50, Math.sin(index * 2.094) * 60)
                eulerRotation: Qt.vector3d(Math.sin(index * 2.094) * 14, 0, -Math.cos(index * 2.094) * 14)
                scale: Qt.vector3d(0.08, 1, 0.08)
                materials: PrincipledMaterial { baseColorMap: Texture { source: vista.tex("latao_velho") }
                    metalness: 0.8; roughness: 0.4 }
            }
        }
        Model {   // caldeira de latão
            geometry: Malha { pedido: "torno|0,100; 60,100; 92,140; 100,190; 86,240; 40,262; 36,300; 46,306; 46,316; 0,316|0|10|plano" }
            materials: PrincipledMaterial { baseColorMap: Texture { source: vista.tex("latao_velho") }
                metalness: 0.85; roughness: 0.35 }
        }
        Model {   // fogo roxo embaixo
            source: "#Sphere"
            position.y: 80
            scale: Qt.vector3d(0.9, 0.3, 0.9)
            materials: PrincipledMaterial { lighting: PrincipledMaterial.NoLighting; baseColor: "#c060ff" }
        }
        PointLight { position.y: 70; color: "#b050ff"; brightness: 5 * vista.pulso; quadraticFade: 1.2 }
        Model {   // a serpentina (tubo de vidro roxo em espiral)
            geometry: Malha { pedido: "helice|40|7|4|200" }
            position: Qt.vector3d(210, 120, 30)
            materials: PrincipledMaterial {
                baseColor: "#c090ff"
                emissiveFactor: Qt.vector3d(0.5, 0.25, 0.9)
                roughness: 0.1
                opacity: 0.8
                alphaMode: PrincipledMaterial.Blend
            }
        }
        Model {   // cano ligando a caldeira na serpentina
            source: "#Cylinder"
            position: Qt.vector3d(120, 330, 15)
            eulerRotation.z: -70
            scale: Qt.vector3d(0.12, 2.0, 0.12)
            materials: PrincipledMaterial { baseColor: "#c090ff"; emissiveFactor: Qt.vector3d(0.4, 0.2, 0.7); roughness: 0.1 }
        }
        Repeater3D {   // armação da serpentina
            model: [-1, 1]
            Model {
                source: "#Cube"
                position: Qt.vector3d(210 + modelData * 70, 170, 30)
                scale: Qt.vector3d(0.12, 3.4, 0.12)
                materials: PrincipledMaterial { baseColorMap: Texture { source: vista.tex("latao_velho") }
                    metalness: 0.8; roughness: 0.4 }
            }
        }
        Model {   // balão de vidro embaixo, com líquido roxo
            source: "#Sphere"
            position: Qt.vector3d(330, 70, 60)
            scale: Qt.vector3d(1.1, 1.1, 1.1)
            materials: PrincipledMaterial { baseColor: "#a050f0"; emissiveFactor: Qt.vector3d(0.4, 0.15, 0.7); roughness: 0.1; opacity: 0.75; alphaMode: PrincipledMaterial.Blend }
        }
        ParticleSystem3D {   // fumaça roxa saindo do bico
            running: vista.anima
            position.y: 320
            SpriteParticle3D {
                id: fumaca
                sprite: Texture { source: vista.tex("sprite_fumaca") }
                maxAmount: 80
                color: Qt.rgba(0.7, 0.45, 1, 0.5)
                fadeInDuration: 300
                fadeOutDuration: 1200
                billboard: true
            }
            ParticleEmitter3D {
                particle: fumaca
                emitRate: 12
                lifeSpan: 3600
                particleScale: 14
                particleEndScale: 40
                velocity: VectorDirection3D { direction: Qt.vector3d(30, 90, -10); directionVariation: Qt.vector3d(15, 20, 15) }
            }
            Wander3D { particles: [fumaca]; globalAmount: Qt.vector3d(40, 10, 40); globalPace: Qt.vector3d(0.4, 0.3, 0.4) }
        }
    }

    // ---------------------------------------------------------------- pilão com pó brilhando (embaixo, direita)
    Node {
        position: Qt.vector3d(720, 0, 430)
        Model {
            geometry: Malha { pedido: "torno|0,0; 80,0; 112,40; 118,120; 100,124; 92,60; 0,52|0.05|8|plano" }
            materials: PrincipledMaterial { baseColorMap: Texture { source: vista.tex("pedra_torre") }
                roughness: 0.85; cullMode: Material.NoCulling }
        }
        Model {   // pó roxo
            geometry: Malha { pedido: "torno|0,96; 96,96; 60,112; 0,120|0.1|10|plano" }
            materials: PrincipledMaterial { baseColor: "#a050ff"; emissiveFactor: Qt.vector3d(0.6, 0.25, 1.1); roughness: 0.9 }
        }
        Model {   // a mão do pilão
            source: "#Cylinder"
            position: Qt.vector3d(60, 170, -30)
            eulerRotation: Qt.vector3d(-20, 0, -38)
            scale: Qt.vector3d(0.32, 2.4, 0.32)
            materials: PrincipledMaterial { baseColorMap: Texture { source: vista.tex("pedra_torre") }
                roughness: 0.8 }
        }
        PointLight { position.y: 160; color: "#b060ff"; brightness: 3 * vista.pulso; quadraticFade: 1.5 }
        ParticleSystem3D {   // pozinho brilhando subindo
            running: vista.anima
            position.y: 120
            SpriteParticle3D {
                id: po
                sprite: Texture { source: vista.tex("sprite_faisca") }
                maxAmount: 60
                color: "#e0a0ff"
                blendMode: SpriteParticle3D.Screen
                fadeOutDuration: 500
                billboard: true
            }
            ParticleEmitter3D {
                particle: po
                emitRate: 14
                lifeSpan: 1500
                particleScale: 1.6
                particleEndScale: 0.3
                shape: ParticleShape3D { type: ParticleShape3D.Cylinder; extents: Qt.vector3d(80, 2, 80) }
                velocity: VectorDirection3D { direction: Qt.vector3d(0, 70, 0); directionVariation: Qt.vector3d(30, 30, 30) }
            }
        }
    }
    Node {   // tigelinha de latão com pó
        position: Qt.vector3d(470, 0, 590)
        Model {
            geometry: Malha { pedido: "torno|0,0; 40,0; 60,30; 64,46; 56,46; 0,14|0|8|plano" }
            materials: PrincipledMaterial { baseColorMap: Texture { source: vista.tex("latao_velho") }
                metalness: 0.8; roughness: 0.4; cullMode: Material.NoCulling }
        }
        Model {
            geometry: Malha { pedido: "torno|0,24; 54,30; 30,42; 0,46|0.15|8|plano" }
            materials: PrincipledMaterial { baseColor: "#a050ff"; emissiveFactor: Qt.vector3d(0.6, 0.25, 1.1); roughness: 0.9 }
        }
    }

    // ---------------------------------------------------------------- lascas de cristal voando em volta
    Repeater3D {
        model: 14
        Model {
            readonly property real a: index * 25.7 + vista.acaso(index, 1) * 15
            readonly property real r: 1250 + vista.acaso(index, 2) * 500
            geometry: Malha { pedido: "torno|0,-1; 0.5,0; 0,1|0|5|plano" }
            position: Qt.vector3d(Math.cos(a * Math.PI / 180) * r * 1.2, -100 + vista.acaso(index, 3) * 600 + Math.sin(vista.tempo * (0.5 + vista.acaso(index, 4)) + index) * 30,
                                  Math.sin(a * Math.PI / 180) * r * 0.8)
            eulerRotation: Qt.vector3d(vista.tempo * (10 + index), vista.tempo * 20 + index * 40, 15)
            scale: Qt.vector3d(20 + vista.acaso(index, 5) * 30, 40 + vista.acaso(index, 5) * 60, 20 + vista.acaso(index, 5) * 30)
            materials: PrincipledMaterial { baseColor: "#9060e0"; emissiveFactor: Qt.vector3d(0.3, 0.1, 0.6); roughness: 0.15 }
        }
    }
}
