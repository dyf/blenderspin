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

def add_camera():
    bpy.ops.object.camera_add()
    scene = bpy.data.scenes[0]
    camera = bpy.data.objects["Camera"]
    camera.location = (0,0,0)
    bpy.context.scene.camera = camera
    #camera.rotation_euler.x = math.pi*0.5
    
    return camera

def add_tracker():
    bpy.ops.mesh.primitive_cube_add()
    cube = bpy.data.objects['Cube']
    cube.location = (0,0,0)
    cube.scale = (.1,.1,.1)
    cube.hide_render = True
    return cube
    
def add_camera_track(steps, camera, tracker):
    bpy.ops.curve.primitive_bezier_circle_add()
    
    circle = bpy.data.curves['BezierCircle']
    circle.path_duration = steps
    
    circle = bpy.data.objects['BezierCircle']
    circle.location = (0,0,0)    
    circle.scale = (10, 10, 1)
    
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

def render_animation(num_frames, directory):
    scn = bpy.context.scene
    scn.frame_end = num_frames
    scn.render.filepath = directory
    bpy.ops.render.render(animation=True)
    
def add_light(tracker):
    bpy.ops.object.lamp_add(type='AREA')
    light = bpy.data.objects['Area']
    
    light.location = (10,-5,10)
    
    bpy.ops.object.select_all(action = "DESELECT")
    light.select = True
    tracker.select = True
    bpy.context.scene.objects.active = tracker
    bpy.ops.object.track_set(type = "TRACKTO") 
    

def add_ply(path, vertex_colors=True):
    bpy.ops.import_mesh.ply(filepath=path)
    obj = bpy.context.scene.objects.active
    obj.location = (0,0,0)
    
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
    
def spin_render(num_frames, out_dir):
    bpy.context.scene.render.engine = 'CYCLES'
    tracker = add_tracker()
    camera = add_camera()
    add_camera_track(num_frames, camera, tracker)
    add_light(tracker)
    
    render_animation(num_frames, out_dir)

reset_blend()
add_ply("C:/Users/davidf/Documents/Python Scripts/bunny/reconstruction/bun_zipper_res3.ply")
spin_render(18, "C:/Users/davidf/Documents/Python Scripts/")

