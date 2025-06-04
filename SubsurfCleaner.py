bl_info = {
    "name": "Subdivision Cleaner",
    "author": "None",
    "version": (2, 0),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > Subsurf Cleaner",
    "description": "Stores original mesh, applies Subsurf, then restores original topology with updated positions, UVs, seams, materials and sharp edges",
    "category": "Object",
}

import bpy
import bmesh
from bpy.props import CollectionProperty, FloatVectorProperty, IntProperty, StringProperty


class SubsurfCleanerVertex(bpy.types.PropertyGroup):
    co: FloatVectorProperty(size=3)


class SubsurfCleanerEdge(bpy.types.PropertyGroup):
    v1: IntProperty()
    v2: IntProperty()
    sharp: IntProperty(default=0)  # 0 = not sharp, 1 = sharp


class SubsurfCleanerFaceVertex(bpy.types.PropertyGroup):
    index: IntProperty()


class SubsurfCleanerFace(bpy.types.PropertyGroup):
    verts: CollectionProperty(type=SubsurfCleanerFaceVertex)
    material_index: IntProperty()


class SubsurfCleanerUV(bpy.types.PropertyGroup):
    uv: FloatVectorProperty(size=2)
    loop_index: IntProperty()
    uv_map_name: StringProperty()


class SubsurfCleanerSeamEdge(bpy.types.PropertyGroup):
    v1: IntProperty()
    v2: IntProperty()


class MESH_OT_SubdivisionClean(bpy.types.Operator):
    bl_idname = "mesh.subdivision_clean"
    bl_label = "Apply Subsurf & Clean"

    def execute(self, context):
        obj = context.object
        if not obj or obj.type != 'MESH':
            self.report({'ERROR'}, "Active object must be a mesh")
            return {'CANCELLED'}

        mesh = obj.data
        previous_mode = obj.mode
        if previous_mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        scene = context.scene
        scene.subsurf_cleaner_verts.clear()
        scene.subsurf_cleaner_edges.clear()
        scene.subsurf_cleaner_faces.clear()
        scene.subsurf_cleaner_uvs.clear()
        scene.subsurf_cleaner_seams.clear()
        scene.subsurf_cleaner_vert_count = len(mesh.vertices)

        # Сохраняем вершины
        for v in mesh.vertices:
            item = scene.subsurf_cleaner_verts.add()
            item.co = v.co.copy()

        # Сохраняем рёбра + mark sharp и seams
        for e in mesh.edges:
            edge = scene.subsurf_cleaner_edges.add()
            edge.v1 = e.vertices[0]
            edge.v2 = e.vertices[1]
            edge.sharp = 1 if e.use_edge_sharp else 0
            if e.use_seam:
                seam = scene.subsurf_cleaner_seams.add()
                seam.v1 = e.vertices[0]
                seam.v2 = e.vertices[1]

        # Сохраняем полигоны (включая материал)
        for poly in mesh.polygons:
            face = scene.subsurf_cleaner_faces.add()
            for idx in poly.vertices:
                v_item = face.verts.add()
                v_item.index = idx
            face.material_index = poly.material_index

        # Сохраняем все UV-каналы
        for uv_layer in mesh.uv_layers:
            uv_data = uv_layer.data
            for loop in mesh.loops:
                uv_item = scene.subsurf_cleaner_uvs.add()
                uv_item.loop_index = loop.index
                uv_item.uv = uv_data[loop.index].uv.copy()
                uv_item.uv_map_name = uv_layer.name

        # Применяем Subdivision Surface модификаторы
        subsurf_mods = [m for m in obj.modifiers if m.type == 'SUBSURF']
        for mod in subsurf_mods:
            bpy.ops.object.modifier_apply(modifier=mod.name)

        # Получаем новые координаты вершин после применения модификации
        current_coords = [mesh.vertices[i].co.copy() for i in range(scene.subsurf_cleaner_vert_count)]

        # Создаём новую меш-структуру с оригинальной топологией, но новыми координатами
        bm = bmesh.new()
        bm_verts = [bm.verts.new(co) for co in current_coords]

        bm.verts.index_update()
        bm.verts.ensure_lookup_table()

        edge_keys = set()
        for e in scene.subsurf_cleaner_edges:
            key = tuple(sorted((e.v1, e.v2)))
            if key not in edge_keys:
                try:
                    bm_edge = bm.edges.new((bm_verts[e.v1], bm_verts[e.v2]))
                    edge_keys.add(key)
                    # Восстанавливаем mark sharp
                    bm_edge.smooth = False if e.sharp == 1 else True
                except ValueError:
                    pass

        for f in scene.subsurf_cleaner_faces:
            try:
                bm.faces.new([bm_verts[v.index] for v in f.verts])
            except ValueError:
                pass

        bm.to_mesh(mesh)
        bm.free()

        # Восстанавливаем швы
        seam_pairs = {frozenset((s.v1, s.v2)) for s in scene.subsurf_cleaner_seams}
        for e in mesh.edges:
            if frozenset((e.vertices[0], e.vertices[1])) in seam_pairs:
                e.use_seam = True

        # Восстанавливаем все UV-каналы
        uv_maps = {}
        for uv in scene.subsurf_cleaner_uvs:
            if uv.uv_map_name not in uv_maps:
                uv_layer = mesh.uv_layers.get(uv.uv_map_name)
                if not uv_layer:
                    uv_layer = mesh.uv_layers.new(name=uv.uv_map_name)
                uv_maps[uv.uv_map_name] = uv_layer.data

        for uv in scene.subsurf_cleaner_uvs:
            data = uv_maps.get(uv.uv_map_name)
            if data and uv.loop_index < len(data):
                data[uv.loop_index].uv = uv.uv

        # Восстанавливаем индексы материалов
        for i, poly in enumerate(mesh.polygons):
            if i < len(scene.subsurf_cleaner_faces):
                poly.material_index = scene.subsurf_cleaner_faces[i].material_index

        mesh.update()

        if previous_mode == 'EDIT':
            bpy.ops.object.mode_set(mode='EDIT')

        self.report({'INFO'}, "Subdivision applied and original topology restored")
        return {'FINISHED'}


class SubsurfCleanerPanel(bpy.types.Panel):
    bl_label = "Subsurf Cleaner"
    bl_idname = "OBJECT_PT_subsurf_cleaner"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Subsurf Cleaner'

    def draw(self, context):
        layout = self.layout
        layout.operator("mesh.subdivision_clean", icon="MOD_SUBSURF")


def register():
    bpy.utils.register_class(SubsurfCleanerVertex)
    bpy.utils.register_class(SubsurfCleanerEdge)
    bpy.utils.register_class(SubsurfCleanerFaceVertex)
    bpy.utils.register_class(SubsurfCleanerFace)
    bpy.utils.register_class(SubsurfCleanerUV)
    bpy.utils.register_class(SubsurfCleanerSeamEdge)
    bpy.utils.register_class(MESH_OT_SubdivisionClean)
    bpy.utils.register_class(SubsurfCleanerPanel)

    bpy.types.Scene.subsurf_cleaner_verts = CollectionProperty(type=SubsurfCleanerVertex)
    bpy.types.Scene.subsurf_cleaner_edges = CollectionProperty(type=SubsurfCleanerEdge)
    bpy.types.Scene.subsurf_cleaner_faces = CollectionProperty(type=SubsurfCleanerFace)
    bpy.types.Scene.subsurf_cleaner_uvs = CollectionProperty(type=SubsurfCleanerUV)
    bpy.types.Scene.subsurf_cleaner_seams = CollectionProperty(type=SubsurfCleanerSeamEdge)
    bpy.types.Scene.subsurf_cleaner_vert_count = IntProperty()


def unregister():
    bpy.utils.unregister_class(SubsurfCleanerVertex)
    bpy.utils.unregister_class(SubsurfCleanerEdge)
    bpy.utils.unregister_class(SubsurfCleanerFaceVertex)
    bpy.utils.unregister_class(SubsurfCleanerFace)
    bpy.utils.unregister_class(SubsurfCleanerUV)
    bpy.utils.unregister_class(SubsurfCleanerSeamEdge)
    bpy.utils.unregister_class(MESH_OT_SubdivisionClean)
    bpy.utils.unregister_class(SubsurfCleanerPanel)

    del bpy.types.Scene.subsurf_cleaner_verts
    del bpy.types.Scene.subsurf_cleaner_edges
    del bpy.types.Scene.subsurf_cleaner_faces
    del bpy.types.Scene.subsurf_cleaner_uvs
    del bpy.types.Scene.subsurf_cleaner_seams
    del bpy.types.Scene.subsurf_cleaner_vert_count


if __name__ == "__main__":
    register()
