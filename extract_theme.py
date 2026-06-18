# -*- coding: utf-8 -*-
import zipfile, re, sys
sys.stdout.reconfigure(encoding='utf-8')

pptx_path = r'd:\文件\unibit\unibit用户操作使用手册\unibit用户操作使用手册.pptx'
with zipfile.ZipFile(pptx_path) as z:
    for name in z.namelist():
        if 'slideLayout' in name or 'theme' in name:
            if name.endswith('.xml'):
                xml = z.read(name).decode('utf-8')
                sizes = set(int(m)/100 for m in re.findall(r'sz="(\d+)"', xml))
                if sizes:
                    print(f'{name}: font sizes {sorted(sizes)}')

    # slide32 content run properties
    xml32 = z.read('ppt/slides/slide32.xml').decode('utf-8')
    # find body text run
    idx = xml32.find('用户在Unibit')
    print('\nSlide32 body XML snippet:')
    print(xml32[idx-500:idx+200])
