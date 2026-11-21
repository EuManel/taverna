// 🚀 Futurista, tela 2 (v0.58, pacote do Manel): CABINE DE NAVE. Painel de controle na frente cheio de botõezinhos
// piscando, janelão pro espaço com um planeta girando e uma estação espacial passando devagar. As opções são
// HOLOGRAMAS que sobem dos projetores do console: parados têm interferência (tremem, falham, linhas de varredura);
// o mouse FIRMA o holograma (para de tremer e acende).
import QtQuick
import QtQuick3D
import QtQuick3D.Helpers

View3D {
    id: vista
    property int nivel: ponte.nivel
    readonly property bool anima: nivel >= 1
    function tex(n) { return ponte.textura(n) }
    function acaso(i, k) { var s = Math.sin(i * 12.9898 + k * 78.233) * 43758.5453; return s - Math.floor(s) }
    camera: camera
    readonly property bool menuProprio: true
    readonly property bool tituloProprio: true
    property int sobre: -1

    property real tempo: 0
    NumberAnimation on tempo { from: 0; to: 1000; duration: 1000000; loops: Animation.Infinite; running: vista.anima }

    readonly property var opcoes: [
        {titulo: "TAVERNA", y: 640, w: 560, h: 120, cor: "#5ae8ff"},
        {rotulo: "MESTRE", y: 545, w: 240, h: 40, cor: "#5ae8ff"},
        {texto: "Nova sessão", acao: "mestre_nova", y: 490, w: 400, h: 62, cor: "#5ae8ff"},
        {texto: "Continuar sessão", acao: "mestre_continuar", y: 420, w: 460, h: 62, cor: "#7affc8",
         det: ponte.temUltima ? ponte.ultimaAventura : "", ok: ponte.temUltima},
        {texto: "Abrir sessão…", acao: "mestre_abrir", y: 350, w: 400, h: 62, cor: "#5ae8ff"},
        {rotulo: "JOGADOR", y: 290, w: 240, h: 40, cor: "#5ae8ff"},
        {texto: "Entrar na sessão", acao: "jogador_entrar", y: 235, w: 460, h: 62, cor: "#ffc86a",
         det: ponte.servidor !== "" ? "da última vez: " + ponte.servidor : ""},
        {texto: "Sair", acao: "sair", y: 165, w: 240, h: 62, cor: "#ff6a7a"}
    ]

    environment: SceneEnvironment {
        backgroundMode: SceneEnvironment.Color
        clearColor: "#020308"
        antialiasingMode: SceneEnvironment.MSAA
        antialiasingQuality: vista.nivel === 2 ? SceneEnvironment.VeryHigh : SceneEnvironment.High
        tonemapMode: SceneEnvironment.TonemapModeNone
    }
    PerspectiveCamera {
        id: camera
        position: Qt.vector3d(0, 430, 900)
        eulerRotation.x: -9
        fieldOfView: 50
        clipNear: 10
        clipFar: 20000
    }
    DirectionalLight { eulerRotation: Qt.vector3d(-30, -30, 0); color: "#9ab0ff"; brightness: 2.2 }
    DirectionalLight { eulerRotation: Qt.vector3d(-60, 160, 0); color: "#3a4a7a"; brightness: 1.2 }   // preenchimento (de trás)   // luz do planeta
    PointLight { position: Qt.vector3d(0, 260, 380); color: "#3ac8ff"; brightness: 4; quadraticFade: 0.5 }   // brilho do console

    // ---------------------------------------------------------------- O ESPAÇO (lá fora)
    Model {   // fundo de estrelas e nebulosa (desliza bem devagar: a nave anda)
        source: "#Rectangle"
        position: Qt.vector3d(0, 600, -9000)
        scale: Qt.vector3d(260, 130, 1)
        materials: PrincipledMaterial {
            lighting: PrincipledMaterial.NoLighting
            baseColorMap: Texture { source: vista.tex("estrelas_nave"); positionU: vista.tempo * 0.002 }
        }
    }
    Node {   // o PLANETA
        position: Qt.vector3d(-1500, 700, -5200)
        Model {   // a atmosfera (brilho atrás)
            source: "#Rectangle"
            position.z: -900
            scale: Qt.vector3d(40, 40, 1)
            materials: PrincipledMaterial {
                lighting: PrincipledMaterial.NoLighting
                baseColorMap: Texture { source: vista.tex("sprite_brilho") }
                baseColor: "#6a8aff"
                alphaMode: PrincipledMaterial.Blend
                blendMode: PrincipledMaterial.Screen
                depthDrawMode: Material.NeverDepthDraw
            }
        }
        Model {
            source: "#Sphere"
            scale: Qt.vector3d(14, 14, 14)
            eulerRotation: Qt.vector3d(12, vista.tempo * 2, 8)
            materials: PrincipledMaterial {
                baseColorMap: Texture { source: vista.tex("planeta") }
                roughness: 0.9
            }
        }
        Model {   // anel do planeta
            geometry: Malha { pedido: "toro|1|0.02|1|96|4" }
            eulerRotation: Qt.vector3d(14, 0, 18)
            scale: Qt.vector3d(1150, 60, 1150)
            materials: PrincipledMaterial { baseColor: "#a8b8e8"; roughness: 0.8; opacity: 0.7; alphaMode: PrincipledMaterial.Blend }
        }
    }
    Node {   // a ESTAÇÃO ESPACIAL passando devagar
        id: estacao
        property real t: (vista.tempo % 160) / 160
        position: Qt.vector3d(2600 - estacao.t * 5200, 1100, -3600)
        eulerRotation: Qt.vector3d(70, 0, 20)
        Model {   // o anel girando
            geometry: Malha { pedido: "toro|1|0.06|1|64|8" }
            eulerRotation.y: vista.tempo * 8
            scale: Qt.vector3d(260, 260, 260)
            materials: PrincipledMaterial { baseColor: "#8a909c"; metalness: 0.7; roughness: 0.4 }
        }
        Model { source: "#Cylinder"; scale: Qt.vector3d(0.7, 2.2, 0.7); materials: PrincipledMaterial { baseColor: "#9aa0ac"; metalness: 0.7; roughness: 0.4 } }
        Repeater3D {   // raios do anel
            model: 4
            Model {
                source: "#Cube"
                eulerRotation.y: index * 45 + vista.tempo * 8
                scale: Qt.vector3d(5.2, 0.12, 0.12)
                materials: PrincipledMaterial { baseColor: "#6a707c"; metalness: 0.7; roughness: 0.5 }
            }
        }
        Model {   // painéis solares
            source: "#Cube"
            position.y: 170
            scale: Qt.vector3d(5, 0.04, 1.4)
            materials: PrincipledMaterial { baseColor: "#1a2a5a"; metalness: 0.5; roughness: 0.3 }
        }
        Repeater3D {   // luzinhas piscando na estação
            model: 6
            Model {
                source: "#Sphere"
                position: Qt.vector3d(Math.cos(index) * 262, 0, Math.sin(index) * 262)
                scale: Qt.vector3d(0.08, 0.08, 0.08)
                materials: PrincipledMaterial {
                    lighting: PrincipledMaterial.NoLighting
                    baseColor: Math.sin(vista.tempo * 4 + index * 1.7) > 0.6 ? (index % 2 ? "#ff4a4a" : "#4aff8a") : "#202020"
                }
            }
        }
    }

    // ---------------------------------------------------------------- A CABINE (a moldura da janela e o console)
    component Casco: PrincipledMaterial {
        baseColorMap: Texture { source: vista.tex("painel_nave"); scaleU: 2; scaleV: 2; tilingModeHorizontal: Texture.Repeat; tilingModeVertical: Texture.Repeat }
        metalness: 0.25
        roughness: 0.5
    }
    // colunas da janela (inclinadas, como um para-brisa) e a viga de cima
    Model { source: "#Cube"; position: Qt.vector3d(-760, 520, -200); eulerRotation.z: -14; scale: Qt.vector3d(1.6, 11, 1.4); materials: Casco {} }
    Model { source: "#Cube"; position: Qt.vector3d(760, 520, -200); eulerRotation.z: 14; scale: Qt.vector3d(1.6, 11, 1.4); materials: Casco {} }
    Model { source: "#Cube"; position: Qt.vector3d(0, 1060, -200); scale: Qt.vector3d(18, 1.8, 1.6); materials: Casco {} }
    Model { source: "#Cube"; position: Qt.vector3d(0, 1160, 200); eulerRotation.x: -15; scale: Qt.vector3d(20, 0.4, 8); materials: Casco {} }   // teto
    Repeater3D {   // painéis laterais (paredes da cabine)
        model: [-1, 1]
        Model {
            source: "#Cube"
            position: Qt.vector3d(modelData * 980, 500, 300)
            eulerRotation.y: modelData * 18
            scale: Qt.vector3d(0.4, 12, 9)
            materials: Casco {}
        }
    }
    Repeater3D {   // filetes de luz nas colunas
        model: [-1, 1]
        Model {
            source: "#Cube"
            position: Qt.vector3d(modelData * 728, 520, -128)
            eulerRotation.z: modelData * 14
            scale: Qt.vector3d(0.06, 10, 0.02)
            materials: PrincipledMaterial { lighting: PrincipledMaterial.NoLighting; baseColor: "#3ac8ff" }
        }
    }
    // o CONSOLE: tampo inclinado + frente
    Node {   // o tampo inclinado, com os botõezinhos e telinhas em cima dele
    position: Qt.vector3d(0, 90, 260)
    eulerRotation.x: 22
    Model { source: "#Cube"; scale: Qt.vector3d(14, 0.5, 4.2); materials: Casco {} }
    Model { source: "#Cube"; position: Qt.vector3d(0, -40, 440); scale: Qt.vector3d(15, 2.4, 1); materials: Casco {} }
    Repeater3D {   // botõezinhos piscando no console
        model: 36
        Model {
            readonly property real c: index % 12
            readonly property real l: Math.floor(index / 12)
            source: "#Cube"
            position: Qt.vector3d(c < 6 ? -460 + c * 30 : 300 + (c - 6) * 30, 27, -120 + l * 34)
            scale: Qt.vector3d(0.14, 0.06, 0.14)
            materials: PrincipledMaterial {
                lighting: PrincipledMaterial.NoLighting
                baseColor: Math.sin(vista.tempo * (1 + vista.acaso(index, 1) * 3) + index) > 0.2
                           ? ["#3ac8ff", "#ff4a6a", "#ffc84a", "#4aff8a"][index % 4] : "#10141c"
            }
        }
    }
    Repeater3D {   // telinhas no console (gráficos de radar)
        model: [-1, 1]
        Model {
            source: "#Rectangle"
            position: Qt.vector3d(modelData * 250, 26, 70)
            eulerRotation.x: -90
            scale: Qt.vector3d(1.3, 0.8, 1)
            materials: PrincipledMaterial {
                lighting: PrincipledMaterial.NoLighting
                baseColorMap: Texture {
                    sourceItem: Rectangle {
                        width: 256; height: 160; color: "#04121a"; border.color: "#3ac8ff"; border.width: 3
                        Repeater { model: 3; Rectangle { anchors.centerIn: parent; width: 40 + index * 45; height: width; radius: width / 2; color: "transparent"; border.color: "#1a6a8a"; border.width: 2 } }
                        Rectangle {   // a varredura do radar
                            anchors.centerIn: parent; width: 2; height: 70; color: "#7affff"
                            transformOrigin: Item.Bottom; anchors.verticalCenterOffset: -35
                            rotation: vista.tempo * 120 * modelData
                        }
                        Rectangle { x: 60 + modelData * 30; y: 50; width: 6; height: 6; radius: 3; color: "#ff4a6a" }
                    }
                }
            }
        }
    }
    }

    // ---------------------------------------------------------------- os HOLOGRAMAS (as opções)
    Repeater3D {   // projetores no console e o cone de luz subindo
        model: [-1, 1]
        Node {
            position: Qt.vector3d(modelData * 120, 120, 230)
            Model { source: "#Cylinder"; scale: Qt.vector3d(0.5, 0.12, 0.5); materials: PrincipledMaterial { baseColor: "#2a3040"; metalness: 0.8; roughness: 0.3 } }
            Model { source: "#Cylinder"; position.y: 7; scale: Qt.vector3d(0.3, 0.02, 0.3); materials: PrincipledMaterial { lighting: PrincipledMaterial.NoLighting; baseColor: "#7affff" } }
        }
    }
    Model {   // o feixe do projetor (luz subindo, larga em cima)
        source: "#Rectangle"
        position: Qt.vector3d(0, 280, 200)
        scale: Qt.vector3d(4.2, 3.2, 1)
        opacity: 0.22 + 0.05 * Math.sin(vista.tempo * 7)
        materials: PrincipledMaterial {
            lighting: PrincipledMaterial.NoLighting
            alphaMode: PrincipledMaterial.Blend
            blendMode: PrincipledMaterial.Screen
            depthDrawMode: Material.NeverDepthDraw
            baseColorMap: Texture {
                sourceItem: Item {
                    width: 128; height: 128
                    Rectangle {
                        anchors.fill: parent
                        gradient: Gradient {
                            GradientStop { position: 0; color: "#00000000" }
                            GradientStop { position: 1; color: "#3a9ad8" }
                        }
                    }
                }
            }
        }
    }
    component Holo: Node {
        id: h
        property var d
        property int i: 0
        readonly property bool ehBotao: d.texto !== undefined
        readonly property bool habilitado: d.ok === undefined || d.ok
        readonly property bool firme: (vista.sobre === i && habilitado) || d.titulo !== undefined
        property real f: firme ? 1 : 0
        Behavior on f { NumberAnimation { duration: 260 } }
        // a interferência: tremidinha de lado, falha (some por um instante) e desliza
        readonly property real ruido: (1 - f) * (vista.acaso(i, Math.floor(vista.tempo * 9)) > 0.86 ? 1 : 0)
        readonly property real falha: (1 - f) * (vista.acaso(i + 7, Math.floor(vista.tempo * 5)) > 0.93 ? 1 : 0)
        position: Qt.vector3d(ruido * (vista.acaso(i, vista.tempo) - 0.5) * 24, 130 + d.y * 0.52, 200)
        scale: Qt.vector3d(0.52, 0.52, 0.52)
        Model {
            property int opcao: h.i
            pickable: h.ehBotao
            source: "#Rectangle"
            scale: Qt.vector3d(h.d.w / 100, h.d.h / 100, 1)
            opacity: (h.d.titulo ? 1 : h.habilitado ? 0.55 + 0.45 * h.f : 0.3) * (1 - h.falha * 0.8)
            materials: PrincipledMaterial {
                lighting: PrincipledMaterial.NoLighting
                alphaMode: PrincipledMaterial.Blend
                blendMode: PrincipledMaterial.Screen
                depthDrawMode: Material.NeverDepthDraw
                cullMode: Material.NoCulling
                baseColor: Qt.rgba(0.9 + 0.5 * h.f, 0.9 + 0.5 * h.f, 0.9 + 0.5 * h.f, 1)
                baseColorMap: Texture {
                    sourceItem: Item {
                        width: h.d.w * 2; height: h.d.h * 2
                        readonly property color c: h.d.cor
                        Rectangle {   // a "tela" do holograma (só nos botões)
                            visible: h.ehBotao
                            anchors.fill: parent
                            color: Qt.rgba(parent.c.r, parent.c.g, parent.c.b, 0.10 + 0.12 * h.f)
                            border.width: 3
                            border.color: Qt.rgba(parent.c.r, parent.c.g, parent.c.b, 0.6 + 0.4 * h.f)
                            Repeater {   // cantinhos
                                model: 4
                                Rectangle {
                                    x: index % 2 ? parent.width - 26 : 4; y: index < 2 ? 4 : parent.height - 8
                                    width: 22; height: 4; color: Qt.lighter(h.d.cor, 1.3)
                                }
                            }
                        }
                        Text {
                            anchors.centerIn: parent
                            anchors.verticalCenterOffset: h.d.det ? -10 : 0
                            text: h.d.titulo || h.d.rotulo || h.d.texto
                            font.family: ponte.cores.fonte
                            font.pixelSize: h.d.titulo ? 170 : h.d.rotulo ? 40 : 60
                            font.letterSpacing: h.d.rotulo ? 14 : h.d.titulo ? 10 : 2
                            font.bold: true
                            color: Qt.lighter(h.d.cor, 1.25)
                            style: Text.Outline
                            styleColor: Qt.rgba(parent.c.r, parent.c.g, parent.c.b, 0.6)
                        }
                        Text {
                            visible: !!h.d.det
                            anchors.horizontalCenter: parent.horizontalCenter
                            anchors.bottom: parent.bottom; anchors.bottomMargin: 6
                            text: h.d.det || ""
                            font.pixelSize: 20
                            color: h.d.cor
                        }
                    }
                }
            }
        }
        Model {   // linhas de varredura descendo (somem quando firma)
            source: "#Rectangle"
            position.z: 1
            scale: Qt.vector3d(h.d.w / 100, h.d.h / 100, 1)
            opacity: (h.d.titulo ? 0.25 : 0.5) * (1 - h.f * 0.8)
            materials: PrincipledMaterial {
                lighting: PrincipledMaterial.NoLighting
                alphaMode: PrincipledMaterial.Blend
                depthDrawMode: Material.NeverDepthDraw
                cullMode: Material.NoCulling
                baseColor: "#020308"
                baseColorMap: Texture {
                    source: vista.tex("linhas_holo")
                    scaleU: h.d.w / 8; scaleV: h.d.h / 6
                    tilingModeHorizontal: Texture.Repeat; tilingModeVertical: Texture.Repeat
                    positionV: vista.tempo * 0.6
                }
            }
        }
    }
    Repeater3D { model: vista.opcoes; Holo { d: modelData; i: index } }
    MouseArea {   // mouse nos hologramas: firma; clique escolhe
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
}
