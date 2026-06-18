# -*- coding: utf-8 -*-
"""
将 PPT 全局统一为第 32 页的样式：
- 居中标题（32pt）
- 描述文字区域
- 底部截图区域
"""
import copy
import re
import sys
import shutil
from pathlib import Path

from pptx import Presentation
from pptx.util import Pt, Emu
from pptx.enum.text import PP_ALIGN, MSO_AUTO_SIZE
from pptx.enum.shapes import MSO_SHAPE_TYPE

sys.stdout.reconfigure(encoding='utf-8')

SRC = Path(r'd:\文件\unibit\unibit用户操作使用手册\unibit用户操作使用手册.pptx')
BACKUP = SRC.with_suffix('.pptx.bak')
OUTPUT = SRC  # 直接覆盖原文件（已备份）

# 第32页标准位置（EMU）
TITLE_LEFT = 2567305
TITLE_TOP = 228600
TITLE_WIDTH = 4923155
TITLE_HEIGHT = 534035

CONTENT_LEFT = 838200
CONTENT_TOP = 838200
CONTENT_WIDTH = 9121140
CONTENT_MIN_HEIGHT = 790575

PIC_AREA_LEFT = 609600
PIC_AREA_TOP = 2286000
PIC_AREA_WIDTH = 8528050
PIC_AREA_HEIGHT = 4492625

TITLE_FONT_SIZE = Pt(32)
CONTENT_LINE_SPACING = Pt(28.6)


def emu_to_pt(emu):
    return round(emu / 12700, 1) if emu else None


def get_shape_text(shape):
    if not shape.has_text_frame:
        return ''
    return ''.join(
        run.text
        for para in shape.text_frame.paragraphs
        for run in para.runs
    ).strip()


def delete_shape(shape):
    el = shape._element
    el.getparent().remove(el)


def extract_title_and_body(slide, slide_idx):
    """从幻灯片中提取标题和正文"""
    title = ''
    body = ''
    group_shapes = []
    title_boxes = []
    content_boxes = []
    pictures = []

    all_texts = []

    for shape in slide.shapes:
        stype = shape.shape_type
        if stype == MSO_SHAPE_TYPE.GROUP:
            group_shapes.append(shape)
            for sub in shape.shapes:
                if sub.has_text_frame:
                    t = get_shape_text(sub)
                    if t and len(t) < 50:
                        title = t
        elif stype == MSO_SHAPE_TYPE.PICTURE:
            pictures.append(shape)
        elif shape.has_text_frame:
            text = get_shape_text(shape)
            if not text:
                continue
            all_texts.append(text)
            # 顶部居中大标题（28-32页风格）
            if shape.top < 500000 and shape.width > 3000000:
                if emu_to_pt(shape.height) and shape.height < 700000:
                    title_boxes.append((shape, text))
                    continue
            content_boxes.append((shape, text))

    # 从 title_boxes 取标题
    if title_boxes:
        title = title_boxes[0][1]

    # 从 GROUP 取标题（优先）
    for gs in group_shapes:
        for sub in gs.shapes:
            if sub.has_text_frame:
                t = get_shape_text(sub)
                if t:
                    title = t
                    break

    # 合并正文
    if content_boxes:
        # 取最大的正文框
        content_boxes.sort(key=lambda x: len(x[1]), reverse=True)
        body = content_boxes[0][1]

    # 特殊页：标题嵌在正文中
    if not title and body:
        m = re.match(r'^(注册\s*[-–]\s*(?:个人|企业)\s*KYC)\s*', body)
        if m:
            title = m.group(1).replace(' ', '')
            body = body[m.end():].strip()
        elif slide_idx == 0:  # 封面
            title = 'Unibit用户端 系统使用手册'
            all_text = ''.join(all_texts)
            date_m = re.search(r'20\d{2}-\d{2}-\d{1,2}', all_text)
            body = f'版本日期：{date_m.group()}' if date_m else '版本日期：2025-03-29'
        elif slide_idx == 1:  # 第2页
            title = '系统简介'
        elif slide_idx in (5, 6):  # 第6、7页 KYC
            m2 = re.match(r'^(注册[-–](?:个人|企业)KYC)', body.replace(' ', ''))
            if m2:
                title = m2.group(1)
                body = body[len(m2.group(0)):].strip()

    # 正文中移除与标题重复的开头
    if title and body.startswith(title):
        body = body[len(title):].strip()

    return title, body, group_shapes, title_boxes, content_boxes, pictures


def apply_title_style(text_frame, text):
    text_frame.clear()
    text_frame.word_wrap = True
    text_frame.margin_left = Emu(91440)
    text_frame.margin_top = Emu(45720)
    text_frame.margin_right = Emu(91440)
    text_frame.margin_bottom = Emu(45720)

    para = text_frame.paragraphs[0]
    para.alignment = PP_ALIGN.CENTER
    para.line_spacing = 0.9
    run = para.add_run()
    run.text = text
    run.font.size = TITLE_FONT_SIZE


def apply_content_style(text_frame, text):
    text_frame.clear()
    text_frame.word_wrap = True
    text_frame.margin_left = Emu(0)
    text_frame.margin_top = Emu(57150)
    text_frame.margin_right = Emu(0)
    text_frame.margin_bottom = Emu(0)
    text_frame.auto_size = MSO_AUTO_SIZE.SHAPE_TO_FIT_TEXT

    para = text_frame.paragraphs[0]
    para.line_spacing = CONTENT_LINE_SPACING
    para.space_before = Pt(4.5)
    run = para.add_run()
    run.text = text


def layout_pictures(slide, pictures, slide_part):
    """将图片排列到底部截图区域"""
    if not pictures:
        return

    n = len(pictures)
    if n == 1:
        pic = pictures[0]
        # 保持宽高比缩放至区域
        ratio = min(PIC_AREA_WIDTH / pic.width, PIC_AREA_HEIGHT / pic.height)
        new_w = int(pic.width * ratio)
        new_h = int(pic.height * ratio)
        left = PIC_AREA_LEFT + (PIC_AREA_WIDTH - new_w) // 2
        top = PIC_AREA_TOP + (PIC_AREA_HEIGHT - new_h) // 2

        image = pic.image
        blob = image.blob
        delete_shape(pic)
        slide.shapes.add_picture(
            slide_part.get_or_add_image_part(blob).blob if False else _image_stream(blob),
            left, top, new_w, new_h
        )
    else:
        gap = Emu(80000)
        total_gap = gap * (n - 1)
        each_w = (PIC_AREA_WIDTH - total_gap) // n
        each_h = PIC_AREA_HEIGHT

        blobs = []
        for pic in pictures:
            blobs.append(pic.image.blob)
            delete_shape(pic)

        for i, blob in enumerate(blobs):
            from io import BytesIO
            stream = BytesIO(blob)
            # 先用原始尺寸添加，再调整
            new_shape = slide.shapes.add_picture(stream, 0, 0)
            ratio = min(each_w / new_shape.width, each_h / new_shape.height)
            new_w = int(new_shape.width * ratio)
            new_h = int(new_shape.height * ratio)
            left = PIC_AREA_LEFT + i * (each_w + gap) + (each_w - new_w) // 2
            top = PIC_AREA_TOP + (PIC_AREA_HEIGHT - new_h) // 2
            new_shape.left = left
            new_shape.top = top
            new_shape.width = new_w
            new_shape.height = new_h


def _image_stream(blob):
    from io import BytesIO
    return BytesIO(blob)


def unify_slide(slide, slide_idx, prs, is_reference=False):
    """统一单页样式"""
    if is_reference:
        # 第32页：仅校正位置
        for shape in slide.shapes:
            if shape.has_text_frame:
                text = get_shape_text(shape)
                if shape.top < 500000 and '购买' in text or shape.top < 500000 and len(text) < 20:
                    shape.left = TITLE_LEFT
                    shape.top = TITLE_TOP
                    shape.width = TITLE_WIDTH
                    shape.height = TITLE_HEIGHT
                elif shape.top < 1500000:
                    shape.left = CONTENT_LEFT
                    shape.top = CONTENT_TOP
                    shape.width = CONTENT_WIDTH
            elif shape.shape_type == MSO_SHAPE_TYPE.PICTURE:
                ratio = min(PIC_AREA_WIDTH / shape.width, PIC_AREA_HEIGHT / shape.height)
                new_w = int(shape.width * ratio)
                new_h = int(shape.height * ratio)
                shape.left = PIC_AREA_LEFT + (PIC_AREA_WIDTH - new_w) // 2
                shape.top = PIC_AREA_TOP + (PIC_AREA_HEIGHT - new_h) // 2
                shape.width = new_w
                shape.height = new_h
        return

    title, body, group_shapes, title_boxes, content_boxes, pictures = extract_title_and_body(slide, slide_idx)

    # 保存图片 blob（删除前先提取）
    pic_blobs = [p.image.blob for p in pictures]

    # 删除 GROUP、旧标题框、旧正文框
    shapes_to_delete = []
    for shape in slide.shapes:
        if shape.shape_type == MSO_SHAPE_TYPE.GROUP:
            shapes_to_delete.append(shape)
        elif shape.has_text_frame:
            shapes_to_delete.append(shape)
        elif shape.shape_type == MSO_SHAPE_TYPE.PICTURE:
            shapes_to_delete.append(shape)

    for shape in shapes_to_delete:
        delete_shape(shape)

    # 添加标题
    if title:
        title_box = slide.shapes.add_textbox(
            TITLE_LEFT, TITLE_TOP, TITLE_WIDTH, TITLE_HEIGHT
        )
        apply_title_style(title_box.text_frame, title)

    # 添加正文
    if body:
        content_box = slide.shapes.add_textbox(
            CONTENT_LEFT, CONTENT_TOP, CONTENT_WIDTH, CONTENT_MIN_HEIGHT
        )
        apply_content_style(content_box.text_frame, body)

    # 添加图片
    if pic_blobs:
        from io import BytesIO
        n = len(pic_blobs)
        if n == 1:
            stream = BytesIO(pic_blobs[0])
            pic = slide.shapes.add_picture(stream, 0, 0)
            ratio = min(PIC_AREA_WIDTH / pic.width, PIC_AREA_HEIGHT / pic.height)
            new_w = int(pic.width * ratio)
            new_h = int(pic.height * ratio)
            pic.left = PIC_AREA_LEFT + (PIC_AREA_WIDTH - new_w) // 2
            pic.top = PIC_AREA_TOP + (PIC_AREA_HEIGHT - new_h) // 2
            pic.width = new_w
            pic.height = new_h
        else:
            gap = Emu(80000)
            total_gap = gap * (n - 1)
            each_w = (PIC_AREA_WIDTH - total_gap) // n
            each_h = PIC_AREA_HEIGHT
            for i, blob in enumerate(pic_blobs):
                stream = BytesIO(blob)
                pic = slide.shapes.add_picture(stream, 0, 0)
                ratio = min(each_w / pic.width, each_h / pic.height)
                new_w = int(pic.width * ratio)
                new_h = int(pic.height * ratio)
                left = PIC_AREA_LEFT + i * (each_w + gap) + (each_w - new_w) // 2
                top = PIC_AREA_TOP + (each_h - new_h) // 2
                pic.left = left
                pic.top = top
                pic.width = new_w
                pic.height = new_h

    print(f'  Slide {slide_idx + 1}: title={title!r}, body_len={len(body)}, pics={len(pic_blobs)}')


def main():
    if not SRC.exists():
        print(f'文件不存在: {SRC}')
        sys.exit(1)

    # 备份
    shutil.copy2(SRC, BACKUP)
    print(f'已备份至: {BACKUP}')

    prs = Presentation(str(SRC))
    total = len(prs.slides)
    print(f'共 {total} 页，开始统一...')

    for idx in range(total):
        slide = prs.slides[idx]
        is_ref = (idx == 31)  # 第32页作为参考，仅微调
        unify_slide(slide, idx, prs, is_reference=is_ref)

    prs.save(str(OUTPUT))
    print(f'\n已保存: {OUTPUT}')
    print('完成！')


if __name__ == '__main__':
    main()
