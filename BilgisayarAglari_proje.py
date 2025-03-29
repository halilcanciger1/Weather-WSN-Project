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
from tkinter import ttk, filedialog
from datetime import datetime
import json
import folium
import os
import webview
import random
import tkinter.messagebox as messagebox
import skfuzzy.control as ctrl

class HavaDurumuArayuz:
    def __init__(self, root):
        self.root = root
        self.root.title("Ankara Sensör Ağı")
        self.root.geometry("1200x800")
        
        # Ana scroll frame
        self.main_canvas = tk.Canvas(root)
        self.scrollbar = ttk.Scrollbar(root, orient="vertical", command=self.main_canvas.yview)
        self.scrollable_frame = ttk.Frame(self.main_canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.main_canvas.configure(scrollregion=self.main_canvas.bbox("all"))
        )
        
        self.main_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.main_canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Pack scrollbar and canvas
        self.scrollbar.pack(side="right", fill="y")
        self.main_canvas.pack(side="left", fill="both", expand=True)
        
        # Ana frame'i scrollable frame'e taşı
        self.main_frame = ttk.Frame(self.scrollable_frame)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Fare tekerleği ile kaydırma
        self.main_canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        
        # API anahtarı
        self.api_key = "1d3ba4e02dda8d44b246972c395518f4"
        
        # Ankara'nın bölgesel koordinatları (kara alanları)
        self.ankara_bolgeler = [
            # Merkez Bölgeler
            {
                'isim': 'Çankaya Bölgesi',
                'min_lat': 39.80,
                'max_lat': 40.00,
                'min_lon': 32.70,
                'max_lon': 33.00
            },
            {
                'isim': 'Keçiören-Yenimahalle Bölgesi',
                'min_lat': 39.90,
                'max_lat': 40.10,
                'min_lon': 32.60,
                'max_lon': 33.00
            },
            # Batı Bölgeler
            {
                'isim': 'Etimesgut-Sincan Bölgesi',
                'min_lat': 39.85,
                'max_lat': 40.05,
                'min_lon': 32.40,
                'max_lon': 32.80
            },
            # Doğu Bölgeler
            {
                'isim': 'Mamak-Altındağ Bölgesi',
                'min_lat': 39.85,
                'max_lat': 40.10,
                'min_lon': 32.80,
                'max_lon': 33.20
            },
            # Güney Bölgeler
            {
                'isim': 'Gölbaşı Bölgesi',
                'min_lat': 39.60,
                'max_lat': 39.90,
                'min_lon': 32.70,
                'max_lon': 33.00
            },
            # Kuzey Bölgeler
            {
                'isim': 'Pursaklar-Akyurt Bölgesi',
                'min_lat': 40.00,
                'max_lat': 40.20,
                'min_lon': 32.80,
                'max_lon': 33.20
            }
        ]
        
        # Su alanları (sadece Mogan Gölü)
        self.su_alanlari = [
            {
                'isim': 'Mogan Gölü',
                'min_lat': 39.72,
                'max_lat': 39.78,
                'min_lon': 32.74,
                'max_lon': 32.83
            }
        ]
        
        # Güvenli mesafe (derece cinsinden)
        self.guvenli_mesafe = 0.005  # Yaklaşık 500 metre
        
        # Sensör noktaları için boş sözlük
        self.sensor_noktalari = {}
        
        # KAA simülasyonunu başlat
        self.kaa_simulasyon = KAASimulasyon()
        
        # Enerji seviyesi renk kodları
        self.enerji_renkleri = {
            'tam_dolu': {'min': 90, 'max': 100, 'renk': 'green', 'aciklama': 'Tam Dolu'},
            'cok_iyi': {'min': 75, 'max': 89, 'renk': 'green4', 'aciklama': 'Çok İyi'},
            'iyi': {'min': 60, 'max': 74, 'renk': 'blue', 'aciklama': 'İyi'},
            'orta': {'min': 45, 'max': 59, 'renk': 'orange', 'aciklama': 'Orta'},
            'dusuk': {'min': 30, 'max': 44, 'renk': 'orange3', 'aciklama': 'Düşük'},
            'kritik': {'min': 15, 'max': 29, 'renk': 'red', 'aciklama': 'Kritik'},
            'tukenme': {'min': 0, 'max': 14, 'renk': 'red4', 'aciklama': 'Tükenme'}
        }
        
        self.arayuz_olustur()
        self.harita_olustur()
    
    def arayuz_olustur(self):
        # Ana frame'i oluştur
        self.main_frame = ttk.Frame(self.main_frame)
        self.main_frame.pack(expand=True, fill="both", padx=10, pady=10)
        
        # Sensör ayarları için frame
        self.sensor_frame = ttk.LabelFrame(self.main_frame, text="Sensör Ayarları")
        self.sensor_frame.pack(pady=10, fill="x")
        
        # Sensör sayısı girişi
        ttk.Label(self.sensor_frame, text="Sensör Sayısı:").pack(side="left", padx=5)
        self.sensor_sayi_var = tk.StringVar(value="20")
        self.sensor_entry = ttk.Entry(self.sensor_frame, textvariable=self.sensor_sayi_var, width=15)
        self.sensor_entry.pack(side="left", padx=5)
        
        # Alan boyutu girişi
        ttk.Label(self.sensor_frame, text="Alan Boyutu (km²):").pack(side="left", padx=5)
        self.alan_boyut_var = tk.StringVar(value="5")
        self.alan_entry = ttk.Entry(self.sensor_frame, textvariable=self.alan_boyut_var, width=15)
        self.alan_entry.pack(side="left", padx=5)
        
        # Sensörleri yerleştir butonu
        self.yerlestir_btn = ttk.Button(
            self.sensor_frame,
            text="Sensörleri Yerleştir",
            command=self.sensorleri_yerlestir
        )
        self.yerlestir_btn.pack(side="left", padx=5)
        
        # Buton frame'i
        self.button_frame = ttk.Frame(self.main_frame)
        self.button_frame.pack(pady=10)
        
        # Hava durumu güncelleme butonu
        self.guncelle_btn = ttk.Button(
            self.button_frame,
            text="Hava Durumunu Güncelle",
            command=self.hava_durumu_guncelle
        )
        self.guncelle_btn.pack(side="left", padx=5)
        
        # Harita gösterme butonu
        self.harita_btn = ttk.Button(
            self.button_frame,
            text="Haritayı Göster",
            command=self.harita_goster
        )
        self.harita_btn.pack(side="left", padx=5)
        
        # Bulanık mantık detayları butonu
        self.bulanik_btn = ttk.Button(
            self.button_frame,
            text="Bulanık Mantık Detayları",
            command=self.bulanik_mantik_detaylari_goster
        )
        self.bulanik_btn.pack(side="left", padx=5)
        
        # MATLAB .fis dosyasını yükle butonu
        self.fis_yukle_btn = ttk.Button(
            self.button_frame,
            text="MATLAB FIS Dosyası Yükle",
            command=self.fis_dosyasi_sec
        )
        self.fis_yukle_btn.pack(side="left", padx=5)
        
        # Hava durumu bilgi alanı
        self.bilgi_frame = ttk.LabelFrame(self.main_frame, text="Ortalama Hava Durumu Bilgileri")
        self.bilgi_frame.pack(pady=10, fill="x")
        
        self.sicaklik_label = ttk.Label(self.bilgi_frame, text="Ortalama Sıcaklık: ")
        self.sicaklik_label.pack(pady=5)
        
        self.nem_label = ttk.Label(self.bilgi_frame, text="Ortalama Nem: ")
        self.nem_label.pack(pady=5)
        
        self.basinc_label = ttk.Label(self.bilgi_frame, text="Ortalama Basınç: ")
        self.basinc_label.pack(pady=5)
        
        self.ruzgar_label = ttk.Label(self.bilgi_frame, text="Ortalama pH: ")
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
        self.enerji_frame = ttk.LabelFrame(self.main_frame, text="Bulanık Mantık Enerji Analizi")
        self.enerji_frame.pack(pady=10, fill="x")
        
        self.enerji_tuketim_label = ttk.Label(self.enerji_frame, text="Tahmini Enerji Tüketimi: ")
        self.enerji_tuketim_label.pack(pady=5)
        
        # Renk kodları ve üyelik fonksiyonları frame'i
        style = ttk.Style()
        style.configure('Title.TLabel', font=('Arial', 10, 'bold'))
        style.configure('Subtitle.TLabel', font=('Arial', 9))
        style.configure('Separator.TFrame', background='gray')

        # Ana container frame
        info_container = ttk.Frame(self.main_frame)
        info_container.pack(fill=tk.X, padx=10, pady=5)

        # Sol panel - Renk kodları
        left_panel = ttk.LabelFrame(info_container, text="Enerji Tüketimi Renk Kodları")
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

        ttk.Label(left_panel, text="Renk Kodları:", style='Title.TLabel').pack(anchor=tk.W, pady=(5,2))
        ttk.Label(left_panel, text="■ Çok Yüksek (81-100%)", foreground="red").pack(anchor=tk.W, padx=5)
        ttk.Label(left_panel, text="■ Yüksek (61-80%)", foreground="orange").pack(anchor=tk.W, padx=5)
        ttk.Label(left_panel, text="■ Normal (41-60%)", foreground="blue").pack(anchor=tk.W, padx=5)
        ttk.Label(left_panel, text="■ Düşük (21-40%)", foreground="green").pack(anchor=tk.W, padx=5)
        ttk.Label(left_panel, text="■ Minimum (0-20%)", foreground="darkgreen").pack(anchor=tk.W, padx=5)

        # Sağ panel - Üyelik fonksiyonları
        right_panel = ttk.LabelFrame(info_container, text="Üyelik Fonksiyonları")
        right_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

        # Pil seviyesi
        ttk.Label(right_panel, text="Pil Seviyesi:", style='Title.TLabel').pack(anchor=tk.W, pady=(5,2))
        ttk.Label(right_panel, text="• Çok Kötü: 0-20%", style='Subtitle.TLabel').pack(anchor=tk.W, padx=5)
        ttk.Label(right_panel, text="• Kötü: 21-40%", style='Subtitle.TLabel').pack(anchor=tk.W, padx=5)
        ttk.Label(right_panel, text="• Orta: 41-60%", style='Subtitle.TLabel').pack(anchor=tk.W, padx=5)
        ttk.Label(right_panel, text="• İyi: 61-80%", style='Subtitle.TLabel').pack(anchor=tk.W, padx=5)
        ttk.Label(right_panel, text="• Çok İyi: 81-100%", style='Subtitle.TLabel').pack(anchor=tk.W, padx=5)

        separator1 = ttk.Frame(right_panel, height=1, style='Separator.TFrame')
        separator1.pack(fill=tk.X, padx=5, pady=5)

        # Nem seviyesi
        ttk.Label(right_panel, text="Nem Seviyesi:", style='Title.TLabel').pack(anchor=tk.W, pady=(5,2))
        ttk.Label(right_panel, text="• Kuru Toprak: 0-300 g/m³", style='Subtitle.TLabel').pack(anchor=tk.W, padx=5)
        ttk.Label(right_panel, text="• Nemli Toprak: 300-700 g/m³", style='Subtitle.TLabel').pack(anchor=tk.W, padx=5)
        ttk.Label(right_panel, text="• Suda: 700-950 g/m³", style='Subtitle.TLabel').pack(anchor=tk.W, padx=5)

        separator2 = ttk.Frame(right_panel, height=1, style='Separator.TFrame')
        separator2.pack(fill=tk.X, padx=5, pady=5)

        # pH seviyesi
        ttk.Label(right_panel, text="pH Seviyesi:", style='Title.TLabel').pack(anchor=tk.W, pady=(5,2))
        ttk.Label(right_panel, text="• Asidik: 0-6.9", style='Subtitle.TLabel').pack(anchor=tk.W, padx=5)
        ttk.Label(right_panel, text="• Nötr: 7.0", style='Subtitle.TLabel').pack(anchor=tk.W, padx=5)
        ttk.Label(right_panel, text="• Bazik: 7.1-14", style='Subtitle.TLabel').pack(anchor=tk.W, padx=5)

        separator3 = ttk.Frame(right_panel, height=1, style='Separator.TFrame')
        separator3.pack(fill=tk.X, padx=5, pady=5)

        # Basınç seviyesi
        ttk.Label(right_panel, text="Basınç Seviyesi:", style='Title.TLabel').pack(anchor=tk.W, pady=(5,2))
        ttk.Label(right_panel, text="• Düşük: -1.0 ile -0.4 bar", style='Subtitle.TLabel').pack(anchor=tk.W, padx=5)
        ttk.Label(right_panel, text="• Normal: -0.4 ile 0.4 bar", style='Subtitle.TLabel').pack(anchor=tk.W, padx=5)
        ttk.Label(right_panel, text="• Yüksek: 0.4 ile 1.0 bar", style='Subtitle.TLabel').pack(anchor=tk.W, padx=5)

        # Enerji tüketimi açıklaması
        consumption_frame = ttk.LabelFrame(self.main_frame, text="Enerji Tüketimi Seviyeleri")
        consumption_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(consumption_frame, text="Minimum (0-20%): En düşük enerji tüketimi, optimal çalışma koşulları", style='Subtitle.TLabel').pack(anchor=tk.W, padx=5, pady=2)
        ttk.Label(consumption_frame, text="Düşük (21-40%): Verimli çalışma, normal koşullar altında enerji tasarrufu", style='Subtitle.TLabel').pack(anchor=tk.W, padx=5, pady=2)
        ttk.Label(consumption_frame, text="Normal (41-60%): Standart çalışma koşulları, ortalama enerji tüketimi", style='Subtitle.TLabel').pack(anchor=tk.W, padx=5, pady=2)
        ttk.Label(consumption_frame, text="Yüksek (61-80%): Zorlu koşullar altında artan enerji tüketimi", style='Subtitle.TLabel').pack(anchor=tk.W, padx=5, pady=2)
        ttk.Label(consumption_frame, text="Çok Yüksek (81-100%): Kritik durum, maksimum enerji tüketimi", style='Subtitle.TLabel').pack(anchor=tk.W, padx=5, pady=2)
    
    def sensorleri_yerlestir(self):
        try:
            # Kullanıcının girdiği değerleri al
            sensor_sayisi = int(self.sensor_sayi_var.get())
            alan_boyutu = float(self.alan_boyut_var.get())  # km² cinsinden
            
            if sensor_sayisi <= 0:
                raise ValueError("Sensör sayısı pozitif olmalıdır!")
            
            if alan_boyutu <= 0:
                raise ValueError("Alan boyutu pozitif olmalıdır!")
            
            # Sensör noktalarını ve verilerini temizle
            self.sensor_noktalari.clear()
            self.tum_veriler = {}
            
            # Her bölge için sensör sayısını hesapla
            bolge_basina = sensor_sayisi // len(self.ankara_bolgeler)
            kalan_sensor = sensor_sayisi % len(self.ankara_bolgeler)
            
            # Derece cinsinden alan boyutunu hesapla
            derece_boyut = alan_boyutu / 111.0
            
            # Sensörleri yerleştir
            yerlestirilmis = 0
            
            # Her bölgeye sensör yerleştir
            for i, bolge in enumerate(self.ankara_bolgeler):
                hedef_sensor = bolge_basina + (1 if i < kalan_sensor else 0)
                bolgedeki_sensor = 0
                merkez_lat = (bolge['min_lat'] + bolge['max_lat']) / 2
                merkez_lon = (bolge['min_lon'] + bolge['max_lon']) / 2
                
                while bolgedeki_sensor < hedef_sensor:
                    # Belirlenen alan içinde rastgele bir nokta seç
                    lat = random.uniform(
                        max(bolge['min_lat'], merkez_lat - derece_boyut/2),
                        min(bolge['max_lat'], merkez_lat + derece_boyut/2)
                    )
                    lon = random.uniform(
                        max(bolge['min_lon'], merkez_lon - derece_boyut/2),
                        min(bolge['max_lon'], merkez_lon + derece_boyut/2)
                    )
                    
                    if self.nokta_karada_mi(lat, lon):
                        sensor_isim = f'Sensör {yerlestirilmis + 1}'
                        self.sensor_noktalari[sensor_isim] = {
                            'lat': lat,
                            'lon': lon,
                            'bolge': bolge['isim']
                        }
                        
                        # Varsayılan hava durumu verilerini ata
                        self.tum_veriler[sensor_isim] = {
                            'sicaklik': 20.0,  # Varsayılan sıcaklık (°C)
                            'nem': 500.0,      # Varsayılan nem (g/m³)
                            'basinc': 0.0,     # Varsayılan basınç (bar)
                            'ph': 7.0          # Varsayılan pH
                        }
                        
                        yerlestirilmis += 1
                        bolgedeki_sensor += 1
            
            messagebox.showinfo(
                "Başarılı",
                f"{yerlestirilmis} adet sensör başarıyla yerleştirildi.\n" +
                f"Alan Boyutu: {alan_boyutu} km²\n" +
                "Not: Sensörler belirlenen alan içinde ve kara bölgelerinde dağıtılmıştır."
            )
            
            # KAA simülasyonunu güncelle
            self.kaa_simulasyon.ag_olustur(yerlestirilmis)
            
            # Haritayı güncelle
            self.harita_olustur()
            
        except ValueError as e:
            messagebox.showerror("Hata", str(e))
    
    def nokta_karada_mi(self, lat, lon):
        """Verilen koordinatın karada olup olmadığını kontrol eder"""
        # Önce noktanın su alanlarında olup olmadığını kontrol et
        for su in self.su_alanlari:
            # Su alanına güvenli mesafe ekleyerek kontrol et
            if (su['min_lat'] - self.guvenli_mesafe <= lat <= su['max_lat'] + self.guvenli_mesafe and 
                su['min_lon'] - self.guvenli_mesafe <= lon <= su['max_lon'] + self.guvenli_mesafe):
                return False
        
        # Sonra noktanın kara bölgelerinden birinde olup olmadığını kontrol et
        for bolge in self.ankara_bolgeler:
            # Kara bölgesinin iç kısmında olup olmadığını kontrol et
            if (bolge['min_lat'] + self.guvenli_mesafe <= lat <= bolge['max_lat'] - self.guvenli_mesafe and 
                bolge['min_lon'] + self.guvenli_mesafe <= lon <= bolge['max_lon'] - self.guvenli_mesafe):
                return True
        
        return False
    
    def harita_olustur(self):
        """Ankara haritasını ve sensör noktalarını oluşturur"""
        # Ankara'nın merkezi
        merkez_lat = 39.90
        merkez_lon = 32.80
        
        # Hava durumu verilerini sakla
        if not hasattr(self, 'tum_veriler'):
            self.tum_veriler = {}
            for isim, konum in self.sensor_noktalari.items():
                self.tum_veriler[isim] = {
                    'sicaklik': 20.0,  # Varsayılan değerler
                    'nem': 500.0,
                    'basinc': 0.0,
                    'ph': 7.0
                }
        
        m = folium.Map(
            location=[merkez_lat, merkez_lon],
            zoom_start=10,
            tiles="OpenStreetMap"
        )
        
        # Alan boyutunu derece cinsine çevir
        try:
            alan_boyutu = float(self.alan_boyut_var.get())
            derece_boyut = alan_boyutu / 111.0
        except:
            derece_boyut = 0
        
        # Kara bölgelerini yeşil renkle göster
        for bolge in self.ankara_bolgeler:
            folium.Rectangle(
                bounds=[
                    [bolge['min_lat'], bolge['min_lon']],
                    [bolge['max_lat'], bolge['max_lon']]
                ],
                color="green",
                fill=True,
                fillColor="green",
                fillOpacity=0.2,
                popup=bolge['isim'],
                weight=2
            ).add_to(m)
            
            # Seçili alan boyutunu göster
            if derece_boyut > 0:
                merkez_lat = (bolge['min_lat'] + bolge['max_lat']) / 2
                merkez_lon = (bolge['min_lon'] + bolge['max_lon']) / 2
                
                alan_min_lat = max(bolge['min_lat'], merkez_lat - derece_boyut/2)
                alan_max_lat = min(bolge['max_lat'], merkez_lat + derece_boyut/2)
                alan_min_lon = max(bolge['min_lon'], merkez_lon - derece_boyut/2)
                alan_max_lon = min(bolge['max_lon'], merkez_lon + derece_boyut/2)
                
                folium.Rectangle(
                    bounds=[
                        [alan_min_lat, alan_min_lon],
                        [alan_max_lat, alan_max_lon]
                    ],
                    color="red",
                    fill=True,
                    fillColor="red",
                    fillOpacity=0.1,
                    popup=f"Seçili Alan: {alan_boyutu} km²",
                    weight=1,
                    dash_array='5, 5'
                ).add_to(m)
        
        # Su alanlarını mavi renkle göster
        for su in self.su_alanlari:
            folium.Rectangle(
                bounds=[
                    [su['min_lat'], su['min_lon']],
                    [su['max_lat'], su['max_lon']]
                ],
                color="blue",
                fill=True,
                fillColor="blue",
                fillOpacity=0.3,
                popup=su['isim'],
                weight=1
            ).add_to(m)
        
        # Sensör noktalarını haritaya ekle
        for isim, konum in self.sensor_noktalari.items():
            # Sensörün enerji seviyesini al
            sensor_id = int(isim.split()[1]) - 1
            enerji_seviyesi = self.kaa_simulasyon.sensor_durumlari[sensor_id]['enerji_seviyesi']
            
            # Enerji tüketimini hesapla
            enerji_tuketimi = self.kaa_simulasyon.bulanik_mantik_kurallari(
                enerji_seviyesi,
                self.tum_veriler[isim]['nem'],
                self.tum_veriler[isim]['basinc'],
                self.tum_veriler[isim]['ph']
            )
            
            # Enerji tüketimine göre renk belirle
            if enerji_tuketimi >= 90:
                marker_renk = 'darkred'  # Çok yüksek tüketim
            elif enerji_tuketimi >= 70:
                marker_renk = 'red'      # Yüksek tüketim
            elif enerji_tuketimi >= 45:
                marker_renk = 'orange'   # Normal tüketim
            elif enerji_tuketimi >= 20:
                marker_renk = 'blue'     # Düşük tüketim
            else:
                marker_renk = 'green'    # Minimum tüketim
            
            # Pil seviyesine göre durum belirleme
            if enerji_seviyesi >= 90:
                pil_durumu = "Tam Dolu"
                pil_renk = "green"
            elif enerji_seviyesi >= 75:
                pil_durumu = "Çok İyi"
                pil_renk = "green"
            elif enerji_seviyesi >= 60:
                pil_durumu = "İyi"
                pil_renk = "blue"
            elif enerji_seviyesi >= 45:
                pil_durumu = "Orta"
                pil_renk = "orange"
            elif enerji_seviyesi >= 30:
                pil_durumu = "Düşük"
                pil_renk = "red"
            elif enerji_seviyesi >= 15:
                pil_durumu = "Kritik"
                pil_renk = "red"
            else:
                pil_durumu = "Tükenme"
                pil_renk = "darkred"
            
            # Popup içeriğini hazırla
            popup_content = f"""
            <div style="font-family: Arial, sans-serif; text-align: center; background-color: rgba(255,255,255,0.9); 
                        padding: 10px; border-radius: 5px; border: 1px solid {pil_renk};">
                <h4>{isim} ({konum['bolge']})</h4>
                <p><b>Pil Seviyesi:</b> <span style="color: {pil_renk}">%{enerji_seviyesi:.1f}</span> ({pil_durumu})</p>
                <p><b>Enerji Tüketimi:</b> <span style="color: {marker_renk}">%{enerji_tuketimi:.1f}</span></p>
                <p><b>Durum:</b> {'Aktif' if self.kaa_simulasyon.sensor_durumlari[sensor_id]['aktif'] else 'Pasif'}</p>
                <p><b>Hava Durumu Verileri:</b></p>
                <p>Sıcaklık: {self.tum_veriler[isim]['sicaklik']:.1f}°C</p>
                <p>Nem: {self.tum_veriler[isim]['nem']:.1f} g/m³</p>
                <p>Basınç: {self.tum_veriler[isim]['basinc']:.2f} bar</p>
                <p>pH: {self.tum_veriler[isim]['ph']:.2f}</p>
                <p><b>Konum:</b><br>
                Enlem: {konum['lat']:.6f}<br>
                Boylam: {konum['lon']:.6f}</p>
            </div>
            """
            
            # Sensör işaretçisini ekle
            folium.Marker(
                [konum['lat'], konum['lon']],
                popup=popup_content,
                icon=folium.Icon(color=marker_renk, icon='info-sign')
            ).add_to(m)
        
        # Lejant ekle
        legend_html = """
        <div style="position: fixed; bottom: 50px; right: 50px; z-index: 1000; background-color: white;
                     padding: 10px; border: 2px solid grey; border-radius: 5px">
        <h4 style='margin-top:0'><b>Harita Göstergeleri</b></h4>
        <div style='margin-bottom:10px'>
            <span style='background-color:green;padding:0 10px'>&nbsp;</span>
            <span style='margin-left:5px'>Kara Bölgeleri</span>
        </div>
        <div style='margin-bottom:10px'>
            <span style='background-color:blue;padding:0 10px'>&nbsp;</span>
            <span style='margin-left:5px'>Su Alanları</span>
        </div>
        <div style='margin-bottom:10px'>
            <span style='background-color:red;padding:0 10px'>&nbsp;</span>
            <span style='margin-left:5px'>Seçili Alan</span>
        </div>
        <h4><b>Enerji Tüketimi</b></h4>
        <div style='margin-bottom:5px'>
            <i class='fa fa-map-marker' style='color:darkred'></i>
            <span style='margin-left:5px'>90-100%: Çok Yüksek</span>
        </div>
        <div style='margin-bottom:5px'>
            <i class='fa fa-map-marker' style='color:red'></i>
            <span style='margin-left:5px'>70-89%: Yüksek</span>
        </div>
        <div style='margin-bottom:5px'>
            <i class='fa fa-map-marker' style='color:orange'></i>
            <span style='margin-left:5px'>45-69%: Normal</span>
        </div>
        <div style='margin-bottom:5px'>
            <i class='fa fa-map-marker' style='color:blue'></i>
            <span style='margin-left:5px'>20-44%: Düşük</span>
        </div>
        <div style='margin-bottom:5px'>
            <i class='fa fa-map-marker' style='color:green'></i>
            <span style='margin-left:5px'>0-19%: Minimum</span>
        </div>
        </div>
        """
        m.get_root().html.add_child(folium.Element(legend_html))
        
        # Haritayı HTML dosyası olarak kaydet
        self.harita_dosyasi = os.path.join(os.getcwd(), "ankara_harita.html")
        m.save(self.harita_dosyasi)
    
    def harita_goster(self):
        """Haritayı ayrı bir pencerede gösterir"""
        try:
            # Haritayı güncelle
            self.harita_olustur()
            
            # Haritayı webview ile göster
            if hasattr(self, 'window'):
                try:
                    self.window.destroy()
                except:
                    pass
            
            self.window = webview.create_window(
                'Ankara Sensör Ağı Haritası',
                html=open(self.harita_dosyasi, 'r', encoding='utf-8').read(),
                width=1024,
                height=768,
                resizable=True
            )
            webview.start()
            
        except Exception as e:
            print(f"Harita gösterme hatası: {e}")
            messagebox.showerror("Hata", f"Harita gösterilirken bir hata oluştu: {str(e)}")
    
    def hava_durumu_guncelle(self):
        try:
            # Sensör noktaları kontrolü
            if not self.sensor_noktalari:
                messagebox.showerror("Hata", "Önce sensörleri yerleştirmelisiniz!")
                return
                
            tum_veriler = {}
            toplam_sicaklik = 0
            toplam_nem = 0
            toplam_basinc = 0
            toplam_ph = 0
            aktif_sensor_sayisi = 0
            
            # Her sensör noktası için sıcaklık verilerini çek
            for isim, konum in self.sensor_noktalari.items():
                try:
                    url = f"http://api.openweathermap.org/data/2.5/weather?lat={konum['lat']}&lon={konum['lon']}&appid={self.api_key}&units=metric"
                    response = requests.get(url)
                    data = response.json()
                    
                    if response.status_code == 200:
                        sicaklik = data['main']['temp']
                        
                        # Rastgele değerler üret
                        nem = random.uniform(0, 950)  # 0-950 arası
                        basinc = random.uniform(-1, 1)  # -1 ile 1 bar arası
                        ph = random.uniform(0, 14)  # 0-14 pH arası
                        
                        tum_veriler[isim] = {
                            'sicaklik': sicaklik,
                            'nem': nem,
                            'basinc': basinc,
                            'ph': ph
                        }
                        
                        toplam_sicaklik += sicaklik
                        toplam_nem += nem
                        toplam_basinc += basinc
                        toplam_ph += ph
                        aktif_sensor_sayisi += 1
                        
                except Exception as e:
                    print(f"Sensör {isim} için veri çekme hatası: {e}")
                    continue
            
            if aktif_sensor_sayisi == 0:
                messagebox.showerror("Hata", "Hiç aktif sensör bulunamadı!")
                return
            
            # Verileri sakla
            self.tum_veriler = tum_veriler
            
            # Ortalama değerleri hesapla
            ort_sicaklik = toplam_sicaklik / aktif_sensor_sayisi
            ort_nem = toplam_nem / aktif_sensor_sayisi
            ort_basinc = toplam_basinc / aktif_sensor_sayisi
            ort_ph = toplam_ph / aktif_sensor_sayisi
            
            # Son değerleri sakla
            self.son_sicaklik = ort_sicaklik
            self.son_nem = ort_nem
            self.son_basinc = ort_basinc
            self.son_ph = ort_ph
            
            # Arayüzü güncelle
            self.sicaklik_label.config(text=f"Ortalama Sıcaklık: {ort_sicaklik:.1f}°C")
            self.nem_label.config(text=f"Ortalama Nem: {ort_nem:.1f} g/m³")
            self.basinc_label.config(text=f"Ortalama Basınç: {ort_basinc:.2f} bar")
            self.ruzgar_label.config(text=f"Ortalama pH: {ort_ph:.2f}")
            
            guncel_zaman = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
            self.guncelleme_label.config(text=f"Son Güncelleme: {guncel_zaman}")
            
            # Sensör detaylarını göster
            self.sensor_detaylarini_goster(tum_veriler)
            
            # Bulanık mantık sistemini çalıştır
            hava_durumu_verileri = {
                'nem': ort_nem,
                'basinc': ort_basinc,
                'ph': ort_ph
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
            
            # Ortalama enerji tüketimini hesapla
            aktif_sensorler = [node for node in self.kaa_simulasyon.ag.nodes() if self.kaa_simulasyon.sensor_durumlari[node]['aktif']]
            if aktif_sensorler:
                self.son_enerji_tuketimi = sum(self.kaa_simulasyon.sensor_durumlari[node]['enerji_seviyesi'] for node in aktif_sensorler) / len(aktif_sensorler)
            else:
                self.son_enerji_tuketimi = 0
            
            self.enerji_tuketim_label.config(text=f"Ortalama Enerji Seviyesi: {self.son_enerji_tuketimi:.2f}%")
            
            # Haritayı güncelle
            self.harita_olustur()
            
            messagebox.showinfo("Başarılı", "Hava durumu verileri başarıyla güncellendi!")
            
        except Exception as e:
            print(f"Hata oluştu: {e}")
            messagebox.showerror("Hata", f"Veri güncellenirken bir hata oluştu: {str(e)}")
    
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
            ttk.Label(grid_frame, text=f"{veri['nem']:.1f} g/m³").grid(row=2, column=1, padx=5, pady=2, sticky="w")
            
            ttk.Label(grid_frame, text="Basınç").grid(row=3, column=0, padx=5, pady=2, sticky="w")
            ttk.Label(grid_frame, text=f"{veri['basinc']:.2f} bar").grid(row=3, column=1, padx=5, pady=2, sticky="w")
            
            ttk.Label(grid_frame, text="pH").grid(row=4, column=0, padx=5, pady=2, sticky="w")
            ttk.Label(grid_frame, text=f"{veri['ph']:.2f}").grid(row=4, column=1, padx=5, pady=2, sticky="w")
        
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

    def bulanik_mantik_detaylari_goster(self):
        """Bulanık mantık detaylarını gösteren yeni pencere"""
        detay_pencere = tk.Toplevel(self.root)
        detay_pencere.title("Bulanık Mantık Sistem Detayları")
        detay_pencere.geometry("800x600")
        
        # Pencereyi ekranın ortasına konumlandır
        screen_width = detay_pencere.winfo_screenwidth()
        screen_height = detay_pencere.winfo_screenheight()
        x = (screen_width - 800) // 2
        y = (screen_height - 600) // 2
        detay_pencere.geometry(f"800x600+{x}+{y}")
        
        # Canvas ve scrollbar oluştur
        canvas = tk.Canvas(detay_pencere)
        scrollbar = ttk.Scrollbar(detay_pencere, orient="vertical", command=canvas.yview)
        
        # Frame oluştur
        scrollable_frame = ttk.Frame(canvas)
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Başlık
        ttk.Label(
            scrollable_frame,
            text="BULANIK MANTIK SİSTEM ANALİZİ",
            font=("Arial", 14, "bold")
        ).pack(pady=10)
        
        # Giriş değişkenleri
        giris_frame = ttk.LabelFrame(scrollable_frame, text="Giriş Değişkenleri")
        giris_frame.pack(pady=10, padx=5, fill="x")
        
        ttk.Label(giris_frame, text="Pil Seviyesi (0-100%):").pack(pady=5)
        ttk.Label(giris_frame, text="• Kritik: 0-30%").pack()
        ttk.Label(giris_frame, text="• Normal: 20-80%").pack()
        ttk.Label(giris_frame, text="• Yüksek: 70-100%").pack()
        
        ttk.Label(giris_frame, text="\nNem (0-950 g/m³):").pack(pady=5)
        ttk.Label(giris_frame, text="• Düşük: 0-300 g/m³").pack()
        ttk.Label(giris_frame, text="• Orta: 250-650 g/m³").pack()
        ttk.Label(giris_frame, text="• Yüksek: 600-950 g/m³").pack()
        
        ttk.Label(giris_frame, text="\nBasınç (-1 ile 1 bar):").pack(pady=5)
        ttk.Label(giris_frame, text="• Düşük: -1 ile -0.5 bar").pack()
        ttk.Label(giris_frame, text="• Normal: -0.4 ile 0.4 bar").pack()
        ttk.Label(giris_frame, text="• Yüksek: 0.5 ile 1 bar").pack()
        
        ttk.Label(giris_frame, text="\nToprak pH (0-14):").pack(pady=5)
        ttk.Label(giris_frame, text="• Asit: 0-6").pack()
        ttk.Label(giris_frame, text="• Nötr: 6-8").pack()
        ttk.Label(giris_frame, text="• Bazik: 8-14").pack()
        
        # Çıkış değişkeni
        cikis_frame = ttk.LabelFrame(scrollable_frame, text="Çıkış Değişkeni")
        cikis_frame.pack(pady=10, padx=5, fill="x")
        
        ttk.Label(cikis_frame, text="Enerji Tüketimi (%0-100):").pack(pady=5)
        ttk.Label(cikis_frame, text="• Minimum: 0-10%").pack()
        ttk.Label(cikis_frame, text="• Düşük: 20-25%").pack()
        ttk.Label(cikis_frame, text="• Normal: 45-50%").pack()
        ttk.Label(cikis_frame, text="• Yüksek: 70-80%").pack()
        ttk.Label(cikis_frame, text="• Çok Yüksek: 90%").pack()
        
        # Bulanık kurallar
        kural_frame = ttk.LabelFrame(scrollable_frame, text="Bulanık Mantık Kuralları")
        kural_frame.pack(pady=10, padx=5, fill="x")
        
        kurallar = [
            "1. EĞER pil kritik seviyede ise, enerji tüketimi çok yüksek (90%)",
            "2. EĞER pil normal VE pH nötr VE basınç normal VE nem normal İSE, enerji tüketimi orta (50%)",
            "3. EĞER pil yüksek VE pH nötr VE basınç normal VE nem normal İSE, enerji tüketimi düşük (20%)",
            "4. EĞER pH asidik VEYA bazik İSE, enerji tüketimi yüksek (70%)",
            "5. EĞER basınç çok düşük VEYA çok yüksek İSE, enerji tüketimi yüksek (75%)",
            "6. EĞER nem çok yüksek İSE, enerji tüketimi yüksek (80%)",
            "7. EĞER nem normal VE pH nötr İSE, enerji tüketimi normal (45%)",
            "8. EĞER tüm değerler optimal İSE, enerji tüketimi minimum (10%)"
        ]
        
        for kural in kurallar:
            ttk.Label(kural_frame, text=kural).pack(pady=2)
        
        # Mevcut durum
        durum_frame = ttk.LabelFrame(scrollable_frame, text="Mevcut Sistem Durumu")
        durum_frame.pack(pady=10, padx=5, fill="x")
        
        if hasattr(self, 'son_sicaklik'):
            ttk.Label(durum_frame, text=f"Sıcaklık: {self.son_sicaklik:.1f}°C").pack(pady=2)
            ttk.Label(durum_frame, text=f"Nem: {self.son_nem:.1f} g/m³").pack(pady=2)
            ttk.Label(durum_frame, text=f"Basınç: {self.son_basinc:.2f} bar").pack(pady=2)
            ttk.Label(durum_frame, text=f"pH: {self.son_ph:.2f}").pack(pady=2)
            ttk.Label(durum_frame, text=f"Hesaplanan Enerji Tüketimi: {self.son_enerji_tuketimi:.1f}%").pack(pady=2)
        else:
            ttk.Label(durum_frame, text="Henüz veri güncellenmedi").pack(pady=2)
        
        # Scrollbar'ı yerleştir
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        
        # Mouse wheel ile scroll yapabilme
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # Pencere kapatıldığında bind'ı kaldır
        def _on_closing():
            canvas.unbind_all("<MouseWheel>")
            detay_pencere.destroy()
        
        detay_pencere.protocol("WM_DELETE_WINDOW", _on_closing)

    def fis_dosyasi_sec(self):
        """MATLAB .fis dosyasını seçmek için dosya dialogu açar"""
        dosya_yolu = filedialog.askopenfilename(
            title="MATLAB FIS Dosyası Seç",
            filetypes=[("FIS files", "*.fis"), ("All files", "*.*")]
        )
        
        if dosya_yolu:
            if self.kaa_simulasyon.fis_dosyasi_yukle(dosya_yolu):
                messagebox.showinfo(
                    "Başarılı",
                    "MATLAB bulanık mantık sistemi başarıyla yüklendi!"
                )
            else:
                messagebox.showerror(
                    "Hata",
                    "FIS dosyası yüklenirken bir hata oluştu!"
                )

    def _on_mousewheel(self, event):
        self.main_canvas.yview_scroll(int(-1*(event.delta/120)), "units")

class KAASimulasyon:
    def __init__(self):
        self.ag = None
        self.sensor_durumlari = {}
        
        # MATLAB .fis dosyasından bulanık mantık sistemini yükle
        self.fis_dosyasi = None  # .fis dosyası yolu buraya gelecek
        
    def ag_olustur(self, sensor_sayisi):
        """Kablosuz algılayıcı ağın topolojisini oluşturur."""
        self.ag = nx.random_geometric_graph(sensor_sayisi, 0.3)
        
        # Sensörlerin başlangıç durumlarını ayarla
        for node in self.ag.nodes():
            self.sensor_durumlari[node] = {
                'enerji_seviyesi': random.uniform(0, 100),  # Rastgele pil seviyesi (0-100 arası)
                'aktif': True
            }
    
    def fis_dosyasi_yukle(self, dosya_yolu):
        """MATLAB'dan oluşturulan .fis dosyasını yükler"""
        if os.path.exists(dosya_yolu):
            self.fis_dosyasi = dosya_yolu
            return True
        return False
    
    def bulanik_mantik_kurallari(self, pil_seviyesi, nem, basinc, ph):
        """Bulanık mantık kurallarını uygular ve enerji tüketimini hesaplar"""
        try:
            # Giriş değerlerini sayısal değerlere dönüştür
            pil_seviyesi_deger = float(pil_seviyesi)
            nem_deger = float(nem)
            basinc_deger = float(basinc)
            ph_deger = float(ph)
            
            # Pil seviyesi için bulanık kümeler
            pil_seviyesi_var = ctrl.Antecedent(np.arange(0, 101, 1), 'pil_seviyesi')
            pil_seviyesi_var['cok_kotu'] = fuzz.trapmf(pil_seviyesi_var.universe, [0, 0, 20, 20])
            pil_seviyesi_var['kotu'] = fuzz.trapmf(pil_seviyesi_var.universe, [20, 21, 40, 40])
            pil_seviyesi_var['orta'] = fuzz.trapmf(pil_seviyesi_var.universe, [40, 41, 60, 60])
            pil_seviyesi_var['iyi'] = fuzz.trapmf(pil_seviyesi_var.universe, [60, 61, 80, 80])
            pil_seviyesi_var['cok_iyi'] = fuzz.trapmf(pil_seviyesi_var.universe, [80, 81, 100, 100])

            # Nem için bulanık kümeler
            nem_var = ctrl.Antecedent(np.arange(0, 951, 1), 'nem')
            nem_var['kuru_toprak'] = fuzz.trapmf(nem_var.universe, [0, 0, 250, 300])
            nem_var['nemli_toprak'] = fuzz.trimf(nem_var.universe, [300, 500, 700])
            nem_var['suda'] = fuzz.trapmf(nem_var.universe, [700, 800, 950, 950])

            # Basınç için bulanık kümeler
            basinc_var = ctrl.Antecedent(np.arange(-1, 1.1, 0.1), 'basinc')
            basinc_var['dusuk'] = fuzz.trapmf(basinc_var.universe, [-1, -1, -0.5, -0.4])
            basinc_var['normal'] = fuzz.trimf(basinc_var.universe, [-0.4, 0, 0.4])
            basinc_var['yuksek'] = fuzz.trapmf(basinc_var.universe, [0.4, 0.5, 1, 1])

            # pH için bulanık kümeler
            ph_var = ctrl.Antecedent(np.arange(0, 14.1, 0.1), 'ph')
            ph_var['asidik'] = fuzz.trapmf(ph_var.universe, [0, 0, 6.8, 6.9])
            ph_var['notr'] = fuzz.trimf(ph_var.universe, [6.9, 7, 7.1])
            ph_var['bazik'] = fuzz.trapmf(ph_var.universe, [7.1, 7.2, 14, 14])

            # Enerji tüketimi için bulanık kümeler
            enerji_tuketimi = ctrl.Consequent(np.arange(0, 101, 1), 'enerji_tuketimi')
            enerji_tuketimi['minimum'] = fuzz.trapmf(enerji_tuketimi.universe, [0, 0, 20, 20])
            enerji_tuketimi['dusuk'] = fuzz.trapmf(enerji_tuketimi.universe, [20, 21, 40, 40])
            enerji_tuketimi['normal'] = fuzz.trapmf(enerji_tuketimi.universe, [40, 41, 60, 60])
            enerji_tuketimi['yuksek'] = fuzz.trapmf(enerji_tuketimi.universe, [60, 61, 80, 80])
            enerji_tuketimi['cok_yuksek'] = fuzz.trapmf(enerji_tuketimi.universe, [80, 81, 100, 100])

            # Bulanık kurallar
            # Pil seviyesi kuralları
            kural1 = ctrl.Rule(pil_seviyesi_var['cok_kotu'], enerji_tuketimi['cok_yuksek'])
            kural2 = ctrl.Rule(pil_seviyesi_var['kotu'], enerji_tuketimi['yuksek'])
            kural3 = ctrl.Rule(pil_seviyesi_var['orta'], enerji_tuketimi['normal'])
            kural4 = ctrl.Rule(pil_seviyesi_var['iyi'], enerji_tuketimi['dusuk'])
            kural5 = ctrl.Rule(pil_seviyesi_var['cok_iyi'], enerji_tuketimi['minimum'])
            
            # Nem kuralları
            kural6 = ctrl.Rule(nem_var['kuru_toprak'], enerji_tuketimi['normal'])
            kural7 = ctrl.Rule(nem_var['nemli_toprak'], enerji_tuketimi['dusuk'])
            kural8 = ctrl.Rule(nem_var['suda'], enerji_tuketimi['yuksek'])
            
            # pH kuralları
            kural9 = ctrl.Rule(ph_var['asidik'], enerji_tuketimi['yuksek'])
            kural10 = ctrl.Rule(ph_var['notr'], enerji_tuketimi['dusuk'])
            kural11 = ctrl.Rule(ph_var['bazik'], enerji_tuketimi['yuksek'])
            
            # Basınç kuralları
            kural12 = ctrl.Rule(basinc_var['dusuk'], enerji_tuketimi['yuksek'])
            kural13 = ctrl.Rule(basinc_var['normal'], enerji_tuketimi['dusuk'])
            kural14 = ctrl.Rule(basinc_var['yuksek'], enerji_tuketimi['yuksek'])
            
            # Kombinasyon kuralları
            # İdeal durum: Tüm koşullar optimal
            kural15 = ctrl.Rule(
                pil_seviyesi_var['cok_iyi'] & 
                nem_var['nemli_toprak'] & 
                basinc_var['normal'] & 
                ph_var['notr'], 
                enerji_tuketimi['minimum']
            )
            
            # Kritik durum: Pil düşük ve pH uygun değil
            kural16 = ctrl.Rule(
                (pil_seviyesi_var['cok_kotu'] | pil_seviyesi_var['kotu']) & 
                (ph_var['asidik'] | ph_var['bazik']), 
                enerji_tuketimi['cok_yuksek']
            )
            
            # Yüksek enerji tüketimi: Nemli ortam ve yüksek basınç
            kural17 = ctrl.Rule(
                nem_var['suda'] & basinc_var['yuksek'], 
                enerji_tuketimi['yuksek']
            )
            
            # Normal durum: Orta seviye pil ve normal koşullar
            kural18 = ctrl.Rule(
                pil_seviyesi_var['orta'] & 
                nem_var['nemli_toprak'] & 
                basinc_var['normal'] & 
                ph_var['notr'], 
                enerji_tuketimi['normal']
            )
            
            # Düşük enerji tüketimi: İyi pil ve optimal koşullar
            kural19 = ctrl.Rule(
                (pil_seviyesi_var['iyi'] | pil_seviyesi_var['cok_iyi']) & 
                nem_var['nemli_toprak'] & 
                basinc_var['normal'] & 
                ph_var['notr'], 
                enerji_tuketimi['dusuk']
            )
            
            # Kontrol sistemini oluştur
            enerji_tuketimi_ctrl = ctrl.ControlSystem([
                kural1, kural2, kural3, kural4, kural5,  # Pil seviyesi kuralları
                kural6, kural7, kural8,                   # Nem kuralları
                kural9, kural10, kural11,                 # pH kuralları
                kural12, kural13, kural14,                # Basınç kuralları
                kural15,                                  # İdeal durum
                kural16,                                  # Kritik durum
                kural17,                                  # Yüksek tüketim
                kural18,                                  # Normal durum
                kural19                                   # Düşük tüketim
            ])
            
            # Kontrolcü oluştur
            enerji_tuketimi_sim = ctrl.ControlSystemSimulation(enerji_tuketimi_ctrl)
            
            # Giriş değerlerini kontrolcüye aktar
            enerji_tuketimi_sim.input['pil_seviyesi'] = pil_seviyesi_deger
            enerji_tuketimi_sim.input['nem'] = nem_deger
            enerji_tuketimi_sim.input['basinc'] = basinc_deger
            enerji_tuketimi_sim.input['ph'] = ph_deger
            
            # Kontrolcüyü çalıştır
            enerji_tuketimi_sim.compute()
            
            # Sonucu al
            enerji_tuketimi_sonuc = enerji_tuketimi_sim.output['enerji_tuketimi']
            return min(100, max(0, enerji_tuketimi_sonuc))  # 0-100 arasında sınırla
            
        except Exception as e:
            print(f"Bulanık mantık hesaplama hatası: {e}")
            return 50  # Hata durumunda varsayılan değer
    
    def enerji_hesapla(self, hava_durumu_verileri):
        """Sensör düğümlerinin enerji tüketimini hesaplar."""
        for node in self.ag.nodes():
            if self.sensor_durumlari[node]['aktif']:
                # Bulanık mantık ile enerji tüketimini hesapla
                enerji_tuketimi = self.bulanik_mantik_kurallari(
                    self.sensor_durumlari[node]['enerji_seviyesi'],
                    hava_durumu_verileri['nem'],
                    hava_durumu_verileri['basinc'],
                    hava_durumu_verileri['ph']
                )
                
                # Sensörün enerji seviyesini güncelle
                self.sensor_durumlari[node]['enerji_seviyesi'] -= (enerji_tuketimi / 100)
                
                # Enerji seviyesini 0-100 arasında sınırla
                self.sensor_durumlari[node]['enerji_seviyesi'] = max(0, min(100, self.sensor_durumlari[node]['enerji_seviyesi']))
                
                # Enerji seviyesi kritik seviyenin altına düşerse sensörü devre dışı bırak
                if self.sensor_durumlari[node]['enerji_seviyesi'] < 10:
                    self.sensor_durumlari[node]['aktif'] = False
    
    def senkronizasyon_protokolu(self):
        """Senkronizasyon protokolünü uygular."""
        aktif_sensorler = [node for node in self.ag.nodes() if self.sensor_durumlari[node]['aktif']]
        
        if not aktif_sensorler:
            return "Aktif sensör kalmadı!"
        
        koordinator = max(aktif_sensorler, 
                         key=lambda x: self.sensor_durumlari[x]['enerji_seviyesi'])
        
        ortalama_enerji = np.mean([self.sensor_durumlari[node]['enerji_seviyesi'] 
                                 for node in aktif_sensorler]) if aktif_sensorler else 0
        
        return {
            'koordinator': koordinator,
            'aktif_sensor_sayisi': len(aktif_sensorler),
            'ortalama_enerji': ortalama_enerji
        }

    def hesapla_sicaklik_uyelik(self, sicaklik):
        """Sıcaklık için üyelik derecelerini hesaplar"""
        if self.fis_dosyasi is None:
            # Varsayılan değerler
            return {
                'dusuk': 0.33,
                'orta': 0.33,
                'yuksek': 0.34
            }
        return {
            'dusuk': 0.33,
            'orta': 0.33,
            'yuksek': 0.34
        }
    
    def hesapla_nem_uyelik(self, nem):
        """Nem için üyelik derecelerini hesaplar"""
        if self.fis_dosyasi is None:
            # Varsayılan değerler
            return {
                'dusuk': 0.33,
                'orta': 0.33,
                'yuksek': 0.34
            }
        return {
            'dusuk': 0.33,
            'orta': 0.33,
            'yuksek': 0.34
        }
    
    def hesapla_ph_uyelik(self, ph):
        """pH için üyelik derecelerini hesaplar"""
        if self.fis_dosyasi is None:
            # Varsayılan değerler
            return {
                'asit': 0.33,
                'notr': 0.33,
                'bazik': 0.34
            }
        return {
            'asit': 0.33,
            'notr': 0.33,
            'bazik': 0.34
        }

def main():
    root = tk.Tk()
    app = HavaDurumuArayuz(root)
    root.mainloop()

if __name__ == "__main__":
    main() 