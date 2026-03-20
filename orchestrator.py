#!/usr/bin/env python
"""
Doraemon LLM Loop Orchestrator
LLMがコード生成 → Blender実行 → Vision評価 → 改善 を繰り返す
"""

import os
import sys
import subprocess
import base64
import json
import tempfile
from datetime import datetime
from pathlib import Path

from openai import OpenAI
import wandb

# ============================================================
# 設定
# ============================================================
MAX_ITERATIONS = int(os.environ.get("MAX_ITERATIONS", "5"))
# Qwen-VL-Plus など画像認識に対応したモデルを指定
MODEL = os.environ.get("QWEN_MODEL", "qwen-vl-plus")
BLENDER_BIN = os.environ.get("BLENDER_BIN", "blender")
WORK_DIR = Path(__file__).parent
DASHSCOPE_API_KEY = os.environ.get("DASHSCOPE_API_KEY", "")

# DashScope (Qwen) の OpenAI 互換エンドポイントを使用
client = OpenAI(
    api_key=DASHSCOPE_API_KEY,
    base_url="https://dashscope-jp.aliyuncs.com/compatible-mode/v1",
)

# ============================================================
# システムプロンプト
# ============================================================
SYSTEM_PROMPT = """\
You are an expert Blender Python (bpy) developer.
Your task is to iteratively improve a Blender script that renders a 2D Doraemon illustration.

Rules:
- Output ONLY the complete Python script, no markdown fences, no explanation.
- The script must run with: blender --background --python <script.py>
- Use BLENDER_EEVEE_NEXT as the render engine (not CYCLES).
- Save the rendered PNG to the path stored in the environment variable OUTPUT_PNG.
  Use: bpy.context.scene.render.filepath = os.environ.get('OUTPUT_PNG', '/tmp/out.png')
- Do NOT use wandb inside the generated script.
- Aim for a clean, recognizable Doraemon: blue head, white face, red nose, whiskers, collar with bell.
- Each iteration should improve on the previous feedback.
"""

INITIAL_PROMPT = """\
Generate a Blender Python script that renders a 2D front-facing Doraemon illustration.
Requirements:
- Blue circular head
- White oval face
- Two round black eyes with white highlights
- Red circular nose
- Curved smile mouth
- Six whiskers (3 per side)
- Red collar with yellow bell
- Use BLENDER_EEVEE_NEXT engine
- Resolution: 512x512
- Save PNG to os.environ.get('OUTPUT_PNG', '/tmp/out.png')
"""

# ============================================================
# ユーティリティ
# ============================================================

def run_blender(script_path: Path, output_png: Path) -> tuple[bool, str]:
    """Blenderでスクリプトを実行。(success, log) を返す"""
    env = os.environ.copy()
    env["OUTPUT_PNG"] = str(output_png)
    try:
        result = subprocess.run(
            [BLENDER_BIN, "--background", "--python", str(script_path)],
            capture_output=True, text=True, timeout=120, env=env
        )
        log = result.stdout + result.stderr
        success = result.returncode == 0 and output_png.exists()
        return success, log
    except subprocess.TimeoutExpired:
        return False, "Timeout: blender took more than 120 seconds"
    except Exception as e:
        return False, str(e)


def encode_image(path: Path) -> str:
    with open(path, "rb") as f:
        return base64.standard_b64encode(f.read()).decode("utf-8")


def vision_score(image_path: Path, iteration: int) -> tuple[float, str]:
    """Qwen-VL で画像を評価してスコア(0-1)とフィードバックを返す"""
    img_b64 = encode_image(image_path)
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{img_b64}"}
                },
                {
                    "type": "text",
                    "text": (
                        "You are evaluating a Blender-rendered 2D Doraemon illustration.\n"
                        "Score it from 0.0 to 1.0 based on:\n"
                        "- Recognizability as Doraemon (blue head, white face, red nose, whiskers, collar+bell)\n"
                        "- Visual clarity and correct colors\n"
                        "- Completeness of features\n\n"
                        "Respond with JSON only:\n"
                        "{\"score\": <float 0-1>, \"feedback\": \"<what to improve>\"}"
                    )
                }
            ]
        }]
    )
    text = resp.choices[0].message.content.strip()
    try:
        # JSON部分を抽出 (稀にMarkdownが含まれる場合への対策)
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "{" in text:
            text = "{" + text.split("{")[1].split("}")[0] + "}"
        data = json.loads(text)
        return float(data["score"]), data["feedback"]
    except Exception:
        return 0.3, text


def generate_code(messages: list) -> str:
    """Qwen APIでBlenderコードを生成/改善"""
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "system", "content": SYSTEM_PROMPT}] + messages,
    )
    text = resp.choices[0].message.content.strip()
    # コードブロックが返ってきた場合の抽出
    if "```python" in text:
        text = text.split("```python")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()
    return text


# ============================================================
# メインループ
# ============================================================

def main():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    run = wandb.init(
        project="bpy-doraemon-generation",
        name=f"llm-loop-{timestamp}",
        config={
            "max_iterations": MAX_ITERATIONS,
            "model": MODEL,
            "engine": "BLENDER_EEVEE_NEXT",
        },
        mode=os.environ.get("WANDB_MODE", "offline"),
    )

    table = wandb.Table(columns=[
        "iteration", "code", "render_success",
        "vision_score", "feedback", "render_image"
    ])

    conversation = [{"role": "user", "content": INITIAL_PROMPT}]

    best_score = -1.0
    best_png = None

    for i in range(MAX_ITERATIONS):
        print(f"\n{'='*50}")
        print(f"Iteration {i+1}/{MAX_ITERATIONS}")
        print('='*50)

        # 1. コード生成
        print("Generating code...")
        code = generate_code(conversation)
        print(f"  Generated {len(code)} chars")

        # 2. スクリプトを一時ファイルに保存
        script_path = WORK_DIR / f"generated_{i}.py"
        script_path.write_text(code)

        output_png = WORK_DIR / f"doraemon_gen_{i}.png"
        if output_png.exists():
            output_png.unlink()

        # 3. Blender実行
        print("Running Blender...")
        success, log = run_blender(script_path, output_png)
        print(f"  Success: {success}")
        if not success:
            print(f"  Log tail: {log[-500:]}")

        # 4. スコア評価
        if success:
            print("Scoring with Vision...")
            score, feedback = vision_score(output_png, i)
        else:
            score = 0.0
            # エラーログの末尾500文字をフィードバックとして使う
            feedback = f"Render failed. Fix these errors:\n{log[-800:]}"

        print(f"  Score: {score:.3f}")
        print(f"  Feedback: {feedback[:120]}")

        # 5. W&Bログ
        wandb_img = wandb.Image(str(output_png)) if success else None
        table.add_data(i, code, success, score, feedback, wandb_img)

        run.log({
            "iteration": i,
            "score": score,
            "render_success": int(success),
        })

        if score > best_score:
            best_score = score
            best_png = output_png

        # 6. 次のイテレーションへのフィードバック
        conversation.append({"role": "assistant", "content": code})
        conversation.append({
            "role": "user",
            "content": (
                f"Iteration {i+1} result:\n"
                f"- Render success: {success}\n"
                f"- Vision score: {score:.3f}/1.0\n"
                f"- Feedback: {feedback}\n\n"
                "Please improve the script based on this feedback. "
                "Output the complete improved script only."
            )
        })

        # 早期終了
        if score >= 0.95:
            print(f"  Reached target score {score:.3f}, stopping early.")
            break

    # 最終ログ
    run.log({"eval_results": table, "best_score": best_score})

    if best_png and best_png.exists():
        artifact = wandb.Artifact(
            name=f"doraemon-best-{timestamp}",
            type="result",
            metadata={"best_score": best_score, "model": MODEL},
        )
        artifact.add_file(str(best_png))
        run.log_artifact(artifact)
        print(f"\nBest score: {best_score:.3f} → {best_png}")

    run.finish()
    print("\nDone.")


if __name__ == "__main__":
    main()
