// 🌃 Moderno, tela 2 (v0.58, refeita pelo desenho do Manel): noite na cidade. Na ESQUERDA, um OUTDOOR DE PAPEL
// COLADO (folhas emendadas, rugas, canto rasgado) em cima de pernas de ferro, com o MENU IMPRESSO no cartaz.
// Dois REFLETORES, um de cada lado, giram e apontam a luz pra opção que está embaixo do mouse. Prédio alto atrás
// do outdoor, outro alto na direita e um prédio baixo na frente (embaixo, à direita). Helicóptero passando.
import QtQuick
import QtQuick3D
import QtQuick3D.Particles3D
import QtQuick3D.Helpers
import QtQuick.Shapes

View3D {
    id: vista
    property int nivel: ponte.nivel
    readonly property bool anima: nivel >= 1
    function tex(n) { return ponte.textura(n) }
    camera: camera
    readonly property color destaque: ponte.cores.destaque
    readonly property bool menuProprio: true
    readonly property bool tituloProprio: true
    component Lataria: PrincipledMaterial { baseColor: "#3a4250"; metalness: 0.45; roughness: 0.35 }

    property real tempo: 0
    NumberAnimation on tempo { from: 0; to: 1000; duration: 1000000; loops: Animation.Infinite; running: vista.anima }

    // ---- o outdoor
    readonly property vector3d centro: Qt.vector3d(-560, 300, -350)
    readonly property real larg: 1150
    readonly property real alt: 700
    readonly property real frente: centro.z + 12
    readonly property real pxPorUn: 1650 / larg
    // o cartaz (em pixels da textura): onde fica cada linha do menu (fy = centro da linha, de 0 a 1)
    readonly property var opcoes: [
        {rotulo: "Mestre", fy: 0.30},
        {texto: "Nova sessão", acao: "mestre_nova", fy: 0.385},
        {texto: "Continuar sessão", acao: "mestre_continuar", fy: 0.475,
         det: ponte.temUltima ? ponte.ultimaAventura : "", ok: ponte.temUltima},
        {texto: "Abrir sessão…", acao: "mestre_abrir", fy: 0.565},
        {rotulo: "Jogador", fy: 0.65},
        {texto: "Entrar na sessão", acao: "jogador_entrar", fy: 0.735,
         det: ponte.servidor !== "" ? "da última vez: " + ponte.servidor : ""},
        {texto: "Sair", acao: "sair", fy: 0.83}
    ]
    readonly property real colX: 90        // a coluna do menu (pixels)
    readonly property real colLarg: 760
    function pontoDaLinha(fy) {            // centro da linha do menu no mundo 3D
        return Qt.vector3d(centro.x - larg / 2 + (colX + colLarg / 2) / pxPorUn, centro.y + alt / 2 - fy * alt + 28, frente)
    }
    property int sobre: -1
    // pra onde cada refletor aponta (sem nada embaixo do mouse: um no título, o outro no meio do cartaz)
    readonly property vector3d alvoEsq: sobre >= 0 ? pontoDaLinha(opcoes[sobre].fy)
                                                    : Qt.vector3d(centro.x - larg * 0.22, centro.y + alt * 0.33, frente)
    readonly property vector3d alvoDir: sobre >= 0 ? pontoDaLinha(opcoes[sobre].fy)
                                                    : Qt.vector3d(centro.x + larg * 0.2, centro.y - alt * 0.05, frente)

    environment: SceneEnvironment {
        backgroundMode: SceneEnvironment.Color
        clearColor: "#070b16"
        antialiasingMode: SceneEnvironment.MSAA
        antialiasingQuality: vista.nivel === 2 ? SceneEnvironment.VeryHigh : SceneEnvironment.High
        tonemapMode: SceneEnvironment.TonemapModeFilmic
        fog: Fog {
            enabled: true
            color: "#161c30"
            depthEnabled: true
            depthNear: 1800
            depthFar: 10000
            depthCurve: 1.1
        }
    }
    PerspectiveCamera {
        id: camera
        position: Qt.vector3d(0, 150, 1500)
        eulerRotation.x: -6
        fieldOfView: 46
        clipNear: 20
        clipFar: 20000
    }
    DirectionalLight {   // a noite (fraquinha: quem manda são os refletores)
        eulerRotation: Qt.vector3d(-30, 25, 0)
        color: "#8aa0d0"
        brightness: 0.2
    }

    // ---------------------------------------------------------------- céu e prédios
    Model {
        source: "#Rectangle"
        position: Qt.vector3d(0, 1500, -9000)
        scale: Qt.vector3d(260, 80, 1)
        materials: PrincipledMaterial { lighting: PrincipledMaterial.NoLighting
            baseColorMap: Texture { source: vista.tex("ceu_cidade") } }
    }
    // (v0.58, pedido do Manel) cada prédio tem a SUA fachada inteira (nada repetido): janelas grandes,
    // umas acesas, outras não, com cortina, persiana, gente, TV… (`moderno_cenas._predio`)
    component Predio: Model {
        property int semente: 0
        property real largura: 600
        property real altura: 2000
        property real fundo: 600
        property real tamJanela: 200                     // largura de cada "módulo" de janela (unidades)
        readonly property int cols: Math.max(2, Math.round(largura / tamJanela))
        readonly property int lins: Math.max(3, Math.round(altura / (tamJanela * 1.05)))
        readonly property string nome: "predio_" + semente + "_" + cols + "_" + lins
        source: "#Cube"
        scale: Qt.vector3d(largura / 100, altura / 100, fundo / 100)
        materials: PrincipledMaterial {
            baseColorMap: Texture { source: vista.tex(nome) }
            emissiveMap: Texture { source: vista.tex(nome + "_luz") }
            emissiveFactor: Qt.vector3d(1.25, 1.25, 1.25)
            roughness: 0.75
        }
    }
    // (o Predio é centrado: o topo = position.y + altura/2)
    Predio { semente: 11; largura: 1400; altura: 4200; fundo: 900; tamJanela: 230; position: Qt.vector3d(-450, 1500 - 2100, -2000) }   // alto, atrás do outdoor
    Predio { semente: 12; largura: 750; altura: 4400; fundo: 800; tamJanela: 190; position: Qt.vector3d(900, 1750 - 2200, -1500) }     // alto, na direita

    // ---------------------------------------------------------------- o prédio da FRENTE, detalhado
    readonly property real topoFrente: -150
    readonly property real andar: 150                    // altura de um andar do prédio da frente
    readonly property real fachadaZ: 600                 // a fachada dele (virada pra câmera)
    Predio { semente: 7; largura: 1500; altura: 3000; fundo: 360; tamJanela: 150; position: Qt.vector3d(700, vista.topoFrente - 1500, 420) }
    PointLight {   // poste da rua iluminando a fachada da frente (luz de sódio)
        position: Qt.vector3d(420, vista.topoFrente - 520, 1000)
        color: "#ffb060"
        brightness: 9
        quadraticFade: 0.35
    }
    Model {   // laje (teto) com mureta
        source: "#Cube"
        position: Qt.vector3d(700, vista.topoFrente + 10, 420)
        scale: Qt.vector3d(15.2, 0.22, 3.8)
        materials: PrincipledMaterial { baseColorMap: Texture { source: vista.tex("concreto"); scaleU: 6; scaleV: 4; tilingModeHorizontal: Texture.Repeat; tilingModeVertical: Texture.Repeat }
            roughness: 0.9 }
    }
    Repeater3D {   // caixas d'água em cima da laje
        model: [Qt.vector3d(300, vista.topoFrente + 80, 360), Qt.vector3d(1100, vista.topoFrente + 80, 330)]
        Model {
            source: "#Cube"
            position: modelData
            scale: Qt.vector3d(1.4, 1.2, 1.4)
            materials: PrincipledMaterial { baseColor: "#3a3e46"; roughness: 0.7 }
        }
    }
    // escada de incêndio de ferro (lado esquerdo da fachada): plataformas, guarda-corpo e escadas em zigue-zague
    Node {
        position: Qt.vector3d(150, vista.topoFrente, vista.fachadaZ)
        Repeater3D {
            model: 4
            Node {
                y: -(index + 0.86) * vista.andar
                Model {   // plataforma (grade)
                    source: "#Cube"
                    position: Qt.vector3d(0, 0, 45)
                    scale: Qt.vector3d(3.0, 0.04, 0.9)
                    materials: PrincipledMaterial { baseColor: "#1a1c20"; metalness: 0.8; roughness: 0.5 }
                }
                Model {   // corrimão da frente
                    source: "#Cube"
                    position: Qt.vector3d(0, 55, 90)
                    scale: Qt.vector3d(3.0, 0.03, 0.03)
                    materials: PrincipledMaterial { baseColor: "#24262c"; metalness: 0.8; roughness: 0.4 }
                }
                Repeater3D {   // pilaretes do guarda-corpo
                    model: 7
                    Model {
                        source: "#Cube"
                        position: Qt.vector3d(-145 + index * 48, 27, 90)
                        scale: Qt.vector3d(0.025, 0.55, 0.025)
                        materials: PrincipledMaterial { baseColor: "#24262c"; metalness: 0.8; roughness: 0.4 }
                    }
                }
                Model {   // a escada diagonal descendo pro andar de baixo (alterna o lado)
                    source: "#Cube"
                    position: Qt.vector3d(index % 2 ? 60 : -60, -vista.andar / 2, 55)
                    eulerRotation.z: index % 2 ? -48 : 48
                    scale: Qt.vector3d(2.1, 0.05, 0.5)
                    materials: PrincipledMaterial { baseColor: "#1e2024"; metalness: 0.8; roughness: 0.5 }
                }
            }
        }
    }
    // jardineiras com planta embaixo de algumas janelas, e aparelhos de ar-condicionado
    readonly property var jardineiras: [{c: 4, a: 0}, {c: 6, a: 0}, {c: 8, a: 0}, {c: 5, a: 1}, {c: 7, a: 1}, {c: 9, a: 2}, {c: 4, a: 2}]
    Repeater3D {
        model: vista.jardineiras
        Node {
            position: Qt.vector3d(-50 + (modelData.c + 0.5) * 150, vista.topoFrente - modelData.a * vista.andar - vista.andar * 0.84,
                                  vista.fachadaZ + 22)
            Model {
                source: "#Cube"
                scale: Qt.vector3d(1.2, 0.3, 0.4)
                materials: PrincipledMaterial { baseColor: "#6a3a24"; roughness: 0.8 }
            }
            Repeater3D {   // as plantas (bolotas verdes de tamanhos diferentes) + umas flores
                model: 5
                Model {
                    source: "#Sphere"
                    position: Qt.vector3d(-48 + index * 24, 22 + (index % 2) * 8, 0)
                    scale: Qt.vector3d(0.28 + (index % 3) * 0.06, 0.32 + (index % 2) * 0.1, 0.28)
                    materials: PrincipledMaterial { baseColor: index === 2 ? "#c84a6a" : (index % 2 ? "#3a7a32" : "#2e6a2a"); roughness: 0.8 }
                }
            }
        }
    }
    Repeater3D {   // ar-condicionado
        model: [{c: 1, a: 0}, {c: 6, a: 2}, {c: 2, a: 1}]
        Model {
            source: "#Cube"
            position: Qt.vector3d(-50 + (modelData.c + 0.5) * 150 + 55, vista.topoFrente - modelData.a * vista.andar - vista.andar * 0.86,
                                  vista.fachadaZ + 30)
            scale: Qt.vector3d(0.7, 0.45, 0.55)
            materials: PrincipledMaterial { baseColor: "#b8b8b4"; roughness: 0.6 }
        }
    }    readonly property var longe: [
        {x: -2600, z: -4200, l: 1100, a: 3800, k: 0}, {x: 2600, z: -4500, l: 1100, a: 4200, k: 1},
        {x: 0, z: -6000, l: 1500, a: 5600, k: 2}, {x: -4200, z: -6200, l: 1300, a: 4400, k: 1},
        {x: 4300, z: -6000, l: 1300, a: 5000, k: 0}, {x: 1700, z: -3400, l: 700, a: 3000, k: 0}
    ]
    Repeater3D {
        model: vista.longe
        Predio { semente: 20 + index; largura: modelData.l; altura: modelData.a; fundo: modelData.l; tamJanela: 260
                 position: Qt.vector3d(modelData.x, modelData.a / 2 - 2400, modelData.z) }
    }
    Repeater3D {   // luzinhas vermelhas piscando nos topos
        model: [Qt.vector3d(-450, 1530, -2000), Qt.vector3d(900, 1780, -1500), Qt.vector3d(0, 3230, -6000)]
        Model {
            source: "#Sphere"
            position: modelData
            scale: Qt.vector3d(0.25, 0.25, 0.25)
            materials: PrincipledMaterial { lighting: PrincipledMaterial.NoLighting
                baseColor: Math.sin(vista.tempo * 3 + index) > 0.3 ? "#ff3030" : "#401010" }
        }
    }

    // ---------------------------------------------------------------- o OUTDOOR de papel (com o menu impresso)
    Node {
        position: vista.centro
        Model {   // a placa de trás (chapa)
            source: "#Cube"
            scale: Qt.vector3d((vista.larg + 40) / 100, (vista.alt + 40) / 100, 0.18)
            materials: PrincipledMaterial { baseColor: "#2a2c30"; metalness: 0.6; roughness: 0.5 }
        }
        Model {   // o CARTAZ (papel impresso; a luz dos refletores bate nele de verdade)
            source: "#Rectangle"
            position.z: 10
            scale: Qt.vector3d(vista.larg / 100, vista.alt / 100, 1)
            materials: PrincipledMaterial {
                roughness: 0.9
                // (um pouco de brilho próprio: dá pra ler mesmo fora da luz dos refletores)
                emissiveMap: cartazTex
                emissiveFactor: Qt.vector3d(0.38, 0.38, 0.42)
                baseColorMap: Texture {
                    id: cartazTex
                    sourceItem: Item {
                        width: 1650; height: 1050
                        Rectangle {
                            anchors.fill: parent
                            gradient: Gradient {
                                orientation: Gradient.Horizontal
                                GradientStop { position: 0; color: "#0d5c68" }
                                GradientStop { position: 0.6; color: "#142446" }
                                GradientStop { position: 1; color: "#1e1440" }
                            }
                        }
                        Rectangle {   // o "sol" laranja da arte
                            x: 1060; y: 160; width: 520; height: 520; radius: 260
                            color: "#ff8a3a"
                            opacity: 0.9
                        }
                        Shape {   // um D20 de verdade (hexágono, triângulo da face e as arestas) por cima do sol
                            id: d20
                            x: 1320 - 210; y: 420 - 210; width: 420; height: 420
                            readonly property real r: 200
                            function v(a, f) { return Qt.point(210 + Math.cos((a - 90) * Math.PI / 180) * r * f,
                                                               210 + Math.sin((a - 90) * Math.PI / 180) * r * f) }
                            ShapePath {   // o corpo
                                strokeColor: "#14183a"; strokeWidth: 12; fillColor: "#1c2250"; joinStyle: ShapePath.RoundJoin
                                startX: d20.v(0, 1).x; startY: d20.v(0, 1).y
                                PathLine { x: d20.v(60, 1).x; y: d20.v(60, 1).y }
                                PathLine { x: d20.v(120, 1).x; y: d20.v(120, 1).y }
                                PathLine { x: d20.v(180, 1).x; y: d20.v(180, 1).y }
                                PathLine { x: d20.v(240, 1).x; y: d20.v(240, 1).y }
                                PathLine { x: d20.v(300, 1).x; y: d20.v(300, 1).y }
                                PathLine { x: d20.v(0, 1).x; y: d20.v(0, 1).y }
                            }
                            ShapePath {   // a face da frente (triângulo) e as arestas até as pontas
                                strokeColor: "#ff8a3a"; strokeWidth: 7; fillColor: "transparent"; joinStyle: ShapePath.RoundJoin
                                startX: d20.v(0, 0.56).x; startY: d20.v(0, 0.56).y
                                PathLine { x: d20.v(120, 0.56).x; y: d20.v(120, 0.56).y }
                                PathLine { x: d20.v(240, 0.56).x; y: d20.v(240, 0.56).y }
                                PathLine { x: d20.v(0, 0.56).x; y: d20.v(0, 0.56).y }
                                PathLine { x: d20.v(0, 1).x; y: d20.v(0, 1).y }
                                PathMove { x: d20.v(0, 0.56).x; y: d20.v(0, 0.56).y }
                                PathLine { x: d20.v(60, 1).x; y: d20.v(60, 1).y }
                                PathLine { x: d20.v(120, 0.56).x; y: d20.v(120, 0.56).y }
                                PathLine { x: d20.v(120, 1).x; y: d20.v(120, 1).y }
                                PathMove { x: d20.v(120, 0.56).x; y: d20.v(120, 0.56).y }
                                PathLine { x: d20.v(180, 1).x; y: d20.v(180, 1).y }
                                PathLine { x: d20.v(240, 0.56).x; y: d20.v(240, 0.56).y }
                                PathLine { x: d20.v(240, 1).x; y: d20.v(240, 1).y }
                                PathMove { x: d20.v(240, 0.56).x; y: d20.v(240, 0.56).y }
                                PathLine { x: d20.v(300, 1).x; y: d20.v(300, 1).y }
                                PathLine { x: d20.v(0, 0.56).x; y: d20.v(0, 0.56).y }
                            }
                            Text {
                                x: 210 - width / 2; y: 236 - height / 2
                                text: "20"
                                color: "#ffb060"
                                font.family: ponte.cores.fonte
                                font.pixelSize: 86
                            }
                        }
                        Text {
                            x: 1080; y: 700; width: 460
                            text: "Sua mesa de RPG,\nonde você estiver."
                            color: "#f2f2f2"; font.family: ponte.cores.fonte; font.pixelSize: 54
                            horizontalAlignment: Text.AlignHCenter
                        }
                        Text {   // título
                            x: 86; y: 40
                            text: "TAVERNA"
                            color: "#ffffff"
                            font.family: ponte.cores.fonte
                            font.pixelSize: 210
                            font.letterSpacing: 8
                        }
                        Rectangle { x: 92; y: 262; width: 300; height: 10; color: vista.destaque }
                        Repeater {   // o menu impresso
                            model: vista.opcoes
                            Item {
                                readonly property bool ehBotao: modelData.texto !== undefined
                                readonly property bool habilitado: modelData.ok === undefined || modelData.ok
                                readonly property bool aceso: vista.sobre === index && habilitado
                                x: vista.colX; width: vista.colLarg
                                y: modelData.fy * 1050 - height / 2
                                height: 90
                                Text {
                                    visible: parent.ehBotao
                                    anchors.verticalCenter: parent.verticalCenter
                                    anchors.verticalCenterOffset: modelData.det ? -12 : 0
                                    text: (parent.aceso ? "▸ " : "") + (modelData.texto || "")
                                    color: !parent.habilitado ? "#6a7a8a" : parent.aceso ? "#ffb040" : "#ffffff"
                                    font.family: ponte.cores.fonte
                                    font.pixelSize: 66
                                    font.letterSpacing: 2
                                }
                                Text {
                                    visible: !!modelData.det
                                    y: parent.height - 26
                                    text: modelData.det || ""
                                    color: "#a8c0d0"; font.pixelSize: 24
                                    width: vista.colLarg; elide: Text.ElideRight
                                }
                                Row {
                                    visible: !parent.ehBotao
                                    anchors.verticalCenter: parent.verticalCenter
                                    spacing: 16
                                    Text {
                                        text: (modelData.rotulo || "").toUpperCase(); color: vista.destaque
                                        font.family: ponte.cores.fonte; font.pixelSize: 34; font.letterSpacing: 12
                                    }
                                    Rectangle {
                                        width: 380; height: 3; color: vista.destaque; opacity: 0.6
                                        anchors.verticalCenter: parent.verticalCenter
                                    }
                                }
                            }
                        }
                        Image {   // o papel: emendas, rugas, sujeira, canto rasgado
                            anchors.fill: parent
                            source: vista.tex("papel_outdoor")
                        }
                    }
                }
            }
        }
        Repeater3D {   // as linhas clicáveis (invisíveis): o mouse é testado nelas
            model: vista.opcoes
            Model {
                property int opcao: index
                visible: modelData.texto !== undefined
                pickable: modelData.texto !== undefined
                source: "#Rectangle"
                position: Qt.vector3d(-vista.larg / 2 + (vista.colX + vista.colLarg / 2) / vista.pxPorUn,
                                      vista.alt / 2 - modelData.fy * vista.alt, 14)
                scale: Qt.vector3d(vista.colLarg / vista.pxPorUn / 100, 80 / vista.pxPorUn / 100, 1)
                materials: PrincipledMaterial {
                    lighting: PrincipledMaterial.NoLighting; baseColor: "black"; opacity: 0.01   // (0 some do teste do mouse)
                    alphaMode: PrincipledMaterial.Blend; depthDrawMode: Material.NeverDepthDraw
                }
            }
        }
        Model {   // passarela de manutenção embaixo do cartaz
            source: "#Cube"
            position: Qt.vector3d(0, -vista.alt / 2 - 40, 60)
            scale: Qt.vector3d((vista.larg + 100) / 100, 0.08, 1.2)
            materials: PrincipledMaterial { baseColor: "#24272c"; metalness: 0.8; roughness: 0.4 }
        }
        Repeater3D {   // pernas de ferro descendo
            model: [-0.36, 0, 0.36]
            Model {
                source: "#Cube"
                position: Qt.vector3d(modelData * vista.larg, -vista.alt / 2 - 800, -10)
                scale: Qt.vector3d(0.32, 15, 0.32)
                materials: PrincipledMaterial { baseColor: "#1e2024"; metalness: 0.8; roughness: 0.45 }
            }
        }
    }

    // ---------------------------------------------------------------- os 2 REFLETORES (miram a opção do mouse)
    component Refletor: Node {
        id: ref
        property vector3d alvo
        // a mira vai escorregando até o alvo a cada quadro (suave, sem pulo)
        property vector3d alvoSuave: Qt.vector3d(-560, 300, -338)
        Connections {
            target: vista
            function onTempoChanged() {
                var a = ref.alvo, s = ref.alvoSuave, k = 0.14
                if (Math.abs(a.x - s.x) + Math.abs(a.y - s.y) + Math.abs(a.z - s.z) > 0.5)
                    ref.alvoSuave = Qt.vector3d(s.x + (a.x - s.x) * k, s.y + (a.y - s.y) * k, s.z + (a.z - s.z) * k)
            }
        }
        // direção até o alvo → giro (y) e inclinação (x); a cabeça aponta pra -z
        readonly property vector3d dir: Qt.vector3d(alvoSuave.x - ref.x, alvoSuave.y - ref.y, alvoSuave.z - ref.z)
        Node {
            id: cabeca
            eulerRotation: Qt.vector3d(Math.atan2(ref.dir.y, Math.sqrt(ref.dir.x * ref.dir.x + ref.dir.z * ref.dir.z)) * 180 / Math.PI,
                                       Math.atan2(-ref.dir.x, -ref.dir.z) * 180 / Math.PI, 0)
            Model {   // a lata do refletor (aponta pra -z)
                geometry: Malha { pedido: "torno|20,-40; 34,-40; 40,30; 36,34; 0,34|0|16" }
                eulerRotation.x: -90
                materials: PrincipledMaterial { baseColor: "#2c2f36"; metalness: 0.8; roughness: 0.35 }
            }
            Model {   // a lente acesa
                source: "#Cylinder"
                position.z: -36
                eulerRotation.x: 90
                scale: Qt.vector3d(0.72, 0.02, 0.72)
                materials: PrincipledMaterial { lighting: PrincipledMaterial.NoLighting; baseColor: "#fff4d8" }
            }
            Model {   // o facho de luz no ar úmido
                geometry: Malha { pedido: "torno|36,0; 220,900|0|20" }
                eulerRotation.x: -90
                materials: PrincipledMaterial {
                    lighting: PrincipledMaterial.NoLighting
                    baseColor: "#fff0c8"
                    opacityMap: Texture { source: vista.tex("feixe_grad") }
                    opacity: 0.16
                    alphaMode: PrincipledMaterial.Blend
                    blendMode: PrincipledMaterial.Screen
                    cullMode: Material.NoCulling
                    depthDrawMode: Material.NeverDepthDraw
                }
            }
            SpotLight {
                color: "#fff0d0"
                brightness: 70
                coneAngle: 15
                innerConeAngle: 7
                quadraticFade: 0.0
                linearFade: 0.4
                castsShadow: false
            }
        }
    }
    Model {   // braço do refletor da esquerda
        source: "#Cube"
        position: Qt.vector3d(vista.centro.x - vista.larg / 2 - 60, vista.centro.y - vista.alt / 2 - 40, -150)
        scale: Qt.vector3d(0.12, 0.12, 2.2)
        materials: PrincipledMaterial { baseColor: "#1e2024"; metalness: 0.8; roughness: 0.4 }
    }
    Model {   // braço do refletor da direita
        source: "#Cube"
        position: Qt.vector3d(vista.centro.x + vista.larg / 2 + 60, vista.centro.y - vista.alt / 2 - 40, -150)
        scale: Qt.vector3d(0.12, 0.12, 2.2)
        materials: PrincipledMaterial { baseColor: "#1e2024"; metalness: 0.8; roughness: 0.4 }
    }
    Refletor { position: Qt.vector3d(vista.centro.x - vista.larg / 2 - 60, vista.centro.y - vista.alt / 2 - 20, -40); alvo: vista.alvoEsq }
    Refletor { position: Qt.vector3d(vista.centro.x + vista.larg / 2 + 60, vista.centro.y - vista.alt / 2 - 20, -40); alvo: vista.alvoDir }

    MouseArea {   // mouse no cartaz: os refletores miram a opção; clique escolhe
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
            if (i >= 0 && vista.opcoes[i].acao) ponte.escolher(vista.opcoes[i].acao)
        }
    }

    // ---------------------------------------------------------------- o helicóptero com holofote
    property real voo: -1
    Timer {
        running: vista.anima; repeat: true; interval: 6000
        onTriggered: { interval = 22000 + Math.random() * 16000; passa.restart() }
    }
    NumberAnimation { id: passa; target: vista; property: "voo"; from: 0; to: 1; duration: 16000 }
    Node {
        visible: vista.voo >= 0 && vista.voo < 1
        position: Qt.vector3d(3200 - vista.voo * 6400, 700 + Math.sin(vista.voo * 6) * 40, -1000)
        scale: Qt.vector3d(2.1, 2.1, 2.1)
        eulerRotation.y: 160
        eulerRotation.z: Math.sin(vista.voo * 9) * 3
        // (v0.58, o Manel achou "um cilindro voador") helicóptero detalhado — o bico aponta pra +x
        Model {   // fuselagem (bico arredondado na frente, afinando atrás)
            geometry: Malha { pedido: "torno|0,-120; 30,-112; 52,-80; 62,-20; 64,40; 56,95; 38,130; 0,150|0|14" }
            eulerRotation.z: -90
            materials: Lataria {}
        }
        Model {   // a cabine de vidro (acesa por dentro)
            source: "#Sphere"
            position: Qt.vector3d(92, 16, 0)
            scale: Qt.vector3d(0.95, 0.66, 0.9)
            materials: PrincipledMaterial { baseColor: "#203040"; roughness: 0.05; metalness: 0.2
                emissiveFactor: Qt.vector3d(0.08, 0.14, 0.2) }
        }
        Model {   // cauda (o tubo comprido)
            geometry: Malha { pedido: "torno|17,0; 7,270; 0,272|0|10" }
            position.x: -100
            eulerRotation.z: 90
            materials: Lataria {}
        }
        Model {   // aleta vertical do rabo
            source: "#Cube"
            position: Qt.vector3d(-362, 34, 0)
            eulerRotation.z: -18
            scale: Qt.vector3d(0.45, 0.72, 0.04)
            materials: Lataria {}
        }
        Model {   // estabilizador horizontal
            source: "#Cube"
            position: Qt.vector3d(-320, 4, 0)
            scale: Qt.vector3d(0.14, 0.03, 0.9)
            materials: Lataria {}
        }
        Model {   // rotor do rabo (girando)
            source: "#Cube"
            position: Qt.vector3d(-372, 42, 16)
            eulerRotation.z: vista.tempo * 3200
            scale: Qt.vector3d(0.03, 0.9, 0.02)
            materials: PrincipledMaterial { baseColor: "#101014" }
        }
        Repeater3D {   // esquis (dois tubos) + as pernas
            model: [-1, 1]
            Node {
                Model {
                    source: "#Cylinder"
                    position: Qt.vector3d(10, -82, modelData * 50)
                    eulerRotation.z: 90
                    scale: Qt.vector3d(0.05, 2.7, 0.05)
                    materials: Lataria {}
                }
                Repeater3D {
                    model: [-55, 70]
                    Model {
                        source: "#Cylinder"
                        position: Qt.vector3d(modelData, -62, parent.parent.modelData * 44)
                        eulerRotation.x: parent.parent.modelData * 14
                        scale: Qt.vector3d(0.035, 0.42, 0.035)
                        materials: Lataria {}
                    }
                }
            }
        }
        Model {   // mastro do rotor
            source: "#Cylinder"
            position: Qt.vector3d(10, 72, 0)
            scale: Qt.vector3d(0.12, 0.22, 0.12)
            materials: Lataria {}
        }
        Repeater3D {   // as 4 pás do rotor principal (girando)
            model: 4
            Model {
                source: "#Cube"
                position: Qt.vector3d(10, 86, 0)
                eulerRotation.y: vista.tempo * 2400 + index * 90
                scale: Qt.vector3d(4.8, 0.012, 0.16)
                materials: PrincipledMaterial { baseColor: "#0c0c10"; roughness: 0.6 }
            }
        }
        Model {   // o "borrão" das pás girando
            source: "#Cylinder"
            position: Qt.vector3d(10, 86, 0)
            scale: Qt.vector3d(4.8, 0.004, 4.8)
            materials: PrincipledMaterial { baseColor: "#9aa0b0"; opacity: 0.08; alphaMode: PrincipledMaterial.Blend }
        }
        Model {   // luz vermelha piscando no rabo
            source: "#Sphere"
            position: Qt.vector3d(-380, 72, 0)
            scale: Qt.vector3d(0.12, 0.12, 0.12)
            materials: PrincipledMaterial {
                lighting: PrincipledMaterial.NoLighting
                baseColor: Math.sin(vista.tempo * 8) > 0.5 ? "#ff3030" : "#300808"
            }
        }
        Repeater3D {   // luzes de navegação: verde de um lado, vermelha do outro, e o pisca branco embaixo
            model: [{z: 62, c: "#30ff60"}, {z: -62, c: "#ff3030"}]
            Model {
                source: "#Sphere"
                position: Qt.vector3d(20, -8, modelData.z)
                scale: Qt.vector3d(0.07, 0.07, 0.07)
                materials: PrincipledMaterial { lighting: PrincipledMaterial.NoLighting; baseColor: modelData.c }
            }
        }
        Model {
            source: "#Sphere"
            position: Qt.vector3d(-20, -60, 0)
            scale: Qt.vector3d(0.08, 0.08, 0.08)
            materials: PrincipledMaterial { lighting: PrincipledMaterial.NoLighting
                baseColor: Math.sin(vista.tempo * 13) > 0.85 ? "#ffffff" : "#202020" }
        }        Node {   // o holofote (embaixo do bico)
            position: Qt.vector3d(90, -50, 0)
            eulerRotation.z: 180 + Math.sin(vista.tempo * 0.8) * 18
            eulerRotation.x: Math.cos(vista.tempo * 0.6) * 12
            Model {
                geometry: Malha { pedido: "torno|6,0; 420,2600|0|16" }
                materials: PrincipledMaterial {
                    lighting: PrincipledMaterial.NoLighting
                    baseColor: "#e8f0ff"
                    opacityMap: Texture { source: vista.tex("feixe_grad") }
                    opacity: 0.2
                    alphaMode: PrincipledMaterial.Blend
                    blendMode: PrincipledMaterial.Screen
                    cullMode: Material.NoCulling
                    depthDrawMode: Material.NeverDepthDraw
                }
            }
            SpotLight {
                eulerRotation.x: 90
                color: "#e8f0ff"
                brightness: 40
                coneAngle: 12
                innerConeAngle: 4
                quadraticFade: 0.02
                linearFade: 0.2
            }
        }
    }
}
