import bpy
import math
import os

def reset_blend():
    #bpy.ops.wm.read_factory_settings()

    for scene in bpy.data.scenes:
        for obj in scene.objects:
            scene.objects.unlink(obj)

    # only worry about data in the startup scene
    for bpy_data_iter in (
            bpy.data.objects,
            bpy.data.meshes,
            bpy.data.lamps,
            bpy.data.cameras,
            bpy.data.curves,
            bpy.data.materials
            ):
        for id_data in bpy_data_iter:
            bpy_data_iter.remove(id_data)

def add_camera():
    bpy.ops.object.camera_add()
    
    camera = bpy.data.cameras["Camera"]
    camera.lens = 39.18   
    
    scene = bpy.data.scenes[0]
    camera = bpy.data.objects["Camera"]
    camera.location = (0,-25,0)   

    bpy.context.scene.camera = camera    
        
    return camera

def add_tracker():
    bpy.ops.mesh.primitive_cube_add()
    cube = bpy.data.objects['Cube']
    cube.location = (0,-3.77811,0)
    cube.scale = (.1,.1,.1)
    cube.hide_render = True
    return cube
    
def add_lights(tracker):
    bpy.ops.object.lamp_add(type='AREA')
    light = bpy.data.objects['Area']
    light.location = (0,-10.09,8.31)

    track_object_to(light, tracker)
    
    # lamp-specific
    light = bpy.data.lamps['Area']
    light.shape = 'RECTANGLE'
    light.size = 12
    light.size_y = 4
    light.node_tree.nodes['Emission'].inputs['Strength'].default_value = 5000

    bpy.ops.object.lamp_add(type='SUN')
    sun = bpy.data.objects['Sun']
    sun.location = (0,-25.08,0)

    track_object_to(sun, tracker)
    
    bpy.ops.object.track_set(type = "TRACKTO")     
    sun = bpy.data.lamps['Sun']
    sun.shadow_soft_size = 2.5
    sun.node_tree.nodes['Emission'].inputs['Strength'].default_value = 0.5    

def add_ply(path, vertex_colors=True):
    bpy.ops.import_mesh.ply(filepath=path)
    obj = bpy.context.scene.objects.active
    obj.location = (0,0,0)
    bpy.ops.object.shade_smooth()
    
    mat = bpy.data.materials.new("Material")
    mat.use_nodes = True
    
    if vertex_colors:
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links           
        
        nodes.remove(nodes.get('Diffuse BSDF'))
        
        att = nodes.new('ShaderNodeAttribute')
        att.attribute_name = 'Col'
        
        glass = nodes.new('ShaderNodeBsdfGlass')
        glass.inputs['Roughness'].default_value = 0.217
        glass.inputs['IOR'].default_value = 2.1
        
        links.new(att.outputs['Color'], glass.inputs['Color'])
        
        material_output = nodes.get('Material Output')
        links.new(glass.outputs[0], material_output.inputs[0])
        
    obj.data.materials.append(mat)

def track_object_to(object, tracker):
    bpy.ops.object.select_all(action = "DESELECT")
    object.select = True
    tracker.select = True
    bpy.context.scene.objects.active = tracker
    bpy.ops.object.track_set(type = "TRACKTO")

    
def render(out_path, dry_run=False):
    tracker = add_tracker()
    camera = add_camera()
    track_object_to(camera, tracker)
    add_lights(tracker)

    bpy.context.scene.render.filepath = out_path
    
    if not dry_run:
        bpy.ops.render.render(write_still=True)

def setup_world(resolution_x=5940, resolution_y=3600, transparent_background=True, resolution_percentage=100):
    bpy.context.scene.render.engine = 'CYCLES'
    bpy.context.scene.render.resolution_x = resolution_x
    bpy.context.scene.render.resolution_y = resolution_y
    bpy.context.scene.render.resolution_percentage = resolution_percentage
    bpy.context.scene.cycles.film_transparent = transparent_background
    #bpy.data.worlds['World'].light_settings.use_ambient_occlusion = True
    #bpy.data.worlds['World'].light_settings.ao_factor = 0.4  
    bpy.data.worlds['World'].horizon_color = (0,0,0)


def main():
    ply_dir = 'C:/Users/davidf/workspace/conn'
    out_path = 'C:/Users/davidf/workspace/conn/test.png'
    
    reset_blend()    
    setup_world(resolution_percentage=5)
    
    for filename in os.listdir(ply_dir):
        print(filename)
        if filename.endswith('ply'):
            add_ply(os.path.join(ply_dir,filename))
            break
    
    render(out_path, dry_run=False)
    
if __name__ == "__main__": main()

