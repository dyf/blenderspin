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
    circle.scale = (10.0,10.0,10.0)
    
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

def setup_world(resolution_x=5940, resolution_y=3600, transparent_background=True, resolution_percentage=100):
    bpy.context.scene.render.engine = 'CYCLES'
    bpy.context.scene.render.resolution_x = resolution_x
    bpy.context.scene.render.resolution_y = resolution_y
    bpy.context.scene.render.resolution_percentage = resolution_percentage
    bpy.context.scene.cycles.film_transparent = transparent_background
    bpy.data.worlds['World'].light_settings.use_ambient_occlusion = True
    bpy.data.worlds['World'].light_settings.ao_factor = 0.4  
    bpy.data.worlds['World'].horizon_color = (0,0,0)

def main():
    base_config = {
        'scale': 1.88,
        'z': -0.0185,
        'steps': 300
        }
    
    for dir_name in os.listdir('.'):
        ply_file = None
        if os.isdir(dir_name):
            ply_file = os.path.join(dir_name, 'recon.ply')
            
        if not os.path.exists(ply_file):
            continue

        base_config['ply'] = ply_file
        base_config['outdir'] = dir_name

        reset_blend()    
        setup_world(resolution_percentage=20)
        add_ply(config['ply'])
        spin_render(config['steps'], config['outdir'], config['scale'], config['z'], dry_run=False)


def main_manual():
    configs = [
        dict(ply = "/allen/aibs/technology/mousecelltypes/artwork/human_press_release/H17.06.003.11.06.01_589259963_m.ply",
             outdir = "/allen/aibs/technology/mousecelltypes/artwork/human_press_release/H17.06.003.11.06.01_589259963_m/",
             scale = 1.88,
             z = -.0185,
             steps = 300),
        dict(ply = "/allen/aibs/technology/mousecelltypes/artwork/human_press_release/H17.06.006.11.09.05_601947568_m.ply",
             outdir = "/allen/aibs/technology/mousecelltypes/artwork/human_press_release/H17.06.006.11.09.05_601947568_m/",
             scale = 1.88,
             z = 0.376,
             steps = 300),
        dict(ply = "/allen/aibs/technology/mousecelltypes/artwork/human_press_release/H16.06.010.01.03.04.01_566350716_m.ply",
             outdir = "/allen/aibs/technology/mousecelltypes/artwork/human_press_release/H16.06.010.01.03.04.01_566350716_m/",
             scale = 1.48,
             z = -.085,
             steps = 300),
        dict(ply = "/allen/aibs/technology/mousecelltypes/artwork/human_press_release/H16.03.007.01.01.08.01_564395300_m.ply",
             outdir = "/allen/aibs/technology/mousecelltypes/artwork/human_press_release/H16.03.007.01.01.08.01_564395300_m/",
             scale = 2.0,
             z = .163,
             steps = 300),
        dict(ply = "/allen/aibs/technology/mousecelltypes/artwork/human_press_release/H16.06.004.01.04.05_556380170_m.ply",
             outdir = "/allen/aibs/technology/mousecelltypes/artwork/human_press_release/H16.06.004.01.04.05_556380170_m/",
             scale = 4.8,
             z = .3,
             steps = 300),
        dict(ply = "/allen/aibs/technology/mousecelltypes/artwork/human_press_release/H16.06.010.01.03.05.02_599474744_m.ply",
             outdir = "/allen/aibs/technology/mousecelltypes/artwork/human_press_release/H16.06.010.01.03.05.02_599474744_m/",
             scale = 4.8,
             z = .3,
             steps = 300),
        dict(ply = "/allen/aibs/technology/mousecelltypes/artwork/human_press_release/H16.06.010.01.03.14.02_599474317_m.ply",
             outdir = "/allen/aibs/technology/mousecelltypes/artwork/human_press_release/H16.06.010.01.03.14.02_599474317_m/",
             scale = 2.1,
             z = .24,
             steps = 300),
        dict(ply = "/allen/aibs/technology/mousecelltypes/artwork/human_press_release/H16.06.007.01.05.02_550397440_p_DendriteAxon_aligned.ply",
             outdir = "/allen/aibs/technology/mousecelltypes/artwork/human_press_release/H16.06.007.01.05.02_550397440_p_DendriteAxon_aligned/",
             scale = 28.6,
             z = -4,
             steps = 300),
        dict(ply = "/allen/aibs/technology/mousecelltypes/artwork/human_press_release/H16.06.010.01.03.14.02_548268538_p_dendriteaxon_aligned.ply",
             outdir = "/allen/aibs/technology/mousecelltypes/artwork/human_press_release/H16.06.010.01.03.14.02_548268538_p_dendriteaxon_aligned/",
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

