import pyxel
import math
import re


# ======================================================================
# WRL File Parser
# WRLファイル（V1.0およびV2.0）を解析し、頂点と面のリストを返す
# ======================================================================
def parse_wrl(wrl_data, scale=50.0):
    """
    WRLデータ文字列を解析して、頂点と面のリストを返す。
    VRML V1.0とV2.0の両方の形式に対応。
    """
    vertices = []
    # V2.0形式の頂点定義 "Coordinate { point [ ... ] }" を検索
    point_match = re.search(
        r"coord\s+Coordinate\s*{\s*point\s*\[(.*?)\]", wrl_data, re.S
    )
    if not point_match:
        # V1.0形式 "Coordinate3 { point [ ... ] }" を検索
        point_match = re.search(r"Coordinate3\s*{\s*point\s*\[(.*?)\]", wrl_data, re.S)

    if point_match:
        # 抽出した数値データを浮動小数点数に変換
        point_data = re.findall(
            r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", point_match.group(1)
        )
        points_float = [float(p) for p in point_data]
        # 3つずつまとめて頂点リストを作成（Y軸を反転、スケールを適用）
        for i in range(0, len(points_float), 3):
            vertices.append(
                [
                    points_float[i] * scale,
                    -points_float[i + 1] * scale,  # Pyxelの座標系に合わせてYを反転
                    points_float[i + 2] * scale,
                ]
            )

    faces = []
    # 面のインデックス定義 "coordIndex [ ... ]" を検索
    coord_match = re.search(r"coordIndex\s*\[(.*?)\]", wrl_data, re.S)
    if coord_match:
        index_data = [int(i) for i in re.findall(r"-?\d+", coord_match.group(1))]
        current_face = []
        for index in index_data:
            if index == -1:  # "-1" は面の区切り
                if len(current_face) == 3:  # 三角形ポリゴン
                    faces.append(tuple(current_face))
                elif len(current_face) == 4:  # 四角形ポリゴンは2つの三角形に分割
                    faces.append((current_face[0], current_face[1], current_face[2]))
                    faces.append((current_face[0], current_face[2], current_face[3]))
                current_face = []
            else:
                current_face.append(index)
    return vertices, faces


# ======================================================================
# Pyxel Application Class
# ======================================================================
class App:
    def __init__(self):
        # ★★★ 修正点: tkinter のインポートを削除 ★★★
        pyxel.init(320, 240, title="WRL Dithered Polygon Viewer", fps=60)

        # 描画関連の初期設定
        self.screen_center_x = pyxel.width / 2
        self.screen_center_y = pyxel.height / 2
        self.bayer_matrix = [
            [0, 8, 2, 10],
            [12, 4, 14, 6],
            [3, 11, 1, 9],
            [15, 7, 13, 5],
        ]
        self.light_vec = [0, 0, -1]
        self.ambient_light = 0.2
        self.model_color = 11  # 明るい水色

        # モデルデータ
        self.model_v = []
        self.model_f = []

        # UIと状態管理
        self.message = ""
        self.is_auto_rotate = True
        self.angle_x = 0
        self.angle_y = 0
        self.last_mouse_x = 0
        self.last_mouse_y = 0

        # ★★★ 修正点: 起動時にデフォルトファイルを読み込む ★★★
        self._load_model_from_file("model.wrl")

        pyxel.mouse(True)
        pyxel.run(self.update, self.draw)

    def _load_model_from_file(self, filepath):
        """
        指定されたファイルパスからWRLモデルを読み込んで解析する
        """
        try:
            # ★★★ 修正点: `pyxel.root_dir` を削除し、直接ファイルを開くように修正 ★★★
            with open(filepath, "r", encoding="utf-8") as f:
                wrl_content = f.read()

            self.model_v, self.model_f = parse_wrl(wrl_content, scale=50.0)

            if not self.model_v or not self.model_f:
                self.message = "Parse Error: No model data."
            else:
                self.message = f"Loaded: {filepath}"
        except FileNotFoundError:
            self.message = "model.wrl not found."
        except Exception as e:
            self.message = f"Error: {e}"

    def update(self):
        # 右クリックで回転モードを切り替え
        if pyxel.btnp(pyxel.MOUSE_BUTTON_RIGHT):
            self.is_auto_rotate = not self.is_auto_rotate

        # モデルの回転処理
        if self.is_auto_rotate:
            self.angle_x = (pyxel.frame_count * 0.01) % (2 * math.pi)
            self.angle_y = (pyxel.frame_count * 0.015) % (2 * math.pi)
        else:
            # ★★★ 修正点: ボタン関連の処理を削除 ★★★
            if pyxel.btn(pyxel.MOUSE_BUTTON_LEFT):
                dx = pyxel.mouse_x - self.last_mouse_x
                dy = pyxel.mouse_y - self.last_mouse_y
                self.angle_y += dx * 0.01
                self.angle_x -= dy * 0.01

        self.last_mouse_x = pyxel.mouse_x
        self.last_mouse_y = pyxel.mouse_y

    def draw(self):
        pyxel.cls(0)

        # モデルの描画
        if self.model_v and self.model_f:
            self.draw_solid_polygon(self.model_v, self.model_f, 0, 0, self.model_color)

        # --- UIの描画 ---
        # メッセージ表示
        if self.message:
            pyxel.text(5, 5, self.message, 7)

        # ★★★ 修正点: ボタン描画処理を削除 ★★★

        # モード表示
        mode_text = (
            "Mode: Auto (Right-click)" if self.is_auto_rotate else "Mode: Manual (Drag)"
        )
        pyxel.text(5, pyxel.height - 10, mode_text, 7)

    def draw_solid_polygon(self, vertices, faces, offset_x, offset_y, color):
        rotated_points = []
        projected_points = []
        cos_x, sin_x = math.cos(self.angle_x), math.sin(self.angle_x)
        cos_y, sin_y = math.cos(self.angle_y), math.sin(self.angle_y)

        # 頂点データがない場合は処理を中断
        if not vertices:
            return

        for v in vertices:
            x, y, z = v[0], v[1], v[2]
            rx = x * cos_y - z * sin_y
            rz = x * sin_y + z * cos_y
            ry = y * cos_x - rz * sin_x
            final_z = y * sin_x + rz * cos_x
            rotated_points.append([rx, ry, final_z])

            perspective_strength = 300
            # final_z が perspective_strength に近づきすぎると発散するのでクリップ
            if final_z >= perspective_strength:
                final_z = perspective_strength - 1
            perspective = perspective_strength / (perspective_strength - final_z)
            px = rx * perspective + self.screen_center_x + offset_x
            py = ry * perspective + self.screen_center_y + offset_y
            projected_points.append((px, py))

        polygons_to_draw = []
        # projected_pointsが空の場合があるためチェックを追加
        if not projected_points:
            return

        for f in faces:
            # projected_pointsの範囲外のインデックスを参照しないようにチェック
            if any(
                idx >= len(projected_points) or idx >= len(rotated_points) for idx in f
            ):
                continue

            p1_rot, p2_rot, p3_rot = (
                rotated_points[f[0]],
                rotated_points[f[1]],
                rotated_points[f[2]],
            )
            v1 = [p2_rot[i] - p1_rot[i] for i in range(3)]
            v2 = [p3_rot[i] - p1_rot[i] for i in range(3)]
            normal = [
                v1[1] * v2[2] - v1[2] * v2[1],
                v1[2] * v2[0] - v1[0] * v2[2],
                v1[0] * v2[1] - v1[1] * v2[0],
            ]

            length = math.sqrt(sum(n * n for n in normal))
            if length == 0:
                continue

            normal = [n / length for n in normal]

            if normal[2] <= 0:
                normal = [-n for n in normal]

            dot_product = sum(normal[i] * self.light_vec[i] for i in range(3))
            diffuse_light = max(0, -dot_product)
            brightness = min(
                1.0, self.ambient_light + diffuse_light * (1.0 - self.ambient_light)
            )

            avg_z = (p1_rot[2] + p2_rot[2] + p3_rot[2]) / 3
            p1_proj, p2_proj, p3_proj = (
                projected_points[f[0]],
                projected_points[f[1]],
                projected_points[f[2]],
            )
            polygons_to_draw.append((avg_z, p1_proj, p2_proj, p3_proj, brightness))

        polygons_to_draw.sort(key=lambda x: x[0], reverse=True)

        for _, p1, p2, p3, brightness in polygons_to_draw:
            self.draw_dithered_triangle(p1, p2, p3, color, brightness)

    def draw_dithered_triangle(self, p1, p2, p3, color, brightness):
        min_x = int(max(0, min(p1[0], p2[0], p3[0])))
        max_x = int(min(pyxel.width - 1, max(p1[0], p2[0], p3[0])))
        min_y = int(max(0, min(p1[1], p2[1], p3[1])))
        max_y = int(min(pyxel.height - 1, max(p1[1], p2[1], p3[1])))

        if self.edge_function(p1, p2, p3) < 0:
            p2, p3 = p3, p2

        for y in range(min_y, max_y + 1):
            for x in range(min_x, max_x + 1):
                p = (x, y)
                if (
                    self.edge_function(p1, p2, p) >= 0
                    and self.edge_function(p2, p3, p) >= 0
                    and self.edge_function(p3, p1, p) >= 0
                ):

                    threshold = self.bayer_matrix[y % 4][x % 4] / 16.0
                    if brightness > threshold:
                        pyxel.pset(x, y, color)

    def edge_function(self, p1, p2, p):
        return (p[0] - p1[0]) * (p2[1] - p1[1]) - (p[1] - p1[1]) * (p2[0] - p1[0])


# ======================================================================
# アプリケーションの実行
# ======================================================================
if __name__ == "__main__":
    App()
