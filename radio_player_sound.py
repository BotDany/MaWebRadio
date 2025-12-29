#!/usr/bin/env python3
"""
Lecteur Radio Complet avec SON et Reprise Instantanée en Direct
Lecture audio réelle + métadonnées + reprise instantanée en direct
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import requests
import io
import sys
import os
from radio_metadata_fetcher_fixed_clean import RadioFetcher, add_to_history_cache

# Essayer d'importer pygame pour le son
try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    print("⚠️ pygame non installé. Installation: pip install pygame")

class RadioPlayerWithSound:
    def __init__(self, root):
        self.root = root
        self.root.title("🎵 Lecteur Radio avec SON - Reprise Instantanée en Direct")
        self.root.geometry("800x700")
        
        # Variables
        self.current_station = None
        self.current_url = None
        self.is_playing = False
        self.fetcher = RadioFetcher()
        self.last_metadata = None
        
        # Audio
        self.audio_thread = None
        self.stop_audio = False
        
        # Initialiser pygame si disponible
        if PYGAME_AVAILABLE:
            try:
                pygame.mixer.init()
                pygame.mixer.music.set_volume(0.7)
                print("🔊 Audio initialisé avec pygame")
            except Exception as e:
                print(f"⚠️ Erreur initialisation audio: {e}")
                PYGAME_AVAILABLE = False
        
        # Liste des radios
        self.stations = [
            ("Chante France-80s", "https://chantefrance80s.ice.infomaniak.ch/chantefrance80s-128.mp3"),
            ("RTL", "http://streaming.radio.rtl.fr/rtl-1-44-128"),
            ("100% Radio 80", "http://100radio-80.ice.infomaniak.ch/100radio-80-128.mp3"),
            ("Nostalgie-Les 80 Plus Grand Tubes", "https://streaming.nrjaudio.fm/ouwg8usk6j4d"),
            ("Flash 80 Radio", "https://manager7.streamradio.fr:1985/stream"),
            ("Radio Comercial", "https://stream-icy.bauermedia.pt/comercial.mp3"),
            ("Bide Et Musique", "https://relay1.bide-et-musique.com:9300/bm.mp3"),
            ("Mega Hits", "https://playerservices.streamtheworld.com/api/livestream-redirect/MEGA_HITSAAC_SC"),
            ("Superloustic", "https://radio6.pro-fhi.net/live/SUPERLOUSTIC"),
            ("Radio Gérard", "https://radiosurle.net:8765/radiogerard"),
            ("Supernana", "https://radiosurle.net:8765/showsupernana"),
            ("Génération Dorothée", "https://stream.votreradiosurlenet.eu/generationdorothee.mp3"),
            ("Made In 80", "https://listen.radioking.com/radio/260719/stream/305509"),
            ("Top 80 Radio", "https://securestreams6.autopo.st:2321/"),
            ("Générikds", "https://www.radioking.com/play/generikids"),
            ("Chansons Oubliées Où Presque", "https://manager7.streamradio.fr:2850/stream"),
            ("Nostalgie-Les Tubes 80 N1", "https://streaming.nrjaudio.fm/ouo6im7nfibk"),
        ]
        
        self.setup_ui()
        self.update_metadata_thread()
        
    def setup_ui(self):
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configuration du poids pour le redimensionnement
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Titre
        title_label = ttk.Label(main_frame, text="🎵 Lecteur Radio avec SON", font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 10))
        
        # Status audio
        audio_status = "🔊 Audio OK" if PYGAME_AVAILABLE else "🔇 Audio non disponible (pip install pygame)"
        ttk.Label(main_frame, text=audio_status, font=("Arial", 10), foreground="green" if PYGAME_AVAILABLE else "red").grid(row=1, column=0, columnspan=3, pady=(0, 10))
        
        # Sélection de la radio
        ttk.Label(main_frame, text="Radio:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.station_var = tk.StringVar()
        self.station_combo = ttk.Combobox(main_frame, textvariable=self.station_var, width=40)
        self.station_combo['values'] = [name for name, _ in self.stations]
        self.station_combo.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        self.station_combo.bind('<<ComboboxSelected>>', self.on_station_change)
        
        # Volume
        ttk.Label(main_frame, text="Volume:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.volume_var = tk.DoubleVar(value=70)
        self.volume_scale = ttk.Scale(main_frame, from_=0, to=100, orient=tk.HORIZONTAL, variable=self.volume_var, command=self.update_volume)
        self.volume_scale.grid(row=3, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        self.volume_label = ttk.Label(main_frame, text="70%")
        self.volume_label.grid(row=3, column=2, pady=5)
        
        # Boutons de contrôle
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=3, pady=20)
        
        self.play_button = ttk.Button(button_frame, text="▶️ Play", command=self.toggle_play_pause, width=12)
        self.play_button.grid(row=0, column=0, padx=5)
        
        self.stop_button = ttk.Button(button_frame, text="⏹️ Stop", command=self.stop_radio, width=12)
        self.stop_button.grid(row=0, column=1, padx=5)
        
        self.history_button = ttk.Button(button_frame, text="📋 Historique", command=self.show_history, width=12)
        self.history_button.grid(row=0, column=2, padx=5)
        
        # Métadonnées actuelles
        metadata_frame = ttk.LabelFrame(main_frame, text="En direct", padding="10")
        metadata_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        metadata_frame.columnconfigure(0, weight=1)
        
        self.artist_label = ttk.Label(metadata_frame, text="Artiste: --", font=("Arial", 12, "bold"))
        self.artist_label.grid(row=0, column=0, sticky=tk.W, pady=2)
        
        self.title_label = ttk.Label(metadata_frame, text="Titre: --", font=("Arial", 11))
        self.title_label.grid(row=1, column=0, sticky=tk.W, pady=2)
        
        self.status_label = ttk.Label(metadata_frame, text="Status: Arrêté", font=("Arial", 10), foreground="red")
        self.status_label.grid(row=2, column=0, sticky=tk.W, pady=5)
        
        # URL du flux
        url_frame = ttk.LabelFrame(main_frame, text="URL du flux", padding="10")
        url_frame.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        url_frame.columnconfigure(0, weight=1)
        
        self.url_label = ttk.Label(url_frame, text="Aucune radio sélectionnée", font=("Courier", 9))
        self.url_label.grid(row=0, column=0, sticky=tk.W)
        
        # Instructions
        info_frame = ttk.LabelFrame(main_frame, text="⚡ Reprise Instantanée en Direct", padding="10")
        info_frame.grid(row=7, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        info_frame.columnconfigure(0, weight=1)
        
        info_text = """💡 Quand vous mettez en pause (⏸️) et que vous appuyez sur Play (▶️):
   → La radio reprend INSTANTANÉMENT en DIRECT avec le SON 🔊
   → Pas de reprise là où vous vous êtes arrêté
   → Toujours en temps réel comme une vraie radio !"""
        
        ttk.Label(info_frame, text=info_text, font=("Arial", 9)).grid(row=0, column=0, sticky=tk.W)
        
        # Console de messages
        console_frame = ttk.LabelFrame(main_frame, text="Console", padding="10")
        console_frame.grid(row=8, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        console_frame.columnconfigure(0, weight=1)
        console_frame.rowconfigure(0, weight=1)
        
        self.console_text = tk.Text(console_frame, height=8, wrap=tk.WORD, font=("Courier", 9))
        console_scrollbar = ttk.Scrollbar(console_frame, orient=tk.VERTICAL, command=self.console_text.yview)
        self.console_text.configure(yscrollcommand=console_scrollbar.set)
        
        self.console_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        console_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        console_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(8, weight=1)
        
        self.log_message("🎵 Lecteur Radio avec SON prêt!")
        
    def log_message(self, message):
        """Ajoute un message dans la console"""
        timestamp = time.strftime("%H:%M:%S")
        self.console_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.console_text.see(tk.END)
        self.root.update_idletasks()
    
    def on_station_change(self, event=None):
        station_name = self.station_var.get()
        for name, url in self.stations:
            if name == station_name:
                self.current_station = name
                self.current_url = url
                self.url_label.config(text=url)
                self.log_message(f"📻 Radio sélectionnée: {name}")
                break
    
    def update_volume(self, value):
        volume = int(float(value))
        self.volume_label.config(text=f"{volume}%")
        if PYGAME_AVAILABLE:
            pygame.mixer.music.set_volume(volume / 100.0)
    
    def toggle_play_pause(self):
        if not self.current_station:
            messagebox.showwarning("Aucune radio", "Veuillez sélectionner une radio d'abord!")
            return
            
        if self.is_playing:
            # Mettre en pause
            self.is_playing = False
            self.stop_audio = True
            self.play_button.config(text="▶️ Play")
            self.status_label.config(text="Status: En pause", foreground="orange")
            self.log_message(f"⏸️  Pause: {self.current_station}")
            
            # Arrêter le son
            if PYGAME_AVAILABLE:
                pygame.mixer.music.stop()
        else:
            # Reprendre en direct
            self.is_playing = True
            self.stop_audio = False
            self.play_button.config(text="⏸️ Pause")
            self.status_label.config(text="Status: En direct 🎵", foreground="green")
            self.log_message(f"▶️  Reprise en direct: {self.current_station}")
            
            # Démarrer le son
            if PYGAME_AVAILABLE and self.current_url:
                self.start_audio_stream()
    
    def start_audio_stream(self):
        """Démarre le streaming audio dans un thread séparé"""
        if not PYGAME_AVAILABLE:
            self.log_message("❌ Audio non disponible - installez pygame")
            return
        
        def audio_worker():
            try:
                self.log_message(f"🔊 Connexion audio à: {self.current_url}")
                
                # Télécharger le flux audio
                response = requests.get(self.current_url, stream=True, timeout=10)
                response.raise_for_status()
                
                # Créer un fichier temporaire pour le flux
                audio_data = io.BytesIO()
                
                for chunk in response.iter_content(chunk_size=1024):
                    if self.stop_audio:
                        break
                    
                    if chunk:
                        audio_data.write(chunk)
                        
                        # Jouer quand on a assez de données
                        if audio_data.tell() > 8192:  # 8KB minimum
                            audio_data.seek(0)
                            try:
                                pygame.mixer.music.load(audio_data)
                                pygame.mixer.music.play()
                                time.sleep(0.1)  # Petite pause pour éviter la surcharge
                            except Exception as e:
                                # Réessier avec moins de données
                                audio_data.seek(0)
                                audio_data.truncate(8192)
                                continue
                            
                            # Vider le buffer pour éviter qu'il ne devienne trop grand
                            audio_data.seek(0)
                            audio_data.truncate(0)
                
                self.log_message("🔊 Flux audio terminé")
                
            except Exception as e:
                self.log_message(f"❌ Erreur audio: {e}")
                self.is_playing = False
                self.play_button.config(text="▶️ Play")
                self.status_label.config(text="Status: Erreur audio", foreground="red")
        
        # Démarrer le thread audio
        self.audio_thread = threading.Thread(target=audio_worker, daemon=True)
        self.audio_thread.start()
    
    def stop_radio(self):
        self.is_playing = False
        self.stop_audio = True
        self.play_button.config(text="▶️ Play")
        self.status_label.config(text="Status: Arrêté", foreground="red")
        self.artist_label.config(text="Artiste: --")
        self.title_label.config(text="Titre: --")
        
        # Arrêter le son
        if PYGAME_AVAILABLE:
            pygame.mixer.music.stop()
        
        self.log_message(f"⏹️  Stop: {self.current_station}")
    
    def update_metadata_thread(self):
        """Thread qui met à jour les métadonnées en continu"""
        def update():
            while True:
                try:
                    if self.is_playing and self.current_station and self.current_url:
                        # Récupérer les métadonnées
                        metadata = self.fetcher.get_metadata_with_history(self.current_station, self.current_url)
                        
                        if metadata:
                            # Mettre à jour l'interface
                            self.artist_label.config(text=f"Artiste: {metadata.artist}")
                            self.title_label.config(text=f"Titre: {metadata.title}")
                            
                            # Afficher dans la console
                            if self.last_metadata != (metadata.artist, metadata.title):
                                self.log_message(f"🎵 {metadata.artist} - {metadata.title}")
                                self.last_metadata = (metadata.artist, metadata.title)
                    
                    time.sleep(5)  # Vérifier toutes les 5 secondes
                    
                except Exception as e:
                    self.log_message(f"❌ Erreur métadonnées: {e}")
                    time.sleep(10)
        
        # Démarrer le thread
        thread = threading.Thread(target=update, daemon=True)
        thread.start()
    
    def show_history(self):
        """Afficher l'historique de la radio actuelle"""
        if not self.current_station:
            messagebox.showwarning("Aucune radio", "Veuillez sélectionner une radio d'abord!")
            return
        
        try:
            history = self.fetcher.get_history(self.current_station, self.current_url, 20)
            
            if not history:
                messagebox.showinfo("Historique", f"Aucun historique disponible pour {self.current_station}")
                return
            
            # Créer une fenêtre pour l'historique
            history_window = tk.Toplevel(self.root)
            history_window.title(f"📋 Historique - {self.current_station}")
            history_window.geometry("600x400")
            
            # Frame pour l'historique
            frame = ttk.Frame(history_window, padding="10")
            frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
            history_window.columnconfigure(0, weight=1)
            history_window.rowconfigure(0, weight=1)
            
            # Text widget avec scrollbar
            text_widget = tk.Text(frame, wrap=tk.WORD, width=70, height=20)
            scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=text_widget.yview)
            text_widget.configure(yscrollcommand=scrollbar.set)
            
            text_widget.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
            scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
            
            frame.columnconfigure(0, weight=1)
            frame.rowconfigure(0, weight=1)
            
            # Ajouter l'historique
            text_widget.insert(tk.END, f"📋 Historique des 20 dernières musiques sur {self.current_station}\n")
            text_widget.insert(tk.END, "=" * 60 + "\n\n")
            
            for i, track in enumerate(history, 1):
                text_widget.insert(tk.END, f"{i:2d}. {track['artist']} - {track['title']}\n")
                if track.get('timestamp'):
                    text_widget.insert(tk.END, f"    Heure: {track['timestamp']}\n")
                if track.get('cover_url'):
                    text_widget.insert(tk.END, f"    Pochette: {track['cover_url']}\n")
                text_widget.insert(tk.END, "\n")
            
            text_widget.config(state=tk.DISABLED)
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de charger l'historique: {e}")

def main():
    root = tk.Tk()
    app = RadioPlayerWithSound(root)
    root.mainloop()

if __name__ == "__main__":
    print("🎵 Démarrage du Lecteur Radio avec SON")
    print("=" * 50)
    print("⚡ CARACTÉRISTIQUE PRINCIPALE:")
    print("   Pause → Play = Reprise INSTANTANÉE en direct avec SON!")
    print("=" * 50)
    
    if not PYGAME_AVAILABLE:
        print("\n⚠️ POUR LE SON: pip install pygame")
        print("Le lecteur fonctionnera sans son, mais l'audio est recommandé")
    
    main()
