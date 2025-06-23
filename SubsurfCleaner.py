bl_info = {
    "name": "Subdivision Cleaner (V3)",
    "author": "None",
    "version": (3, 0),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > Subsurf Cleaner",
    "description": "Smooth base mesh using Subsurf Level 1 without changing topology or data",
    "category": "Object",
}

import bpy

class MESH_OT_subdivision_clean_copy_add_subsurf(bpy.types.Operator):
    bl_idname = "mesh.subdivision_clean_copy_add_subsurf"
    bl_label = "Smooth Base Vertices via Subsurf Copy"
    bl_description = "Smooth base mesh using Subsurf Level 1 without modifying topology or data"

    def execute(self, context):
        obj = context.object
        if not obj or obj.type != 'MESH':
            self.report({'ERROR'}, "Active object must be a mesh")
            return {'CANCELLED'}

        previous_mode = obj.mode
        if previous_mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        obj_copy = obj.copy()
        obj_copy.data = obj.data.copy()
        context.collection.objects.link(obj_copy)

        obj_copy.modifiers.clear()

        mod = obj_copy.modifiers.new(name="Subsurf", type='SUBSURF')
        mod.levels = 1
        mod.render_levels = 1

        context.view_layer.update()

        depsgraph = context.evaluated_depsgraph_get()
        obj_eval = obj_copy.evaluated_get(depsgraph)
        eval_mesh = obj_eval.to_mesh()

        if not eval_mesh or len(eval_mesh.vertices) < len(obj.data.vertices):
            self.report({'ERROR'}, "Failed to evaluate mesh or vertex count mismatch")
            if eval_mesh:
                obj_eval.to_mesh_clear()
            bpy.data.objects.remove(obj_copy, do_unlink=True)
            if previous_mode != 'OBJECT':
                bpy.ops.object.mode_set(mode=previous_mode)
            return {'CANCELLED'}

        base_verts = obj.data.vertices
        for i, v in enumerate(base_verts):
            v.co = eval_mesh.vertices[i].co

        obj.data.update()
        obj_eval.to_mesh_clear()

        bpy.data.objects.remove(obj_copy, do_unlink=True)

        if previous_mode != 'OBJECT':
            bpy.ops.object.mode_set(mode=previous_mode)

        self.report({'INFO'}, "Base vertices smoothed using Subsurf Level 1")
        return {'FINISHED'}


class SubsurfCleanerPanel(bpy.types.Panel):
    bl_label = "Subsurf Cleaner"
    bl_idname = "OBJECT_PT_subsurf_cleaner"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Subsurf Cleaner'

    def draw(self, context):
        layout = self.layout
        layout.operator("mesh.subdivision_clean_copy_add_subsurf", icon="MOD_SUBSURF")


def register():
    bpy.utils.register_class(MESH_OT_subdivision_clean_copy_add_subsurf)
    bpy.utils.register_class(SubsurfCleanerPanel)


def unregister():
    bpy.utils.unregister_class(MESH_OT_subdivision_clean_copy_add_subsurf)
    bpy.utils.unregister_class(SubsurfCleanerPanel)


if __name__ == "__main__":
    register()
