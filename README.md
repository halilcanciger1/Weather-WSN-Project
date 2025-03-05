# Kablosuz Algılayıcı Ağlar için Hava Durumu Tabanlı Enerji Verimli Senkronizasyon Protokolü

Bu proje, kablosuz algılayıcı ağların (KAA) enerji verimliliğini artırmak için bulanık mantık tabanlı bir yaklaşım kullanmaktadır. Sistem, hava durumu verilerini kullanarak sensörlerin enerji tüketimini optimize eder.

## Özellikler

- Gerçek zamanlı hava durumu verisi takibi
- Bulanık mantık tabanlı enerji tüketimi optimizasyonu
- İnteraktif sensör ağı haritası
- Detaylı sensör durumu izleme
- Enerji tüketimi tahminleme

## Gereksinimler

Projeyi çalıştırmak için gerekli kütüphaneler requirements.txt dosyasında listelenmiştir. Kurulum için:

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

- Sıcaklık (0-40°C)
- Nem (%0-100)
- Rüzgar Hızı (0-20 m/s)

## Lisans

Bu proje MIT lisansı altında lisanslanmıştır. 