# -*- coding: utf-8 -*-
"""生成 IExpress SED 自解压安装包描述文件"""
import os

BASE = 'dist/懒人畅听大师_便携版'

files = []
for root, dirs, fnames in os.walk(BASE):
    for f in fnames:
        full = os.path.join(root, f)
        rel = os.path.relpath(full, BASE)
        files.append(rel.replace('\\', '\\'))

print('文件数:', len(files))

sed = []
sed.append('[Version]')
sed.append('Class=IEXPRESS')
sed.append('SEDVersion=3')
sed.append('')
sed.append('[Options]')
sed.append('PackagePurpose=InstallApp')
sed.append('ShowInstallProgram=Hide')
sed.append('HideExtractAnimationHandler=1')
sed.append('UseCustomExtractCommand=1')
sed.append('CustomExtractCommand=install.bat')
sed.append('UninstallCommand=')
sed.append('ExtractFilename=懒人畅听大师_解压')
sed.append('')
sed.append('[Strings]')
sed.append('Title=懒人听书畅听大师 v2.0.0 安装')
sed.append('Prompt=正在解压并安装，请稍候...')
sed.append('')
sed.append('[SourceFiles]')
sed.append('SourceFiles=')
# 每行一个文件，使用反斜杠相对路径
for f in files:
    sed.append(f)
sed.append('')
sed.append('[SourceFiles0]')
sed.append('SourceFiles0=dist\\懒人畅听大师_便携版\\')

open('_tools/iexpress_setup.sed', 'w', encoding='utf-8-sig').write('\n'.join(sed))
print('SED 已生成: _tools/iexpress_setup.sed, 行数:', len(sed))
