#!/usr/bin/env python3
"""
Test simple du lecteur radio avec reprise instantanée en direct
"""

try:
    import tkinter as tk
    from tkinter import ttk, messagebox
    TKINTER_AVAILABLE = True
except ImportError:
    TKINTER_AVAILABLE = False
    print("⚠️ Tkinter non disponible, utilisation de la version console")

import time
from radio_metadata_fetcher_fixed_clean import RadioFetcher

class SimpleRadioPlayer:
    def __init__(self):
        self.fetcher = RadioFetcher()
        self.current_station = None
        self.current_url = None
        self.is_playing = False
        
        self.stations = [
            ("Chante France-80s", "https://chantefrance80s.ice.infomaniak.ch/chantefrance80s-128.mp3"),
            ("RTL", "http://streaming.radio.rtl.fr/rtl-1-44-128"),
            ("Flash 80 Radio", "https://manager7.streamradio.fr:1985/stream"),
        ]
        
        if TKINTER_AVAILABLE:
            self.setup_gui()
        else:
            self.setup_console()
    
    def setup_gui(self):
        self.root = tk.Tk()
        self.root.title("🎵 Lecteur Radio - Reprise Instantanée")
        self.root.geometry("600x400")
        
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Titre
        ttk.Label(main_frame, text="🎵 Lecteur Radio", font=("Arial", 16, "bold")).grid(row=0, column=0, columnspan=2, pady=10)
        
        # Sélection de la radio
        ttk.Label(main_frame, text="Radio:").grid(row=1, column=0, sticky=tk.W)
        self.station_var = tk.StringVar()
        self.station_combo = ttk.Combobox(main_frame, textvariable=self.station_var, width=40)
        self.station_combo['values'] = [name for name, _ in self.stations]
        self.station_combo.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=10)
        self.station_combo.bind('<<ComboboxSelected>>', self.on_station_change)
        
        # Boutons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=20)
        
        self.play_button = ttk.Button(button_frame, text="▶️ Play", command=self.toggle_play_pause, width=12)
        self.play_button.grid(row=0, column=0, padx=5)
        
        self.stop_button = ttk.Button(button_frame, text="⏹️ Stop", command=self.stop_radio, width=12)
        self.stop_button.grid(row=0, column=1, padx=5)
        
        # Status
        self.status_label = ttk.Label(main_frame, text="Status: Arrêté", font=("Arial", 12), foreground="red")
        self.status_label.grid(row=3, column=0, columnspan=2, pady=10)
        
        # Métadonnées
        self.artist_label = ttk.Label(main_frame, text="Artiste: --", font=("Arial", 11))
        self.artist_label.grid(row=4, column=0, columnspan=2, sticky=tk.W)
        
        self.title_label = ttk.Label(main_frame, text="Titre: --", font=("Arial", 10))
        self.title_label.grid(row=5, column=0, columnspan=2, sticky=tk.W)
        
        # Info
        info_text = "⚡ Reprise instantanée en direct: Pause → Play = Direct immédiat!"
        ttk.Label(main_frame, text=info_text, font=("Arial", 9), foreground="blue").grid(row=6, column=0, columnspan=2, pady=20)
        
        # Démarrer la mise à jour des métadonnées
        self.update_metadata()
        
        print("🎵 Interface graphique démarrée!")
        print("💡 Test: Play → Pause → Play = Reprise instantanée en direct!")
        
        self.root.mainloop()
    
    def setup_console(self):
        print("🎵 Lecteur Radio Console - Reprise Instantanée en Direct")
        print("=" * 50)
        
        while True:
            print("\nRadios disponibles:")
            for i, (name, _) in enumerate(self.stations, 1):
                print(f"{i}. {name}")
            
            try:
                choice = input("\nChoisissez une radio (1-3) ou 'q' pour quitter: ").strip()
                
                if choice.lower() == 'q':
                    break
                
                choice_idx = int(choice) - 1
                if 0 <= choice_idx < len(self.stations):
                    self.current_station, self.current_url = self.stations[choice_idx]
                    self.console_player()
                else:
                    print("Choix invalide!")
                    
            except (ValueError, KeyboardInterrupt):
                break
    
    def console_player(self):
        print(f"\n🎵 Radio: {self.current_station}")
        print("⚡ Reprise instantanée en direct activée!")
        print("Commandes: 'p' = Play, 's' = Pause, 'x' = Stop, 'h' = Historique, 'q' = Quitter")
        
        while True:
            try:
                cmd = input(f"\n[{self.current_station}]> ").strip().lower()
                
                if cmd == 'p':
                    self.toggle_play_pause()
                elif cmd == 's':
                    self.pause_radio()
                elif cmd == 'x':
                    self.stop_radio()
                    break
                elif cmd == 'h':
                    self.show_history_console()
                elif cmd == 'q':
                    return
                else:
                    print("Commande inconnue!")
                    
            except KeyboardInterrupt:
                print("\n👋 Au revoir!")
                break
    
    def on_station_change(self, event=None):
        station_name = self.station_var.get()
        for name, url in self.stations:
            if name == station_name:
                self.current_station = name
                self.current_url = url
                break
    
    def toggle_play_pause(self):
        if not self.current_station:
            if TKINTER_AVAILABLE:
                messagebox.showwarning("Aucune radio", "Veuillez sélectionner une radio!")
            else:
                print("Veuillez sélectionner une radio!")
            return
        
        if self.is_playing:
            # Pause
            self.is_playing = False
            if TKINTER_AVAILABLE:
                self.play_button.config(text="▶️ Play")
                self.status_label.config(text="Status: En pause", foreground="orange")
            print(f"⏸️  Pause: {self.current_station}")
        else:
            # Play/Reprise en direct
            self.is_playing = True
            if TKINTER_AVAILABLE:
                self.play_button.config(text="⏸️ Pause")
                self.status_label.config(text="Status: En direct 🎵", foreground="green")
            print(f"▶️  {'Reprise en direct' if self.current_station else 'Lecture'}: {self.current_station}")
    
    def pause_radio(self):
        if self.is_playing:
            self.is_playing = False
            if TKINTER_AVAILABLE:
                self.play_button.config(text="▶️ Play")
                self.status_label.config(text="Status: En pause", foreground="orange")
            print(f"⏸️  Pause: {self.current_station}")
    
    def stop_radio(self):
        self.is_playing = False
        if TKINTER_AVAILABLE:
            self.play_button.config(text="▶️ Play")
            self.status_label.config(text="Status: Arrêté", foreground="red")
            self.artist_label.config(text="Artiste: --")
            self.title_label.config(text="Titre: --")
        print(f"⏹️  Stop: {self.current_station}")
    
    def show_history_console(self):
        if not self.current_station:
            print("Aucune radio sélectionnée!")
            return
        
        try:
            history = self.fetcher.get_history(self.current_station, self.current_url, 10)
            if history:
                print(f"\n📋 Historique - {self.current_station}:")
                print("=" * 40)
                for i, track in enumerate(history, 1):
                    print(f"{i}. {track['artist']} - {track['title']}")
                    if track.get('timestamp'):
                        print(f"   Heure: {track['timestamp']}")
            else:
                print("Aucun historique disponible")
        except Exception as e:
            print(f"Erreur: {e}")
    
    def update_metadata(self):
        if not TKINTER_AVAILABLE:
            return
            
        def update():
            while True:
                try:
                    if self.is_playing and self.current_station and self.current_url:
                        metadata = self.fetcher.get_metadata_with_history(self.current_station, self.current_url)
                        
                        if metadata:
                            self.artist_label.config(text=f"Artiste: {metadata.artist}")
                            self.title_label.config(text=f"Titre: {metadata.title}")
                    
                    time.sleep(5)
                except Exception as e:
                    print(f"Erreur métadonnées: {e}")
                    time.sleep(10)
        
        import threading
        thread = threading.Thread(target=update, daemon=True)
        thread.start()

if __name__ == "__main__":
    print("🎵 Démarrage du Lecteur Radio avec Reprise Instantanée en Direct")
    print("=" * 60)
    print("⚡ CARACTÉRISTIQUE PRINCIPALE:")
    print("   Pause → Play = Reprise INSTANTANÉE en direct!")
    print("   Pas de reprise là où vous vous êtes arrêté")
    print("=" * 60)
    
    player = SimpleRadioPlayer()
