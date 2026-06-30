import streamlit as st
import sqlite3
import pandas as pd

# Sayfa ayarları
st.set_page_config(page_title="Fikir Seçim Uygulaması", layout="wide")

# Veritabanı bağlantısı ve tablo kurulumu
conn = sqlite3.connect('fikir_oylama.db', check_same_thread=False)
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS fikirler (isim TEXT UNIQUE)''')
c.execute('''CREATE TABLE IF NOT EXISTS oylar 
             (kullanici TEXT, fikir TEXT, teknik INTEGER, is_modeli INTEGER, sure INTEGER, yenilik INTEGER,
              UNIQUE(kullanici, fikir) ON CONFLICT REPLACE)''')
conn.commit()


# Yardımcı Fonksiyonlar
def fikir_ekle(isim):
    try:
        c.execute("INSERT INTO fikirler (isim) VALUES (?)", (isim,))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False


def fikirleri_getir():
    c.execute("SELECT isim FROM fikirler")
    return [row[0] for row in c.fetchall()]


def oy_kaydet(kullanici, fikir, teknik, is_modeli, sure, yenilik):
    c.execute('''INSERT INTO oylar (kullanici, fikir, teknik, is_modeli, sure, yenilik)
                 VALUES (?, ?, ?, ?, ?, ?)''', (kullanici, fikir, teknik, is_modeli, sure, yenilik))
    conn.commit()


st.title("🚀 Ekip Startup Fikir Oylama Sistemi")
st.markdown(
    "Ekip üyeleri farklı ortamlardan girerek fikirleri oylayabilir. Sistem sonuçları ağırlıklı olarak hesaplar.")

# Arayüzü Sekmelere Ayırma
tab1, tab2, tab3 = st.tabs(["💡 Fikirler", "🗳️ Oy Ver", "📊 Sonuçlar & Rapor"])

# --- SEKME 1: FİKİR EKLEME ---
with tab1:
    st.subheader("Yeni Fikir Ekle")
    yeni_fikir = st.text_input("Geliştirmeyi düşündüğünüz fikrin adı:")
    if st.button("Fikri Sisteme Ekle"):
        if yeni_fikir:
            if fikir_ekle(yeni_fikir):
                st.success(f"'{yeni_fikir}' başarıyla eklendi!")
            else:
                st.warning("Bu fikir zaten listede var.")
        else:
            st.error("Lütfen bir fikir adı girin.")

    st.divider()
    st.markdown("**Mevcut Fikirler:**")
    for f in fikirleri_getir():
        st.write(f"- {f}")

# --- SEKME 2: OY VERME ---
with tab2:
    st.subheader("Kriterlere Göre Değerlendirme")

    mevcut_fikirler = fikirleri_getir()
    if not mevcut_fikirler:
        st.info("Oy vermek için önce 'Fikirler' sekmesinden proje ekleyin.")
    else:
        kullanici_adi = st.selectbox("Kim oy veriyor?",
                                     ["Osman", "Ferdi", "Şükrü", "Berkan", "Yiğit)"])
        secilen_fikir = st.selectbox("Hangi fikri oyluyorsun?", mevcut_fikirler)

        st.markdown("Lütfen **1 (Çok Kötü) - 10 (Çok İyi)** arası puan verin:")

        t_puan = st.slider("💻 Teknik Uygulanabilirlik (Ekibin yetkinliği)", 1, 10, 5)
        i_puan = st.slider("📈 İş Modeli / Pazar Potansiyeli", 1, 10, 5)
        s_puan = st.slider("⏱️ Geliştirme Süresi (Kısa sürede bitmesi = Yüksek Puan)", 1, 10, 5)
        y_puan = st.slider("🌟 Yenilikçilik / Özgünlük", 1, 10, 5)

        if st.button("Oyu Kaydet"):
            oy_kaydet(kullanici_adi, secilen_fikir, t_puan, i_puan, s_puan, y_puan)
            st.success(f"{kullanici_adi}, '{secilen_fikir}' için oylaman kaydedildi!")

# --- SEKME 3: SONUÇLAR ---
with tab3:
    st.subheader("Ağırlıklı Proje Sıralaması")

    df = pd.read_sql_query("SELECT * FROM oylar", conn)

    if df.empty:
        st.info("Henüz hiç oy kullanılmadı.")
    else:
        # Ağırlıkların hesaplanması
        df['Agirlikli_Puan'] = (df['teknik'] * 0.30) + (df['is_modeli'] * 0.30) + (df['sure'] * 0.20) + (
                    df['yenilik'] * 0.20)

        # Fikirlere göre ortalama puanları gruplama
        sonuclar = df.groupby('fikir')['Agirlikli_Puan'].mean().reset_index()
        sonuclar = sonuclar.sort_values(by='Agirlikli_Puan', ascending=False)
        sonuclar.columns = ['Proje Fikri', 'Ortalama Ağırlıklı Puan']

        st.dataframe(sonuclar, use_container_width=True, hide_index=True)

        kazanan = sonuclar.iloc[0]
        st.success(
            f"🏆 **Şu anki lider proje:** {kazanan['Proje Fikri']} ({kazanan['Ortalama Ağırlıklı Puan']:.2f} puan)")

        with st.expander("Detaylı Oylama Dökümünü Gör"):
            st.dataframe(df)

conn.close()