import bpy
import math

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
            ):
        for id_data in bpy_data_iter:
            bpy_data_iter.remove(id_data)

def add_camera(scale):
    bpy.ops.object.camera_add()
    scene = bpy.data.scenes[0]
    camera = bpy.data.objects["Camera"]
    camera.data.type = 'ORTHO'
    camera.data.ortho_scale = scale
    
    camera.location = (0,0,0)   
    

    bpy.context.scene.camera = camera
    #camera.rotation_euler.x = math.pi*0.5
    
    return camera

def add_tracker(z):
    bpy.ops.mesh.primitive_cube_add()
    cube = bpy.data.objects['Cube']
    cube.location = (0,0,z)
    cube.scale = (.1,.1,.1)
    cube.hide_render = True
    return cube
    
def add_camera_track(steps, camera, tracker, z):
    bpy.ops.curve.primitive_bezier_circle_add()
    
    circle = bpy.data.curves['BezierCircle']
    circle.path_duration = steps
    
    circle = bpy.data.objects['BezierCircle']
    circle.location = (0,0,z)        
    circle.scale = (1.0,1.0,1.0)
    
    camera.select = True

    bpy.context.scene.objects.active = camera
    
    camera.constraints.new('FOLLOW_PATH')
    constraint = camera.constraints['Follow Path']
    constraint.target = circle
    override={'constraint':camera.constraints["Follow Path"]}
    bpy.ops.constraint.followpath_path_animate(override,constraint='Follow Path')
        
    bpy.ops.object.select_all(action = "DESELECT")
    camera.select = True
    tracker.select = True
    bpy.context.scene.objects.active = tracker
    bpy.ops.object.track_set(type = "TRACKTO") 

def setup_animation(num_frames, directory):
    scn = bpy.context.scene
    scn.frame_end = num_frames
    scn.render.filepath = directory
    
def add_light(tracker):
    bpy.ops.object.lamp_add(type='AREA')
    light = bpy.data.objects['Area']
    light.location = (10,-5,10)    
    
    bpy.ops.object.select_all(action = "DESELECT")
    light.select = True
    tracker.select = True
    bpy.context.scene.objects.active = tracker
    bpy.ops.object.track_set(type = "TRACKTO") 
    
    light = bpy.data.lamps['Area']
    light.node_tree.nodes['Emission'].inputs['Strength'].default_value = 5000
    

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
        
        att = nodes.new('ShaderNodeAttribute')
        att.attribute_name = 'Col'
        
        diff = nodes.get('Diffuse BSDF')
        
        links.new(att.outputs['Color'], diff.inputs['Color'])
    obj.data.materials.append(mat)
    
def spin_render(num_frames, out_dir, scale, z, dry_run=False):
    tracker = add_tracker(z)
    camera = add_camera(scale)
    add_camera_track(num_frames, camera, tracker, z)
    add_light(tracker)
    setup_animation(num_frames, out_dir)
    
    if not dry_run:
        bpy.ops.render.render(animation=True)

def setup_world():
    bpy.context.scene.render.engine = 'CYCLES'
    bpy.context.scene.render.resolution_x = 1980
    bpy.context.scene.render.resolution_y = 1200
    bpy.context.scene.render.resolution_percentage = 100
    bpy.context.scene.cycles.film_transparent = True
    bpy.data.worlds['World'].light_settings.use_ambient_occlusion = True
    bpy.data.worlds['World'].light_settings.ao_factor = 0.4  
    bpy.data.worlds['World'].horizon_color = (0,0,0)

def main():
    configs = [
        dict(ply = "/Users/davidf/tmp/allen/aibs/technology/mousecelltypes/artwork/human_press_release/H16.06.007.01.05.02_550397440_p_DendriteAxon_aligned.ply",
             outdir = "/Users/davidf/tmp/allen/aibs/technology/mousecelltypes/artwork/human_press_release/H16.06.007.01.05.02_550397440_p_DendriteAxon_aligned/",
             scale = 28.6,
             z = -4,
             steps = 300),
        dict(ply = "/Users/davidf/tmp/allen/aibs/technology/mousecelltypes/artwork/human_press_release/H16.06.010.01.03.14.02_548268538_p_dendriteaxon_aligned.ply",
             outdir = "/Users/davidf/tmp/allen/aibs/technology/mousecelltypes/artwork/human_press_release/H16.06.010.01.03.14.02_548268538_p_dendriteaxon_aligned/",
             scale = 18,
             z = 2,
             steps = 300)
    ]   
    
    for config in configs:
        reset_blend()    
        setup_world()
        add_ply(config['ply'])
        spin_render(config['steps'], config['outdir'], config['scale'], config['z'], dry_run=False)

    
if __name__ == "__main__": main()

