#!/usr/bin/env python
"""
Doraemon 2D 描画スクリプト
Git ワークフロー対応 - 都度画像を保存してコミット
"""

import bpy
import math
import sys
import os
import subprocess
from datetime import datetime

# W&B のインポート（オプション）
try:
    import wandb
    WANDB_AVAILABLE = True
except ImportError:
    WANDB_AVAILABLE = False
    print("wandb is not available, skipping W&B logging")


def get_git_info():
    """Git リポジトリの情報を取得（subprocess を使用）"""
    try:
        commit_hash = subprocess.check_output(
            ['git', 'rev-parse', '--short', 'HEAD'], text=True
        ).strip()
        branch = subprocess.check_output(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'], text=True
        ).strip()
        return commit_hash, branch
    except Exception:
        return "unknown", "unknown"


def create_curve_curve(name, points, resolution=12):
    """カーブオブジェクトを作成する関数"""
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


def create_circle(name, center, radius, resolution=32):
    """円を作成する関数"""
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
        h_angle = angle
        h_len = radius * 0.55
        bp.handle_left = (x - h_len * math.sin(h_angle), y + h_len * math.cos(h_angle), 0)
        bp.handle_right = (x + h_len * math.sin(h_angle), y - h_len * math.cos(h_angle), 0)

    curve_object = bpy.data.objects.new(name, curve_data)
    bpy.context.collection.objects.link(curve_object)
    return curve_object


def create_arc(name, center, radius, start_angle, end_angle, resolution=16):
    """円弧を作成する関数"""
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
        tan_x = -math.sin(angle)
        tan_y = math.cos(angle)
        h_len = radius * 0.55 * (angle_range / (2 * math.pi)) * num_points
        bp.handle_left = (x - h_len * tan_x, y - h_len * tan_y, 0)
        bp.handle_right = (x + h_len * tan_x, y + h_len * tan_y, 0)

    curve_object = bpy.data.objects.new(name, curve_data)
    bpy.context.collection.objects.link(curve_object)
    return curve_object


def create_material(name, color):
    """マテリアルを作成する関数"""
    mat = bpy.data.materials.new(name=name)
    mat.diffuse_color = color
    return mat


def main():
    # スクリプトのディレクトリを基準にする（blender --background 実行時も安全）
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # シーンをクリア
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)

    # Git 情報を取得
    commit_hash, branch = get_git_info()
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    base_name = "doraemon_2d"

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
        create_curve_curve(f"Whisker{i}", points)

    # 首輪（赤い円）
    collar = create_circle("Collar", (0.3, -1.5), 1.8)

    # 鈴（黄色い円）
    bell = create_circle("Bell", (0.3, -1.8), 0.3)

    # 鈴のディテール
    bell_detail = create_circle("BellDetail", (0.3, -1.8), 0.15)

    # 体の一部（青い円弧）
    body_arc = create_arc("BodyArc", (0.3, -2.5), 1.5, math.pi, 2 * math.pi)

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

    # ブレンドファイルを絶対パスで保存
    blend_filepath = os.path.join(script_dir, f'{base_name}.blend')
    bpy.ops.wm.save_as_mainfile(filepath=blend_filepath)

    # カメラを設定
    camera_data = bpy.data.cameras.new(name='Camera')
    camera_obj = bpy.data.objects.new('Camera', camera_data)
    bpy.context.collection.objects.link(camera_obj)
    camera_obj.location = (0.3, -5, 5)
    camera_obj.rotation_euler = (math.radians(60), 0, 0)
    bpy.context.scene.camera = camera_obj

    # レンダリング設定（EEVEE: ヘッドレスCI環境でも安定動作）
    bpy.context.scene.render.engine = 'BLENDER_EEVEE_NEXT'
    bpy.context.scene.render.resolution_x = 1024
    bpy.context.scene.render.resolution_y = 1024
    bpy.context.scene.render.resolution_percentage = 100
    bpy.context.scene.render.image_settings.file_format = 'PNG'
    bpy.context.scene.render.image_settings.color_mode = 'RGBA'

    # PNG ファイルを絶対パスで指定（コミットハッシュ付き）
    png_filename = f'{base_name}_{commit_hash}.png'
    png_filepath = os.path.join(script_dir, png_filename)
    bpy.context.scene.render.filepath = png_filepath

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

    print(f"Doraemon 2D drawing completed!")
    print(f"  - Blend file: {blend_filepath}")
    print(f"  - PNG image:  {png_filepath}")
    print(f"  - Commit:     {commit_hash}")
    print(f"  - Branch:     {branch}")

    # W&B 初期化（オプション）
    if WANDB_AVAILABLE:
        run = wandb.init(
            project="bpy-doraemon-generation",
            config={
                "resolution": 1024,
                "render_engine": "BLENDER_EEVEE_NEXT",
                "output_format": "PNG",
                "commit_hash": commit_hash,
                "branch": branch,
            },
            mode=os.environ.get('WANDB_MODE', 'offline'),
        )

        eval_table = wandb.Table(
            columns=["iteration", "code", "status", "score", "error_msg", "render_image", "commit_hash"]
        )

        import inspect
        current_code = inspect.getsource(inspect.getmodule(inspect.currentframe()))

        status = "success"
        score = 1.0
        error_msg = ""

        eval_table.add_data(
            0,
            current_code,
            status,
            score,
            error_msg,
            wandb.Image(png_filepath),
            commit_hash,
        )

        run.log({"eval_results": eval_table})

        artifact = wandb.Artifact(
            name=f"doraemon-code-{timestamp}",
            type="code",
            description="Successfully generated Doraemon 2D drawing code",
            metadata={
                "score": score,
                "status": status,
                "resolution": 1024,
                "render_engine": "BLENDER_EEVEE_NEXT",
                "commit_hash": commit_hash,
            },
        )

        artifact.add_file(os.path.join(script_dir, "run_doraemon.py"))
        artifact.add_file(blend_filepath)
        artifact.add_file(png_filepath)

        run.log_artifact(artifact)
        run.log({"success_rate": 1.0, "code_token_count": len(current_code.split()), "score": score})
        run.finish()
        print("W&B logging completed successfully!")


if __name__ == "__main__":
    main()
