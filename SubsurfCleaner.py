bl_info = {
    "name": "Subdivision Cleaner",
    "author": "None",
    "version": (1, 5),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > Subsurf Cleaner",
    "description": "Stores original mesh, applies Subsurf, then restores original topology with updated positions",
    "category": "Object",
}

import bpy
import bmesh
from bpy.props import CollectionProperty, FloatVectorProperty, IntProperty


class SubsurfCleanerVertex(bpy.types.PropertyGroup):
    co: FloatVectorProperty(size=3)


class SubsurfCleanerEdge(bpy.types.PropertyGroup):
    v1: IntProperty()
    v2: IntProperty()


class SubsurfCleanerFaceVertex(bpy.types.PropertyGroup):
    index: IntProperty()


class SubsurfCleanerFace(bpy.types.PropertyGroup):
    verts: CollectionProperty(type=SubsurfCleanerFaceVertex)


class MESH_OT_SubdivisionClean(bpy.types.Operator):
    bl_idname = "mesh.subdivision_clean"
    bl_label = "Apply Subsurf & Clean"

    def execute(self, context):
        obj = context.object
        if not obj or obj.type != 'MESH':
            self.report({'ERROR'}, "Active object must be a mesh")
            return {'CANCELLED'}

        mesh = obj.data

        # Сохраняем текущий режим
        previous_mode = obj.mode
        if previous_mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        # --- Сохраняем оригинальную топологию ---
        context.scene.subsurf_cleaner_verts.clear()
        context.scene.subsurf_cleaner_edges.clear()
        context.scene.subsurf_cleaner_faces.clear()
        context.scene.subsurf_cleaner_vert_count = len(mesh.vertices)

        for v in mesh.vertices:
            item = context.scene.subsurf_cleaner_verts.add()
            item.co = v.co.copy()

        for e in mesh.edges:
            item = context.scene.subsurf_cleaner_edges.add()
            item.v1 = e.vertices[0]
            item.v2 = e.vertices[1]

        for poly in mesh.polygons:
            face = context.scene.subsurf_cleaner_faces.add()
            for idx in poly.vertices:
                v_item = face.verts.add()
                v_item.index = idx

        # --- Применяем модификаторы Subdivision Surface ---
        subsurf_mods = [m for m in obj.modifiers if m.type == 'SUBSURF']
        for mod in subsurf_mods:
            bpy.ops.object.modifier_apply(modifier=mod.name)

        # --- Восстанавливаем топологию, оставляя позиции ---
        current_coords = [mesh.vertices[i].co.copy() for i in range(context.scene.subsurf_cleaner_vert_count)]

        bm = bmesh.new()
        bm.clear()

        old_to_new_verts = []
        for co in current_coords:
            v = bm.verts.new(co)
            old_to_new_verts.append(v)

        bm.verts.index_update()
        bm.verts.ensure_lookup_table()

        for e in context.scene.subsurf_cleaner_edges:
            try:
                bm.edges.new((old_to_new_verts[e.v1], old_to_new_verts[e.v2]))
            except ValueError:
                pass

        for f in context.scene.subsurf_cleaner_faces:
            try:
                bm.faces.new([old_to_new_verts[v.index] for v in f.verts])
            except ValueError:
                pass

        bm.to_mesh(mesh)
        bm.free()

        # Возвращаем в исходный режим
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
    bpy.utils.register_class(MESH_OT_SubdivisionClean)
    bpy.utils.register_class(SubsurfCleanerPanel)

    bpy.types.Scene.subsurf_cleaner_verts = CollectionProperty(type=SubsurfCleanerVertex)
    bpy.types.Scene.subsurf_cleaner_edges = CollectionProperty(type=SubsurfCleanerEdge)
    bpy.types.Scene.subsurf_cleaner_faces = CollectionProperty(type=SubsurfCleanerFace)
    bpy.types.Scene.subsurf_cleaner_vert_count = IntProperty()


def unregister():
    bpy.utils.unregister_class(SubsurfCleanerVertex)
    bpy.utils.unregister_class(SubsurfCleanerEdge)
    bpy.utils.unregister_class(SubsurfCleanerFaceVertex)
    bpy.utils.unregister_class(SubsurfCleanerFace)
    bpy.utils.unregister_class(MESH_OT_SubdivisionClean)
    bpy.utils.unregister_class(SubsurfCleanerPanel)

    del bpy.types.Scene.subsurf_cleaner_verts
    del bpy.types.Scene.subsurf_cleaner_edges
    del bpy.types.Scene.subsurf_cleaner_faces
    del bpy.types.Scene.subsurf_cleaner_vert_count


if __name__ == "__main__":
    register()
