# Kablosuz Algılayıcı Ağlar için Hava Durumu Tabanlı Enerji Verimli Senkronizasyon Protokolü

Bu proje, kablosuz algılayıcı ağların (KAA) enerji verimliliğini artırmak için bulanık mantık tabanlı bir yaklaşım kullanmaktadır. Sistem, hava durumu verilerini kullanarak sensörlerin enerji tüketimini optimize eder.

## Özellikler

* Gerçek zamanlı hava durumu verisi takibi
* Bulanık mantık tabanlı enerji tüketimi optimizasyonu
* İnteraktif sensör ağı haritası
* Detaylı sensör durumu izleme
* Enerji tüketimi tahminleme
* Özelleştirilebilir sensör ağı boyutu
* Scrollbar destekli kullanıcı arayüzü

## Gereksinimler

Projeyi çalıştırmak için gerekli kütüphaneler:
* Python 3.x
* tkinter
* requests
* numpy
* matplotlib
* scikit-fuzzy

Kurulum için:
```bash
pip install -r requirements.txt
```

## Kullanım

1. OpenWeatherMap API anahtarınızı `api_key` değişkenine atayın
2. Uygulamayı çalıştırın:
```bash
python BilgisayarAglari_proje.py
```

## Bulanık Mantık Sistemi

Uygulama, aşağıdaki parametreleri kullanarak bulanık mantık ile enerji tüketimini hesaplar:

### Pil Seviyesi (0-100%)
* Çok Kötü: 0-20%
* Kötü: 21-40%
* Orta: 41-60%
* İyi: 61-80%
* Çok İyi: 81-100%

### Nem Seviyesi (0-950 g/m³)
* Kuru Toprak: 0-300 g/m³
* Nemli Toprak: 300-700 g/m³
* Suda: 700-950 g/m³

### pH Seviyesi (0-14)
* Asidik: 0-6.9
* Nötr: 7.0
* Bazik: 7.1-14

### Basınç Seviyesi (-1.0 ile 1.0 bar)
* Düşük: -1.0 ile -0.4 bar
* Normal: -0.4 ile 0.4 bar
* Yüksek: 0.4 ile 1.0 bar

### Enerji Tüketimi Seviyeleri
* Minimum (0-20%): En düşük enerji tüketimi, optimal çalışma koşulları
* Düşük (21-40%): Verimli çalışma, normal koşullar altında enerji tasarrufu
* Normal (41-60%): Standart çalışma koşulları, ortalama enerji tüketimi
* Yüksek (61-80%): Zorlu koşullar altında artan enerji tüketimi
* Çok Yüksek (81-100%): Kritik durum, maksimum enerji tüketimi

## Arayüz Özellikleri

* Sensör yerleştirme ve konfigürasyon
* Gerçek zamanlı hava durumu verisi güncelleme
* İnteraktif harita görüntüleme
* Detaylı sensör bilgileri
* Enerji tüketimi renk kodları
* Üyelik fonksiyonları görüntüleme
* Scrollbar destekli kullanıcı arayüzü

## Lisans

Bu proje MIT lisansı altında lisanslanmıştır. 