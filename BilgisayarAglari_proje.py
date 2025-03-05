#!/usr/bin/env python3

"""
KAA İÇİN HAVA TAHMİNİNE DAYALI, BULANIK MANTIK TABANLI,
ENERJİ VERİMLİ SENKRONİZASYON PROTOKOLÜ

Bu proje, kablosuz algılayıcı ağların simülasyonunu gerçekleştirmektedir.
"""

import numpy as np
import skfuzzy as fuzz
import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd
from scipy import stats
import requests
import tkinter as tk
from tkinter import ttk
from datetime import datetime
import json
import folium
import os
import webview

class HavaDurumuArayuz:
    def __init__(self, root):
        self.root = root
        self.root.title("İstanbul Hava Durumu Takip Sistemi")
        self.root.geometry("600x800")
        
        # API anahtarı
        self.api_key = "1d3ba4e02dda8d44b246972c395518f4"
        
        # Kadıköy'deki 10 sensör noktası (mahalleler)
        self.sensor_noktalari = {
            'Kadıköy Merkez': {'lat': 40.9892, 'lon': 29.0282},
            'Moda': {'lat': 40.9800, 'lon': 29.0260},
            'Fenerbahçe': {'lat': 40.9697, 'lon': 29.0360},
            'Caddebostan': {'lat': 40.9650, 'lon': 29.0600},
            'Suadiye': {'lat': 40.9572, 'lon': 29.0800},
            'Bostancı': {'lat': 40.9500, 'lon': 29.1000},
            'Kozyatağı': {'lat': 40.9800, 'lon': 29.1000},
            'Acıbadem': {'lat': 41.0000, 'lon': 29.0400},
            'Fikirtepe': {'lat': 41.0000, 'lon': 29.0300},
            'Göztepe': {'lat': 40.9700, 'lon': 29.0500}
        }
        
        # KAA simülasyonunu başlat
        self.kaa_simulasyon = KAASimulasyon()
        self.kaa_simulasyon.ag_olustur(sensor_sayisi=len(self.sensor_noktalari))
        
        # Sensör verilerini saklamak için sözlük
        self.sensor_verileri = {}
        
        self.arayuz_olustur()
        self.harita_olustur()
    
    def arayuz_olustur(self):
        # Ana frame'i oluştur
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(expand=True, fill="both", padx=10, pady=10)
        
        # İlçe seçim alanı
        self.ilce_label = ttk.Label(self.main_frame, text="Sensör Noktaları:")
        self.ilce_label.pack(pady=10)
        
        self.ilce_combo = ttk.Combobox(self.main_frame, values=list(self.sensor_noktalari.keys()))
        self.ilce_combo.pack(pady=5)
        self.ilce_combo.set(list(self.sensor_noktalari.keys())[0])
        
        # Hava durumu güncelleme butonu
        self.guncelle_btn = ttk.Button(
            self.main_frame,
            text="Hava Durumunu Güncelle",
            command=self.hava_durumu_guncelle
        )
        self.guncelle_btn.pack(pady=20)

        # Harita gösterme butonu
        self.harita_btn = ttk.Button(
            self.main_frame,
            text="Haritayı Göster",
            command=self.harita_goster
        )
        self.harita_btn.pack(pady=10)
        
        # Hava durumu bilgi alanı
        self.bilgi_frame = ttk.LabelFrame(self.main_frame, text="Ortalama Hava Durumu Bilgileri")
        self.bilgi_frame.pack(pady=10, fill="x")
        
        self.sicaklik_label = ttk.Label(self.bilgi_frame, text="Ortalama Sıcaklık: ")
        self.sicaklik_label.pack(pady=5)
        
        self.nem_label = ttk.Label(self.bilgi_frame, text="Ortalama Nem: ")
        self.nem_label.pack(pady=5)
        
        self.basinc_label = ttk.Label(self.bilgi_frame, text="Ortalama Basınç: ")
        self.basinc_label.pack(pady=5)
        
        self.ruzgar_label = ttk.Label(self.bilgi_frame, text="Ortalama Rüzgar Hızı: ")
        self.ruzgar_label.pack(pady=5)
        
        self.guncelleme_label = ttk.Label(self.bilgi_frame, text="Son Güncelleme: ")
        self.guncelleme_label.pack(pady=5)
        
        # Sensör ağı bilgi alanı
        self.sensor_frame = ttk.LabelFrame(self.main_frame, text="Sensör Ağı Bilgileri")
        self.sensor_frame.pack(pady=10, fill="x")
        
        self.aktif_sensor_label = ttk.Label(self.sensor_frame, text="Aktif Sensör Sayısı: ")
        self.aktif_sensor_label.pack(pady=5)
        
        self.ortalama_enerji_label = ttk.Label(self.sensor_frame, text="Ortalama Enerji Seviyesi: ")
        self.ortalama_enerji_label.pack(pady=5)
        
        self.koordinator_label = ttk.Label(self.sensor_frame, text="Koordinatör Sensör: ")
        self.koordinator_label.pack(pady=5)
        
        # Enerji tüketimi göstergesi
        self.enerji_frame = ttk.LabelFrame(self.main_frame, text="Enerji Tüketim Tahmini")
        self.enerji_frame.pack(pady=10, fill="x")
        
        self.enerji_tuketim_label = ttk.Label(self.enerji_frame, text="Tahmini Enerji Tüketimi: ")
        self.enerji_tuketim_label.pack(pady=5)
    
    def harita_olustur(self):
        """Kadıköy'ün haritasını ve sensör noktalarını oluşturur"""
        m = folium.Map(
            location=[40.9892, 29.0282],  # Kadıköy merkez
            zoom_start=13,
            tiles="OpenStreetMap"
        )
        
        # Sensör noktalarını haritaya ekle
        for isim, konum in self.sensor_noktalari.items():
            folium.Marker(
                [konum['lat'], konum['lon']],
                popup=f"Sensör: {isim}",
                icon=folium.Icon(color='red', icon='info-sign')
            ).add_to(m)
        
        # Haritayı HTML dosyası olarak kaydet
        self.harita_dosyasi = os.path.join(os.getcwd(), "kadikoy_harita.html")
        m.save(self.harita_dosyasi)
    
    def harita_goster(self):
        """Haritayı ayrı bir pencerede gösterir"""
        # Haritayı güncelle
        self.harita_olustur()
        # Yeni bir pencerede haritayı göster
        webview.create_window("Kadıköy Haritası", url=self.harita_dosyasi, width=800, height=600)
        webview.start()
    
    def hava_durumu_guncelle(self):
        try:
            tum_veriler = {}
            toplam_sicaklik = 0
            toplam_nem = 0
            toplam_ruzgar = 0
            toplam_basinc = 0
            
            # Her sensör noktası için hava durumu verilerini çek
            for isim, konum in self.sensor_noktalari.items():
                url = f"http://api.openweathermap.org/data/2.5/weather?lat={konum['lat']}&lon={konum['lon']}&appid={self.api_key}&units=metric"
                response = requests.get(url)
                data = response.json()
                
                if response.status_code == 200:
                    sicaklik = data['main']['temp']
                    nem = data['main']['humidity']
                    basinc = data['main']['pressure']
                    ruzgar = data['wind']['speed']
                    
                    tum_veriler[isim] = {
                        'sicaklik': sicaklik,
                        'nem': nem,
                        'basinc': basinc,
                        'ruzgar': ruzgar
                    }
                    
                    toplam_sicaklik += sicaklik
                    toplam_nem += nem
                    toplam_basinc += basinc
                    toplam_ruzgar += ruzgar
            
            # Ortalama değerleri hesapla
            sensor_sayisi = len(self.sensor_noktalari)
            ort_sicaklik = toplam_sicaklik / sensor_sayisi
            ort_nem = toplam_nem / sensor_sayisi
            ort_basinc = toplam_basinc / sensor_sayisi
            ort_ruzgar = toplam_ruzgar / sensor_sayisi
            
            # Arayüzü güncelle
            self.sicaklik_label.config(text=f"Ortalama Sıcaklık: {ort_sicaklik:.1f}°C")
            self.nem_label.config(text=f"Ortalama Nem: {ort_nem:.1f}%")
            self.basinc_label.config(text=f"Ortalama Basınç: {ort_basinc:.1f} hPa")
            self.ruzgar_label.config(text=f"Ortalama Rüzgar Hızı: {ort_ruzgar:.1f} m/s")
            
            guncel_zaman = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
            self.guncelleme_label.config(text=f"Son Güncelleme: {guncel_zaman}")
            
            # Sensör detaylarını göster
            self.sensor_detaylarini_goster(tum_veriler)
            
            # Bulanık mantık sistemini çalıştır
            hava_durumu_verileri = {
                'sicaklik': ort_sicaklik,
                'nem': ort_nem,
                'ruzgar': ort_ruzgar
            }
            
            # Sensörlerin enerji tüketimini hesapla
            self.kaa_simulasyon.enerji_hesapla(hava_durumu_verileri)
            
            # Senkronizasyon protokolünü çalıştır
            sonuc = self.kaa_simulasyon.senkronizasyon_protokolu()
            
            if isinstance(sonuc, str):
                self.aktif_sensor_label.config(text="Aktif Sensör Sayısı: 0")
                self.ortalama_enerji_label.config(text="Ortalama Enerji Seviyesi: 0%")
                self.koordinator_label.config(text="Koordinatör Sensör: Yok")
            else:
                self.aktif_sensor_label.config(text=f"Aktif Sensör Sayısı: {sonuc['aktif_sensor_sayisi']}")
                self.ortalama_enerji_label.config(text=f"Ortalama Enerji Seviyesi: {sonuc['ortalama_enerji']:.2f}%")
                self.koordinator_label.config(text=f"Koordinatör Sensör: {list(self.sensor_noktalari.keys())[sonuc['koordinator']]}")
            
            # Enerji tüketim tahminini göster
            enerji_tuketimi = self.kaa_simulasyon.bulanik_mantik_kurallari(ort_sicaklik, ort_nem, ort_ruzgar)
            self.enerji_tuketim_label.config(text=f"Tahmini Enerji Tüketimi: {enerji_tuketimi:.2f}%")
            
        except Exception as e:
            print(f"Hata oluştu: {e}")
    
    def sensor_detaylarini_goster(self, veriler):
        """Her sensör için detaylı bilgileri gösterir"""
        # Eğer detay penceresi daha önce oluşturulmadıysa
        if not hasattr(self, 'detay_pencere'):
            self.detay_pencere = tk.Toplevel(self.root)
            self.detay_pencere.title("Sensör Detayları")
            self.detay_pencere.geometry("600x800")  # Pencere boyutunu artır
            
            # Pencereyi ekranın ortasına konumlandır
            screen_width = self.detay_pencere.winfo_screenwidth()
            screen_height = self.detay_pencere.winfo_screenheight()
            x = (screen_width - 600) // 2
            y = (screen_height - 800) // 2
            self.detay_pencere.geometry(f"600x800+{x}+{y}")
        
        # Mevcut içeriği temizle
        for widget in self.detay_pencere.winfo_children():
            widget.destroy()
        
        # Ana container frame
        container = ttk.Frame(self.detay_pencere)
        container.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Canvas ve scrollbar oluştur
        canvas = tk.Canvas(container)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        
        # Frame oluştur ve canvas'a yerleştir
        scrollable_frame = ttk.Frame(canvas)
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        # Canvas'a frame'i yerleştir
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Başlık etiketi
        baslik = ttk.Label(
            scrollable_frame,
            text="SENSÖR ÖLÇÜM VERİLERİ",
            font=("Arial", 12, "bold")
        )
        baslik.pack(pady=10, fill="x")
        
        # Güncelleme zamanı
        guncel_zaman = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        zaman_etiketi = ttk.Label(
            scrollable_frame,
            text=f"Son Güncelleme: {guncel_zaman}",
            font=("Arial", 10, "italic")
        )
        zaman_etiketi.pack(pady=5, fill="x")
        
        ttk.Separator(scrollable_frame).pack(fill="x", pady=10)  # Ayraç çizgisi
        
        # Her sensör için bilgileri göster
        for isim, veri in veriler.items():
            frame = ttk.LabelFrame(
                scrollable_frame,
                text=isim,
                padding=10
            )
            frame.pack(pady=5, padx=2, fill="x")
            
            # Grid layout için frame
            grid_frame = ttk.Frame(frame)
            grid_frame.pack(fill="x", expand=True)
            
            # Başlıklar
            ttk.Label(grid_frame, text="Parametre", font=("Arial", 10, "bold")).grid(row=0, column=0, padx=5, pady=5, sticky="w")
            ttk.Label(grid_frame, text="Değer", font=("Arial", 10, "bold")).grid(row=0, column=1, padx=5, pady=5, sticky="w")
            
            # Veriler
            ttk.Label(grid_frame, text="Sıcaklık").grid(row=1, column=0, padx=5, pady=2, sticky="w")
            ttk.Label(grid_frame, text=f"{veri['sicaklik']:.1f}°C").grid(row=1, column=1, padx=5, pady=2, sticky="w")
            
            ttk.Label(grid_frame, text="Nem").grid(row=2, column=0, padx=5, pady=2, sticky="w")
            ttk.Label(grid_frame, text=f"{veri['nem']:.1f}%").grid(row=2, column=1, padx=5, pady=2, sticky="w")
            
            ttk.Label(grid_frame, text="Basınç").grid(row=3, column=0, padx=5, pady=2, sticky="w")
            ttk.Label(grid_frame, text=f"{veri['basinc']} hPa").grid(row=3, column=1, padx=5, pady=2, sticky="w")
            
            ttk.Label(grid_frame, text="Rüzgar Hızı").grid(row=4, column=0, padx=5, pady=2, sticky="w")
            ttk.Label(grid_frame, text=f"{veri['ruzgar']:.1f} m/s").grid(row=4, column=1, padx=5, pady=2, sticky="w")
        
        # Scrollbar ve canvas'ı yerleştir
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        
        # Mouse wheel ile scroll yapabilme
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # Pencere kapatıldığında bind'ı kaldır
        def _on_closing():
            canvas.unbind_all("<MouseWheel>")
            self.detay_pencere.destroy()
            delattr(self, 'detay_pencere')
        
        self.detay_pencere.protocol("WM_DELETE_WINDOW", _on_closing)

class KAASimulasyon:
    def __init__(self):
        self.ag = None
        self.sensor_durumlari = {}
        
        # Bulanık mantık için evren değişkenleri
        self.sicaklik_universe = np.arange(0, 41, 1)  # 0-40°C
        self.nem_universe = np.arange(0, 101, 1)      # 0-100%
        self.ruzgar_universe = np.arange(0, 21, 1)    # 0-20 m/s
        self.enerji_universe = np.arange(0, 101, 1)   # 0-100% enerji tüketimi
        
        # Üyelik fonksiyonlarını oluştur
        self.sicaklik_uyelik = self._sicaklik_uyelik_fonksiyonlari()
        self.nem_uyelik = self._nem_uyelik_fonksiyonlari()
        self.ruzgar_uyelik = self._ruzgar_uyelik_fonksiyonlari()
        self.enerji_uyelik = self._enerji_uyelik_fonksiyonlari()
        
    def ag_olustur(self, sensor_sayisi):
        """Kablosuz algılayıcı ağın topolojisini oluşturur."""
        self.ag = nx.random_geometric_graph(sensor_sayisi, 0.3)
        
        # Sensörlerin başlangıç durumlarını ayarla
        for node in self.ag.nodes():
            self.sensor_durumlari[node] = {
                'enerji_seviyesi': 100,  # Başlangıçta %100 enerji
                'aktif': True
            }
    
    def _sicaklik_uyelik_fonksiyonlari(self):
        """Sıcaklık için üyelik fonksiyonlarını tanımlar"""
        dusuk = fuzz.trimf(self.sicaklik_universe, [0, 0, 20])
        orta = fuzz.trimf(self.sicaklik_universe, [15, 25, 35])
        yuksek = fuzz.trimf(self.sicaklik_universe, [30, 40, 40])
        return {'dusuk': dusuk, 'orta': orta, 'yuksek': yuksek}
    
    def _nem_uyelik_fonksiyonlari(self):
        """Nem için üyelik fonksiyonlarını tanımlar"""
        dusuk = fuzz.trimf(self.nem_universe, [0, 0, 40])
        orta = fuzz.trimf(self.nem_universe, [30, 50, 70])
        yuksek = fuzz.trimf(self.nem_universe, [60, 100, 100])
        return {'dusuk': dusuk, 'orta': orta, 'yuksek': yuksek}
    
    def _ruzgar_uyelik_fonksiyonlari(self):
        """Rüzgar hızı için üyelik fonksiyonlarını tanımlar"""
        yavas = fuzz.trimf(self.ruzgar_universe, [0, 0, 8])
        orta = fuzz.trimf(self.ruzgar_universe, [6, 10, 14])
        hizli = fuzz.trimf(self.ruzgar_universe, [12, 20, 20])
        return {'yavas': yavas, 'orta': orta, 'hizli': hizli}
    
    def _enerji_uyelik_fonksiyonlari(self):
        """Enerji tüketimi için üyelik fonksiyonlarını tanımlar"""
        cok_dusuk = fuzz.trimf(self.enerji_universe, [0, 0, 25])
        dusuk = fuzz.trimf(self.enerji_universe, [20, 35, 50])
        orta = fuzz.trimf(self.enerji_universe, [45, 60, 75])
        yuksek = fuzz.trimf(self.enerji_universe, [70, 85, 100])
        return {'cok_dusuk': cok_dusuk, 'dusuk': dusuk, 'orta': orta, 'yuksek': yuksek}
    
    def bulanik_mantik_kurallari(self, sicaklik, nem, ruzgar):
        """Bulanık mantık kurallarını uygular ve enerji tüketimini hesaplar"""
        # Giriş değerlerinin üyelik derecelerini hesapla
        sicaklik_derece = {
            'dusuk': fuzz.interp_membership(self.sicaklik_universe, self.sicaklik_uyelik['dusuk'], sicaklik),
            'orta': fuzz.interp_membership(self.sicaklik_universe, self.sicaklik_uyelik['orta'], sicaklik),
            'yuksek': fuzz.interp_membership(self.sicaklik_universe, self.sicaklik_uyelik['yuksek'], sicaklik)
        }
        
        nem_derece = {
            'dusuk': fuzz.interp_membership(self.nem_universe, self.nem_uyelik['dusuk'], nem),
            'orta': fuzz.interp_membership(self.nem_universe, self.nem_uyelik['orta'], nem),
            'yuksek': fuzz.interp_membership(self.nem_universe, self.nem_uyelik['yuksek'], nem)
        }
        
        ruzgar_derece = {
            'yavas': fuzz.interp_membership(self.ruzgar_universe, self.ruzgar_uyelik['yavas'], ruzgar),
            'orta': fuzz.interp_membership(self.ruzgar_universe, self.ruzgar_uyelik['orta'], ruzgar),
            'hizli': fuzz.interp_membership(self.ruzgar_universe, self.ruzgar_uyelik['hizli'], ruzgar)
        }
        
        # Kural tabanı
        rules = {
            'cok_dusuk': [],  # En düşük enerji tüketimi
            'dusuk': [],      # Düşük enerji tüketimi
            'orta': [],       # Orta enerji tüketimi
            'yuksek': []      # Yüksek enerji tüketimi
        }
        
        # Örnek kurallar:
        # 1. Eğer sıcaklık düşük ve nem düşük ve rüzgar yavaş ise, enerji tüketimi çok düşük
        rules['cok_dusuk'].append(min([sicaklik_derece['dusuk'], nem_derece['dusuk'], ruzgar_derece['yavas']]))
        
        # 2. Eğer sıcaklık yüksek veya nem yüksek ise, enerji tüketimi yüksek
        rules['yuksek'].append(max([sicaklik_derece['yuksek'], nem_derece['yuksek']]))
        
        # 3. Eğer koşullar orta seviyede ise, enerji tüketimi orta
        rules['orta'].append(min([sicaklik_derece['orta'], nem_derece['orta'], ruzgar_derece['orta']]))
        
        # Her kural grubu için maksimum değeri al
        activation = {
            'cok_dusuk': max(rules['cok_dusuk']) if rules['cok_dusuk'] else 0,
            'dusuk': max(rules['dusuk']) if rules['dusuk'] else 0,
            'orta': max(rules['orta']) if rules['orta'] else 0,
            'yuksek': max(rules['yuksek']) if rules['yuksek'] else 0
        }
        
        # Durulaştırma için ağırlıklı ortalama yöntemi
        numerator = 0
        denominator = 0
        
        for label, degree in activation.items():
            if degree > 0:
                # Her üyelik fonksiyonunun ağırlık merkezini hesapla
                centroid = fuzz.defuzz(self.enerji_universe, self.enerji_uyelik[label], 'centroid')
                if not np.isnan(centroid):  # Eğer centroid hesaplanabilirse
                    numerator += centroid * degree
                    denominator += degree
        
        # Enerji tüketim seviyesini hesapla
        if denominator > 0:
            enerji_tuketimi = numerator / denominator
        else:
            enerji_tuketimi = 50  # Varsayılan değer
        
        return enerji_tuketimi
    
    def enerji_hesapla(self, hava_durumu_verileri):
        """Sensör düğümlerinin enerji tüketimini hesaplar."""
        for node in self.ag.nodes():
            if self.sensor_durumlari[node]['aktif']:
                # Bulanık mantık ile enerji tüketimini hesapla
                enerji_tuketimi = self.bulanik_mantik_kurallari(
                    hava_durumu_verileri['sicaklik'],
                    hava_durumu_verileri['nem'],
                    hava_durumu_verileri['ruzgar']
                )
                
                # Sensörün enerji seviyesini güncelle
                self.sensor_durumlari[node]['enerji_seviyesi'] -= (enerji_tuketimi / 100)  # Yüzdelik değeri
                
                # Enerji seviyesi kritik seviyenin altına düşerse sensörü devre dışı bırak
                if self.sensor_durumlari[node]['enerji_seviyesi'] < 10:  # %10 kritik seviye
                    self.sensor_durumlari[node]['aktif'] = False
    
    def senkronizasyon_protokolu(self):
        """Senkronizasyon protokolünü uygular."""
        aktif_sensorler = [node for node in self.ag.nodes() if self.sensor_durumlari[node]['aktif']]
        
        if not aktif_sensorler:
            return "Aktif sensör kalmadı!"
        
        # En yüksek enerjiye sahip sensörü koordinatör seç
        koordinator = max(aktif_sensorler, 
                         key=lambda x: self.sensor_durumlari[x]['enerji_seviyesi'])
        
        return {
            'koordinator': koordinator,
            'aktif_sensor_sayisi': len(aktif_sensorler),
            'ortalama_enerji': np.mean([self.sensor_durumlari[node]['enerji_seviyesi'] 
                                      for node in aktif_sensorler])
        }

def main():
    root = tk.Tk()
    app = HavaDurumuArayuz(root)
    root.mainloop()

if __name__ == "__main__":
    main() 