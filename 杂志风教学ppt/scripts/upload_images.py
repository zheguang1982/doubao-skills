"""
批量上传图片到飞书幻灯片并记录file_token。
使用前修改 PRES_ID 和 images 字典。
用法: python upload_images.py
"""
import subprocess
import json
import os

# ========== 修改以下配置 ==========
PRES_ID = "你的xml_presentation_id"
# 工作目录（包含图片的目录）
WORK_DIR = r"你的工作目录路径"
# 图片列表: {名称: 相对路径}
images = {
    # "cover": "generated/cover.png",
    # "scene1": "generated/scene1.png",
}
# ==================================

def main():
    os.chdir(WORK_DIR)
    tokens = {}
    for name, rel_path in images.items():
        cmd = ["lark-cli", "slides", "+media-upload", "--file", rel_path, "--presentation", PRES_ID]
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=WORK_DIR)
        try:
            data = json.loads(result.stdout)
            token = data.get("data", {}).get("file_token", "")
            tokens[name] = token
            print(f"[OK] {name}: {token}")
        except Exception as e:
            print(f"[FAIL] {name}: {e}")
            print(f"  stdout: {result.stdout[:300]}")
            print(f"  stderr: {result.stderr[:300]}")

    out_path = os.path.join(WORK_DIR, "image_tokens.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(tokens, f, ensure_ascii=False, indent=2)
    print(f"\nTokens saved to {out_path}")

if __name__ == "__main__":
    main()
