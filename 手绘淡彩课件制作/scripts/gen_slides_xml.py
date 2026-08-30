# -*- coding: utf-8 -*-
"""
手绘淡彩课件制作 - 批量生成幻灯片XML脚本
用法：修改下方 tokens 和 notes 字典，然后运行 python gen_slides_xml.py
每页生成一个 new_slide_NN.xml 文件，包含全屏图片 + 演讲者备注
"""

import os

# ========== 配置区：修改以下内容 ==========

# file_token 映射：序号 -> 上传图片后获得的 file_token
tokens = {
    '01': '在此填入第1页的file_token',
    '02': '在此填入第2页的file_token',
    # '03': '...',
    # 继续添加...
}

# 演讲者备注：序号 -> 3-5句可直接照读的讲稿
notes = {
    '01': '在此填入第1页的演讲者备注。',
    '02': '在此填入第2页的演讲者备注。',
    # '03': '...',
    # 继续添加...
}

# 输出目录（当前目录）
OUTPUT_DIR = '.'

# ========== 以下为生成逻辑，一般不需要修改 ==========

def gen_xml(token, note):
    """生成单页XML：全屏图片 + 演讲者备注"""
    return (
        '<slide>\n'
        '  <data>\n'
        '    <img src="' + token + '" topLeftX="0" topLeftY="0" width="960" height="540"/>\n'
        '  </data>\n'
        '  <note>\n'
        '    <content textType="body">\n'
        '      <p>' + note + '</p>\n'
        '    </content>\n'
        '  </note>\n'
        '</slide>'
    )

def main():
    count = 0
    for num, token in tokens.items():
        if num not in notes:
            print('警告：第' + num + '页缺少演讲者备注，跳过')
            continue
        note = notes[num]
        xml = gen_xml(token, note)
        out_path = os.path.join(OUTPUT_DIR, 'new_slide_' + num + '.xml')
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(xml)
        print('已生成 ' + out_path)
        count += 1
    print('全部' + str(count) + '页XML生成完成')

if __name__ == '__main__':
    main()
