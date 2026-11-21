// 🌆 Futurista, tela 1 (v0.58, pacote do Manel): BECO DE NEON NA CHUVA. No fundo do beco, a parede com o título
// e CADA OPÇÃO É UMA PLACA DE NEON: apagada ela fica só com o tubo fraquinho; o mouse LIGA a placa piscando
// ("tz-tz") até firmar, e a luz dela pinta a parede e a POÇA embaixo (as placas são espelhadas por baixo do chão
// e aparecem só através da poça = reflexo). Vapor saindo do bueiro, fios pendurados, letreiros de fundo com
// palavras inventadas, chuva.
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
    readonly property bool menuProprio: true
    readonly property bool tituloProprio: true
    property int sobre: -1

    property real tempo: 0
    NumberAnimation on tempo { from: 0; to: 1000; duration: 1000000; loops: Animation.Infinite; running: vista.anima }

    readonly property real fundoZ: -1900         // a fachada do outro lado da rua (com as placas)
    // cada placa é de um "estabelecimento" diferente: fonte, moldura, inclinação e posição próprias (bagunça
    // cyberpunk, muita informação). Fontes: Orbitron/Bebas vêm com o Taverna; as outras são do sistema (se faltar,
    // o Qt usa uma parecida).
    readonly property var opcoes: [
        {titulo: "TAVERNA", y: 760, x: 0, cor: "#ff3cbe", w: 640, h: 150, fonte: "Orbitron", px: 200, moldura: "dupla"},
        {rotulo: "MESTRE", y: 650, x: -40, cor: "#4ee8ff", w: 260, h: 44, fonte: "Consolas", px: 40, moldura: "seta"},
        {texto: "Nova sessão", acao: "mestre_nova", y: 575, x: -70, rot: 3, cor: "#ff4f8a", w: 430, h: 80,
         fonte: "Bebas Neue", px: 84, moldura: "tubo"},
        {texto: "Continuar sessão", acao: "mestre_continuar", y: 480, x: 60, rot: -2, cor: "#4ee8ff", w: 540, h: 78,
         fonte: "Consolas", px: 58, moldura: "terminal", det: ponte.temUltima ? ponte.ultimaAventura : "", ok: ponte.temUltima},
        {texto: "Abrir sessão…", acao: "mestre_abrir", y: 385, x: -40, rot: -4, cor: "#c070ff", w: 460, h: 86,
         fonte: "Segoe Script", px: 62, moldura: "redonda"},
        {rotulo: "JOGADOR", y: 312, x: 50, cor: "#4ee8ff", w: 260, h: 44, fonte: "Consolas", px: 40, moldura: "seta"},
        {texto: "Entrar na sessão", acao: "jogador_entrar", y: 240, x: 20, rot: 2, cor: "#ffb03a", w: 540, h: 80,
         fonte: "Impact", px: 66, moldura: "cantos", det: ponte.servidor !== "" ? "da última vez: " + ponte.servidor : ""},
        {texto: "SAIR", acao: "sair", y: 150, x: 150, rot: 0, cor: "#ff3a3a", w: 200, h: 76,
         fonte: "Courier New", px: 64, moldura: "exit"}
    ]

    environment: SceneEnvironment {
        backgroundMode: SceneEnvironment.Color
        clearColor: "#05040a"
        antialiasingMode: SceneEnvironment.MSAA
        antialiasingQuality: vista.nivel === 2 ? SceneEnvironment.VeryHigh : SceneEnvironment.High
        tonemapMode: SceneEnvironment.TonemapModeNone
        fog: Fog {
            enabled: true
            color: "#0e0a1a"
            depthEnabled: true
            depthNear: 3200
            depthFar: 9000
        }
    }
    PerspectiveCamera {
        id: camera
        position: Qt.vector3d(0, 400, 900)
        eulerRotation.x: 12
        fieldOfView: 52
        clipNear: 10
        clipFar: 20000
    }
    DirectionalLight {   // a noite (bem fraquinha: quem ilumina são os neons)
        eulerRotation: Qt.vector3d(-40, 20, 0)
        color: "#6a7ab8"
        brightness: 1.9
    }
    PointLight { position: Qt.vector3d(0, 160, 50); color: "#8a6aff"; brightness: 6; quadraticFade: 0.4 }   // clarão no chão molhado
    PointLight { position: Qt.vector3d(-300, 500, 200); color: "#ff3cbe"; brightness: 9; quadraticFade: 0.25 }
    PointLight { position: Qt.vector3d(300, 300, 400); color: "#3ad8ff"; brightness: 9; quadraticFade: 0.25 }

    // ---------------------------------------------------------------- paredes, chão molhado e a POÇA
    component Parede: PrincipledMaterial {
        property real su: 3
        property real sv: 2
        baseColorMap: Texture { source: vista.tex("concreto_cyber"); scaleU: su; scaleV: sv; tilingModeHorizontal: Texture.Repeat; tilingModeVertical: Texture.Repeat }
        roughness: 0.55
        specularAmount: 0.6
    }
    // ESCALA DE GENTE: o olho fica a 400 (≈1,70 m; 1 m ≈ 235). Você está em pé no beco; o beco SAI NUMA RUA de
    // verdade (duas mãos, carros em tamanho real passando na sua frente) e, do outro lado da rua, a FACHADA de um
    // prédio de lojas, com vitrines acesas embaixo e as placas das opções em cima.
    readonly property real bocaZ: -200
    readonly property real escPlaca: 2.3            // as placas da fachada são grandes (estão do outro lado da rua)
    readonly property real topoLojas: 660    // onde acabam as vitrines e começam as placas
    Model { source: "#Rectangle"; position: Qt.vector3d(0, 1500, vista.fundoZ); scale: Qt.vector3d(90, 30, 1); materials: Parede { su: 11; sv: 5 } }   // a fachada do outro lado
    Model { source: "#Rectangle"; position: Qt.vector3d(-560, 1500, 700); eulerRotation.y: 90; scale: Qt.vector3d(18, 30, 1); materials: Parede { su: 2.25; sv: 5 } }
    Model { source: "#Rectangle"; position: Qt.vector3d(560, 1500, 700); eulerRotation.y: -90; scale: Qt.vector3d(18, 30, 1); materials: Parede { su: 2.25; sv: 5 } }
    Repeater3D {   // quina das paredes na boca do beco (a espessura do prédio, vista de frente)
        model: [-1, 1]
        Model { source: "#Cube"; position: Qt.vector3d(modelData * 640, 1500, vista.bocaZ); scale: Qt.vector3d(1.6, 30, 0.1); materials: Parede { su: 0.2; sv: 5 } }
    }
    Repeater3D {   // janelas dos apartamentos lá em cima na fachada (umas acesas)
        model: 30
        Model {
            source: "#Rectangle"
            position: Qt.vector3d(-2250 + (index % 10) * 500, 2150 + Math.floor(index / 10) * 330, vista.fundoZ + 2)
            scale: Qt.vector3d(1.8, 1.9, 1)
            materials: PrincipledMaterial {
                lighting: PrincipledMaterial.NoLighting
                baseColor: vista.acaso(index, 3) > 0.55 ? ["#ffcf8a", "#8ad8ff", "#ff8ad0", "#c8a8ff"][index % 4] : "#0c0a14"
            }
        }
    }
    component Asfalto: PrincipledMaterial {
        baseColorMap: Texture { source: vista.tex("chao_beco"); scaleU: 3; scaleV: 3; tilingModeHorizontal: Texture.Repeat; tilingModeVertical: Texture.Repeat }
        roughness: 0.18                  // molhado: brilha
        specularAmount: 1
    }
    // o chão do beco em volta da poça (opaco) — a poça é um buraco "de vidro" que mostra o reflexo
    Model { source: "#Rectangle"; eulerRotation.x: -90; position: Qt.vector3d(0, 0, 950); scale: Qt.vector3d(12, 13, 1); materials: Asfalto {} }
    Model { source: "#Rectangle"; eulerRotation.x: -90; position: Qt.vector3d(-430, 0, 100); scale: Qt.vector3d(2.6, 4, 1); materials: Asfalto {} }
    Model { source: "#Rectangle"; eulerRotation.x: -90; position: Qt.vector3d(430, 0, 100); scale: Qt.vector3d(2.6, 4, 1); materials: Asfalto {} }
    Model { source: "#Rectangle"; eulerRotation.x: -90; position: Qt.vector3d(0, 0, -150); scale: Qt.vector3d(12, 1, 1); materials: Asfalto {} }
    Model {   // a POÇA: vidro escuro transparente por cima do mundo espelhado
        source: "#Rectangle"
        eulerRotation.x: -90
        position: Qt.vector3d(0, 0, 100)
        scale: Qt.vector3d(6, 4, 1)
        materials: PrincipledMaterial {
            baseColor: "#0a0a14"
            opacity: 0.3
            alphaMode: PrincipledMaterial.Blend
            roughness: 0.02
            specularAmount: 1
        }
    }
    Model {   // o "fundo" embaixo da poça (pra não ver o vazio)
        source: "#Rectangle"
        eulerRotation.x: -90
        position: Qt.vector3d(0, -4000, -1000)
        scale: Qt.vector3d(60, 60, 1)
        materials: PrincipledMaterial { lighting: PrincipledMaterial.NoLighting; baseColor: "#04030a" }
    }

    // ---------------------------------------------------------------- A RUA (bem iluminada, carros passando)
    Model {   // calçada de cá (na boca do beco)
        source: "#Cube"; position: Qt.vector3d(0, 15, -325); scale: Qt.vector3d(120, 0.3, 2.5)
        materials: PrincipledMaterial { baseColor: "#4a4a58"; roughness: 0.3 }
    }
    Model {   // o asfalto da rua (duas mãos)
        source: "#Rectangle"; eulerRotation.x: -90
        position: Qt.vector3d(0, -1, -1025); scale: Qt.vector3d(120, 11.5, 1)
        materials: PrincipledMaterial {
            baseColorMap: Texture { source: vista.tex("chao_beco"); scaleU: 24; scaleV: 2; tilingModeHorizontal: Texture.Repeat; tilingModeVertical: Texture.Repeat }
            baseColor: "#b0b0c8"; roughness: 0.1; specularAmount: 1
        }
    }
    Repeater3D {   // faixa tracejada no meio da rua
        model: 20
        Model {
            source: "#Rectangle"; eulerRotation.x: -90
            position: Qt.vector3d(-6000 + index * 600, 0.5, -1025); scale: Qt.vector3d(3, 0.16, 1)
            materials: PrincipledMaterial { baseColor: "#d8c860"; roughness: 0.3 }
        }
    }
    Model {   // a calçada do outro lado
        source: "#Cube"; position: Qt.vector3d(0, 15, -1750); scale: Qt.vector3d(120, 0.3, 3)
        materials: PrincipledMaterial { baseColor: "#4a4a58"; roughness: 0.3 }
    }
    Repeater3D {   // VITRINES das lojas: caixilho de metal, tubo de neon em cima, prateleiras com produtos, balcão,
                   // gente dentro, porta de vidro; umas com a porta de enrolar meio abaixada
        model: [{x: -1150, w: 620, c: "#ff6ab0", grade: 0.35, t: 6}, {x: -380, w: 680, c: "#ffd08a", grade: 0, t: 0},
                {x: 380, w: 560, c: "#6ae8ff", grade: 0, t: 3}, {x: 1150, w: 640, c: "#b08aff", grade: 0.5, t: 7},
                {x: -1950, w: 600, c: "#8aff9a", grade: 0.2, t: 4}, {x: 1950, w: 620, c: "#ffb06a", grade: 0, t: 1}]
        Node {
            id: loja
            readonly property var d: modelData
            readonly property color c: d.cor || d.c
            position: Qt.vector3d(d.x, 0, vista.fundoZ + 4)
            Model {   // o vidro com a loja lá dentro
                source: "#Rectangle"; position.y: 300; scale: Qt.vector3d(loja.d.w / 100, 6, 1)
                materials: PrincipledMaterial {
                    lighting: PrincipledMaterial.NoLighting
                    baseColorMap: Texture {
                        sourceItem: Rectangle {
                            id: vit
                            width: loja.d.w / 2; height: 300
                            gradient: Gradient {
                                GradientStop { position: 0; color: Qt.darker(loja.c, 1.2) }
                                GradientStop { position: 0.75; color: Qt.darker(loja.c, 2.6) }
                                GradientStop { position: 1; color: Qt.darker(loja.c, 4) }
                            }
                            Repeater {   // prateleiras com produtos coloridos
                                model: 3
                                Item {
                                    y: 40 + index * 52; width: vit.width; height: 50
                                    Rectangle { anchors.bottom: parent.bottom; width: parent.width; height: 4; color: "#1a1420" }
                                    Repeater {
                                        model: Math.floor(vit.width / 16)
                                        Rectangle {
                                            readonly property real a: vista.acaso(index + loja.d.x, parent.parent.y)
                                            x: 4 + index * 16; anchors.bottom: parent.bottom; anchors.bottomMargin: 4
                                            width: 10; height: 12 + a * 22; radius: a > 0.7 ? 5 : 1
                                            color: ["#ff5a8a", "#ffe08a", "#5ae8ff", "#ffffff", "#8aff9a", "#b08aff"][Math.floor(a * 6)]
                                            opacity: 0.85
                                        }
                                    }
                                }
                            }
                            Repeater {   // gente (cabeça + corpo)
                                model: 2
                                Item {
                                    x: vit.width * (0.25 + index * 0.4); y: 130 + index * 8
                                    Rectangle { x: 8; width: 26; height: 28; radius: 13; color: "#120a16" }
                                    Rectangle { y: 24; width: 42; height: 150; radius: 14; color: "#120a16" }
                                }
                            }
                            Rectangle { y: 220; width: vit.width; height: 80; color: "#0e0a12"; opacity: 0.92 }   // balcão
                            Rectangle { y: 220; width: vit.width; height: 4; color: Qt.lighter(loja.c, 1.3) }      // filete de luz no balcão
                            Rectangle { x: vit.width * 0.72; width: 6; height: 300; color: "#24202c" }              // a porta
                            Rectangle { x: vit.width * 0.72 + 30; y: 150; width: 4; height: 40; color: "#c8c8d0" }  // puxador
                            Rectangle {   // reflexo no vidro (faixa diagonal)
                                x: vit.width * 0.1; y: -40; width: 26; height: 400; rotation: 24
                                color: "#ffffff"; opacity: 0.08
                            }
                        }
                    }
                }
            }
            Model {   // porta de enrolar (aço corrugado) meio abaixada
                visible: loja.d.grade > 0
                source: "#Rectangle"
                position: Qt.vector3d(0, 600 - loja.d.grade * 300, 3)
                scale: Qt.vector3d(loja.d.w / 100 + 0.04, loja.d.grade * 6, 1)
                materials: PrincipledMaterial {
                    baseColorMap: Texture {
                        sourceItem: Rectangle {
                            width: 128; height: 128; color: "#5a5c66"
                            Repeater { model: 16; Rectangle { y: index * 8; width: 128; height: 3; color: "#2c2c34" } }
                            Text { anchors.centerIn: parent; text: "✕ 404 ✕"; rotation: -8; font.pixelSize: 26; font.bold: true; color: "#ff3a8a"; opacity: 0.8 }   // pichação
                        }
                    }
                    roughness: 0.5; metalness: 0.6
                }
            }
            Repeater3D {   // caixilho de metal (as duas laterais e a viga de cima)
                model: [{x: -1, y: 300, sx: 0.2, sy: 6.2}, {x: 1, y: 300, sx: 0.2, sy: 6.2}, {x: 0, y: 610, sx: loja.d.w / 100 + 0.2, sy: 0.25}]
                Model {
                    source: "#Cube"
                    position: Qt.vector3d(modelData.x * loja.d.w / 2, modelData.y, 6)
                    scale: Qt.vector3d(modelData.sx, modelData.sy, 0.2)
                    materials: PrincipledMaterial { baseColor: "#2a2c34"; metalness: 0.8; roughness: 0.35 }
                }
            }
            Model {   // tubo de neon em cima da vitrine
                source: "#Cube"; position: Qt.vector3d(0, 636, 14)
                scale: Qt.vector3d(loja.d.w / 100, 0.06, 0.06)
                materials: PrincipledMaterial { lighting: PrincipledMaterial.NoLighting; baseColor: Qt.lighter(loja.c, 1.25) }
            }
            Model {   // letreirinho da loja (nome inventado) em cima
                source: "#Rectangle"; position: Qt.vector3d(0, 565, 12)
                scale: Qt.vector3d(loja.d.w / 140, 0.9, 1)
                materials: PrincipledMaterial {
                    lighting: PrincipledMaterial.NoLighting
                    alphaMode: PrincipledMaterial.Blend
                    blendMode: PrincipledMaterial.Screen
                    baseColorMap: Texture {
                        sourceItem: Item {
                            width: 300; height: 60
                            Text {
                                anchors.centerIn: parent
                                text: ponte.letreiros[loja.d.t % ponte.letreiros.length]
                                font.family: ["Orbitron", "Bebas Neue", "Consolas", "Impact", "Courier New", "Arial Black"][loja.d.t % 6]
                                font.pixelSize: 40; font.bold: true
                                color: Qt.lighter(loja.c, 1.3); style: Text.Outline; styleColor: loja.c
                            }
                        }
                    }
                }
            }
            Model {   // aparelho de ar-condicionado pingando (só em algumas)
                visible: Math.abs(loja.d.x) > 1000
                source: "#Cube"; position: Qt.vector3d(loja.d.w * 0.3, 820, 60)
                scale: Qt.vector3d(1.4, 0.9, 1.0)
                materials: PrincipledMaterial { baseColor: "#8a8c94"; roughness: 0.5; metalness: 0.3 }
            }
            PointLight { position: Qt.vector3d(0, 300, 300); color: loja.c; brightness: 5; quadraticFade: 0.3 }
        }
    }
    Repeater3D {   // POSTES de luz na calçada de lá
        model: [-900, 950]
        Node {
            position: Qt.vector3d(modelData, 0, -1650)
            Model { source: "#Cylinder"; position.y: 550; scale: Qt.vector3d(0.22, 11, 0.22); materials: PrincipledMaterial { baseColor: "#2a2c34"; metalness: 0.8; roughness: 0.4 } }
            Model { source: "#Cube"; position: Qt.vector3d(0, 1100, 150); scale: Qt.vector3d(0.25, 0.2, 3); materials: PrincipledMaterial { baseColor: "#2a2c34"; metalness: 0.8 } }
            Model { source: "#Cube"; position: Qt.vector3d(0, 1086, 280); scale: Qt.vector3d(0.8, 0.05, 0.8); materials: PrincipledMaterial { lighting: PrincipledMaterial.NoLighting; baseColor: "#e8f0ff" } }
            SpotLight { position: Qt.vector3d(0, 1080, 280); eulerRotation.x: -90; color: "#d8e0ff"; brightness: 30; coneAngle: 75; innerConeAngle: 35; quadraticFade: 0.05 }
        }
    }
    PointLight { position: Qt.vector3d(-700, 600, -1100); color: "#ff3cbe"; brightness: 20; quadraticFade: 0.05 }   // a rua é colorida de neon
    PointLight { position: Qt.vector3d(700, 600, -1100); color: "#3ad8ff"; brightness: 20; quadraticFade: 0.05 }
    // os CARROS em tamanho real (≈4,5 m): passam de vez em quando, um em cada mão, com faróis e neon embaixo
    readonly property var carros: [
        {z: -730, dir: 1, per: 9, atraso: 1.5, cor: "#c83a5a", neon: "#ff3cbe"},
        {z: -1320, dir: -1, per: 13, atraso: 6, cor: "#3a6ac8", neon: "#3ad8ff"},
        {z: -730, dir: 1, per: 17, atraso: 11, cor: "#d8d8e0", neon: "#b04aff"}
    ]
    Repeater3D {
        model: vista.carros
        Node {
            id: carro
            readonly property real fase: ((vista.tempo + modelData.atraso) % modelData.per) * 3200   // ≈ 50 km/h
            position: Qt.vector3d(modelData.dir * (-6500 + fase), 0, modelData.z)
            eulerRotation.y: modelData.dir > 0 ? 0 : 180
            visible: vista.anima && fase < 13000
            Model { source: "#Cube"; position.y: 130; scale: Qt.vector3d(10.5, 1.3, 4.2); materials: PrincipledMaterial { baseColor: modelData.cor; metalness: 0.6; roughness: 0.25 } }   // carroceria
            Model { source: "#Cube"; position: Qt.vector3d(-60, 250, 0); scale: Qt.vector3d(5.4, 1.2, 3.8); materials: PrincipledMaterial { baseColor: "#0c1018"; metalness: 0.4; roughness: 0.05 } }   // cabine (vidros)
            Repeater3D {   // rodas
                model: 4
                Model {
                    source: "#Cylinder"
                    position: Qt.vector3d(index < 2 ? 330 : -330, 65, index % 2 ? 200 : -200)
                    eulerRotation.x: 90
                    scale: Qt.vector3d(1.3, 0.4, 1.3)
                    materials: PrincipledMaterial { baseColor: "#0a0a0c"; roughness: 0.7 }
                }
            }
            Model { source: "#Cube"; position: Qt.vector3d(526, 150, 0); scale: Qt.vector3d(0.04, 0.3, 3.6); materials: PrincipledMaterial { lighting: PrincipledMaterial.NoLighting; baseColor: "#f8f8ff" } }   // faróis
            Model { source: "#Cube"; position: Qt.vector3d(-526, 160, 0); scale: Qt.vector3d(0.04, 0.22, 3.9); materials: PrincipledMaterial { lighting: PrincipledMaterial.NoLighting; baseColor: "#ff2a3a" } }   // lanterna
            Model { source: "#Cube"; position.y: 50; scale: Qt.vector3d(9.6, 0.1, 3.8); materials: PrincipledMaterial { lighting: PrincipledMaterial.NoLighting; baseColor: modelData.neon } }   // neon de baixo
            PointLight { position: Qt.vector3d(0, 30, 0); color: modelData.neon; brightness: 8; quadraticFade: 0.4 }
            SpotLight { position: Qt.vector3d(540, 150, 0); eulerRotation: Qt.vector3d(-8, -90, 0); color: "#f0f4ff"; brightness: 20; coneAngle: 35; quadraticFade: 0.1 }
        }
    }

    // ---------------------------------------------------------------- as PLACAS DE NEON (e o reflexo delas)
    component Placa: Node {
        id: pl
        property var d
        property int i: 0
        property bool espelho: false
        readonly property bool ehBotao: d.texto !== undefined
        readonly property bool habilitado: d.ok === undefined || d.ok
        readonly property bool fixa: d.titulo !== undefined || d.rotulo !== undefined   // título/rótulos ficam sempre acesos
        property real luz: fixa ? 1 : 0.2
        readonly property bool acesa: vista.sobre === i && habilitado
        onAcesaChanged: {
            if (fixa) return
            liga.stop(); desliga.stop()
            if (acesa) liga.start(); else desliga.start()
        }
        SequentialAnimation {   // "tz-tz": pisca antes de firmar
            id: liga
            NumberAnimation { target: pl; property: "luz"; to: 0.9; duration: 40 }
            NumberAnimation { target: pl; property: "luz"; to: 0.1; duration: 60 }
            NumberAnimation { target: pl; property: "luz"; to: 0.8; duration: 30 }
            NumberAnimation { target: pl; property: "luz"; to: 0.25; duration: 90 }
            NumberAnimation { target: pl; property: "luz"; to: 1.0; duration: 50 }
            NumberAnimation { target: pl; property: "luz"; to: 0.6; duration: 40 }
            NumberAnimation { target: pl; property: "luz"; to: 1.0; duration: 60 }
        }
        NumberAnimation { id: desliga; target: pl; property: "luz"; to: 0.2; duration: 220 }
        position: Qt.vector3d((d.x || 0) * vista.escPlaca, (espelho ? -1 : 1) * (vista.topoLojas + (d.y - 110) * vista.escPlaca), vista.fundoZ + 20)
        scale: Qt.vector3d(vista.escPlaca, espelho ? -vista.escPlaca : vista.escPlaca, vista.escPlaca)
        eulerRotation.z: d.rot || 0
        readonly property color corC: d.cor
        function cor(a) { return Qt.rgba(corC.r, corC.g, corC.b, a) }
        Model {   // a placa de trás (chapa escura com borda)
            property int opcao: pl.i
            pickable: pl.ehBotao && !pl.espelho
            visible: !pl.espelho && !pl.d.rotulo
            source: "#Cube"
            position.z: -6
            scale: Qt.vector3d((pl.d.w + 40) / 100, (pl.d.h + 26) / 100, 0.06)
            materials: PrincipledMaterial {
                baseColor: pl.d.moldura === "terminal" ? "#04120f" : pl.d.moldura === "exit" ? "#1a0606"
                         : pl.d.moldura === "redonda" ? "#140a1e" : "#121018"
                roughness: 0.5; metalness: 0.4
            }
        }
        Model {   // o HALO do neon (brilho espalhado em volta, cresce quando liga)
            source: "#Rectangle"
            position.z: -2
            scale: Qt.vector3d(pl.d.w * 1.5 / 100, pl.d.h * 2.6 / 100, 1)
            opacity: Math.max(0, pl.luz - 0.2) * (pl.espelho ? 0.4 : 1.1)
            materials: PrincipledMaterial {
                lighting: PrincipledMaterial.NoLighting
                baseColorMap: Texture { source: vista.tex("sprite_brilho") }
                baseColor: pl.d.cor
                alphaMode: PrincipledMaterial.Blend
                blendMode: PrincipledMaterial.Screen
                depthDrawMode: Material.NeverDepthDraw
                cullMode: Material.NoCulling   // o reflexo (escala -1) vira de costas
            }
        }
        Model {   // o NEON (texto com brilho)
            source: "#Rectangle"
            scale: Qt.vector3d(pl.d.w / 100, pl.d.h / 100, 1)
            materials: PrincipledMaterial {
                lighting: PrincipledMaterial.NoLighting
                alphaMode: PrincipledMaterial.Blend
                blendMode: PrincipledMaterial.Screen
                depthDrawMode: Material.NeverDepthDraw
                cullMode: Material.NoCulling   // o reflexo (escala -1) vira de costas
                readonly property real k: (0.72 + 0.28 * pl.luz) * (pl.espelho ? 0.6 : 1)
                baseColor: Qt.rgba(k, k, k, 1)
                baseColorMap: Texture {
                    sourceItem: Item {
                        id: chapa
                        width: pl.d.w * 2; height: pl.d.h * 2
                        readonly property string m: pl.d.moldura || ""
                        Rectangle {   // moldura de tubo (tubo / dupla / redonda / exit)
                            visible: chapa.m === "tubo" || chapa.m === "dupla" || chapa.m === "redonda" || chapa.m === "exit"
                            anchors.fill: parent; anchors.margins: 6
                            radius: chapa.m === "redonda" ? height / 2 : chapa.m === "tubo" ? 18 : 4
                            color: "transparent"
                            border.width: chapa.m === "exit" ? 8 : 5
                            border.color: Qt.lighter(pl.d.cor, 1.2)
                        }
                        Rectangle {   // segundo tubo da moldura dupla (o título)
                            visible: chapa.m === "dupla"
                            anchors.fill: parent; anchors.margins: 20
                            radius: 2; color: "transparent"
                            border.width: 3; border.color: "#4ee8ff"
                        }
                        Rectangle {   // tela de terminal: fundo verde-água com linhas
                            visible: chapa.m === "terminal"
                            anchors.fill: parent; anchors.margins: 4
                            color: pl.cor(0.12); border.width: 3; border.color: pl.d.cor
                            Text { x: 14; y: 6; text: "> SYS.LOG_04 //"; font.family: "Consolas"; font.pixelSize: 18; color: pl.cor(0.8) }
                            Text { anchors.right: parent.right; anchors.rightMargin: 14; y: 6; text: "▮▮▮▯ 87%"; font.family: "Consolas"; font.pixelSize: 18; color: pl.cor(0.8) }
                        }
                        Repeater {   // cantoneiras (Impact)
                            model: chapa.m === "cantos" ? 4 : 0
                            Item {
                                x: index % 2 ? chapa.width - 50 : 6; y: index < 2 ? 6 : chapa.height - 50
                                width: 44; height: 44
                                Rectangle { x: index % 2 ? 36 : 0; width: 8; height: 44; color: Qt.lighter(pl.d.cor, 1.2) }
                                Rectangle { y: index < 2 ? 0 : 36; width: 44; height: 8; color: Qt.lighter(pl.d.cor, 1.2) }
                            }
                        }
                        Text {   // setinha dos rótulos
                            visible: chapa.m === "seta"
                            anchors.verticalCenter: parent.verticalCenter; x: 6
                            text: "▶"; font.pixelSize: 40; color: pl.d.cor
                        }
                        Text {   // o brilho em volta (borda grossa e transparente)
                            anchors.centerIn: neon
                            text: neon.text; font: neon.font
                            color: "transparent"
                            style: Text.Outline
                            styleColor: pl.cor(0.55)
                        }
                        Text {
                            id: neon
                            anchors.centerIn: parent
                            anchors.verticalCenterOffset: pl.d.det ? -12 : (chapa.m === "terminal" ? 8 : 0)
                            text: (chapa.m === "terminal" ? "> " : "") + (pl.d.titulo || pl.d.rotulo || pl.d.texto) + (chapa.m === "terminal" ? "_" : "")
                            font.family: pl.d.fonte || ponte.cores.fonte
                            font.pixelSize: pl.d.px || 74
                            font.letterSpacing: pl.d.rotulo ? 12 : chapa.m === "exit" ? 8 : 2
                            font.bold: chapa.m !== "redonda" && chapa.m !== "cantos"
                            font.italic: chapa.m === "cantos"
                            color: Qt.lighter(pl.d.cor, 1.25 + (pl.fixa ? 0 : 0.7 * Math.max(0, pl.luz - 0.5)))   // miolo claro; aceso, quase branco
                            style: Text.Outline
                            styleColor: pl.d.cor
                        }
                        Text {
                            visible: !!pl.d.det
                            anchors.horizontalCenter: parent.horizontalCenter
                            anchors.bottom: parent.bottom
                            anchors.bottomMargin: 4
                            text: pl.d.det || ""
                            font.pixelSize: 22
                            color: pl.d.cor
                        }
                    }
                }
            }
        }
        PointLight {   // a luz da placa pinta a parede e a poça
            visible: !pl.espelho
            position.z: 80
            color: pl.d.cor
            brightness: (pl.d.titulo ? 12 : pl.ehBotao ? 8 : 0) * Math.max(0, pl.luz - 0.2)
            quadraticFade: 0.4
        }
    }
    Repeater3D { model: vista.opcoes; Placa { d: modelData; i: index } }
    Repeater3D { model: vista.opcoes; Placa { d: modelData; i: index; espelho: true } }
    MouseArea {   // mouse nas placas: liga; clique escolhe
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

    // ---------------------------------------------------------------- letreiros de fundo (palavras inventadas)
    // cada um é de um tipo: vertical com letras empilhadas, moldura de lâmpadas correndo, círculo, telinha de
    // pixel, seta apontando, duas linhas. Fontes diferentes em cada (Orbitron/Bebas vêm com o Taverna; o resto é
    // do sistema, e se faltar o Qt usa uma parecida).
    readonly property var letreiros: [
        {lado: -1, z: 40, y: 560, cor: "#ff5a3a", t: 0, forma: "vertical", w: 70, h: 300, fonte: "Impact", px: 50},
        {lado: -1, z: -150, y: 690, cor: "#3affd8", t: 1, forma: "seta", w: 220, h: 90, fonte: "Bebas Neue", px: 62},
        {lado: 1, z: 0, y: 650, cor: "#c04aff", t: 2, forma: "lampadas", w: 240, h: 100, fonte: "Orbitron", px: 40},
        {lado: 1, z: -100, y: 380, cor: "#ffdd3a", t: 3, forma: "pixel", w: 200, h: 80, fonte: "Consolas", px: 44},
        {lado: -1, z: -80, y: 250, cor: "#ff3a8a", t: 4, forma: "duas", w: 200, h: 100, fonte: "Arial Black", px: 36, sub: "ABERTO 24H"},
        {lado: 1, z: 120, y: 190, cor: "#3a9aff", t: 5, forma: "redonda", w: 130, h: 130, fonte: "Segoe Script", px: 40},
        {lado: 1, z: -170, y: 560, cor: "#5aff8a", t: 6, forma: "vertical", w: 60, h: 340, fonte: "Courier New", px: 40},
        {lado: -1, z: 140, y: 900, cor: "#ffa03a", t: 7, forma: "duas", w: 220, h: 90, fonte: "Bebas Neue", px: 52, sub: "▲ 2º ANDAR ▲"}
    ]
    Repeater3D {
        model: vista.letreiros
        Node {
            id: lat
            readonly property var d: modelData
            readonly property color c: d.cor
            readonly property real pisca: (Math.sin(vista.tempo * (3 + index) + index * 2) > -0.92) ? 1 : 0.15
            readonly property real dx: d.lado < 0 ? d.w / 2 + 10 : -d.w / 2 - 10   // sai da parede pra dentro do beco
            position: Qt.vector3d(d.lado * 520, d.y, d.z)
            Model {   // suporte (barra de ferro presa na parede)
                source: "#Cube"
                position: Qt.vector3d(lat.dx / 2, lat.d.h / 2 + 8, 0)
                scale: Qt.vector3d(Math.abs(lat.dx) / 100 + 0.1, 0.04, 0.04)
                materials: PrincipledMaterial { baseColor: "#2a2a30"; metalness: 0.8; roughness: 0.4 }
            }
            Model {   // a chapa
                source: lat.d.forma === "redonda" ? "#Cylinder" : "#Cube"
                position.x: lat.dx
                eulerRotation.x: lat.d.forma === "redonda" ? 90 : 0
                scale: lat.d.forma === "redonda" ? Qt.vector3d(lat.d.w / 100 + 0.1, 0.06, lat.d.h / 100 + 0.1)
                                                 : Qt.vector3d(lat.d.w / 100 + 0.1, lat.d.h / 100 + 0.1, 0.06)
                materials: PrincipledMaterial { baseColor: lat.d.forma === "pixel" ? "#06060a" : "#100c16"; roughness: 0.5 }
            }
            Model {
                source: "#Rectangle"
                position: Qt.vector3d(lat.dx, 0, 6)
                scale: Qt.vector3d(lat.d.w / 100, lat.d.h / 100, 1)
                materials: PrincipledMaterial {
                    lighting: PrincipledMaterial.NoLighting
                    alphaMode: PrincipledMaterial.Blend
                    blendMode: PrincipledMaterial.Screen
                    baseColor: Qt.rgba(1.3 * lat.pisca, 1.3 * lat.pisca, 1.3 * lat.pisca, 1)
                    baseColorMap: Texture {
                        sourceItem: Item {
                            id: q
                            width: lat.d.w * 2; height: lat.d.h * 2
                            readonly property string f: lat.d.forma
                            readonly property string palavra: ponte.letreiros[lat.d.t % ponte.letreiros.length]
                            Rectangle {   // tubo da moldura
                                visible: q.f !== "pixel" && q.f !== "lampadas"
                                anchors.fill: parent; anchors.margins: 5
                                radius: q.f === "redonda" ? width / 2 : q.f === "vertical" ? 20 : 8
                                color: "transparent"; border.width: 5; border.color: lat.d.cor
                            }
                            Repeater {   // moldura de LÂMPADAS (uma corrida de luz passando)
                                model: q.f === "lampadas" ? 22 : 0
                                Rectangle {
                                    readonly property real p: index / 22
                                    readonly property real per: 2 * (q.width + q.height) - 40
                                    readonly property real s: p * per
                                    x: s < q.width - 20 ? 6 + s : s < q.width + q.height - 40 ? q.width - 18 : s < 2 * q.width + q.height - 60 ? q.width - 18 - (s - q.width - q.height + 40) : 6
                                    y: s < q.width - 20 ? 6 : s < q.width + q.height - 40 ? 6 + s - q.width + 20 : s < 2 * q.width + q.height - 60 ? q.height - 18 : q.height - 18 - (s - 2 * q.width - q.height + 60)
                                    width: 12; height: 12; radius: 6
                                    color: (index + Math.floor(vista.tempo * 8)) % 3 === 0 ? "#fff6d0" : Qt.rgba(lat.c.r, lat.c.g, lat.c.b, 0.5)
                                }
                            }
                            Rectangle {   // telinha de pixel (fundo quadriculado)
                                visible: q.f === "pixel"
                                anchors.fill: parent
                                color: Qt.rgba(lat.c.r, lat.c.g, lat.c.b, 0.12)
                                Repeater {
                                    model: q.f === "pixel" ? Math.floor(q.height / 8) : 0
                                    Rectangle { y: index * 8; width: q.width; height: 2; color: "#000000"; opacity: 0.5 }
                                }
                            }
                            Text {   // seta embaixo
                                visible: q.f === "seta"
                                anchors.horizontalCenter: parent.horizontalCenter; anchors.bottom: parent.bottom; anchors.bottomMargin: -6
                                text: "▼"; font.pixelSize: 40; color: Qt.lighter(lat.d.cor, 1.3)
                            }
                            Text {
                                anchors.centerIn: parent
                                anchors.verticalCenterOffset: q.f === "duas" ? -lat.d.h * 0.25 : q.f === "seta" ? -12 : 0
                                text: q.f === "vertical" ? q.palavra.replace(/[ -]/g, "").split("").join("\n") : q.palavra
                                horizontalAlignment: Text.AlignHCenter
                                lineHeight: 0.82
                                font.family: lat.d.fonte; font.pixelSize: lat.d.px
                                font.bold: q.f !== "redonda"
                                font.italic: q.f === "duas"
                                rotation: q.f === "redonda" ? -12 : 0
                                color: Qt.lighter(lat.d.cor, 1.35); style: Text.Outline; styleColor: lat.d.cor
                            }
                            Text {
                                visible: q.f === "duas"
                                anchors.horizontalCenter: parent.horizontalCenter
                                anchors.bottom: parent.bottom; anchors.bottomMargin: 14
                                text: lat.d.sub || ""
                                font.family: "Consolas"; font.pixelSize: 22; font.bold: true
                                color: (Math.floor(vista.tempo * 2) % 2) ? "#ffffff" : lat.d.cor   // a segunda linha pisca sozinha
                            }
                        }
                    }
                }
            }
            PointLight { position: Qt.vector3d(lat.dx, 0, 40); color: lat.d.cor; brightness: 4 * lat.pisca; quadraticFade: 1.0 }
        }
    }

    // ---------------------------------------------------------------- canos, ar-condicionado, fios pendurados
    Repeater3D {
        model: [{x: -540, y: 900, z: 0, l: 22}, {x: 540, y: 820, z: -200, l: 20}]
        Model {   // cano comprido na parede
            source: "#Cylinder"
            position: Qt.vector3d(modelData.x, modelData.y, modelData.z)
            eulerRotation.x: 90
            scale: Qt.vector3d(0.2, modelData.l, 0.2)
            materials: PrincipledMaterial { baseColor: "#2a2c34"; metalness: 0.8; roughness: 0.4 }
        }
    }
    Repeater3D {
        model: [{x: -500, y: 420, z: 650}, {x: 500, y: 760, z: 100}, {x: -500, y: 860, z: -500}, {x: 500, y: 200, z: 450}]
        Model {
            source: "#Cube"
            position: Qt.vector3d(modelData.x, modelData.y, modelData.z)
            scale: Qt.vector3d(0.9, 0.7, 1.1)
            materials: PrincipledMaterial { baseColor: "#3a3e48"; roughness: 0.6 }
        }
    }
    Repeater3D {   // fios pendurados atravessando o beco (meia argola achatada)
        model: [{z: 600, y: 1050, f: 0.5}, {z: 150, y: 980, f: 0.4}, {z: -350, y: 1100, f: 0.6}, {z: 350, y: 1150, f: 0.35}]
        Model {
            geometry: Malha { pedido: "toro|1|0.004|0.5|40|4" }
            position: Qt.vector3d(0, modelData.y, modelData.z)
            eulerRotation: Qt.vector3d(90, 0, 180)
            scale: Qt.vector3d(560, 560, 560 * modelData.f)
            materials: PrincipledMaterial { baseColor: "#0a0a0e"; roughness: 0.6 }
        }
    }

    // ---------------------------------------------------------------- vapor do bueiro e chuva
    Model {   // tampa do bueiro
        source: "#Cylinder"
        position: Qt.vector3d(160, 1, -120)
        scale: Qt.vector3d(1.1, 0.01, 1.1)
        materials: PrincipledMaterial { baseColor: "#24242a"; metalness: 0.7; roughness: 0.4 }
    }
    ParticleSystem3D {
        running: vista.anima
        position: Qt.vector3d(160, 10, -120)
        SpriteParticle3D {
            id: vapor
            sprite: Texture { source: vista.tex("sprite_fumaca") }
            maxAmount: 90
            color: Qt.rgba(0.75, 0.7, 0.9, 0.12)
            fadeInDuration: 500
            fadeOutDuration: 1500
            billboard: true
        }
        ParticleEmitter3D {
            particle: vapor
            emitRate: 16
            lifeSpan: 4200
            particleScale: 8
            particleEndScale: 28
            shape: ParticleShape3D { type: ParticleShape3D.Cylinder; extents: Qt.vector3d(50, 2, 50) }
            velocity: VectorDirection3D { direction: Qt.vector3d(10, 110, 0); directionVariation: Qt.vector3d(20, 20, 20) }
        }
        Wander3D { particles: [vapor]; globalAmount: Qt.vector3d(60, 10, 40); globalPace: Qt.vector3d(0.3, 0.2, 0.3) }
    }
    ParticleSystem3D {
        running: vista.anima
        position: Qt.vector3d(0, 1300, 300)
        SpriteParticle3D {
            id: gota
            sprite: Texture { source: vista.tex("gota") }
            maxAmount: vista.nivel === 2 ? 2400 : 1200
            color: "#b8c8ff"
            billboard: true
        }
        ParticleEmitter3D {
            particle: gota
            emitRate: vista.nivel === 2 ? 900 : 450
            lifeSpan: 1000
            particleScale: 6
            particleScaleVariation: 2
            shape: ParticleShape3D { type: ParticleShape3D.Cube; extents: Qt.vector3d(560, 10, 1300) }
            velocity: VectorDirection3D { direction: Qt.vector3d(120, -1500, 0); directionVariation: Qt.vector3d(30, 150, 30) }
        }
    }
}
