import os

path = os.path.join(os.getcwd(), 'auditoria_app', 'static', 'img')
print("Arquivos em static/img/:")
for f in os.listdir(path):
    print("-", f)
