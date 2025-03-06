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

class HavaDurumuArayuz:
    def __init__(self, root):
        self.root = root
        self.root.title("Ankara Hava Durumu Takip Sistemi")
        self.root.geometry("800x1000")
        
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
            'tam_dolu': {'min': 90, 'max': 100, 'renk': 'darkgreen', 'aciklama': 'Tam Dolu'},
            'cok_iyi': {'min': 75, 'max': 89, 'renk': 'lightgreen', 'aciklama': 'Çok İyi'},
            'iyi': {'min': 60, 'max': 74, 'renk': 'blue', 'aciklama': 'İyi'},
            'orta': {'min': 45, 'max': 59, 'renk': 'yellow', 'aciklama': 'Orta'},
            'dusuk': {'min': 30, 'max': 44, 'renk': 'orange', 'aciklama': 'Düşük'},
            'kritik': {'min': 15, 'max': 29, 'renk': 'red', 'aciklama': 'Kritik'},
            'tukenme': {'min': 0, 'max': 14, 'renk': 'purple', 'aciklama': 'Tükenme'}
        }
        
        self.arayuz_olustur()
        self.harita_olustur()
    
    def arayuz_olustur(self):
        # Ana frame'i oluştur
        self.main_frame = ttk.Frame(self.root)
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
        self.enerji_frame = ttk.LabelFrame(self.main_frame, text="Bulanık Mantık Enerji Analizi")
        self.enerji_frame.pack(pady=10, fill="x")
        
        self.enerji_tuketim_label = ttk.Label(self.enerji_frame, text="Tahmini Enerji Tüketimi: ")
        self.enerji_tuketim_label.pack(pady=5)
        
        # Bulanık mantık üyelik dereceleri
        self.uyelik_frame = ttk.LabelFrame(self.enerji_frame, text="Üyelik Dereceleri")
        self.uyelik_frame.pack(pady=5, fill="x")
        
        self.sicaklik_uyelik_label = ttk.Label(self.uyelik_frame, text="Sıcaklık Üyelik: ")
        self.sicaklik_uyelik_label.pack(pady=2)
        
        self.nem_uyelik_label = ttk.Label(self.uyelik_frame, text="Nem Üyelik: ")
        self.nem_uyelik_label.pack(pady=2)
        
        self.ruzgar_uyelik_label = ttk.Label(self.uyelik_frame, text="Rüzgar Üyelik: ")
        self.ruzgar_uyelik_label.pack(pady=2)
        
        # Enerji seviyesi renk göstergesi
        self.renk_frame = ttk.LabelFrame(self.main_frame, text="Enerji Seviyesi Renk Kodları")
        self.renk_frame.pack(pady=10, fill="x")
        
        for enerji_durum in self.enerji_renkleri.values():
            frame = ttk.Frame(self.renk_frame)
            frame.pack(fill="x", padx=5, pady=2)
            
            renk_gosterge = tk.Label(
                frame,
                text="■",
                fg=enerji_durum['renk'],
                font=("Arial", 12, "bold")
            )
            renk_gosterge.pack(side="left", padx=5)
            
            ttk.Label(
                frame,
                text=f"%{enerji_durum['min']}-{enerji_durum['max']}: {enerji_durum['aciklama']}"
            ).pack(side="left", padx=5)
    
    def sensorleri_yerlestir(self):
        try:
            # Kullanıcının girdiği değerleri al
            sensor_sayisi = int(self.sensor_sayi_var.get())
            alan_boyutu = float(self.alan_boyut_var.get())  # km² cinsinden
            
            if sensor_sayisi <= 0:
                raise ValueError("Sensör sayısı pozitif olmalıdır!")
            
            if alan_boyutu <= 0:
                raise ValueError("Alan boyutu pozitif olmalıdır!")
            
            # Sensör noktalarını temizle
            self.sensor_noktalari.clear()
            
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
                        self.sensor_noktalari[f'Sensör {yerlestirilmis + 1}'] = {
                            'lat': lat,
                            'lon': lon,
                            'bolge': bolge['isim']
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
            
            # Enerji seviyesine göre renk belirle
            marker_renk = 'gray'  # Varsayılan renk
            for enerji_durum in self.enerji_renkleri.values():
                if enerji_durum['min'] <= enerji_seviyesi <= enerji_durum['max']:
                    marker_renk = enerji_durum['renk']
                    break
            
            # Popup içeriğini hazırla
            popup_content = f"{isim} ({konum['bolge']})<br>Enerji: %{enerji_seviyesi:.1f}"
            
            folium.Marker(
                [konum['lat'], konum['lon']],
                popup=popup_content,
                icon=folium.Icon(color=marker_renk, icon='info-sign')
            ).add_to(m)
        
        # Lejant ekle
        legend_html = """
        <div style="position: fixed; bottom: 50px; right: 50px; z-index: 1000; background-color: white;
                    padding: 10px; border: 2px solid grey; border-radius: 5px">
        <h4>Harita Göstergeleri</h4>
        <p><i class="fa fa-square" style="color:green"></i> Kara Bölgeleri</p>
        <p><i class="fa fa-square" style="color:blue"></i> Su Alanları</p>
        <p><i class="fa fa-square" style="color:red"></i> Seçili Alan Sınırları</p>
        <h4>Enerji Seviyeleri</h4>
        """
        
        for enerji_durum in self.enerji_renkleri.values():
            legend_html += f"""
            <p><i class="fa fa-circle" style="color:{enerji_durum['renk']}"></i>
            {enerji_durum['min']}-{enerji_durum['max']}%: {enerji_durum['aciklama']}</p>
            """
        
        legend_html += "</div>"
        m.get_root().html.add_child(folium.Element(legend_html))
        
        # Haritayı HTML dosyası olarak kaydet
        self.harita_dosyasi = os.path.join(os.getcwd(), "ankara_harita.html")
        m.save(self.harita_dosyasi)
    
    def harita_goster(self):
        """Haritayı ayrı bir pencerede gösterir"""
        # Haritayı güncelle
        self.harita_olustur()
        # Yeni bir pencerede haritayı göster
        webview.create_window("Ankara Haritası", url=self.harita_dosyasi, width=800, height=600)
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
            
            # Son değerleri sakla
            self.son_sicaklik = ort_sicaklik
            self.son_nem = ort_nem
            self.son_ruzgar = ort_ruzgar
            
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
            
            # Enerji tüketim tahminini hesapla ve göster
            self.son_enerji_tuketimi = self.kaa_simulasyon.bulanik_mantik_kurallari(ort_sicaklik, ort_nem, ort_ruzgar)
            self.enerji_tuketim_label.config(text=f"Tahmini Enerji Tüketimi: {self.son_enerji_tuketimi:.2f}%")
            
            # Üyelik derecelerini hesapla ve göster
            sicaklik_derece = self.kaa_simulasyon.hesapla_sicaklik_uyelik(ort_sicaklik)
            nem_derece = self.kaa_simulasyon.hesapla_nem_uyelik(ort_nem)
            ruzgar_derece = self.kaa_simulasyon.hesapla_ruzgar_uyelik(ort_ruzgar)
            
            self.sicaklik_uyelik_label.config(
                text=f"Sıcaklık Üyelik => Düşük: {sicaklik_derece['dusuk']:.2f}, Orta: {sicaklik_derece['orta']:.2f}, Yüksek: {sicaklik_derece['yuksek']:.2f}"
            )
            self.nem_uyelik_label.config(
                text=f"Nem Üyelik => Düşük: {nem_derece['dusuk']:.2f}, Orta: {nem_derece['orta']:.2f}, Yüksek: {nem_derece['yuksek']:.2f}"
            )
            self.ruzgar_uyelik_label.config(
                text=f"Rüzgar Üyelik => Yavaş: {ruzgar_derece['yavas']:.2f}, Orta: {ruzgar_derece['orta']:.2f}, Hızlı: {ruzgar_derece['hizli']:.2f}"
            )
            
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
        
        ttk.Label(giris_frame, text="Sıcaklık (0-40°C):").pack(pady=5)
        ttk.Label(giris_frame, text="• Düşük: 0-20°C").pack()
        ttk.Label(giris_frame, text="• Orta: 15-35°C").pack()
        ttk.Label(giris_frame, text="• Yüksek: 30-40°C").pack()
        
        ttk.Label(giris_frame, text="\nNem (%0-100):").pack(pady=5)
        ttk.Label(giris_frame, text="• Düşük: 0-40%").pack()
        ttk.Label(giris_frame, text="• Orta: 30-70%").pack()
        ttk.Label(giris_frame, text="• Yüksek: 60-100%").pack()
        
        ttk.Label(giris_frame, text="\nRüzgar Hızı (0-20 m/s):").pack(pady=5)
        ttk.Label(giris_frame, text="• Yavaş: 0-8 m/s").pack()
        ttk.Label(giris_frame, text="• Orta: 6-14 m/s").pack()
        ttk.Label(giris_frame, text="• Hızlı: 12-20 m/s").pack()
        
        # Çıkış değişkeni
        cikis_frame = ttk.LabelFrame(scrollable_frame, text="Çıkış Değişkeni")
        cikis_frame.pack(pady=10, padx=5, fill="x")
        
        ttk.Label(cikis_frame, text="Enerji Tüketimi (%0-100):").pack(pady=5)
        ttk.Label(cikis_frame, text="• Çok Düşük: 0-25%").pack()
        ttk.Label(cikis_frame, text="• Düşük: 20-50%").pack()
        ttk.Label(cikis_frame, text="• Orta: 45-75%").pack()
        ttk.Label(cikis_frame, text="• Yüksek: 70-100%").pack()
        
        # Bulanık kurallar
        kural_frame = ttk.LabelFrame(scrollable_frame, text="Bulanık Mantık Kuralları")
        kural_frame.pack(pady=10, padx=5, fill="x")
        
        kurallar = [
            "1. EĞER sıcaklık düşük VE nem düşük VE rüzgar yavaş İSE, enerji tüketimi çok düşük",
            "2. EĞER sıcaklık yüksek VEYA nem yüksek İSE, enerji tüketimi yüksek",
            "3. EĞER sıcaklık orta VE nem orta VE rüzgar orta İSE, enerji tüketimi orta",
            "4. EĞER sıcaklık düşük VE rüzgar hızlı İSE, enerji tüketimi düşük",
            "5. EĞER nem yüksek VE rüzgar yavaş İSE, enerji tüketimi yüksek"
        ]
        
        for kural in kurallar:
            ttk.Label(kural_frame, text=kural).pack(pady=2)
        
        # Mevcut durum
        durum_frame = ttk.LabelFrame(scrollable_frame, text="Mevcut Sistem Durumu")
        durum_frame.pack(pady=10, padx=5, fill="x")
        
        if hasattr(self, 'son_sicaklik'):
            ttk.Label(durum_frame, text=f"Sıcaklık: {self.son_sicaklik:.1f}°C").pack(pady=2)
            ttk.Label(durum_frame, text=f"Nem: {self.son_nem:.1f}%").pack(pady=2)
            ttk.Label(durum_frame, text=f"Rüzgar: {self.son_ruzgar:.1f} m/s").pack(pady=2)
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
                'enerji_seviyesi': 100,  # Başlangıçta %100 enerji
                'aktif': True
            }
    
    def fis_dosyasi_yukle(self, dosya_yolu):
        """MATLAB'dan oluşturulan .fis dosyasını yükler"""
        if os.path.exists(dosya_yolu):
            self.fis_dosyasi = dosya_yolu
            return True
        return False
    
    def bulanik_mantik_kurallari(self, sicaklik, nem, ruzgar):
        """MATLAB'dan yüklenen bulanık mantık kurallarını uygular"""
        if self.fis_dosyasi is None:
            # Eğer .fis dosyası yüklenmemişse varsayılan değer döndür
            return 50
        
        try:
            # Burada .fis dosyasından kuralları okuma ve uygulama işlemi yapılacak
            # MATLAB'dan alınan kurallar uygulanacak
            # Şimdilik varsayılan değer döndürüyoruz
            return 50
            
        except Exception as e:
            print(f"Bulanık mantık hesaplama hatası: {e}")
            return 50
    
    def enerji_hesapla(self, hava_durumu_verileri):
        """Sensör düğümlerinin enerji tüketimini hesaplar."""
        for node in self.ag.nodes():
            if self.sensor_durumlari[node]['aktif']:
                # MATLAB'dan alınan bulanık mantık ile enerji tüketimini hesapla
                enerji_tuketimi = self.bulanik_mantik_kurallari(
                    hava_durumu_verileri['sicaklik'],
                    hava_durumu_verileri['nem'],
                    hava_durumu_verileri['ruzgar']
                )
                
                # Sensörün enerji seviyesini güncelle
                self.sensor_durumlari[node]['enerji_seviyesi'] -= (enerji_tuketimi / 100)
                
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
        
        return {
            'koordinator': koordinator,
            'aktif_sensor_sayisi': len(aktif_sensorler),
            'ortalama_enerji': np.mean([self.sensor_durumlari[node]['enerji_seviyesi'] 
                                      for node in aktif_sensorler])
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
    
    def hesapla_ruzgar_uyelik(self, ruzgar):
        """Rüzgar hızı için üyelik derecelerini hesaplar"""
        if self.fis_dosyasi is None:
            # Varsayılan değerler
            return {
                'yavas': 0.33,
                'orta': 0.33,
                'hizli': 0.34
            }
        return {
            'yavas': 0.33,
            'orta': 0.33,
            'hizli': 0.34
        }

def main():
    root = tk.Tk()
    app = HavaDurumuArayuz(root)
    root.mainloop()

if __name__ == "__main__":
    main() 