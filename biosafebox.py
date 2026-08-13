import time
import threading
import json
import os
import random
from datetime import datetime

# --- YAPILANDIRMA ---
VERI_DOSYASI = "kutu_verisi.json"
OFFLINE_KUYRUK_DOSYASI = "offline_kuyruk.json"

# --- STRATEJİ: KİMLİK DOĞRULAMA ---
class KimlikDogrulama:
    def dogrula(self): raise NotImplementedError

class YuzTanimaDogrulama(KimlikDogrulama):
    def dogrula(self):
        print("🔍 [SİSTEM] Yüz taraması yapılıyor...")
        return random.choice([True, False]) # Simülasyon

# --- İLAÇ SINIFI ---
class Ilac:
    def __init__(self, isim, doz, verilecek_saat, stok_miktari, kritik_stok_siniri, etki_kayip_suresi_dk, tolerans_gec_dk, **kwargs):
        self.isim = isim
        self.doz = doz
        self.verilecek_saat = verilecek_saat
        self.stok_miktari = stok_miktari
        self.kritik_stok_siniri = kritik_stok_siniri
        self.etki_kayip_suresi_dk = etki_kayip_suresi_dk
        self.tolerans_gec_dk = tolerans_gec_dk
        self.bozuldu_mu = kwargs.get('bozuldu_mu', False)
        self.alindi_mi = False
        self.islem_goruyor_mu = False

    def to_dict(self):
        return self.__dict__

# --- AKILLI KUTU SİSTEMİ ---
class AkilliKutuSistemi:
    def __init__(self, dogrulama_yontemi):
        self.dogrulama_yontemi = dogrulama_yontemi
        self.ilac_listesi = []
        self.istatistikler = {"basarili_alim": 0, "cope_atilan": 0}
        self.internet_baglantisi = True
        self._verileri_yukle()
        threading.Thread(target=self._ag_kuyrugunu_islet, daemon=True).start()

    def _verileri_yukle(self):
        if os.path.exists(VERI_DOSYASI):
            with open(VERI_DOSYASI, "r") as f:
                data = json.load(f)
                self.ilac_listesi = [Ilac(**i) for i in data.get("ilac_listesi", [])]
                self.istatistikler = data.get("istatistikler", self.istatistikler)

    def _verileri_kaydet(self):
        with open(VERI_DOSYASI, "w") as f:
            json.dump({"ilac_listesi": [i.to_dict() for i in self.ilac_listesi], "istatistikler": self.istatistikler}, f)

    def otomasyon_merkezini_bilgilendir(self, baslik, mesaj):
        if self.internet_baglantisi:
            print(f"\n🌐 [BULUT] {baslik}: {mesaj}")
        else:
            self._cevrimdisi_kuyruga_yaz(f"[{baslik}] {mesaj}")

    def _cevrimdisi_kuyruga_yaz(self, mesaj):
        kuyruk = []
        if os.path.exists(OFFLINE_KUYRUK_DOSYASI):
            with open(OFFLINE_KUYRUK_DOSYASI, "r") as f: kuyruk = json.load(f)
        kuyruk.append({"zaman": str(datetime.now()), "mesaj": mesaj})
        with open(OFFLINE_KUYRUK_DOSYASI, "w") as f: json.dump(kuyruk, f)

    def _ag_kuyrugunu_islet(self):
        while True:
            if self.internet_baglantisi and os.path.exists(OFFLINE_KUYRUK_DOSYASI):
                print("📶 [SİSTEM] Kuyruk buluta aktarılıyor...")
                os.remove(OFFLINE_KUYRUK_DOSYASI)
            time.sleep(10)

    # --- PİVOT NOKTASI: TETİKLEMELİ ÇALIŞMA ---
    def ir_sensoru_tetiklendi(self, ilac):
        """PIR sensörü hareketi algıladı, sistem uyanıyor."""
        print(f"\n💡 [PIR SENSÖRÜ] Hareket algılandı! {ilac.isim} için doğrulama başlıyor...")
        if self.dogrulama_yontemi.dogrula():
            self._ilac_teslim_et(ilac)
        else:
            print("❌ Doğrulama başarısız! İlaç kilitlendi.")

    def _ilac_teslim_et(self, ilac):
        print(f"✅ {ilac.isim} teslim edildi.")
        ilac.alindi_mi = True
        self.istatistikler["basarili_alim"] += 1
        self.ilac_listesi.remove(ilac)
        self._verileri_kaydet()

    def hasta_uyum_raporu_olustur(self):
        a = self.istatistikler["basarili_alim"]
        c = self.istatistikler["cope_atilan"]
        skor = (a / (a + c) * 100) if (a + c) > 0 else 0
        print(f"\n📊 [RAPOR] Hasta Uyum Skoru: %{skor:.1f}")

# --- TEST SENARYOSU ---
yuz_tanima = YuzTanimaDogrulama()
kutu = AkilliKutuSistemi(yuz_tanima)

# Örnek ilaç
ilac = Ilac("Tansiyon Hapı", "1 Tablet", "09:00", 10, 2, 5, 2)
kutu.ilac_listesi.append(ilac)

# PIR sensörü tetiklendiğinde süreç başlar
kutu.ir_sensoru_tetiklendi(ilac)
kutu.hasta_uyum_raporu_olustur()
