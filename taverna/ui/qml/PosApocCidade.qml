// ☢ Pós-apocalíptico, tela 1 (v0.59.1, refeita a pedido do Manel): CIDADE TOMADA PELAS PLANTAS num DIA CINZA.
// Rua rachada com mato, prédios com janelas quebradas/tapadas e lojas fechadas, hera, árvores e moitas de folha,
// carros enferrujados (uma árvore crescendo de dentro de um), postes, semáforo caído e, lá no fundo, UMA RUA
// CRUZANDO com mais prédios. O MENU É PICHADO COM SPRAY na lateral de um ÔNIBUS ESCOLAR amarelo atravessado na
// rua como barricada (janelas tapadas com tábua, sacos de areia); no hover a tinta da opção escorre fresca.
// Um cervo atravessa a rua de vez em quando; corvos rodam lá no alto; raramente um zumbi cambaleia na rua do fundo.
// Medidas em centímetros.
import QtQuick
import QtQuick3D
import QtQuick3D.Helpers
import QtQuick3D.Particles3D

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

    readonly property string spray: "Sedgwick Ave Display"   // letra de pichação (OFL)
    // o menu pichado na lateral do ônibus (x/y em cm no ônibus; w/h o tamanho da pichação; px a altura da letra)
    readonly property var opcoes: [
        {titulo: "TAVERNA", x: 40, y: 266, w: 1080, h: 140, px: 136, cor: "#d42e1c", rot: -3},
        {rotulo: "MESTRE", x: -175, y: 188, w: 260, h: 44, px: 40, cor: "#f6f4ec", rot: -4},
        {texto: "Nova sessão", acao: "mestre_nova", x: -170, y: 150, w: 380, h: 48, px: 50, cor: "#141414", rot: 2},
        {texto: "Continuar", acao: "mestre_continuar", x: -175, y: 112, w: 360, h: 48, px: 50, cor: "#1d4fc4", rot: -2, ok: ponte.temUltima},
        {texto: "Abrir sessão", acao: "mestre_abrir", x: -165, y: 74, w: 380, h: 48, px: 48, cor: "#16702e", rot: 1},
        {rotulo: "JOGADOR", x: 175, y: 188, w: 280, h: 44, px: 40, cor: "#f6f4ec", rot: 3},
        {texto: "Entrar na sessão", acao: "jogador_entrar", x: 175, y: 146, w: 420, h: 48, px: 46, cor: "#6a1fa0", rot: -2},
        {texto: "Sair", acao: "sair", x: 160, y: 96, w: 240, h: 66, px: 70, cor: "#d42e1c", rot: 4}
    ]

    environment: SceneEnvironment {
        backgroundMode: SceneEnvironment.SkyBox                 // o céu nublado é fundo E luz ambiente
        lightProbe: Texture { source: vista.tex("pa_ceu"); mappingMode: Texture.LightProbe }
        probeExposure: 1.0
        antialiasingMode: SceneEnvironment.MSAA
        antialiasingQuality: vista.nivel === 2 ? SceneEnvironment.VeryHigh : SceneEnvironment.High
        fog: Fog { enabled: true; color: "#c3c6c2"; depthEnabled: true; depthNear: 2000; depthFar: 32000; density: 0.85 }
    }
    PerspectiveCamera {
        id: camera
        position: Qt.vector3d(0, 530, 1250)
        eulerRotation.x: -11
        fieldOfView: 50
        clipNear: 10
        clipFar: 40000
    }
    DirectionalLight {   // o sol atrás das nuvens: luz branca de cima, sombra bem fraca
        eulerRotation: Qt.vector3d(-62, -30, 0)
        color: "#f2f2ee"
        brightness: 0.7
        castsShadow: vista.nivel >= 1
        shadowFactor: 30
        shadowMapQuality: Light.ShadowMapQualityHigh
        shadowMapFar: 9000
    }

    // ---------------------------------------------------------------- materiais e texturas repetidos
    Texture { id: tFolhas; source: vista.tex("pa_folhas") }
    Texture { id: tCasca; source: vista.tex("pa_casca"); scaleV: 2; tilingModeHorizontal: Texture.Repeat; tilingModeVertical: Texture.Repeat }
    Texture { id: tCarro; source: vista.tex("pa_tinta_carro") }
    Texture { id: tCompensado; source: vista.tex("pa_compensado") }
    PrincipledMaterial { id: matFolhas; baseColorMap: tFolhas; alphaMode: PrincipledMaterial.Mask; alphaCutoff: 0.5
        cullMode: Material.NoCulling; roughness: 0.85 }
    PrincipledMaterial { id: matCapim; baseColorMap: Texture { source: vista.tex("pa_capim") }
        alphaMode: PrincipledMaterial.Mask; alphaCutoff: 0.5; cullMode: Material.NoCulling; roughness: 0.9 }
    PrincipledMaterial { id: matCasca; baseColorMap: tCasca; roughness: 0.95 }
    PrincipledMaterial { id: matBorracha; baseColor: "#181716"; roughness: 0.9 }
    PrincipledMaterial { id: matCalota; baseColor: "#8e8a80"; metalness: 0.6; roughness: 0.5 }
    PrincipledMaterial { id: matVidro; baseColor: "#262d35"; roughness: 0.06; metalness: 0.1 }
    PrincipledMaterial { id: matFarol; baseColor: "#c8ccc6"; roughness: 0.15 }
    PrincipledMaterial { id: matLanterna; baseColor: "#6a1610"; roughness: 0.25 }
    PrincipledMaterial { id: matPoste; baseColor: "#5a5a54"; metalness: 0.4; roughness: 0.75 }
    PrincipledMaterial { id: matCompensado; baseColorMap: tCompensado; roughness: 0.9 }
    PrincipledMaterial { id: matTabua; baseColorMap: Texture { source: vista.tex("pa_compensado"); scaleU: 0.4; scaleV: 0.3 } roughness: 0.9 }
    PrincipledMaterial { id: matSaco; baseColor: "#9c8c6a"; roughness: 0.95 }
    PrincipledMaterial { id: matFerrugem; baseColorMap: Texture { source: vista.tex("ferrugem") } roughness: 0.85; metalness: 0.2 }
    PrincipledMaterial { id: matEntulho; baseColorMap: Texture { source: vista.tex("pa_calcada") } baseColor: "#c8c4bc"; roughness: 0.95 }

    // ---------------------------------------------------------------- peças
    component Arvore: Node {   // tronco que afina, galhos e a copa feita de vários galhos de folha (instanciados)
        id: arv
        property real alto: 650
        property int semente: 0
        property real copa: 1
        Model { source: "#Cone"; scale: Qt.vector3d(0.44 * arv.copa, arv.alto / 100 * 1.15, 0.44 * arv.copa); materials: matCasca }
        Repeater3D {
            model: 5
            Node {
                position.y: arv.alto * (0.55 + 0.09 * index)
                eulerRotation.y: index * 72 + arv.semente * 41
                Model { source: "#Cone"; eulerRotation.z: -58; scale: Qt.vector3d(0.13 * arv.copa, 2.4 * arv.copa, 0.13 * arv.copa); materials: matCasca }
            }
        }
        Repeater3D {
            model: 6
            Model {
                readonly property real a: index * 1.05 + arv.semente
                source: "#Rectangle"
                position: index === 5 ? Qt.vector3d(0, arv.alto + 200 * arv.copa, 0)
                                      : Qt.vector3d(Math.cos(a) * 170 * arv.copa, arv.alto + (60 + (index % 2) * 90) * arv.copa, Math.sin(a) * 170 * arv.copa)
                scale: Qt.vector3d(arv.copa, arv.copa, arv.copa)
                instancing: RandomInstancing {
                    instanceCount: vista.nivel === 2 ? 22 : 13
                    randomSeed: arv.semente * 7 + index
                    position: InstanceRange { from: Qt.vector3d(-150, -105, -150); to: Qt.vector3d(150, 105, 150) }
                    rotation: InstanceRange { from: Qt.vector3d(-50, 0, -40); to: Qt.vector3d(50, 360, 40) }
                    scale: InstanceRange { from: Qt.vector3d(1.5, 1.5, 1); to: Qt.vector3d(2.5, 2.5, 1); proportional: true }
                }
                materials: matFolhas
                castsShadows: false
            }
        }
    }
    component Moita: Model {
        property int semente: 1
        property real tam: 1
        source: "#Rectangle"
        scale: Qt.vector3d(tam, tam, tam)
        instancing: RandomInstancing {
            instanceCount: 14
            randomSeed: semente
            position: InstanceRange { from: Qt.vector3d(-120, 40, -120); to: Qt.vector3d(120, 120, 120) }
            rotation: InstanceRange { from: Qt.vector3d(-40, 0, -30); to: Qt.vector3d(40, 360, 30) }
            scale: InstanceRange { from: Qt.vector3d(1.1, 1.1, 1); to: Qt.vector3d(1.9, 1.9, 1); proportional: true }
        }
        castsShadows: false
        materials: matFolhas
    }
    component Capim: Model {   // tufos de capim espalhados numa caixa
        property vector3d de
        property vector3d ate
        property int n: 40
        property int semente: 1
        property real tam: 1
        source: "#Rectangle"
        instancing: RandomInstancing {
            instanceCount: vista.nivel === 0 ? Math.round(n / 3) : n
            randomSeed: semente
            position: InstanceRange { from: de; to: ate }
            rotation: InstanceRange { from: Qt.vector3d(0, 0, 0); to: Qt.vector3d(0, 360, 0) }
            scale: InstanceRange { from: Qt.vector3d(0.5 * tam, 0.45 * tam, 1); to: Qt.vector3d(0.9 * tam, 0.75 * tam, 1) }
        }
        castsShadows: false
        materials: matCapim
    }
    component Carro: Node {
        id: car
        property color tinta: "#5f7d96"
        property bool arvore: false
        property bool queimado: false
        PrincipledMaterial { id: matLataria; baseColorMap: tCarro; baseColor: car.tinta
            roughness: car.queimado ? 0.95 : 0.5; metalness: car.queimado ? 0 : 0.25 }
        Model { source: "#Cube"; position.y: 62; scale: Qt.vector3d(4.4, 0.62, 1.78); materials: matLataria }
        Model { source: "#Cube"; position: Qt.vector3d(-25, 118, 0); scale: Qt.vector3d(2.3, 0.52, 1.6); materials: matLataria }
        Model { source: "#Rectangle"; position: Qt.vector3d(91.2, 118, 0); eulerRotation.y: 90; scale: Qt.vector3d(1.48, 0.44, 1); materials: matVidro; visible: !car.queimado }
        Model { source: "#Rectangle"; position: Qt.vector3d(-141.2, 118, 0); eulerRotation.y: -90; scale: Qt.vector3d(1.48, 0.44, 1); materials: matVidro; visible: !car.queimado }
        Repeater3D { model: [-1, 1]
            Model { source: "#Rectangle"; position: Qt.vector3d(-25, 118, modelData * 80.6); eulerRotation.y: modelData > 0 ? 0 : 180
                scale: Qt.vector3d(2.1, 0.42, 1); materials: matVidro; visible: !car.queimado } }
        Repeater3D { model: [-1, 1]
            Model { source: "#Cube"; position: Qt.vector3d(modelData * 224, 46, 0); scale: Qt.vector3d(0.1, 0.2, 1.84); materials: matBorracha } }
        Repeater3D { model: [-1, 1]
            Model { source: "#Cube"; position: Qt.vector3d(221, 74, modelData * 62); scale: Qt.vector3d(0.04, 0.16, 0.34); materials: matFarol } }
        Repeater3D { model: [-1, 1]
            Model { source: "#Cube"; position: Qt.vector3d(-221, 76, modelData * 66); scale: Qt.vector3d(0.04, 0.14, 0.3); materials: matLanterna } }
        Repeater3D { model: 4
            Node {
                position: Qt.vector3d(index < 2 ? 140 : -140, 30, index % 2 ? 80 : -80)
                Model { source: "#Cylinder"; eulerRotation.x: 90; scale: Qt.vector3d(0.62, 0.22, 0.58); materials: matBorracha }
                Model { source: "#Cylinder"; eulerRotation.x: 90; position.z: index % 2 ? 4 : -4; scale: Qt.vector3d(0.36, 0.2, 0.36)
                    materials: car.queimado ? matFerrugem : matCalota }
            }
        }
        Arvore { visible: car.arvore; position: Qt.vector3d(-25, 60, 0); alto: 560; semente: 3; copa: 1.1 }
    }
    component Poste: Node {
        id: pst
        property real lado: 1          // pra que lado o braço vai (sempre pra rua)
        property real torto: 0
        eulerRotation.z: torto
        Model { source: "#Cylinder"; position.y: 450; scale: Qt.vector3d(0.16, 9, 0.16); materials: matPoste }
        Model { source: "#Cylinder"; position.y: 40; scale: Qt.vector3d(0.26, 0.8, 0.26); materials: matPoste }
        Model { source: "#Cube"; position: Qt.vector3d(pst.lado * 110, 892, 0); scale: Qt.vector3d(2.2, 0.08, 0.08); materials: matPoste }
        Model { source: "#Cube"; position: Qt.vector3d(pst.lado * 215, 882, 0); scale: Qt.vector3d(0.6, 0.14, 0.3); materials: matPoste }
        Model { source: "#Cube"; position: Qt.vector3d(pst.lado * 215, 873, 0); scale: Qt.vector3d(0.5, 0.04, 0.24); materials: matFarol }
    }
    component Semaforo: Node {
        Model { source: "#Cylinder"; position.y: 300; scale: Qt.vector3d(0.14, 6, 0.14); materials: matPoste }
        Model { source: "#Cube"; position: Qt.vector3d(0, 520, 12); scale: Qt.vector3d(0.42, 1.1, 0.3); materials: matBorracha }
        Repeater3D { model: 3
            Node {
                position: Qt.vector3d(0, 556 - index * 36, 28)
                Model { source: "#Cylinder"; eulerRotation.x: 90; scale: Qt.vector3d(0.24, 0.02, 0.24)
                    materials: PrincipledMaterial { baseColor: ["#3a1410", "#3a3010", "#123a18"][index]; roughness: 0.2 } }
                Model { source: "#Cube"; position: Qt.vector3d(0, 10, 6); scale: Qt.vector3d(0.3, 0.02, 0.14); materials: matBorracha }
            }
        }
    }
    component Predio: Node {   // posto na frente da fachada (no chão), girado pra a fachada olhar pra rua (+z local)
        id: pr
        property real largura: 1400
        property real alto: 2400
        property real fundo: 1400
        property int estilo: 0
        property int loja: 0
        property bool temLoja: true
        property bool hera: false
        property real heraX: 0
        Model {
            source: "#Cube"
            position: Qt.vector3d(0, pr.alto / 2, -pr.fundo / 2)
            scale: Qt.vector3d(pr.largura / 100, pr.alto / 100, pr.fundo / 100)
            materials: PrincipledMaterial {
                baseColorMap: Texture { source: vista.tex("pa_predio" + pr.estilo); scaleU: pr.largura / 1400; scaleV: pr.alto / 1050
                    tilingModeHorizontal: Texture.Repeat; tilingModeVertical: Texture.Repeat }
                roughness: 0.9
            }
        }
        Model {   // a loja do térreo
            visible: pr.temLoja
            source: "#Rectangle"
            position: Qt.vector3d(0, 230, 1.5)
            scale: Qt.vector3d(pr.largura / 100, 4.6, 1)
            materials: PrincipledMaterial { baseColorMap: Texture { source: vista.tex("pa_loja" + pr.loja) } roughness: 0.75 }
        }
        Model {   // hera descendo do alto
            id: heraM
            visible: pr.hera
            readonly property real w: pr.largura * 0.6
            readonly property real h: pr.alto * 0.78
            source: "#Rectangle"
            position: Qt.vector3d(pr.heraX * pr.largura * 0.2, pr.alto - h / 2, 3)
            scale: Qt.vector3d(w / 100, h / 100, 1)
            materials: PrincipledMaterial {
                alphaMode: PrincipledMaterial.Mask; alphaCutoff: 0.5
                baseColorMap: Texture { source: vista.tex("pa_hera"); scaleU: Math.max(1, Math.round(heraM.w / (heraM.h * 0.5)))
                    tilingModeHorizontal: Texture.Repeat }
                roughness: 0.85
            }
        }
    }
    component Calcada: Model {
        property real su: 1
        property real sv: 1
        source: "#Cube"
        materials: PrincipledMaterial {
            baseColorMap: Texture { source: vista.tex("pa_calcada"); scaleU: su; scaleV: sv
                tilingModeHorizontal: Texture.Repeat; tilingModeVertical: Texture.Repeat }
            roughness: 0.95
        }
    }

    // ---------------------------------------------------------------- chão: a rua, a rua que cruza lá no fundo, calçadas
    Model {
        source: "#Rectangle"; eulerRotation.x: -90; position: Qt.vector3d(0, -3, -9000); scale: Qt.vector3d(600, 600, 1)
        materials: PrincipledMaterial { baseColor: "#6a6a5a"; roughness: 1 }
    }
    Model {
        source: "#Rectangle"; eulerRotation.x: -90; position: Qt.vector3d(0, 0, -2900); scale: Qt.vector3d(22, 88, 1)
        materials: PrincipledMaterial {
            baseColorMap: Texture { source: vista.tex("pa_asfalto"); scaleV: 8; tilingModeHorizontal: Texture.Repeat; tilingModeVertical: Texture.Repeat }
            roughness: 0.92
        }
    }
    Node {   // a rua que cruza (as faixas correm em x)
        position: Qt.vector3d(0, 0.8, -8400)
        eulerRotation.y: 90
        Model {
            source: "#Rectangle"; eulerRotation.x: -90; scale: Qt.vector3d(22, 300, 1)
            materials: PrincipledMaterial {
                baseColorMap: Texture { source: vista.tex("pa_asfalto"); scaleV: 27; tilingModeHorizontal: Texture.Repeat; tilingModeVertical: Texture.Repeat }
                roughness: 0.92
            }
        }
    }
    Calcada { position: Qt.vector3d(-1300, 9, -2700); scale: Qt.vector3d(4, 0.18, 84); sv: 21 }
    Calcada { position: Qt.vector3d(1300, 9, -2700); scale: Qt.vector3d(4, 0.18, 84); sv: 21 }
    Calcada { position: Qt.vector3d(-7550, 9, -7100); scale: Qt.vector3d(129, 0.18, 4); su: 32 }
    Calcada { position: Qt.vector3d(7550, 9, -7100); scale: Qt.vector3d(129, 0.18, 4); su: 32 }
    Calcada { position: Qt.vector3d(0, 9, -9700); scale: Qt.vector3d(300, 0.18, 4); su: 75 }

    // ---------------------------------------------------------------- os prédios
    Repeater3D {   // dos dois lados da rua
        model: 12
        Predio {
            readonly property int k: Math.floor(index / 2)
            readonly property int lado: index % 2 ? 1 : -1
            position: Qt.vector3d(lado * 1500, 18, 800 - k * 1400)
            eulerRotation.y: lado < 0 ? 90 : -90
            largura: 1400
            fundo: 1200
            alto: (lado < 0 ? [2400, 3600, 1900, 3100, 2600, 3400] : [3200, 2100, 3800, 2400, 2900, 2000])[k]
            estilo: (lado < 0 ? [0, 2, 1, 3, 0, 1] : [1, 3, 0, 2, 3, 0])[k]
            loja: (lado < 0 ? [0, 1, 2, 3, 4, 5] : [3, 5, 1, 0, 2, 4])[k]
            hera: (lado < 0 ? [true, false, true, true, false, true] : [false, true, true, false, true, true])[k]
            heraX: vista.acaso(index, 4) * 2 - 1
        }
    }
    Repeater3D {   // a fileira do outro lado da rua que cruza, de frente pra gente
        model: [[-7000, 2400, 1600, 3], [-4900, 1800, 1200, 0], [-2700, 2600, 2100, 1], [-300, 2200, 1400, 2],
                [2300, 3000, 1800, 0], [4800, 2000, 1100, 3], [7000, 2400, 1500, 1]]
        Predio {
            position: Qt.vector3d(modelData[0], 18, -9900)
            largura: modelData[1]
            alto: modelData[2]
            estilo: modelData[3]
            loja: index % 6
            hera: index % 3 !== 1
            heraX: vista.acaso(index, 8) * 2 - 1
        }
    }
    Model {   // pichação grande no prédio do fim da rua
        source: "#Rectangle"
        position: Qt.vector3d(-300, 820, -9895)
        scale: Qt.vector3d(16, 3, 1)
        materials: PrincipledMaterial {
            alphaMode: PrincipledMaterial.Blend; roughness: 0.8
            baseColorMap: Texture { sourceItem: Item { width: 1600; height: 300
                Text { id: sobrev; anchors.centerIn: parent; anchors.horizontalCenterOffset: -110; text: "SOBREVIVENTES"; font.family: vista.spray; font.pixelSize: 170; color: "#f2f0e8" }
                Rectangle { x: sobrev.x + sobrev.width + 30; y: 140; width: 150; height: 26; radius: 10; color: "#f2f0e8" }
                Rectangle { x: sobrev.x + sobrev.width + 120; y: 110; width: 70; height: 26; radius: 10; rotation: 40; color: "#f2f0e8" }
                Rectangle { x: sobrev.x + sobrev.width + 120; y: 170; width: 70; height: 26; radius: 10; rotation: -40; color: "#f2f0e8" } } }
        }
    }
    Repeater3D {   // prédios altos lá longe, sumindo na névoa
        model: [[-9000, -17000, 2500, 6500], [-3500, -19500, 3000, 9000], [2500, -18000, 2200, 7000],
                [8000, -20000, 3500, 8000], [13000, -17500, 2000, 5000], [-14000, -19000, 3000, 6000]]
        Model {
            source: "#Cube"
            position: Qt.vector3d(modelData[0], modelData[3] / 2, modelData[1])
            scale: Qt.vector3d(modelData[2] / 100, modelData[3] / 100, 20)
            materials: PrincipledMaterial {
                baseColorMap: Texture { source: vista.tex("pa_predio2"); scaleU: modelData[2] / 1400; scaleV: modelData[3] / 1050
                    tilingModeHorizontal: Texture.Repeat; tilingModeVertical: Texture.Repeat }
                roughness: 0.9
            }
        }
    }
    Model {   // entulho de uma fachada que desabou
        source: "#Cube"
        position: Qt.vector3d(-1330, 40, -3400)
        instancing: RandomInstancing {
            instanceCount: 40; randomSeed: 5
            position: InstanceRange { from: Qt.vector3d(-170, -20, -450); to: Qt.vector3d(170, 40, 450) }
            rotation: InstanceRange { from: Qt.vector3d(0, 0, 0); to: Qt.vector3d(360, 360, 360) }
            scale: InstanceRange { from: Qt.vector3d(0.3, 0.2, 0.3); to: Qt.vector3d(1.1, 0.6, 0.9) }
        }
        materials: matEntulho
    }

    // ---------------------------------------------------------------- carros, postes, semáforos, árvores, mato
    Carro { position: Qt.vector3d(-850, 0, 230); eulerRotation.y: 72; tinta: "#a8463a" }          // fechando a barricada
    Carro { position: Qt.vector3d(-720, 0, -1900); eulerRotation.y: 8; tinta: "#5f7d96" }
    Carro { position: Qt.vector3d(720, 0, -3100); eulerRotation.y: -164; tinta: "#6a9a8e"; arvore: true }
    Carro { position: Qt.vector3d(-560, 0, -4700); eulerRotation.y: 32; tinta: "#3a3430"; queimado: true }
    Carro { position: Qt.vector3d(330, 0, -5900); eulerRotation.y: 100; tinta: "#cbbf9c" }
    Carro { position: Qt.vector3d(1250, 18, -1300); eulerRotation.y: 86; tinta: "#d8d4cc" }        // em cima da calçada
    Carro { position: Qt.vector3d(-900, 0, -8250); eulerRotation.y: 3; tinta: "#a8463a" }          // na rua que cruza
    Carro { position: Qt.vector3d(1150, 0, -8800); eulerRotation.y: 176; tinta: "#5f7d96" }
    Repeater3D { model: [-200, -2800, -5400]
        Poste { position: Qt.vector3d(-1180, 18, modelData); lado: 1 } }
    Poste { position: Qt.vector3d(1180, 18, -1500); lado: -1 }
    Poste { position: Qt.vector3d(1180, 18, -4100); lado: -1; torto: 13 }
    Semaforo { position: Qt.vector3d(1180, 18, -6960) }
    Semaforo { position: Qt.vector3d(-150, 22, -3600); eulerRotation: Qt.vector3d(0, 30, 86) }    // caído atravessado
    Arvore { position: Qt.vector3d(-1300, 18, -1100); alto: 700; semente: 1; copa: 1.1 }
    Arvore { position: Qt.vector3d(1300, 18, -2300); alto: 650; semente: 2 }
    Arvore { position: Qt.vector3d(-1300, 18, -4300); alto: 800; semente: 4; copa: 1.2 }
    Arvore { position: Qt.vector3d(1300, 18, -5400); alto: 600; semente: 5 }
    Arvore { position: Qt.vector3d(-1350, 18, -7100); alto: 900; semente: 6; copa: 1.4 }
    Arvore { position: Qt.vector3d(1500, 18, -9750); alto: 750; semente: 7; copa: 1.2 }
    Moita { position: Qt.vector3d(-1350, 18, -2600); semente: 11 }
    Moita { position: Qt.vector3d(1350, 18, -2600); semente: 12 }
    Moita { position: Qt.vector3d(-1250, 18, 300); semente: 13; tam: 1.2 }
    Moita { position: Qt.vector3d(1380, 18, -3900); semente: 14 }
    Moita { position: Qt.vector3d(1150, 0, 500); semente: 15; tam: 1.3 }
    Moita { position: Qt.vector3d(-600, 18, -9750); semente: 16 }
    Moita { position: Qt.vector3d(900, 18, -9750); semente: 17; tam: 1.2 }
    Capim { de: Qt.vector3d(-1150, 26, -6800); ate: Qt.vector3d(-1050, 26, 900); n: 140; semente: 1 }
    Capim { de: Qt.vector3d(1050, 26, -6800); ate: Qt.vector3d(1150, 26, 900); n: 140; semente: 2 }
    Capim { de: Qt.vector3d(-1490, 44, -6800); ate: Qt.vector3d(-1110, 44, 900); n: 80; semente: 3 }
    Capim { de: Qt.vector3d(1110, 44, -6800); ate: Qt.vector3d(1490, 44, 900); n: 80; semente: 4 }
    Capim { de: Qt.vector3d(-1000, 20, -6800); ate: Qt.vector3d(1000, 20, -300); n: 120; semente: 5; tam: 0.7 }
    Capim { de: Qt.vector3d(-1050, 28, 250); ate: Qt.vector3d(1050, 28, 900); n: 90; semente: 6; tam: 1.1 }
    Capim { de: Qt.vector3d(-4000, 44, -9900); ate: Qt.vector3d(4000, 44, -9500); n: 90; semente: 7 }
    Capim { de: Qt.vector3d(-4000, 44, -7300); ate: Qt.vector3d(4000, 44, -6900); n: 70; semente: 8 }

    // ---------------------------------------------------------------- a barricada do lado direito do ônibus
    Repeater3D { model: 14   // sacos de areia
        Model { source: "#Sphere"
            readonly property int fila: index < 5 ? 0 : (index < 9 ? 1 : 2)
            readonly property int pos: index < 5 ? index : (index < 9 ? index - 5 : index - 9)
            position: Qt.vector3d(650 + pos * 92 + fila * 46, 15 + fila * 27, -190)
            eulerRotation.y: (vista.acaso(index, 3) - 0.5) * 20
            scale: Qt.vector3d(0.55, 0.32, 0.36); materials: matSaco } }
    Repeater3D { model: [[700, -40], [810, -10], [760, 70]]   // tambores enferrujados
        Model { source: "#Cylinder"; position: Qt.vector3d(modelData[0], 45, modelData[1]); scale: Qt.vector3d(0.3, 0.9, 0.3); materials: matFerrugem } }
    Repeater3D { model: 3   // pneus empilhados
        Model { source: "#Cylinder"; position: Qt.vector3d(990, 12 + index * 22, -40); scale: Qt.vector3d(0.42, 0.2, 0.42); materials: matBorracha } }

    // ---------------------------------------------------------------- O ÔNIBUS ESCOLAR com o menu pichado
    Node {
        id: onibus
        position: Qt.vector3d(-30, 0, 0)
        eulerRotation: Qt.vector3d(0, 16, -1.2)
        Model {   // a carroceria
            source: "#Cube"; position.y: 190; scale: Qt.vector3d(12, 3, 2.5)
            materials: PrincipledMaterial { baseColorMap: Texture { source: vista.tex("pa_amarelo") } roughness: 0.6; metalness: 0.1 }
        }
        Model {   // a lateral (pintura, porta, vãos das janelas, rodas)
            source: "#Rectangle"; position: Qt.vector3d(0, 190, 125.4); scale: Qt.vector3d(12, 3, 1)
            materials: PrincipledMaterial { baseColorMap: Texture { source: vista.tex("pa_lateral") } roughness: 0.55; metalness: 0.1 }
        }
        Model {   // a frente
            source: "#Rectangle"; position: Qt.vector3d(-600.4, 190, 0); eulerRotation.y: -90; scale: Qt.vector3d(2.5, 3, 1)
            materials: PrincipledMaterial { baseColorMap: Texture { source: vista.tex("pa_frente") } roughness: 0.5; metalness: 0.1 }
        }
        Model {   // o teto
            source: "#Rectangle"; position: Qt.vector3d(0, 340.4, 0); eulerRotation.x: -90; scale: Qt.vector3d(12, 2.5, 1)
            materials: PrincipledMaterial { baseColorMap: Texture { source: vista.tex("pa_teto") } roughness: 0.85 }
        }
        Model { source: "#Cube"; position.y: 207; scale: Qt.vector3d(12.04, 0.06, 2.55); materials: matBorracha }   // frisos
        Model { source: "#Cube"; position.y: 44; scale: Qt.vector3d(12.04, 0.1, 2.55); materials: matBorracha }
        Model { source: "#Cube"; position: Qt.vector3d(-607, 58, 0); scale: Qt.vector3d(0.16, 0.34, 2.6); materials: matBorracha }   // para-choques
        Model { source: "#Cube"; position: Qt.vector3d(607, 58, 0); scale: Qt.vector3d(0.16, 0.34, 2.6); materials: matBorracha }
        Node {   // retrovisor
            position: Qt.vector3d(-612, 300, 110)
            Model { source: "#Cylinder"; eulerRotation.z: 60; position: Qt.vector3d(-20, -10, 0); scale: Qt.vector3d(0.04, 0.5, 0.04); materials: matPoste }
            Model { source: "#Cube"; position: Qt.vector3d(-42, -40, 10); scale: Qt.vector3d(0.08, 0.36, 0.22); materials: matBorracha }
        }
        Repeater3D {   // rodas (a do lado de cá)
            model: [-430, 400]
            Node {
                position: Qt.vector3d(modelData, 48, 118)
                Model { source: "#Cylinder"; eulerRotation.x: 90; scale: Qt.vector3d(1.04, 0.32, 0.96); materials: matBorracha }
                Model { source: "#Cylinder"; eulerRotation.x: 90; position.z: 10; scale: Qt.vector3d(0.6, 0.2, 0.6); materials: matCalota }
                Model { source: "#Cylinder"; eulerRotation.x: 90; position.z: 14; scale: Qt.vector3d(0.22, 0.2, 0.22); materials: matBorracha }
            }
        }
        Repeater3D {   // as janelas: tapadas com chapa, com tábuas, ou com o vidro sujo
            model: 8
            Node {
                readonly property string tipo: ["chapa", "vidro", "tabuas", "chapa", "quebrada", "tabuas", "vidro", "chapa"][index]
                position: Qt.vector3d(-417.5 + index * 125, 268, 126)
                Model { visible: parent.tipo === "vidro"; source: "#Rectangle"; scale: Qt.vector3d(0.98, 0.98, 1); materials: matVidro }
                Model { visible: parent.tipo === "chapa"; source: "#Cube"; position.z: 1.5
                    eulerRotation.z: (vista.acaso(index, 9) - 0.5) * 6; scale: Qt.vector3d(1.16, 1.12, 0.02); materials: matCompensado }
                Repeater3D {
                    model: parent.tipo === "tabuas" ? 3 : 0
                    Model { source: "#Cube"; position: Qt.vector3d(0, -34 + index * 34, 1.5 + index * 0.4)
                        eulerRotation.z: (vista.acaso(index, 11) - 0.5) * 16; scale: Qt.vector3d(1.32, 0.26, 0.025); materials: matTabua }
                }
            }
        }
        Repeater3D { model: [-73, 73]   // tábuas em X na porta
            Model { source: "#Cube"; position: Qt.vector3d(-552, 185, 128); eulerRotation.z: modelData
                scale: Qt.vector3d(2.9, 0.17, 0.025); materials: matTabua } }
        Repeater3D { model: 7   // em cima: sacos de areia, pneus, caixote
            Model { source: "#Sphere"; position: Qt.vector3d(-380 + index * 58, 352, 80 - (index % 2) * 20); eulerRotation.y: index * 17
                scale: Qt.vector3d(0.62, 0.32, 0.4); materials: matSaco } }
        Repeater3D { model: 3
            Model { source: "#Cylinder"; position: Qt.vector3d(330, 352 + index * 22, -20); scale: Qt.vector3d(0.7, 0.2, 0.7); materials: matBorracha } }
        Model { source: "#Cube"; position: Qt.vector3d(110, 385, -40); eulerRotation.y: 20; scale: Qt.vector3d(0.9, 0.85, 0.9); materials: matCompensado }
        Model {   // hera subindo pela traseira
            source: "#Rectangle"; position: Qt.vector3d(560, 140, 127.5); eulerRotation.z: 180; scale: Qt.vector3d(1.0, 1.9, 1)
            materials: PrincipledMaterial { alphaMode: PrincipledMaterial.Mask; alphaCutoff: 0.5; baseColorMap: Texture { source: vista.tex("pa_hera") }
                roughness: 0.85 }
        }
        Repeater3D {   // as PICHAÇÕES (cada opção é um texto de spray; no hover, a tinta escorre fresca)
            model: vista.opcoes
            Model {
                id: pich
                readonly property bool ehBotao: modelData.texto !== undefined
                readonly property bool habilitado: modelData.ok === undefined || modelData.ok
                readonly property bool acesa: vista.sobre === index && habilitado
                property real escorre: 0                     // 0..1: o comprimento dos escorridos
                property int opcao: index
                readonly property color tinta: modelData.cor
                readonly property real folga: ehBotao ? 50 : 0          // espaço embaixo pros escorridos
                pickable: ehBotao
                NumberAnimation on escorre { running: pich.acesa; from: 0; to: 1; duration: 1400; easing.type: Easing.OutQuad }
                onAcesaChanged: if (!acesa) escorre = 0
                source: "#Rectangle"
                position: Qt.vector3d(modelData.x, modelData.y - folga / 2, 131 + index * 0.05)
                eulerRotation.z: modelData.rot
                scale: Qt.vector3d(modelData.w / 100, (modelData.h + folga) / 100, 1)
                materials: PrincipledMaterial {
                    alphaMode: PrincipledMaterial.Blend
                    roughness: pich.acesa ? 0.1 : 0.7                 // tinta fresca brilha
                    baseColorMap: Texture {
                        sourceItem: Item {
                            width: modelData.w * 3; height: (modelData.h + pich.folga) * 3
                            Repeater {   // o borrifo em volta da letra (spray)
                                model: 4
                                Text {
                                    anchors.centerIn: letra
                                    anchors.horizontalCenterOffset: [-4, 4, 0, 0][index]
                                    anchors.verticalCenterOffset: [0, 0, -4, 4][index]
                                    text: letra.text; font: letra.font; color: letra.color; opacity: 0.16
                                }
                            }
                            Text {
                                id: letra
                                anchors.horizontalCenter: parent.horizontalCenter
                                anchors.verticalCenter: parent.top
                                anchors.verticalCenterOffset: modelData.h * 1.5
                                text: modelData.titulo || modelData.rotulo || modelData.texto
                                font.family: vista.spray
                                font.pixelSize: modelData.px * 3
                                color: pich.habilitado ? modelData.cor : Qt.rgba(0.32, 0.3, 0.26, 0.55)
                                font.bold: true
                                style: Text.Outline                                   // contorno de tag
                                styleColor: modelData.cor === "#141414" ? "#f6f4ec" : "#141414"
                            }
                            Repeater {   // os escorridos (crescem no hover)
                                model: pich.ehBotao ? 9 : 0
                                Rectangle {
                                    readonly property real r: vista.acaso(index + pich.opcao * 10, 7)
                                    x: letra.x + letra.width * (0.05 + index * 0.105) + r * 18
                                    y: letra.y + letra.height * 0.7
                                    width: 8 + r * 8
                                    height: pich.escorre * (30 + r * 110)
                                    radius: width / 2
                                    color: pich.tinta
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    Capim { de: Qt.vector3d(-650, 26, -120); ate: Qt.vector3d(650, 26, 260); n: 70; semente: 9; tam: 1.2 }

    // ---------------------------------------------------------------- poeira/sementes voando
    ParticleSystem3D {
        running: vista.anima
        position: Qt.vector3d(0, 400, -800)
        SpriteParticle3D {
            id: polen
            sprite: Texture { source: vista.tex("sprite_brilho") }
            maxAmount: vista.nivel === 2 ? 220 : 90
            color: "#c0f4f2ea"
            blendMode: SpriteParticle3D.Screen
            fadeInDuration: 1500; fadeOutDuration: 1500
            billboard: true
        }
        ParticleEmitter3D {
            particle: polen
            emitRate: vista.nivel === 2 ? 22 : 9
            lifeSpan: 10000
            particleScale: 0.7; particleScaleVariation: 0.4
            shape: ParticleShape3D { type: ParticleShape3D.Cube; extents: Qt.vector3d(1800, 400, 1500) }
            velocity: VectorDirection3D { direction: Qt.vector3d(18, 2, 0); directionVariation: Qt.vector3d(10, 8, 10) }
        }
    }

    // ---------------------------------------------------------------- corvos rodando lá no alto
    Repeater3D {
        model: 6
        Node {
            readonly property real ang: vista.tempo * 0.12 + index * 1.05
            visible: vista.anima
            position: Qt.vector3d(Math.cos(ang) * (1300 + index * 90), 1500 + (index % 3) * 120, -8800 + Math.sin(ang) * 900)
            eulerRotation.y: -ang * 57.3
            Model { source: "#Sphere"; scale: Qt.vector3d(0.12, 0.08, 0.32); materials: matBorracha }
            Repeater3D { model: [-1, 1]
                Model { source: "#Rectangle"; eulerRotation.x: 90
                    eulerRotation.z: modelData * 25 * Math.sin(vista.tempo * 8 + index)
                    position.x: modelData * 34; scale: Qt.vector3d(0.6, 0.22, 1)
                    materials: PrincipledMaterial { baseColor: "#121212"; cullMode: Material.NoCulling; roughness: 0.9 } } }
        }
    }

    // ---------------------------------------------------------------- o CERVO atravessando a rua de vez em quando
    Node {
        id: cervo
        readonly property real ciclo: 38
        readonly property real fase: (vista.tempo % ciclo) / ciclo        // anda de 0 a 0.4 do ciclo; no resto, sumido
        readonly property real t: Math.min(1, fase / 0.4)
        visible: vista.anima && fase < 0.4
        position: Qt.vector3d(-1350 + t * 2700, 0, -2600)
        readonly property real passo: Math.sin(vista.tempo * 9)
        PrincipledMaterial { id: matCervo; baseColor: "#7a5634"; roughness: 0.9 }
        Model { source: "#Sphere"; position.y: 125; scale: Qt.vector3d(1.5, 0.62, 0.55); materials: matCervo }
        Model { source: "#Cylinder"; position: Qt.vector3d(70, 170, 0); eulerRotation.z: -35; scale: Qt.vector3d(0.16, 0.7, 0.16); materials: matCervo }
        Model { source: "#Sphere"; position: Qt.vector3d(98, 205, 0); scale: Qt.vector3d(0.42, 0.24, 0.22); materials: matCervo }
        Model { source: "#Sphere"; position: Qt.vector3d(-74, 140, 0); scale: Qt.vector3d(0.14, 0.14, 0.12)
            materials: PrincipledMaterial { baseColor: "#e8e0d0" } }   // o rabinho branco
        Repeater3D { model: [-1, 1]   // galhada
            Node { position: Qt.vector3d(92, 222, modelData * 10); eulerRotation.x: modelData * 25
                Model { source: "#Cylinder"; position.y: 25; scale: Qt.vector3d(0.035, 0.5, 0.035); materials: PrincipledMaterial { baseColor: "#d8c8a8" } }
                Model { source: "#Cylinder"; position: Qt.vector3d(8, 30, 0); eulerRotation.z: -40; scale: Qt.vector3d(0.03, 0.25, 0.03); materials: PrincipledMaterial { baseColor: "#d8c8a8" } } } }
        Repeater3D { model: 4   // pernas balançando
            Model { source: "#Cylinder"
                position: Qt.vector3d(index < 2 ? 50 : -50, 60, index % 2 ? 16 : -16)
                eulerRotation.z: cervo.passo * 20 * ((index % 2) ? 1 : -1) * (index < 2 ? 1 : -1)
                scale: Qt.vector3d(0.06, 1.2, 0.06); materials: matCervo } }
    }
    // ---------------------------------------------------------------- RARAMENTE: um zumbi cambaleando na rua do fundo
    Node {
        id: zumbi
        readonly property real ciclo: 55
        readonly property int volta: Math.floor(vista.tempo / ciclo)
        readonly property real fase: (vista.tempo % ciclo) / ciclo
        readonly property bool vez: vista.acaso(volta, 31) < 0.25            // 1 a cada ~4 voltas
        visible: vista.anima && vez && fase < 0.6
        position: Qt.vector3d(-1900 + fase / 0.6 * 3600, 0, -8450)
        eulerRotation.y: 0
        eulerRotation.z: 6 * Math.sin(vista.tempo * 2.3)
        Model { source: "#Cube"; position.y: 125; scale: Qt.vector3d(0.6, 0.85, 0.35); materials: PrincipledMaterial { baseColor: "#3a3a30"; roughness: 0.95 } }
        Model { source: "#Sphere"; position: Qt.vector3d(12, 185, 0); scale: Qt.vector3d(0.32, 0.36, 0.32); materials: PrincipledMaterial { baseColor: "#6a7050" } }
        Repeater3D { model: [-1, 1]   // braços pra frente
            Model { source: "#Cube"; position: Qt.vector3d(36, 145, modelData * 30); eulerRotation.z: -70 + 10 * Math.sin(vista.tempo * 2 + modelData)
                scale: Qt.vector3d(0.12, 0.65, 0.12); materials: PrincipledMaterial { baseColor: "#4a4a3c" } } }
        Repeater3D { model: [-1, 1]
            Model { source: "#Cube"; position: Qt.vector3d(0, 45, modelData * 14); eulerRotation.z: 12 * Math.sin(vista.tempo * 2.3 + modelData)
                scale: Qt.vector3d(0.13, 0.9, 0.13); materials: PrincipledMaterial { baseColor: "#2a2a24" } } }
    }

    // ---------------------------------------------------------------- mouse
    MouseArea {
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: vista.sobre >= 0 ? Qt.PointingHandCursor : Qt.ArrowCursor
        function qual(x, y) {
            var r = vista.pick(x, y)
            var i = r.objectHit && r.objectHit.opcao !== undefined ? r.objectHit.opcao : -1
            if (i >= 0 && (!vista.opcoes[i].acao || (vista.opcoes[i].ok !== undefined && !vista.opcoes[i].ok))) return -1
            return i
        }
        onPositionChanged: (m) => vista.sobre = qual(m.x, m.y)
        onExited: vista.sobre = -1
        onClicked: (m) => {
            var i = qual(m.x, m.y)
            if (i >= 0) ponte.escolher(vista.opcoes[i].acao)
        }
    }
}
