import time
import requests
import threading
import queue
import json
import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from g_python.gextension import Extension
from g_python.hpacket import HPacket
from g_python.hmessage import Direction
from g_python.hparsers import HFloorItem, HWallItem

# =============================================================
# CONFIGURAÇÕES
# =============================================================
args_manuais = ["-p", "9092", "-v", "1.4.1"]

IDS_BLOQUEADOS_BC = {4578, 4882, 4767, 4814}

BC_STACK_1X1 = 13259
BC_STACK_2X1 = 8033
BC_STACK_2X2 = 8034

CONFIG_FILE  = "config_roomcopy.json"
PATH_PRESETS = ""

def carregar_configuracao():
    global PATH_PRESETS
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                PATH_PRESETS = json.load(f).get("pasta_presets", "presets")
        except:
            PATH_PRESETS = "presets"
    else:
        PATH_PRESETS = "presets"
    if not os.path.exists(PATH_PRESETS):
        try:
            os.makedirs(PATH_PRESETS)
        except:
            pass

def salvar_configuracao(caminho):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump({"pasta_presets": caminho}, f, indent=4)
    except:
        pass

carregar_configuracao()

extension_info = {
    "title":       "RoomCopy",
    "description": "Clona quartos completos com mobis, paredes e states",
    "version":     "1.0",
    "author":      "Krush"
}

ext = Extension(extension_info, args_manuais)
ext.start()

# =============================================================
# VARIÁVEIS GLOBAIS
# =============================================================
PAGE_ID_BC            = -1
DICIONARIO_UNIVERSAL  = {}
SCAN_ITENS            = {}
SCAN_ITENS_PAREDE     = {}
SCAN_CHAO             = ""

CLIPBOARD_ITENS   = []
CLIPBOARD_PAREDES = []
CLIPBOARD_CHAO    = ""

ESTADO_COLAGEM      = "INATIVO"
STACK_IDS_INSTANCIA = {"1x1": -1, "2x1": -1, "2x2": -1}

EM_EXECUCAO       = False
PARAR_EXECUCAO    = False
LISTA_SYNC_STATES = {}

IGNORAR_WIRED  = False
IGNORAR_PAREDE = False
WIRED_TYPE_IDS: set = set()

# =============================================================
# IDIOMAS — definido antes de tudo que usa T()
# =============================================================
LANG = "pt"

STRINGS = {
    "pt": {
        "furni_loading":          "carregando furnidata...",
        "furni_ok":               "furnidata ok",
        "furni_err":              "furnidata erro",
        "sec_status":             "STATUS",
        "sec_filters":            "FILTROS",
        "sec_actions":            "AÇÕES",
        "sec_presets":            "PRESETS",
        "lbl_estado":             "estado",
        "lbl_mobis":              "mobis",
        "lbl_paredes":            "paredes",
        "filter_wired":           "Não copiar Wireds",
        "filter_wall":            "Não copiar itens de parede",
        "btn_copy":               "COPIAR QUARTO",
        "btn_paste":              "COLAR QUARTO",
        "btn_abort":              "■  ABORTAR",
        "btn_export":             "↑  EXPORTAR",
        "btn_import":             "↓  IMPORTAR",
        "msg_ready":              "pronto.",
        "estado_inativo":         "inativo",
        "estado_click":           "aguardando clique",
        "estado_reentrada":       "aguardar reentrada",
        "estado_stacks":          "posicionando stacks",
        "estado_colando":         "colando...",
        "status_copied":          "Copiado — {f} mobis, {w} paredes.",
        "status_pasting":         "Colagem iniciada...",
        "status_done":            "Concluído — {f} mobis, {w} paredes.",
        "status_aborted":         "Operação abortada.",
        "status_stacks":          "Posicionando StackTiles...",
        "status_floor_changed":   "Chão alterado — saia e entre novamente, depois cole.",
        "status_floor_validated": "Chão validado — clique em qualquer piso para iniciar.",
        "status_click":           "Clique em qualquer piso para iniciar.",
        "status_nothing_copied":  "Nada copiado. Copie um quarto primeiro.",
        "status_preset_exported": "Preset '{n}' exportado.",
        "status_preset_loaded":   "Preset '{n}' carregado — {f} mobis, {w} paredes.",
        "status_preset_err_exp":  "Erro ao exportar: {e}",
        "status_preset_err_load": "Erro ao carregar: {e}",
        "status_empty_clipboard": "Prancheta vazia — copie um quarto primeiro.",
        "dialog_save":            "Salvar Preset",
        "dialog_load":            "Carregar Preset",
        "dialog_floor_title":     "RoomCopy — Atenção",
        "dialog_floor_body":      "O formato do chão foi alterado.\nSaia do quarto, entre novamente e clique em Colar.",
        "progress_floors":        "Mobis",
        "progress_walls":         "Paredes",
        "by":                     "by Krush",
        "lang_btn":               "EN",
    },
    "en": {
        "furni_loading":          "loading furnidata...",
        "furni_ok":               "furnidata ok",
        "furni_err":              "furnidata error",
        "sec_status":             "STATUS",
        "sec_filters":            "FILTERS",
        "sec_actions":            "ACTIONS",
        "sec_presets":            "PRESETS",
        "lbl_estado":             "state",
        "lbl_mobis":              "floor items",
        "lbl_paredes":            "wall items",
        "filter_wired":           "Do not copy Wireds",
        "filter_wall":            "Do not copy wall items",
        "btn_copy":               "COPY ROOM",
        "btn_paste":              "PASTE ROOM",
        "btn_abort":              "■  ABORT",
        "btn_export":             "↑  EXPORT",
        "btn_import":             "↓  IMPORT",
        "msg_ready":              "ready.",
        "estado_inativo":         "idle",
        "estado_click":           "waiting for click",
        "estado_reentrada":       "waiting re-entry",
        "estado_stacks":          "placing stacks",
        "estado_colando":         "pasting...",
        "status_copied":          "Copied — {f} floor, {w} wall items.",
        "status_pasting":         "Paste started...",
        "status_done":            "Done — {f} floor, {w} wall items.",
        "status_aborted":         "Operation aborted.",
        "status_stacks":          "Placing StackTiles...",
        "status_floor_changed":   "Floor changed — leave and re-enter, then paste again.",
        "status_floor_validated": "Floor validated — click any tile to start.",
        "status_click":           "Click any tile to start.",
        "status_nothing_copied":  "Nothing copied. Copy a room first.",
        "status_preset_exported": "Preset '{n}' exported.",
        "status_preset_loaded":   "Preset '{n}' loaded — {f} floor, {w} wall items.",
        "status_preset_err_exp":  "Export error: {e}",
        "status_preset_err_load": "Load error: {e}",
        "status_empty_clipboard": "Clipboard empty — copy a room first.",
        "dialog_save":            "Save Preset",
        "dialog_load":            "Load Preset",
        "dialog_floor_title":     "RoomCopy — Notice",
        "dialog_floor_body":      "Floor layout was changed.\nLeave the room, re-enter, then click Paste.",
        "progress_floors":        "Floor",
        "progress_walls":         "Walls",
        "by":                     "by Krush",
        "lang_btn":               "PT",
    },
}

def T(key, **kw):
    s = STRINGS[LANG].get(key, key)
    return s.format(**kw) if kw else s

# =============================================================
# ESTADOS UI — definido antes de _atualizar_estado_gui
# =============================================================
ESTADOS_UI = {
    "INATIVO":             ("estado_inativo",   None),
    "ESPERANDO_CLICK":     ("estado_click",     None),
    "ESPERANDO_REENTRADA": ("estado_reentrada", None),
    "POSICIONANDO_STACKS": ("estado_stacks",    None),
    "COLANDO":             ("estado_colando",   None),
}

# =============================================================
# FILA DE SYNC DE STATES
# =============================================================
FILA_SYNC = queue.Queue()

def worker_sync_states():
    while True:
        item = FILA_SYNC.get()
        if item is None:
            break
        mobi_id, state_alvo = item
        if state_alvo > 0:
            time.sleep(0.6)
            ext.send_to_server(HPacket("WiredSetObjectVariableValue", 0, mobi_id, "-110", state_alvo, 0))
        FILA_SYNC.task_done()

threading.Thread(target=worker_sync_states, daemon=True).start()

# =============================================================
# FUNÇÕES DE ATUALIZAÇÃO DA GUI
# =============================================================

def _painel_status(msg, erro=False):
    try:
        lbl_status_msg.config(text=msg, fg=DANGER if erro else SUCCESS)
    except:
        pass

def _atualizar_status_furni(ok):
    try:
        lbl_furni.config(text=T("furni_ok" if ok else "furni_err"),
                         fg=SUCCESS if ok else DANGER)
    except:
        pass

def _atualizar_estado_gui():
    try:
        key, _ = ESTADOS_UI.get(ESTADO_COLAGEM, ("estado_inativo", None))
        cores  = {
            "estado_inativo":   FG_DIM,
            "estado_click":     WARNING,
            "estado_reentrada": WARNING,
            "estado_stacks":    ACCENT,
            "estado_colando":   SUCCESS,
        }
        lbl_estado_val.config(text=T(key), fg=cores.get(key, FG_DIM))
    except:
        pass

def _atualizar_contadores():
    try:
        lbl_mobis_val.config(text=str(len(CLIPBOARD_ITENS)))
        lbl_paredes_val.config(text=str(len(CLIPBOARD_PAREDES)))
    except:
        pass

def _atualizar_progresso(atual, total, label=""):
    try:
        pct = int((atual / total) * 100) if total > 0 else 0
        progress_bar["value"] = pct
        lbl_prog.config(text=f"{label}  {pct}%" if label else "")
    except:
        pass

# =============================================================
# FURNIDATA
# =============================================================

def fetch_furnidata():
    global DICIONARIO_UNIVERSAL, WIRED_TYPE_IDS
    try:
        r = requests.get(
            "https://www.habbo.com.br/gamedata/furnidata_json/1",
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=15
        )
        if r.status_code == 200:
            data = r.json()
            wired_ids = set()
            for item in data["roomitemtypes"]["furnitype"]:
                classname  = item["classname"]
                id_tecnico = int(item["id"])
                DICIONARIO_UNIVERSAL[classname] = {
                    "bc_id":      int(item.get("bcofferid") or item.get("offerid") or item["id"]),
                    "id_tecnico": id_tecnico,
                    "xdim":       int(item.get("xdim", 1)),
                    "ydim":       int(item.get("ydim", 1)),
                    "tipo":       "chao",
                }
                if str(item.get("category", "")).lower().startswith("wired_"):
                    wired_ids.add(id_tecnico)
            for item in data["wallitemtypes"]["furnitype"]:
                classname  = item["classname"]
                id_tecnico = int(item["id"])
                DICIONARIO_UNIVERSAL[classname] = {
                    "bc_id":      int(item.get("bcofferid") or item.get("offerid") or item["id"]),
                    "id_tecnico": id_tecnico,
                    "tipo":       "parede",
                }
                if str(item.get("category", "")).lower().startswith("wired_"):
                    wired_ids.add(id_tecnico)
            WIRED_TYPE_IDS = wired_ids
        _atualizar_status_furni(ok=True)
    except:
        _atualizar_status_furni(ok=False)

# =============================================================
# LÓGICA DE COLAGEM
# =============================================================

def colocar_stacktiles(x, y):
    try:
        ext.send_to_server(HPacket("BuildersClubPlaceRoomItem", PAGE_ID_BC, BC_STACK_1X1, "0", x, y, 0, False))
        time.sleep(0.3)
        ext.send_to_server(HPacket("BuildersClubPlaceRoomItem", PAGE_ID_BC, BC_STACK_2X1, "0", x, y, 0, False))
        time.sleep(0.3)
        ext.send_to_server(HPacket("BuildersClubPlaceRoomItem", PAGE_ID_BC, BC_STACK_2X2, "0", x, y, 0, False))
    except:
        pass

def thread_colagem_mobis():
    global PARAR_EXECUCAO, STACK_IDS_INSTANCIA, LISTA_SYNC_STATES, EM_EXECUCAO, ESTADO_COLAGEM

    EM_EXECUCAO    = True
    PARAR_EXECUCAO = False
    ESTADO_COLAGEM = "COLANDO"
    _atualizar_estado_gui()
    _painel_status(T("status_pasting"))

    # ── MOBIS DE CHÃO ─────────────────────────────────────────
    total = len(CLIPBOARD_ITENS)
    for idx, mobi in enumerate(CLIPBOARD_ITENS):
        if PARAR_EXECUCAO:
            break
        if int(mobi["bc_id"]) in IDS_BLOQUEADOS_BC:
            continue

        xdim, ydim = mobi.get("xdim", 1), mobi.get("ydim", 1)
        if xdim >= 2 and ydim >= 2:
            stack_alvo = STACK_IDS_INSTANCIA["2x2"]
        elif (xdim == 2 and ydim == 1) or (xdim == 1 and ydim == 2):
            stack_alvo = STACK_IDS_INSTANCIA["2x1"]
        else:
            stack_alvo = STACK_IDS_INSTANCIA["1x1"]

        if stack_alvo == -1:
            stack_alvo = STACK_IDS_INSTANCIA["1x1"]

        if stack_alvo != -1:
            ext.send_to_server(HPacket("MoveObject", stack_alvo, int(mobi["x"]), int(mobi["y"]), 0))
            ext.send_to_server(HPacket("SetCustomStackingHeight", stack_alvo, int(mobi["z"] * 100)))
            time.sleep(0.06)

        LISTA_SYNC_STATES[(mobi["x"], mobi["y"], mobi["type_id"])] = mobi["state"]
        ext.send_to_server(
            HPacket("BuildersClubPlaceRoomItem", PAGE_ID_BC, int(mobi["bc_id"]), "0",
                    int(mobi["x"]), int(mobi["y"]), int(mobi["rot"]), False)
        )
        time.sleep(0.15)
        _atualizar_progresso(idx + 1, total, T("progress_floors"))

    # Remove stacks
    for s_id in STACK_IDS_INSTANCIA.values():
        if s_id != -1:
            ext.send_to_server(HPacket("PickupObject", 2, s_id))
            time.sleep(0.2)

    # ── ITENS DE PAREDE ───────────────────────────────────────
    if not PARAR_EXECUCAO and CLIPBOARD_PAREDES:
        total_p = len(CLIPBOARD_PAREDES)
        for idx, parede in enumerate(CLIPBOARD_PAREDES):
            if PARAR_EXECUCAO:
                break
            ext.send_to_server(
                HPacket("BuildersClubPlaceWallItem", PAGE_ID_BC, int(parede["bc_id"]), "0", parede["location"])
            )
            time.sleep(0.3)
            _atualizar_progresso(idx + 1, total_p, T("progress_walls"))

    if not PARAR_EXECUCAO:
        _painel_status(T("status_done", f=len(CLIPBOARD_ITENS), w=len(CLIPBOARD_PAREDES)))

    EM_EXECUCAO    = False
    ESTADO_COLAGEM = "INATIVO"
    STACK_IDS_INSTANCIA = {"1x1": -1, "2x1": -1, "2x2": -1}
    _atualizar_estado_gui()
    _atualizar_progresso(0, 1, "")

# =============================================================
# PRESETS
# =============================================================

def carregar_preset(caminho):
    global CLIPBOARD_CHAO, CLIPBOARD_ITENS, CLIPBOARD_PAREDES
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            dados = json.load(f)
        CLIPBOARD_CHAO    = dados.get("chao", "")
        CLIPBOARD_ITENS   = dados.get("mobis", [])
        CLIPBOARD_PAREDES = dados.get("paredes", [])
        nome = os.path.splitext(os.path.basename(caminho))[0]
        _painel_status(T("status_preset_loaded", n=nome, f=len(CLIPBOARD_ITENS), w=len(CLIPBOARD_PAREDES)))
        _atualizar_contadores()
        return True
    except Exception as e:
        _painel_status(T("status_preset_err_load", e=e), erro=True)
        return False

# =============================================================
# AÇÕES PRINCIPAIS
# =============================================================

def acao_rcopy():
    global CLIPBOARD_ITENS, CLIPBOARD_PAREDES, CLIPBOARD_CHAO
    CLIPBOARD_CHAO    = SCAN_CHAO
    CLIPBOARD_ITENS   = []
    CLIPBOARD_PAREDES = []

    id_to_classname_chao = {
        v["id_tecnico"]: k for k, v in DICIONARIO_UNIVERSAL.items() if v.get("tipo") == "chao"
    }
    id_to_classname_parede = {
        v["id_tecnico"]: k for k, v in DICIONARIO_UNIVERSAL.items() if v.get("tipo") == "parede"
    }

    # Captura todos os mobis de chão com aplicação dos filtros
    for inst_id, item in SCAN_ITENS.items():
        if IGNORAR_WIRED and item.type_id in WIRED_TYPE_IDS:
            continue

        c_name = id_to_classname_chao.get(item.type_id, "")
        if c_name in DICIONARIO_UNIVERSAL:
            info = DICIONARIO_UNIVERSAL[c_name]
            if int(info["bc_id"]) in IDS_BLOQUEADOS_BC:
                continue
            state = 0
            try:
                if item.stuff and len(item.stuff) > 0:
                    val = str(item.stuff[0]).lstrip("-")
                    if val.isdigit():
                        state = int(val)
            except:
                pass
            CLIPBOARD_ITENS.append({
                "bc_id":   info["bc_id"],
                "type_id": item.type_id,
                "xdim":    info.get("xdim", 1),
                "ydim":    info.get("ydim", 1),
                "x":       item.tile.x,
                "y":       item.tile.y,
                "z":       float(item.tile.z),
                "rot":     item.facing.value if hasattr(item.facing, "value") else item.facing,
                "state":   state,
            })
    CLIPBOARD_ITENS.sort(key=lambda x: x["z"])

    # Captura todos os itens de parede com aplicação dos filtros
    for inst_id, item in SCAN_ITENS_PAREDE.items():
        if IGNORAR_PAREDE:
            continue
        if IGNORAR_WIRED and item.type_id in WIRED_TYPE_IDS:
            continue

        c_name = id_to_classname_parede.get(item.type_id, "")
        if c_name in DICIONARIO_UNIVERSAL:
            info = DICIONARIO_UNIVERSAL[c_name]
            if int(info["bc_id"]) in IDS_BLOQUEADOS_BC:
                continue
            location = ""
            try:
                location = str(item.location).strip()
            except:
                pass
            if not location:
                continue
            state = 0
            try:
                raw = None
                if hasattr(item, "state"):
                    raw = item.state
                elif hasattr(item, "stuff") and item.stuff:
                    raw = item.stuff[0]
                if raw is not None:
                    val = str(raw).lstrip("-")
                    if val.isdigit():
                        state = int(val)
            except:
                pass
            CLIPBOARD_PAREDES.append({
                "bc_id":    info["bc_id"],
                "type_id":  item.type_id,
                "location": location,
                "state":    state,
            })

    _painel_status(T("status_copied", f=len(CLIPBOARD_ITENS), w=len(CLIPBOARD_PAREDES)))
    _atualizar_contadores()

def acao_rpaste():
    global ESTADO_COLAGEM
    if not CLIPBOARD_CHAO:
        _painel_status(T("status_nothing_copied"), erro=True)
        return
    if SCAN_CHAO == CLIPBOARD_CHAO:
        ESTADO_COLAGEM = "ESPERANDO_CLICK"
        _painel_status(T("status_click"))
    else:
        ext.send_to_server(HPacket("UpdateFloorProperties", CLIPBOARD_CHAO))
        ESTADO_COLAGEM = "ESPERANDO_REENTRADA"
        _painel_status(T("status_floor_changed"))
        messagebox.showinfo(T("dialog_floor_title"), T("dialog_floor_body"))
    _atualizar_estado_gui()

def acao_abortar():
    global PARAR_EXECUCAO, ESTADO_COLAGEM, STACK_IDS_INSTANCIA
    PARAR_EXECUCAO = True
    ESTADO_COLAGEM = "INATIVO"
    _painel_status(T("status_aborted"))
    _atualizar_estado_gui()
    _atualizar_progresso(0, 1, "")
    # Recolhe stacks caso o abort ocorra durante a colagem
    def _recolher():
        time.sleep(0.5)  # aguarda a thread de colagem pausar
        for s_id in STACK_IDS_INSTANCIA.values():
            if s_id != -1:
                ext.send_to_server(HPacket("PickupObject", 2, s_id))
                time.sleep(0.2)
        STACK_IDS_INSTANCIA = {"1x1": -1, "2x1": -1, "2x2": -1}
    threading.Thread(target=_recolher, daemon=True).start()

# =============================================================
# INTERCEPTORES
# =============================================================

def monitorar_objetos(message):
    global SCAN_ITENS
    try:
        SCAN_ITENS = {i.id: i for i in HFloorItem.parse(message.packet)}
    except:
        pass

def monitorar_itens_parede(message):
    global SCAN_ITENS_PAREDE
    try:
        SCAN_ITENS_PAREDE = {i.id: i for i in HWallItem.parse(message.packet)}
    except:
        pass

def monitorar_chao(message):
    global SCAN_CHAO, ESTADO_COLAGEM
    try:
        p = message.packet
        p.read_int()
        p.read_bool()
        SCAN_CHAO = p.read_string()
        if ESTADO_COLAGEM == "ESPERANDO_REENTRADA" and SCAN_CHAO == CLIPBOARD_CHAO:
            ESTADO_COLAGEM = "ESPERANDO_CLICK"
            _painel_status(T("status_floor_validated"))
            _atualizar_estado_gui()
    except:
        pass

def monitorar_movimento(message):
    global ESTADO_COLAGEM
    if ESTADO_COLAGEM == "ESPERANDO_CLICK":
        message.is_blocked = True
        x, y = message.packet.read_int(), message.packet.read_int()
        ESTADO_COLAGEM = "POSICIONANDO_STACKS"
        _painel_status(T("status_stacks"))
        threading.Thread(target=colocar_stacktiles, args=(x, y), daemon=True).start()

def monitorar_entrada_e_gatilho(message):
    global STACK_IDS_INSTANCIA, ESTADO_COLAGEM, LISTA_SYNC_STATES, EM_EXECUCAO
    try:
        mobi = HFloorItem(message.packet)

        if ESTADO_COLAGEM == "POSICIONANDO_STACKS":
            t1 = next((v["id_tecnico"] for v in DICIONARIO_UNIVERSAL.values() if v["bc_id"] == BC_STACK_1X1), BC_STACK_1X1)
            t2 = next((v["id_tecnico"] for v in DICIONARIO_UNIVERSAL.values() if v["bc_id"] == BC_STACK_2X1), BC_STACK_2X1)
            t3 = next((v["id_tecnico"] for v in DICIONARIO_UNIVERSAL.values() if v["bc_id"] == BC_STACK_2X2), BC_STACK_2X2)

            if mobi.type_id == t1:   STACK_IDS_INSTANCIA["1x1"] = mobi.id
            elif mobi.type_id == t2: STACK_IDS_INSTANCIA["2x1"] = mobi.id
            elif mobi.type_id == t3: STACK_IDS_INSTANCIA["2x2"] = mobi.id

            if all(v != -1 for v in STACK_IDS_INSTANCIA.values()):
                if (CLIPBOARD_ITENS or CLIPBOARD_PAREDES) and not EM_EXECUCAO:
                    threading.Thread(target=thread_colagem_mobis, daemon=True).start()

        chave = (mobi.tile.x, mobi.tile.y, mobi.type_id)
        if chave in LISTA_SYNC_STATES:
            state = LISTA_SYNC_STATES.pop(chave)
            if state > 0:
                FILA_SYNC.put((mobi.id, state))
    except:
        pass

ext.intercept(Direction.TO_CLIENT, monitorar_objetos,           "Objects")
ext.intercept(Direction.TO_CLIENT, monitorar_itens_parede,      "Items")
ext.intercept(Direction.TO_CLIENT, monitorar_chao,              "FloorHeightMap")
ext.intercept(Direction.TO_CLIENT, monitorar_entrada_e_gatilho, "ObjectAdd")
ext.intercept(Direction.TO_SERVER, monitorar_movimento,         "MoveAvatar")

threading.Thread(target=fetch_furnidata, daemon=True).start()

# =============================================================
# CORES E FONTES — definidas antes da GUI
# =============================================================
BG       = "#111111"
BG2      = "#181818"
BG3      = "#202020"
BORDER   = "#333333"
ACCENT   = "#f0a500"
ACCENT_D = "#b87800"
SUCCESS  = "#4caf7d"
DANGER   = "#d94f4f"
WARNING  = "#e8c547"
FG       = "#d0d0d0"
FG_DIM   = "#555555"
FG_MID   = "#888888"
FM       = "Courier New"

# =============================================================
# WIDGETS HELPERS
# =============================================================

def _btn(parent, text, cmd, fg=None, active_bg=None, pady=5, padx=8, font_size=8):
    if fg is None:       fg = ACCENT
    if active_bg is None: active_bg = ACCENT
    b = tk.Button(
        parent, text=text, command=cmd,
        bg=BG3, fg=fg,
        activebackground=active_bg, activeforeground=BG,
        relief="flat", bd=0, cursor="hand2",
        font=(FM, font_size, "bold"), padx=padx, pady=pady,
        highlightthickness=1, highlightbackground=BORDER,
    )
    b.bind("<Enter>", lambda e: b.config(bg=active_bg, fg=BG))
    b.bind("<Leave>", lambda e: b.config(bg=BG3, fg=fg))
    return b

def _danger_btn(parent, text, cmd):
    b = tk.Button(
        parent, text=text, command=cmd,
        bg=BG3, fg=DANGER,
        activebackground=DANGER, activeforeground=BG,
        relief="flat", bd=0, cursor="hand2",
        font=(FM, 8, "bold"), padx=8, pady=5,
        highlightthickness=1, highlightbackground=BORDER,
    )
    b.bind("<Enter>", lambda e: b.config(bg=DANGER, fg=BG))
    b.bind("<Leave>", lambda e: b.config(bg=BG3, fg=DANGER))
    return b

def _make_check(parent, text, var):
    f = tk.Frame(parent, bg=BG)
    f.pack(fill="x", pady=1)
    def _toggle():
        var.set(not var.get())
        atualizar_filtros()
        dot.config(text="◆" if var.get() else "◇", fg=ACCENT if var.get() else FG_DIM)
    dot = tk.Label(f, text="◇", bg=BG, fg=FG_DIM, font=(FM, 8), cursor="hand2")
    dot.pack(side="left", padx=(0, 6))
    dot.bind("<Button-1>", lambda e: _toggle())
    lbl = tk.Label(f, text=text, bg=BG, fg=FG_MID, font=(FM, 8), cursor="hand2", anchor="w")
    lbl.pack(side="left", fill="x")
    lbl.bind("<Button-1>", lambda e: _toggle())
    return lbl

def _section(parent, key):
    row = tk.Frame(parent, bg=BG)
    row.pack(fill="x", pady=(8, 3))
    lbl = tk.Label(row, text=T(key), bg=BG, fg=FG_MID, font=(FM, 7, "bold"))
    lbl.pack(side="left")
    tk.Frame(row, bg=BORDER, height=1).pack(side="left", fill="x", expand=True, padx=(6, 0), pady=5)
    return lbl

def _status_row(parent, key, row_idx):
    lbl_k = tk.Label(parent, text=T(key), bg=BG, fg=FG_DIM, font=(FM, 8), anchor="w", width=12)
    lbl_k.grid(row=row_idx, column=0, sticky="w", pady=1)
    val = tk.Label(parent, text="—", bg=BG, fg=FG_MID, font=(FM, 8), anchor="w")
    val.grid(row=row_idx, column=1, sticky="w", padx=(4, 0), pady=1)
    return lbl_k, val

# =============================================================
# CALLBACKS GUI
# =============================================================

def atualizar_filtros():
    global IGNORAR_WIRED, IGNORAR_PAREDE
    IGNORAR_WIRED  = var_wired.get()
    IGNORAR_PAREDE = var_parede.get()

def gui_copiar():
    threading.Thread(target=acao_rcopy, daemon=True).start()

def gui_colar():
    threading.Thread(target=acao_rpaste, daemon=True).start()

def gui_exportar():
    caminho = filedialog.asksaveasfilename(
        title=T("dialog_save"),
        initialdir=PATH_PRESETS,
        defaultextension=".json",
        filetypes=[("Preset JSON", "*.json")],
    )
    if not caminho:
        return
    nome = os.path.splitext(os.path.basename(caminho))[0]
    if not CLIPBOARD_CHAO and not CLIPBOARD_ITENS and not CLIPBOARD_PAREDES:
        _painel_status(T("status_empty_clipboard"), erro=True)
        return
    try:
        dados = {"chao": CLIPBOARD_CHAO, "mobis": CLIPBOARD_ITENS, "paredes": CLIPBOARD_PAREDES}
        with open(caminho, "w", encoding="utf-8") as f:
            json.dump(dados, f, indent=4)
        _painel_status(T("status_preset_exported", n=nome))
    except Exception as e:
        _painel_status(T("status_preset_err_exp", e=e), erro=True)

def gui_importar():
    caminho = filedialog.askopenfilename(
        title=T("dialog_load"),
        initialdir=PATH_PRESETS,
        filetypes=[("Preset JSON", "*.json")],
    )
    if not caminho:
        return
    carregar_preset(caminho)

def gui_toggle_lang():
    global LANG
    LANG = "en" if LANG == "pt" else "pt"
    _aplicar_idioma()

def _aplicar_idioma():
    try:
        lbl_sec_status.config(text=T("sec_status"))
        lbl_sec_filters.config(text=T("sec_filters"))
        lbl_sec_actions.config(text=T("sec_actions"))
        lbl_sec_presets.config(text=T("sec_presets"))
        lbl_key_estado.config(text=T("lbl_estado"))
        lbl_key_mobis.config(text=T("lbl_mobis"))
        lbl_key_paredes.config(text=T("lbl_paredes"))
        lbl_check_wired.config(text=T("filter_wired"))
        lbl_check_wall.config(text=T("filter_wall"))
        btn_copy_ref.config(text=T("btn_copy"))
        btn_paste_ref.config(text=T("btn_paste"))
        btn_abort_ref.config(text=T("btn_abort"))
        btn_exp_ref.config(text=T("btn_export"))
        btn_imp_ref.config(text=T("btn_import"))
        btn_lang_ref.config(text=T("lang_btn"))
        lbl_by.config(text=T("by"))
        lbl_status_msg.config(text=T("msg_ready"))
        _atualizar_estado_gui()
    except:
        pass

# =============================================================
# JANELA
# =============================================================

root = tk.Tk()
root.title("RoomCopy 1.0")
root.geometry("320x530")
root.resizable(False, False)
root.attributes("-topmost", True)
root.configure(bg=BG)

# ── Cabeçalho ────────────────────────────────────────────────
header = tk.Frame(root, bg=BG2, height=44)
header.pack(fill="x")
header.pack_propagate(False)

tk.Label(header, text="ROOMCOPY", bg=BG2, fg=ACCENT,
         font=(FM, 14, "bold")).pack(side="left", padx=12, pady=10)
tk.Label(header, text="v1.0", bg=BG2, fg=FG_DIM,
         font=(FM, 8)).pack(side="left", pady=14)

btn_lang_ref = tk.Button(
    header, text="EN", command=gui_toggle_lang,
    bg=BG3, fg=FG_DIM, activebackground=ACCENT, activeforeground=BG,
    relief="flat", bd=0, cursor="hand2", font=(FM, 7, "bold"), padx=6, pady=2,
    highlightthickness=1, highlightbackground=BORDER,
)
btn_lang_ref.pack(side="right", padx=(4, 10), pady=12)

lbl_furni = tk.Label(header, text=T("furni_loading"), bg=BG2, fg=WARNING, font=(FM, 7))
lbl_furni.pack(side="right", padx=4)

# ── Container principal ───────────────────────────────────────
main = tk.Frame(root, bg=BG, padx=14, pady=6)
main.pack(fill="both", expand=True)

# ── STATUS ───────────────────────────────────────────────────
lbl_sec_status = _section(main, "sec_status")

grid_s = tk.Frame(main, bg=BG)
grid_s.pack(fill="x")

lbl_key_estado,  lbl_estado_val  = _status_row(grid_s, "lbl_estado",  0)
lbl_key_mobis,   lbl_mobis_val   = _status_row(grid_s, "lbl_mobis",   1)
lbl_key_paredes, lbl_paredes_val = _status_row(grid_s, "lbl_paredes", 2)

style_pb = ttk.Style()
style_pb.theme_use("clam")
style_pb.configure("RC.Horizontal.TProgressbar",
    troughcolor=BG3, background=ACCENT,
    bordercolor=BORDER, lightcolor=ACCENT, darkcolor=ACCENT_D)
progress_bar = ttk.Progressbar(main, orient="horizontal", mode="determinate",
                                maximum=100, style="RC.Horizontal.TProgressbar")
progress_bar.pack(fill="x", pady=(6, 0))
lbl_prog = tk.Label(main, text="", bg=BG, fg=FG_DIM, font=(FM, 7), anchor="e")
lbl_prog.pack(fill="x")

lbl_status_msg = tk.Label(main, text=T("msg_ready"), bg=BG, fg=FG_DIM,
                           font=(FM, 8), anchor="w", wraplength=290, justify="left")
lbl_status_msg.pack(fill="x", pady=(2, 0))

tk.Frame(main, bg=BORDER, height=1).pack(fill="x", pady=7)

# ── FILTROS ───────────────────────────────────────────────────
lbl_sec_filters = _section(main, "sec_filters")

var_wired  = tk.BooleanVar(value=False)
var_parede = tk.BooleanVar(value=False)
lbl_check_wired = _make_check(main, T("filter_wired"), var_wired)
lbl_check_wall  = _make_check(main, T("filter_wall"),  var_parede)

tk.Frame(main, bg=BORDER, height=1).pack(fill="x", pady=7)

# ── AÇÕES ────────────────────────────────────────────────────
lbl_sec_actions = _section(main, "sec_actions")

row_ac = tk.Frame(main, bg=BG)
row_ac.pack(fill="x", pady=2)
btn_copy_ref  = _btn(row_ac, T("btn_copy"),  gui_copiar, pady=7)
btn_paste_ref = _btn(row_ac, T("btn_paste"), gui_colar, fg=SUCCESS, active_bg=SUCCESS, pady=7)
btn_copy_ref.pack(side="left",  fill="x", expand=True, padx=(0, 3))
btn_paste_ref.pack(side="right", fill="x", expand=True, padx=(3, 0))

btn_abort_ref = _danger_btn(main, T("btn_abort"), acao_abortar)
btn_abort_ref.pack(fill="x", pady=(4, 0))

tk.Frame(main, bg=BORDER, height=1).pack(fill="x", pady=7)

# ── PRESETS ──────────────────────────────────────────────────
lbl_sec_presets = _section(main, "sec_presets")

row_pre = tk.Frame(main, bg=BG)
row_pre.pack(fill="x", pady=2)
row_pre.columnconfigure(0, weight=1)
row_pre.columnconfigure(1, weight=1)

btn_exp_ref = _btn(row_pre, T("btn_export"), gui_exportar, pady=7)
btn_imp_ref = _btn(row_pre, T("btn_import"), gui_importar, fg=WARNING, active_bg=WARNING, pady=7)
btn_exp_ref.grid(row=0, column=0, sticky="ew", padx=(0, 2))
btn_imp_ref.grid(row=0, column=1, sticky="ew", padx=(2, 0))

# ── Rodapé ───────────────────────────────────────────────────
tk.Frame(main, bg=BORDER, height=1).pack(fill="x", pady=(10, 4))
lbl_by = tk.Label(main, text=T("by"), bg=BG, fg=FG_DIM, font=(FM, 7))
lbl_by.pack(anchor="e")

# Inicializa displays
_atualizar_estado_gui()
lbl_mobis_val.config(text="0")
lbl_paredes_val.config(text="0")

root.mainloop()