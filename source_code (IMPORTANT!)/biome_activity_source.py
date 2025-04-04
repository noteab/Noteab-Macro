import json, requests, time, os, threading, re, webbrowser, random, keyboard, pyautogui, pytesseract, autoit, psutil, locale
import traceback
import pygetwindow as gw

from tkinter import messagebox, filedialog
from PIL import Image, ImageTk
from datetime import datetime, timedelta

import ttkbootstrap as ttk
    
class SnippingWidget:
    def __init__(self, root, config_key=None, callback=None):
        self.root = root
        self.config_key = config_key
        self.callback = callback
        self.snipping_window = None
        self.begin_x = None
        self.begin_y = None
        self.end_x = None
        self.end_y = None

    def start(self):
        self.snipping_window = ttk.Toplevel(self.root)
        self.snipping_window.attributes('-fullscreen', True)
        self.snipping_window.attributes('-alpha', 0.3)
        self.snipping_window.configure(bg="lightblue")
        
        self.snipping_window.bind("<Button-1>", self.on_mouse_press)
        self.snipping_window.bind("<B1-Motion>", self.on_mouse_drag)
        self.snipping_window.bind("<ButtonRelease-1>", self.on_mouse_release)

        self.canvas = ttk.Canvas(self.snipping_window, bg="lightblue", highlightthickness=0)
        self.canvas.pack(fill=ttk.BOTH, expand=True)
        
    # hi im tea (ffffffffff)
    
    def on_mouse_press(self, event):
        self.begin_x = event.x
        self.begin_y = event.y
        self.canvas.delete("selection_rect")

    def on_mouse_drag(self, event):
        self.end_x, self.end_y = event.x, event.y
        self.canvas.delete("selection_rect")
        self.canvas.create_rectangle(self.begin_x, self.begin_y, self.end_x, self.end_y,
                                      outline="white", width=2, tag="selection_rect")

    def on_mouse_release(self, event):
        self.end_x = event.x
        self.end_y = event.y

        x1, y1 = min(self.begin_x, self.end_x), min(self.begin_y, self.end_y)
        x2, y2 = max(self.begin_x, self.end_x), max(self.begin_y, self.end_y)

        self.capture_region(x1, y1, x2, y2)
        self.snipping_window.destroy()

    def capture_region(self, x1, y1, x2, y2):
        if self.config_key:
            region = [x1, y1, x2 - x1, y2 - y1]
            print(f"Region for '{self.config_key}' set to {region}")
            
            if self.callback:
                self.callback(region)
                
class BiomePresence():
    def __init__(self):
        try:
            locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
        except locale.Error:
            locale.setlocale(locale.LC_ALL, '')
            
        self.logs_dir = os.path.join(os.getenv('LOCALAPPDATA'), 'Roblox', 'logs')
        self.config = self.load_config()
        self.auras_data = self.load_auras_json()
        self.biome_data = self.load_biome_data()
        
        self.current_biome = None
        self.last_sent = {biome: datetime.min for biome in self.biome_data}
        
        self.biome_counts = self.config.get("biome_counts", {})
        for biome in self.biome_data.keys():
            if biome not in self.biome_counts:
                self.biome_counts[biome] = 0
                
        self.start_time = None
        self.saved_session = self.parse_session_time(self.config.get("session_time", "0:00:00"))
        
        self.last_position = 0
        self.detection_running = False
        self.detection_thread = None
        self.lock = threading.Lock()
        self.logs = self.load_logs()
        
        #item use
        self.last_br_time = datetime.min
        self.last_sc_time = datetime.min
        self.last_mt_time = datetime.min
        self.on_auto_merchant_state = False
        
        # Buff variables
        self.auto_pop_state = False
        self.buff_vars = {}
        self.buff_amount_vars = {}
        
        # Reconnect state
        self.reconnecting_state = False
    
        # start gui
        self.variables = {}
        self.init_gui()
        
        # aura detection:
        self.last_aura_found = None
       
    def load_logs(self):
        if os.path.exists('macro_logs.txt'):
            with open('macro_logs.txt', 'r') as file:
                lines = file.read().splitlines()
                return lines
        return []
    
    def load_biome_data(self):
        biomes_paths = [
            "biomes_data.json",
            "source_code/biomes_data.json",
            os.path.join(os.path.dirname(__file__), "biomes_data.json"),
            os.path.join(os.path.dirname(__file__), "source_code/biomes_data.json")
        ]
        
        default_biome_data = {
            "WINDY": {
                "color": "0x9ae5ff",
                "thumbnail_url": "https://i.postimg.cc/6qPH4wy6/image.png"
            },
            "RAINY": {
                "color": "0x027cbd",
                "thumbnail_url": "https://static.wikia.nocookie.net/sol-rng/images/e/ec/Rainy.png"
            },
            "SNOWY": {
                "color": "0xDceff9",
                "thumbnail_url": "https://static.wikia.nocookie.net/sol-rng/images/d/d7/Snowy_img.png"
            },
            "SAND STORM": {
                "color": "0x8F7057",
                "thumbnail_url": "https://i.postimg.cc/3JyL25Kz/image.png"
            },
            "HELL": {
                "color": "0xff4719",
                "thumbnail_url": "https://i.postimg.cc/hGC5xNyY/image.png"
            },
            "STARFALL": {
                "color": "0x011ab7",
                "thumbnail_url": "https://i.postimg.cc/1t0dY4J8/image.png"
            },
            "CORRUPTION": {
                "color": "0x6d32a8",
                "thumbnail_url": "https://i.postimg.cc/ncZQ84Dh/image.png"
            },
            "NULL": {
                "color": "0x838383",
                "thumbnail_url": "https://static.wikia.nocookie.net/sol-rng/images/f/fc/NULLLL.png"
            },
            "GLITCHED": {
                "color": "0xbfff00",
                "thumbnail_url": "https://i.postimg.cc/W3Lhtn5g/image.png"
            },
            
            "DREAMSPACE": {
                "color": "0xea9dda",
                "thumbnail_url": "https://i.postimg.cc/rFjCcW3w/image.png"
            }
        }
        
        try:
            for path in biomes_paths:
                if os.path.exists(path):
                    with open(path, "r") as file:
                        biome_data = json.load(file)
                        return biome_data
        except Exception as e:
            print(f"Error loading biomes_data.json: {e}")
            self.error_logging(e, f"Error loading biomes_data.json")
        
        with open("biomes_data.json", "w") as file:
            json.dump(default_biome_data, file, indent=4)
            print("Default biomes_data.json created.")
        
        return default_biome_data

    def error_logging(self, exception, custom_message=None, max_log_size=3 * 1024 * 1024):
        log_file = "error_logs.txt"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        error_type = type(exception).__name__
        error_message = str(exception)
        stack_trace = traceback.format_exc()

        if not os.path.exists(log_file):
            with open(log_file, "w") as log:
                log.write("Error Log File Created\n")
                log.write("-" * 40 + "\n")

        if os.path.exists(log_file) and os.path.getsize(log_file) > max_log_size:
            with open(log_file, "r") as log:
                lines = log.readlines()
            with open(log_file, "w") as log:
                log.writelines(lines[-1000:])

        with open(log_file, "a") as log:
            log.write(f"\n[{timestamp}] ERROR LOG\n")
            log.write(f"Error Type: {error_type}\n")
            log.write(f"Error Message: {error_message}\n")
            if custom_message:
                log.write(f"Custom Message: {custom_message}\n")
            log.write(f"Traceback:\n{stack_trace}\n")
            log.write("-" * 40 + "\n")

        print(f"Error logged to {log_file}.")
    
    def save_logs(self):
        log_file_path = 'macro_logs.txt'
        
        if os.path.exists(log_file_path) and os.path.getsize(log_file_path) > 2 * 1024 * 1024:
            with open(log_file_path, 'w') as file:
                file.write("")
        else:
            with open(log_file_path, 'a') as file:
                for log in self.logs:
                    file.write(log + "\n")
                
    def save_config(self):
        try:
            with open("config.json", "r") as file:
                config = json.load(file)
        except FileNotFoundError:
            config = {}

        auto_buff_glitched = config.get("auto_buff_glitched", self.config.get("auto_buff_glitched", {}))
        session_time = self.get_total_session_time()

        config.update({
            "webhook_url": self.webhook_url_entry.get(),
            "private_server_link": self.private_server_link_entry.get(),
            "auto_reconnect": self.auto_reconnect_var.get(),
            "biome_notifier": {biome: self.variables[biome].get() for biome in self.biome_data},
            "biome_counts": self.biome_counts,
            "session_time": session_time,
            "biome_randomizer": self.br_var.get(),
            "br_duration": self.br_duration_var.get(),
            "strange_controller": self.sc_var.get(),
            "sc_duration": self.sc_duration_var.get(),
            "auto_pop_glitched": self.auto_pop_glitched_var.get(),
            "auto_buff_glitched": {
                buff: (self.buff_vars[buff].get(), int(self.buff_amount_vars[buff].get()))
                for buff in self.buff_vars
            },
            "selected_theme": self.root.style.theme.name,
            "dont_ask_for_update": self.config.get("dont_ask_for_update", False),
            "merchant_teleporter": self.mt_var.get(),
            "mt_duration": self.mt_duration_var.get(),
            "merchant_extra_slot": self.merchant_extra_slot_var.get(),
            "Mari_Items": self.config.get("Mari_Items", {}),
            "Jester_Items": self.config.get("Jester_Items", {}),
            "ping_mari": self.ping_mari_var.get(),
            "mari_user_id": self.mari_user_id_var.get(),
            "ping_jester": self.ping_jester_var.get(),
            "jester_user_id": self.jester_user_id_var.get(),
            "merchant_open_button": self.config.get("merchant_open_button", [579, 906]),
            "merchant_dialogue_box": self.config.get("merchant_dialogue_box", [1114, 796]),
            "purchase_amount_button": self.config.get("purchase_amount_button", [700, 584]),
            "purchase_button": self.config.get("purchase_button", [739, 635]),
            "first_item_slot_pos": self.config.get("first_item_slot_pos", [571, 704]),
            "merchant_name_ocr_pos": self.config.get("merchant_name_ocr_pos", [746, 680, 103, 32]),
            "item_name_ocr_pos": self.config.get("item_name_ocr_pos", [728, 731, 218, 24]),
            "enable_aura_detection": self.enable_aura_detection_var.get(),
            "ping_minimum": self.ping_minimum_var.get(),
            "aura_user_id": self.aura_user_id_var.get(),
            "enable_aura_record": self.enable_aura_record_var.get(),
            "aura_record_keybind": self.aura_record_keybind_var.get(),
            "aura_record_minimum": self.aura_record_minimum_var.get(),
            "inventory_menu": self.config.get("inventory_menu", [36, 535]),
            "items_tab": self.config.get("items_tab", [1272, 329]),
            "search_bar": self.config.get("search_bar", [855, 358]),
            "first_item_slot": self.config.get("first_item_slot", [839, 434]),
            "amount_box": self.config.get("amount_box", [594, 570]),
            "use_button": self.config.get("use_button", [710, 573]),
            "reconnect_start_button": self.config.get("reconnect_start_button", [954, 876]),
            "inventory_click_delay": self.click_delay_var.get(),
            "record_rare_biome":  self.record_rarest_biome_var.get(),
            "rare_biome_record_keybind":  self.rarest_biome_keybind_var.get()
            
        })

        if not config["auto_buff_glitched"]:
            config["auto_buff_glitched"] = auto_buff_glitched

        with open("config.json", "w") as file:
            json.dump(config, file, indent=4)

        self.config = config

    def load_config(self):
        try:
            config_paths = [
                "config.json",
                "source_code/config.json",
                os.path.join(os.path.dirname(__file__), "config.json"),
                os.path.join(os.path.dirname(__file__), "source_code/config.json")
            ]
            
            for path in config_paths:
                if os.path.exists(path):
                    with open(path, "r") as file:
                        config = json.load(file)
                        return config
                    
            return {"biome_counts": {biome: 0 for biome in self.biome_data}, "session_time": "0:00:00"}
        
        except Exception as e:
                self.error_logging(e, "Error at loading config.json. Try adding empty: '{}' into config.json to fix this error!")
    
    def import_config(self):
        try:
            file_path = filedialog.askopenfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json")],
                title="Select CONFIG.JSON please!"
            )
            
            if not file_path: return
            with open(file_path, "r") as file: config = json.load(file)
            self.config = config
            
            # da webhook
            self.webhook_url_entry.delete(0, 'end')
            self.webhook_url_entry.insert(0, config.get("webhook_url", ""))
            self.private_server_link_entry.delete(0, 'end')
            self.private_server_link_entry.insert(0, config.get("private_server_link", ""))
            
            # misc
            self.auto_pop_glitched_var.set(config.get("auto_pop_glitched", False))
            self.record_rarest_biome_var.set(config.get("record_rare_biome", False))
            self.rarest_biome_keybind_var.set(config.get("rare_biome_record_keybind", "shift + F8"))
            self.br_var.set(config.get("biome_randomizer", False))
            self.br_duration_var.set(config.get("br_duration", "30"))
            self.sc_var.set(config.get("strange_controller", False))
            self.sc_duration_var.set(config.get("sc_duration", "15"))
            self.mt_var.set(config.get("merchant_teleporter", False))
            self.mt_duration_var.set(config.get("mt_duration", "1"))
            self.auto_reconnect_var.set(config.get("auto_reconnect", False))
            self.click_delay_var.set(config.get("inventory_click_delay", "0"))
            auto_buff_glitched = config.get("auto_buff_glitched", {})
            for buff, (enabled, amount) in auto_buff_glitched.items():
                if buff in self.buff_vars:
                    self.buff_vars[buff].set(enabled)
                    self.buff_amount_vars[buff].set(amount)
            # aura
            self.enable_aura_detection_var.set(config.get("enable_aura_detection", False))
            self.aura_user_id_var.set(config.get("aura_user_id", ""))
            self.ping_minimum_var.set(config.get("ping_minimum", "100000"))
            self.enable_aura_record_var.set(config.get("enable_aura_record", False))
            self.aura_record_keybind_var.set(config.get("aura_record_keybind", "shift + F8"))
            self.aura_record_minimum_var.set(config.get("aura_record_minimum", "500000"))
            
            # merchant
            self.merchant_extra_slot_var.set(config.get("merchant_extra_slot", "0"))
            self.ping_mari_var.set(config.get("ping_mari", False))
            self.mari_user_id_var.set(config.get("mari_user_id", ""))
            self.ping_jester_var.set(config.get("ping_jester", False))
            self.jester_user_id_var.set(config.get("jester_user_id", ""))
            
            # biome count
            self.biome_counts = config.get("biome_counts", {biome: 0 for biome in self.biome_data})
            for biome, count in self.biome_counts.items():
                if biome in self.stats_labels:
                    self.stats_labels[biome].config(text=f"{biome}: {count}")
            
            total_biomes = sum(self.biome_counts.values())
            self.total_biomes_label.config(text=f"Total Biomes Found: {total_biomes}")
            
            session_time = config.get("session_time")
            self.session_label.config(text=f"Running Session: {session_time}")
            self.save_config()
            messagebox.askokcancel("Ok imported!!", "Your selected config.json imported and saved successfully!")
        except Exception as e:
            self.error_logging(e, "Error at importing config.json")
     
            
    def init_gui(self):
        selected_theme = self.config.get("selected_theme", "solar")
        abslt_path = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(abslt_path, "NoteabBiomeTracker.ico")
        
        self.root = ttk.Window(themename=selected_theme)
        self.root.title("Noteab's Biome Macro (v1.5.4-patch2.8.4) (Idle)")
        self.root.geometry("695x355")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        try:
            self.root.iconbitmap(icon_path)
        except Exception as e:
            pass
            
        self.variables = {biome: ttk.StringVar(master=self.root, value=self.config.get("biome_notifier", {}).get(biome, "Message"))
                        for biome in self.biome_data}

        
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        webhook_frame = ttk.Frame(notebook)
        misc_frame = ttk.Frame(notebook)
        aura_webhook_frame = ttk.Frame(notebook)
        merchant_frame = ttk.Frame(notebook)
        credits_frame = ttk.Frame(notebook)
        stats_frame = ttk.Frame(notebook)

        notebook.add(webhook_frame, text='Webhook')
        notebook.add(misc_frame, text='Misc')
        notebook.add(merchant_frame, text='Merchant')
        notebook.add(aura_webhook_frame, text='Auras')
        notebook.add(stats_frame, text='Stats')
        notebook.add(credits_frame, text='Credits')

        self.create_webhook_tab(webhook_frame)
        self.create_misc_tab(misc_frame)
        self.create_auras_tab(aura_webhook_frame)
        self.create_merchant_tab(merchant_frame)
        self.create_stats_tab(stats_frame)
        self.create_credit_tab(credits_frame)
        
        button_frame = ttk.Frame(self.root)
        button_frame.pack(pady=10)
        start_button = ttk.Button(button_frame, text="Start (F1)", command=self.start_detection)
        stop_button = ttk.Button(button_frame, text="Stop (F2)", command=self.stop_detection)
        start_button.pack(side='left', padx=5)
        stop_button.pack(side='left', padx=5)

        # Theme
        theme_label = ttk.Label(button_frame, text="Macro Theme:")
        theme_label.pack(side='left', padx=15)
        theme_combobox = ttk.Combobox(button_frame, values=ttk.Style().theme_names(), state="readonly")
        theme_combobox.set(selected_theme)
        theme_combobox.pack(side='left', padx=5)
        theme_combobox.bind("<<ComboboxSelected>>", lambda event: self.update_theme(theme_combobox.get()))


        keyboard.add_hotkey('F1', self.start_detection)
        keyboard.add_hotkey('F2', self.stop_detection)
        
        self.check_for_updates()
        self.root.mainloop()
        

    def update_theme(self, theme_name):
        self.root.style.theme_use(theme_name)
        self.config["selected_theme"] = theme_name
        self.save_config()

    def check_for_updates(self):
        current_version = "v1.5.4-patch2.8.4"
        dont_ask_again = self.config.get("dont_ask_for_update", False)
        
        if dont_ask_again: return
        
        try:
            response = requests.get("https://api.github.com/repos/noteab/Noteab-Macro/releases/latest")
            response.raise_for_status()
            latest_release = response.json()
            latest_version = latest_release['tag_name']
            
            if latest_version != current_version:
                message = f"New update of this macro {latest_version} is available. Do you want to download the newest version?"
                if messagebox.askyesno("Update Available!!", message):
                    download_url = latest_release['assets'][0]['browser_download_url']
                    self.download_update(download_url)
                else:
                    if messagebox.askyesno("Don't Ask Again", "Would you like to stop receiving update notifications?"):
                        self.config["dont_ask_for_update"] = True
                        self.save_config()
                            
        except requests.RequestException as e:
            print(f"Failed to fetch the latest version from GitHub: {e}")
            
    # this cro was here (funny easter egg)
    
    def download_update(self, download_url):
        try:
            zip_filename = os.path.basename(download_url)
            save_path = filedialog.asksaveasfilename(defaultextension=".zip", initialfile=zip_filename, title="Save As")
            
            if not save_path: return
            
            response = requests.get(download_url)
            response.raise_for_status()
        
            with open(save_path, 'wb') as file:
                file.write(response.content)
            
            messagebox.showinfo("Download Complete", f"The latest version has been downloaded as {save_path}. Make sure to turn off antivirus and extract it manually.")
        except requests.RequestException as e:
            print(f"Failed to download the update: {e}")
    
    def open_biome_settings(self):
        settings_window = ttk.Toplevel(self.root)
        settings_window.title("Biome Settings")

        silly_note_label = ttk.Label(settings_window, text="GLITCHED and DREAMSPACE are both forced 'everyone' ping grrr >:((", foreground="red")
        silly_note_label.grid(row=0, columnspan=2, padx=(10, 0), pady=(10, 0))

        biomes = [biome for biome in self.biome_data.keys() if biome not in ["GLITCHED", "DREAMSPACE"]]
        window_height = max(475, len(biomes) * 43)
        settings_window.geometry(f"465x{window_height}")

        options = ["None", "Message"]

        for i, biome in enumerate(biomes):
            ttk.Label(settings_window, text=f"{biome}:").grid(row=i + 1, column=0, sticky="e")

            if biome not in self.variables:
                self.variables[biome] = ttk.StringVar(value="Message")

            dropdown = ttk.Combobox(settings_window, textvariable=self.variables[biome], values=options, state="readonly")
            dropdown.grid(row=i + 1, column=1, pady=5)

        def save_biome_setting():
            self.save_config()
            settings_window.destroy()

        ttk.Button(settings_window, text="Save", command=save_biome_setting).grid(row=len(biomes) + 2, column=1, pady=10)
        
    def open_buff_selections_window(self):
        buff_window = ttk.Toplevel(self.root)
        buff_window.title("Buff Selections")
        buff_window.geometry("440x340")

        buffs = {
            "Xyz Potion": 1,
            "Oblivion Potion": 1,
            "Heavenly Potion II": 1,
            "Fortune Potion III": 1,
            "Fortune Potion II": 1,
            "Fortune Potion I": 1,
            "Haste Potion III": 1,
            "Haste Potion II": 1,
            "Haste Potion I": 1,
            "Warp Potion": 1,
            "Strange Potion I": 1,
            "Strange Potion II": 1,
            "Stella's Candle": 1,
            "Speed Potion": 1,
            "Lucky Potion": 1,
        }

        if "auto_buff_glitched" not in self.config:
            self.config["auto_buff_glitched"] = {}

        num_columns = 2
        for i, (buff, default_amount) in enumerate(buffs.items()):
            buff_config = self.config["auto_buff_glitched"].get(buff, (False, default_amount))
            buff_enabled, buff_amount = buff_config

            self.buff_vars[buff] = ttk.BooleanVar(value=buff_enabled)
            self.buff_amount_vars[buff] = ttk.StringVar(value=str(buff_amount))

            row = i // num_columns
            col = (i % num_columns) * 2

            ttk.Checkbutton(
                buff_window, 
                text=buff, 
                variable=self.buff_vars[buff],
                command=self.save_config
            ).grid(row=row, column=col, sticky="w", padx=10, pady=5)

            entry = ttk.Entry(
                buff_window, 
                textvariable=self.buff_amount_vars[buff], 
                width=5
            )
            entry.grid(row=row, column=col + 1, padx=10, pady=5)
            entry.bind("<FocusOut>", lambda event: self.save_config())

    def create_webhook_tab(self, frame):
        ttk.Label(frame, text="Webhook URL:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        self.webhook_url_entry = ttk.Entry(frame, width=50, show="*")
        self.webhook_url_entry.grid(row=0, column=1, columnspan=2, pady=5)
        self.webhook_url_entry.insert(0, self.config.get("webhook_url", ""))
        self.webhook_url_entry.bind("<FocusOut>", lambda event: self.save_config())

        ttk.Label(frame, text="Private Server Link:").grid(row=2, column=0, sticky="e", padx=5, pady=5)
        self.private_server_link_entry = ttk.Entry(frame, width=50)
        self.private_server_link_entry.grid(row=2, column=1, columnspan=2, pady=5)
        self.private_server_link_entry.insert(0, self.config.get("private_server_link", ""))
        self.private_server_link_entry.bind("<FocusOut>", lambda event: self.validate_and_save_ps_link())

        ttk.Button(frame, text="Configure Biomes", command=self.open_biome_settings).grid(row=5, column=1, pady=10)
        ttk.Button(frame, text="Import Config", command=self.import_config).grid(row=5, column=2, pady=10)
        
    def create_misc_tab(self, frame):
        hp2_frame = ttk.Frame(frame)
        hp2_frame.pack(pady=10)

        # Auto Pop
        self.auto_pop_glitched_var = ttk.BooleanVar(value=self.config.get("auto_pop_glitched", False))
        auto_pop_glitched_check = ttk.Checkbutton(
            hp2_frame, 
            text="Auto Pop (in glitched biome)", 
            variable=self.auto_pop_glitched_var,
            command=self.save_config
        )
        auto_pop_glitched_check.grid(row=0, column=0, padx=5, sticky="w")

        # Glitched/Dreamspace biome record keybind
        self.record_rarest_biome_var = ttk.BooleanVar(value=self.config.get("record_rare_biome", False))
        record_rarest_biome_check = ttk.Checkbutton(
            hp2_frame, 
            text="Glitched/Dreamspace Biome clip keybind\n(require 1 of 2 recorders: Medal, Xbox Gaming Bar)", 
            variable=self.record_rarest_biome_var,
            command=self.save_config
        )
        record_rarest_biome_check.grid(row=1, column=0, padx=5, sticky="w")

        self.rarest_biome_keybind_var = ttk.StringVar(value=self.config.get("rare_biome_record_keybind", "shift + F8"))
        rarest_biome_keybind_entry = ttk.Entry(hp2_frame, textvariable=self.rarest_biome_keybind_var, width=10)
        rarest_biome_keybind_entry.grid(row=1, column=1, pady=5)
        rarest_biome_keybind_entry.bind("<FocusOut>", lambda event: self.save_config())

        # Buff Selections
        buff_selections_button = ttk.Button(
            hp2_frame, 
            text="Buff Selections", 
            command=self.open_buff_selections_window
        )
        buff_selections_button.grid(row=0, column=1, padx=5)

        # Biome Randomizer
        self.br_var = ttk.BooleanVar(value=self.config.get("biome_randomizer", False))
        br_check = ttk.Checkbutton(
            hp2_frame, 
            text="Biome Randomizer (BR)", 
            variable=self.br_var,
            command=self.save_config
        )
        br_check.grid(row=2, column=0, padx=5, sticky="w")

        ttk.Label(hp2_frame, text="Usage Duration (minutes):").grid(row=2, column=1, padx=5)
        self.br_duration_var = ttk.StringVar(value=self.config.get("br_duration", "30"))
        br_duration_entry = ttk.Entry(hp2_frame, textvariable=self.br_duration_var, width=10)
        br_duration_entry.grid(row=2, column=2, padx=5)
        br_duration_entry.bind("<FocusOut>", lambda event: self.save_config())

        # Strange Controller
        self.sc_var = ttk.BooleanVar(value=self.config.get("strange_controller", False))
        sc_check = ttk.Checkbutton(
            hp2_frame, 
            text="Strange Controller (SC)", 
            variable=self.sc_var,
            command=self.save_config
        )
        sc_check.grid(row=3, column=0, padx=5, sticky="w")

        ttk.Label(hp2_frame, text="Usage Duration (minutes):").grid(row=3, column=1, padx=5)
        self.sc_duration_var = ttk.StringVar(value=self.config.get("sc_duration", "15"))
        sc_duration_entry = ttk.Entry(hp2_frame, textvariable=self.sc_duration_var, width=10)
        sc_duration_entry.grid(row=3, column=2, padx=5)
        sc_duration_entry.bind("<FocusOut>", lambda event: self.save_config())

        # Merchant Teleporter
        self.mt_var = ttk.BooleanVar(value=self.config.get("merchant_teleporter", False))
        mt_check = ttk.Checkbutton(
            hp2_frame, 
            text="Merchant Teleporter (Auto Merchant)", 
            variable=self.mt_var,
            command=self.save_config
        )
        mt_check.grid(row=4, column=0, padx=5, sticky="w")

        ttk.Label(hp2_frame, text="Usage Duration (minutes):").grid(row=4, column=1, padx=5)
        self.mt_duration_var = ttk.StringVar(value=self.config.get("mt_duration", "1"))
        mt_duration_entry = ttk.Entry(hp2_frame, textvariable=self.mt_duration_var, width=10)
        mt_duration_entry.grid(row=4, column=2, padx=5)
        mt_duration_entry.bind("<FocusOut>", lambda event: self.save_config())

        # Auto Reconnect
        self.auto_reconnect_var = ttk.BooleanVar(value=self.config.get("auto_reconnect", False))
        auto_reconnect_check = ttk.Checkbutton(
            hp2_frame, 
            text="Auto reconnect to your PS (experimental)", 
            variable=self.auto_reconnect_var,
            command=self.save_config
        )
        auto_reconnect_check.grid(row=5, column=0, padx=5, sticky="w")
        auto_reconnect_check.bind("<FocusOut>", lambda event: self.save_config())

        reconnect_question_button = ttk.Button(
            hp2_frame, 
            text="?", 
            command=self.show_reconnect_info
        )
        reconnect_question_button.grid(row=5, column=1, padx=5, sticky="w")

        # Inventory Mouse Click Delay
        ttk.Label(hp2_frame, text="Inventory Mouse Click Delay (milliseconds):").grid(
            row=6, column=0, padx=5, pady=5, sticky="w"
        )
        self.click_delay_var = ttk.StringVar(value=self.config.get("inventory_click_delay", "0"))
        click_delay_entry = ttk.Entry(hp2_frame, textvariable=self.click_delay_var, width=10)
        click_delay_entry.grid(row=6, column=1, padx=5, pady=5, sticky="w")
        click_delay_entry.bind("<FocusOut>", lambda event: self.save_config())

        assign_inventory_button = ttk.Button(
            hp2_frame, 
            text="Assign Inventory Click", 
            command=self.open_assign_inventory_window
        )
        assign_inventory_button.grid(row=6, column=2, pady=5, sticky="w")
    
    def create_auras_tab(self, frame):
        self.enable_aura_detection_var = ttk.BooleanVar(value=self.config.get("enable_aura_detection", False))
        enable_aura_detection_check = ttk.Checkbutton(
            frame, 
            text="Enable Aura Detection", 
            variable=self.enable_aura_detection_var,
            command=self.save_config
        )
        enable_aura_detection_check.pack(anchor="w", padx=5, pady=5)

        aura_frame = ttk.LabelFrame(frame, text="Aura Detection")
        aura_frame.pack(fill='x', padx=5, pady=5)
        
        # Discord UserID (Aura Ping)
        ttk.Label(aura_frame, text="Discord UserID (Aura Ping):").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.aura_user_id_var = ttk.StringVar(value=self.config.get("aura_user_id", ""))
        aura_id_entry = ttk.Entry(aura_frame, textvariable=self.aura_user_id_var, width=25)
        aura_id_entry.grid(row=1, column=1, padx=5, pady=5)
        aura_id_entry.bind("<FocusOut>", lambda event: self.save_config())

        # Ping Minimum
        ttk.Label(aura_frame, text="Aura Ping Minimum:").grid(row=3, column=0, sticky="w", padx=5, pady=5)
        self.ping_minimum_var = ttk.StringVar(value=self.config.get("ping_minimum", "100000"))
        ping_minimum_entry = ttk.Entry(aura_frame, textvariable=self.ping_minimum_var, width=25)
        ping_minimum_entry.grid(row=3, column=1, padx=5, pady=5)
        ping_minimum_entry.bind("<FocusOut>", lambda event: self.save_config())

        # aura rec bool
        self.enable_aura_record_var = ttk.BooleanVar(value=self.config.get("enable_aura_record", False))
        enable_aura_record_check = ttk.Checkbutton(
            aura_frame, 
            text="Aura Clipping Keybind\n(require 1 of 2 recorders: Medal, Xbox Gaming Bar)", 
            variable=self.enable_aura_record_var,
            command=self.save_config
        )
        enable_aura_record_check.grid(row=4, column=0, sticky="w", padx=5, pady=5)

        # Aura rec keybind
        self.aura_record_keybind_var = ttk.StringVar(value=self.config.get("aura_record_keybind", "shift + F8"))
        aura_record_keybind_entry = ttk.Entry(aura_frame, textvariable=self.aura_record_keybind_var, width=25)
        aura_record_keybind_entry.grid(row=4, column=1, padx=5, pady=5)
        aura_record_keybind_entry.bind("<FocusOut>", lambda event: self.save_config())
        
        # Aura rec minimum
        ttk.Label(aura_frame, text="Aura minimum rarity to record:").grid(row=5, column=0, sticky="w", padx=5, pady=5)
        self.aura_record_minimum_var = ttk.StringVar(value=self.config.get("aura_record_minimum", "500000"))
        aura_record_minimum_entry = ttk.Entry(aura_frame, textvariable=self.aura_record_minimum_var, width=25)
        aura_record_minimum_entry.grid(row=5, column=1, padx=5, pady=5)
        aura_record_minimum_entry.bind("<FocusOut>", lambda event: self.save_config())

    def create_merchant_tab(self, frame):
        mari_frame = ttk.LabelFrame(frame, text="Mari")
        mari_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        mari_button = ttk.Button(mari_frame, text="Mari Item Settings", command=self.open_mari_settings)
        mari_button.pack(padx=3, pady=3)
        
        jester_frame = ttk.LabelFrame(frame, text="Jester")
        jester_frame.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
        jester_button = ttk.Button(jester_frame, text="Jester Item Settings", command=self.open_jester_settings)
        jester_button.pack(padx=3, pady=3)

        calibration_button = ttk.Button(frame, text="Merchant Calibrations", command=self.open_merchant_calibration_window)
        calibration_button.grid(row=1, column=0, padx=5, pady=3, sticky="w")


        ttk.Label(frame, text="Merchant item extra slot\n(extra slot if your mouse missed/cannot reach to merchant's 5th slot):").grid(row=2, column=0, padx=5, sticky="w")
        self.merchant_extra_slot_var = ttk.StringVar(value=self.config.get("merchant_extra_slot", "0"))
        merchant_extra_slot_entry = ttk.Entry(frame, textvariable=self.merchant_extra_slot_var, width=15)
        merchant_extra_slot_entry.grid(row=2, column=1, padx=0, pady=3, sticky="w")
        merchant_extra_slot_entry.bind("<FocusOut>", lambda event: self.save_config())

        # Ping Mari
        self.ping_mari_var = ttk.BooleanVar(value=self.config.get("ping_mari", False))
        ping_mari_check = ttk.Checkbutton(
            frame, text="Ping if Mari found? (Custom Ping UserID/RoleID: &roleid)",
            variable=self.ping_mari_var, command=self.save_config)
        ping_mari_check.grid(row=3, column=0, padx=5, pady=3, sticky="w")

        self.mari_user_id_var = ttk.StringVar(value=self.config.get("mari_user_id", ""))
        mari_user_id_entry = ttk.Entry(frame, textvariable=self.mari_user_id_var, width=15)
        mari_user_id_entry.grid(row=3, column=1, padx=0, pady=3, sticky="w")
        mari_user_id_entry.bind("<FocusOut>", lambda event: self.save_config())

        mari_label = ttk.Label(frame, text="")
        mari_label.grid(row=3, column=2, padx=5, pady=3, sticky="w")

        # Ping Jester
        self.ping_jester_var = ttk.BooleanVar(value=self.config.get("ping_jester", False))
        ping_jester_check = ttk.Checkbutton(
            frame, text="Ping if Jester found? (Custom Ping UserID/RoleID: &roleid)",
            variable=self.ping_jester_var, command=self.save_config)
        ping_jester_check.grid(row=4, column=0, padx=5, pady=3, sticky="w")

        self.jester_user_id_var = ttk.StringVar(value=self.config.get("jester_user_id", ""))
        jester_user_id_entry = ttk.Entry(frame, textvariable=self.jester_user_id_var, width=15)
        jester_user_id_entry.grid(row=4, column=1, padx=0, pady=3, sticky="w")
        jester_user_id_entry.bind("<FocusOut>", lambda event: self.save_config())

        jester_label = ttk.Label(frame, text="")
        jester_label.grid(row=4, column=2, padx=5, pady=3, sticky="w")

        # Required Package Frame
        package_frame = ttk.LabelFrame(frame, text="Required Package For Auto Merchant")
        package_frame.grid(row=5, column=0, padx=5, pady=5, sticky="nsew")

        # Tesseract OCR Status
        ocr_status = self.check_tesseract_ocr()
        ocr_status_text = "Tesseract OCR Installed: Yes" if ocr_status else "Tesseract OCR Installed: No, click here to get OCR module"
        ocr_status_label = ttk.Label(package_frame, text=ocr_status_text, foreground="light blue", cursor="hand2")
        ocr_status_label.pack(anchor="w", padx=5, pady=3)
        if not ocr_status:
            ocr_status_label.bind("<Button-1>", lambda e: self.download_tesseract())

        frame.grid_columnconfigure(0, weight=1)
        frame.grid_columnconfigure(1, weight=1)
        frame.grid_columnconfigure(2, weight=1)

    def check_tesseract_ocr(self):
        tesseract_env_path = os.getenv('TESSERACT_PATH')
        if tesseract_env_path and os.path.exists(tesseract_env_path):
            pytesseract.pytesseract.tesseract_cmd = tesseract_env_path
            return True

        possible_paths = [
            r'C:\Program Files\Tesseract-OCR\tesseract.exe',
            r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
            os.path.join(os.getenv('LOCALAPPDATA'), 'Programs', 'Tesseract-OCR', 'tesseract.exe'),
            os.path.join(os.getenv('LOCALAPPDATA'), 'Tesseract-OCR', 'tesseract.exe')
        ]

        for path in possible_paths:
            if os.path.exists(path):
                pytesseract.pytesseract.tesseract_cmd = path
                return True
                
        return False
    
    def download_tesseract(self):
        download_url = "https://github.com/tesseract-ocr/tesseract/releases/download/5.5.0/tesseract-ocr-w64-setup-5.5.0.20241111.exe"
        try:
            exe_filename = os.path.basename(download_url)
            save_path = filedialog.asksaveasfilename(defaultextension=".exe", initialfile=exe_filename, title="Save As")
            
            if not save_path:
                messagebox.showwarning("Download Cancelled", "No file path selected. Download cancelled.")
                return
            
            response = requests.get(download_url)
            response.raise_for_status()
        
            with open(save_path, 'wb') as file:
                file.write(response.content)
            
            messagebox.showinfo("Download Complete", f"Tesseract installer has been downloaded as {save_path}. Please run the installer to complete the setup. \n \n After installed tesseract, restart the macro to let it check if your ocr module is ready!")
        except requests.RequestException as e:
            messagebox.showerror("Download Failed", f"Failed to download Tesseract: {e}")
        except IOError as e:
            messagebox.showerror("File Error", f"Failed to save the file: {e}")

        
    def open_merchant_calibration_window(self):
        calibration_window = ttk.Toplevel(self.root)
        calibration_window.title("Merchant Calibration")
        calibration_window.geometry("765x345")

        positions = [
            ("Merchant Open Button", "merchant_open_button"),
            ("Merchant Dialogue Box", "merchant_dialogue_box"),
            ("Purchase Amount Button", "purchase_amount_button"),
            ("Purchase Button", "purchase_button"),
            ("First Item Slot Position", "first_item_slot_pos"),
            ("Merchant Name OCR Position", "merchant_name_ocr_pos"),
            ("Item Name OCR Position", "item_name_ocr_pos")
        ]

        self.coord_vars = {}

        for i, (label_text, config_key) in enumerate(positions):
            if "ocr" in config_key:
                label = ttk.Label(calibration_window, text=f"{label_text} (X, Y, W, H):")
                label.grid(row=i, column=0, padx=5, pady=5, sticky="w")

                x_var = ttk.IntVar(value=self.config.get(config_key, [0, 0, 0, 0])[0])
                y_var = ttk.IntVar(value=self.config.get(config_key, [0, 0, 0, 0])[1])
                w_var = ttk.IntVar(value=self.config.get(config_key, [0, 0, 0, 0])[2])
                h_var = ttk.IntVar(value=self.config.get(config_key, [0, 0, 0, 0])[3])
                self.coord_vars[config_key] = (x_var, y_var, w_var, h_var)

                ttk.Entry(calibration_window, textvariable=x_var, width=6).grid(row=i, column=1, padx=5, pady=5)
                ttk.Entry(calibration_window, textvariable=y_var, width=6).grid(row=i, column=2, padx=5, pady=5)
                ttk.Entry(calibration_window, textvariable=w_var, width=6).grid(row=i, column=3, padx=5, pady=5)
                ttk.Entry(calibration_window, textvariable=h_var, width=6).grid(row=i, column=4, padx=5, pady=5)

                select_button = ttk.Button(
                    calibration_window, text="Select Region (drag your mouse to select it)",
                    command=lambda key=config_key: self.merchant_snipping(key)
                )
            else:
                label = ttk.Label(calibration_window, text=f"{label_text} (X, Y):")
                label.grid(row=i, column=0, padx=5, pady=5, sticky="w")

                x_var = ttk.IntVar(value=self.config.get(config_key, [0, 0])[0])
                y_var = ttk.IntVar(value=self.config.get(config_key, [0, 0])[1])
                self.coord_vars[config_key] = (x_var, y_var)

                ttk.Entry(calibration_window, textvariable=x_var, width=6).grid(row=i, column=1, padx=5, pady=5)
                ttk.Entry(calibration_window, textvariable=y_var, width=6).grid(row=i, column=2, padx=5, pady=5)

                select_button = ttk.Button(
                    calibration_window, text="Select Pos",
                    command=lambda key=config_key: self.start_capture_thread(key, self.coord_vars)
                )

            select_button.grid(row=i, column=5, padx=5, pady=5)

        save_button = ttk.Button(calibration_window, text="Save Calibration", command=lambda: self.save_merchant_coordinates(calibration_window))
        save_button.grid(row=len(positions), column=0, columnspan=6, pady=10)
        
    def merchant_snipping(self, config_key):
        def on_region_selected(region):
            x, y, w, h = region
            x_var, y_var, w_var, h_var = self.coord_vars[config_key]
            x_var.set(x)
            y_var.set(y)
            w_var.set(w)
            h_var.set(h)

        snipping_tool = SnippingWidget(self.root, config_key=config_key, callback=on_region_selected)
        snipping_tool.start()
    
    def save_merchant_coordinates(self, calibration_window):
        for config_key, vars in self.coord_vars.items():
            if len(vars) == 4:
                self.config[config_key] = [var.get() for var in vars]
            else:
                self.config[config_key] = [vars[0].get(), vars[1].get()]
        self.save_config()
        calibration_window.destroy()
    
    def open_mari_settings(self):
        mari_window = ttk.Toplevel(self.root)
        mari_window.title("Mari Items")

        items = [
            "Void Coin", "Lucky Penny", "Mixed Potion", "Lucky Potion",
            "Lucky Potion L", "Lucky Potion XL", "Speed Potion",
            "Speed Potion L", "Speed Potion XL", "Gear A", "Gear B"
        ]

        item_frame = ttk.Frame(mari_window)
        item_frame.pack(padx=10, pady=10, fill='x')
        ttk.Label(item_frame, text="Item Name").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        ttk.Label(item_frame, text="Amount").grid(row=0, column=1, padx=5, pady=5, sticky="w")
        ttk.Label(item_frame, text="Rebuy").grid(row=0, column=2, padx=5, pady=5, sticky="w")

        self.mari_items_vars = {}
        self.mari_items_amounts = {}
        self.mari_items_rebuy = {}
        saved_mari_items = self.config.get("Mari_Items", {})

        for i, item in enumerate(items, start=1):
            saved_data = saved_mari_items.get(item, [False, 1, False])
            var = ttk.BooleanVar(value=saved_data[0])
            self.mari_items_vars[item] = var
            ttk.Checkbutton(item_frame, text=item, variable=var).grid(row=i, column=0, sticky="w", padx=5, pady=2)

            amount_var = ttk.StringVar(value=str(saved_data[1]))
            self.mari_items_amounts[item] = amount_var
            ttk.Entry(item_frame, textvariable=amount_var, width=5).grid(row=i, column=1, padx=5, pady=2)

            rebuy_var = ttk.BooleanVar(value=saved_data[2] if len(saved_data) > 2 else False)
            self.mari_items_rebuy[item] = rebuy_var
            ttk.Checkbutton(item_frame, variable=rebuy_var).grid(row=i, column=2, sticky="w", padx=5, pady=2)

        save_button = ttk.Button(mari_window, text="Save Selections", command=lambda: self.save_mari_selections(mari_window))
        save_button.pack(pady=10)


    def save_mari_selections(self, mari_window):
        mari_items = {
            item: [var.get(), int(self.mari_items_amounts[item].get()), self.mari_items_rebuy[item].get()]
            for item, var in self.mari_items_vars.items()
        }
        self.config["Mari_Items"] = mari_items
        self.save_config()
        mari_window.destroy()
    
    def open_jester_settings(self):
        jester_window = ttk.Toplevel(self.root)
        jester_window.title("Jester Items")

        items = [
            "Oblivion Potion", "Heavenly Potion", "Rune of Everything", "Rune of Dust",
            "Rune of Nothing", "Rune Of Corruption", "Rune Of Hell", "Rune of Galaxy",
            "Rune of Rainstorm", "Rune of Frost", "Rune of Wind", "Strange Potion", "Lucky Potion",
            "Stella's Candle", "Merchant Tracker", "Random Potion Sack"
        ]

        item_frame = ttk.Frame(jester_window)
        item_frame.pack(padx=10, pady=10, fill='x')
        ttk.Label(item_frame, text="Item Name").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        ttk.Label(item_frame, text="Amount").grid(row=0, column=1, padx=5, pady=5, sticky="w")
        ttk.Label(item_frame, text="Rebuy").grid(row=0, column=2, padx=5, pady=5, sticky="w")

        self.jester_items_vars = {}
        self.jester_items_amounts = {}
        self.jester_items_rebuy = {}
        saved_jester_items = self.config.get("Jester_Items", {})

        for i, item in enumerate(items, start=1):
            saved_data = saved_jester_items.get(item, [False, 1, False])
            var = ttk.BooleanVar(value=saved_jester_items.get(item, [False, 1, False])[0])
            self.jester_items_vars[item] = var
            ttk.Checkbutton(item_frame, text=item, variable=var).grid(row=i, column=0, sticky="w", padx=5, pady=2)
        
            amount_var = ttk.StringVar(value=str(saved_jester_items.get(item, [False, 1, False])[1]))
            self.jester_items_amounts[item] = amount_var
            ttk.Entry(item_frame, textvariable=amount_var, width=5).grid(row=i, column=1, padx=5, pady=2)

            rebuy_var = ttk.BooleanVar(value=saved_data[2] if len(saved_data) > 2 else False)
            self.jester_items_rebuy[item] = rebuy_var
            ttk.Checkbutton(item_frame, variable=rebuy_var).grid(row=i, column=2, sticky="w", padx=5, pady=2)

        save_button = ttk.Button(jester_window, text="Save Selections", command=lambda: self.save_jester_selections(jester_window))
        save_button.pack(pady=10)

    def save_jester_selections(self, jester_window):
        jester_items = {
            item: [var.get(), int(self.jester_items_amounts[item].get()), self.jester_items_rebuy[item].get()]
            for item, var in self.jester_items_vars.items()
        }
        self.config["Jester_Items"] = jester_items
        self.save_config()
        jester_window.destroy()
    
    def create_stats_tab(self, frame):
        self.stats_labels = {}
        biomes = list(self.biome_data.keys())
    
        columns = 5
        for i, biome in enumerate(biomes):
            color = f"#{int(self.biome_data[biome]['color'], 16):06x}"
            label = ttk.Label(frame, text=f"{biome}: {self.biome_counts[biome]}", foreground=color)
            
            row = i // columns
            col = i % columns
            
            label.grid(row=row, column=col, sticky="w", padx=2, pady=1)
            self.stats_labels[biome] = label

        # Total Biomes Found
        total_biomes = sum(self.biome_counts.values())
        self.total_biomes_label = ttk.Label(frame, text=f"Total Biomes Found: {total_biomes}", foreground="light green")
        self.total_biomes_label.grid(row=row + 1, column=0, columnspan=columns, sticky="w", padx=5, pady=5)

        # Running Session
        session_time = self.get_total_session_time()
        self.session_label = ttk.Label(frame, text=f"Running Session: {session_time}")
        self.session_label.grid(row=row + 2, column=0, columnspan=columns, sticky="w", padx=5, pady=10)

        # Biome Logs
        logs_frame = ttk.Frame(frame, borderwidth=2, relief="solid")
        logs_frame.grid(row=0, column=6, rowspan=5, sticky="nsew", padx=10, pady=2)
        logs_label = ttk.Label(logs_frame, text="Biome Logs")
        logs_label.pack(anchor="w", padx=5, pady=2)

        search_entry = ttk.Entry(logs_frame)
        search_entry.pack(anchor="w", padx=5, pady=1)
        search_entry.bind("<KeyRelease>", lambda event: self.filter_logs(search_entry.get()))

        self.logs_text = ttk.Text(logs_frame, height=8, width=25, wrap="word")
        self.logs_text.pack(expand=True, fill="both", padx=5, pady=5)
        self.logs_text.config(state="disabled")
        
        
        self.glitch_effect()
        
    def glitch_effect(self):
        glitch_texts = [
            "GLITCHED", "GlItChEd", "gLiTcHeD", "GL1TCHED", "g#lt#c%", 
            "g!olitc3", "g$&*ct", "G1iTcHeD", "gL1tCh3d", "gL!tCh3d",
            "G1!tCh3D", "gL1tCh3D", "gL!tCh3D", "G1!tCh3d", "gL1tCh3d"]
        
        glitch_colors = [
            "#FF0000", "#00FF00", "#0000FF", "#FFFF00", "#FF00FF", 
            "#00FFFF", "#a6c9a3", "#ff69b4", "#8a2be2", "#7fff00",
            "#d2691e", "#ff7f50", "#6495ed", "#dc143c", "#00ced1"
        ]

        def update_glitch():
            glitchy_ahh_text = random.choice(glitch_texts)
            color = random.choice(glitch_colors)
            self.stats_labels["GLITCHED"].config(text=f"{glitchy_ahh_text}: {self.biome_counts['GLITCHED']}", foreground=color)
            self.root.after(25, update_glitch)

        update_glitch()
        
    def create_credit_tab(self, credits_frame):
        current_dir = os.getcwd()
        images_dir = os.path.join(current_dir, "images")
        credit_paths = [
            os.path.join(images_dir, "tea.png"),
            os.path.join(images_dir, "maxstellar.png")
        ]

        def load_image(filename, size):
            for path in credit_paths:
                if os.path.basename(path) == filename and os.path.exists(path):
                    try:
                        img = Image.open(path)
                        img = img.resize(size, Image.LANCZOS)
                        return ImageTk.PhotoImage(img)
                    except Exception as e:
                        print(f"Failed to load image: {path}, Error: {e}")
                        return None
            return None

        credits_frame_content = ttk.Frame(credits_frame)
        credits_frame_content.pack(pady=20)

        noteab_image = load_image("tea.png", (85, 85))
        maxstellar_image = load_image("maxstellar.png", (85, 85))

        noteab_frame = ttk.Frame(credits_frame_content, borderwidth=2, relief="solid")
        noteab_frame.grid(row=0, column=0, padx=10, pady=2)

        maxstellar_frame = ttk.Frame(credits_frame_content, borderwidth=2, relief="solid")
        maxstellar_frame.grid(row=0, column=1, padx=10, pady=2)

        if noteab_image:
            ttk.Label(noteab_frame, image=noteab_image).pack(pady=5)
        ttk.Label(noteab_frame, text="Main Developer: Noteab").pack()

        discord_label = ttk.Label(noteab_frame, text="Join my Community Server!!", foreground="#03cafc", cursor="hand2")
        discord_label.pack()
        discord_label.bind("<Button-1>", lambda e: webbrowser.open_new("https://discord.gg/radiant-team"))

        github_label = ttk.Label(noteab_frame, text="GitHub: Noteab Biome Macro!", foreground="#03cafc", cursor="hand2")
        github_label.pack()
        github_label.bind("<Button-1>", lambda e: webbrowser.open_new("https://github.com/noteab/Sol-Biome-Tracker"))

        if maxstellar_image:
            ttk.Label(maxstellar_frame, image=maxstellar_image).pack(pady=5)
        ttk.Label(maxstellar_frame, text="Inspired Biome Macro Creator: Maxstellar").pack()
        maxstellar_yt = ttk.Label(maxstellar_frame, text="Their YT channel", foreground="#03cafc", cursor="hand2")
        maxstellar_yt.pack()
        maxstellar_yt.bind("<Button-1>", lambda e: webbrowser.open_new("https://www.youtube.com/@maxstellar_"))

        self.noteab_image = noteab_image
        self.maxstellar_image = maxstellar_image
    
    def update_stats(self):
        total_biomes = sum(self.biome_counts.values())

        for biome, label in self.stats_labels.items():
            label.config(text=f"{biome}: {self.biome_counts[biome]}")

        self.total_biomes_label.config(text=f"Total Biomes Found: {total_biomes}", foreground="light green")
        self.session_label.config(text=f"Running Session: {self.get_total_session_time()}")
        self.save_config()
        

    def get_total_session_time(self):
        try:
            if self.start_time:
                elapsed_time = datetime.now() - self.start_time
                total_seconds = int(elapsed_time.total_seconds()) + self.saved_session
            else:
                total_seconds = self.saved_session

            # hours, minutes, and seconds
            hours, remainder = divmod(total_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)

            # Format time string
            return f"{hours:02}:{minutes:02}:{seconds:02}"

        except Exception as e:
            self.error_logging(e, "Error in get_total_session_time function.")
            return "00:00:00"

    def parse_session_time(self, session_time_str):
        try:
            parts = session_time_str.split(":")
            if len(parts) == 3:  # Format: hours:minutes:seconds
                hours, minutes, seconds = map(int, parts)
                return hours * 3600 + minutes * 60 + seconds
            else:
                raise ValueError("Invalid session time format")

        except Exception as e:
            self.error_logging(e, "Error parsing session time.")
            return 0  # Return default value in case of error, well yeah
    
    def update_session_time(self):
        try:
            if self.start_time:
                elapsed_time = datetime.now() - self.start_time
                total_seconds = int(elapsed_time.total_seconds()) + self.saved_session

                # hours, minutes, and seconds
                hours, remainder = divmod(total_seconds, 3600)
                minutes, seconds = divmod(remainder, 60)

                # Format string
                session_time_str = f"{hours:02}:{minutes:02}:{seconds:02}"
                self.session_label.config(text=f"Running Session: {session_time_str}")

        except Exception as e:
            self.error_logging(e, "Error in update_session_time function.")
    
    def display_logs(self, logs=None):
        self.logs_text.config(state="normal")
        self.logs_text.delete(1.0, ttk.END)
        
        if logs is None: 
            logs = self.logs
            
        last_logs = logs[-10:]
         
        for log in last_logs: 
            self.logs_text.insert(ttk.END, log + "\n")
        self.logs_text.config(state="disabled")

    def filter_logs(self, keyword):
        filtered_logs = [log for log in self.logs if keyword.lower() in log.lower()]
        self.display_logs(filtered_logs)
        
    def append_log(self, message):
        self.logs.append(message)
        self.display_logs()
        self.save_logs()
        self.logs_text.see(ttk.END)
        
    ## INVENTORY SNIPPING ##
    
    def open_assign_inventory_window(self):
        assign_window = ttk.Toplevel(self.root)
        assign_window.title("Inventory Coordinates")
        assign_window.geometry("550x340")

        positions = [
            ("Inventory Menu", "inventory_menu"),
            ("Items Tab", "items_tab"),
            ("Search Bar", "search_bar"),
            ("First Item Slot", "first_item_slot"),
            ("Amount Box", "amount_box"),
            ("Use Button", "use_button"),
            ("'START' button (for reconnect feature, \n the one above 'Update Logs' button)", "reconnect_start_button")
        ]

        coord_vars = {}

        for i, (label_text, config_key) in enumerate(positions):
            label = ttk.Label(assign_window, text=f"{label_text} (X, Y):")
            label.grid(row=i, column=0, padx=5, pady=5, sticky="w")

            x_var = ttk.IntVar(value=self.config.get(config_key, [0, 0])[0])
            y_var = ttk.IntVar(value=self.config.get(config_key, [0, 0])[1])
            coord_vars[config_key] = (x_var, y_var)

            x_entry = ttk.Entry(assign_window, textvariable=x_var, width=6)
            x_entry.grid(row=i, column=1, padx=5, pady=5)

            y_entry = ttk.Entry(assign_window, textvariable=y_var, width=6)
            y_entry.grid(row=i, column=2, padx=5, pady=5)

            select_button = ttk.Button(
                assign_window, text="Assign Click",
                command=lambda key=config_key: self.start_capture_thread(key, coord_vars)
            )
            select_button.grid(row=i, column=3, padx=5, pady=5)

        save_button = ttk.Button(assign_window, text="Save", command=lambda: self.save_inventory_coordinates(assign_window, coord_vars))
        save_button.grid(row=len(positions), column=0, columnspan=4, pady=10)
        
    def save_inventory_coordinates(self, window, coord_vars):
        for key, (x_var, y_var) in coord_vars.items():
            self.config[key] = [x_var.get(), y_var.get()]
        self.save_config()
        window.destroy()
        
    def start_capture_thread(self, config_key, coord_vars):
        snipping_tool = SnippingWidget(self.root, config_key=config_key, callback=lambda region: self.update_coordinates(config_key, region, coord_vars))
        snipping_tool.start()

    def update_coordinates(self, config_key, region, coord_vars):
        x, y, _, _ = region
        x_var, y_var = coord_vars[config_key]
        x_var.set(x)
        y_var.set(y)
            
    ## INVENTORY SNIPPING ^^ ##
    def validate_and_save_ps_link(self):
        private_server_link = self.private_server_link_entry.get()
        if not self.validate_private_server_link(private_server_link):
            messagebox.showwarning(
                "Invalid PS Link!",
                "The link you provided is not a valid Roblox link. It could be either a share link or a private server code link. "
                "Please ensure the link is correct and try again.\n\n"
                "Valid links should look like:\n"
                "- Share link: https://www.roblox.com/share?code=1234567899abcdefxyz&type=Server\n"
                "- Private server link: https://www.roblox.com/games/15532962292/Sols-RNG-Eon1-1?privateServerLinkCode=..."
            )
            return

        self.save_config()

    def validate_private_server_link(self, link):
        share_pattern = r"https://www\.roblox\.com/share\?code=\w+&type=Server"
        private_server_pattern = r"https://www\.roblox\.com/games/\d+/Sols-RNG-Eon1-1\?privateServerLinkCode=\w+"
        second_ps_pattern = r"https://www\.roblox\.com/games/\d+/Sols-RNG\?privateServerLinkCode=\w+"

        return re.match(share_pattern, link) or re.match(private_server_pattern, link) or re.match(second_ps_pattern, link)
    
    def show_reconnect_info(self):
        messagebox.showinfo(
            "Auto Reconnect Info",
            "(?) This feature only able to reconnect if:\n \n"
            "(1) Your private server link is a private server code 'Sols-RNG?privateServerLinkCode=randomnumberhere', not a share link like this: 'https://www.roblox.com/share?code=...&type=Server' \n \n"
            "(2) Make sure to calibrate mouse click for 'Start' button in 'Assign Inventory Click' \n \n"
            "(3) You can find a tutorial on YouTube to see how to convert a share link to a private server code! \n \n"
            "(Note: This reconnect feature still on experimental phase, there's a chance it gonna be failed to reconnect back to your server!)"
        )

    def start_detection(self):
        if not self.detection_running:
            self.detection_running = True
            self.start_time = datetime.now()
            
            self.check_disconnect_thread = threading.Thread(target=self.check_disconnect_loop, daemon=True)
            self.check_disconnect_thread.start()
            
            self.detection_thread = threading.Thread(target=self.biome_loop_check, daemon=True)
            self.detection_thread.start()
            
            self.biome_item_change_thread = threading.Thread(target=self.biome_itemchange_loop, daemon=True)
            self.biome_item_change_thread.start()
            
            self.aura_check_thread = threading.Thread(target=self.aura_loop_check, daemon=True)
            self.aura_check_thread.start()
            
            self.root.title("Noteab's Biome Macro (v1.5.4-patch2.8.4) (Running)")
            self.send_webhook_status("Macro started!", color=0x64ff5e)
            print("Biome detection started.")

    def stop_detection(self):
        if self.detection_running:
            self.detection_running = False

            elapsed_time = int((datetime.now() - self.start_time).total_seconds())
            self.saved_session += elapsed_time

            self.start_time = None
            self.root.title("Noteab's Biome Macro (v1.5.4-patch2.8.4) (Stopped)")
            self.send_webhook_status("Macro stopped!", color=0xff0000)
            self.save_config()
            print("Biome detection stopped.")
    
    def get_latest_log_file(self):
        files = [os.path.join(self.logs_dir, f) for f in os.listdir(self.logs_dir) if f.endswith('.log')]
        latest_file = max(files, key=os.path.getmtime)
        return latest_file

    def read_log_file(self, log_file_path):
        if not os.path.exists(log_file_path):
            print(f"Log file not found: {log_file_path}")
            return []

        with open(log_file_path, 'r', encoding='utf-8', errors='ignore') as file:
            file.seek(self.last_position)
            lines = file.readlines()
            self.last_position = file.tell()
            return lines
        
    def read_full_log_file(self, log_file_path):
        if not os.path.exists(log_file_path):
            print(f"Log file not found: {log_file_path}")
            return []

        with open(log_file_path, 'r', encoding='utf-8', errors='ignore') as file:
            return file.readlines()
        
    def load_auras_json(self):
        auras_paths = [
            "auras.json",
            "source_code/auras.json",
            os.path.join(os.path.dirname(__file__), "auras.json"),
            os.path.join(os.path.dirname(__file__), "source_code/auras.json")
        ]
        
        try:
            for path in auras_paths:
                if os.path.exists(path):
                    with open(path, "r") as file:
                        aura_data = json.load(file)
                        return aura_data
        except Exception as e:
            print(f"Error loading auras.json: {e}")
            self.error_logging(e, f"Error loading auras.json")
            return {}
        
    def check_aura_in_logs(self, log_file_path):
        try:
            if self.reconnecting_state: return
            
            if not hasattr(self, 'last_aura_found'):
                self.last_aura_found = None

            log_lines = self.read_full_log_file(log_file_path)

            for line in reversed(log_lines):
                try:
                    match = re.search(r'"state":"Equipped \\"(.*?)\\"', line)
                    if match:
                        aura = match.group(1)

                        if aura in self.auras_data:
                            aura_info = self.auras_data[aura]
                            rarity = aura_info["rarity"]
                            exclusive_biome, multiplier = aura_info["exclusive_biome"]

                            # Check if the current biome is GLITCHED
                            if self.current_biome == "GLITCHED":
                                rarity /= multiplier
                                biome_message = "[From GLITCHED!]"

                            # Check if the current biome is the aura's exclusive biome
                            elif self.current_biome == exclusive_biome:
                                rarity /= multiplier
                                biome_message = f"[From {exclusive_biome}!]"

                            else:
                                biome_message = ""

                            # Format rarity 
                            formatted_rarity = f"{int(rarity):,}"

                            if aura != self.last_aura_found:
                                self.send_aura_webhook(aura, formatted_rarity, biome_message)
                                self.last_aura_found = aura
                                
                                if self.enable_aura_record_var.get() and rarity >= int(self.aura_record_minimum_var.get()):
                                    self.trigger_aura_record()
                        else:
                            # Aura not found in auras_data (biomes_data.json)
                            if aura != self.last_aura_found:
                                self.send_aura_webhook(aura, None, "")
                                self.last_aura_found = aura
                        return

                except Exception as e:
                    self.error_logging(e, "Error processing specific aura in check_aura_in_logs.")

        except Exception as e:
            self.error_logging(e, "Error in main check_aura_in_logs function")
            
    def check_biome_in_logs(self):
        try:
            log_file_path = self.get_latest_log_file()
            log_lines = self.read_log_file(log_file_path)

            for line in reversed(log_lines):
                for biome in self.biome_data:
                    if f'"largeImage":{{"hoverText":"{biome}"' in line:
                        threading.Thread(target=self.handle_biome_detection, args=(biome,)).start()
                        return

        except Exception as e:
            self.error_logging(e, "Error in check_biome_in_logs function :skull:")
                
    def handle_biome_detection(self, biome):
        try:
            if self.current_biome != biome:
                biome_info = self.biome_data[biome]
                now = datetime.now()
                
                print(f"Detected Biome: {biome}, Color: {biome_info['color']}")
                self.append_log(f"Detected Biome: {biome}")
                
                self.current_biome = biome
                self.last_sent[biome] = now

                # Update counter of that biome
                self.biome_counts[biome] += 1
                self.update_stats()

                message_type = self.config["biome_notifier"].get(biome, "None")
                
                if biome in ["GLITCHED", "DREAMSPACE"]:
                    message_type = "Ping"
                    if self.config.get("record_rare_biome", False): 
                        self.trigger_biome_record()

                self.send_webhook(biome, message_type, "start")
                
                if biome == "GLITCHED":
                    with self.lock:
                        if self.config.get("auto_pop_glitched", False):
                            self.auto_pop_state = True
                            self.auto_pop_buffs()
                            self.auto_pop_state = False

        except Exception as e:
            self.error_logging(e, f"Error in handle_biome_detection for biome: {biome}. Hell naw go fix your ass macro noteab! - Wise greenie word")
            
    def biome_loop_check(self):
        last_log_file = None

        while self.detection_running:
            try:
                current_log_file = self.get_latest_log_file()
                if current_log_file != last_log_file:
                    self.last_position = 0
                    last_log_file = current_log_file
                    
                self.check_biome_in_logs()
                self.update_session_time()
                time.sleep(1)

            except Exception as e:
                self.error_logging(e, "Error in biome_loop_check function.")
                
    def aura_loop_check(self):
        last_log_file = None
        while self.detection_running:
            try:
                current_log_file = self.get_latest_log_file()
                if current_log_file != last_log_file:
                    self.last_position = 0
                    last_log_file = current_log_file
                    
                if self.enable_aura_detection_var.get(): self.check_aura_in_logs(current_log_file)
                time.sleep(0.6)
                    
            except Exception as e:
                self.error_logging(e, "Error in aura_loop_check function.")

    def biome_itemchange_loop(self):
        while self.detection_running:
            try:           
                with self.lock: self.auto_biome_change()
                time.sleep(1)
                    
            except Exception as e:
                self.error_logging(e, "Error in biome_itemchange_loop function.")
                
    def check_disconnect_loop(self, current_attempt=1):
        if not hasattr(self, 'has_sent_disconnected_message'):
            self.has_sent_disconnected_message = False

        while self.detection_running:
            try:
                if not self.check_roblox_procs():
                    print("Roblox instance is closed. Stopping detection.")
                    
                    if not self.has_sent_disconnected_message:
                        self.send_webhook_status("Roblox instance closed!", color=0xff0000)
                        self.has_sent_disconnected_message = True
                    
                    self.root.title("Noteab's Biome Macro (v1.5.4-patch2.8.4) (Roblox Disconnected :c )")
                    self.reconnecting_state = True
                    
                    time.sleep(4.5)
                    
                    # Check for auto reconnect
                    if self.config.get("auto_reconnect"):
                        private_server_link = self.config.get("private_server_link")
                        if private_server_link:
                            private_server_code = private_server_link.split("privateServerLinkCode=")[-1]
                            roblox_deep_link = f"roblox://placeID=15532962292&linkCode={private_server_code}"
                            
                            max_retries = 3
                            self.reconnecting_state = True
                            for attempt in range(current_attempt, max_retries + 1):
                                print(f"Reconnecting to your server... hold on bro (Attempt #{attempt})")
                                self.terminate_roblox_processes()
                                self.send_webhook_status(f"Reconnecting to your server... hold on bro", color=0xffff00)
                                self.root.title("Noteab's Biome Macro (v1.5.4-patch2.8.4) (Reconnecting)")
                                
                                os.startfile(roblox_deep_link)
                                time.sleep(36)
                                
                                if self.check_roblox_procs():
                                    print("Roblox instance is now running.")
                                    self.send_webhook_status("Roblox opened. Loading into the games...", color=0x4aff65)
                                    self.has_sent_disconnected_message = False
                                    if not self.reconnect_check_start_button():
                                        print("Fallback: Unable to start the game after multiple attempts.")
                                        self.send_webhook_status("Stuck in 'In Main Menu' for too long. I might reconnect bro back to server again", color=0xff0000)
                                        continue
                                    break
                                
                                time.sleep(1)
                            
                            if attempt == max_retries:
                                print("Max retries reached. Unable to reconnect to Roblox. Reconnecting to public server.")
                                self.terminate_roblox_processes()
                                self.send_webhook_status("Max retries reached. Reconnecting to public server.", color=0xff0000)
                                os.startfile("roblox://placeID=15532962292")
                                time.sleep(36)
                                
                                if self.check_roblox_procs():
                                    print("Roblox instance is now running.")
                                    self.send_webhook_status("Roblox opened. Loading into the games...", color=0x4aff65)
                                    self.has_sent_disconnected_message = False 
                                    if not self.reconnect_check_start_button():
                                        print("Fallback: Unable to start the game after multiple attempts.")
                                        self.send_webhook_status("Cannot start after reconnecting to the public server", color=0xff0000)

                        else:
                            self.send_webhook_status("No correct PS link format found for reconnection (Either your link is shared link not privateServerLinkCode)", color=0xff0000)
                    
                    self.detection_running = True
                    continue
                
                # Reset flag if Roblox is running
                self.has_sent_disconnected_message = False
                self.root.title("Noteab's Biome Macro (v1.5.4-patch2.8.4) (Running)")
                
                if self.reconnecting_state:
                    time.sleep(18)
                    self.reconnecting_state = False
                    
                time.sleep(1)
                
            except Exception as e:
                self.error_logging(e, "Error in check_disconnect_loop function.")

    def fallback_reconnect(self, current_attempt):
        print(f"Attempting fallback reconnect from attempt {current_attempt}...")
        self.reconnecting_state = True 

        self.terminate_roblox_processes()
        self.check_disconnect_loop(current_attempt)
        self.reconnecting_state = False
    
    def reconnect_check_start_button(self):
        try:
            self.root.title("Noteab's Biome Macro (v1.5.4-patch2.8.4) (Reconnecting - In Main Menu)")
            reconnect_start_button = self.config.get("reconnect_start_button", [954, 876])
            max_clicks = 25
            failed_clicks = 0
            
            for _ in range(8):
                if not self.detection_running: return
                self.activate_roblox_window()
                time.sleep(0.35)

            for _ in range(max_clicks):
                if not self.detection_running: return
                self.Global_MouseClick(reconnect_start_button[0], reconnect_start_button[1])
                time.sleep(0.95)

                # Check reconnect state in the logs
                if self.reconnect_logs_state():
                    self.send_webhook_status("Clicked 'Start' button and you are in the game now!!", color=0x4aff65)
                    print("Game has started, exiting click loop.")
                    self.detection_running = True
                    self.root.title("Noteab's Biome Macro (v1.5.4-patch2.8.4) (Running)")
                    return True  # yay joins!!
                
                print("Still in Main Menu, clicking again...")
                failed_clicks += 1
                
                # Fallback if stuck in "In Main Menu" screen
                if failed_clicks >= 25:
                    print("Fallback: Stuck in 'In Main Menu' for too long. What is this skibidi")
                    return False
                
        except Exception as e:
            self.error_logging(e, "Error in reconnect_check_start_button function.")
        
        return False
        

    def reconnect_logs_state(self):
        try:
            log_file_path = self.get_latest_log_file()
            log_lines = self.read_full_log_file(log_file_path)

            for line in reversed(log_lines):
                if re.search(r'"state":"Equipped', line): return True 

        except Exception as e:
            self.error_logging(e, "Error in reconnect_logs_state function.")
        
        return False
        
    def check_roblox_procs(self):
        try:
            current_user = psutil.Process().username()
            running_processes = psutil.process_iter(['pid', 'name', 'username'])
            roblox_processes = []

            for proc in running_processes:
                if proc.info['name'] in ['RobloxPlayerBeta.exe', 'Windows10Universal.exe'] and proc.info['username'] == current_user:
                    roblox_processes.append(proc.info)

            if roblox_processes: return True

        except Exception as e:
            self.error_logging(e, "Error in check_roblox_procs function.")
        
        return False  # no Roblox processes are found
    
    def terminate_roblox_processes(self):
        try:
            current_user = psutil.Process().username()
            running_processes = psutil.process_iter(['pid', 'name', 'username'])

            for proc in running_processes:
                if proc.info['name'] in ['RobloxPlayerBeta.exe', 'Windows10Universal.exe'] and proc.info['username'] == current_user:
                    print(f"Terminating process: {proc.info['name']} (PID: {proc.info['pid']})")
                    proc.terminate()
                    proc.wait()

        except Exception as e:
            self.error_logging(e, "Error in terminate_roblox_processes function.")
        
    def auto_biome_change(self):
        try:
            mt_cooldown = timedelta(minutes=int(self.mt_duration_var.get()) if self.mt_duration_var.get() else 1) 
        except ValueError:
            mt_cooldown = timedelta(minutes=1)

        if self.mt_var.get() and datetime.now() - self.last_mt_time >= mt_cooldown:
            self.use_merchant_teleporter()
            self.last_mt_time = datetime.now()
            
        try:
            sc_cooldown = timedelta(minutes=int(self.sc_duration_var.get()) if self.sc_duration_var.get() else 20)
        except ValueError:
            sc_cooldown = timedelta(minutes=20)

        if self.sc_var.get() and datetime.now() - self.last_sc_time >= sc_cooldown:
            self.use_br_sc('strange controller')
            self.last_sc_time = datetime.now()
            
        try:
            br_cooldown = timedelta(minutes=int(self.br_duration_var.get()) if self.br_duration_var.get() else 35)
        except ValueError:
            br_cooldown = timedelta(minutes=35)

        if self.br_var.get() and datetime.now() - self.last_br_time >= br_cooldown:
            self.use_br_sc('biome randomizer')
            self.last_br_time = datetime.now()
    
    def Global_MouseClick(self, x, y, click=1):
        time.sleep(0.335)
        autoit.mouse_click("left", x, y, click, speed=3)
        
    def use_br_sc(self, item_name):
        try:
            if not self.detection_running or self.reconnecting_state or self.auto_pop_state or self.on_auto_merchant_state or self.current_biome == "GLITCHED": return
            time.sleep(1.3)

            inventory_click_delay = int(self.config.get("inventory_click_delay", "0")) / 1000.0
            inventory_menu = self.config.get("inventory_menu", [36, 535])
            items_tab = self.config.get("items_tab", [1272, 329])
            search_bar = self.config.get("search_bar", [855, 358])
            first_item_slot = self.config.get("first_item_slot", [839, 434])
            amount_box = self.config.get("amount_box", [594, 570])
            use_button = self.config.get("use_button", [710, 573])

            for _ in range(5):
                if not self.detection_running or self.reconnecting_state or self.auto_pop_state or self.on_auto_merchant_state or self.current_biome == "GLITCHED": return
                self.activate_roblox_window()
                time.sleep(0.15)

            print(f"Using {item_name.capitalize()}")

            # Inventory menu
            self.Global_MouseClick(inventory_menu[0], inventory_menu[1])
            time.sleep(0.2 + inventory_click_delay)

            # Items tab
            self.Global_MouseClick(items_tab[0], items_tab[1])
            time.sleep(0.2 + inventory_click_delay) 
            if not self.detection_running or self.reconnecting_state or self.auto_pop_state or self.on_auto_merchant_state or self.current_biome == "GLITCHED": return

            # Search bar
            self.Global_MouseClick(search_bar[0], search_bar[1], click=2)
            time.sleep(0.2 + inventory_click_delay) 
            if not self.detection_running or self.reconnecting_state or self.auto_pop_state or self.on_auto_merchant_state or self.current_biome == "GLITCHED": return
            autoit.send(item_name)
            time.sleep(0.3 + inventory_click_delay)
            self.Global_MouseClick(first_item_slot[0], first_item_slot[1])
            time.sleep(0.3 + inventory_click_delay) 
            if not self.detection_running or self.reconnecting_state or self.auto_pop_state or self.on_auto_merchant_state or self.current_biome == "GLITCHED": return
            # Amount
            self.Global_MouseClick(amount_box[0], amount_box[1])
            time.sleep(0.16 + inventory_click_delay) 
            autoit.send("^{a}")
            time.sleep(0.13 + inventory_click_delay)
            autoit.send("{BACKSPACE}")
            time.sleep(0.13 + inventory_click_delay)
            autoit.send('1')
            time.sleep(0.13 + inventory_click_delay)
            
            if not self.detection_running or self.reconnecting_state or self.auto_pop_state or self.on_auto_merchant_state or self.current_biome == "GLITCHED": return
            # use button
            self.Global_MouseClick(use_button[0], use_button[1])
            time.sleep(0.22 + inventory_click_delay) 

            if not self.detection_running or self.reconnecting_state or self.auto_pop_state or self.on_auto_merchant_state or self.current_biome == "GLITCHED": return
            # inventory menu
            self.Global_MouseClick(inventory_menu[0], inventory_menu[1])
            time.sleep(0.22 + inventory_click_delay) 

        except Exception as e:
            self.error_logging(e, "Error in use_br_sc function.")
        
    def use_merchant_teleporter(self):
        try:
            if not self.detection_running or self.reconnecting_state or self.auto_pop_state or self.on_auto_merchant_state or self.current_biome == "GLITCHED": return
            time.sleep(0.75)

            inventory_click_delay = int(self.config.get("inventory_click_delay", "0")) / 1000.0
            inventory_menu = self.config.get("inventory_menu", [36, 535])
            items_tab = self.config.get("items_tab", [1272, 329])
            search_bar = self.config.get("search_bar", [855, 358])
            first_item_slot = self.config.get("first_item_slot", [839, 434])
            amount_box = self.config.get("amount_box", [594, 570])
            use_button = self.config.get("use_button", [710, 573])

            for _ in range(3):
                if not self.detection_running or self.reconnecting_state or self.auto_pop_state or self.on_auto_merchant_state or self.current_biome == "GLITCHED": return
                self.activate_roblox_window()
                time.sleep(0.3)

            #  inventory menu
            self.Global_MouseClick(inventory_menu[0], inventory_menu[1])
            time.sleep(0.24 + inventory_click_delay)

            # items tab
            self.Global_MouseClick(items_tab[0], items_tab[1])
            time.sleep(0.24 + inventory_click_delay)
            if not self.detection_running or self.reconnecting_state or self.auto_pop_state or self.on_auto_merchant_state or self.current_biome == "GLITCHED": return
            # search bar
            self.Global_MouseClick(search_bar[0], search_bar[1], click=2)
            time.sleep(0.27 + inventory_click_delay)
            if not self.detection_running or self.reconnecting_state or self.auto_pop_state or self.on_auto_merchant_state or self.current_biome == "GLITCHED": return
            # teleport item
            autoit.send("teleport")
            time.sleep(0.2 + inventory_click_delay)
            self.Global_MouseClick(first_item_slot[0], first_item_slot[1])
            time.sleep(0.25 + inventory_click_delay)
            if not self.detection_running or self.reconnecting_state or self.auto_pop_state or self.on_auto_merchant_state or self.current_biome == "GLITCHED": return
            # amount box
            self.Global_MouseClick(amount_box[0], amount_box[1])
            time.sleep(0.17 + inventory_click_delay)
            if not self.detection_running or self.reconnecting_state or self.auto_pop_state or self.on_auto_merchant_state or self.current_biome == "GLITCHED": return
            autoit.send("^{a}")
            time.sleep(0.15 + inventory_click_delay)
            autoit.send("{BACKSPACE}")
            time.sleep(0.15 + inventory_click_delay)
            autoit.send('1')
            time.sleep(0.14 + inventory_click_delay)
            if not self.detection_running or self.reconnecting_state or self.auto_pop_state or self.on_auto_merchant_state or self.current_biome == "GLITCHED": return
            # use
            self.Global_MouseClick(use_button[0], use_button[1])
            time.sleep(0.23 + inventory_click_delay)

            # inv
            self.Global_MouseClick(inventory_menu[0], inventory_menu[1])
            time.sleep(0.23 + inventory_click_delay)
            self.Merchant_Handler()
            
            if not self.detection_running or self.reconnecting_state or self.auto_pop_state or self.on_auto_merchant_state or self.current_biome == "GLITCHED": return
            
            time.sleep(0.33 + inventory_click_delay)
            self.Global_MouseClick(inventory_menu[0], inventory_menu[1])
            time.sleep(0.33 + inventory_click_delay)
            self.Global_MouseClick(inventory_menu[0], inventory_menu[1])

        except Exception as e:
            self.error_logging(e, "Error in use_merchant_teleporter function.")
                
    def Merchant_Handler(self):
        try:
            if not self.detection_running or self.reconnecting_state or self.auto_pop_state or self.current_biome == "GLITCHED": return
            
            self.on_auto_merchant_state = True
            merchant_name_ocr_pos = self.config["merchant_name_ocr_pos"]
            merchant_open_button = self.config["merchant_open_button"]
            first_item_slot_pos = self.config["first_item_slot_pos"]
            item_name_ocr_pos = self.config["item_name_ocr_pos"]
            merchant_dialogue_box = self.config["merchant_dialogue_box"]
            merchant_extra_slot = int(self.config.get("merchant_extra_slot", "0"))
            
            merchant_name = ""
            ocrMisdetect_Key = {
                "heovenly potion": "heavenly potion",
                "heovenly potion!": "heavenly potion",
                "heavenly potion": "heavenly potion",
                "heavenly potion!": "heavenly potion",
                "rune of goloxy": "rune of galaxy",
                "rune of roinstorm": "rune of rainstorm",
                "stronge potion": "strange potion",
                "stello's condle": "stella's candle",
                "merchont trocker": "merchant tracker",
                "rondom potion sock": "random potion sack",
                "geor a": "gear a",
                "geor b": "gear b"
            }
            
            if not hasattr(self, 'last_merchant_interaction'):
                self.last_merchant_interaction = 0
            
            if not hasattr(self, 'last_merchant_sent'):
                self.last_merchant_sent = {}

            merchant_cooldown_time = 300
            current_time = time.time()
            
            if current_time - self.last_merchant_interaction < merchant_cooldown_time: return
            
            for _ in range(5):
                if not self.detection_running or self.reconnecting_state or self.auto_pop_state or self.current_biome == "GLITCHED": return
                autoit.send("e")
                time.sleep(0.35)
                
            time.sleep(0.45)
                
            self.autoit_hold_left_click(merchant_dialogue_box[0], merchant_dialogue_box[1], holdTime=4250)
                
            for _ in range(6):
                if not self.detection_running or self.reconnecting_state or self.auto_pop_state or self.current_biome == "GLITCHED": return
                
                x, y, w, h = merchant_name_ocr_pos
                screenshot = pyautogui.screenshot(region=(x, y, w, h))
                merchant_name_text = pytesseract.image_to_string(screenshot, config='--psm 6').strip()
                if any(name in merchant_name_text for name in ["Mari", "Mori", "Marl", "Mar1", "MarI", "Mar!", "Maori"]):
                    merchant_name = "Mari"
                    print("[Merchant Detection]: Mari name found!")
                    break
                elif "Jester" in merchant_name_text:
                    merchant_name = "Jester"
                    print("[Merchant Detection]: Jester name found!")
                    break

                time.sleep(0.12)

            if merchant_name:
                last_sent_time = self.last_merchant_sent.get(merchant_name, 0)
                if current_time - last_sent_time < merchant_cooldown_time:
                    print(f"Merchant {merchant_name} already sent recently lol")
                    return

                print(f"Opening merchant interface for {merchant_name}")

                x, y = merchant_open_button
                autoit.mouse_click("left", x, y, 3)
                time.sleep(0.73)

                screenshot_dir = os.path.join(os.getcwd(), "images")
                os.makedirs(screenshot_dir, exist_ok=True)

                item_screenshot = pyautogui.screenshot()
                screenshot_path = os.path.join(screenshot_dir, "merchant_screenshot.png")
                item_screenshot.save(screenshot_path)

                self.send_merchant_webhook(merchant_name, screenshot_path)
                self.last_merchant_sent[merchant_name] = current_time

                auto_buy_items = self.config.get(f"{merchant_name}_Items", {})
                if not auto_buy_items: return
                purchased_items = {}
                
                total_slots = 5 + merchant_extra_slot
                for slot_index in range(total_slots):
                    if not self.detection_running or self.reconnecting_state or self.auto_pop_state or self.current_biome == "GLITCHED": return

                    x, y = first_item_slot_pos
                    slot_x = x + (slot_index * 193)
                    autoit.mouse_click("left", slot_x, y, 2)
                    time.sleep(0.15)

                    # OCR - item name
                    x, y, w, h = item_name_ocr_pos
                    screenshot = pyautogui.screenshot(region=(x, y, w, h))
                    item_text = pytesseract.image_to_string(screenshot, config='--psm 6').strip().lower()

                    self.append_log(f"[Merchant Detection - {merchant_name}] Detected item text: {item_text}")

                    corrected_item_name = item_text.split('|')[0].strip()
                    for misdetect, correct in ocrMisdetect_Key.items():
                        if misdetect in corrected_item_name:
                            corrected_item_name = correct
                            print(f"Corrected OCR misdetection: '{item_text}' -> '{correct}'")
                            break

                    print(f"Detected item text: {item_text} | Corrected: {corrected_item_name}")

                    for item_name, (enabled, quantity, rebuy) in auto_buy_items.items():
                        if enabled and corrected_item_name == item_name.lower():
                            purchased_count = purchased_items.get(item_name, 0)

                            if rebuy or purchased_count == 0:
                                self.append_log(f"[Merchant Detection - {merchant_name}] - Item {item_name} found. Proceeding to buy {quantity}")

                                purchase_amount_button = self.config["purchase_amount_button"]
                                purchase_button = self.config["purchase_button"]

                                autoit.mouse_click("left", *purchase_amount_button)
                                autoit.send(str(quantity))
                                time.sleep(0.23)

                                autoit.mouse_click("left", *purchase_button)
                                time.sleep(0.35)
                                self.autoit_hold_left_click(merchant_dialogue_box[0], merchant_dialogue_box[1], holdTime=3350)

                                purchased_items[item_name] = purchased_count + 1
                                break

                # Update last merchant autobuy
                self.last_merchant_interaction = current_time
            else:
                print("No merchant detected.")
                
        except Exception as e:
            self.error_logging(e, "Error in Merchant_Handler function \n (If it say valueError: not enough values to unpack (expect 3 got 2) then open both mari and jester setting and click save selection again!)")
        finally: 
            self.on_auto_merchant_state = False
            
        
    def send_webhook(self, biome, message_type, event_type):
        webhook_url = self.config.get("webhook_url")
        if not webhook_url:
            print("Webhook URL is missing/not included in the config.json")
            return

        if message_type == "None": return

        biome_info = self.biome_data[biome]
        biome_color = int(biome_info["color"], 16)
        timestamp = time.strftime("[%H:%M:%S]") 
        icon_url = "https://i.postimg.cc/rsXpGncL/Noteab-Biome-Tracker.png"
        
        content = ""
        
        if event_type == "start" and biome in ["GLITCHED", "DREAMSPACE"]:
            content = "@everyone"

        title = f"{timestamp} Biome Started - {biome}" if event_type == "start" else f"{timestamp} Biome Ended - {biome}"

        fields = []
        if event_type == "start":
            private_server_link = self.config.get("private_server_link")
            if private_server_link == "":
                private_server_link = "No link provided (who let bro cook 💀)"
                
            fields.append({
                "name": "Private Server Link",
                "value": private_server_link,
                "inline": False
            })

        embed = {
            "title": title,
            "color": biome_color,
            "footer": {
                "text": "Noteab's Biome Detection (v1.5.4-patch2.8.4)",
                "icon_url": icon_url
            },
            "fields": fields
        }

        if event_type == "start":
            embed["thumbnail"] = {"url": biome_info["thumbnail_url"]}

        payload = {
            "content": content,
            "embeds": [embed]
        }

        try:
            response = requests.post(webhook_url, json=payload)
            response.raise_for_status()
            print(f"[Line 1744] Sent {message_type} for {biome} - {event_type}")
            
        except requests.exceptions.RequestException as e:
            print(f"Failed to send webhook: {e}")
    
    def send_merchant_webhook(self, merchant_name, screenshot_path):
        webhook_url = self.config.get("webhook_url")
        
        if not webhook_url:
            print("Webhook URL is missing/not included in the config.json")
            return

        merchant_thumbnails = {
            "Mari": "https://static.wikia.nocookie.net/sol-rng/images/d/df/Mari_cropped.png/revision/latest?cb=20241015111527",
            "Jester": "https://static.wikia.nocookie.net/sol-rng/images/d/db/Headshot_of_Jester.png/revision/latest?cb=20240630142936"
        }


        if merchant_name == "Mari":
            ping_id = self.config.get("mari_user_id", "")
        elif merchant_name == "Jester":
            ping_id = self.config.get("jester_user_id", "")
        else:
            ping_id = ""

        content = f"<@{ping_id}>" if ping_id else ""
        ps_link = self.config.get("private_server_link", "")

        embeds = [{
            "title": f"{merchant_name} Detected!",
            "description": f"{merchant_name} has been detected on your screen.\n**Item screenshot**\n \nMerchant PS Link: {ps_link}",
            "color": 11753 if merchant_name == "Mari" else 8595632,
            "image": {"url": f"attachment://{os.path.basename(screenshot_path)}"},
            "thumbnail": {"url": merchant_thumbnails.get(merchant_name, "")}
        }]

        with open(screenshot_path, "rb") as image_file:
            files = {"file": (os.path.basename(screenshot_path), image_file, "image/png")}
            response = requests.post(
                webhook_url,
                data={
                    "payload_json": json.dumps({
                        "content": content,
                        "embeds": embeds
                    })
                },
                files=files
            )
            response.raise_for_status()
            print(f"Webhook sent successfully for {merchant_name}: {response.status_code}")
            
    def send_aura_webhook(self, aura_name, rarity, biome_message):
        webhook_url = self.config.get("webhook_url")
        if not webhook_url:
            print("Webhook URL is missing/not included in the config.json")
            return
        
        icon_url = "https://i.postimg.cc/rsXpGncL/Noteab-Biome-Tracker.png"
        ping_minimum = int(self.config.get("ping_minimum", "100000"))
        color = 0xffffff
        
        # sigma rarity
        if rarity is not None:
            rarity_value = int(rarity.replace(',', ''))
            if 99000 <= rarity_value < 1000000:
                color = 0x3dd3e0  # 99k - 999k
            elif 1000000 <= rarity_value < 10000000:
                color = 0xff73ec  # 1m - 9m
            elif 10000000 <= rarity_value < 99000000:
                color = 0x2d30f7  # 10m - 99m
            elif 99000000 <= rarity_value < 1000000000:
                color = 0xed2f59  # 99m - 999m
            else:
                color = 0xff9447 #orange: hi, just pretend I didn't exist

            description = f"## {time.strftime('[%H:%M:%S]')} \n ## > Aura found/last equipped: {aura_name} | 1 in {rarity} {biome_message}"
        else:
            description = f"## {time.strftime('[%H:%M:%S]')} \n ## > Aura found/last equipped: {aura_name}"

        payload = {
            "embeds": [
                {
                    "title": "⭐ Aura Detection ⭐",
                    "description": description,
                    "color": color,
                    "footer": {
                        "text": "Noteab's Macro (v1.5.4-patch2.8.4)",
                        "icon_url": icon_url
                    }
                }
            ]
        }

        if rarity is not None and rarity_value >= ping_minimum:
            aura_user_id = self.config.get("aura_user_id", "")
            if aura_user_id:
                payload["content"] = f"<@{aura_user_id}>"
            
        try:
            response = requests.post(webhook_url, json=payload)
            response.raise_for_status()
            print(f"Aura webhook sent for {aura_name}")
        except requests.exceptions.RequestException as e:
            print(f"Failed to send aura webhook: {e}")
                   
    def send_webhook_status(self, status, color=None):
        try:
            webhook_url = self.config.get("webhook_url")
            if not webhook_url:
                print("Webhook URL is missing/not included in the config.json")
                return
            
            default_color = 3066993 if "started" in status.lower() else 15158332
            embed_color = color if color is not None else default_color
            icon_url = "https://i.postimg.cc/rsXpGncL/Noteab-Biome-Tracker.png"

            embeds = [{
                "title": "== 🌟 Macro Status 🌟 ==",
                "description": f"## [{time.strftime('%H:%M:%S')}] \n ## > {status}",
                "color": embed_color,
                "footer": {
                    "text": "Noteab's Macro (v1.5.4-patch2.8.4)",
                    "icon_url": icon_url
                }
            }]
            response = requests.post(
                webhook_url,
                data={"payload_json": json.dumps({"embeds": embeds})}
            )
            response.raise_for_status()

        except requests.exceptions.RequestException as e:
            print(f"Failed to send webhook: {e}")
        except Exception as e:
            print(f"An error occurred in webhook_status: {e}")
        
    def activate_roblox_window(self):
        windows = gw.getAllTitles()
        roblox_window = None
        
        for window in windows:
            if "Roblox" in window:
                roblox_window = gw.getWindowsWithTitle(window)[0]
                break

        if roblox_window:
            try:
                roblox_window.activate()
            except Exception as e:
                print(f"Failed to activate window: {e}")
        else:
            print("Roblox window not found.")
    
    def autoit_hold_left_click(self, posX, posY, holdTime=3300):
        autoit.mouse_click("left", posX, posY, 5, speed=2)
        time.sleep(0.13)
        autoit.mouse_click("left", posX, posY, 3, speed=2)
        autoit.mouse_down("left")
        time.sleep(holdTime / 1000)
        autoit.mouse_up("left")
        
    def get_scaled_coordinates(self, original_x, original_y):
        original_width = 1920 
        original_height = 1080
        current_width, current_height = pyautogui.size()
        
        x_scale = current_width / original_width
        y_scale = current_height / original_height
        return int(original_x * x_scale), int(original_y * y_scale)
    
    def trigger_aura_record(self):
        def aura_record():
            try:
                #print("hi me running aura record")
                keybind = self.aura_record_keybind_var.get()
                keys = [key.strip() for key in keybind.split('+')]
                time.sleep(10)
                pyautogui.hotkey(*keys)
            except Exception as e:
                self.error_logging(e, "Error in trigger_aura_record")
        
        threading.Thread(target=aura_record).start()
    
    def trigger_biome_record(self):
        def record():
            try:
                #print("hi me running biome record")
                keybind = self.rarest_biome_keybind_var.get()
                keys = [key.strip() for key in keybind.split('+')]
                time.sleep(45)
                pyautogui.hotkey(*keys)
            except Exception as e:
                self.error_logging(e, "Error in trigger_biome_record")

        threading.Thread(target=record).start()
    
    # this dock was here
    
    def auto_pop_buffs(self):
        try:
            inventory_click_delay = int(self.config.get("inventory_click_delay", "0")) / 1000.0
            
            # Priority list for potions
            buffs_to_use = []
            priority_order = [
                "Xyz Potion",
                "Warp Potion",
                "Heavenly Potion II",
                "Oblivion Potion"
            ]

            # Priority potions
            for buff in priority_order:
                if buff in self.config.get("auto_buff_glitched", {}) and self.config["auto_buff_glitched"][buff][0]:  # Check if enabled
                    amount = self.config["auto_buff_glitched"][buff][1]
                    buffs_to_use.append((buff, amount))

            # Remaining potions that are enabled but not in the priority order
            for buff, (enabled, amount) in self.config.get("auto_buff_glitched", {}).items():
                if enabled and buff not in priority_order: 
                    buffs_to_use.append((buff, amount))

            warp_enabled = any(buff == "Warp Potion" for buff, _ in buffs_to_use)

            for buff, amount in buffs_to_use:
                if not self.detection_running or self.reconnecting_state: return
                print(f"Using {buff} x{amount}")
                
                self.send_webhook_status(f"Using x{amount} {buff} in GLITCHED", color=0x34ebab)
                
                additional_wait_time = 0
                if buff == "Heavenly Potion II" or buff == "Oblivion Potion":
                    additional_wait_time = 0.85 * amount  # 0.85 seconds per potion
                    if warp_enabled:
                        additional_wait_time *= 0.12  # warp wait delay

                for _ in range(4):
                    if not self.detection_running or self.reconnecting_state: return
                    self.activate_roblox_window()
                    time.sleep(0.35)
                    
                time.sleep(0.37) # wait atm before other macro actions like teleporter, biome random, strange controller stopped completely

                # Inventory menu
                inventory_menu = self.config.get("inventory_menu", [36, 535])
                self.Global_MouseClick(inventory_menu[0], inventory_menu[1])
                time.sleep(0.22 + inventory_click_delay)

                # Buff item
                search_bar = self.config.get("search_bar", [855, 358]) 
                self.Global_MouseClick(search_bar[0], search_bar[1], click=2)
                time.sleep(0.23 + inventory_click_delay)

                if not self.detection_running or self.reconnecting_state: return
                
                # name
                keyboard.write(buff.lower())
                time.sleep(0.22 + inventory_click_delay)

                # first buff item slot
                first_item_slot = self.config.get("first_item_slot", [839, 434])
                self.Global_MouseClick(first_item_slot[0], first_item_slot[1])
                time.sleep(0.22 + inventory_click_delay)

                # amountaaaa
                amount_box = self.config.get("amount_box", [594, 570])
                self.Global_MouseClick(amount_box[0], amount_box[1])
                time.sleep(0.22 + inventory_click_delay)
                
                if not self.detection_running or self.reconnecting_state: return
                
                # use cro
                autoit.send("^{a}")
                time.sleep(0.285 + inventory_click_delay)
                autoit.send("{BACKSPACE}")
                time.sleep(0.285 + inventory_click_delay)
                autoit.send(str(amount))
                time.sleep(0.285 + inventory_click_delay)

                # use??!
                use_button = self.config.get("use_button", [710, 573])
                self.Global_MouseClick(use_button[0], use_button[1])
                time.sleep(0.3 + inventory_click_delay)

                # close ts pmo icl :pray:
                self.Global_MouseClick(inventory_menu[0], inventory_menu[1])
                time.sleep(0.32 + inventory_click_delay)

                # additional wait time
                if additional_wait_time > 0: time.sleep(additional_wait_time)

        except Exception as e:
            self.error_logging(e, "Error in auto_pop_buffs function")

try:
    biome_presence = BiomePresence()
except KeyboardInterrupt:
    print("Exited (Keyboard Interrupted)")
finally:
    keyboard.unhook_all()
