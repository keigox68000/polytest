import pyxel
import math
import re

# このコードを wrl_viewer_web.py として保存してください

# デフォルトで表示するモデルデータ（トーラス）
DEFAULT_WRL_DATA = """
#VRML V2.0 utf8
DEF Torus1 Transform {
  children [
    Shape {
      geometry IndexedFaceSet {
        coord Coordinate {
          point [
            1.25 -0.0 0.0, 1.0 -0.25 0.0, 0.75 -0.0 0.0, 1.0 0.25 0.0,
            0.883883 -0.0 0.883883, 0.707107 -0.25 0.707107, 0.53033 -0.0 0.53033,
            0.707107 0.25 0.707107, 0.0 -0.0 1.25, 0.0 -0.25 1.0, 0.0 -0.0 0.75,
            0.0 0.25 1.0, -0.883883 -0.0 0.883883, -0.707107 -0.25 0.707107,
            -0.53033 -0.0 0.53033, -0.707107 0.25 0.707107, -1.25 -0.0 0.0,
            -1.0 -0.25 0.0, -0.75 -0.0 0.0, -1.0 0.25 0.0, -0.883883 -0.0 -0.883883,
            -0.707107 -0.25 -0.707107, -0.53033 -0.0 -0.53033, -0.707107 0.25 -0.707107,
            0.0 -0.0 -1.25, 0.0 -0.25 -1.0, 0.0 -0.0 -0.75, 0.0 0.25 -1.0,
            0.883883 -0.0 -0.883883, 0.707107 -0.25 -0.707107, 0.53033 -0.0 -0.53033,
            0.707107 0.25 -0.707107
          ]
        }
        coordIndex [
          0, 1, 29, 28, -1, 0, 3, 7, 4, -1, 0, 4, 5, 1, -1, 0, 28, 31, 3, -1,
          1, 2, 30, 29, -1, 1, 5, 6, 2, -1, 2, 3, 31, 30, -1, 2, 6, 7, 3, -1,
          4, 7, 11, 8, -1, 4, 8, 9, 5, -1, 5, 9, 10, 6, -1, 6, 10, 11, 7, -1,
          8, 11, 15, 12, -1, 8, 12, 13, 9, -1, 9, 13, 14, 10, -1, 10, 14, 15, 11, -1,
          12, 15, 19, 16, -1, 12, 16, 17, 13, -1, 13, 17, 18, 14, -1, 14, 18, 19, 15, -1,
          16, 19, 23, 20, -1, 16, 20, 21, 17, -1, 17, 21, 22, 18, -1, 18, 22, 23, 19, -1,
          20, 23, 27, 24, -1, 20, 24, 25, 21, -1, 21, 25, 26, 22, -1, 22, 26, 27, 23, -1,
          24, 27, 31, 28, -1, 24, 28, 29, 25, -1, 25, 29, 30, 26, -1, 26, 30, 31, 27, -1
        ]
      }
    }
  ]
}
"""

BAYER_MATRIX = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]

# Appインスタンスをグローバルに保持するための変数
app_instance = None


def load_wrl_data(wrl_string):
    """
    JavaScriptから呼び出される関数。
    新しいWRLデータ（文字列）を読み込んでモデルを更新する。
    """
    if app_instance:
        app_instance.load_new_model(wrl_string)


class App:
    def __init__(self):
        global app_instance
        app_instance = self

        pyxel.init(320, 240, title="WRL Dithered Polygon", fps=60)

        self.screen_center_x = pyxel.width / 2
        self.screen_center_y = pyxel.height / 2

        self.angle_x = 0
        self.angle_y = 0

        self.light_vec = [0, 0, -1]
        self.ambient_light = 0.2

        self.model_v = []
        self.model_f = []
        self.message = ""

        self.is_auto_rotate = True
        self.last_mouse_x = 0
        self.last_mouse_y = 0
        pyxel.mouse(True)

        # デフォルトのモデルを読み込む
        self.load_new_model(DEFAULT_WRL_DATA)

        pyxel.run(self.update, self.draw)

    def load_new_model(self, wrl_data_string):
        """新しいWRLデータをパースしてモデルを更新する"""
        try:
            self.model_v, self.model_f = self.parse_wrl(wrl_data_string, scale=50.0)
            if not self.model_v:
                self.message = "Failed to parse WRL data."
            else:
                self.message = ""
        except Exception as e:
            self.message = f"Error: {e}"

    def parse_wrl(self, wrl_data, scale=1.0):
        vertices = []
        point_match = re.search(r"point\s*\[(.*?)\]", wrl_data, re.S)
        if point_match:
            point_data = re.findall(
                r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", point_match.group(1)
            )
            points_float = [float(p) for p in point_data]
            for i in range(0, len(points_float), 3):
                vertices.append(
                    [
                        points_float[i] * scale,
                        -points_float[i + 1] * scale,
                        points_float[i + 2] * scale,
                    ]
                )

        faces = []
        coord_match = re.search(r"coordIndex\s*\[(.*?)\]", wrl_data, re.S)
        if coord_match:
            index_data = [int(i) for i in re.findall(r"-?\d+", coord_match.group(1))]
            current_face = []
            for index in index_data:
                if index == -1:
                    if len(current_face) == 3:
                        faces.append(tuple(current_face))
                    elif len(current_face) == 4:
                        faces.append(
                            (current_face[0], current_face[1], current_face[2])
                        )
                        faces.append(
                            (current_face[0], current_face[2], current_face[3])
                        )
                    current_face = []
                else:
                    current_face.append(index)
        return vertices, faces

    def update(self):
        if pyxel.btnp(pyxel.MOUSE_BUTTON_RIGHT):
            self.is_auto_rotate = not self.is_auto_rotate

        if self.is_auto_rotate:
            self.angle_x = (pyxel.frame_count * 0.01) % (2 * math.pi)
            self.angle_y = (pyxel.frame_count * 0.015) % (2 * math.pi)
        else:
            if pyxel.btn(pyxel.MOUSE_BUTTON_LEFT):
                dx = pyxel.mouse_x - self.last_mouse_x
                dy = pyxel.mouse_y - self.last_mouse_y
                self.angle_y += dx * 0.01
                self.angle_x -= dy * 0.01

        self.last_mouse_x = pyxel.mouse_x
        self.last_mouse_y = pyxel.mouse_y

    def draw(self):
        pyxel.cls(0)

        if self.model_v and self.model_f:
            self.draw_solid_polygon(self.model_v, self.model_f, 0, 0, 11)
        elif self.message:
            pyxel.text(10, 10, self.message, 7)

        mode_text = (
            "Mode: Auto (Right-click)"
            if self.is_auto_rotate
            else "Mode: Manual (Drag Left-click)"
        )
        pyxel.text(5, pyxel.height - 15, mode_text, 7)
        pyxel.text(5, pyxel.height - 8, "Drop a .wrl file to view", 7)

    def draw_solid_polygon(self, vertices, faces, offset_x, offset_y, color):
        rotated_points = []
        projected_points = []

        cos_x, sin_x = math.cos(self.angle_x), math.sin(self.angle_x)
        cos_y, sin_y = math.cos(self.angle_y), math.sin(self.angle_y)

        for v in vertices:
            x, y, z = v[0], v[1], v[2]
            rx = x * cos_y - z * sin_y
            rz = x * sin_y + z * cos_y
            ry = y * cos_x - rz * sin_x
            final_z = y * sin_x + rz * cos_x
            rotated_points.append([rx, ry, final_z])

            perspective = 300 / (300 - final_z)
            px = rx * perspective + self.screen_center_x + offset_x
            py = ry * perspective + self.screen_center_y + offset_y
            projected_points.append((px, py))

        polygons_to_draw = []
        for f in faces:
            if any(idx >= len(rotated_points) for idx in f):
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
                    threshold = BAYER_MATRIX[y % 4][x % 4] / 16.0
                    if brightness > threshold:
                        pyxel.pset(x, y, color)

    def edge_function(self, p1, p2, p):
        return (p[0] - p1[0]) * (p2[1] - p1[1]) - (p[1] - p1[1]) * (p2[0] - p1[0])


App()
