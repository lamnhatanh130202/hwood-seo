# -*- coding: utf-8 -*-
"""
GRAPHIFY ENGINE FOR ANTIGRAVITY
================================
Xây dựng Đồ thị tri thức (Knowledge Graph) toàn diện cho Codebase bằng AST Parsing.
Không cần phụ thuộc bên ngoài, chạy cục bộ 100%, bảo mật tuyệt đối.

Tạo ra 3 file đầu ra chuẩn trong thư mục graphify-out/:
  1. graph.json       - Bản đồ dữ liệu nút (nodes) và liên kết (edges) cho AI đọc
  2. GRAPH_REPORT.md  - Báo cáo cấu trúc hệ thống, hàm gọi nhau & độ phức tạp
  3. graph.html       - Giao diện đồ thị mạng lưới tương tác trực quan xem trên trình duyệt
"""

import os
import sys
import ast
import json
import html
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set, Any

class CodebaseGraphifier:
    def __init__(self, root_dir: str = "."):
        self.root_dir = Path(root_dir).resolve()
        self.nodes = []
        self.edges = []
        self.files_map = {}
        self.functions_map = {}
        self.classes_map = {}
        self.calls_map = []
        self.imports_map = []
        self.summary = {
            "total_files": 0,
            "total_lines": 0,
            "total_functions": 0,
            "total_classes": 0,
            "total_imports": 0,
            "total_calls": 0,
            "generated_at": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        }

    def should_ignore(self, path: Path) -> bool:
        ignore_dirs = {
            ".git", "__pycache__", ".venv", "venv", "env", "node_modules",
            ".gemini", ".idea", ".vscode", "graphify-out", ".agent", ".agents"
        }
        for part in path.parts:
            if part in ignore_dirs:
                return True
        return False

    def scan_codebase(self):
        print(f"🔍 [Graphify] Bắt đầu quét mã nguồn tại: {self.root_dir}")
        for path in self.root_dir.rglob("*.py"):
            if self.should_ignore(path):
                continue
            self.analyze_python_file(path)

        # Xây dựng các cạnh (edges) từ hàm gọi nhau
        self.build_call_edges()

    def analyze_python_file(self, file_path: Path):
        rel_path = file_path.relative_to(self.root_dir).as_posix()
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception:
            try:
                with open(file_path, "r", encoding="latin-1") as f:
                    content = f.read()
            except Exception:
                return

        lines_count = len(content.splitlines())
        self.summary["total_files"] += 1
        self.summary["total_lines"] += lines_count

        file_node_id = f"file::{rel_path}"
        self.nodes.append({
            "id": file_node_id,
            "type": "file",
            "name": file_path.name,
            "path": rel_path,
            "lines": lines_count,
            "group": rel_path.split("/")[0] if "/" in rel_path else "root"
        })
        self.files_map[rel_path] = {
            "node_id": file_node_id,
            "lines": lines_count,
            "functions": [],
            "classes": [],
            "imports": []
        }

        try:
            tree = ast.parse(content, filename=str(file_path))
        except Exception as e:
            return

        # Bóc tách AST: Imports, Classes, Functions, Calls
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imp_name = alias.name
                    self.summary["total_imports"] += 1
                    self.imports_map.append({
                        "file": rel_path,
                        "imported": imp_name
                    })
                    # Cạnh import
                    self.edges.append({
                        "source": file_node_id,
                        "target": f"pkg::{imp_name}",
                        "relation": "imports"
                    })
            elif isinstance(node, ast.ImportFrom):
                mod_name = node.module or ""
                self.summary["total_imports"] += 1
                for alias in node.names:
                    full_name = f"{mod_name}.{alias.name}" if mod_name else alias.name
                    self.imports_map.append({
                        "file": rel_path,
                        "imported": full_name
                    })
                    self.edges.append({
                        "source": file_node_id,
                        "target": f"symbol::{full_name}",
                        "relation": "imports_from"
                    })

            elif isinstance(node, ast.ClassDef):
                self.summary["total_classes"] += 1
                cls_id = f"class::{rel_path}::{node.name}"
                doc = ast.get_docstring(node) or ""
                doc_summary = doc.strip().split("\n")[0] if doc else ""
                self.nodes.append({
                    "id": cls_id,
                    "type": "class",
                    "name": node.name,
                    "file": rel_path,
                    "line": node.lineno,
                    "doc": doc_summary,
                    "group": "classes"
                })
                self.edges.append({
                    "source": file_node_id,
                    "target": cls_id,
                    "relation": "defines_class"
                })
                self.classes_map[f"{rel_path}::{node.name}"] = cls_id

            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self.summary["total_functions"] += 1
                func_id = f"func::{rel_path}::{node.name}"
                doc = ast.get_docstring(node) or ""
                doc_summary = doc.strip().split("\n")[0] if doc else ""
                args = [arg.arg for arg in node.args.args]
                
                func_data = {
                    "id": func_id,
                    "type": "function",
                    "name": node.name,
                    "file": rel_path,
                    "line": node.lineno,
                    "args": args,
                    "is_async": isinstance(node, ast.AsyncFunctionDef),
                    "doc": doc_summary,
                    "group": "functions"
                }
                self.nodes.append(func_data)
                self.functions_map[node.name] = func_id
                self.files_map[rel_path]["functions"].append(func_data)
                self.edges.append({
                    "source": file_node_id,
                    "target": func_id,
                    "relation": "defines_function"
                })

                # Quét các lời gọi hàm bên trong hàm này
                for sub in ast.walk(node):
                    if isinstance(sub, ast.Call):
                        called_name = None
                        if isinstance(sub.func, ast.Name):
                            called_name = sub.func.id
                        elif isinstance(sub.func, ast.Attribute):
                            called_name = sub.func.attr
                        if called_name:
                            self.calls_map.append({
                                "caller": func_id,
                                "callee": called_name,
                                "file": rel_path
                            })

    def build_call_edges(self):
        """Xây dựng liên kết gọi hàm giữa các module (call graph)"""
        for call in self.calls_map:
            callee_name = call["callee"]
            caller_id = call["caller"]
            if callee_name in self.functions_map:
                target_id = self.functions_map[callee_name]
                if caller_id != target_id:
                    self.summary["total_calls"] += 1
                    self.edges.append({
                        "source": caller_id,
                        "target": target_id,
                        "relation": "calls"
                    })

    def export_graph_json(self, out_dir: Path):
        graph_data = {
            "summary": self.summary,
            "nodes": self.nodes,
            "edges": self.edges,
            "files": self.files_map
        }
        json_path = out_dir / "graph.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(graph_data, f, ensure_ascii=False, indent=2)
        print(f"  [OK] Đã xuất {json_path} ({len(self.nodes)} nút, {len(self.edges)} liên kết)")

    def export_graph_report_md(self, out_dir: Path):
        md_path = out_dir / "GRAPH_REPORT.md"
        with open(md_path, "w", encoding="utf-8") as f:
            f.write("# 🧭 BÁO CÁO ĐỒ THỊ TRI THỨC MÃ NGUỒN (CODEBASE KNOWLEDGE GRAPH)\n\n")
            f.write(f"> **Thời gian tạo:** {self.summary['generated_at']}  \n")
            f.write(f"> **Tổng quan:** `{self.summary['total_files']} files` | `{self.summary['total_lines']} dòng code` | `{self.summary['total_functions']} hàm` | `{self.summary['total_classes']} classes` | `{self.summary['total_calls']} liên kết gọi hàm`\n\n")
            f.write("---\n\n")
            f.write("## 🗂️ 1. Bản Đồ Danh Mục Files & Kiến Trúc\n\n")
            
            for rel_path, data in sorted(self.files_map.items()):
                f.write(f"### 📄 `{rel_path}` ({data['lines']} dòng)\n")
                if data["functions"]:
                    f.write("**Các hàm định nghĩa:**\n")
                    for fn in data["functions"]:
                        doc_str = f" - *{fn['doc']}*" if fn['doc'] else ""
                        async_str = "`async` " if fn["is_async"] else ""
                        f.write(f"- {async_str}**`{fn['name']}({', '.join(fn['args'])})`** (dòng {fn['line']}){doc_str}\n")
                f.write("\n")

            f.write("---\n\n")
            f.write("## 🔗 2. Sơ Đồ Mối Quan Hệ Gọi Hàm (Key Function Calls)\n\n")
            f.write("| Hàm gọi (Caller) | Hàm được gọi (Callee) | Loại liên kết |\n")
            f.write("| :--- | :--- | :--- |\n")
            call_edges = [e for e in self.edges if e["relation"] == "calls"]
            for e in call_edges[:60]:
                c_from = e["source"].split("::")[-1]
                c_to = e["target"].split("::")[-1]
                f_from = e["source"].split("::")[1]
                f_to = e["target"].split("::")[1]
                f.write(f"| `{c_from}` ({f_from}) | `{c_to}` ({f_to}) | `calls` |\n")

            if len(call_edges) > 60:
                f.write(f"| *...và {len(call_edges) - 60} liên kết gọi hàm khác trong graph.json* | | |\n")

            f.write("\n---\n")
            f.write("💡 *Mẹo dành cho AI Agent: Tra cứu file này hoặc `graph.json` trước khi đọc từng file để tiết kiệm token và nắm bắt chuẩn xác điểm ảnh hưởng (blast radius).*")

        print(f"  [OK] Đã xuất {md_path}")

    def export_graph_html(self, out_dir: Path):
        """Tạo giao diện mạng lưới đồ thị tương tác HTML5 Canvas / SVG có thể zoom, pan, click xem chi tiết"""
        html_path = out_dir / "graph.html"
        
        # Lọc danh sách nodes & links gọn nhẹ để hiển thị mượt mà
        vis_nodes = []
        for n in self.nodes:
            color = "#4CAF50" if n["type"] == "file" else ("#2196F3" if n["type"] == "function" else "#FF9800")
            size = 15 if n["type"] == "file" else (10 if n["type"] == "class" else 7)
            vis_nodes.append({
                "id": n["id"],
                "label": n["name"],
                "type": n["type"],
                "color": color,
                "size": size,
                "title": f"[{n['type'].upper()}] {n.get('path', '')} (dòng {n.get('line', '')})"
            })

        vis_edges = []
        for e in self.edges:
            vis_edges.append({
                "from": e["source"],
                "to": e["target"],
                "relation": e["relation"]
            })

        html_content = f"""<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HWOOD Codebase Knowledge Graph - Graphify</title>
    <script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            margin: 0;
            padding: 0;
            background: #0f172a;
            color: #f8fafc;
            overflow: hidden;
        }}
        #header {{
            position: absolute;
            top: 15px;
            left: 20px;
            z-index: 100;
            background: rgba(30, 41, 59, 0.85);
            backdrop-filter: blur(8px);
            padding: 14px 22px;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.4);
            border: 1px solid #334155;
        }}
        h1 {{
            margin: 0 0 6px 0;
            font-size: 19px;
            color: #38bdf8;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .stats {{
            font-size: 13px;
            color: #94a3b8;
        }}
        .legend {{
            margin-top: 8px;
            font-size: 12px;
            display: flex;
            gap: 14px;
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 5px;
        }}
        .dot {{
            width: 10px;
            height: 10px;
            border-radius: 50%;
            display: inline-block;
        }}
        #network {{
            width: 100vw;
            height: 100vh;
        }}
        #details {{
            position: absolute;
            bottom: 20px;
            right: 20px;
            z-index: 100;
            background: rgba(30, 41, 59, 0.9);
            padding: 14px 18px;
            border-radius: 10px;
            border: 1px solid #334155;
            max-width: 320px;
            font-size: 13px;
            display: none;
        }}
    </style>
</head>
<body>
    <div id="header">
        <h1>🪵 Graphify - Đồ Thị Tri Thức Codebase</h1>
        <div class="stats">
            {self.summary['total_files']} Files • {self.summary['total_functions']} Functions • {self.summary['total_classes']} Classes • {len(vis_edges)} Connections
        </div>
        <div class="legend">
            <div class="legend-item"><span class="dot" style="background:#4CAF50"></span> File</div>
            <div class="legend-item"><span class="dot" style="background:#2196F3"></span> Function</div>
            <div class="legend-item"><span class="dot" style="background:#FF9800"></span> Class</div>
        </div>
    </div>

    <div id="details"></div>
    <div id="network"></div>

    <script>
        const nodes = new vis.DataSet({json.dumps(vis_nodes, ensure_ascii=False)});
        const edges = new vis.DataSet({json.dumps(vis_edges, ensure_ascii=False)});

        const container = document.getElementById('network');
        const data = {{ nodes: nodes, edges: edges }};
        const options = {{
            nodes: {{
                shape: 'dot',
                font: {{ color: '#f8fafc', size: 12 }}
            }},
            edges: {{
                arrows: 'to',
                color: {{ color: '#475569', highlight: '#38bdf8' }},
                smooth: {{ type: 'continuous' }}
            }},
            physics: {{
                stabilization: false,
                barnesHut: {{
                    gravitationalConstant: -2000,
                    springConstant: 0.04,
                    springLength: 95
                }}
            }},
            interaction: {{
                hover: true,
                tooltipDelay: 150
            }}
        }};

        const network = new vis.Network(container, data, options);

        network.on("click", function (params) {{
            if (params.nodes.length > 0) {{
                const nodeId = params.nodes[0];
                const node = nodes.get(nodeId);
                const detailsBox = document.getElementById('details');
                detailsBox.style.display = 'block';
                detailsBox.innerHTML = `<strong>${{node.label}}</strong><br><span style="color:#94a3b8">Loại: ${{node.type}}</span><br><small>${{nodeId}}</small>`;
            }}
        }});
    </script>
</body>
</html>
"""
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"  [OK] Đã xuất {html_path} (mở trên trình duyệt để xem sơ đồ mạng lưới)")

    def run(self):
        start_time = time.time()
        self.scan_codebase()
        
        out_dir = self.root_dir / "graphify-out"
        out_dir.mkdir(exist_ok=True)

        self.export_graph_json(out_dir)
        self.export_graph_report_md(out_dir)
        self.export_graph_html(out_dir)

        duration = round(time.time() - start_time, 2)
        print(f"\n🎉 [Graphify Hoàn Tất] Quét xong {self.summary['total_files']} files trong {duration}s!")
        print(f"👉 Mở xem đồ thị trực quan tại: {out_dir / 'graph.html'}\n")

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "."
    graphifier = CodebaseGraphifier(target)
    graphifier.run()
