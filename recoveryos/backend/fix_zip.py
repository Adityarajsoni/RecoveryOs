import os
import zipfile

with open('Procfile', 'w', encoding='utf-8', newline='\n') as f:
    f.write("web: python -m uvicorn app.main:app --host 0.0.0.0 --port 8000\n")

targets = ['app', 'data', '.env', 'Procfile', 'requirements.txt', 'dist']
zip_filename = 'backend_deployment.zip'
if os.path.exists(zip_filename):
    os.remove(zip_filename)

with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zf:
    for target in targets:
        if not os.path.exists(target):
            continue
        if os.path.isfile(target):
            zf.write(target, target.replace('\\', '/'))
        else:
            for root, dirs, files in os.walk(target):
                if '__pycache__' in root:
                    continue
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, start='.').replace('\\', '/')
                    zf.write(file_path, arcname)
print('Fixed Procfile port to 8000 and zipped!')
