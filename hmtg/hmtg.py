import bpy
import csv

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

def setup_world(resolution_x=5940, resolution_y=3600, transparent_background=True, resolution_percentage=100):
    bpy.context.scene.render.engine = 'CYCLES'
    bpy.context.scene.render.resolution_x = resolution_x
    bpy.context.scene.render.resolution_y = resolution_y
    bpy.context.scene.render.resolution_percentage = resolution_percentage
    bpy.context.scene.cycles.film_transparent = transparent_background
    bpy.data.worlds['World'].light_settings.use_ambient_occlusion = True
    bpy.data.worlds['World'].light_settings.ao_factor = 0.4
    bpy.data.worlds['World'].horizon_color = (0,0,0)

def spin_render(num_frames, out_dir, scale, z, dry_run=False):
    tracker = add_tracker(z)
    camera = add_camera(scale)
    add_camera_track(num_frames, camera, tracker, z)
    add_light(tracker)
    setup_animation(num_frames, out_dir)

    if not dry_run:
        bpy.ops.render.render(animation=True)

def load_data():
    file_name = "/allen/scratch/aibstemp/davidf/artwork/hmtg/hmtg_cells.csv"

    with open(file_name, 'r') as f:
        r = csv.DictReader(f)
    
        points = list(r)
        
    
    for i, point in enumerate(points[:1000]):
        bpy.ops.surface.primitive_nurbs_surface_sphere_add()
        obj = bpy.context.object
        obj.location = ( float(point['y']), 
                         float(point['x']), 
                         float(point['z']) )
        obj.scale = ( 0.1, 0.1, 0.1 )
        
        mat = bpy.data.materials.new("Material %d" % i)
        mat.use_nodes = True
        
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links           
        
        nodes.remove(nodes.get('Diffuse BSDF'))
                
        glass = nodes.new('ShaderNodeBsdfGlass')
        glass.inputs['Roughness'].default_value = 0.817
        glass.inputs['IOR'].default_value = 2.1
        glass.inputs['Color'].default_value = ( float(point['r']), 
                                                float(point['g']), 
                                                float(point['b']), 1.0 )
        
        material_output = nodes.get('Material Output')
        links.new(glass.outputs[0], material_output.inputs[0])
        
        obj.data.materials.append(mat)
            
reset_blend()
setup_world(resolution_x=600, resolution_y=400)
load_data()
        
    
spin_render(300, "/Users/davidf/Projects/blenderspin/hmtg", 20, 0, dry_run=True)