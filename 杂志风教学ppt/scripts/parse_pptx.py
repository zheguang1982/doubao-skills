import zipfile
import xml.etree.ElementTree as ET
import os
import json
import re

PPTX_PATH = r"C:\Users\实验\Desktop\1 桂花雨【新课标版】.pptx"
OUT_DIR = r"C:\Users\实验\Doubao\chats\2026-09-02\new-chat\guihua_work"

ns = {
    'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
    'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
    'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
}

def extract_text_from_shape(shape):
    texts = []
    for t in shape.iter('{http://schemas.openxmlformats.org/drawingml/2006/main}t'):
        if t.text:
            texts.append(t.text)
    return ''.join(texts)

def get_shape_info(shape):
    info = {'type': shape.tag.split('}')[-1], 'text': '', 'has_image': False, 'image_rel': None}
    # text
    info['text'] = extract_text_from_shape(shape)
    # image check
    for blip in shape.iter('{http://schemas.openxmlformats.org/drawingml/2006/main}blip'):
        embed = blip.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed')
        if embed:
            info['has_image'] = True
            info['image_rel'] = embed
    return info

with zipfile.ZipFile(PPTX_PATH, 'r') as z:
    # List all slide files
    slide_files = sorted([n for n in z.namelist() if re.match(r'ppt/slides/slide\d+\.xml$', n)],
                         key=lambda x: int(re.search(r'slide(\d+)', x).group(1)))
    
    print(f"Total slides: {len(slide_files)}")
    print("="*80)
    
    all_slides = []
    
    for sf in slide_files:
        slide_num = int(re.search(r'slide(\d+)', sf).group(1))
        content = z.read(sf)
        root = ET.fromstring(content)
        
        # Get relationships for this slide
        rel_file = f"ppt/slides/_rels/slide{slide_num}.xml.rels"
        rels = {}
        if rel_file in z.namelist():
            rel_content = z.read(rel_file)
            rel_root = ET.fromstring(rel_content)
            for rel in rel_root:
                rid = rel.get('Id')
                target = rel.get('Target')
                rels[rid] = target
        
        shapes_info = []
        for sp in root.iter('{http://schemas.openxmlformats.org/presentationml/2006/main}sp'):
            info = get_shape_info(sp)
            if info['text'] or info['has_image']:
                shapes_info.append(info)
        
        for pic in root.iter('{http://schemas.openxmlformats.org/presentationml/2006/main}pic'):
            info = get_shape_info(pic)
            if info['text'] or info['has_image']:
                shapes_info.append(info)
        
        # notes
        notes_text = ""
        notes_file = f"ppt/notesSlides/notesSlide{slide_num}.xml"
        if notes_file in z.namelist():
            notes_content = z.read(notes_file)
            notes_root = ET.fromstring(notes_content)
            notes_text = extract_text_from_shape(notes_root)
        
        slide_data = {
            'slide_num': slide_num,
            'shapes': shapes_info,
            'notes': notes_text,
            'image_files': [rels.get(s['image_rel'], '') for s in shapes_info if s['has_image'] and s['image_rel'] in rels]
        }
        all_slides.append(slide_data)
        
        print(f"\n--- Slide {slide_num} ---")
        for i, s in enumerate(shapes_info):
            label = f"[{'IMG' if s['has_image'] else 'TXT'}]"
            txt = s['text'][:100] if s['text'] else '(no text)'
            print(f"  {label} Shape {i}: {txt}")
            if s['has_image'] and s['image_rel'] in rels:
                print(f"         -> image: {rels[s['image_rel']]}")
        if notes_text:
            print(f"  NOTES: {notes_text[:150]}")
    
    # Save full JSON
    with open(os.path.join(OUT_DIR, 'pptx_content.json'), 'w', encoding='utf-8') as f:
        json.dump(all_slides, f, ensure_ascii=False, indent=2)
    
    # Extract all media files
    media_dir = os.path.join(OUT_DIR, 'media')
    os.makedirs(media_dir, exist_ok=True)
    media_files = [n for n in z.namelist() if n.startswith('ppt/media/')]
    for mf in media_files:
        out_path = os.path.join(media_dir, os.path.basename(mf))
        with open(out_path, 'wb') as f:
            f.write(z.read(mf))
    print(f"\n\nExtracted {len(media_files)} media files to {media_dir}")
    for mf in sorted(media_files):
        info = z.getinfo(mf)
        print(f"  {mf} ({info.file_size} bytes)")
