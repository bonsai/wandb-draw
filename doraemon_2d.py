import bpy
import math
import sys
sys.path.insert(0, r'C:\Users\dance\AppData\Roaming\Python\Python311\site-packages')
import wandb
from datetime import datetime

# W&B 初期化 (offline モード)
run = wandb.init(
    project="bpy-doraemon-generation",
    config={
        "resolution": 1024,
        "render_engine": "CYCLES",
        "output_format": "PNG"
    },
    mode="offline"  # オフラインモードで実行
)

# 評価用テーブル
eval_table = wandb.Table(columns=[
    "iteration", 
    "code", 
    "status", 
    "score", 
    "error_msg",
    "render_image"
])

# シーンをクリア
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# カーブオブジェクトを作成する関数
def create_curve_curve(name, points, resolution=12):
    curve_data = bpy.data.curves.new(name=name, type='CURVE')
    curve_data.dimensions = '2D'
    curve_data.resolution_u = resolution
    
    spline = curve_data.splines.new(type='BEZIER')
    spline.bezier_points.add(len(points) - 1)
    
    for i, (co, handle_left, handle_right) in enumerate(points):
        bp = spline.bezier_points[i]
        bp.co = co
        bp.handle_left = handle_left
        bp.handle_right = handle_right
    
    curve_object = bpy.data.objects.new(name, curve_data)
    bpy.context.collection.objects.link(curve_object)
    return curve_object

# 円を作成する関数
def create_circle(name, center, radius, resolution=32):
    curve_data = bpy.data.curves.new(name=name, type='CURVE')
    curve_data.dimensions = '2D'
    curve_data.resolution_u = resolution
    
    spline = curve_data.splines.new(type='BEZIER')
    num_points = resolution
    spline.bezier_points.add(num_points - 1)
    
    for i in range(num_points):
        angle = (i / num_points) * 2 * math.pi
        x = center[0] + radius * math.cos(angle)
        y = center[1] + radius * math.sin(angle)
        bp = spline.bezier_points[i]
        bp.co = (x, y, 0)
        # ハンドルを円形に設定
        h_angle = angle
        h_len = radius * 0.55
        bp.handle_left = (x - h_len * math.sin(h_angle), y + h_len * math.cos(h_angle), 0)
        bp.handle_right = (x + h_len * math.sin(h_angle), y - h_len * math.cos(h_angle), 0)
    
    curve_object = bpy.data.objects.new(name, curve_data)
    bpy.context.collection.objects.link(curve_object)
    return curve_object

# 円弧を作成する関数
def create_arc(name, center, radius, start_angle, end_angle, resolution=16):
    curve_data = bpy.data.curves.new(name=name, type='CURVE')
    curve_data.dimensions = '2D'
    curve_data.resolution_u = resolution
    
    spline = curve_data.splines.new(type='BEZIER')
    num_points = resolution
    spline.bezier_points.add(num_points - 1)
    
    angle_range = end_angle - start_angle
    
    for i in range(num_points):
        t = i / (num_points - 1)
        angle = start_angle + t * angle_range
        x = center[0] + radius * math.cos(angle)
        y = center[1] + radius * math.sin(angle)
        bp = spline.bezier_points[i]
        bp.co = (x, y, 0)
        # タンジェントを計算
        tan_x = -math.sin(angle)
        tan_y = math.cos(angle)
        h_len = radius * 0.55 * (angle_range / (2 * math.pi)) * num_points
        bp.handle_left = (x - h_len * tan_x, y - h_len * tan_y, 0)
        bp.handle_right = (x + h_len * tan_x, y + h_len * tan_y, 0)
    
    curve_object = bpy.data.objects.new(name, curve_data)
    bpy.context.collection.objects.link(curve_object)
    return curve_object

# ドラえもんの頭（青い円）
head = create_circle("Head", (0, 0), 2.0)

# 顔（白い円 - 頭の前面）
face = create_circle("Face", (0.3, 0), 1.7)

# 目（黒い円）
left_eye = create_circle("LeftEye", (-0.5, 0.5), 0.25)
right_eye = create_circle("RightEye", (1.1, 0.5), 0.25)

# 鼻（赤い円）
nose = create_circle("Nose", (0.3, 0), 0.15)

# 口
mouth_points = [
    ((0.3, -0.8, 0), (0, 0.3, 0), (0, 0.3, 0)),
    ((0.3, -0.2, 0), (0.6, 0, 0), (0.6, 0, 0)),
]
mouth = create_curve_curve("Mouth", mouth_points)

# ひげ（左右に 3 本ずつ）
whisker_data = [
    # 左側
    [((-0.3, -0.3, 0), (-0.8, -0.4, 0), (-0.8, -0.4, 0)),
     ((-1.2, -0.5, 0), (0, 0, 0), (0, 0, 0))],
    [((-0.3, -0.5, 0), (-0.8, -0.5, 0), (-0.8, -0.5, 0)),
     ((-1.3, -0.5, 0), (0, 0, 0), (0, 0, 0))],
    [((-0.3, -0.7, 0), (-0.8, -0.6, 0), (-0.8, -0.6, 0)),
     ((-1.2, -0.5, 0), (0, 0, 0), (0, 0, 0))],
    # 右側
    [((0.9, -0.3, 0), (1.4, -0.4, 0), (1.4, -0.4, 0)),
     ((1.9, -0.5, 0), (0, 0, 0), (0, 0, 0))],
    [((0.9, -0.5, 0), (1.4, -0.5, 0), (1.4, -0.5, 0)),
     ((1.9, -0.5, 0), (0, 0, 0), (0, 0, 0))],
    [((0.9, -0.7, 0), (1.4, -0.6, 0), (1.4, -0.6, 0)),
     ((1.9, -0.5, 0), (0, 0, 0), (0, 0, 0))],
]

for i, points in enumerate(whisker_data):
    whisker = create_curve_curve(f"Whisker{i}", points)

# 首輪（赤い円）
collar = create_circle("Collar", (0.3, -1.5), 1.8)

# 鈴（黄色い円）
bell = create_circle("Bell", (0.3, -1.8), 0.3)

# 鈴のディテール
bell_detail = create_circle("BellDetail", (0.3, -1.8), 0.15)

# 体の一部（青い円弧）
body_arc = create_arc("BodyArc", (0.3, -2.5), 1.5, math.pi, 2 * math.pi)

# マテリアルを設定
def create_material(name, color):
    mat = bpy.data.materials.new(name=name)
    mat.diffuse_color = color
    return mat

# マテリアル作成
blue_mat = create_material("Blue", (0.2, 0.4, 0.8, 1.0))
white_mat = create_material("White", (1.0, 1.0, 1.0, 1.0))
red_mat = create_material("Red", (0.8, 0.1, 0.1, 1.0))
black_mat = create_material("Black", (0.1, 0.1, 0.1, 1.0))
yellow_mat = create_material("Yellow", (0.9, 0.8, 0.2, 1.0))

# オブジェクトにマテリアルを割り当て
head.data.materials.append(blue_mat)
face.data.materials.append(white_mat)
left_eye.data.materials.append(black_mat)
right_eye.data.materials.append(black_mat)
nose.data.materials.append(red_mat)
mouth.data.materials.append(black_mat)
for i in range(6):
    bpy.data.objects[f"Whisker{i}"].data.materials.append(black_mat)
collar.data.materials.append(red_mat)
bell.data.materials.append(yellow_mat)
bell_detail.data.materials.append(yellow_mat)
body_arc.data.materials.append(blue_mat)

# カーブにベベルを設定して太くする
for obj in bpy.context.collection.objects:
    if obj.type == 'CURVE':
        obj.data.bevel_depth = 0.02
        obj.data.bevel_resolution = 4

# ブレンドファイルを保存
bpy.ops.wm.save_as_mainfile(filepath='doraemon_2d.blend')

# カメラを設定
camera_data = bpy.data.cameras.new(name='Camera')
camera_obj = bpy.data.objects.new('Camera', camera_data)
bpy.context.collection.objects.link(camera_obj)
camera_obj.location = (0.3, -5, 5)
camera_obj.rotation_euler = (math.radians(60), 0, 0)
bpy.context.scene.camera = camera_obj

# レンダリング設定
bpy.context.scene.render.engine = 'CYCLES'
bpy.context.scene.render.resolution_x = 1024
bpy.context.scene.render.resolution_y = 1024
bpy.context.scene.render.resolution_percentage = 100
bpy.context.scene.render.image_settings.file_format = 'PNG'
bpy.context.scene.render.image_settings.color_mode = 'RGBA'
bpy.context.scene.render.filepath = '//doraemon_2d.png'

# マテリアルを Emission に設定して明るくする
for mat in bpy.data.materials:
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    bsdf = nodes.get("Principled BSDF")
    if bsdf:
        nodes.remove(bsdf)
    emission = nodes.new(type='ShaderNodeEmission')
    emission.inputs['Color'].default_value = mat.diffuse_color
    emission.inputs['Strength'].default_value = 1.0
    output = nodes.get("Material Output")
    if output:
        mat.node_tree.links.new(emission.outputs['Emission'], output.inputs['Surface'])

# レンダリング実行
bpy.ops.render.render(write_still=True)

print("Doraemon 2D drawing completed and saved to doraemon_2d.blend and doraemon_2d.png")

# ============================================
# W&B によるコードと実行結果の管理
# ============================================

# 現在のスクリプトコードを取得
import inspect
current_code = inspect.getsource(inspect.getmodule(inspect.currentframe()))

# 実行結果の評価
status = "success"
score = 1.0  # 成功時は満点
error_msg = ""

# W&B Table にログを記録
eval_table.add_data(
    0,  # iteration
    current_code,  # code
    status,  # status
    score,  # score
    error_msg,  # error_msg
    wandb.Image("doraemon_2d.png")  # render_image
)

# W&B にテーブルをログ
run.log({"eval_results": eval_table})

# 成功したコードを Artifact として保存
artifact = wandb.Artifact(
    name=f"doraemon-code-{datetime.now().strftime('%Y%m%d_%H%M%S')}",
    type="code",
    description="Successfully generated Doraemon 2D drawing code",
    metadata={
        "score": score,
        "status": status,
        "resolution": 1024,
        "render_engine": "CYCLES"
    }
)

# アーティファクトにファイルを追加
artifact.add_file("doraemon_2d.py")
artifact.add_file("doraemon_2d.blend")
artifact.add_file("doraemon_2d.png")

# アーティファクトをログ
# (offline モードではタグは設定できないため、メタデータで代用)
run.log_artifact(artifact)

# 改善推移のメトリクスをログ
run.log({
    "success_rate": 1.0,
    "code_token_count": len(current_code.split()),
    "execution_time": 0,  # 実際の計測は time モジュールで可能
    "score": score
})

# W&B Trace によるデバッグ情報
wandb.run._log({"trace": {
    "generation_step": "code_generation",
    "execution_step": "blender_render",
    "evaluation_step": "success_check"
}})

# ラン終了
run.finish()

print("W&B logging completed successfully!")