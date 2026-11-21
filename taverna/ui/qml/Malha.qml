// Uma forma 3D calculada no Python (torno, toro, icosaedro, espuma) — ver ui/geometria3d.py.
import QtQuick
import QtQuick3D
import QtQuick3D.Helpers

ProceduralMesh {
    property string pedido: ""
    readonly property var m: pedido ? ponte.malha(pedido) : ({pos: [], nor: [], uv: [], idx: []})
    positions: m.pos
    normals: m.nor
    uv0s: m.uv
    indexes: m.idx
}
