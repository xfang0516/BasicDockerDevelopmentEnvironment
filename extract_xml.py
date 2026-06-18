# -*- coding: utf-8 -*-
import zipfile, re, sys
sys.stdout.reconfigure(encoding='utf-8')

pptx_path = r'd:\文件\unibit\unibit用户操作使用手册\unibit用户操作使用手册.pptx'
with zipfile.ZipFile(pptx_path) as z:
    for slide_num in [32, 3, 28, 1]:
        xml = z.read(f'ppt/slides/slide{slide_num}.xml').decode('utf-8')
        print(f'=== Slide {slide_num} ===')
        texts = re.findall(r'<a:t>([^<]*)</a:t>', xml)
        for t in texts:
            print(f'  text: {t[:80]}')
        sizes = set(int(m)/100 for m in re.findall(r'sz="(\d+)"', xml))
        print(f'  font sizes: {sorted(sizes)}')
        # positions
        offs = re.findall(r'<a:off x="(\d+)" y="(\d+)"/>', xml)
        exts = re.findall(r'<a:ext cx="(\d+)" cy="(\d+)"/>', xml)
        print(f'  positions: {offs[:5]}')
        print(f'  sizes: {exts[:5]}')
        print()
