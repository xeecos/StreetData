# StreetData

中国范围栅格瓦片底图，供 [ch32v467-cam](https://github.com/xeecos/ch32v467-cam)
的「光污染」栏目使用：出门前看头顶这片天有多亮、往哪开一小时能到暗区。

由 OpenStreetMap 数据离屏渲染，Web Mercator / 256 px，缩放 **z4–z12**。

## 用法

```
https://cdn.jsdmirror.com/gh/xeecos/StreetData@2026.11.5/{z}/{x}/{y}.webp
https://cdn.osyb.cn/gh/xeecos/StreetData@2026.11.5/{z}/{x}/{y}.webp
https://cdn.jsdelivr.net/gh/xeecos/StreetData@2026.11.5/{z}/{x}/{y}.webp
https://raw.githubusercontent.com/xeecos/StreetData/2026.11.5/{z}/{x}/{y}.webp
```

前两个是国内节点，客户端默认按这个顺序试；jsDelivr 只作兜底
（本仓库已超出它惯常的体积门限，不保证服务），raw 最后。

- z ≥ 8 的路径多一层分桶：`{z}/{x>>3}/{x}/{y}.{ext}`
- **当前所有瓦片都是 `.webp`**（z4–z7 逐片比过 WebP/JPEG，WebP 100% 更小）。
  `index.json` 仍保留 `ext_jpg` 位图（现在全 0）以便将来出现 JPEG 时不必改 schema；
  为 0 时一律按 `.webp` 取。
- `index.json` 的 `present` 位图为 0 的位置**没有文件**，直接画
  `base/blank.webp`（纯海/纯陆，内容全同）。
- 位图布局：行优先，索引 = `(y - y0) * (x1 - x0 + 1) + (x - x0)`，MSB 在前。

## 目录

```
index.json                  片范围 + present/ext 位图 + 体积
base/blank.webp             空片替身
base/{z}/{x}/{y}.{webp,jpg}          z ≤ 7
base/{z}/{x>>3}/{x}/{y}.{webp,jpg}   z ≥ 8
tools/verify.py             逐片 magic byte + 尺寸 + 片数核对
```

## 数据

- 数据源：Geofabrik `china` + `taiwan` 提取，osmium merge
- 渲染：osm2pgsql → PostGIS → openstreetmap-carto → Mapnik（8×8 metatile）
- 署名与许可：见 [ATTRIBUTION.md](ATTRIBUTION.md)，**© OpenStreetMap contributors，ODbL 1.0**

## 体积

合计 239205198 字节
（单文件 ≤ 20 MB、仓库 ≤ 150 MB —— jsDelivr 的限制）。
