<div align="center">

# ⏱️ Controle de Horas Extras

**Registre, acompanhe e calcule suas horas extras mensais — com uma interface desktop premium.**

Aplicativo desktop para Windows feito em **Python + PySide6 (Qt 6)**, com banco local **SQLite** e uma UI totalmente customizada: janela sem moldura nativa, ícones vetoriais, animações fluidas e microinterações.

<br/>

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)
![PySide6](https://img.shields.io/badge/PySide6-Qt%206-41CD52?style=for-the-badge&logo=qt&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-local-003B57?style=for-the-badge&logo=sqlite&logoColor=white)
![Windows](https://img.shields.io/badge/Windows-desktop-0078D6?style=for-the-badge&logo=windows&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-A31F34?style=for-the-badge)

<br/>

`#4F46E5` Índigo · `#10B981` Esmeralda · `#8B5CF6` Violeta — tipografia **Inter**

</div>

---

## ✨ Sobre

O **Controle de Horas Extras** transforma o registro de horas em algo simples e
agradável. Você cadastra cada hora extra (data, duração e motivo), navega por
mês, e o app calcula automaticamente o total de horas, o valor a receber e o
salário estimado — tudo numa interface com acabamento de produto comercial.

A versão **2.0** é uma reescrita profunda de UI/UX, organizada em camadas
reutilizáveis e com identidade visual própria.

---

## 🎯 Recursos

| | Funcionalidade |
|---|---|
| 📝 | **Cadastro completo** — criar, editar e excluir horas extras (data, duração, motivo). |
| 📅 | **Navegação por mês** — seletor Jan–Dez com pílula indicadora deslizante. |
| 🧮 | **Resumo automático** — total de horas, valor das extras, salário estimado, totais mensais e anual. |
| ⏰ | **Calculadora de horas** — desconto de intervalo e suporte a virada de dia; vira registro em um clique. |
| ⚙️ | **Personalização** — defina seu **salário base** e o **valor da hora extra**; salvos no banco e aplicados na hora. |
| 📊 | **Dashboard anual** — cards de resumo, gráfico de barras animado e tabela detalhada. |
| 📄 | **Exportar NF** — gera o pedido de nota fiscal (.doc / .docx / .pdf) com o valor do mês preenchido. |
| 🔔 | **Toasts** — notificações discretas de sucesso, info e erro. |

---

## 🎨 Experiência visual (v2.0)

- **Identidade própria** — paleta índigo + esmeralda + violeta, fundo em camadas, cantos arredondados e tokens centralizados em [`app/theme.py`](app/theme.py).
- **Ícones vetoriais (SVG, estilo Lucide)** renderizados via `QtSvg`, coloridos dinamicamente e cacheados — nítidos em qualquer DPI, **nenhum emoji** como ícone.
- **Janela frameless** com sombra própria, arrastável pela barra de título e redimensionável pelas bordas; botões min / max / fechar pintados via `QPainter` com hover animado.
- **Navegação inferior** com indicador (cápsula) que desliza entre as abas.
- **Transição entre telas** com deslize lateral fluido, estilo iOS.
- **Cards premium** — chip de ícone tonal, sombra real que se eleva no hover e *pulse* ao atualizar o valor.
- **Calculadora** com números em animação tipo *odômetro* (slide vertical + fade).
- **Tabela moderna** — cabeçalho em pill, hover de linha e *flash* na linha recém-editada.
- **Animações reutilizáveis** centralizadas em [`app/anim.py`](app/anim.py) com curvas suaves (ease-out / out-quint).
- **HiDPI** via `Qt.HighDpiScaleFactorRoundingPolicy.PassThrough`.

---

## 💰 Como o cálculo funciona

```
valor_extra            = total_horas_decimais × valor_da_hora
salario_total_estimado = salário_base + valor_extra
```

| Parâmetro | Padrão (1ª execução) | Onde fica depois |
|-----------|----------------------|------------------|
| Salário base | **R$ 7.150,00** | Persistido na tabela `settings` do SQLite |
| Valor da hora | **R$ 42,55** | Editável a qualquer momento nas **Configurações** (⚙) |

> Os valores padrão vivem em [`app/config.py`](app/config.py) e são usados apenas
> na primeira execução. Depois, ficam salvos no banco e podem ser alterados pelo
> próprio usuário.

---

## 🚀 Como executar (desenvolvimento)

> Requer **Python 3.10+** no Windows.

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

Os dados ficam em `%APPDATA%\ControleHoras\horas.db`.

---

## 📦 Gerar o `.exe`

Basta rodar o `build.bat` na raiz — ele cria a venv (se preciso), instala as
dependências + PyInstaller e empacota o app (one-file, sem console, com assets e
fontes embarcados):

```powershell
.\build.bat
```

O executável final fica em `dist\Controle de Horas.exe`.

<details>
<summary>Empacotar manualmente</summary>

```powershell
pyinstaller --noconfirm --clean --windowed --onefile `
    --name "Controle de Horas" `
    --add-data "app\assets;app\assets" `
    --hidden-import PySide6.QtSvg `
    --collect-submodules PySide6.QtSvg `
    main.py
```

</details>

> **Exportar NF** usa automação do **Microsoft Word** (pywin32) — requer o Word
> instalado no Windows.

---

## 🗂️ Estrutura

```
Controle de Horas/
├── main.py                      # entrada — HiDPI, fonte Inter, paleta, QSS
├── requirements.txt
├── build.bat
├── README.md
└── app/
    ├── config.py                # salário base / valor da hora / meses
    ├── database.py              # SQLite (CRUD + agregações)
    ├── utils.py                 # formatadores BRL / data / horas
    ├── theme.py                 # tokens de design (cores, raios, tempos)
    ├── icons.py                 # ícones vetoriais SVG (QtSvg) + cache
    ├── anim.py                  # helpers de animação reutilizáveis
    ├── styles.py                # QSS global (consome theme.py)
    ├── nf_export.py             # exportação da NF via Word COM (pywin32)
    ├── assets/                  # SVGs, modelo de NF e fontes Inter
    └── views/
        ├── window_controls.py   # botões min/max/restore/close
        ├── title_bar.py         # barra de título customizada
        ├── custom_widgets.py    # widgets animados (botões, pickers, nav…)
        ├── widgets.py           # Card, SummaryCard, MonthSelector
        ├── toast.py             # notificações (toasts) animadas
        ├── chart.py             # gráfico de barras (QPainter)
        ├── main_window.py       # QMainWindow frameless + entrada animada
        ├── monthly_view.py      # tela mensal
        ├── annual_view.py       # dashboard anual
        ├── calculator_view.py   # calculadora de horas
        ├── settings_dialog.py   # ⚙ configurações
        └── record_dialog.py     # diálogo de novo/editar registro
```

---

## 🛠️ Tech stack

- **Python 3.10+**
- **PySide6** (Qt 6) — UI, animações (`QPropertyAnimation`, `QEasingCurve`) e gráficos (`QPainter`)
- **SQLite** — armazenamento local
- **pywin32** — automação do Word para exportação de NF (Windows)
- **PyInstaller** — empacotamento em `.exe`

---

## 📄 Licença

Distribuído sob a **Licença MIT**. Veja o arquivo [`LICENSE`](LICENSE) para mais detalhes.

---

<div align="center">

Criado por **João Carvalho** · © 2026 · v1.0

</div>
