# Guia de Criação de Ícone — Organizador de Ficheiros

## Formato final necessário

A aplicação usa PyInstaller, que aceita um ficheiro `.ico` como ícone do executável. O ficheiro `.ico` deve conter múltiplas resoluções internamente.

## Tamanhos a exportar no Illustrator

| Tamanho | Uso |
|---------|-----|
| **16×16** | Ícone na barra de título, lista de ficheiros |
| **24×24** | Barra de tarefas (Windows 10/11 pequena) |
| **32×32** | Ícone no explorador de ficheiros |
| **48×48** | Ambiente de trabalho (padrão) |
| **64×64** | Ambiente de trabalho (HiDPI 125%) |
| **128×128** | Ambiente de trabalho (HiDPI 150%) |
| **256×256** | Propriedades do ficheiro, loja, alta resolução |

> **Regra:** cria um artboard de **256×256** no Illustrator e exporta PNGs para cada tamanho a partir dele.

## Recomendações de design

- **Forma base:** pasta/biblioteca ou caixa organizada — comunica "organização de ficheiros"
- **Simplicidade:** evita detalhes finos, não se veem a 16×16
- **Contraste alto:** fundo escuro + elemento claro (a app tem tema escuro, o ícone pode usar tons de laranja `#e67e22` e azul `#2980b9`)
- **Sem texto** (ou no máximo 1-2 letras grandes como monograma)
- **Cantos arredondados** para consistência com o estilo Windows 11
- **Alinhamento à grelha de pixels** — ativa *Pixel Preview* no Illustrator (`Alt + Ctrl + Y`) para garantir nitidez nos tamanhos pequenos
- **Espaço de segurança** mínimo de 8% em cada lado (o ícone nunca toca as bordas)

## Paleta sugerida

| Cor | Hex |
|-----|-----|
| Laranja principal | `#e67e22` |
| Laranja escuro | `#d35400` |
| Azul escuro | `#1e1e2f` |
| Branco/cinza claro | `#e0e0e8` |

## Passo-a-passo no Illustrator

1. **Novo ficheiro** → 256×256 px, RGB
2. **Ativar Snap to Pixel** → `Editar → Preferências → Geral → Alinhar à grelha de pixels`
3. **Criar o ícone** (forma base + detalhes)
4. **Exportar** → `Ficheiro → Exportar → Exportar para écrans` → criar écrans para 16, 24, 32, 48, 64, 128, 256 → formato PNG

## Converter PNGs para `.ico`

### Opção 1 — Online (rápido)
Usa https://icoconvert.com — carrega o PNG 256×256, seleciona todos os tamanhos e descarrega `.ico`.

### Opção 2 — Python (local)
```bash
pip install Pillow
```

```python
from PIL import Image

sizes = [16, 24, 32, 48, 64, 128, 256]
images = []
for s in sizes:
    img = Image.open(f"icon_{s}.png")
    images.append(img)

images[0].save(
    "app_icon.ico",
    format="ICO",
    sizes=[(s, s) for s in sizes],
    append_images=images[1:]
)
```

### Opção 3 — ImageMagick
```bash
magick icon_256.png -define icon:auto-resize=256,128,64,48,32,24,16 app_icon.ico
```

## Usar o ícone no PyInstaller

Adiciona o parâmetro `--icon` ao compilar:

```bash
pyinstaller --onefile --windowed --icon=app_icon.ico --name "Organizador_Ficheiros" file_organizer.py
```

## Checklist

- [ ] Ícone funciona a 16×16 (testar zoom 400%)
- [ ] Ícone reconhecível a 48×48
- [ ] Ícone nítido a 256×256
- [ ] Ficheiro `.ico` contém todos os 7 tamanhos
- [ ] Cores consistentes com a identidade visual da app (tema escuro, laranja)
